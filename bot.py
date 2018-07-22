from keys.config import PARAMS

import youtube_dl
import asyncio
import discord
from discord.ext import commands

client = commands.Bot(command_prefix='-')


@client.event
async def on_ready():
    if not discord.opus.is_loaded():
        discord.opus.load_opus("/usr/local/lib/libopus.so")
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.command(pass_context=True)
async def yt(ctx, url):
    author = ctx.message.author
    voice = await author.voice.channel.connect()
    opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(opts) as ydl:
        song_info = ydl.extract_info(url, download=False)
        audio = discord.FFmpegPCMAudio(song_info['url'])
        voice.play(audio)

@client.command(pass_context=True)
async def leave(ctx):
    for voice in client.voice_clients:
        if voice.guild == ctx.message.guild:
            await voice.disconnect()

async def run():
    await client.start(PARAMS["discord"]["jinx"])

loop = asyncio.get_event_loop()
loop.run_until_complete(run())

