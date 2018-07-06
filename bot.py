import discord

client = discord.Client()


@client.event
async def on_ready():
    if not discord.opus.is_loaded():
        discord.opus.load_opus()
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
async def on_message(message):
    if message.content.startswith('!test'):
        voice = await client.join_voice_channel(message.author.voice.voice_channel)
        player = await voice.create_ytdl_player('https://www.youtube.com/watch?v=xfUa4IVRZFI')
        player.start()

client.run('Mjk3MTI3MzM4MTg4MDc5MTA1.Daf5HQ.Bj_eHukXITK77SgnhBK4dF24lBo')
