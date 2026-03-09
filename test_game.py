"""
test_game.py — Unit tests for Quest: Avalon game logic.

Runs without a Discord connection. Use:
    python3 -m pytest test_game.py -v
or:
    python3 test_game.py
"""
import sys
import types
import unittest
from unittest.mock import MagicMock, AsyncMock
import random

# ─── Stub the discord module so we can import game_state without a bot ─────────
discord_stub = types.ModuleType("discord")

class _Member:
    def __init__(self, uid: int, name: str):
        self.id = uid
        self.display_name = name
    async def send(self, *a, **kw): pass

discord_stub.Member = _Member
discord_stub.TextChannel = MagicMock
sys.modules.setdefault("discord", discord_stub)

# ─── Now safe to import game logic ────────────────────────────────────────────
from roles import (
    Side, QUEST_SIZES, AMULET_PLACEMENTS, assign_roles,
    STANDARD_COMPOSITION, ALL_ROLES,
    LOYAL_SERVANT, MORGAN_LE_FEY, SCION, MINION_OF_MORDRED,
)
from game_state import GameState, PlayerInfo, Phase


def make_member(uid: int, name: str = None) -> _Member:
    return _Member(uid, name or f"Player{uid}")


def make_game(n: int) -> GameState:
    """Create a game with n fake players, already started."""
    channel = MagicMock()
    channel.id = 999
    host = make_member(1, "Host")
    game = GameState(channel=channel, host=host)
    for i in range(1, n + 1):
        game.add_player(make_member(i, f"P{i}"))
    game.start_game()
    return game


# ══════════════════════════════════════════════════════════════════════════════
class TestRoleAssignment(unittest.TestCase):

    def test_correct_player_count_4(self):
        roles = assign_roles(4)
        self.assertEqual(len(roles), 4)
        good = [r for r in roles if r.side == Side.GOOD]
        evil = [r for r in roles if r.side == Side.EVIL]
        self.assertEqual(len(good), 2)
        self.assertEqual(len(evil), 2)

    def test_correct_player_count_7(self):
        roles = assign_roles(7)
        self.assertEqual(len(roles), 7)
        good = [r for r in roles if r.side == Side.GOOD]
        evil = [r for r in roles if r.side == Side.EVIL]
        self.assertEqual(len(good), 4)
        self.assertEqual(len(evil), 3)

    def test_morgan_always_present(self):
        for n in range(4, 11):
            roles = assign_roles(n)
            names = [r.name for r in roles]
            self.assertIn("Morgan le Fey", names, f"Morgan missing for {n} players")

    def test_all_player_counts(self):
        for n in range(4, 11):
            roles = assign_roles(n)
            self.assertEqual(len(roles), n)


# ══════════════════════════════════════════════════════════════════════════════
class TestPlayerInfo(unittest.TestCase):

    def test_player_info_hashable(self):
        """PlayerInfo must be usable as dict key / in sets (critical bug fix)."""
        m = make_member(1)
        pi = PlayerInfo(member=m)
        pi.role = LOYAL_SERVANT
        # This must NOT raise 'unhashable type: PlayerInfo'
        d = {pi: "value"}
        self.assertEqual(d[pi], "value")
        s = {pi}
        self.assertIn(pi, s)


# ══════════════════════════════════════════════════════════════════════════════
class TestGameStart(unittest.TestCase):

    def test_start_assigns_roles(self):
        game = make_game(5)
        self.assertEqual(game.phase, Phase.TEAM_BUILD)
        for p in game.players:
            self.assertIsNotNone(p.role)

    def test_start_sets_leader(self):
        game = make_game(5)
        self.assertTrue(game.leader.is_leader)
        self.assertTrue(game.leader.has_veteran)

    def test_start_phase_is_team_build(self):
        game = make_game(6)
        self.assertEqual(game.phase, Phase.TEAM_BUILD)


# ══════════════════════════════════════════════════════════════════════════════
class TestAutoPickTeam(unittest.TestCase):

    def test_auto_pick_correct_size_mission1(self):
        for n in [4, 5, 6, 7, 8]:
            game = make_game(n)
            game.auto_pick_team()
            expected = QUEST_SIZES[n][0]
            self.assertEqual(len(game.team), expected,
                             f"n={n}: expected {expected}, got {len(game.team)}")

    def test_auto_pick_sets_seal(self):
        game = make_game(5)
        game.auto_pick_team()
        self.assertIsNotNone(game.magic_seal_target)
        self.assertTrue(any(p.has_magic_seal for p in game.players))

    def test_auto_pick_team_members_are_in_game(self):
        game = make_game(6)
        game.auto_pick_team()
        for p in game.team:
            self.assertIn(p, game.players)

    def test_auto_pick_no_duplicate_team_members(self):
        game = make_game(8)
        game.auto_pick_team()
        ids = [p.user_id for p in game.team]
        self.assertEqual(len(ids), len(set(ids)))

    def test_auto_pick_seal_is_on_team_member(self):
        game = make_game(5)
        game.auto_pick_team()
        self.assertIn(game.magic_seal_target, game.team)


# ══════════════════════════════════════════════════════════════════════════════
class TestQuestVoting(unittest.TestCase):

    def _setup_quest(self, n: int):
        game = make_game(n)
        game.auto_pick_team()
        game.begin_quest_phase()
        return game

    def test_all_success_quest_succeeds(self):
        game = self._setup_quest(5)
        for p in game.team:
            ok, err = game.record_vote(p.user_id, True)
            self.assertTrue(ok, f"Vote rejected: {err}")
        self.assertTrue(game.all_votes_in())
        result = game.resolve_quest()
        self.assertTrue(result["success"])
        self.assertEqual(result["fail_count"], 0)

    def test_one_fail_quest_fails(self):
        game = self._setup_quest(6)
        votes = [True] * len(game.team)
        votes[0] = False   # one evil vote
        for p, v in zip(game.team, votes):
            # Override forced-success for testing
            game.quest_votes[p.user_id] = v
        result = game.resolve_quest()
        self.assertFalse(result["success"])
        self.assertEqual(result["fail_count"], 1)

    def test_good_wins_after_3_successes(self):
        game = make_game(5)
        # Simulate 3 successful missions
        game.good_wins = 2
        game.auto_pick_team()
        game.begin_quest_phase()
        for p in game.team:
            game.quest_votes[p.user_id] = True
        result = game.resolve_quest()
        self.assertTrue(result["success"])
        self.assertEqual(result["winner"], "good")

    def test_evil_triggers_final_mission_after_3_fails(self):
        game = make_game(5)
        game.evil_wins = 2
        game.auto_pick_team()
        game.begin_quest_phase()
        for p in game.team:
            game.quest_votes[p.user_id] = False
        result = game.resolve_quest()
        self.assertFalse(result["success"])
        self.assertEqual(result["winner"], "evil_final")

    def test_4player_2fails_triggers_final(self):
        game = make_game(4)
        game.evil_wins = 1
        game.auto_pick_team()
        game.begin_quest_phase()
        for p in game.team:
            game.quest_votes[p.user_id] = False
        result = game.resolve_quest()
        self.assertEqual(result["winner"], "evil_final")

    def test_double_fail_rule_mission4_7players(self):
        """In 7+ player games, mission 4 needs 2 Fail cards to fail."""
        game = make_game(7)
        game.current_mission = 3  # mission 4 (0-indexed)
        game.auto_pick_team()
        game.begin_quest_phase()
        # Only 1 fail → should still SUCCEED (double-fail rule)
        for i, p in enumerate(game.team):
            game.quest_votes[p.user_id] = (i > 0)  # first player fails
        result = game.resolve_quest()
        self.assertTrue(result["success"], "M4 with 1 fail in 7p game should succeed")


# ══════════════════════════════════════════════════════════════════════════════
class TestMagicSeal(unittest.TestCase):

    def test_forced_success_standard_good(self):
        game = make_game(5)
        good_player = next(p for p in game.players if p.role.side == Side.GOOD)
        self.assertTrue(game.is_forced_success(good_player))

    def test_morgan_bypasses_seal(self):
        game = make_game(5)
        morgan = next((p for p in game.players if p.role.name == "Morgan le Fey"), None)
        if morgan:
            morgan.has_magic_seal = True
            # Morgan can STILL fail even when sealed
            self.assertFalse(game.is_forced_success(morgan))


# ══════════════════════════════════════════════════════════════════════════════
class TestQuestSizeTable(unittest.TestCase):

    def test_all_sizes_defined(self):
        for n in range(4, 11):
            self.assertIn(n, QUEST_SIZES)

    def test_5player_missions(self):
        self.assertEqual(QUEST_SIZES[5], [2, 3, 2, 3, 3])

    def test_8player_missions(self):
        self.assertEqual(QUEST_SIZES[8], [3, 4, 4, 5, 5])


# ══════════════════════════════════════════════════════════════════════════════
class TestAmuletPlacements(unittest.TestCase):

    def test_4_5_players_no_amulet(self):
        self.assertEqual(AMULET_PLACEMENTS[4], [])
        self.assertEqual(AMULET_PLACEMENTS[5], [])

    def test_6_players_one_amulet(self):
        self.assertEqual(AMULET_PLACEMENTS[6], [1])  # after mission 2

    def test_8_players_three_amulets(self):
        self.assertEqual(AMULET_PLACEMENTS[8], [1, 2, 3])


# ══════════════════════════════════════════════════════════════════════════════
class TestHunt(unittest.TestCase):

    def test_correct_hunt_evil_wins(self):
        game = make_game(6)
        # Find two Good players
        good_players = [p for p in game.players if p.role.side == Side.GOOD][:2]
        guesses = [(good_players[0].role.name, good_players[0].user_id),
                   (good_players[1].role.name, good_players[1].user_id)]
        result = game.resolve_hunt(guesses)
        self.assertTrue(result["evil_wins"])
        self.assertEqual(result["correct"], 2)

    def test_wrong_hunt_good_wins(self):
        game = make_game(6)
        good_players = [p for p in game.players if p.role.side == Side.GOOD]
        # Deliberately wrong role names
        guesses = [("WrongRole1", good_players[0].user_id),
                   ("WrongRole2", good_players[1].user_id)]
        result = game.resolve_hunt(guesses)
        self.assertFalse(result["evil_wins"])


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    random.seed(42)   # reproducible results
    unittest.main(verbosity=2)
