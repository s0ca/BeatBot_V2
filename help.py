import discord
from discord.ext import commands

from settings import PREFIX


class Help(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            emby = discord.Embed(description=page)
            await destination.send(embed=emby)

    def add_aliases_formatting(self, aliases):
        formatted_aliases = ['`{}`'.format(PREFIX + a) for a in aliases]
        self.paginator.add_line('**%s** %s' % (self.aliases_heading, ', '.join(formatted_aliases)), empty=True)

    def get_command_signature(self, command):
        signature = """{prefix}{name}""".format(
            name=command.name,
            help=command.help,
            description=command.description,
            prefix=PREFIX
        )

        if len(command.signature):
            signature += " " + command.signature

        return '`{}`'.format(signature)