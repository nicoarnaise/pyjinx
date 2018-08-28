from keys.config import PARAMS

import youtube_dl
import asyncio
import discord
from discord.ext import commands

loop = asyncio.get_event_loop()
client = commands.Bot(command_prefix='-',loop=loop ,activity=discord.Game("Multiple restarts ic, sorry ?"))
playlist = {}
current = {}
is_playing = {}

@client.event
async def on_ready():
    if not discord.opus.is_loaded():
        discord.opus.load_opus("/usr/local/lib/libopus.so")
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.command(pass_context=True)
async def leave(ctx):
    for voice in client.voice_clients:
        if voice.guild == ctx.guild:
            await voice.disconnect()
    playlist[ctx.guild] = []
    is_playing[ctx.guild] = False
    current[ctx.guild] = 0
    try:
        await ctx.message.delete()
    except:
        pass

@client.command(pass_context=True)
async def yt(ctx, url):
    if ctx.guild not in is_playing:
        is_playing[ctx.guild] = False
    if ctx.guild not in playlist:
        playlist[ctx.guild] = [url]
    else:
        playlist[ctx.guild].append(url)
    if not is_playing[ctx.guild]:
        author = ctx.message.author
        voice = await author.voice.channel.connect()
    await ctx.message.delete()
    if not is_playing[ctx.guild]:
        await play(ctx, voice)


async def play(ctx, voice):
    if ctx.guild not in current:
        current[ctx.guild] = 0

    opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    def my_after(error):
        current[ctx.guild] += 1
        print(current[ctx.guild], len(playlist[ctx.guild]))
        if current[ctx.guild] >= len(playlist[ctx.guild]):
            print("playlist end, leaving ...")
            asyncio.run_coroutine_threadsafe(ctx.invoke(leave), client.loop)
        else:
            asyncio.run_coroutine_threadsafe(play(ctx,voice), client.loop)
    
    is_playing[ctx.guild] = True
    with youtube_dl.YoutubeDL(opts) as ydl:
        song_info = ydl.extract_info(playlist[ctx.guild][current[ctx.guild]], download=False)
        audio = discord.FFmpegPCMAudio(song_info['url'])
        voice.play(audio, after=my_after)

@client.event
async def on_command_error(ctx, error):
    pass

async def run():
    await client.start(PARAMS["discord"]["jinx"])

loop.run_until_complete(run())
