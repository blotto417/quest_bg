"""
bot.py — Quest: Avalon Discord Bot (main entry point).

Commands:
  /quest new     — Start a new game lobby in this channel
  /quest join    — Join the lobby
  /quest start   — Start the game (host only, 4-10 players)
  /quest status  — Show current game state
  /quest pick    — Leader picks team
  /quest seal    — Leader applies Magic Seal
  /quest vote    — Submit quest card (Success/Fail) — also done via DM buttons
  /quest nextleader — Leader selects next leader (post-mission)
  /quest amulet  — Leader gives Amulet to a player (amulet phase)
  /quest check   — Amulet holder checks a player's loyalty (amulet phase)
  /quest accuse  — Good player accuses Evil suspects (Last Chance)
  /quest hunt    — Blind Hunter names 2 Good players by role (Hunt)
  /quest cancel  — Cancel the game (host only)
"""

import asyncio
import os
import logging

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from game_state import GameState, Phase
from roles import Side, ALL_ROLES
import embeds
import views

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("quest_bot")

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# In-memory store: channel_id → GameState
games: dict[int, GameState] = {}


# ─── Helper utilities ──────────────────────────────────────────────────────────

def get_game(channel_id: int, require_phase: Phase | None = None) -> tuple[GameState | None, str]:
    """Fetch game for a channel, optionally requiring a specific phase."""
    game = games.get(channel_id)
    if not game:
        return None, "❌ No active game in this channel. Use `/quest new` to start one."
    if require_phase and game.phase != require_phase:
        return None, f"❌ That command is not available in the current phase (`{game.phase.name}`)."
    return game, ""


async def send_role_dms(game: GameState):
    """Send each player their role card via DM."""
    failed = []
    for pi in game.players:
        night_info = game.get_night_info(pi)
        embed = embeds.role_card_embed(pi, night_info)
        try:
            await pi.member.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            failed.append(pi.display_name)
    if failed:
        await game.channel.send(
            f"⚠️ Could not DM role cards to: **{', '.join(failed)}**\n"
            "Please make sure DMs are open from server members."
        )


async def send_quest_vote_dms(game: GameState):
    """DM each team member their voting buttons."""
    for pi in game.team:
        forced_success = game.is_forced_success(pi)
        forced_fail = game.is_forced_fail(pi)

        async def vote_callback(user_id: int, success: bool, _pi=pi):
            g = games.get(game.channel.id)
            if not g or g.phase != Phase.QUEST:
                return
            ok, err = g.record_vote(user_id, success)
            if not ok:
                try:
                    await _pi.member.send(f"❌ Your vote was rejected: {err}")
                except Exception:
                    pass
                return
            log.info("Vote recorded for %s: %s", _pi.display_name, "Success" if success else "Fail")
            # Check if all votes are in
            if g.all_votes_in():
                await resolve_quest_results(g)

        view = views.QuestVoteView(
            player_id=pi.user_id,
            forced_success=forced_success,
            forced_fail=forced_fail,
            callback=vote_callback,
        )
        card_label = "Success (forced)" if forced_success else ("Fail (forced)" if forced_fail else "Success or Fail")
        try:
            await pi.member.send(
                f"🗡️ **Quest {game.current_mission + 1}** — Cast your card!\n"
                f"*(You {'**must**' if forced_success or forced_fail else 'may'} play {card_label})*",
                view=view,
            )
        except (discord.Forbidden, discord.HTTPException):
            await game.channel.send(
                f"⚠️ Could not DM **{pi.display_name}** for their quest vote. "
                "Please make sure DMs are open!"
            )


async def resolve_quest_results(game: GameState):
    """Called when all quest votes are in; tally and post results."""
    result = game.resolve_quest()
    embed = embeds.quest_result_embed(result)
    await game.channel.send(embed=embed)

    if result["winner"] == "good":
        # Good wins — game over
        end_embed = embeds.game_over_embed("good", game)
        await game.channel.send(embed=end_embed)
        del games[game.channel.id]
        return

    if result["winner"] == "evil_final":
        # Trigger final mission discussion
        game.start_final_mission()
        await game.channel.send(embed=embeds.discussion_embed())
        # Check for Blind Hunter
        hunter = next((p for p in game.players if p.role and p.role.can_hunt), None)
        if hunter:
            game.start_hunt()
            embed_hunt = embeds.hunt_prompt_embed(hunter)

            async def on_hunt():
                await game.channel.send(
                    f"🎹 **{hunter.display_name}** đã chọn **Đi Săn**!\n"
                    f"Dùng: `/quest hunt <vai_trò_1> @người1 <vai_trò_2> @người2`\n\n"
                    f"Không ai khác được nói trong Cuộc Đi Săn."
                )

            async def on_pass():
                game.start_last_chance()
                evil_count = sum(1 for p in game.players if p.role.side == Side.EVIL and not p.revealed_evil)
                await game.channel.send(embed=embeds.last_chance_embed(evil_count))

            hunt_view = views.HuntDecisionView(
                hunter_id=hunter.user_id,
                hunt_cb=on_hunt,
                pass_cb=on_pass,
            )
            try:
                await hunter.member.send(embed=embed_hunt, view=hunt_view)
                await game.channel.send(
                    f"🎹 **Thợ Săn Mù** đã được thông báo qua DM. Chờ họ quyết định."
                )
            except (discord.Forbidden, discord.HTTPException):
                await game.channel.send(
                    f"⚠️ Không gửi được DM cho Thợ Săn Mù. "
                    f"**{hunter.display_name}**: dùng `/quest hunt` để Săn hoặc im lặng để qua Cơ Hội Cuối Cùng."
                )
        else:
            # No Blind Hunter — go straight to Last Chance
            game.start_last_chance()
            evil_count = sum(1 for p in game.players if p.role.side == Side.EVIL and not p.revealed_evil)
            await game.channel.send(embed=embeds.last_chance_embed(evil_count))
        return

    # Advance to next mission — show leader selection prompt first
    info = game.advance_to_next_mission()
    if info["amulet_available"]:
        await game.channel.send(embed=embeds.leader_select_embed(game))
        await game.channel.send(embed=embeds.amulet_embed(game))
    else:
        await game.channel.send(embed=embeds.leader_select_embed(game))


# ─── Slash Command Group ────────────────────────────────────────────────────────

class QuestGroup(app_commands.Group):
    """All Quest: Avalon commands live under /quest."""

    # ── /quest new ──────────────────────────────────────────────────────────
    @app_commands.command(name="new", description="Start a new Quest: Avalon game lobby in this channel.")
    async def new(self, interaction: discord.Interaction):
        cid = interaction.channel_id
        if cid in games:
            await interaction.response.send_message(
                "❌ Đã có trận đang chạy trong kênh này. Dùng `/quest cancel` để kết thúc trước.",
                ephemeral=True,
            )
            return
        channel = interaction.channel or bot.get_channel(interaction.channel_id)
        game = GameState(channel=channel, host=interaction.user)
        game.add_player(interaction.user)
        games[cid] = game
        await interaction.response.send_message(embed=embeds.lobby_embed(game))

    # ── /quest join ─────────────────────────────────────────────────────────
    @app_commands.command(name="join", description="Join the Quest: Avalon lobby.")
    async def join(self, interaction: discord.Interaction):
        game, err = get_game(interaction.channel_id, require_phase=Phase.LOBBY)
        if not game:
            await interaction.response.send_message(err, ephemeral=True)
            return
        ok = game.add_player(interaction.user)
        if not ok:
            await interaction.response.send_message("❌ Bạn đã tham gia hoặc phòng đã đầy.", ephemeral=True)
            return
        await interaction.response.send_message(embed=embeds.lobby_embed(game))

    # ── /quest start ─────────────────────────────────────────────────────────
    @app_commands.command(name="start", description="Start the game (host only, 4–10 players).")
    async def start(self, interaction: discord.Interaction):
        game, err = get_game(interaction.channel_id, require_phase=Phase.LOBBY)
        if not game:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if interaction.user.id != game.host.id:
            await interaction.response.send_message("❌ Chỉ host mới có thể bắt đầu.", ephemeral=True)
            return
        n = game.player_count()
        if n < 2 or n > 10:
            await interaction.response.send_message(
                f"❌ Cần 2–10 người để bắt đầu. Hiện có {n} người.", ephemeral=True
            )
            return

        await interaction.response.defer()
        try:
            game.start_game()
            await send_role_dms(game)
            await interaction.followup.send(
                f"🎭 **Trò chơi bắt đầu với {n} người!** Thẻ vai trò đã gửi qua DM — giữ bí mật!"
            )
            await game.channel.send(embed=embeds.roles_in_play_embed(game))
            await game.channel.send(embed=embeds.team_build_embed(game))
        except Exception as e:
            log.exception("Lỗi khi bắt đầu trò chơi")
            await interaction.followup.send(f"❌ Lỗi khi bắt đầu: {e}")

    # ── /quest status ─────────────────────────────────────────────────────────
    @app_commands.command(name="status", description="Show the current game state.")
    async def status(self, interaction: discord.Interaction):
        game, err = get_game(interaction.channel_id)
        if not game:
            await interaction.response.send_message(err, ephemeral=True)
            return
        await interaction.response.send_message(embed=embeds.status_embed(game))

    # ── /quest pick ──────────────────────────────────────────────────────────
    @app_commands.command(name="pick", description="Leader: pick team members for this quest.")
    @app_commands.describe(
        player1="Team member 1 (required)",
        player2="Team member 2 (required)",
        player3="Team member 3 (optional)",
        player4="Team member 4 (optional)",
        player5="Team member 5 (optional)",
    )
    async def pick(
        self,
        interaction: discord.Interaction,
        player1: discord.Member,
        player2: discord.Member,
        player3: discord.Member | None = None,
        player4: discord.Member | None = None,
        player5: discord.Member | None = None,
    ):
        game, err = get_game(interaction.channel_id, require_phase=Phase.TEAM_BUILD)
        if not game:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if interaction.user.id not in game.player_map:
            await interaction.response.send_message("❌ Bạn không ở trong trò chơi này.", ephemeral=True)
            return

        picks = [m for m in [player1, player2, player3, player4, player5] if m is not None]
        ids = [m.id for m in picks]
        ok, err2 = game.set_team(ids)
        if not ok:
            await interaction.response.send_message(f"❌ {err2}", ephemeral=True)
            return

        team_names = ", ".join(f"**{p.display_name}**" for p in game.team)
        await interaction.response.send_message(
            f"✅ **{interaction.user.display_name}** đã chọn đội: {team_names}\n\n"
            f"Tiếp theo: phong ấn với `/quest seal @người`, rồi bắt đầu với `/quest go`."
        )

    # ── /quest seal ──────────────────────────────────────────────────────────
    @app_commands.command(name="seal", description="Leader: apply the Magic Seal to a player.")
    @app_commands.describe(player="The player to seal (can be yourself)")
    async def seal(self, interaction: discord.Interaction, player: discord.Member):
        game, err = get_game(interaction.channel_id, require_phase=Phase.TEAM_BUILD)
        if not game:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if interaction.user.id not in game.player_map:
            await interaction.response.send_message("❌ Bạn không ở trong trò chơi này.", ephemeral=True)
            return
        if not game.team:
            await interaction.response.send_message("❌ Hãy chọn đội trước với `/quest pick`.", ephemeral=True)
            return
        ok, err2 = game.set_magic_seal(player.id)
        if not ok:
            await interaction.response.send_message(f"❌ {err2}", ephemeral=True)
            return
        await interaction.response.send_message(
            f"🔮 **Con Dấu Ma Thuật** đặt lên **{player.display_name}**.\n"
            f"Họ không thể chơi Thất Bại trong nhiệm vụ này.\n\n"
            f"Sẵn sàng? Bắt đầu với `/quest go`."
        )

    # ── /quest autopick ───────────────────────────────────────────────────────
    @app_commands.command(name="autopick", description="Bot tự chọn ngẫu nhiên đội và con dấu, rồi bắt đầu nhiệm vụ.")
    async def autopick(self, interaction: discord.Interaction):
        game, err = get_game(interaction.channel_id, require_phase=Phase.TEAM_BUILD)
        if not game:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if interaction.user.id not in game.player_map:
            await interaction.response.send_message("❌ Bạn không ở trong trò chơi này.", ephemeral=True)
            return
        game.auto_pick_team()
        game.begin_quest_phase()
        team_names = ", ".join(
            f"**{p.display_name}**{'🔮' if p.has_magic_seal else ''}"
            for p in game.team
        )
        await interaction.response.send_message(
            f"🎲 Bot đã chọn ngẫu nhiên đội: {team_names}\n_(🔮 = Con Dấu Ma Thuật)_\n\nĐang gửi thẻ nhiệm vụ qua DM..."
        )
        await send_quest_vote_dms(game)

    # ── /quest go ────────────────────────────────────────────────────────────
    @app_commands.command(name="go", description="Bắt đầu nhiệm vụ. Tự động chọn đội nếu chưa chọn.")
    async def go(self, interaction: discord.Interaction):
        game, err = get_game(interaction.channel_id, require_phase=Phase.TEAM_BUILD)
        if not game:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if interaction.user.id not in game.player_map:
            await interaction.response.send_message("❌ Bạn không ở trong trò chơi này.", ephemeral=True)
            return
        # Auto-pick if not manually done
        if not game.team or not game.magic_seal_target:
            game.auto_pick_team()
        game.begin_quest_phase()
        await interaction.response.send_message(embed=embeds.quest_start_embed(game))
        await send_quest_vote_dms(game)

    # ── /quest vote ──────────────────────────────────────────────────────────
    @app_commands.command(name="vote", description="Cast your quest card (Success or Fail). Use in DM or here.")
    @app_commands.describe(card="Your choice: success or fail")
    @app_commands.choices(card=[
        app_commands.Choice(name="✅ Success", value="success"),
        app_commands.Choice(name="❌ Fail", value="fail"),
    ])
    async def vote(self, interaction: discord.Interaction, card: app_commands.Choice[str]):
        # Work in both DM and channel
        game = None
        if interaction.guild:
            game = games.get(interaction.channel_id)
        else:
            # DM context — find the player's game
            for g in games.values():
                if interaction.user.id in g.player_map:
                    game = g
                    break
        if not game:
            await interaction.response.send_message("❌ You are not in an active game.", ephemeral=True)
            return
        if game.phase != Phase.QUEST:
            await interaction.response.send_message("❌ No quest is active right now.", ephemeral=True)
            return

        success = card.value == "success"
        ok, err = game.record_vote(interaction.user.id, success)
        if not ok:
            await interaction.response.send_message(f"❌ {err}", ephemeral=True)
            return

        await interaction.response.send_message(
            "✅ Phiếu của bạn đã được ghi nhận. Chờ các thành viên còn lại bỏ phiếu.",
            ephemeral=True,
        )
        if game.all_votes_in():
            await resolve_quest_results(game)

    # ── /quest nextleader ─────────────────────────────────────────────────────
    @app_commands.command(name="nextleader", description="Chọn người lãnh đạo nhiệm vụ tiếp theo.")
    @app_commands.describe(player="Người sẽ làm Leader tiếp theo")
    async def nextleader(self, interaction: discord.Interaction, player: discord.Member):
        game, err = get_game(interaction.channel_id)
        if not game:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if game.phase not in (Phase.TEAM_BUILD, Phase.AMULET):
            await interaction.response.send_message("❌ Lệnh này không khả dụng lúc này.", ephemeral=True)
            return
        if interaction.user.id != game.leader.user_id:
            await interaction.response.send_message("❌ Chỉ Leader hiện tại mới chọn Leader tiếp theo.", ephemeral=True)
            return
        ok, err2 = game.assign_next_leader(player.id)
        if not ok:
            await interaction.response.send_message(f"❌ {err2}", ephemeral=True)
            return
        await interaction.response.send_message(
            f"👑 **{player.display_name}** là Người Lãnh Đạo tiếp theo và đã nhận Thẻ Cựu Chiến Binh."
        )
        # After leader is chosen, show team-build embed (if not waiting for amulet)
        if game.phase == Phase.TEAM_BUILD:
            await game.channel.send(embed=embeds.team_build_embed(game))

    # ── /quest amulet ─────────────────────────────────────────────────────────
    @app_commands.command(name="amulet", description="Leader: give the Amulet to a player (Amulet phase only).")
    @app_commands.describe(player="The player who receives the Amulet")
    async def amulet(self, interaction: discord.Interaction, player: discord.Member):
        game, err = get_game(interaction.channel_id, require_phase=Phase.AMULET)
        if not game:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if interaction.user.id != game.leader.user_id:
            await interaction.response.send_message("❌ Only the Leader assigns the Amulet.", ephemeral=True)
            return
        ok, err2 = game.assign_amulet_holder(interaction.user.id, player.id)
        if not ok:
            await interaction.response.send_message(f"❌ {err2}", ephemeral=True)
            return

        await interaction.response.send_message(
            f"🔮 **{player.display_name}** now holds the **Amulet**.\n"
            f"Use `/quest check @player` to secretly check someone's loyalty before the next mission starts.\n"
            f"Then use `/quest nextleader @player` if not done, and `/quest advance` to proceed."
        )

    # ── /quest check ─────────────────────────────────────────────────────────
    @app_commands.command(name="check", description="Amulet holder: secretly check a player's loyalty.")
    @app_commands.describe(player="The player to check")
    async def check(self, interaction: discord.Interaction, player: discord.Member):
        game, err = get_game(interaction.channel_id, require_phase=Phase.AMULET)
        if not game:
            await interaction.response.send_message(err, ephemeral=True)
            return
        ok, err2, shown_side = game.use_amulet(interaction.user.id, player.id)
        if not ok:
            await interaction.response.send_message(f"❌ {err2}", ephemeral=True)
            return

        holder = game.player_map[interaction.user.id]
        target = game.player_map[player.id]
        embed = embeds.amulet_result_embed(holder, target, shown_side)
        # Send privately to amulet holder only
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message(
                f"🔮 **{interaction.user.display_name}** used the Amulet to check **{player.display_name}**. Result sent via DM.",
                ephemeral=False,
            )
        except (discord.Forbidden, discord.HTTPException):
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /quest advance ────────────────────────────────────────────────────────
    @app_commands.command(name="advance", description="Leader: advance to the next mission after Amulet phase.")
    async def advance(self, interaction: discord.Interaction):
        game, err = get_game(interaction.channel_id, require_phase=Phase.AMULET)
        if not game:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if interaction.user.id != game.leader.user_id:
            await interaction.response.send_message("❌ Only the Leader can advance.", ephemeral=True)
            return
        if not game.player_map.get(interaction.user.id, None) or not any(
            p.is_leader and p.user_id != game.leader.user_id for p in game.players
        ):
            # Ensure next leader was chosen
            pass  # next leader assignment is their responsibility; we allow advancing

        game.current_mission += 1
        game.phase = Phase.TEAM_BUILD
        await interaction.response.send_message(embed=embeds.team_build_embed(game))

    # ── /quest accuse ─────────────────────────────────────────────────────────
    @app_commands.command(name="accuse", description="Last Chance: point at 2 suspected Evil players.")
    @app_commands.describe(player1="Suspect 1", player2="Suspect 2")
    async def accuse(
        self,
        interaction: discord.Interaction,
        player1: discord.Member,
        player2: discord.Member,
    ):
        game, err = get_game(interaction.channel_id, require_phase=Phase.LAST_CHANCE)
        if not game:
            await interaction.response.send_message(err, ephemeral=True)
            return
        pi = game.player_map.get(interaction.user.id)
        if not pi:
            await interaction.response.send_message("❌ Bạn không ở trong trò chơi này.", ephemeral=True)
            return
        if pi.role.side != Side.GOOD:
            await interaction.response.send_message("❌ Chỉ người chơi phe Thiện mới tham gia Cơ Hội Cuối Cùng.", ephemeral=True)
            return

        ok, err2 = game.record_last_chance_accusation(interaction.user.id, [player1.id, player2.id])
        if not ok:
            await interaction.response.send_message(f"❌ {err2}", ephemeral=True)
            return

        # Hidden — only the accuser sees their own choice
        await interaction.response.send_message(
            f"🎯 Bạn đã chỉ vào **{player1.display_name}** và **{player2.display_name}**. *(Chỉ bạn thấy tin này)*",
            ephemeral=True,
        )

        # Announce in channel that this person voted (without revealing targets)
        await game.channel.send(
            f"🎯 **{interaction.user.display_name}** đã bỏ phiếu."
        )

        # Check if all Good players have accused
        good_players = [p for p in game.players if p.role.side == Side.GOOD]
        accused_count = len(game.last_chance_accusations)
        if accused_count >= len(good_players):
            result = game.resolve_last_chance()
            await game.channel.send(embed=embeds.last_chance_result_embed(result))
            winner = "good" if result["good_wins"] else "evil"
            await game.channel.send(embed=embeds.game_over_embed(winner, game))
            del games[game.channel.id]

    # ── /quest hunt ───────────────────────────────────────────────────────────
    @app_commands.command(name="hunt", description="Blind Hunter: name 2 Good players by their role to win.")
    @app_commands.describe(
        role1="First role name (e.g. 'Duke')",
        player1="Player you think has role1",
        role2="Second role name (e.g. 'Cleric')",
        player2="Player you think has role2",
    )
    async def hunt(
        self,
        interaction: discord.Interaction,
        role1: str,
        player1: discord.Member,
        role2: str,
        player2: discord.Member,
    ):
        game, err = get_game(interaction.channel_id, require_phase=Phase.HUNT)
        if not game:
            await interaction.response.send_message(err, ephemeral=True)
            return
        pi = game.player_map.get(interaction.user.id)
        if not pi or not pi.role.can_hunt:
            await interaction.response.send_message("❌ Only the Blind Hunter can initiate The Hunt.", ephemeral=True)
            return

        guesses = [(role1, player1.id), (role2, player2.id)]
        result = game.resolve_hunt(guesses)
        await interaction.response.send_message(embed=embeds.hunt_result_embed(result))
        winner = result["winner"]
        await game.channel.send(embed=embeds.game_over_embed(winner, game))
        del games[game.channel.id]

    # ── /quest cancel ─────────────────────────────────────────────────────────
    @app_commands.command(name="cancel", description="Cancel the current game (host only).")
    async def cancel(self, interaction: discord.Interaction):
        game, err = get_game(interaction.channel_id)
        if not game:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if interaction.user.id != game.host.id:
            await interaction.response.send_message("❌ Chỉ host mới có thể hủy trò chơi.", ephemeral=True)
            return
        del games[interaction.channel_id]
        await interaction.response.send_message("🗑️ Trò chơi đã bị hủy. Dùng `/quest new` để tạo trận mới.")

    # ── /quest roles ──────────────────────────────────────────────────────────
    @app_commands.command(name="roles", description="List all available roles and their descriptions.")
    async def roles(self, interaction: discord.Interaction):
        good_lines = []
        evil_lines = []
        for role in ALL_ROLES.values():
            line = f"{role.emoji} **{role.name}** — {role.description.splitlines()[0]}"
            if role.side == Side.GOOD:
                good_lines.append(line)
            else:
                evil_lines.append(line)

        embed = discord.Embed(title="⚔️ Quest: Avalon — All Roles", color=0xF4C430)
        embed.add_field(name="⚔️ Good", value="\n".join(good_lines), inline=False)
        embed.add_field(name="💀 Evil", value="\n".join(evil_lines), inline=False)
        embed.set_footer(text="All optional roles replace standard Good or Evil slots.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /quest help ───────────────────────────────────────────────────────────
    @app_commands.command(name="help", description="Show a quick game guide.")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚔️ Quest: Avalon — How to Play",
            color=0xF4C430,
            description=(
                "**Quest: Avalon** is a social deduction game of loyalty and deception.\n\n"
                "**Good** wins by completing 3 Quests, or correctly identifying ALL Evil in Last Chance.\n"
                "**Evil** wins by failing 3 Quests, or if the Blind Hunter correctly names 2 Good by role.\n"
            ),
        )
        embed.add_field(
            name="🎮 Quick Start",
            value=(
                "1. `/quest new` — Open a lobby\n"
                "2. `/quest join` — Players join (4–10 players)\n"
                "3. `/quest start` — Host starts; **check your DMs for your role!**\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="🛡️ Each Round",
            value=(
                "4. Leader: `/quest pick @p1 @p2 ...` — Choose a team\n"
                "5. Leader: `/quest seal @player` — Place the Magic Seal\n"
                "6. Leader: `/quest go` — Start the quest\n"
                "7. Team members: vote via **DM buttons** (or `/quest vote`)\n"
                "8. Leader: `/quest nextleader @player` then `/quest advance` (if amulet phase)\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="🏁 Endgame",
            value=(
                "• After 3 fails → **Final Discussion** → Blind Hunter may **Hunt** or pass\n"
                "• If no Hunt → All Good players `/quest accuse @p1 @p2` for **Last Chance**\n"
            ),
            inline=False,
        )
        embed.set_footer(text="Use /quest roles to see all role descriptions.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ─── Bot events ────────────────────────────────────────────────────────────────

# Register command group once at module level (not inside on_ready to avoid duplicates)
_quest_group = QuestGroup(name="quest", description="Quest: Avalon board game commands")
tree.add_command(_quest_group)


@bot.event
async def on_ready():
    await tree.sync()
    log.info("Quest: Avalon bot is online as %s", bot.user)
    log.info("Slash commands synced globally.")


@bot.event
async def on_guild_join(guild: discord.Guild):
    """Sync slash commands when joining a new guild."""
    await tree.sync(guild=guild)


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN not set in .env file. Copy .env.example to .env and add your token.")
    bot.run(TOKEN)
