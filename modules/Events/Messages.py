import discord
from discord.ext import commands

from utils.database.GuildSettings import Prefixes, Check

__author__ = "Kanin"
__date__ = "11/19/2019"
__copyright__ = "Copyright 2019, Kanin"
__credits__ = ["Kanin"]
__license__ = "GPL v3.0"
__version__ = "1.0.0"
__maintainer__ = "Kanin"
__email__ = "im@kanin.dev"
__status__ = "Production"


class Messages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        ctx = await self.bot.get_context(message)
        # Adding some statistics
        self.bot.counter["messages"] += 1
        # Checking if the author of the message is a bot
        if message.author.bot:
            return
        if not isinstance(message.channel, discord.DMChannel):
            await Check().main(ctx.bot, ctx.guild)
        # Mention the bot to list prefixes
        mentions = [self.bot.user.mention]
        if not isinstance(message.channel, discord.DMChannel):
            mentions.append(message.guild.me.mention)
        if message.content in mentions:
            await ctx.send(f"My prefixes here are:\n{await Prefixes(ctx).list()}")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        message, command = ctx.message, ctx.command

        cmd = command.qualified_name.replace(" ", "_")
        self.bot.commands_used[cmd] += 1
        self.bot.counter["commands_ran"] += 1

        destination = "Private Message" if isinstance(ctx.channel, discord.DMChannel) else \
            f"#{message.channel.name} ({message.guild.name})"

        self.bot.log.info(f"{message.author} in {destination}: {message.content}")


def setup(bot):
    bot.add_cog(Messages(bot))
