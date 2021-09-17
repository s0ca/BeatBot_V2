import math
import itertools
import functools
import random
import discord
import youtube_dl
import asyncio
import datetime
from async_timeout import timeout
from discord.ext import commands


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': False,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Impossible de trouver quoi que ce soit qui corresponde à `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries'][0]:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Impossible de trouver quoi que ce soit qui corresponde à `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Impossible de récupérer `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Impossible de récupérer les correspondances pour `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(colour=discord.Colour.green(),
                               title='Now Playing',
                               description='```css\n{0.source.title}\n```'.format(self),
                               timestamp=datetime.datetime.now(),
                               color=discord.Color.blurple())
                 .add_field(name='Duration', value=self.source.duration, inline=False)
                 .add_field(name='Queried by', value=self.requester.mention)
                 .add_field(name='Direct link', value='[Here]({0.source.url})'.format(self))
                 .set_thumbnail(url=self.source.thumbnail)
                 .set_footer(text='BeatBot REV2'))
        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]

    def removelast(self):
        del self._queue[-1]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self.exists = True

        self._loop = False
        self._volume = 0.15
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:
                try:
                    async with timeout(120):  # 2 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    ciao = [
                        'Ciao bande de nazes! <:s0cul:730551865334562834>\n(2 minutes d\'inactivité)',
                        'Vers l\'infini et au delà! <:butplug:646778028071845949>\n(2 minutes d\'inactivité)',
                        'Bon, bah, je me tire 🚽\n(2 minutes d\'inactivité)',
                        'A plus dans le bus! 🖕\n(2 minutes d\'inactivité)',
                        'Hasta la (windows) vista, Baby! 🏍️\n(2 minutes d\'inactivité)',
                        'I\'ll be back! 🔫\n(2 minutes d\'inactivité)',
                        'J\'ai autre chose à foutre que de rester planter là à vous mater vous toucher la bite... 🧻\n(2 minutes d\'inactivité)',
                        'Bon je me fais un bréxit, si vous me cherchez je suis pas loin! <:ah:647451727867674628>\n(2 minutes d\'inactivité)'
                    ]
                    reponse_ciao = random.choice(ciao)
                    await self._ctx.send(reponse_ciao)
                    print('Déconnection pour inactivité')
                    self.bot.loop.create_task(self.stop())
                    self.exists = False
                    return

                self.current.source.volume = self._volume
                self.voice.play(self.current.source, after=self.play_next_song)
                await self.current.source.channel.send(embed=self.current.create_embed())

            # Si c'est loopé
            elif self.loop:
                self.now = discord.FFmpegPCMAudio(self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
                self.voice.play(self.now, after=self.play_next_song)

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            await self.bot.change_presence(status=discord.Status.idle)  # Change le status du bot lors de la déco
            self.voice = None


class Music2(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    async def on_reaction_add(self, reaction, user):
        """Play videos that receive certain reactions

        @TODO
            - filter embeds so only videos can trigger
            - make sure multitheading works
            - make emoji list customisable
            - don't add track if already in current playlist
        """
        msg = reaction.message
        emoji = str(reaction)
        ascii_emoji = emoji if emoji[0] != '<' else ':{}:'.format(emoji.split(':')[1])

        if msg.author.bot or reaction.count <= 1:
            return

        for embed in msg.embeds:
            if embed.video and ascii_emoji in ["🎵", "⏯", "👂", "<:butplug:882625527725318144>"]:
                ctx = await self.bot.get_context(msg)
                ctx.voice_state = self.get_voice_state(ctx)
                await ctx.invoke(self._play, search=embed.video.url)
                break

    # Make this optional
    async def on_message(self, message):
        if message.author.bot:
            return

        for embed in message.embeds:
            if embed.video:
                print('VIDEO', message)
                await message.add_reaction("🎵")
                break

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage("Tu m'as pris pour ton DJ perso ? Pas de ça en DM !.")

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))

    # COMMANDE JOIN
    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        destination = await ctx.invoke(self._summon)

        if destination:
            print(f'Connecté au chan {destination}\n')

        return destination

    # COMMANDE D'INVOCATION
    @commands.command(name='summon')
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        if not channel and not ctx.author.voice:
            await ctx.send("Tu n'es dans aucun canal vocal ...")
            return False

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

        return destination

    # COMMANDE STOP (vide la liste et quitte le chan)
    @commands.command(name='leave', aliases=['stop', 'stp', 'tg'])
    async def _leave(self, ctx: commands.Context):
        if not ctx.voice_state.voice:
            return await ctx.send('Non connecté à un canal vocal.')

        await ctx.voice_state.stop()
        await self.bot.change_presence(status=discord.Status.idle)
        del self.voice_states[ctx.guild.id]
        print(f"Déconnection à la demande de l'utilisateur")

    # COMMANDE VOLUME
    @commands.command(aliases=['vol', 'v'])
    async def volume(self, ctx, *, volume: float):
        if ctx.voice_client is None:
            return await ctx.send("Non connecté à un canal vocal.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Volume réglé à {}%".format(volume))
        print("Volume réglé à {}%".format(volume))

    # COMMANDE NOW
    @commands.command(name='now', aliases=['nw', 'playing'])
    async def _now(self, ctx: commands.Context):

        await ctx.send(embed=ctx.voice_state.current.create_embed())

    # COMMANDE PAUSE
    @commands.command(name='pause', aliases=['pa', 'pose', 'pase'])
    async def _pause(self, ctx: commands.Context):

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

    # COMMANDE RESUME
    @commands.command(name='resume', aliases=['r', 'res', 'reprise', 'rep'])
    async def _resume(self, ctx: commands.Context):

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    # COMMANDE NEXT
    @commands.command(name='skip', aliases=['n', 'nxt', 'next'])
    async def _skip(self, ctx: commands.Context):

        if not ctx.voice_state.is_playing:
            return await ctx.send('Aucune lecture en cours...')

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 1:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.send('Vote ajouté, actuellement **{}/3**'.format(total_votes))

        else:
            await ctx.send('Tu as déjà voté')

    # COMMANDE LIST
    @commands.command(name='queue', aliases=['list', 'll', 'ls'])
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("File d'attente vide.")

        items_per_page = 20
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='Page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    # COMMANDE SHUFFLE
    @commands.command(name='shuffle', aliases=['shfl'])
    async def _shuffle(self, ctx: commands.Context):

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("File d'attente vide.")

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    # COMMANDE REMOVE
    @commands.command(name='remove', aliases=['rm'])
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("File d'attente vide.")

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    # COMMANDE REMOVE LAST
    @commands.command(name='removelast', aliases=['rml'])
    async def _removelast(self, ctx: commands.Context):

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("File d'attente vide.")

        ctx.voice_state.songs.removelast()
        await ctx.message.add_reaction('✅')
        await ctx.send("Suppression du dernier morceau ajouté")

    # COMMANDE LOOP (Bug volume)
    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song.
        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send("Aucune lecture en cours.")

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction('✅')

    # COMMANDE PLAY
    @commands.command(name='play', aliases=["p", "pl"])
    async def _play(self, ctx: commands.Context, *, search: str):
        print('_play !!!')
        if not ctx.voice_state.voice:
            if not await ctx.invoke(self._join):
                return

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                song = Song(source)

                await ctx.voice_state.songs.put(song)
                await ctx.send('{} added'.format(str(source)))
                await ctx.message.add_reaction('💾')
                await self.bot.change_presence(status=discord.Status.online,
                                               activity=discord.Game("🎶!help🎹!now🎶"))  # Change le status du bot

    #    #COMMANDE PLAYLIST
    #    #Lecture d'un fichier et envoi d'un message par ligne
    #    @commands.command(name='pl1')
    #    async def pl1(self, ctx: commands.Context):
    #
    #        if not ctx.voice_state.voice:
    #            await ctx.invoke(self._join)
    #
    #        with open("./playlist/01_[Fanatic12000]_abduction01") as f:
    #            data = f.readlines()
    #        for i in data:
    #                await ctx.send(f"!p {i}")
    #                time.sleep(1)

    #    #Liste les playlist dispo
    #    @commands.command(name='pll')
    #    async def pll(self, ctx: commands.Context, *, page: int = 1):
    #
    #        playlist = []
    #        for x in (os.listdir('./playlist')):
    #            playlist.append(x)
    #            playlist.sort()
    #
    #        embed = (discord.Embed(title="Playlist Dispos", description='\n'.join(playlist), color=0xff8040)
    #             .set_footer(text=f"Quémandé par: {ctx.author}"))
    #             #.set_footer(text='Page {}/{}'.format(page, pages)))
    #        await ctx.send(embed=embed)

    # Check si l'utilisateur qui demande la lecture est dans un canal vocal
    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("You're not connected to any voice channel. ")

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError("BeatBot is already connected to a voice channel.")


def setup(bot):
    instance = Music2(bot)

    bot.add_listener(instance.on_reaction_add)
    bot.add_listener(instance.on_message)

    bot.add_cog(instance)
