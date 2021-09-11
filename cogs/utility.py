import json
import discord
from discord.ext import commands


class Utility(commands.Cog):
    @commands.command(aliases=['characters', 'char'],
                      help="count characters in given string")
    async def length(self, ctx, string):
        await ctx.send(len(string))

    @commands.command(aliases=['wc'], help="count words in given string")
    async def wordcount(self, ctx, *args):
        await ctx.send(len(args))

    @commands.command(aliases=['rev'], help="reverse characters in given string")
    async def reverse(self, ctx, message):
        await ctx.send(message[::(- 1)])

    @commands.command(help="count each character occurrences in the given string")
    async def count(self, ctx, message):
        # Count the amount of characters in a string.
        count = {}
        for char in message:
            if char in count.keys():
                count[char] += 1
            else:
                count[char] = 1
        await ctx.send(str(count))

    @commands.command(aliases=['head', 'magicb'], help="show known file signatures for given format")
    async def file(self, ctx, filetype):
        file = open('magic.json').read()
        alldata = json.loads(file)

        try:
            messy_signs = str(alldata[filetype]['signs'])
            signs = messy_signs.split('[')[1].split(',')[0].split(']')[0].replace("'", '')
            filetype = alldata[filetype]['mime']
            await ctx.send(f'''{filetype}: {signs}''')
        except: # if the filetype is not in magicb.json...
            await ctx.send(f"{filetype} not found :(  If you think this filetype should be included please do `!request \"magicb {filetype}\"`")

    @commands.command(name='purge', help="delete messages, from latest to earliest (default: 5)") #Bug de limit
    async def purge(self, ctx, messages: int = 5):
        if messages > 100:
            return ctx.send("Wow relax, it's already been a lot!")
        await ctx.channel.purge(limit=messages)
        removed = messages
        await ctx.send(f"{removed} messages removed")
        print(f"{removed} messages removed")
    
    @commands.command(aliases=['info', 'wois', 'whoi', 'hois', 'wohis'], help="show info about given member")
    async def whois(self, ctx, member: discord.Member = None):
        if not member:
            member = ctx.message.author
        roles = [role for role in member.roles[1:]]
        whois_e = discord.Embed(
            colour=discord.Colour.orange(), 
            timestamp=ctx.message.created_at,
            title=f"Hmm Who is {member} ?")
        whois_e.set_thumbnail(url=member.avatar_url)
        whois_e.set_footer(text=f"Asked by: {ctx.author}")

        whois_e.add_field(name="ID:", value=member.id, inline=True)
        whois_e.add_field(name="Pseudo:", value=member.display_name)

        whois_e.add_field(name="On Discord since:", value=member.created_at.strftime("%d %b %Y à %H:%M")) 
        whois_e.add_field(name="Joined the server:", value=member.joined_at.strftime("%d %b %Y à %H:%M"))

        whois_e.add_field(name="Roles:", value="\n".join([role.mention for role in roles]))
        whois_e.add_field(name="Highest role:", value=member.top_role.mention)
        await ctx.send(embed=whois_e)


def setup(bot):
    bot.add_cog(Utility())
