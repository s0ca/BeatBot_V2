#!/usr/bin/python3
"""
BeatBot 2.0
Authors: s0ca, zM_
"""

import os
import sys
import random
import discord
from discord.ext import commands

import settings
from help import Help

bot = commands.Bot(command_prefix=settings.PREFIX,
                   allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False),
                   description="**__BiteBotte__ - Bot de stream musical**")

# Each extension corresponds to a file within the cogs directory.  Remove from the list to take away the functionality.
extensions = ['music2', 'ctftime', 'encoding', 'cipher', 'utility']


@bot.event
async def on_ready():
    print(f"{bot.user.name} - Online")
    print(f"discord.py {discord.__version__}\n")
    print("-------------------------------")

    await bot.change_presence(activity=discord.Game(name="!help | !source"))


async def attach_embed_info(ctx=None, embed=None):
    embed.set_thumbnail(url=f'{bot.user.avatar_url}')
    return embed


@bot.command()
async def source(ctx):
    await ctx.send('https://github.com/ZanyMonk/beatbot')


@bot.event
async def on_command_error(ctx, error):
    print('Exception raised following message from "{}"'.format(ctx.author), file=sys.stderr)
    print(error, file=sys.stderr)

    if isinstance(error, commands.CommandNotFound):
        nop_e = discord.Embed(
            colour=discord.Colour.red(),
            title=f"RTFM!"
        )
        nop_e.add_field(name="Apprendre à taper...",
                        value=f"Si on m'avait filé un euro à\nchaque fois que tu te plantes,\nje serais riche.",
                        inline=True)
        nop_e.add_field(name="Un petit coup de pouce ?", value=f"```css\n!help```")
        await ctx.send(embed=nop_e)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing a required argument.  Try `!help`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the appropriate permissions to run this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I don't have sufficient permissions!")
    else:
        await ctx.send(embed=discord.Embed(colour=discord.Colour.red(), title=type(error.original).__name__,
                                           description=error))


@bot.command()
async def request(ctx, feature):
    # Bot sends a dm to creator with the name of the user and their request.
    creator = await bot.fetch_user(settings.OWNER)
    authors_name = str(ctx.author)
    await creator.send(f''':pencil: {authors_name}: {feature}''')
    await ctx.send(f''':pencil: Thanks, "{feature}" has been requested!''')


@bot.command()
async def report(ctx, error_report):
    # Bot sends a dm to creator with the name of the user and their report.
    creator = await bot.fetch_user(settings.OWNER)
    authors_name = str(ctx.author)
    await creator.send(f''':triangular_flag_on_post: {authors_name}: {error_report}''')
    await ctx.send(f''':triangular_flag_on_post: Thanks for the help, "{error_report}" has been reported!''')


@bot.listen()
async def on_message(message):
    if "connard" in message.content:
        connard_answ = [
            'Oui?',
            'C\'est mon deuxieme prénom',
            'On m\'appelle?',
            'Tu te trompes de personne, je ne suis pas <@589153146878820364>',
            'C\'est toi le connard non mais!',
            'Qui m\'invoque?',
            'Pourquoi tu t\'appelles toi même ?',
            'Tu m\'as pris pour <@411157117425156099> ou quoi ?'
        ]
        reponse = random.choice(connard_answ)
        await message.channel.send(reponse)

bot.help_command = Help()

if __name__ == '__main__':
    sys.path.insert(1, os.getcwd() + '/cogs/')

    for extension in extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load cogs : {e}')
    bot.run(settings.TOKEN)