from keys.config import PARAMS

import discord
from discord.ext import commands
from player import *
import asyncio

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
async def chan(ctx):
    youtube_player.set_show_chan(ctx.guild.id, show_chan_id=ctx.message.channel.id)
    await ctx.message.channel.send("Chan set as default.\nFor playing music, please do -yt <youtube_link> :heart:", delete_after=15)
    await ctx.message.delete()


@client.command(pass_context=True)
async def yt(ctx, *, url):
    if not YoutubePlayer.is_youtube_link(url):
        print("searching ", url)
        await youtube_player.search_video(ctx, url, False)
    else:
        print("playing ", url)
        await youtube_player.add_to_playlist(ctx, url, False)
    await ctx.message.delete()


@client.command(pass_context=True)
async def ytp(ctx, *, url):
    if not YoutubePlayer.is_youtube_link(url):
        await youtube_player.search_video(ctx, url, True)
    else:
        await youtube_player.add_to_playlist(ctx, url, True)
    await ctx.message.delete()


@client.event
async def on_command_error(ctx, error):
    pass


@client.event
async def on_reaction_add(reaction, user):
    if reaction.count > 1 and reaction.me:
        guild_id = reaction.message.guild.id
        delete = True
        if reaction.message.id in youtube_player.ctx:
            context = youtube_player.ctx[reaction.message.id]
            req_mess_id = context.message.id
            print(req_mess_id)
            if reaction.emoji == ONE:
                url = youtube_player.servers[guild_id]["search_map"][req_mess_id]["urls"][0]
                playlist = youtube_player.servers[guild_id]["search_map"][req_mess_id]["playlist"]
                await youtube_player.add_to_playlist(context, url, playlist)
                await reaction.message.delete()
                delete=False
            if reaction.emoji == TWO:
                url = youtube_player.servers[guild_id]["search_map"][req_mess_id]["urls"][1]
                playlist = youtube_player.servers[guild_id]["search_map"][req_mess_id]["playlist"]
                await youtube_player.add_to_playlist(context, url, playlist)
                await reaction.message.delete()
                delete=False
            if reaction.emoji == THREE:
                url = youtube_player.servers[guild_id]["search_map"][req_mess_id]["urls"][2]
                playlist = youtube_player.servers[guild_id]["search_map"][req_mess_id]["playlist"]
                await youtube_player.add_to_playlist(context, url, playlist)
                await reaction.message.delete()
                delete=False
            if reaction.emoji == FOUR:
                url = youtube_player.servers[guild_id]["search_map"][req_mess_id]["urls"][3]
                playlist = youtube_player.servers[guild_id]["search_map"][req_mess_id]["playlist"]
                await youtube_player.add_to_playlist(context, url, playlist)
                await reaction.message.delete()
                delete=False
            if reaction.emoji == FIVE:
                url = youtube_player.servers[guild_id]["search_map"][req_mess_id]["urls"][0]
                playlist = youtube_player.servers[guild_id]["search_map"][req_mess_id]["playlist"]
                await youtube_player.add_to_playlist(context, url, playlist)
                await reaction.message.delete()
                delete=False
            if reaction.emoji == NPAGEBTN:
                msg = youtube_player.servers[guild_id]["search_map"][req_mess_id]
                suffix = msg['suffix']
                playlist = msg['playlist']
                token = msg['next']
                await youtube_player.next_page(context, suffix, playlist, token)
            if reaction.emoji == PPAGEBTN:
                msg = youtube_player.servers[guild_id]["search_map"][req_mess_id]
                suffix = msg['suffix']
                playlist = msg['playlist']
                token = msg['prev']
                await youtube_player.next_page(context, suffix, playlist, token)
            if reaction.emoji == CANCEL:
                await reaction.message.delete()
                delete = False

        if 'jinxMessage' in youtube_player.servers[guild_id] and reaction.message.id == youtube_player.servers[guild_id]['jinxMessage'].id:
            print('playMessage')
            if reaction.emoji == NEXTBTN:
                print('next')
                youtube_player.current[guild_id] += 1
                youtube_player.voice[guild_id].pause()
                await youtube_player.play(youtube_player.voice[guild_id], guild_id)
            if reaction.emoji == PREVBTN:
                print('prev')
                youtube_player.current[guild_id] -= 1
                if youtube_player.current[guild_id] < 0:
                    youtube_player.current[guild_id] = 0
                youtube_player.voice[guild_id].pause()
                await youtube_player.play(youtube_player.voice[guild_id], guild_id)
            if reaction.emoji == REPLAYBTN:
                print('replay')
                youtube_player.voice[guild_id].pause()
                await youtube_player.play(youtube_player.voice[guild_id], guild_id)
            if reaction.emoji == PAUSEBTN:
                print('pause')
                if 'paused' not in youtube_player.servers[guild_id] or not youtube_player.servers[guild_id]['paused']:
                    youtube_player.voice[guild_id].pause()
                    youtube_player.servers[guild_id]['paused'] = True
                else:
                    youtube_player.voice[guild_id].resume()
                    youtube_player.servers[guild_id]['paused'] = False
            if reaction.emoji == STOPBTN:
                print("stop asked, leaving ...")
                # delete jinx youtube player message
                await youtube_player.servers[guild_id]['jinxMessage'].delete()
                # make jinx leave voice chat
                await youtube_player.ctx[guild_id].invoke(leave)
                delete = False
            if reaction.emoji == LOOPBTN:
                print('loop')
                if 'infinite' not in youtube_player.servers[guild_id]:
                    youtube_player.servers[guild_id]['infinite'] = True
                else:
                    youtube_player.servers[guild_id]['infinite'] = not youtube_player.servers[guild_id]['infinite']
                await youtube_player.edit_embed(guild_id)

        if delete:
            await reaction.message.remove_reaction(reaction, user)


async def run():
    await client.start(PARAMS["discord"]["jinx"])

loop.run_until_complete(run())
