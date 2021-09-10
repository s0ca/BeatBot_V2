#!/usr/bin/python3
"""
BeatBot 2.0
Authors: s0ca, zM_
"""

import os
import sys
from dotenv import load_dotenv
import discord
from discord.ext import commands
import help_info
import random

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
OWNER = int(os.getenv("DISCORD_OWNER"))

client = discord.Client()
bot = commands.Bot(command_prefix="!",
                   allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))
bot.remove_command('help')

# Each extension corresponds to a file within the cogs directory.  Remove from the list to take away the functionality.
extensions = ['music2', 'ctftime', 'encoding', 'cipher', 'utility']


@bot.event
async def on_ready():
    print(f"{bot.user.name} - Online")
    print(f"discord.py {discord.__version__}\n")
    print("-------------------------------")

    await bot.change_presence(activity=discord.Game(name="!help | !source"))


@bot.command()
async def help(ctx, page=None):
    # Custom help command.  Each main category is set as a 'page'.
    if page == 'ctftime':
        emb = discord.Embed(description=help_info.ctftime_help, colour=4387968)
        emb.set_author(name='CTFTime Help')
    elif page == 'ctf':
        emb = discord.Embed(description=help_info.ctf_help, colour=4387968)
        emb.set_author(name='CTF Help')
    elif page == 'utility':
        emb = discord.Embed(description=help_info.utility_help, colour=4387968)
        emb.set_author(name='Utilities Help')
    elif page == 'music':
        emb = discord.Embed(description=help_info.music_help, colour=4387968)
        emb.set_author(name='Music Help')
    else:
        emb = discord.Embed(description=help_info.help_page, colour=4387968)
        emb.set_author(name='BeatBot Help')

    await attach_embed_info(ctx, emb)
    await ctx.channel.send(embed=emb)


async def attach_embed_info(ctx=None, embed=None):
    embed.set_thumbnail(url=f'{bot.user.avatar_url}')
    return embed


@bot.command()
async def source(ctx):
    # Sends the github link of the bot.
    await ctx.send(help_info.src)


@bot.event
async def on_command_error(ctx, error):
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
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing a required argument.  Do !help")
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the appropriate permissions to run this command.")
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I don't have sufficient permissions!")
    else:
        print("error not caught")
        print(error)


@bot.command()
async def request(ctx, feature):
    # Bot sends a dm to creator with the name of the user and their request.
    creator = await bot.fetch_user(OWNER)
    authors_name = str(ctx.author)
    await creator.send(f''':pencil: {authors_name}: {feature}''')
    await ctx.send(f''':pencil: Thanks, "{feature}" has been requested!''')


@bot.command()
async def report(ctx, error_report):
    # Bot sends a dm to creator with the name of the user and their report.
    creator = await bot.fetch_user(OWNER)
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


if __name__ == '__main__':
    sys.path.insert(1, os.getcwd() + '/cogs/')
    for extension in extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load cogs : {e}')
    bot.run(TOKEN)
