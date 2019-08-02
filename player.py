from keys.config import PARAMS

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from discord import Embed
import discord
import re
import youtube_dl
import asyncio

DEVELOPER_KEY = PARAMS["youtube"]["jinx"]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

MAX_RESULT_PER_PAGE = 20

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
    #FIXME I dn't even know why it crashes silently -_-
    #for chan in guild.text_channels::
    #    if chan.permission_for(guild.me).send_messages:
    #        return chan
    return guild.text_channels[0]


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
        if 'http' in link and (('youtube' in link and ('v=' in link or 'list=' in link)) or 'youtu.be' in link):
            return True
        else:
            return False

    def _get_guild_by_id(self, guild_id):
        for guild in self.client.guilds:
            if guild.id == guild_id:
                return guild
        return None

    def set_show_chan(self, guild_id, show_chan_id=None):
        if guild_id not in self.servers:
            self.servers[guild_id] = {}
        guild = self._get_guild_by_id(guild_id)
        print(guild.text_channels)
        if show_chan_id is None:
            show_chan = _get_first_permission_chan(guild)
            show_chan_id = show_chan.id
        else:
            show_chan = guild.get_channel(show_chan_id)
        print(show_chan)
        self.servers[guild_id]["id"] = show_chan_id
        self.servers[guild_id]["chan"] = show_chan

    async def search_video(self, ctx, suffix, playlist):
        print('in search')
        guild_id = ctx.guild.id
        print(guild_id)

        if guild_id not in self.servers:
            self.servers[guild_id] = {}
        if "search_map" not in self.servers[guild_id]:
            self.servers[guild_id]["search_map"] = {}
        await self.next_page(ctx, suffix, playlist)

    async def next_page(self, ctx, suffix, playlist, token=None):
        if token is None:
            print('next_page init search')
            response = self.youtube.search().list(
                part='snippet',
                type='playlist' if playlist else 'video',
                q=suffix
            ).execute()
        else:
            response = self.youtube.search().list(
                part='snippet',
                type='playlist' if playlist else 'video',
                q=suffix,
                pageToken=token
            ).execute()
        print(response)
        await self.show_result_page(ctx, response, suffix, playlist)

    async def show_result_page(self, ctx, response, suffix, playlist):
        print('showing message')
        guild_id = ctx.guild.id
        msg_id = ctx.message.id
        embed = Embed(title='Search results', color=1669525, description='searching `%s`'%suffix)
        embed.set_thumbnail(url='https://www.youtube.com/yts/img/yt_1200-vfl4C3T0K.png')
        embed.set_footer(text='Make your choice by reacting, change pages with %s or %s and cancel with %s'
                              % (PPAGEBTN, NPAGEBTN, CANCEL))
        urls = []
        for i, video in enumerate(response.get("items", [])):
            embed.add_field(
                name='`%d` %s' % (i+1, video["snippet"]["title"]),
                value='desc: `%s`' % (video["snippet"]["description"])
            )
            urls.append((YTPL + video["id"]["playlistId"]) if playlist else (YTLINK + video["id"]["videoId"]))
        print(urls)

        if guild_id not in self.servers:
            self.servers[guild_id] = {}
        if "search_map" not in self.servers[guild_id]:
            self.servers[guild_id]["search_map"] = {}
        if msg_id in self.servers[guild_id]["search_map"]:
            print('editing message')
            await self.servers[guild_id]["search_map"][msg_id]["message"].edit(embed=embed)
            self.servers[guild_id]["search_map"][msg_id]["next"] = response.get("nextPageToken", "")
            self.servers[guild_id]["search_map"][msg_id]["prev"] = response.get("prevPageToken", "")
            self.servers[guild_id]["search_map"][msg_id]["urls"] = urls
            self.servers[guild_id]["search_map"][msg_id]["playlist"] = playlist
        else:
            print('sending message')
            message = await ctx.message.channel.send(embed=embed)
            await message.add_reaction(PPAGEBTN)
            await message.add_reaction(ONE)
            await message.add_reaction(TWO)
            await message.add_reaction(THREE)
            await message.add_reaction(FOUR)
            await message.add_reaction(FIVE)
            await message.add_reaction(NPAGEBTN)
            await message.add_reaction(CANCEL)
            self.ctx[message.id] = ctx
            print(msg_id)
            self.servers[guild_id]["search_map"][msg_id] = {
                'urls': urls,
                'suffix': suffix,
                'playlist': playlist,
                'next': response.get("nextPageToken", ""),
                'prev': response.get("prevPageToken", ""),
                'message': message
            }

    async def add_to_playlist(self, ctx, request, playlist):
        self.ctx[ctx.guild.id] = ctx
        print(request)
        if self.is_youtube_link(request):
            print("adding to playlist ", request)
            videos_to_add = []
            if playlist:
                playlist_id = re.search("([^\/]+\/\/[^\/]+\/(watch\?)?)(.*)list=([^\&\?]+)(.*)", request).group(4)
                req_nb_vid = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=playlist_id
                ).execute()
                totRes = req_nb_vid["pageInfo"]["totalResults"]
                nbReq = 0
                tokenNext = ""
                while tokenNext != "[STOP]":
                    if tokenNext == "":
                        response = self.youtube.playlistItems().list(
                            part='snippet',
                            maxResults=50,
                            playlistId=playlist_id
                        ).execute()
                    else:
                        response = self.youtube.playlistItems().list(
                            part='snippet',
                            maxResults=50,
                            playlistId=playlist_id,
                            pageToken=tokenNext
                        ).execute()
                    print(response)
                    tokenNext = response['nextPageToken'] if 'nextPageToken' in response else "[STOP]"
                    for item in response['items']:
                        video = item["snippet"]
                        if 'thumbnails' not in video:
                            videos_to_add.append({'url': YTLINK + video["resourceId"]["videoId"],
                                              'thumbnail': 'https://www.youtube.com/yts/img/yt_1200-vfl4C3T0K.png',
                                              'title': video["title"]})
                            continue
                        if 'medium' in video['thumbnails']:
                            videos_to_add.append({'url': YTLINK + video["resourceId"]["videoId"],
                                              'thumbnail': video["thumbnails"]["medium"]["url"],
                                              'title': video["title"]})
                        else:
                            videos_to_add.append({'url': YTLINK + video["resourceId"]["videoId"],
                                              'thumbnail': video["thumbnails"]["default"]["url"],
                                              'title': video["title"]})
            else:
                if 'youtu.be' in request:
                    video_id = re.search(".*/(.*)", request).group(1)
                else:
                    video_id = re.search("([^\/]+\/\/[^\/]+\/(watch\?)?)(.*)v=([^\&\?]+)(.*)", request).group(4)
                print(video_id)
                try:
                    response = self.youtube.videos().list(
                        part='snippet',
                        id=video_id
                    ).execute()
                except HttpError as e:
                    print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
                video = response['items'][0]["snippet"]
                if 'medium' in video['thumbnails']:
                    videos_to_add.append({'url': YTLINK+video_id, 'thumbnail': video["thumbnails"]["medium"]["url"], 'title': video["title"]})
                else:
                    videos_to_add.append({'url': YTLINK+video_id, 'thumbnail': video["thumbnails"]["default"]["url"], 'title': video["title"]})
            print("adding videos %s" % videos_to_add)
            if ctx.guild.id not in self.playlist:
                self.playlist[ctx.guild.id] = []
            for video in videos_to_add:
                self.playlist[ctx.guild.id].append(video)
            await self.show_playlist(ctx, False)
            if ctx.guild.id not in self.is_playing or not self.is_playing[ctx.guild.id]:
                author = ctx.message.author
                voice = await author.voice.channel.connect()
                self.voice[ctx.guild.id] = voice
                await self.play(voice, ctx.guild.id)
            else:
                await self.edit_embed(ctx.guild.id)


    async def play(self, voice, guild_id):
        ctx = self.ctx[guild_id]
        if guild_id not in self.current:
            self.current[guild_id] = 0

        opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'nocheckcertificate': True,
            'restrictfilenames': True,
            'source_address': '0.0.0.0',
            #'postprocessors': [{
            #    'key': 'FFmpegExtractAudio',
            #    'preferredcodec': 'mp3',
            #    'preferredquality': '192',
            #}],
        }

        def my_after(error):
            if error is not None:
                asyncio.run_couroutine_threadsafe(self.servers[guild_id]["chan"].send(error), self.client.loop)
            self.current[guild_id] += 1
            print(self.current[guild_id], len(self.playlist[guild_id]))
            infinite = self.servers[guild_id]['infinite'] if 'infinite' in self.servers[guild_id] else False
            if self.current[guild_id] >= len(self.playlist[guild_id]) and not infinite:
                print("playlist end, leaving ...")
                # delete jinx youtube player message
                asyncio.run_coroutine_threadsafe(self.servers[guild_id]['jinxMessage'].delete(), self.client.loop)
                # make jinx leave voice chat
                asyncio.run_coroutine_threadsafe(voice.disconnect(), self.client.loop)
                self.current[guild_id] = 0
                self.playlist[guild_id] = []
                self.is_playing[guild_id] = False
            else:
                if infinite:
                    self.current[guild_id] = 0
                asyncio.run_coroutine_threadsafe(self.play(voice, guild_id), self.client.loop)

        self.is_playing[guild_id] = True
        print("editing embed for guild %s" % guild_id)
        await self.edit_embed(guild_id)
        with youtube_dl.YoutubeDL(opts) as ydl:
            song_info = ydl.extract_info(self.playlist[ctx.guild.id][self.current[guild_id]]['url'], download=True)
            audio = discord.FFmpegPCMAudio(ydl.prepare_filename(song_info))
            voice.play(audio, after=my_after)

    async def edit_embed(self, guild_id):
        infinite = self.servers[guild_id]['infinite'] if 'infinite' in self.servers[guild_id] else False
        embed = Embed(
                      title=self.playlist[guild_id][self.current[guild_id]]['title'],
                      color=12345678,
                      description='Video n° `' + str(self.current[guild_id] + 1) + '` / `' + str(len(self.playlist[guild_id])) + '`\n*Looping over playlist :* `' + str(infinite) + '`'
        )
        embed.set_thumbnail(url='https://pre00.deviantart.net/1cd4/th/pre/i/2015/330/f/d/jinx_chibi_by_yukyuen-d8pnno0.png')
        embed.set_image(url=self.playlist[guild_id][self.current[guild_id]]['thumbnail'])
        print("embed created")
        if guild_id not in self.servers:
            self.servers[guild_id] = {}
        if 'chan' not in self.servers[guild_id]:
            print("setting show chan")
            self.set_show_chan(guild_id)
        try:
            await self.servers[guild_id]['jinxMessage'].edit(embed=embed)
        except:
            print("sending jinxMessage")
            message = await self.servers[guild_id]['chan'].send(embed=embed)
            print(str(message))
            await message.add_reaction(LOOPBTN)
            await message.add_reaction(PREVBTN)
            await message.add_reaction(PAUSEBTN)
            await message.add_reaction(STOPBTN)
            await message.add_reaction(NEXTBTN)
            await message.add_reaction(REPLAYBTN)
            self.servers[guild_id]['jinxMessage'] = message

    async def show_playlist(self, ctx, send_it, page=None):
        guild_id = ctx.guild.id
        self.servers[guild_id]['playlistCtx'] = ctx
        if guild_id not in self.playlist:
            self.playlist[guild_id] = []
        if len(self.playlist[guild_id]) > 0:
            if page is None:
                page = 0 if ('playlistPage' not in self.servers[guild_id] or send_it) else self.servers[guild_id]['playlistPage']
            if page < 0:
                page = 0
            while len(self.playlist[guild_id]) < page * MAX_RESULT_PER_PAGE:
                page -= 1

            embed = Embed(
                title="Playlist for server %s :" % ctx.guild.name,
                color=12345678
            )
            embed.set_thumbnail(
                url='https://pre00.deviantart.net/1cd4/th/pre/i/2015/330/f/d/jinx_chibi_by_yukyuen-d8pnno0.png')

            for i, video in enumerate(self.playlist[guild_id]):
                if i >= page * MAX_RESULT_PER_PAGE and i < (page + 1) * MAX_RESULT_PER_PAGE:
                    embed.add_field(name="%d/%d : " % (i+1, len(self.playlist[guild_id])), value="%s    " % video['title'], inline=True)
            if send_it:
                if 'playlistMessage' in self.servers[guild_id] and self.servers[guild_id]['playlistMessage'] is not None:
                    try:
                        await self.servers[guild_id]['playlistMessage'].delete()
                    except:
                        # Catch a message removed by user
                        pass
                message = await ctx.message.channel.send(embed=embed)
                await message.add_reaction(PPAGEBTN)
                await message.add_reaction(CANCEL)
                await message.add_reaction(NPAGEBTN)
                self.servers[guild_id]['playlistMessage'] = message
                self.servers[guild_id]['playlistPage'] = 0

            elif 'playlistMessage' in self.servers[guild_id] and self.servers[guild_id]['playlistMessage'] is not None:
                try:
                    # Catch a message removed by user
                    await self.servers[guild_id]['playlistMessage'].edit(embed=embed)
                except:
                    self.servers[guild_id]['playlistMessage'] = None
                    self.servers[guild_id]['playlistPage'] = 0
                else:
                    self.servers[guild_id]['playlistPage'] = page

        else:
            self.servers[guild_id]['playlistMessage'] = None
            if send_it:
                message = await ctx.message.channel.send("Your playlist is empty !")
                await message.delete(delay=5.0)
