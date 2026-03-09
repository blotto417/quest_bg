"""
views.py — Discord button UI components for Quest: Avalon.
"""
from __future__ import annotations

from typing import Callable, Awaitable, Optional
import discord


class QuestVoteView(discord.ui.View):
    """
    Sent via DM to each team member. Lets them vote Success or Fail.
    Callback is called with (user_id, success_bool).
    """

    def __init__(
        self,
        player_id: int,
        forced_success: bool,
        forced_fail: bool,
        callback: Callable[[int, bool], Awaitable[None]],
    ):
        super().__init__(timeout=300)
        self.player_id = player_id
        self.callback_fn = callback
        self.voted = False

        # Disable the button that the player cannot choose
        if forced_success:
            self.fail_btn.disabled = True
            self.fail_btn.label = "Fail (Locked 🔒)"
        if forced_fail:
            self.success_btn.disabled = True
            self.success_btn.label = "Success (Locked 🔒)"

    @discord.ui.button(label="✅ Success", style=discord.ButtonStyle.success, custom_id="vote_success")
    async def success_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_vote(interaction, True)

    @discord.ui.button(label="❌ Fail", style=discord.ButtonStyle.danger, custom_id="vote_fail")
    async def fail_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_vote(interaction, False)

    async def _handle_vote(self, interaction: discord.Interaction, success: bool):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("This vote is not for you.", ephemeral=True)
            return
        if self.voted:
            await interaction.response.send_message("You have already voted.", ephemeral=True)
            return
        self.voted = True
        for child in self.children:
            child.disabled = True
        label = "✅ Success" if success else "❌ Fail"
        await interaction.response.edit_message(
            content=f"You voted: **{label}**. Your choice has been recorded.",
            view=self,
        )
        self.stop()
        await self.callback_fn(self.player_id, success)


class ConfirmStartView(discord.ui.View):
    """Simple Yes/No confirmation for starting the game."""

    def __init__(self, host_id: int, confirm_cb: Callable[[], Awaitable[None]]):
        super().__init__(timeout=60)
        self.host_id = host_id
        self.confirm_cb = confirm_cb

    @discord.ui.button(label="▶️ Start Game", style=discord.ButtonStyle.primary)
    async def confirm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.host_id:
            await interaction.response.send_message("Only the host can start the game.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()
        await self.confirm_cb()

    @discord.ui.button(label="🗑️ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.host_id:
            await interaction.response.send_message("Only the host can cancel.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="Game cancelled.", view=self)
        self.stop()


class HuntDecisionView(discord.ui.View):
    """
    Shown to the Blind Hunter at the start of the Final Mission.
    Lets them decide to Hunt or pass to Last Chance.
    """

    def __init__(
        self,
        hunter_id: int,
        hunt_cb: Callable[[], Awaitable[None]],
        pass_cb: Callable[[], Awaitable[None]],
    ):
        super().__init__(timeout=120)
        self.hunter_id = hunter_id
        self.hunt_cb = hunt_cb
        self.pass_cb = pass_cb

    @discord.ui.button(label="🏹 I want to Hunt!", style=discord.ButtonStyle.danger)
    async def hunt_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.hunter_id:
            await interaction.response.send_message("Only the Blind Hunter can decide.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()
        await self.hunt_cb()

    @discord.ui.button(label="🤫 Stay Silent (pass to Last Chance)", style=discord.ButtonStyle.secondary)
    async def pass_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.hunter_id:
            await interaction.response.send_message("Only the Blind Hunter can decide.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()
        await self.pass_cb()
