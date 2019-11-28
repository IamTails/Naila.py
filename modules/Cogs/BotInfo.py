import psutil
import time

from datetime import datetime
from discord.ext import commands
from discord.utils import oauth_url
from utils.functions.time import get_bot_uptime
import discord

__author__ = "Kanin"
__date__ = 11 / 19 / 2019
__copyright__ = "Copyright 2019, Kanin"
__credits__ = ["Kanin"]
__license__ = "GPL v3.0"
__version__ = "1.0.0"
__maintainer__ = "Kanin"
__email__ = "im@kanin.dev"
__status__ = "Production"


class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Invite the bot or join the bots support server!")
    async def invite(self, ctx):
        """{"user": [], "bot": ["embed_links"]}"""
        perms = discord.Permissions(502656087)
        em = discord.Embed(color=await ctx.guildcolor())
        em.description = "**Support server:** https://discord.gg/fox\n" \
                         f"**Bot invite:** [Recommended perms]({oauth_url(self.bot.user.id, permissions=perms)}) |" \
                         f" [No perms]({oauth_url(self.bot.user.id)})"
        await ctx.send(embed=em)

    @commands.command(description="Various stats about the bot")
    async def stats(self, ctx):
        """{"user": [], "bot": ["embed_links"]}"""
        bot = self.bot
        text, voice, category, news = 0, 0, 0, 0
        for channel in self.bot.get_all_channels():
            if isinstance(channel, discord.TextChannel):
                if channel.is_news():
                    news += 1
                text += 1
            elif isinstance(channel, discord.VoiceChannel):
                voice += 1
            elif isinstance(channel, discord.CategoryChannel):
                category += 1
        channels = text + voice + category + news
        cpu_usage = "{0:.1f}%".format(psutil.Process().cpu_percent(interval=None))
        memory_usage = "{:.2f}Mb".format(psutil.Process().memory_full_info().uss / 1024 ** 2)
        t1 = time.perf_counter()
        async with ctx.channel.typing():
            t2 = time.perf_counter()
        em = discord.Embed(
            color=await ctx.guildcolor()
        ).add_field(
            name="Ping:",
            value=f"**{round((t2 - t1) * 1000)}ms** {ctx.emojis('utility.ping')}"
        ).add_field(
            name="Serving:",
            value=f"**Guilds:** {len(bot.guilds)} {ctx.emojis('utility.globe')}\n"
                  f"**Users:** {len(set(bot.get_all_members()))} {ctx.emojis('utility.people')}\n"
                  f"**Channels:** {channels}"
                  f"{ctx.emojis('channels.text')}/{ctx.emojis('channels.voice')}/"
                  f"{ctx.emojis('channels.category')}/{ctx.emojis('channels.news')}\n"
                  f"**Text Channels:** {text} {ctx.emojis('channels.text')}\n"
                  f"**Voice Channels:** {voice} {ctx.emojis('channels.voice')}\n"
                  f"**Category Channels:** {category} {ctx.emojis('channels.category')}\n"
                  f"**News Channels:** {news} {ctx.emojis('channels.news')}",
            inline=False
        ).add_field(
            name="System:",
            value=f"**OS:** Linux {ctx.emojis('system.linux')}\n"
                  f"**Version:** Ubuntu 16.04 {ctx.emojis('system.ubuntu')}\n"
                  f"**CPU Usage:** {cpu_usage} {ctx.emojis('system.cpu')}\n"
                  f"**Memory Usage:** {memory_usage} {ctx.emojis('system.ram')}",
            inline=False
        ).add_field(
            name="Version:",
            value=f"**Bot:** {bot.version['bot']}\n"
                  f"**Python:** {bot.version['python']} {ctx.emojis('utility.python')}\n"
                  f"**Discord.py:** {bot.version['discord.py']} {ctx.emojis('utility.discordpy')}",
            inline=False
        ).add_field(
            name="Counters:",
            value=f"**Command count:** {len(bot.commands)} {ctx.emojis('utility.abacus')}\n"
                  f"**Messages read:** {bot.counter['messages']} {ctx.emojis('utility.chat')}\n"
                  f"**Commands ran:** {bot.counter['commands_ran']} {ctx.emojis('utility.abacus')}\n"
                  f"**Foxes caught:** {bot.counter['foxes_caught']} {ctx.emojis('utility.fox')}",
            inline=False
        ).add_field(
            name="Uptime:",
            value=f"🆙**{get_bot_uptime(bot, brief=True)}**🆙",
            inline=False
        ).set_author(
            name="🦊🐾Bot stats🐾🦊",
            icon_url=bot.user.avatar_url
        ).set_footer(
            text=datetime.now().strftime(bot.config()["time_format"]),
            icon_url=bot.user.avatar_url
        )
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(BotInfo(bot))
