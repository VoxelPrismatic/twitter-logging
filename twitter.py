# Twitter-Discord bot; Log your favorite Twitter accounts in Discord.
# Copyright (C) 2023, PRIZ ;]
#                    (aka VoxelPrismatic)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation version 2.
# The GNU General Public License version 3 does NOT apply to this
# software.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

tokens = [
    # Place Twitter API tokens here
]

followed = {
    # "account_one": [
    #     channel_id_1,
    #     channel_id_2,
    #     channel_id_3
    # ],
}

# Discord bot token
BOT_TOKEN = "bot_token_here"

# Which channels you can send a link to, the bot will save the tweet
tweet_link_grab_channels = [
]

TWEET_TIMEOUT = 15 #Seconds between fetches

# ----------------------------------------------------------- #
#                                                             #
#    WARNING: Do not modify any of the below code unless      #
#    you know EXACTLY what you are doing.                     #
#    Any changes regarding twitter tokens, discord tokens,    #
#    or followed accounts are above this point.               #
#                                                             #
# ----------------------------------------------------------- #

import io
import time
import discord
import asyncio
import requests
import dateutil, dateutil.parser
import random
import html
import aiohttp
import json
import traceback
from datetime import datetime
from discord.ext import commands
import threading
import re
import os
import subprocess
import signal
import traceback

try:
    os.listdir("tw-cache")
except:
    print("\x1b[91;1mWARNING:\x1b[0m Folder `tw-cache' does not exist. Videos will not be saved until this folder is created")
    print("\x1b[95;3mstarting in 5s so you have enough time to read this message")
    time.sleep(5)

bot = commands.Bot(
    command_prefix = "~",
    case_insensitive = True,
    intents = discord.Intents.all()
)

auth = {
    "Authorization": "Bearer " + random.choice(tokens)
}

tweet_exts = {
    "expansions": [
        "attachments.poll_ids",
        "attachments.media_keys",
        "author_id",
        "entities.mentions.username",
        "in_reply_to_user_id",
        "referenced_tweets.id",
        "referenced_tweets.id.author_id"
    ],
    "media.fields": [
        "duration_ms",
        "height",
        "media_key",
        "preview_image_url",
        "type",
        "url",
        "width",
        "public_metrics",
        "variants"
    ],
    "poll.fields": [
        "end_datetime",
        "id",
        "options",
        "voting_status"
    ],
    "tweet.fields": [
        "attachments",
        "author_id",
        "context_annotations",
        "conversation_id",
        "created_at",
        "entities",
        "id",
        "in_reply_to_user_id",
        "public_metrics",
        "possibly_sensitive",
        "referenced_tweets",
        "reply_settings",
        "source",
        "text",
        "withheld"
    ],
    "user.fields": [
        "profile_image_url",
        "name",
        "username"
    ]
}

tweet_ext = ""
for thing in tweet_exts:
    tweet_ext += ("&" if tweet_ext else "?") + thing + "=" + ",".join(tweet_exts[thing])

old_tweets = {}
parsed_tweets = []

def ffmpeg_args(sz = 640):
    return [
        "-vcodec", "libvpx-vp9",
        "-vf", f"scale='if(gt(iw,ih),{sz},-1)':'if(gt(iw,ih),-1,{sz})'",
        "-cpu-used", "-6",
        "-deadline", "realtime",
    ]

async def get_video(data, url):
    view_key = url.split("/")[-1].split(".")[0]

    infos = data["includes"]["media"][0]["variants"]
    # print("\x1b[94;1m" + json.dumps(infos, indent = 4) + "\x1b[0m")
    max_br = {"bit_rate": 0}
    for info in infos:
        if info["content_type"] == "video/mp4" and info["bit_rate"] >= max_br["bit_rate"]:
            max_br = info
    url = max_br["url"].split("?")[0]
    stream_loop = ["-stream_loop", "31"]
    if "duration_ms" in data["includes"]["media"][0]:
        dur = data["includes"]["media"][0]["duration_ms"]
        if dur < 18000:
            stream_loop = ["-stream_loop", str(int(32000 / dur) - 1)]
        else:
            stream_loop = []

    if not os.path.exists(f"./tw-cache/{view_key}.webm"):
        print(view_key)
        print("\x1b[92;1mLoop=" + str(stream_loop) + "\x1b[0m")
        print("\x1b[91;1m" + url + "\x1b[0m")
        szs = [720, 640, 512, 480, 360, 240, 120, 100, 86, 64]
        sz = szs.pop(0)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                open(f"./tw-cache/{view_key}.mp4", "wb+").write(await resp.content.read())
        proc = subprocess.Popen(["ffmpeg", *stream_loop, "-i", f"./tw-cache/{view_key}.mp4", *ffmpeg_args(sz), f"./tw-cache/{view_key}.webm", "-y"])
        print(proc.args)
        while proc.poll() is None:
            if os.path.exists(f"./tw-cache/{view_key}.webm") and os.stat(f"./tw-cache/{view_key}.webm").st_size > 1024 * 1024 * 24: # 24 MiB
                proc.send_signal(signal.SIGKILL)
                if stream_loop and int(stream_loop[1]) > 1:
                    stream_loop[1] -= 1
                    if stream_loop[1] == 0:
                        stream_loop = []
                else:
                    try:
                        sz = szs.pop(0)
                    except:
                        os.remove(f"./tw-cache/{view_key}.mp4")
                        return data["includes"]["media"][0]["preview_image_url"]
                print("\n\n\nproc\n\n\n")
                proc = subprocess.Popen(["ffmpeg", *stream_loop, "-i", f"./tw-cache/{view_key}.mp4", *ffmpeg_args(sz), f"./tw-cache/{view_key}.webm", "-y"])
                await asyncio.sleep(0.5)
            await asyncio.sleep(0.1)
    os.remove(f"./tw-cache/{view_key}.mp4")
    if os.stat(f"./tw-cache/{view_key}.webm").st_size > 1024 * 1024 * 24:
        return data["includes"]["media"][0]["preview_image_url"]

    return f"./tw-cache/{view_key}.webm"

async def get_image(sfw_embed, nsfw_embed, data, depth = 0):
    try:
        url = data["includes"]["media"][0]["url"]
    except:
        try:
            url = data["includes"]["tweets"][0]["urls"][0]["images"][0]["url"]
        except:
            try:
                url = data["includes"]["media"][0]["preview_image_url"]
                if "video_thumb" in url and depth == 0:
                    url = await get_video(data, url)
            except KeyError as ex:
                return
            except Exception as ex:
                print("\n\n\n\x1b[91;1m", ex, "\x1b[0m\n\n\n")
                return
    if not data["data"]["possibly_sensitive"]:
        sfw_embed.set_image(url = url)
    nsfw_embed.set_image(url = url)

def replace_item(block, key, url, sig, ins, pre, text, txt, parsed):
    ls = []
    parsed = []
    while block:
        i = block[0]
        for item in block:
            if len(item[key]) > len(i[key]):
                i = item
        ls.append(i)
        block.remove(i)
    for item in ls:
        if item[key] in parsed:
            continue
        parsed.append(item[key])
        if not text[item["start"]:item["end"]].startswith(sig) and item["end"] <= 1000:
            if sig in text[item["start"]:]:
                while not text[item["start"]:item["end"]].startswith(sig):
                    item["start"] += 1
                    item["end"] += 1
            else:
                while not text[item["start"]:item["end"]].startswith(sig) and item["start"] >= 0:
                    item["start"] -= 1
                    item["end"] -= 1
        st = ins + item[url]
        txt = txt.replace(
            text[item["start"]:item["end"]],
            f"[{st}]({pre}{item[key]})"
        )
    #print(st)
    return txt


def parse_text(tweet):
    text = tweet["text"]
    txt = html.unescape(text)
    parsed = []
    for t in "\\*~`[]|":
        txt = txt.replace(t, "\\" + t)
    try:
        txt = replace_item(tweet["entities"]["mentions"], "username", "username", "@", "@", "https://twitter.com/", text, txt, parsed)
    except KeyError as ex:
        #print(ex)
        pass
    try:
        txt = replace_item(tweet["entities"]["hashtags"], "tag", "tag", "#", "#", "https://twitter.com/hashtag/", text, txt, parsed)
    except KeyError as ex:
        #print(ex)
        pass
    try:
        txt = replace_item(tweet["entities"]["urls"], "url", "display_url", "http", "", "", text, txt, parsed)
    except KeyError as ex:
        #print(ex)
        pass

    return txt

async def parse_tweet(data, sfw_embed, nsfw_embed, bot, tw, prev, depth = 0):
    dan = data["includes"]["users"][0]
    dan_txt = parse_text(data["data"])
    dan_url = f"(https://twitter.com/{dan['username']}/status/{data['data']['id']})"
    await get_image(sfw_embed, nsfw_embed, data, depth)
    field = {}
    tt = data["data"]["author_id"] == tw and len(sfw_embed.fields) == 0
    tt_ = data["data"]["author_id"] == prev
    print("cur:", data["data"]["author_id"], "| tw:", tw, "| prev:", prev, "| depth=0:", len(sfw_embed.fields) == 0, "| cur=tw:", tt, "| cur=prev:", tt_)
    try:
        polls = ""
        for poll_opt in data["includes"]["polls"][0]["options"]:
            polls += f"\n> - {poll_opt['label']}"
        dan_txt += "\n\n> **POLL:**" + polls
    except:
        pass
    try:
        nsfw = data["data"]["possibly_sensitive"]
    except:
        nsfw = False

    needs_fix = True
    if "referenced_tweets" in data["data"]:
        needs_fix = False
        try:
            ref = data["data"]["referenced_tweets"][0]["type"]
            for n_d in data["includes"]["users"]:
                if n_d["id"] == data["includes"]["tweets"][0]["author_id"]:
                    not_dan = n_d
                    break
            if ref == "replied_to":
                if tt:
                    rt_head = f"Replied to __{esc(not_dan['name'])}__ [@{esc(not_dan['username'])}]:"
                elif tt_:
                    rt_head = f"And continued:"
                else:
                    rt_head = f"__{esc(dan['name'])}__ [@{esc(dan['username'])}] replied:"
                if polls: rt_head = rt_head[:-1] + " with a poll:"
                field = {
                    "name": rt_head,
                    "value": dan_txt + "\n\n[Link to thread]" + dan_url,
                    "inline": False
                }
            elif ref == "retweeted":
                if tt:
                    rt_head = f"Retweeted __{esc(not_dan['name'])}__ [@{esc(not_dan['username'])}]:"
                    data3 = await get_json(
                        f"https://api.twitter.com/2/tweets/{data['data']['referenced_tweets'][0]['id']}" + tweet_ext,
                        headers = auth
                    )
                    await get_image(sfw_embed, nsfw_embed, data3, depth)
                    try:
                        nsfw = nsfw or data3["data"]["possibly_senstive"]
                    except:
                        pass
                    dan_txt = parse_text(data3["data"])

                    if polls:
                        rt_head = rt_head[:-1] + "'s poll:"

                    try:
                        rt = data3["data"]["referenced_tweets"][0]["type"]
                        if rt == "quoted":
                            rt_head = rt_head[:-1] + "'s quote tweet:"
                        elif rt == "replied_to":
                            rt_head = rt_head[:-1] + "'s reply:"
                    except:
                        pass
                else:
                    if tt_:
                        rt_head = f"And retweeted the above:"
                    else:
                        rt_head = f"__{esc(dan['name'])}__ [@{esc(dan['username'])}] retweeted the above:"
                    dan_txt = ""
                field = {
                    "name": rt_head,
                    "value": dan_txt + "\n\n[Link to retweet]" + dan_url,
                    "inline": False
                }
            elif ref == "quoted":
                if tt:
                    rt_head = f"Quoted __{esc(not_dan['name'])}__ [@{esc(not_dan['username'])}] with:"
                elif tt_:
                    rt_head = f"And quoted with:"
                else:
                    rt_head = f"__{esc(dan['name'])}__ [@{esc(dan['username'])}] quoted with:"
                if polls: rt_head = rt_head[:-1] + " with a poll:"
                field = {
                    "name": rt_head,
                    "value": dan_txt.rsplit(" [twitter.com", 1)[0] + "\n\n[Link to quote]" + dan_url,
                    "inline": False
                }
            else:
                await bot.get_channel(1085394872149745804).send(
                    "<@481591703959240706> weird reference:",
                    file = discord.File(
                        io.BytesIO(json.dumps(references, indent = 4).encode()),
                        "references.json"
                    )
                )
                raise Exception
        except Exception as ex:
            print("\x1b[91;1mError in `parse_tweet()':")
            traceback.print_exception(type(ex), ex, ex.__traceback__)
            print("\x1b[0m")
            needs_fix = True

    if needs_fix:
        if tt:
            rt_head = f"Tweeted:"
        else:
            rt_head = f"__{esc(dan['name'])}__ [@{esc(dan['username'])}] tweeted:"
        if polls: rt_head = rt_head[:-1] + " a poll:"
        field = {
            "name": rt_head,
            "value": dan_txt + "\n\n[Link to tweet]" + dan_url,
            "inline": False
        }
    if nsfw:
        sfw_embed.add_field(
            name = field["name"],
            value = "**[!]** Possibly NSFW:\n||" + field["value"] + "||",
            inline = False
        )
    else:
        sfw_embed.add_field(
            **field
        )
    nsfw_embed.add_field(
        **field
    )
    print("return:", data["data"]["author_id"])
    return data["data"]["author_id"]

async def parse_thread(data, sfw_embed, nsfw_embed, bot, tw, prev = 0, recur = 0):
    try:
        references = data["data"]["referenced_tweets"]
        if recur < 5 and len(nsfw_embed) <= 5600 and len(sfw_embed) <= 5600:
            data2 = await get_json(
                f"https://api.twitter.com/2/tweets/{references[0]['id']}" + tweet_ext,
                headers = auth
            )
            prev = await parse_thread(data2, sfw_embed, nsfw_embed, bot, tw, prev, recur + 1)
            try:
                sfw_embed.set_thumbnail(url = sfw_embed.image.url)
                sfw_embed.set_image(url = discord.Embed.Empty)
                nsfw_embed.set_thumbnail(url = nsfw_embed.image.url)
                nsfw_embed.set_image(url = discord.Embed.Empty)
            except:
                pass
    except Exception as ex:
        print(f"\x1b[91;1m{type(ex)} {ex}\x1b[0m")
    prev = await parse_tweet(data, sfw_embed, nsfw_embed, bot, tw, prev, recur)
    return prev

def esc(st):
    for c in "_*`|~":
        st = st.replace(c, "\\" + c)
    for c in "#@:":
        st = st.replace(c, c + "\u200b")
    return st

is_done = True
passed = 0

async def get_json(*a, **kw):
    global auth
    while True:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(*a, **kw) as resp:
                try:
                    return await resp.json()
                except Exception as ex:
                    txt = await resp.read()
                    if txt in [b'Rate limit exceeded\n', b'upstream connect error or disconnect/reset before headers. reset reason: connection failure', b'']:
                        print("Rate limit")
                        auth["Authorization"] = "Bearer " + random.choice(tokens)
                        try:
                            kw["headers"]["Authorization"] = auth["Authorization"]
                        except:
                            pass
                        await asyncio.sleep(5)
                        continue
                    print(txt)
                    print(resp.headers)
                    raise ex

async def get_usernames(*ids):
    names = {}
    for i in ids:
        try:
            names[i]
        except:
            names[i] = (await get_json(
                f"https://api.twitter.com/2/users/{i}",
                headers = auth
            ))["data"]["username"].replace("_", "\\_").replace("*", "\\*")
    return names

current_tw = None

async def on_tweet(bot):

    global old_tweets, passed, auth, auth2, current_tw
    send_to = {}
    for user_id in tweeters:
        for channel_id in followed[tweeters[user_id]]:
            try:
                if channel_id not in send_to[user_id]:
                    send_to[user_id].append(channel_id)
            except KeyError:
                send_to[user_id] = [channel_id]

    #print("Listening for tweets")
    tasks = []
    for tweeter in send_to:
        tasks.append(
            asyncio.create_task(
                do_tweet(bot, tweeter, send_to)
            )
        )
    await asyncio.gather(*tasks)
    passed = 1

async def embed_tweet(tID):
    data = await get_json(
        f"https://api.twitter.com/2/tweets/{tID}" + tweet_ext,
        headers = auth
    )
    print(json.dumps(data, indent = 4))
    op = data["includes"]["users"][0]
    tDT = dateutil.parser.isoparse(data["data"]["created_at"])
    sfw_embed = discord.Embed()

    sfw_embed.timestamp = tDT
    sfw_embed.set_footer(
        icon_url = "https://cdn.discordapp.com/avatars/748737393372299297/418fb449a427fd1fdefc42d169346394.png?size=256",
        text = "Logging by PRIZ ;]"
    )
    sfw_embed.color = discord.Color(0x0088ff)
    sfw_embed.set_author(
        name = f"{op['name']} [@{op['username']}]",
        icon_url = f"{op['profile_image_url']}",
        url = f"https://twitter.com/{op['username']}"
    )

    nsfw_embed = sfw_embed.copy()
    await parse_thread(data, sfw_embed, nsfw_embed, bot, data["data"]["author_id"])

    return sfw_embed, nsfw_embed

async def send_tweet(channel, sfw_embed, nsfw_embed):
    f = None

    if channel.is_nsfw():
        embed = nsfw_embed
    else:
        embed = sfw_embed

    if embed.image and embed.image.url.endswith(".webm"):
        f = discord.File(embed.image.url)
        embed.set_image(url = None)
    return await channel.send(embed = embed, file = f)

async def do_tweet(bot, tweeter, send_to):
    global current_tw
    try:
        data = await get_json(
            f"https://api.twitter.com/1.1/statuses/user_timeline.json?user_id={tweeter}&count=1",
            headers = auth
        )
        current_tw = str(tweeter)
        #print(old_tweets)
        #print(json.dumps(data, indent = 4))
        try:
            tID = data[0]["id"]
        except:
            return
        try:
            old_tweets[tweeter]
        except KeyError:
            old_tweets[tweeter] = tID
        #print(tID)
        good_tID = tID
        while tID > old_tweets[tweeter] and tID not in parsed_tweets:
            sfw_embed, nsfw_embed = await embed_tweet(tID)
            parsed_tweets.append(tID)
            for channel in send_to[tweeter]:
                try:
                    channel = bot.get_channel(channel)
                    await send_tweet(channel, sfw_embed, nsfw_embed)
                except Exception as ex:
                    print(ex)
                pass
            #exit()
            data = await get_json(
                f"https://api.twitter.com/1.1/statuses/user_timeline.json?user_id={tweeter}&count=1&max_id={tID}",
                headers = auth
            )
            tID = data[0]["id"]
        old_tweets[tweeter] = good_tID
    except Exception as ex:
        raise ex

@bot.event
async def on_ready():
    print("Here we go!")
    while True:
        try:
            await on_tweet(bot)
        except Exception as ex:
            print(ex)
        await asyncio.sleep(TWEET_TIMEOUT)
            # for x in range(15, -1, -1):
                # print(f"\x1b[1Asleeping... {x}s left\x1b[J")
                # await asyncio.sleep(1)

@bot.event
async def on_message(msg):
    if msg.channel.id not in tweet_link_grab_channels or msg.author.id == bot.user.id:
        return
    if msg.content == "" or re.sub(f"https?://(www\.)?twitter.com/[\d\w_-]+/status/\d+(\?.+)?", "", msg.content):
        return
    ld_msg = await msg.channel.send("Just a sec...")

    sfw_embed, nsfw_embed = await embed_tweet(int(msg.content.split("/status/")[1].split("?")[0]))
    await send_tweet(msg.channel, sfw_embed, nsfw_embed)

    await ld_msg.delete()

tweeters = {}
async def fetch_tweeters():
    d = await get_json(
        f"https://api.twitter.com/2/users/by?usernames={','.join(list(followed))}&user.fields=profile_image_url",
        headers = auth
    )
    for thing in d["data"]:
        print(json.dumps(thing, indent = 4))
        tweeters[thing["id"]] = thing["username"].lower()


asyncio.run(fetch_tweeters())

bot.run(BOT_TOKEN)
