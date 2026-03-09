"""
embeds.py — Rich Discord embed helpers for Quest: Avalon (Tiếng Việt).
"""
from __future__ import annotations

import discord
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game_state import GameState, PlayerInfo
from roles import Side, QUEST_SIZES

C_GOLD   = 0xF4C430
C_RED    = 0xC0392B
C_BLUE   = 0x2980B9
C_GREEN  = 0x27AE60
C_PURPLE = 0x8E44AD
C_DARK   = 0x2C3E50
C_ORANGE = 0xE67E22


def lobby_embed(game: "GameState") -> discord.Embed:
    e = discord.Embed(
        title="⚔️ Quest: Avalon — Phòng Chờ",
        description=(
            "Một trận **Quest: Avalon** mới đang được lập!\n"
            "Dùng `/quest join` để tham gia. Host dùng `/quest start` để bắt đầu (2–10 người)."
        ),
        color=C_GOLD,
    )
    names = "\n".join(f"• {p.display_name}" for p in game.players) or "*Chưa có người chơi.*"
    e.add_field(name=f"Người chơi ({len(game.players)}/10)", value=names, inline=False)
    e.set_footer(text="Quest: Avalon Bot")
    return e


def role_card_embed(pi: "PlayerInfo", night_info: str) -> discord.Embed:
    role = pi.role
    side_label = "⚔️ Phe Thiện" if role.side == Side.GOOD else "💀 Phe Ác"
    color = C_BLUE if role.side == Side.GOOD else C_RED

    role_vn = {
        "Loyal Servant of Arthur": "Tôi Tớ Trung Thành của Arthur",
        "Duke": "Công Tước",
        "Archduke": "Đại Công Tước",
        "Cleric": "Giáo Sĩ",
        "Youth": "Thanh Niên",
        "Troublemaker": "Kẻ Gây Rắc Rối",
        "Apprentice": "Học Việc",
        "Morgan le Fey": "Morgan le Fey",
        "Scion": "Scion",
        "Minion of Mordred": "Tay Sai của Mordred",
        "Changeling": "Kẻ Đổi Chỗ",
        "Blind Hunter": "Thợ Săn Mù",
        "Brute": "Gã Hung Hãn",
        "Lunatic": "Kẻ Điên",
        "Mutineer": "Kẻ Phản Loạn",
        "Trickster": "Kẻ Lừa Đảo",
        "Revealer": "Kẻ Tiết Lộ",
        "Arthur": "Arthur",
    }
    desc_vn = {
        "Loyal Servant of Arthur": "Bạn là **Tôi Tớ Trung Thành của Arthur** ⚔️.\nBạn không có thông tin đặc biệt. Bạn **phải** chơi thẻ **Thành Công** trong mọi nhiệm vụ.\nHãy giúp đồng đội Thiện tìm ra kẻ Ác trong số các người chơi.",
        "Duke": "Bạn là **Công Tước** ⚔️.\nTrong **Cơ Hội Cuối Cùng**, sau khi phe Ác hạ tay, bạn có thể chuyển hướng **bàn tay của một người chơi** sang mục tiêu khác.",
        "Archduke": "Bạn là **Đại Công Tước** ⚔️.\nTrong **Cơ Hội Cuối Cùng**, sau khi phe Ác hạ tay, bạn có thể **đổi bàn tay của một người chơi** sang mục tiêu khác.",
        "Cleric": "Bạn là **Giáo Sĩ** ⚔️.\nBạn biết **Người Lãnh Đạo đầu tiên** thuộc phe Thiện hay phe Ác.",
        "Youth": "Bạn là **Thanh Niên** ⚔️.\nNếu **Con Dấu Ma Thuật** đặt lên bạn, bạn **phải** chơi thẻ **Thất Bại** thay vì Thành Công.",
        "Troublemaker": "Bạn là **Kẻ Gây Rắc Rối** ⚔️.\nNếu ai kiểm tra lòng trung thành của bạn (Bùa Hộ Mệnh, Giáo Sĩ...), bạn **phải nói dối** — khai là Ác.",
        "Apprentice": "Bạn là **Học Việc** ⚔️.\nTrong Cơ Hội Cuối Cùng, bạn chỉ giơ **một tay** lúc đầu. Sau khi phe Ác hạ tay, bạn mới giơ tay thứ hai.",
        "Morgan le Fey": "Bạn là **Morgan le Fey** 💀.\nBạn nhìn thấy đồng đội phe Ác. Bạn có thể **bỏ qua Con Dấu Ma Thuật** — vẫn được chơi Thất Bại dù bị phong ấn.",
        "Scion": "Bạn là **Scion** 💀.\nBạn **không biết** đồng đội phe Ác — nhưng **Morgan le Fey biết bạn**. Chỉ xuất hiện ở ván 4–5 người.",
        "Minion of Mordred": "Bạn là **Tay Sai của Mordred** 💀.\nBạn nhìn thấy các đồng đội phe Ác được đặt tên (Tay Sai + Morgan le Fey) trong lễ tiết lộ ban đêm.",
        "Changeling": "Bạn là **Kẻ Đổi Chỗ** 💀.\nBạn **không biết** đồng đội phe Ác và họ cũng không biết bạn. Xuất hiện từ 6 người trở lên.",
        "Blind Hunter": "Bạn là **Thợ Săn Mù** 💀.\nBạn không biết đồng đội phe Ác (họ biết bạn qua ngón tay cái).\nKhi Nhiệm Vụ Cuối Cùng bắt đầu, bạn có thể **Đi Săn**: đặt tên 2 người Thiện theo vai trò. Đúng cả hai → Ác thắng. Sai → Thiện thắng.",
        "Brute": "Bạn là **Gã Hung Hãn** 💀.\nBạn chỉ được chơi **Thất Bại** trong 3 nhiệm vụ đầu. Nhiệm vụ 4 và 5 bạn phải chơi Thành Công.",
        "Lunatic": "Bạn là **Kẻ Điên** 💀.\nBạn **phải luôn chơi Thất Bại** — trừ khi Con Dấu Ma Thuật đặt lên bạn.",
        "Mutineer": "Bạn là **Kẻ Phản Loạn** 💀.\nBạn không biết đồng đội phe Ác. Trong Cơ Hội Cuối Cùng bạn có thể **không hạ tay**. Nếu bạn đang chỉ vào 2 người Thiện khi kết thúc, bạn chuyển sang phe Thiện (nhưng Thiện vẫn phải chỉ vào bạn để thắng).",
        "Trickster": "Bạn là **Kẻ Lừa Đảo** 💀.\nKhi ai kiểm tra lòng trung thành của bạn, bạn **có thể nói dối** — trả lời kết quả giả.",
        "Revealer": "Bạn là **Kẻ Tiết Lộ** 💀.\nBạn nhìn thấy đồng đội phe Ác. Sau **nhiệm vụ thất bại thứ 3**, bạn **phải tiết lộ** danh tính. Người khác không cần (và không được) chỉ vào bạn trong Cơ Hội Cuối Cùng.",
        "Arthur": "Bạn là **Arthur** ⚔️.\nBạn biết ai là **Morgan le Fey** ngay từ đầu. Nếu Thợ Săn Mù đặt tên bạn **đầu tiên** trong Cuộc Đi Săn, phe Ác thắng ngay lập tức.",
    }

    name_vn = role_vn.get(role.name, role.name)
    desc = desc_vn.get(role.name, role.description)

    # Use English name in title, Vietnamese description
    e = discord.Embed(title=f"{role.emoji} Vai Trò Của Bạn: {role.name}", description=desc, color=color)
    e.add_field(name="Phe", value=side_label, inline=True)
    e.add_field(name="🌙 Thông Tin Đêm", value=night_info, inline=False)
    e.set_footer(text="Giữ bí mật! Không tiết lộ thẻ vai trò của bạn.")
    return e


def status_embed(game: "GameState") -> discord.Embed:
    from game_state import Phase
    n = game.player_count()
    phase_names = {
        Phase.LOBBY: "📋 Phòng Chờ",
        Phase.TEAM_BUILD: "🛡️ Chọn Đội",
        Phase.QUEST: "⚔️ Nhiệm Vụ Đang Diễn Ra",
        Phase.AMULET: "🔮 Giai Đoạn Bùa Hộ Mệnh",
        Phase.DISCUSSION: "💬 Thảo Luận Cuối",
        Phase.HUNT: "🏹 Cuộc Đi Săn",
        Phase.LAST_CHANCE: "🎯 Cơ Hội Cuối Cùng",
        Phase.ENDED: "🏆 Trò Chơi Kết Thúc",
    }
    e = discord.Embed(title="⚔️ Quest: Avalon — Trạng Thái Trò Chơi", color=C_DARK)
    e.add_field(name="Giai Đoạn", value=phase_names.get(game.phase, str(game.phase)), inline=True)
    e.add_field(name="Nhiệm Vụ", value=f"{game.current_mission + 1} / 5", inline=True)
    e.add_field(name="Người Lãnh Đạo", value=game.leader.display_name, inline=True)

    score_str = ""
    for i in range(5 if n > 4 else 4):
        sz = QUEST_SIZES[n][i]
        if sz == 0:
            continue
        r = game.mission_results[i]
        if r is True:
            score_str += f"NV{i+1}(👑{sz})✅  "
        elif r is False:
            score_str += f"NV{i+1}(👑{sz})❌  "
        elif i == game.current_mission:
            score_str += f"**NV{i+1}(👑{sz})**  "
        else:
            score_str += f"NV{i+1}(👑{sz})⬜  "
    e.add_field(name="Nhiệm Vụ", value=score_str or "—", inline=False)
    e.add_field(name="✅ Thiện Thắng", value=str(game.good_wins), inline=True)
    e.add_field(name="❌ Ác Thắng", value=str(game.evil_wins), inline=True)

    if game.team:
        team_str = ", ".join(
            f"**{p.display_name}**{'🔮' if p.has_magic_seal else ''}" for p in game.team
        )
        e.add_field(name="Đội Hiện Tại", value=team_str, inline=False)

    player_lines = []
    for p in game.players:
        tags = []
        if p.is_leader: tags.append("👑Lãnh Đạo")
        if p.has_veteran: tags.append("🎖️Cựu Chiến Binh")
        if p.has_amulet: tags.append("🔮Bùa")
        if p.revealed_evil: tags.append("💀ĐÃ LỘ DIỆN")
        player_lines.append(f"• {p.display_name} {' '.join(tags)}")
    e.add_field(name="Người Chơi", value="\n".join(player_lines), inline=False)
    e.set_footer(text="Quest: Avalon Bot")
    return e


def team_build_embed(game: "GameState") -> discord.Embed:
    n = game.player_count()
    size = QUEST_SIZES[n][game.current_mission]
    e = discord.Embed(
        title=f"🛡️ Nhiệm Vụ {game.current_mission + 1} — Chọn Đội",
        description=(
            f"**Người Lãnh Đạo: {game.leader.display_name}**\n\n"
            f"Bất kỳ người chơi nào cũng có thể chọn đội **{size}** người:\n"
            f"`/quest pick @người1 @người2 ...`\n\n"
            f"Sau đó phong ấn một người với `/quest seal @người`\n"
            f"*(Con Dấu Ma Thuật buộc họ chơi Thành Công)*\n\n"
            f"Hoặc dùng `/quest autopick` để bot chọn ngẫu nhiên."
        ),
        color=C_GOLD,
    )
    vets = [p.display_name for p in game.players if p.has_veteran and not p.is_leader]
    if vets:
        e.add_field(name="🎖️ Cựu Chiến Binh (đã lãnh đạo)", value=", ".join(vets), inline=False)
    e.set_footer(text=f"Nhiệm vụ {game.current_mission + 1} cần {size} người.")
    return e


def quest_start_embed(game: "GameState") -> discord.Embed:
    team_names = ", ".join(
        f"**{p.display_name}**{'🔮' if p.has_magic_seal else ''}" for p in game.team
    )
    e = discord.Embed(
        title=f"⚔️ Nhiệm Vụ {game.current_mission + 1} — Bắt Đầu!",
        description=(
            f"Đội đã được chọn: {team_names}\n\n"
            "Mỗi thành viên sẽ nhận **tin nhắn riêng (DM)** với nút bỏ phiếu.\n"
            "Hãy chọn **Thành Công** hoặc **Thất Bại** trong DM — không tiết lộ phiếu tại đây!"
        ),
        color=C_PURPLE,
    )
    if game.magic_seal_target:
        e.add_field(
            name="🔮 Con Dấu Ma Thuật",
            value=f"**{game.magic_seal_target.display_name}** bị phong ấn — không thể chơi Thất Bại (trừ khi vai trò đặc biệt).",
            inline=False,
        )
    return e


def quest_result_embed(result: dict) -> discord.Embed:
    success = result["success"]
    color = C_GREEN if success else C_RED
    outcome = "✅ **THÀNH CÔNG!**" if success else "❌ **THẤT BẠI!**"
    cards = result["cards"]
    card_str = " ".join("✅" if c else "❌" for c in cards)
    e = discord.Embed(
        title=f"Nhiệm Vụ {result['mission']} — {outcome}",
        description=f"Thẻ đã chơi (đã xáo trộn): {card_str}",
        color=color,
    )
    if result["fail_count"] > 0:
        e.add_field(name="Số Thẻ Thất Bại", value=str(result["fail_count"]), inline=True)
    if result["double_fail_required"]:
        e.add_field(name="Lưu ý", value="Nhiệm vụ này cần 2 thẻ Thất Bại mới thua.", inline=False)
    e.add_field(name="✅ Thiện Thắng", value=str(result["good_wins"]), inline=True)
    e.add_field(name="❌ Ác Thắng", value=str(result["evil_wins"]), inline=True)
    if result.get("revealer_reveals") and result.get("revealer"):
        rev = result["revealer"]
        e.add_field(
            name="👁️ Kẻ Tiết Lộ Lộ Diện!",
            value=f"**{rev.display_name}** là **Kẻ Tiết Lộ** — họ phải công khai danh tính! Không chỉ vào họ trong Cơ Hội Cuối Cùng.",
            inline=False,
        )
    return e


def amulet_embed(game: "GameState") -> discord.Embed:
    e = discord.Embed(
        title="🔮 Giai Đoạn Bùa Hộ Mệnh",
        description=(
            f"**Người Lãnh Đạo ({game.leader.display_name})** cần:\n"
            "1. Chọn **Người Lãnh Đạo tiếp theo** với `/quest nextleader @người`\n"
            "2. Trao **Bùa Hộ Mệnh** cho người khác với `/quest amulet @người`\n\n"
            "Người giữ Bùa có thể bí mật kiểm tra lòng trung thành của một người."
        ),
        color=C_PURPLE,
    )
    excluded = [p.display_name for p in game.players if p.has_veteran or p.has_amulet]
    if excluded:
        e.add_field(name="⛔ Không thể nhận Bùa/Lãnh Đạo", value=", ".join(excluded), inline=False)
    return e


def amulet_result_embed(holder: "PlayerInfo", target: "PlayerInfo", shown_side: Side) -> discord.Embed:
    side_str = "**Phe Ác** 💀" if shown_side == Side.EVIL else "**Phe Thiện** ⚔️"
    e = discord.Embed(
        title="🔮 Kết Quả Bùa Hộ Mệnh (Chỉ Mình Bạn Thấy)",
        description=(
            f"Bạn đã dùng Bùa Hộ Mệnh kiểm tra **{target.display_name}**.\n\n"
            f"Thẻ trung thành hiển thị: {side_str}"
        ),
        color=C_PURPLE,
    )
    e.set_footer(text="Chỉ bạn thấy kết quả này. Bạn có thể tiết lộ hoặc giữ bí mật.")
    return e


def discussion_embed() -> discord.Embed:
    e = discord.Embed(
        title="💬 Thảo Luận Cuối — 5 Phút",
        description=(
            "Ba (hoặc nhiều hơn) nhiệm vụ đã thất bại. Phán quyết cuối cùng bắt đầu!\n\n"
            "**Tất cả người chơi có 5 phút để thảo luận** về phe Ác.\n"
            "Phe Ác có thể gây nhầm lẫn, nằm im, hoặc thậm chí thú nhận.\n\n"
            "Sau đó, **Thợ Săn Mù** có thể chọn Săn, hoặc trò chơi chuyển sang **Cơ Hội Cuối Cùng**."
        ),
        color=C_ORANGE,
    )
    return e


def hunt_prompt_embed(hunter: "PlayerInfo") -> discord.Embed:
    e = discord.Embed(
        title="🏹 Cuộc Đi Săn — Lựa Chọn Của Thợ Săn Mù",
        description=(
            f"**{hunter.display_name}** là **Thợ Săn Mù**.\n\n"
            "Bạn có thể **xác định 2 người Thiện theo đúng vai trò của họ**.\n"
            "Nếu đúng cả hai, **Ác thắng ngay lập tức**.\n"
            "Nếu sai, **Thiện thắng**.\n\n"
            "Dùng: `/quest hunt <vai_trò_1> @người1 <vai_trò_2> @người2`\n\n"
            "Hoặc im lặng để Thiện có **Cơ Hội Cuối Cùng**."
        ),
        color=C_RED,
    )
    return e


def hunt_result_embed(result: dict) -> discord.Embed:
    evil_wins = result["evil_wins"]
    color = C_RED if evil_wins else C_GREEN
    winner = "💀 Ác Thắng!" if evil_wins else "⚔️ Thiện Thắng!"
    e = discord.Embed(title=f"🏹 Kết Quả Cuộc Đi Săn — {winner}", color=color)
    for g in result["guesses"]:
        player_name = g["player"].display_name if "player" in g else f"<uid:{g.get('uid')}>"
        status = "✅ Đúng" if g["correct"] else "❌ Sai"
        e.add_field(name=f"{g['role']}", value=f"{player_name} — {status}", inline=True)
    if result.get("arthur_named_first"):
        e.add_field(
            name="⚜️ Arthur Bị Gọi Tên Đầu Tiên!",
            value="Thợ Săn Mù gọi tên Arthur trước — Ác thắng theo Quy Tắc Arthur!",
            inline=False,
        )
    return e


def last_chance_embed(evil_count: int) -> discord.Embed:
    e = discord.Embed(
        title="🎯 Cơ Hội Cuối Cùng — Phe Thiện Buộc Tội",
        description=(
            f"**Người chơi phe Thiện**: mỗi người phải chỉ vào đúng **{evil_count}** người bị nghi là Ác.\n\n"
            f"Dùng: `/quest accuse @người1 @người2`\n\n"
            "⚠️ Câu trả lời của bạn **ẩn** — chỉ được tiết lộ khi tất cả đã bỏ phiếu.\n\n"
            "Nếu **tất cả** phe Thiện cùng chỉ vào **đúng tất cả** kẻ Ác → **Thiện thắng!**\n"
            "Nếu không → **Ác thắng.**"
        ),
        color=C_GOLD,
    )
    return e


def last_chance_result_embed(result: dict) -> discord.Embed:
    good_wins = result["good_wins"]
    color = C_GREEN if good_wins else C_RED
    winner = "⚔️ Thiện Thắng!" if good_wins else "💀 Ác Thắng!"
    e = discord.Embed(title=f"🎯 Kết Quả Cơ Hội Cuối Cùng — {winner}", color=color)
    evil_names = ", ".join(f"**{p.display_name}** ({p.role.name})" for p in result["evil_players"])
    e.add_field(name="Kẻ Ác Là", value=evil_names or "Không có", inline=False)
    return e


def game_over_embed(winner: str, game: "GameState") -> discord.Embed:
    if winner == "good":
        color = C_GREEN
        title = "⚔️ PHE THIỆN THẮNG — Hoàn Thành 3 Nhiệm Vụ!"
        desc = "Các Tôi Tớ Trung Thành của Arthur đã chiến thắng! Vương quốc được bình an."
    else:
        color = C_RED
        title = "💀 PHE ÁC THẮNG!"
        desc = "Các Tay Sai của Mordred đã nhấn chìm Camelot vào bóng tối…"

    e = discord.Embed(title=title, description=desc, color=color)
    reveal_lines = []
    for p, role in game.get_all_roles_reveal():
        side_icon = "⚔️" if role.side == Side.GOOD else "💀"
        reveal_lines.append(f"{side_icon} **{p.display_name}** — {role.emoji} {role.name}")
    e.add_field(name="🎭 Tiết Lộ Vai Trò", value="\n".join(reveal_lines), inline=False)
    e.set_footer(text="Cảm ơn đã chơi Quest: Avalon!")
    return e


def roles_in_play_embed(game: "GameState") -> discord.Embed:
    """Show all role cards used in this game (not who has them)."""
    from collections import Counter
    role_counts = Counter(p.role.name for p in game.players)
    good_lines = []
    evil_lines = []
    for role_name, count in role_counts.items():
        role = next(p.role for p in game.players if p.role.name == role_name)
        suffix = f" ×{count}" if count > 1 else ""
        line = f"{role.emoji} **{role_name}**{suffix}"
        if role.side == Side.GOOD:
            good_lines.append(line)
        else:
            evil_lines.append(line)
    e = discord.Embed(
        title="🎭 Các Lá Bài Trong Trận Này",
        description="Đây là các vai trò đang được sử dụng. Kiểm tra DM để biết vai của bạn!",
        color=C_GOLD,
    )
    e.add_field(name="⚔️ Phe Thiện", value="\n".join(good_lines) or "—", inline=True)
    e.add_field(name="💀 Phe Ác", value="\n".join(evil_lines) or "—", inline=True)
    e.add_field(
        name=f"👥 Tổng: {game.player_count()} người chơi",
        value=" | ".join(p.display_name for p in game.players),
        inline=False,
    )
    return e


def leader_select_embed(game: "GameState") -> discord.Embed:
    """Prompt the current leader to select next leader after a mission."""
    eligible = [
        p for p in game.players
        if not p.has_veteran and not p.has_amulet
    ]
    eligible_str = "\n".join(f"• {p.display_name}" for p in eligible) or "*(Không còn ai đủ điều kiện — cần reset veteran tokens)*"
    e = discord.Embed(
        title="👑 Chọn Người Lãnh Đạo Tiếp Theo",
        description=(
            f"**{game.leader.display_name}** hãy chọn người lãnh đạo nhiệm vụ tiếp theo:\n"
            f"`/quest nextleader @người`\n\n"
            "⛔ Những người đã từng làm Leader hoặc đang giữ Bùa Hộ Mệnh **không được** chọn."
        ),
        color=C_GOLD,
    )
    e.add_field(name="✅ Đủ điều kiện làm Leader", value=eligible_str, inline=False)
    return e
