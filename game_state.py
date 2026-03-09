"""
game_state.py — Quest: Avalon per-channel game state machine.
"""
from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

import discord

from roles import (
    Role, Side, assign_roles,
    QUEST_SIZES, DOUBLE_FAIL_MISSIONS, AMULET_PLACEMENTS,
    MORGAN_LE_FEY, BLIND_HUNTER, ARTHUR, CLERIC,
)


class Phase(Enum):
    LOBBY = auto()
    TEAM_BUILD = auto()
    QUEST = auto()
    AMULET = auto()
    DISCUSSION = auto()   # Final Mission discussion (5 min)
    HUNT = auto()         # Blind Hunter hunting
    LAST_CHANCE = auto()  # Good side accusation
    ENDED = auto()


@dataclass(eq=False)   # eq=False keeps default identity hash — makes PlayerInfo hashable
class PlayerInfo:
    member: discord.Member
    role: Optional[Role] = None
    is_leader: bool = False
    has_veteran: bool = False        # Can't be chosen as leader again
    has_amulet: bool = False         # Holds the current Amulet token
    amulet_checked: bool = False     # Has been checked by Amulet this cycle
    on_team: bool = False
    has_magic_seal: bool = False
    quest_card_played: Optional[bool] = None  # True=Success, False=Fail
    revealed_evil: bool = False              # Revealer has revealed

    @property
    def user_id(self) -> int:
        return self.member.id

    @property
    def display_name(self) -> str:
        return self.member.display_name


class GameState:
    """Holds all state for a single Quest: Avalon game in one channel."""

    def __init__(self, channel: discord.TextChannel, host: discord.Member):
        self.channel = channel
        self.host = host
        self.phase: Phase = Phase.LOBBY
        self.players: list[PlayerInfo] = []
        self.player_map: dict[int, PlayerInfo] = {}   # user_id → PlayerInfo

        # Mission tracking
        self.current_mission: int = 0   # 0-indexed (0–4)
        self.mission_results: list[Optional[bool]] = [None] * 5  # True=success
        self.good_wins: int = 0
        self.evil_wins: int = 0

        # Leader tracking
        self.leader_index: int = 0       # index into self.players

        # Team building
        self.team: list[PlayerInfo] = []
        self.magic_seal_target: Optional[PlayerInfo] = None

        # Quest voting
        self.quest_votes: dict[int, bool] = {}  # user_id → True/False

        # Amulet state
        self.amulet_tokens_remaining: list[int] = []  # mission indices where amulet activates
        self.amulet_holder: Optional[PlayerInfo] = None
        self.amulet_checked_players: set[int] = set()   # user_ids checked this game

        # Cleric state
        self.first_leader_alignment_revealed_to: Optional[PlayerInfo] = None

        # Last Chance / Hunt
        self.last_chance_accusations: dict[int, list[int]] = {}   # accuser_id → [target_ids]
        self.hunt_targets: list[tuple[str, int]] = []   # [(role_name, user_id), ...]
        self.revealer: Optional[PlayerInfo] = None

        # Final discussion timer
        self._discussion_task: Optional[asyncio.Task] = None

    # ──────────────────────────── Player management ────────────────────────────

    def add_player(self, member: discord.Member) -> bool:
        """Add player to lobby. Returns False if already joined or game full."""
        if member.id in self.player_map:
            return False
        if len(self.players) >= 10:
            return False
        pi = PlayerInfo(member=member)
        self.players.append(pi)
        self.player_map[member.id] = pi
        return True

    def player_count(self) -> int:
        return len(self.players)

    @property
    def leader(self) -> PlayerInfo:
        return self.players[self.leader_index]

    # ──────────────────────────── Game start ───────────────────────────────────

    def start_game(self) -> dict[PlayerInfo, Role]:
        """Assign roles, set up initial state. Returns player→role mapping."""
        n = self.player_count()
        roles = assign_roles(n)
        for pi, role in zip(self.players, roles):
            pi.role = role

        # Set first leader (already chosen randomly or by index 0)
        self.players[self.leader_index].is_leader = True
        self.players[self.leader_index].has_veteran = True

        # Amulet placement
        self.amulet_tokens_remaining = list(AMULET_PLACEMENTS.get(n, []))

        self.phase = Phase.TEAM_BUILD
        return {pi: pi.role for pi in self.players}

    def get_night_info(self, pi: PlayerInfo) -> str:
        """
        Return the night-reveal information string for a player.
        This is sent privately after role cards are dealt.
        """
        role = pi.role
        n = self.player_count()
        lines = []

        # Morgan le Fey sees named Evil players
        if role.name == "Morgan le Fey":
            evil_peers = [
                p.display_name for p in self.players
                if p.role and p.role.side == Side.EVIL
                and p.role.visible_to_evil
                and p.user_id != pi.user_id
            ]
            if evil_peers:
                lines.append(f"🔮 You can see your fellow Evil allies: **{', '.join(evil_peers)}**")
            # In 4-5 player games, Morgan knows Scion
            scion = next((p for p in self.players if p.role and p.role.name == "Scion"), None)
            if scion:
                lines.append(f"🕯️ You know the **Scion** is: **{scion.display_name}**")

        # Minion of Mordred sees named Evil
        elif role.name == "Minion of Mordred":
            evil_peers = [
                p.display_name for p in self.players
                if p.role and p.role.side == Side.EVIL
                and p.role.visible_to_evil
                and p.user_id != pi.user_id
            ]
            if evil_peers:
                lines.append(f"⚔️ You know these Evil allies: **{', '.join(evil_peers)}**")

        # Minions that are visible see each other (Brute, Lunatic, Trickster, Revealer)
        elif role.visible_to_evil and role.side == Side.EVIL:
            evil_peers = [
                p.display_name for p in self.players
                if p.role and p.role.side == Side.EVIL
                and p.role.visible_to_evil
                and p.user_id != pi.user_id
            ]
            if evil_peers:
                lines.append(f"You can see these Evil allies: **{', '.join(evil_peers)}**")

        # Cleric knows if first leader is Good or Evil
        elif role.name == "Cleric":
            first_leader = self.players[self.leader_index]
            alignment = "**Evil** 💀" if first_leader.role.side == Side.EVIL else "**Good** ⚔️"
            lines.append(f"⛪ The first Leader (**{first_leader.display_name}**) is {alignment}.")

        # Arthur knows Morgan le Fey
        elif role.name == "Arthur":
            morgan = next((p for p in self.players if p.role and p.role.name == "Morgan le Fey"), None)
            if morgan:
                lines.append(f"⚜️ You know that **{morgan.display_name}** is Morgan le Fey.")

        return "\n".join(lines) if lines else "You have no special knowledge at game start."

    # ──────────────────────────── Team Building ────────────────────────────────

    def set_team(self, member_ids: list[int]) -> tuple[bool, str]:
        """Leader picks team. Returns (ok, error_msg)."""
        if self.phase != Phase.TEAM_BUILD:
            return False, "It's not the team-building phase."
        required = QUEST_SIZES[self.player_count()][self.current_mission]
        if len(member_ids) != required:
            return False, f"Quest {self.current_mission+1} requires exactly **{required}** players."
        for uid in member_ids:
            if uid not in self.player_map:
                return False, "One or more mentioned players are not in the game."
        # Clear previous team
        for p in self.players:
            p.on_team = False
            p.has_magic_seal = False
        self.team = []
        for uid in member_ids:
            pi = self.player_map[uid]
            pi.on_team = True
            self.team.append(pi)
        self.magic_seal_target = None
        return True, ""

    def set_magic_seal(self, target_id: int) -> tuple[bool, str]:
        """Leader applies magic seal to a team member (or self)."""
        if target_id not in self.player_map:
            return False, "Player not found in the game."
        target = self.player_map[target_id]
        # Clear old seal
        for p in self.players:
            p.has_magic_seal = False
        target.has_magic_seal = True
        self.magic_seal_target = target
        return True, ""

    def auto_pick_team(self) -> None:
        """Randomly picks the team and magic seal target for the current mission."""
        n = self.player_count()
        size = QUEST_SIZES[n][self.current_mission]
        chosen = random.sample(self.players, size)
        ids = [p.user_id for p in chosen]
        self.set_team(ids)
        seal_target = random.choice(self.team)
        self.set_magic_seal(seal_target.user_id)

    def begin_quest_phase(self):
        """Transition from TEAM_BUILD to QUEST. Reset vote tracking."""
        self.quest_votes = {}
        for p in self.team:
            p.quest_card_played = None
        self.phase = Phase.QUEST

    def is_forced_success(self, pi: PlayerInfo) -> bool:
        """Return True if the player MUST play Success this quest."""
        role = pi.role
        if role.side == Side.GOOD and not role.must_fail_if_sealed:
            return True
        if pi.has_magic_seal and not role.can_bypass_magic_seal:
            return True
        # Youth with seal must fail — not forced success
        if pi.has_magic_seal and role.must_fail_if_sealed:
            return False
        # Lunatic must always fail
        if role.must_always_fail and not pi.has_magic_seal:
            return False
        if role.must_always_fail and pi.has_magic_seal:
            return True   # Magic seal overrides Lunatic
        # Brute can only fail first 3 missions
        if role.can_only_fail_first_3 and self.current_mission >= 3:
            return True   # Must play success on M4+
        return False

    def is_forced_fail(self, pi: PlayerInfo) -> bool:
        """Return True if the player MUST play Fail this quest."""
        role = pi.role
        if pi.has_magic_seal and role.must_fail_if_sealed:
            return True
        if role.must_always_fail and not pi.has_magic_seal:
            return True
        return False

    def record_vote(self, user_id: int, success: bool) -> tuple[bool, str]:
        """Record a quest vote: True=Success, False=Fail."""
        if user_id not in self.player_map:
            return False, "You are not in this game."
        pi = self.player_map[user_id]
        if not pi.on_team:
            return False, "You are not on the quest team."
        if self.phase != Phase.QUEST:
            return False, "No quest is active right now."
        # Enforce role restrictions
        if success is False and self.is_forced_success(pi):
            return False, "Your role forces you to play **Success** — you cannot play Fail."
        if success is True and self.is_forced_fail(pi):
            return False, "Your role forces you to play **Fail** — you cannot play Success."
        self.quest_votes[user_id] = success
        return True, ""

    def all_votes_in(self) -> bool:
        return len(self.quest_votes) == len(self.team)

    def resolve_quest(self) -> dict:
        """
        Tally votes, update mission results.
        Returns a result dict with keys: success, fail_count, mission_ended,
        game_over, winner ('good'/'evil'/None), cards.
        """
        n = self.player_count()
        votes = list(self.quest_votes.values())
        fail_count = votes.count(False)
        double_fail_required = self.current_mission in DOUBLE_FAIL_MISSIONS.get(n, set())
        success = (fail_count == 0) or (double_fail_required and fail_count < 2)

        self.mission_results[self.current_mission] = success
        if success:
            self.good_wins += 1
        else:
            self.evil_wins += 1

        # Revealer must reveal after 3rd fail
        revealer_reveals = False
        if not success and self.evil_wins == 3:
            rev = next((p for p in self.players
                        if p.role and p.role.must_reveal_after_3rd_fail and not p.revealed_evil), None)
            if rev:
                rev.revealed_evil = True
                self.revealer = rev
                revealer_reveals = True

        game_over = False
        winner = None
        if self.good_wins >= 3:
            game_over = True
            winner = "good"
        elif self.evil_wins >= 3 or (n == 4 and self.evil_wins >= 2):
            game_over = True
            winner = "evil_final"   # trigger Final Mission phase

        result = {
            "mission": self.current_mission + 1,
            "success": success,
            "fail_count": fail_count,
            "double_fail_required": double_fail_required,
            "good_wins": self.good_wins,
            "evil_wins": self.evil_wins,
            "game_over": game_over,
            "winner": winner,
            "cards": votes,
            "revealer_reveals": revealer_reveals,
            "revealer": self.revealer,
        }
        return result

    # ──────────────────────────── Transition (Amulet + Next Leader) ────────────

    def advance_to_next_mission(self) -> dict:
        """
        Move to next mission: handle amulet placement and pick next leader.
        Returns info about what happened.
        """
        info = {"amulet_available": False, "amulet_mission_after": None}

        # Check if an amulet token is placed after this mission
        if self.current_mission in self.amulet_tokens_remaining:
            self.amulet_tokens_remaining.remove(self.current_mission)
            info["amulet_available"] = True
            info["amulet_mission_after"] = self.current_mission + 1
            # Amulet holder will be assigned by the leader's /quest seal-amulet command
            self.phase = Phase.AMULET
        else:
            self.current_mission += 1
            self.phase = Phase.TEAM_BUILD

        return info

    def assign_next_leader(self, target_id: int) -> tuple[bool, str]:
        """Leader chooses next leader (cannot be veteran or amulet holder)."""
        if target_id not in self.player_map:
            return False, "Player not found."
        target = self.player_map[target_id]
        if target.has_veteran:
            return False, f"**{target.display_name}** already led a mission (has Veteran token)."
        if target.has_amulet:
            return False, f"**{target.display_name}** holds the Amulet token and cannot lead next."
        # Transfer leadership
        self.leader.is_leader = False
        target.is_leader = True
        target.has_veteran = True
        self.leader_index = self.players.index(target)
        return True, ""

    def assign_amulet_holder(self, leader_id: int, target_id: int) -> tuple[bool, str]:
        """Leader assigns amulet to a player (cannot be veteran or same as next leader)."""
        if target_id not in self.player_map:
            return False, "Player not found."
        target = self.player_map[target_id]
        if target.has_veteran:
            return False, f"**{target.display_name}** has a Veteran token and cannot receive the Amulet."
        if target.has_amulet:
            return False, f"**{target.display_name}** already holds an Amulet."
        if target_id in self.amulet_checked_players:
            return False, f"**{target.display_name}** has already been checked by the Amulet."
        # Clear old amulet
        if self.amulet_holder:
            self.amulet_holder.has_amulet = False
        target.has_amulet = True
        self.amulet_holder = target
        return True, ""

    def use_amulet(self, holder_id: int, target_id: int) -> tuple[bool, str, Optional[Side]]:
        """
        Amulet holder checks a player's loyalty.
        Returns (ok, error, loyalty_side).
        The result is the target's TRUE loyalty, EXCEPT:
        - Troublemaker must lie → returns Evil even if Good
        - Trickster may lie → returns evil (we flip for them)
        """
        if holder_id not in self.player_map:
            return False, "You are not in this game.", None
        holder = self.player_map[holder_id]
        if not holder.has_amulet:
            return False, "You don't hold the Amulet.", None
        if target_id not in self.player_map:
            return False, "Target player not found.", None
        if target_id in self.amulet_checked_players:
            return False, "That player has already been checked by an Amulet.", None
        target = self.player_map[target_id]
        if target.has_amulet:
            return False, "You cannot use the Amulet on yourself or the Amulet holder.", None
        if target.has_veteran:
            return False, "That player has a Veteran token and cannot be checked.", None

        # Record check
        self.amulet_checked_players.add(target_id)

        # Determine loyalty shown
        true_side = target.role.side
        shown_side = true_side
        if target.role.must_lie_if_checked:
            shown_side = Side.EVIL   # Troublemaker always claims Evil
        elif target.role.can_lie_if_checked:
            shown_side = Side.EVIL   # Trickster lies (worst case for Good)

        return True, "", shown_side

    # ──────────────────────────── Final Mission ────────────────────────────────

    def start_final_mission(self):
        """Begin Discussion phase before Last Chance / Hunt."""
        self.phase = Phase.DISCUSSION

    def start_hunt(self):
        self.phase = Phase.HUNT

    def start_last_chance(self):
        self.phase = Phase.LAST_CHANCE

    def resolve_hunt(self, guesses: list[tuple[str, int]]) -> dict:
        """
        Blind Hunter names 2 Good players by role.
        guesses = [(role_name, user_id), (role_name, user_id)]
        """
        correct = 0
        arthur_named_first = False
        results = []
        for i, (role_name, uid) in enumerate(guesses):
            if uid not in self.player_map:
                results.append({"role": role_name, "uid": uid, "correct": False})
                continue
            target = self.player_map[uid]
            match = (
                target.role.side == Side.GOOD
                and target.role.name.lower() == role_name.lower()
            )
            if match:
                correct += 1
            # Arthur rule
            if i == 0 and target.role.name == "Arthur":
                arthur_named_first = True
            results.append({"role": role_name, "player": target, "correct": match})

        # Evil wins if both correct, or if Arthur named first (Arthur rule)
        evil_wins = (correct == 2) or arthur_named_first
        self.phase = Phase.ENDED
        return {
            "guesses": results,
            "correct": correct,
            "evil_wins": evil_wins,
            "arthur_named_first": arthur_named_first,
            "winner": "evil" if evil_wins else "good",
        }

    def record_last_chance_accusation(self, accuser_id: int, target_ids: list[int]) -> tuple[bool, str]:
        """Good player (or all) points at 2 suspected Evil players."""
        if accuser_id not in self.player_map:
            return False, "You are not in this game."
        pi = self.player_map[accuser_id]
        if pi.role.side != Side.GOOD:
            return False, "Only Good players participate in Last Chance."
        if len(target_ids) != 2:
            return False, "You must point at exactly **2** players."
        self.last_chance_accusations[accuser_id] = target_ids
        return True, ""

    def resolve_last_chance(self) -> dict:
        """
        Tally Last Chance accusations.
        Good wins if ALL Good players point at ALL Evil players and ONLY Evil players.
        Special: Revealer who has revealed is excluded from needing to be pointed at.
        """
        evil_ids = {
            p.user_id for p in self.players
            if p.role.side == Side.EVIL and not p.revealed_evil
        }
        good_players = [p for p in self.players if p.role.side == Side.GOOD]

        # Check each Good player pointed at exactly the evil set
        good_wins = True
        for gp in good_players:
            # Apprentice: starts with 1 hand — we just check final targets
            accused = set(self.last_chance_accusations.get(gp.user_id, []))
            if accused != evil_ids:
                good_wins = False
                break

        # Edge case: if every leader for every mission was Evil, Good wins per rules
        all_leaders_evil = all(
            self.players[i].role.side == Side.EVIL
            for i in range(len(self.mission_results)) if self.mission_results[i] is not None
        )
        if all_leaders_evil:
            good_wins = True

        self.phase = Phase.ENDED
        return {
            "winner": "good" if good_wins else "evil",
            "good_wins": good_wins,
            "evil_players": [self.player_map[uid] for uid in evil_ids if uid in self.player_map],
        }

    def get_all_roles_reveal(self) -> list[tuple[PlayerInfo, Role]]:
        """Return all (player, role) pairs for end-of-game reveal."""
        return [(p, p.role) for p in self.players]
