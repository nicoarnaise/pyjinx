from keys.config import PARAMS

import discord
from discord.ext import commands
from player import *

loop = asyncio.get_event_loop()
client = commands.Bot(command_prefix='-', loop=loop, activity=discord.Game("Im a DJ again <3"))
youtube_player = YoutubePlayer(client)


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
    youtube_player.playlist[ctx.guild.id] = []
    youtube_player.is_playing[ctx.guild.id] = False
    youtube_player.current[ctx.guild.id] = 0
    try:
        await ctx.message.delete()
    except:
        pass


@client.command(pass_context=True)
async def yt(ctx, *, url):
    if not YoutubePlayer.is_youtube_link(url):
        await youtube_player.search_video(ctx.message, url, False)
    else:
        await youtube_player.add_to_playlist(ctx, url, False)
    await ctx.message.delete()


@client.command(pass_context=True)
async def ytp(ctx, *, url):
    if not YoutubePlayer.is_youtube_link(url):
        await youtube_player.search_video(ctx.message, url, True)
    else:
        await youtube_player.add_to_playlist(ctx, url, True)
    await ctx.message.delete()


@client.event
async def on_command_error(ctx, error):
    pass


@client.event
async def on_reaction_add(reaction, user):
    if not reaction.me:
        guild_id = reaction.message.guild.id
        delete = True
        if reaction.message.id in youtube_player.servers[guild_id]["search_map"]:
            if reaction == discord.Reaction(emoji=ONE):
                url = youtube_player.servers[guild_id]["search_map"][reaction.message.id]["urls"][0]
                playlist = youtube_player.servers[guild_id]["search_map"][reaction.message.id]["playlist"]
                await youtube_player.add_to_playlist(youtube_player.ctx[guild_id], url, playlist)
                await reaction.message.delete()
                delete=False
            if reaction == discord.Reaction(emoji=TWO):
                url = youtube_player.servers[guild_id]["search_map"][reaction.message.id]["urls"][1]
                playlist = youtube_player.servers[guild_id]["search_map"][reaction.message.id]["playlist"]
                await youtube_player.add_to_playlist(youtube_player.ctx[guild_id], url, playlist)
                await reaction.message.delete()
                delete = False
            if reaction == discord.Reaction(emoji=THREE):
                url = youtube_player.servers[guild_id]["search_map"][reaction.message.id]["urls"][2]
                playlist = youtube_player.servers[guild_id]["search_map"][reaction.message.id]["playlist"]
                await youtube_player.add_to_playlist(youtube_player.ctx[guild_id], url, playlist)
                await reaction.message.delete()
                delete = False
            if reaction == discord.Reaction(emoji=FOUR):
                url = youtube_player.servers[guild_id]["search_map"][reaction.message.id]["urls"][3]
                playlist = youtube_player.servers[guild_id]["search_map"][reaction.message.id]["playlist"]
                await youtube_player.add_to_playlist(youtube_player.ctx[guild_id], url, playlist)
                await reaction.message.delete()
                delete = False
            if reaction == discord.Reaction(emoji=FIVE):
                url = youtube_player.servers[guild_id]["search_map"][reaction.message.id]["urls"][4]
                playlist = youtube_player.servers[guild_id]["search_map"][reaction.message.id]["playlist"]
                await youtube_player.add_to_playlist(youtube_player.ctx[guild_id], url, playlist)
                await reaction.message.delete()
                delete = False
            if reaction == discord.Reaction(emoji=NPAGEBTN):
                msg = youtube_player.servers[guild_id]["search_map"][reaction.message.id]
                suffix = msg['suffix']
                playlist = msg['playlist']
                token = msg['next']
                await youtube_player.next_page(msg, suffix, playlist, token)
            if reaction == discord.Reaction(emoji=PPAGEBTN):
                msg = youtube_player.servers[guild_id]["search_map"][reaction.message.id]
                suffix = msg['suffix']
                playlist = msg['playlist']
                token = msg['prev']
                await youtube_player.next_page(msg, suffix, playlist, token)
            if reaction == discord.Reaction(emoji=CANCEL):
                await reaction.message.delete()
                delete = False

        if 'jinxMessage' in youtube_player.servers[guild_id] and reaction.message.id == youtube_player.servers[guild_id]['jinxMessage']:
            if reaction == discord.Reaction(emoji=NEXTBTN):
                youtube_player.current[guild_id] += 1
                await youtube_player.play(youtube_player.voice[guild_id], guild_id)
            if reaction == discord.Reaction(emoji=PREVBTN):
                youtube_player.current[guild_id] -= 1
                await youtube_player.play(youtube_player.voice[guild_id], guild_id)
            if reaction == discord.Reaction(emoji=REPLAYBTN):
                await youtube_player.play(youtube_player.voice[guild_id], guild_id)
            if reaction == discord.Reaction(emoji=PAUSEBTN):
                if 'paused' not in youtube_player.servers[guild_id] or not youtube_player.servers[guild_id]['paused']:
                    youtube_player.voice[guild_id].pause()
                    youtube_player.servers[guild_id]['paused'] = True
                else:
                    youtube_player.voice[guild_id].resume()
            if reaction == discord.Reaction(emoji=STOPBTN):
                print("stop asked, leaving ...")
                # delete jinx youtube player message
                await youtube_player.servers[guild_id]['jinxMessage'].delete()
                # make jinx leave voice chat
                await youtube_player.ctx[guild_id].invoke(leave)
                delete = False
            if reaction == discord.Reaction(emoji=LOOPBTN):
                youtube_player.servers[guild_id]['infinite'] = not youtube_player.servers[guild_id]['infinite']
                delete = False
        if delete:
            await reaction.message.remove_reaction(reaction, user)


async def run():
    await client.start(PARAMS["discord"]["jinx"])

loop.run_until_complete(run())
