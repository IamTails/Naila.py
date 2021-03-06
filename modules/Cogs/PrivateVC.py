import asyncio

import discord
from discord.ext import commands

from utils.ctx import CustomContext
from utils.database import PrivateVCs

__author__ = "Kanin"
__date__ = "12/23/2019"
__copyright__ = "Copyright 2019, Kanin"
__credits__ = ["Kanin"]
__license__ = "GPL v3.0"
__version__ = "0.0.1"
__maintainer__ = "Kanin"
__email__ = "im@kanin.dev"
__status__ = "Development"


class PrivateVC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queued = []

    @commands.group(aliases=["pvc"])
    async def privatevc(self, ctx: CustomContext):
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @privatevc.command(name="add")
    async def privatevc_add(self, ctx: CustomContext, *, member: discord.Member):
        data = await PrivateVCs.fetch_data(self.bot, ctx.author)
        if not data:
            return await ctx.send_error("You don't have a private Voice Channel!")
        tc: discord.TextChannel = ctx.guild.get_channel(data["textchannel_id"])
        vc: discord.VoiceChannel = ctx.guild.get_channel(data["voicechannel_id"])
        if not tc:
            return await ctx.send_error("You must run this in the guild your channel is in!")
        if ctx.channel.id != data["textchannel_id"]:
            return await ctx.send_error("You must use this command in your private channel!")
        if member.permissions_in(tc).read_messages:
            return await ctx.send_error("That member already has access!")
        overwrites = {
            **tc.overwrites,
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True)
        }
        await tc.edit(overwrites=overwrites)
        await vc.edit(overwrites=overwrites)
        await ctx.send(f"{member.mention} now has access to your channels!")

    @privatevc.command(name="remove")
    async def privatevc_remove(self, ctx: CustomContext, *, member: discord.Member):
        data = await PrivateVCs.fetch_data(self.bot, ctx.author)
        if not data:
            return await ctx.send_error("You don't have a private Voice Channel!")
        tc: discord.TextChannel = ctx.guild.get_channel(data["textchannel_id"])
        vc: discord.VoiceChannel = ctx.guild.get_channel(data["voicechannel_id"])
        if not tc:
            return await ctx.send_error("You must run this in the guild your channel is in!")
        if ctx.channel.id != data["textchannel_id"]:
            return await ctx.send_error("You must use this command in your private channel!")
        if not member.permissions_in(tc).read_messages:
            return await ctx.send_error("That member doesn't have access!")
        overwrites = {
            **tc.overwrites,
            member: discord.PermissionOverwrite(read_messages=False, send_messages=False, connect=False)
        }
        await tc.edit(overwrites=overwrites)
        await vc.edit(overwrites=overwrites)
        await ctx.send(f"{member.mention} no longer has access to your channels!")

    async def clear_data(self, member: discord.Member, guild: discord.Guild):
        if member.id in self.queued:
            return
        data = await PrivateVCs.fetch_data(self.bot, member)
        if not data:
            return
        self.queued.append(member.id)
        await asyncio.sleep(10)
        if member.voice is not None and member.voice.channel.id == data["voicechannel_id"]:
            self.queued.remove(member.id)
            return
        vc: discord.VoiceChannel = guild.get_channel(data["voicechannel_id"])
        tc: discord.TextChannel = guild.get_channel(data["textchannel_id"])
        await vc.delete(reason="User left private vc")
        await tc.delete(reason="User left private vc")
        await PrivateVCs.update_data(self.bot, member)
        self.queued.remove(member.id)

    @commands.Cog.listener()
    async def on_voice_state_update(
            self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        guild: discord.Guild = member.guild
        if after.channel is not None:
            settings = await PrivateVCs.fetch_settings(self.bot, guild)
            data = await PrivateVCs.fetch_data(self.bot, member)
            if data:
                if after.channel.id == data["voicechannel_id"]:
                    return
                return await self.clear_data(member, guild)
            if settings["vc_enabled"] and after.channel.id == settings["default_vc_id"]:
                category: discord.CategoryChannel = guild.get_channel(settings["category_id"])
                if not category:
                    await PrivateVCs.reset_settings(self.bot, guild)
                    return
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    member: discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True)
                }
                vc: discord.VoiceChannel = \
                    await category.create_voice_channel(f"{member.name}'s channel", overwrites=overwrites)
                tc: discord.TextChannel = \
                    await category.create_text_channel(f"{member.name}s-channel", overwrites=overwrites)
                await PrivateVCs.add_data(self.bot, member, guild, tc, vc)
                await member.move_to(vc, reason="User created private channel")
                info = f"To add someone to your channel use: `n!pvc add <Member>`\n\n" \
                       f"To remove someone from your channel use: `n!pvc remove <Member>`\n\n" \
                       f"Leave your voice channel and after 10 seconds your channels will be closed."
                em = discord.Embed(color=self.bot.color, description=info)
                em.set_author(name="Welcome to your private channel!")
                return await tc.send(content=member.mention, embed=em)
        await self.clear_data(member, guild)


def setup(bot):
    bot.add_cog(PrivateVC(bot))
