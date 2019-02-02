from keys.config import PARAMS
from apiclient.discovery import build
from discord import Embed
import discord
import re
import youtube_dl
import asyncio

DEVELOPER_KEY = PARAMS["youtube"]["jinx"]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

NEXTBTN = "⏭"
PREVBTN = "⏮"
PAUSEBTN = "⏯"
REPLAYBTN = "↩"
STOPBTN = "⏹"
LOOPBTN = "🔁"

NPAGEBTN = "➡"
PPAGEBTN = "⬅"
ONE = "1⃣"
TWO = "2⃣"
THREE = "3⃣"
FOUR = "4⃣"
FIVE = "5⃣"
CANCEL = "❎"
YTLINK = 'http://www.youtube.com/watch?v='
YTPL = 'http://www.youtube.com/playlist?list='


def _get_first_permission_chan(guild):
    for chan in guild.text_channels:
        if chan.permission_for(guild.me).send_messages:
            return chan
    return None


class YoutubePlayer:

    def __init__(self, client):
        self.playlist = {}
        self.current = {}
        self.is_playing = {}
        self.youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
        self.servers = {}
        self.client = client
        self.ctx = {}
        self.voice = {}

    @staticmethod
    def is_youtube_link(link):
        yt_pattern = re.compile("(http://|https://)(www\.)?(youtu)(.*)")
        return yt_pattern.match(link)

    def _get_guild_by_id(self, guild_id):
        for guild in self.client.guilds:
            if guild.id == guild_id:
                return guild
        return None

    def set_show_chan(self, guild_id, show_chan_id=None):
        if guild_id not in self.servers:
            self.servers[guild_id] = {}
        guild = self._get_guild_by_id(guild_id)
        if show_chan_id is None:
            show_chan = _get_first_permission_chan(guild)
            show_chan_id = show_chan.id
        else:
            show_chan = guild.get_channel(show_chan_id)
        self.servers[guild_id]["id"] = show_chan_id
        self.servers[guild_id]["chan"] = show_chan

    async def search_video(self, ctx, msg, suffix, playlist):
        guild_id = str(msg.guild)
        self.ctx[guild_id] = ctx
        if guild_id not in self.servers:
            self.servers[guild_id] = {}
        if "list_to_play" not in self.servers[guild_id]:
            self.servers[guild_id]["list_to_play"] = []
        if "search_map" not in self.servers[guild_id]:
            self.servers[guild_id]["search_map"] = {}
        await self.next_page(msg, suffix, playlist)

    async def next_page(self, msg, suffix, playlist, token=None):
        if token is None:
            response = self.youtube.search.list(
                part='snippet',
                type='playlist' if playlist else 'video',
                q=suffix
            ).execute()
        else:
            response = self.youtube.search.list(
                part='snippet',
                type='playlist' if playlist else 'video',
                q=suffix,
                pageToken=token
            ).execute()
        await self.show_result_page(msg, response, suffix, playlist)

    async def show_result_page(self, msg, response, suffix, playlist):
        guild_id = str(msg.guild)
        embed = Embed()
        embed.title = 'Search results'
        embed.colour = 1669525
        embed.set_thumbnail(url='https://www.youtube.com/yts/img/yt_1200-vfl4C3T0K.png')
        embed.description = 'searching `%s`' % suffix
        embed.set_footer(text='Make your choice by reacting, change pages with %s or %s and cancel with %s'
                              % (PPAGEBTN, NPAGEBTN, CANCEL))
        urls = []
        for i, video in enumerate(response.get("items", [])):
            embed.add_field(
                name='`%d` %s' % (i+1, video["snippet"]["title"]),
                value='desc: `%s`' % (video["snippet"]["description"])
            )
            urls.append((YTPL + video["id"]["playlistId"]) if playlist else (YTLINK + video["id"]["videoId"]))
        if msg.id in self.servers[guild_id]["search_map"]:
            await msg.edit(embed=embed)
            self.servers[guild_id]["search_map"][msg.id]["next"] = response.get("nextPageToken", "")
            self.servers[guild_id]["search_map"][msg.id]["prev"] = response.get("prevPageToken", "")
            self.servers[guild_id]["search_map"][msg.id]["urls"] = urls
            self.servers[guild_id]["search_map"][msg.id]["playlist"] = playlist
        else:
            message = await msg.channel.send(embed=embed)
            await message.add_reaction(PPAGEBTN)
            await message.add_reaction(ONE)
            await message.add_reaction(TWO)
            await message.add_reaction(THREE)
            await message.add_reaction(FOUR)
            await message.add_reaction(FIVE)
            await message.add_reaction(NPAGEBTN)
            await message.add_reaction(CANCEL)
            self.servers[guild_id]["search_map"][message.id] = {
                'msg': msg,
                'urls': urls,
                'suffix': suffix,
                'playlist': playlist,
                'next': response.get("nextPageToken", ""),
                'prev': response.get("prevPageToken", "")
            }

    async def add_to_playlist(self, ctx, request, playlist):
        self.ctx[ctx.guild.id] = ctx
        if self.is_youtube_link(request):
            videos_to_add = []
            if playlist:
                playlist_id = re.search("([^\/]+\/\/[^\/]+\/(watch\?)?)(.*)list=([^\&\?]+)(.*)", request).group(3)
                response = self.youtube.playlistItems().list(
                    part='snippet',
                    id=playlist_id
                )
                for item in response.get('items'):
                    video = item["snippet"]
                    videos_to_add.append({'url': YTLINK + video["contentDetails"]["videoId"],
                                          'thumbnail': video["thumbnails"]["default"]["url"],
                                          'tittle': video["tittle"]})
            else:
                if 'youtu.be' in request:
                    video_id = re.search(".*/(.*)", request).group(0)
                else:
                    video_id = re.search("([^\/]+\/\/[^\/]+\/(watch\?)?)(.*)v=([^\&\?]+)(.*)", request).group(3)
                response = self.youtube.videos().list(
                    part='snippet',
                    id=video_id
                ).execute()
                video = response.get('items')[0]["snippet"]
                videos_to_add.append({'url': YTLINK+video_id,
                                      'thumbnail': video["thumbnails"]["default"]["url"],
                                      'tittle': video["tittle"]})

            if ctx.guild.id not in self.playlist:
                self.playlist[ctx.guild.id] = []
            for video in videos_to_add:
                self.playlist[ctx.guild.id].append(video)
            await self.edit_embed(ctx.guild.id)
            if not self.is_playing[ctx.guild.id]:
                author = ctx.message.author
                voice = await author.voice.channel.connect()
                self.voice[ctx.guild.id] = voice
                await self.play(voice, ctx.guild.id)

    async def play(self, voice, guild_id):
        ctx = self.ctx[guild_id]
        if ctx.guild.id not in self.current:
            self.current[ctx.guild.id] = 0

        opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        def my_after(error):
            if error is not None:
                self.servers[ctx.guild.id]["chan"].send(error)
            self.current[ctx.guild.id] += 1
            print(self.current[guild_id], len(self.playlist[guild_id]))
            infinite = self.servers[guild_id]['infinite'] if 'infinite' in self.servers[guild_id] else False
            if self.current[guild_id] >= len(self.playlist[guild_id]) and not infinite:
                print("playlist end, leaving ...")
                # delete jinx youtube player message
                asyncio.run_coroutine_threadsafe(self.servers[guild_id]['jinxMessage'].delete(), self.client.loop)
                # make jinx leave voice chat
                asyncio.run_coroutine_threadsafe(voice.disconnect(), self.client.loop)
            else:
                if infinite:
                    self.current[ctx.guild.id] = 0
                asyncio.run_coroutine_threadsafe(self.play(voice, guild_id), self.client.loop)

        self.is_playing[guild_id] = True
        await self.edit_embed(guild_id)
        with youtube_dl.YoutubeDL(opts) as ydl:
            song_info = ydl.extract_info(self.playlist[ctx.guild.id][self.current[guild_id]]['url'], download=False)
            audio = discord.FFmpegPCMAudio(song_info['url'])
            voice.play(audio, after=my_after)

    async def edit_embed(self, guild_id):
        embed = Embed()
        embed.title = self.playlist[guild_id][self.current[guild_id]]['title']
        embed.colour = 12345678
        embed.set_thumbnail(url='https://cdn.discordapp.com/avatars/297127338188079105/4b7b6e74a835176401c0c3affd5ce8d6.jpg?size=1024')
        embed.set_image(url=self.playlist[guild_id][self.current[guild_id]]['thumbnail'])
        embed.description = 'Video n° `' + str(self.current[guild_id] + 1) + '` / `' + str(len(self.playlist[guild_id])) + '`'

        if 'chan' not in self.servers[guild_id]:
            self.set_show_chan(guild_id)
        try:
            await self.servers[guild_id]['jinxMessage'].edit(embed=embed)
        except Exception:
            message = await self.servers[guild_id]['chan'].send(embed=embed)
            await message.add_reaction(LOOPBTN)
            await message.add_reaction(PREVBTN)
            await message.add_reaction(PAUSEBTN)
            await message.add_reaction(STOPBTN)
            await message.add_reaction(NEXTBTN)
            await message.add_reaction(REPLAYBTN)
            self.servers[guild_id]['jinxMessage'] = message
