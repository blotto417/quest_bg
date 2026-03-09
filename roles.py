"""
roles.py — Quest: Avalon role definitions and role-assignment logic.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Side(Enum):
    GOOD = "good"
    EVIL = "evil"


@dataclass
class Role:
    name: str
    side: Side
    emoji: str
    description: str
    # Special ability flags (True = rule applies)
    must_play_success: bool = False         # Standard Good rule
    can_bypass_magic_seal: bool = False     # Morgan le Fey
    must_fail_if_sealed: bool = False       # Youth
    must_lie_if_checked: bool = False       # Troublemaker
    can_lie_if_checked: bool = False        # Trickster
    knows_morgan: bool = False              # Arthur (knows Morgan le Fey at start)
    known_by_morgan: bool = False           # Scion (Morgan knows them)
    knows_first_leader_alignment: bool = False  # Cleric
    can_only_fail_first_3: bool = False     # Brute
    must_always_fail: bool = False          # Lunatic (unless sealed)
    can_refuse_lower_hand: bool = False     # Mutineer
    must_reveal_after_3rd_fail: bool = False  # Revealer
    can_hunt: bool = False                  # Blind Hunter
    # Visibility in the night-reveal phase
    visible_to_evil: bool = False           # Minion, Morgan see each other
    invisible_to_own_side: bool = False     # Changeling: not known by Evil
    # Last Chance modifiers
    last_chance_one_hand_first: bool = False   # Apprentice
    last_chance_redirect_hand: bool = False    # Duke
    last_chance_swap_hand: bool = False        # Archduke
    # If named first in Hunt and role is "Arthur", evil wins
    arthur_rule: bool = False


# ─── Standard roles ────────────────────────────────────────────────────────────

LOYAL_SERVANT = Role(
    name="Loyal Servant of Arthur",
    side=Side.GOOD,
    emoji="🛡️",
    description="You are a **Loyal Servant of Arthur** (⚔️ Good).\nYou know nothing special. You must always play **Success** on quests.\nHelp your fellow Good players identify the Evil among you.",
    must_play_success=True,
)

MORGAN_LE_FEY = Role(
    name="Morgan le Fey",
    side=Side.EVIL,
    emoji="🔮",
    description="You are **Morgan le Fey** (💀 Evil).\nYou see your fellow Evil allies. You can **bypass the Magic Seal** (you may still play Fail even if sealed).\nAt game start you also learn who the **Scion** is (4–5 player games).",
    visible_to_evil=True,
    can_bypass_magic_seal=True,
)

SCION = Role(
    name="Scion",
    side=Side.EVIL,
    emoji="🕯️",
    description="You are the **Scion** (💀 Evil).\nYou do **not** know other Evil players — but **Morgan le Fey knows you**.\nYou appear in 4–5 player games only.",
    known_by_morgan=True,
)

MINION_OF_MORDRED = Role(
    name="Minion of Mordred",
    side=Side.EVIL,
    emoji="⚔️",
    description="You are a **Minion of Mordred** (💀 Evil).\nYou see your fellow Named Evil allies (Minions + Morgan le Fey) during the night reveal.",
    visible_to_evil=True,
)

CHANGELING = Role(
    name="Changeling",
    side=Side.EVIL,
    emoji="🎭",
    description="You are the **Changeling** (💀 Evil).\nYou do **not** know other Evil players, and they don't know you either.\nYou appear in 6+ player games.",
    invisible_to_own_side=True,
)

DUKE = Role(
    name="Duke",
    side=Side.GOOD,
    emoji="👑",
    description="You are the **Duke** (⚔️ Good).\nDuring the **Last Chance**, after Evil players lower their hands, you may redirect **one player's hand** to point at a different target.",
    must_play_success=True,
    last_chance_redirect_hand=True,
)

ARCHDUKE = Role(
    name="Archduke",
    side=Side.GOOD,
    emoji="🏰",
    description="You are the **Archduke** (⚔️ Good).\nDuring the **Last Chance**, after Evil players lower their hands, you may **swap one player's hand** (change who they're pointing at).",
    must_play_success=True,
    last_chance_swap_hand=True,
)

# ─── Optional roles ─────────────────────────────────────────────────────────────

CLERIC = Role(
    name="Cleric",
    side=Side.GOOD,
    emoji="⛪",
    description="You are the **Cleric** (⚔️ Good).\nYou know whether the **first Leader** is Good or Evil.",
    must_play_success=True,
    knows_first_leader_alignment=True,
)

YOUTH = Role(
    name="Youth",
    side=Side.GOOD,
    emoji="🌱",
    description="You are the **Youth** (⚔️ Good).\nIf the **Magic Seal** is placed on you, you must play **Fail** for that quest instead of Success.",
    must_play_success=True,
    must_fail_if_sealed=True,
)

TROUBLEMAKER = Role(
    name="Troublemaker",
    side=Side.GOOD,
    emoji="🃏",
    description="You are the **Troublemaker** (⚔️ Good).\nIf anyone uses an ability to check your loyalty (Cleric, Amulet, etc.), you **must lie** and claim to be Evil.",
    must_play_success=True,
    must_lie_if_checked=True,
)

APPRENTICE = Role(
    name="Apprentice",
    side=Side.GOOD,
    emoji="📜",
    description="You are the **Apprentice** (⚔️ Good).\nDuring the **Last Chance**, you raise **only one hand** initially. You may raise your second hand after Evil players lower theirs.",
    must_play_success=True,
    last_chance_one_hand_first=True,
)

BLIND_HUNTER = Role(
    name="Blind Hunter",
    side=Side.EVIL,
    emoji="🏹",
    description="You are the **Blind Hunter** (💀 Evil).\nYou do **not** know other Evil players (they know you via thumbs-up).\nWhen the Final Mission begins, you may choose to **Hunt**: name 2 Good players by role. If correct, Evil wins. If wrong, Good wins.",
    can_hunt=True,
)

BRUTE = Role(
    name="Brute",
    side=Side.EVIL,
    emoji="🪓",
    description="You are the **Brute** (💀 Evil).\nYou may only play **Fail** during the first 3 quests. On quests 4 and 5 you must play **Success**.",
    visible_to_evil=True,
    can_only_fail_first_3=True,
)

LUNATIC = Role(
    name="Lunatic",
    side=Side.EVIL,
    emoji="🌕",
    description="You are the **Lunatic** (💀 Evil).\nYou **must always play Fail** on every quest you participate in — unless the Magic Seal is placed on you.",
    visible_to_evil=True,
    must_always_fail=True,
)

MUTINEER = Role(
    name="Mutineer",
    side=Side.EVIL,
    emoji="🏴",
    description="You are the **Mutineer** (💀 Evil).\nYou don't know other Evil players.\nDuring the **Last Chance**, you may choose **not** to lower your hand. If you are still pointing at 2 Good players when it ends, you **switch to the Good side** — but Good must have pointed at you to win.",
    can_refuse_lower_hand=True,
)

TRICKSTER = Role(
    name="Trickster",
    side=Side.EVIL,
    emoji="🎩",
    description="You are the **Trickster** (💀 Evil).\nWhenever your loyalty is checked (Amulet, Cleric, etc.), you may give a **false answer**.",
    visible_to_evil=True,
    can_lie_if_checked=True,
)

REVEALER = Role(
    name="Revealer",
    side=Side.EVIL,
    emoji="👁️",
    description="You are the **Revealer** (💀 Evil).\nYou see your fellow Evil allies.\nAfter the **3rd failed quest**, you **must publicly reveal** your identity. Players do not need to (and cannot) point at you during Last Chance.",
    visible_to_evil=True,
    must_reveal_after_3rd_fail=True,
)

ARTHUR = Role(
    name="Arthur",
    side=Side.GOOD,
    emoji="⚜️",
    description="You are **Arthur** (⚔️ Good).\nAt the start you know who **Morgan le Fey** is.\nIf the Blind Hunter names you **first** during the Hunt, Evil wins immediately — even if the second guess is wrong.",
    must_play_success=True,
    knows_morgan=True,
    arthur_rule=True,
)

# ─── Role registry ─────────────────────────────────────────────────────────────

ALL_ROLES: dict[str, Role] = {
    r.name: r for r in [
        LOYAL_SERVANT, MORGAN_LE_FEY, SCION, MINION_OF_MORDRED, CHANGELING,
        DUKE, ARCHDUKE, CLERIC, YOUTH, TROUBLEMAKER, APPRENTICE,
        BLIND_HUNTER, BRUTE, LUNATIC, MUTINEER, TRICKSTER, REVEALER, ARTHUR,
    ]
}

# ─── Standard composition tables ───────────────────────────────────────────────

# (good_roles_list, evil_roles_list) keyed by player count
STANDARD_COMPOSITION: dict[int, tuple[list[str], list[str]]] = {
    # 2-3 player test modes
    2: (
        ["Loyal Servant of Arthur"],
        ["Morgan le Fey"],
    ),
    3: (
        ["Loyal Servant of Arthur", "Loyal Servant of Arthur"],
        ["Morgan le Fey"],
    ),
    4: (
        ["Loyal Servant of Arthur", "Loyal Servant of Arthur"],
        ["Morgan le Fey", "Scion"],
    ),
    5: (
        ["Loyal Servant of Arthur", "Loyal Servant of Arthur", "Loyal Servant of Arthur"],
        ["Morgan le Fey", "Scion"],
    ),
    6: (
        ["Loyal Servant of Arthur", "Loyal Servant of Arthur", "Loyal Servant of Arthur"],
        ["Morgan le Fey", "Minion of Mordred", "Changeling"],
    ),
    7: (
        ["Loyal Servant of Arthur", "Loyal Servant of Arthur", "Loyal Servant of Arthur", "Duke"],
        ["Morgan le Fey", "Minion of Mordred", "Changeling"],
    ),
    8: (
        ["Loyal Servant of Arthur", "Loyal Servant of Arthur", "Loyal Servant of Arthur", "Loyal Servant of Arthur", "Duke"],
        ["Morgan le Fey", "Minion of Mordred", "Changeling"],
    ),
    9: (
        ["Loyal Servant of Arthur", "Loyal Servant of Arthur", "Loyal Servant of Arthur", "Loyal Servant of Arthur", "Duke", "Archduke"],
        ["Morgan le Fey", "Minion of Mordred", "Changeling"],
    ),
    10: (
        ["Loyal Servant of Arthur", "Loyal Servant of Arthur", "Loyal Servant of Arthur", "Loyal Servant of Arthur", "Duke", "Archduke"],
        ["Morgan le Fey", "Minion of Mordred", "Minion of Mordred", "Changeling"],
    ),
}

# Quest team sizes per player count per mission (1-indexed missions)
QUEST_SIZES: dict[int, list[int]] = {
    #                M1  M2  M3  M4  M5
    2:              [ 1,  1,  1,  1,  1],   # test mode
    3:              [ 1,  2,  2,  2,  2],   # test mode
    4:              [ 2,  3,  2,  3,  0],   # 4 players only go to mission 4 to end
    5:              [ 2,  3,  2,  3,  3],
    6:              [ 2,  3,  4,  3,  4],
    7:              [ 2,  3,  3,  4,  4],
    8:              [ 3,  4,  4,  5,  5],
    9:              [ 3,  4,  4,  5,  5],
    10:             [ 3,  4,  4,  5,  5],
}

# For 4-player games, mission 3 and 4 sizes are listed as "2½" in the rules
# meaning the leader counts twice if they're the only one — we model it as 2
# because 4-player max missions is 4 (game ends after 2 fails)
# For 4-player, the game is actually M1–M4; M5 = 0 (not used).

# In 7+ player games, Quest 4 requires 2 Fail cards to fail
DOUBLE_FAIL_MISSIONS: dict[int, set[int]] = {
    p: set()
    for p in range(2, 11)
}
# Actually per rules: "Quest 4 in 7+ player games requires 2 Fail to fail"
for p in range(7, 11):
    DOUBLE_FAIL_MISSIONS[p] = {3}  # 0-indexed mission 4 = index 3

# Amulet positions (0-indexed: placed AFTER which mission index, -1 = none)
# "between missions 2&3" → after mission index 1 (0-based), etc.
AMULET_PLACEMENTS: dict[int, list[int]] = {
    2: [],
    3: [],
    4: [],
    5: [],
    6: [1],          # after M2
    7: [1, 2],       # after M2, after M3
    8: [1, 2, 3],    # after M2, M3, M4
    9: [1, 2, 3],
    10: [1, 2, 3],
}


def assign_roles(player_count: int, use_optional: bool = False) -> list[Role]:
    """
    Return a shuffled list of Role objects for the given player count.
    Uses standard composition unless use_optional is True (not yet implemented).
    """
    good_names, evil_names = STANDARD_COMPOSITION[player_count]
    roles = [ALL_ROLES[n] for n in good_names] + [ALL_ROLES[n] for n in evil_names]
    random.shuffle(roles)
    return roles
