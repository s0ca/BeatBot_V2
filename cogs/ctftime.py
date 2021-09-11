import datetime
import re
import sys
from datetime import *
from dateutil.parser import parse
import discord
from discord.ext import commands
import requests
from colorama import Fore, Style

sys.path.append("..")

cache = {}


# All commands for getting data from ctftime.org
class CtfTime(commands.Cog):
    default_image = "https://pbs.twimg.com/profile_images/2189766987/ctftime-logo-avatar_400x400.png"

    def __init__(self, bot):
        self.bot = bot
        self.upcoming_l = []
        # self.updateDB.start() # pylint: disable=no-member

    # def cog_unload(self):
    # self.updateDB.cancel() # pylint: disable=no-member

    # @tasks.loop(minutes=30.0, reconnect=True)
    async def updateDB(self):
        # I can tell by looking at the start and end date if it's currently running or not using unix timestamps.
        now = datetime.utcnow()
        unix_now = int(now.replace(tzinfo=timezone.utc).timestamp())
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0',
        }
        upcoming = 'https://ctftime.org/api/v1/events/'
        limit = '5'  # Max amount I can grab the json data for
        response = requests.get(upcoming, headers=headers, params=limit)
        jdata = response.json()

        info = []
        for num, i in enumerate(jdata):  # Generate list of dicts of upcoming ctfs
            ctf_title = jdata[num]['title']
            (ctf_start, ctf_end) = (parse(jdata[num]['start'].replace('T', ' ').split('+', 1)[0]),
                                    parse(jdata[num]['finish'].replace('T', ' ').split('+', 1)[0]))
            (unix_start, unix_end) = (int(ctf_start.replace(tzinfo=timezone.utc).timestamp()),
                                      int(ctf_end.replace(tzinfo=timezone.utc).timestamp()))
            dur_dict = jdata[num]['duration']
            (ctf_hours, ctf_days) = (str(dur_dict['hours']), str(dur_dict['days']))
            ctf_link = jdata[num]['url']
            ctf_image = jdata[num]['logo']
            ctf_format = jdata[num]['format']
            ctf_place = jdata[num]['onsite']
            if ctf_place == False:
                ctf_place = 'Online'
            else:
                ctf_place = 'Onsite'

            ctf = {
                'name': ctf_title,
                'start': unix_start,
                'end': unix_end,
                'dur': ctf_days + ' days, ' + ctf_hours + ' hours',
                'url': ctf_link,
                'img': ctf_image,
                'format': ctf_place + ' ' + ctf_format
            }
            info.append(ctf)

        got_ctfs = []
        for ctf in info:  # If the document doesn't exist: add it, if it does: update it.
            query = ctf['name']
            ctfs.update({'name': query}, {"$set": ctf}, upsert=True)
            got_ctfs.append(ctf['name'])
        print(Fore.WHITE + f"{datetime.now()}: " + Fore.GREEN + f"Got and updated {got_ctfs}")
        print(Style.RESET_ALL)

        for ctf in ctfs.find():  # Delete ctfs that are over from the db
            if ctf['end'] < unix_now:
                ctfs.remove({'name': ctf['name']})

    # @updateDB.before_loop
    async def before_updateDB(self):
        await self.bot.wait_until_ready()

    @commands.group()
    async def ctftime(self, ctx):
        # Print usage
        if ctx.invoked_subcommand is None:
            ctftime_commands = list(set([c.qualified_name for c in CtfTime.walk_commands(self)][1:]))
            await ctx.send(f"Current ctftime commands are: ``{', '.join(ctftime_commands)}``")

    # @ctftime.command(aliases=['now', 'running'])
    # async def current(self, ctx):
    #     # Send discord embeds of the currently running ctfs.
    #     now = datetime.utcnow()
    #     unix_now = int(now.replace(tzinfo=timezone.utc).timestamp())
    #     running = False

    #     for ctf in ctfs.find():
    #         if ctf['start'] < unix_now and ctf['end'] > unix_now: # Check if the ctf is running
    #             running = True
    #             embed = discord.Embed(title=':red_circle: ' + ctf['name']+' IS LIVE', description=ctf['url'], color=15874645)
    #             start = datetime.utcfromtimestamp(ctf['start']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
    #             end = datetime.utcfromtimestamp(ctf['end']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
    #             if ctf['img'] != '':
    #                 embed.set_thumbnail(url=ctf['img'])
    #             else:
    #                 embed.set_thumbnail(url="https://pbs.twimg.com/profile_images/2189766987/ctftime-logo-avatar_400x400.png")
    #                 # CTFtime logo

    #             embed.add_field(name='Duration', value=ctf['dur'], inline=True)
    #             embed.add_field(name='Format', value=ctf['format'], inline=True)
    #             embed.add_field(name='Timeframe', value=start+' -> '+end, inline=True)
    #             await ctx.channel.send(embed=embed)

    #     if running == False: # No ctfs were found to be running
    #         await ctx.send("No CTFs currently running! Check out >ctftime countdown, and >ctftime upcoming to see when ctfs will start!")

    def _pull(self, path):
        if not path:
            raise Exception("No path given.")

        if path in cache:
            c = cache[path]
            if c['datetime'] < datetime.now() - timedelta(minutes=5):
                return c.data
            else:
                del cache[path]

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0',
        }

        upcoming_ep = "https://ctftime.org/api/v1/" + path
        r = requests.get(upcoming_ep, headers=headers)

        if r.status_code != 200:
            raise Exception("Error retrieving data, please report this with `!report \"what happened\"`")

        json = r.json()
        cache[path] = {
            'data': json,
            'datetime': datetime.now()
        }

        return json

    @ctftime.command(aliases=["next"], help="show upcoming CTFs")
    async def upcoming(self, ctx, amount=3):
        upcoming = self._pull("events/?limit=" + str(int(amount)))

        for ctf in upcoming:
            (ctf_start, ctf_end) = (ctf["start"].replace("T", " ").split("+", 1)[0] + " UTC",
                                    ctf["finish"].replace("T", " ").split("+", 1)[0] + " UTC")
            (ctf_start, ctf_end) = (re.sub(":00 ", " ", ctf_start), re.sub(":00 ", " ", ctf_end))
            (ctf_hours, ctf_days) = (str(ctf["duration"]["hours"]), str(ctf["duration"]["days"]))

            description = """{}\n{}""".format(
                ctf["description"][:200] + ('...' if len(ctf['description']) > 200 else ''),
                ctf["url"]
            )
            embed = discord.Embed(title=ctf["title"], description=description, color=int("f23a55", 16))
            embed.set_thumbnail(url=ctf["logo"] if ctf["logo"] != '' else self.default_image)

            embed.add_field(name="Duration", value=((ctf_days + " days, ") + ctf_hours) + " hours", inline=True)
            embed.add_field(name="Format", value=("On site" if ctf["onsite"] else "Online") + " " + ctf["format"],
                            inline=True)
            embed.add_field(name="Timeframe", value=(ctf_start + "\n") + ctf_end, inline=True)
            await ctx.channel.send(embed=embed)

    @ctftime.command(aliases=["leaderboard"], help="show top teams on CTFTime on given year")
    async def top(self, ctx, year=None):
        if not year:
            year = str(datetime.today().year)

        leaderboards = ""
        year = str(int(year))
        top = self._pull("top/{}/".format(year))[year]

        for team in range(10):
            # Leaderboard is always top 10 so we can just assume this for ease of formatting
            rank = team + 1
            teamname = top[team]['team_name']
            score = str(round(top[team]['points'], 4))

            if team != 9:
                # This is literally just for formatting.  I'm sure there's a better way to do it but I couldn't think of one :(
                # If you know of a better way to do this, do a pull request or msg me and I'll add  your name to the cool list
                leaderboards += f"\n[{rank}]    {teamname}: {score}"
            else:
                leaderboards += f"\n[{rank}]   {teamname}: {score}\n"

        await ctx.send(f":triangular_flag_on_post:  **{year} CTFtime Leaderboards**```ini\n{leaderboards}```")

        # LOG THIS
    # @ctftime.command()
    # async def timeleft(self, ctx):
    #     # Send the specific time that ctfs that are currently running have left.
    #     now = datetime.utcnow()
    #     unix_now = int(now.replace(tzinfo=timezone.utc).timestamp())
    #     running = False
    #     for ctf in ctfs.find():
    #         if ctf['start'] < unix_now and ctf['end'] > unix_now: # Check if the ctf is running
    #             running = True
    #             time = ctf['end'] - unix_now 
    #             days = time // (24 * 3600)
    #             time = time % (24 * 3600)
    #             hours = time // 3600
    #             time %= 3600
    #             minutes = time // 60
    #             time %= 60
    #             seconds = time
    #             await ctx.send(f"```ini\n{ctf['name']} ends in: [{days} days], [{hours} hours], [{minutes} minutes], [{seconds} seconds]```\n{ctf['url']}")

    #     if running == False:
    #         await ctx.send('No ctfs are running! Use >ctftime upcoming or >ctftime countdown to see upcoming ctfs')

    # @ctftime.command()
    # async def countdown(self, ctx, params=None):
    #     # Send the specific time that upcoming ctfs have until they start.
    #     now = datetime.utcnow()
    #     unix_now = int(now.replace(tzinfo=timezone.utc).timestamp())

    #     if params == None:
    #         self.upcoming_l = []
    #         index = ""
    #         for ctf in ctfs.find():
    #             if ctf['start'] > unix_now:
    #                 # if the ctf start time is in the future...
    #                 self.upcoming_l.append(ctf)
    #         for i, c in enumerate(self.upcoming_l):
    #             index += f"\n[{i + 1}] {c['name']}\n"

    #         await ctx.send(f"Type >ctftime countdown <number> to select.\n```ini\n{index}```")
    #     else:
    #         if self.upcoming_l != []:
    #             x = int(params) - 1     
    #             start = datetime.utcfromtimestamp(self.upcoming_l[x]['start']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
    #             end = datetime.utcfromtimestamp(self.upcoming_l[x]['end']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'

    #             time = self.upcoming_l[x]['start'] - unix_now 
    #             days = time // (24 * 3600)
    #             time = time % (24 * 3600)
    #             hours = time // 3600
    #             time %= 3600
    #             minutes = time // 60
    #             time %= 60
    #             seconds = time

    #             await ctx.send(f"```ini\n{self.upcoming_l[x]['name']} starts in: [{days} days], [{hours} hours], [{minutes} minutes], [{seconds} seconds]```\n{self.upcoming_l[x]['url']}")
    #         else: # TODO: make this a function, too much repeated code here.
    #             for ctf in ctfs.find():
    #                 if ctf['start'] > unix_now:
    #                     self.upcoming_l.append(ctf)
    #             x = int(params) - 1     
    #             start = datetime.utcfromtimestamp(self.upcoming_l[x]['start']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
    #             end = datetime.utcfromtimestamp(self.upcoming_l[x]['end']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'

    #             time = self.upcoming_l[x]['start'] - unix_now 
    #             days = time // (24 * 3600)
    #             time = time % (24 * 3600)
    #             hours = time // 3600
    #             time %= 3600
    #             minutes = time // 60
    #             time %= 60
    #             seconds = time

    #             await ctx.send(f"```ini\n{self.upcoming_l[x]['name']} starts in: [{days} days], [{hours} hours], [{minutes} minutes], [{seconds} seconds]```\n{self.upcoming_l[x]['url']}")


def setup(bot):
    bot.add_cog(CtfTime(bot))
