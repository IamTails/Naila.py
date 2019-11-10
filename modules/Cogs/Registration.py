import asyncio
from datetime import datetime

import discord
from discord.ext import commands
from rethinkdb import r

from utils.checks import checks
from utils.checks.bot_checks import can_manage_user

# TODO: Make registration great again

roles = [
    "He/Him", "She/Her", "They/Them", "Mention", "No Mention", "18+", "<18",
    "Registered", "DMs NOT Allowed", "DMs Allowed", "Ask to DM"
]

default = {
    "enabled": False,
    "role": "Registered",
    "age": {"enabled": True, "ban_age": 12, "roles": {"over": "18+", "under": "<18"}},
    "output": 0000000000,
    "questions": [
        {
            "question": "What is your preferred pronoun?",
            "short": "Pronoun:",
            "options": {
                "he/him": {"aliases": ["male", "he", "him"], "role": "He/Him"},
                "they/them": {"aliases": ["they", "them"], "role": "They/Them"},
                "she/her": {"aliases": ["female", "she", "her"], "role": "She/Her"}
            }
        },
        {
            "question": "Are you okay with being Directly Messaged?",
            "short": "DMs open:",
            "options": {
                "yes": {"aliases": [], "role": "DMs Allowed"},
                "no": {"aliases": [], "role": "DMs NOT Allowed"},
                "ask": {"aliases": [], "role": "Ask to DM"}
            }
        },
        {
            "question": "Are you okay with being mentioned?",
            "short": "Mentions:",
            "options": {
                "yes": {"aliases": [], "role": "Mention"},
                "no": {"aliases": [], "role": "No Mention"}
            }
        }
    ]
}


class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    @commands.group(case_insensitive=True, description="Registration management")
    async def setreg(self, ctx):
        """{"permissions": {"user": ["manage_guild"], "bot": ["embed_links"]}}"""
        if not ctx.invoked_subcommand:
            return await ctx.group_help()

    @setreg.command(description="Set the output channel")
    async def channel(self, ctx, channel: discord.TextChannel = None):
        """{"permissions": {"user": ["manage_guild"], "bot": ["embed_links"]}}"""
        if not channel:
            channel = ctx.channel
        db = await r.table("Registration").get(str(ctx.guild.id)).run(self.bot.conn)
        db["channel"] = str(channel.id)
        await r.table("Registration").insert(db, conflict="update").run(self.bot.conn)
        await ctx.send(f"Set the channel {channel.mention} as the output for registration.")

    @setreg.command(description="Toggle registration")
    async def toggle(self, ctx):
        """{"permissions": {"user": ["manage_guild"], "bot": ["embed_links"]}}"""
        db = await r.table("Registration").get(str(ctx.guild.id)).run(self.bot.conn)
        db["enabled"] = not db["enabled"]
        await r.table("Registration").insert(db, conflict="update").run(self.bot.conn)
        if db["enabled"]:
            await ctx.send("Registration enabled.")
        else:
            await ctx.send("Registration disabled.")

    @setreg.command(description="Create the roles required for registration")
    async def roles(self, ctx):
        """{"permissions": {"user": ["manage_guild"], "bot": ["embed_links", "manage_roles"]}}"""
        guild = ctx.guild

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        try:
            await ctx.send("This will create the roles needed for this cog to function.\n```md\n"
                           "[Pronoun Roles](He/Him, She/Her, They/Them)\n"
                           "[DM Roles](DMs Allowed, DMs NOT Allowed, Ask to DM)\n"
                           "[Mention](Mention, No Mention)\n"
                           "[Misc Roles](18+, Registered, <18)\n"
                           "These roles are required for the cog to function correctly.\n"
                           "DO NOT CHANGE THE NAME OF THESE ROLES\n"
                           "They will be made with no permissions. You can modify this later through Role"
                           " Management if you "
                           "Need/Want to.\nDo you wish to continue? [This command will time out in 60s]```")
            try:
                setrole = await ctx.bot.wait_for("message", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                return await ctx.send("Timed out")
            if setrole.content.lower() == "no":
                await ctx.send("Okay, this must be done before the command will work correctly!")
            elif setrole.content.lower() == "yes":
                created = 0
                await ctx.send("Okay, this will just take a moment")
                for role in roles:
                    check = discord.utils.get(guild.roles, name=role)
                    if check not in guild.roles:
                        await guild.create_role(name=role)
                        created += 1
                await ctx.send(f"All done! Created {created} roles.")
            else:
                await ctx.send("You have entered an invalid response. Valid responses include `yes` and `no`.")
        except (discord.HTTPException, discord.Forbidden):
            await ctx.send("Creation of roles has failed, The most common problem is that I do not have Manage Roles "
                           "Permissions on the server. Please check this and try again.")

    @setreg.command(name="autoban",
                    description="Set the age in which the bot will ban the user if they are less than (Default: 13)")
    async def setreg_autoban(self, ctx, age: int):
        """{"permissions": {"user": ["manage_guild"], "bot": ["embed_links", "ban_members"]}}"""
        guild = ctx.guild
        db = await r.table("Registration").get(str(guild.id)).run(self.bot.conn)
        if age < 13:
            age = 13
            await ctx.send("You tried to set the age lower than the minimum (13) so I have set it to 13!")
        db["autoban_age"] = age
        await r.table("Registration").insert(db, conflict="update").run(self.bot.conn)
        await ctx.send(f"I will now try to ban users who say they are less than {age}!")

    @commands.guild_only()
    @commands.command(description="Unregister, allowing you to register again!")
    async def unregister(self, ctx):
        """{"permissions": {"user": [], "bot": ["embed_links", "manage_roles"]}}"""
        guild, author = ctx.guild, ctx.author
        if not can_manage_user(ctx, author):
            return await ctx.send("I don't have a role above you which means I can't manage your roles,"
                                  " please have someone with permissions move my role up!")
        remove = []
        for role in roles:
            check = discord.utils.get(guild.roles, name=role)
            if check in author.roles:
                remove.append(check)
        await author.remove_roles(*remove, reason="[ Registration ] User unregistered")
        await ctx.send("Done, you may now register again!")

    @commands.guild_only()
    @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.command(description="Register in this guild!")
    async def register(self, ctx):
        """{"permissions": {"user": [], "bot": ["embed_links", "manage_roles"]}}"""
        guild, author = ctx.guild, ctx.author
        # TODO: postgres
        db = await r.table("Registration").get(str(guild.id)).run(self.bot.conn)

        # Few checks to make sure registration will work properly
        await self.registration_checks(ctx)
        ch = guild.get_channel(int(db["channel"]))

        # Setting default embeds and creating role list
        out = discord.Embed(color=await ctx.guildcolor(str(guild.id)))
        out.set_author(name=f"Introduction for {author}:",
                       icon_url=author.avatar_url if author.avatar else author.default_avatar_url)
        out.set_footer(text=f"ID: {author.id} | {datetime.now().strftime(self.bot.config()['time_format'])}")
        em = discord.Embed(color=await ctx.guildcolor(str(guild.id)))
        roles_to_add = []
        x = 0
        questions = len(default["questions"]) + 2 if default["age"]["enabled"] else + 1
        try:
            # Should we check the user's age?
            if default["age"]["enabled"]:
                x += 1

                # Update question embed and send it
                em.set_author(name=f"Question #{x}/{questions}:")
                em.description = "How old are you?"
                em.add_field(name="Options:", value="Whole number: keep in mind that lying about your age is bannable!")
                await author.send(embed=em)

                # Manage answer and role parsing/banning for underage users
                answer = int(await self.ask_question(ctx, "age"))
                if answer < db["autoban_age"]:
                    await author.send("You are under this guilds auto ban age, therefore I have to ban you!")
                    await guild.ban(author, reason="[ Registration ] Underage")
                    # return await ctx.send(f"🇫 | {author} was too young to be in the server")

                role = default["age"]["roles"]["over"] if answer >= 18 else default["age"]["roles"]["under"]
                roles_to_add.append(self.get_role(ctx, role))
                out.add_field(name="Age:", value=str(answer))

            # Loop through questions
            for question in default["questions"]:
                x += 1

                # Update question embed and send it
                em.clear_fields()
                em.set_author(name=f"Question #{x}/{questions}:")
                em.description = question["question"]
                options = [x for x in question["options"]]
                em.add_field(
                    name="Options:",
                    value=f"{', '.join(options[:-1])}, or {options[-1]}" if len(options) > 2 else " or ".join(options)
                )
                await author.send(embed=em)

                # Manage answer and role parsing
                answer = await self.ask_question(ctx, question)
                out.add_field(name=question["short"], value=answer.capitalize())

                role = question["options"][answer]["role"]
                roles_to_add.append(self.get_role(ctx, role))

            # Allow the user to introduce themselves
            x += 1
            em.clear_fields()
            em.set_author(name=f"Question #{x}/{questions}:")
            em.description = "Introduce yourself!"
            em.add_field(name="Options:", value="Long intro or `no` if you would rather not")
            await author.send(embed=em)
            answer = await self.ask_question(ctx, "intro")
            if answer:
                out.description = answer

            # Registration complete, add roles and do all of that stuff
            roles_to_add.append(discord.utils.get(guild.roles, name="Registered"))
            await author.add_roles(*roles_to_add, reason="[ Registration ] User has registered")

            await author.send("Thank you for registering!")
            await ch.send(embed=out)

        # Handle exceptions
        except discord.Forbidden:
            return await ctx.send_error(f"{author.mention} I cannot DM you!")
        except asyncio.TimeoutError:
            ctx.command.reset_cooldown(ctx)
            return await author.send("Timed out!")
        except discord.NotFound:
            return await ctx.send_error(f"I could not find {author}! Perhaps they left?")
        except Exception as e:
            return await ctx.send(e)

    async def registration_checks(self, ctx):
        guild, author = ctx.guild, ctx.author
        # TODO: postgres
        db = await r.table("Registration").get(str(guild.id)).run(self.bot.conn)
        if not db["enabled"]:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send_error("Registration is not enabled here!")

        if not db["channel"] or not guild.get_channel(int(db["channel"])):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send_error("Either you don't have a channel set up or I could not find it!")

        if not can_manage_user(ctx, author):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send_error("I don't have a role above you which means I can't manage your roles,"
                                        " please have someone with permissions move my role up!")
        roles_found = 0
        for role in roles:
            check = discord.utils.get(guild.roles, name=role)
            if check in guild.roles:
                roles_found += 1
        if roles_found < len(roles):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send_error(f"It looks like you haven't set up the roles here, you must have all roles in"
                                        f" the server to use this function:\n"
                                        f"{await ctx.bot.get_prefix(ctx.message)}setreg roles")

        registered_role = discord.utils.get(guild.roles, name="Registered")
        if registered_role in author.roles:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send_error(f"It looks like you've already registered on this server!"
                                        f"Please run `{await ctx.bot.get_prefix(ctx.message)}unregister`"
                                        f" if you wish to re-register.")

    @staticmethod
    def get_role(ctx, role):
        guild = ctx.guild
        if isinstance(role, int):
            return guild.get_role(role)
        return discord.utils.get(guild.roles, name=role)

    @staticmethod
    async def ask_question(ctx, question):
        guild, author = ctx.guild, ctx.author
        answer = ""

        def check(m):
            return m.channel == author.dm_channel and m.author == author

        while True:
            answered = False
            response = await ctx.bot.wait_for("message", timeout=300 if question == "intro" else 60, check=check)
            resp = response.content.lower()
            if question == "intro":
                if resp == "no":
                    return None
                answer = response.content
                answered = True
            elif question == "age":
                if response.content.isdigit():
                    answer = response.content
                    answered = True
            else:
                for option, data in question["options"].items():
                    if resp == option or resp in data["aliases"]:
                        answer = option
                        answered = True
                        break
            if answered:
                return answer
            await author.send("Invalid response!")


def setup(bot):
    bot.add_cog(Registration(bot))
