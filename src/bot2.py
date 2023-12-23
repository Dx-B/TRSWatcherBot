import discord
from discord.ext import commands
import youtube_dl
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # needed for your bot

bot = commands.Bot(command_prefix='*', intents=intents)
print('Logged in as')
print("Bot2")
# These are options for the youtube dl, not needed actually but are recommended
ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'force-ipv4': True,
    'preferredcodec': 'mp3',
    'cachedir': False

}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdlopts)


@bot.command()
async def play(ctx, *, query):
    try:
        voice_channel = ctx.author.voice.channel  # checking if user is in a voice channel
    except AttributeError:
        return await ctx.send(
            "No channel to join. Make sure you are in a voice channel.")  # member is not in a voice channel

    permissions = voice_channel.permissions_for(ctx.me)
    if not permissions.connect or not permissions.speak:
        await ctx.send("I don't have permission to join or speak in that voice channel.")
        return

    voice_client = ctx.guild.voice_client
    if not voice_client:
        await voice_channel.connect()
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url=query,
                                                                      download=False))  # extracting the info and not downloading the source

    title = data['title']  # getting the title
    song = data['url']  # getting the url

    if 'entries' in data:  # checking if the url is a playlist or not
        data = data['entries'][0]  # if its a playlist, we get the first item of it

    try:
        voice_client.play(
            discord.FFmpegPCMAudio(source=song, **ffmpeg_options, executable="ffmpeg"))  # playing the audio
    except Exception as e:
        print(e)

    await ctx.send(f'**Now playing:** {title}')  # sending the title of the video


bot.run('MTE4NzQ5ODgzNjY4ODY1MDMzMA.GX8BzE.z8faIbVjqUPkemImp_Vq6ekY3q5udvNvziGhcU')