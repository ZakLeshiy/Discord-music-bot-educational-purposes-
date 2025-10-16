import discord
from discord.ext import commands
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
import discord.opus



sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id="yourSPOTIFY_CLIENT_ID"
    client_secret="yourSPOTIFY_CLIENT_SECRET"
))

# discord settings
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

queue = []  # track queue
is_playing = False

FFMPEG_PATH = r"your ffmpeg path"
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}


# included youtube and spotify parsing
@bot.command()
async def play(ctx, *, url):
    #function for songs
    global queue, is_playing

    voice_client = ctx.voice_client
    if not voice_client:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            voice_client =await channel.connect()
            await ctx.send(f"✅ joined {channel}")
        else:
            await ctx.send("❌ no channel available")
            return

    # creating queue
    song_list = []

    if "spotify.com" in url:
        await ctx.send("🎧 adding tracks for spotify...")
        if "track" in url:
            track = sp.track(url)
            title = f"{track['name']} {track['artists'][0]['name']}"
            song_list.append({"title": title})
        elif "playlist" in url:
            playlist = sp.playlist(url)
            for item in playlist["tracks"]["items"]:
                track = item["track"]
                title = f"{track['name']} {track['artists'][0]['name']}"
                song_list.append({"title": title})
        elif "album" in url:
            album = sp.album(url)
            for track in album["tracks"]["items"]:
                title = f"{track['name']} {track['artists'][0]['name']}"
                song_list.append({"title": title})
    else:
        # youtube irl or search request
        song_list.append({"title": url, "source": url})

    # adding tracks from request
    queue.extend(song_list)
    await ctx.send(f"📀 added {len(song_list)} tracks for the queue.")

    # playing the queue
    if not is_playing and len(queue) > 0:
        is_playing = True

        while len(queue) > 0:
            song = queue.pop(0)
            await ctx.send(f"🎵playing: **{song['title']}**")

            url2 = song.get('source', song['title'])

            # finding the most possible correlation for youtube
            if "youtube.com" in url2 or "youtu.be" in url2 or not url2.startswith("http"):
                with yt_dlp.YoutubeDL({
                    'format': 'bestaudio[ext=m4a]/bestaudio/best',
                    'noplaylist': True,
                    'quiet': True,
                    'default_search': 'ytsearch'
                }) as ydl:
                    try:
                        info = ydl.extract_info(url2, download=False)
                        if 'entries' in info:
                            info = info['entries'][0]
                        url2 = info['url']  # strait play for ffmpeg
                    except Exception as e:
                        await ctx.send(f"⚠️error: {song['title']}\n{e}")
                        continue

            # -youtube playing through ffmpeg
            try:
                source = discord.FFmpegPCMAudio(
                    url2,
                    executable=FFMPEG_PATH,
                    **FFMPEG_OPTIONS
                )
                voice_client.play(source)
                # waiting for end
                while voice_client.is_playing() or voice_client.is_paused():
                    await asyncio.sleep(1)
            except Exception as e:
                await ctx.send(f"⚠️error: {song['title']}\n{e}")
                continue

        is_playing = False
        await ctx.send("🚫ended")

#pause command
@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ pause")

#resume command
@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ resume")


#skip command
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️skip")


#disconnect
@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋disconnect")


# 🔑 Запуск бота


bot.run('your bot id')
