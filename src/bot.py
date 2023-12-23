import discord
import os
import asyncio
import ffmpeg
#I like cats
import pytube
import yt_dlp as youtube_dl
from discord.ext.bridge import bot
from dotenv import load_dotenv
from discord.ext import bridge
from collections import deque
from discord.ext import commands

from pytube import YouTube

load_dotenv()


class TRSWatcherBot(bridge.Bot):
    TOKEN = os.getenv('TOKEN')
    intents = discord.Intents.all()

    queue = deque()
    paused = False
    connected = False
    currentlyPlaying = " "


client = TRSWatcherBot(intents=TRSWatcherBot.intents, command_prefix='!')
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}


@client.listen()
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for trouble."))
    print('Logged in as ' + client.user.name)


@client.bridge_command(description="Ping, pong!")
async def ping(ctx):
    latency = (str(client.latency).split('.')[1][1:3])
    await ctx.respond(f"Pong! Bot has a latency of {latency} ms")


# https://github.com/Dx-B
@client.bridge_command(description="Check server activity.")
async def status(ctx):
    await ctx.respond(f"Server is online!")


@client.bridge_command(description="Roll credits!")
async def author(ctx):
    await ctx.respond(f"Bot Version 1.0.0, Developed by Dx-B \"https://github.com/Dx-B\"")


@client.bridge_command(description="Makes the bot join the voice channel.")
async def join(ctx):
    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)
    else:
        await ctx.send("You are not connected to a voice channel.")


@client.bridge_command(description="Makes the bot leave the voice channel.")
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@client.bridge_command(description="Search for and play a video.", aliases=['p', 'P'])
async def play(ctx, *, query=None):
    if query is None:  # If no query is specified
        await ctx.send("Please specify a song name or URL.")
    else:
        try:
            YTDL_OPTIONS = {
                'format': 'bestaudio/best',
                'extractaudio': True,
                'audioformat': 'mp3',
                'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
                'restrictfilenames': True,
                'noplaylist': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'quiet': True,
                'no_warnings': True,
                'default_search': 'ytsearch',
                'source_address': '0.0.0.0',
            }

            with youtube_dl.YoutubeDL(YTDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)
                if 'entries' in info and len(info['entries']) > 0:
                    url = info['entries'][0]['webpage_url']
                    # Add the song to the queue
                    TRSWatcherBot.queue.append(url)
                    await ctx.send(f"Added {YouTube(url).title} to the queue {'(' + url + ')'}")
                    # If the bot is not already playing, start playing the song
                    if not ctx.voice_client or not ctx.voice_client.is_playing():
                        TRSWatcherBot.currentlyPlaying = TRSWatcherBot.queue[0]
                        await play_song(ctx)
                else:
                    await ctx.send(f"{query} was not found. Did you spell it correctly?")
        except commands.MissingRequiredArgument:
            await ctx.send("Please specify a song name or URL.")


@client.bridge_command(description="Play the song at the specified queue position.")
async def playat(ctx, *, position: int):
    if position > len(TRSWatcherBot.queue):
        await ctx.send("There are only " + str(len(TRSWatcherBot.queue)) + " songs in the queue.")
        return
    TRSWatcherBot.currentlyPlaying = TRSWatcherBot.queue[position - 1]
    ctx.voice_client.stop()
    await ctx.send("Now playing: **" + YouTube(TRSWatcherBot.currentlyPlaying).title + "**")
    await play_song(ctx)


async def play_song(ctx):
    # Check if the queue is empty
    if len(TRSWatcherBot.queue) == 0:
        await ctx.send("The queue is empty. Use the `play` command to add songs.")
        return

    # Get the URL of the next song in the queue
    url = TRSWatcherBot.queue.popleft()
    # Connect to the voice channel
    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        voice_client = await voice_channel.connect()
        TRSWatcherBot.connected = True
        print("//DEBUG: Not connected but got connected.")
        audio_source = discord.FFmpegOpusAudio(YouTube(url).streams.get_audio_only().url,
                                               before_options
                                               ="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                               options="-vn")
        # Play the audio in the voice channel
        print("Now attempting to play: " + YouTube(url).title)
        voice_client.play(audio_source,
                          after=lambda e: asyncio.run_coroutine_threadsafe(play_song(ctx), voice_client.loop))

    else:
        print("//DEBUG: The bot is currently connected to a voice channel: Attempting to play.")
        audio_source = discord.FFmpegOpusAudio(YouTube(url).streams.get_audio_only().url,
                                               before_options
                                               ="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                               options="-vn")
        voice_client = ctx.voice_client

        # Play the audio in the voice channel
        print("Now attempting to play: " + YouTube(url).title)
        voice_client.play(audio_source,
                          after=lambda e: asyncio.run_coroutine_threadsafe(play_song(ctx), voice_client.loop))


@client.bridge_command(description="Pause the current video")
async def pause(ctx):
    # Check if the bot is connected to a voice channel and if audio is currently playing
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send('Playback paused')
        TRSWatcherBot.paused = True
    else:
        await ctx.send("I'm not currently playing any audio.")


@client.bridge_command(description="Stop the current video")
async def stop(ctx):
    # Check if the bot is connected to a voice channel and if audio is currently playing
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send('Playback stopped')
    else:
        await ctx.send("I'm not currently playing any audio.")


@client.bridge_command(description="Resume the currently paused audio.")
async def resume(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Resumed the audio.")
    else:
        await ctx.send("There is no audio paused to resume.")


@client.bridge_command(description="Skip the current video.")
async def skip(ctx):
    ctx.voice_client.stop()
    if len(TRSWatcherBot.queue) != 0:
        await ctx.send("Skipping: **" + YouTube(TRSWatcherBot.currentlyPlaying).title + "**")
        await play_song(ctx)
        return
    else:
        ctx.send("There are no songs to skip. Use the `play` command to add songs.")


@client.bridge_command(description="Display the music queue.")
async def queue(ctx):
    await ctx.send("Currently playing: **" + YouTube(TRSWatcherBot.currentlyPlaying).title + "**")
    if len(TRSWatcherBot.queue) == 0:
        await ctx.send("There are no other songs in the queue.")
        return

    queue_list = list(TRSWatcherBot.queue)
    queue_message = "```\n"
    for i, url in enumerate(queue_list, start=0):
        queue_message += f"{i + 1}. {YouTube(url).title}\n"
    queue_message += "```"

    await ctx.send(f"Music Queue:\n{queue_message}")


@client.bridge_command(description="Clear the music queue.")
async def clear(ctx):
    TRSWatcherBot.queue.clear()
    await ctx.send("Cleared the music queue.")


@client.bridge_command(description="Remove a song from the queue.")
async def remove(ctx, position):
    if position.isdigit():
        position = int(position)
        if len(TRSWatcherBot.queue) >= position:
            await ctx.send("Removed: **" + YouTube(TRSWatcherBot.queue[position - 1]).title + "**")
            TRSWatcherBot.queue.remove(TRSWatcherBot.queue[position - 1])
        else:
            await ctx.send("There is no song at that position.")


async def main_bot():
    await client.start(TRSWatcherBot.TOKEN)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(main_bot()))
