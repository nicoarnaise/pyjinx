import discord
import asyncio

client = discord.Client()


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
async def on_message(message):
    if message.content.startswith('!test'):
        voice = await client.join_voice_channel(message.author.voice.voice_channel)
        player = await voice.create_ytdl_player('https://www.youtube.com/watch?v=d62TYemN6MQ')
        player.start()

client.run('Mjk3MTI3MzM4MTg4MDc5MTA1.Daf5HQ.Bj_eHukXITK77SgnhBK4dF24lBo')
