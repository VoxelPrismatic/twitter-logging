# This bot
A mostly self contained discord bot which can log Twitter accounts into any channel.

## Contents
- [This bot](#This-bot)
  - [Features](#Features)
- [Set up](#Set-up)
- [Customization](#Customization)
  - [Creating Twitter API keys](#Creating-Twitter-API-keys)
  - [Tweeters](#Tweeters)
  - [Discord bot token](#Discord-bot-token)
  - [Twitter link grabbing](#Twitter-link-grabbing)
  - [Tweet timeout](#Tweet-timeout)
  - [Other notes](#Other-notes)
- [Licensing](#Licensing)

## Features
- Saves video
  - Note: This does take up storage space on your device. Please have a folder called `tw-cache` in the same directory as this bot.
- Saves images
  - Note: This does NOT take up local storage, this is caching straight from twitter.
- Thread interpreting
  - Gives context up to 5 tweets in history
- Displays poll options
- Send links in specified channels to log specific tweets
- Thumbnails provide previews to the image from the previous tweet
- Links reveal the URL, so you know what you're clicking on.
- `@accounts`, `#hashtags` and whatever `$cashtags` are all produce valid links
- Easy to read and understand
<div style="display: flex">
    <img src="https://user-images.githubusercontent.com/45671764/231582339-8e0df70c-39c4-4903-8b68-684bef3f9ee1.png" width="256px"/>
    <img src="https://user-images.githubusercontent.com/45671764/231584752-5ee161ad-52f5-4d02-8d7d-1a999ccc4f5b.png" width="256px"/>
    <img src="https://user-images.githubusercontent.com/45671764/231585107-5ac9182c-cf47-4b63-8d1a-8eb7fa69eb80.png" width="256px"/>
    <img src="https://user-images.githubusercontent.com/45671764/231582640-552d4a85-d8bf-47cf-819e-bb75e48df0c4.png" width="256px"/>
</div>

## Notes
This bot is intended for live feeds, so it will not display likes, comments, retweets or poll statistics.

While you can send specific links to save them, it uses the same underlying system to log tweets and will not display those statistics.

It is a trade-off you must be willing to make when using this bot.

# Set up
**This build is guaranteed to work for Linux. I cannot say anything for macOS or Windows.**
1. Install [Python](https://python.org/download), 3.9+ should do just fine
2. Be sure you have [FFmpeg](https://ffmpeg.org) installed
   - Linux: Should be installed by default. If not, then:
     - Ubuntu/Debian: `apt install ffmpeg`
     - Arch: `pacman -S ffmpeg`
     - Fedora/RHeL/RedHat: `dnf install ffmpeg`
     - Most likely `ffmmpeg` with your package manager
   - macOS:
     - Try `brew install ffmpeg` or install directly from [FFmpeg.org](https://ffmpeg.org)
   - Windows:
     1. Install from [FFmpeg.org](https://ffmpeg.org)
     2. Place `ffmpeg`, `ffplay` and `ffprobe` either in the `C:\Windows` folder, or in the same folder with the `twitter.py` file
3. Copy `twitter.py` into a folder of your choice
4. Create a folder named `tw-cache` in the same place as `twitter.py`
   - This is the location to save videos. If you choose to opt out of this step, videos will not be saved, and only thumbnails shown.
5. Install dependencies
   - Windows:
     - `py -m pip install -U discord.py aiohttp aiohttp[speedups] requests`
   - Linux:
     - `python3 -m pip install -U discord.py aiohttp aiohttp[speedups] requests`
   - macOS:
     - I don't have a mac, try Linux first, then Windows

# Customization
## Creating Twitter API keys
This bot interacts with the Twitter API directly, it does NOT scrape the site.

You will need to create to create at least one account at the [Twitter API Dashboard](https://developer.twitter.com/en/portal/dashboard).
The API in question **must be API v2**, v1.1 will not work.
If I recall correctly, each Twitter account can have at most one API v2 bot. 

Having more tokens means less interruptions when tracking lots of tweeters. The bot will automatically switch to
the next token if the current one is hitting a rate limit.

In the code, you'll find this section at the top:
```py
tokens = [
    # Place Twitter API tokens here
]
```
In here, place your Twitter API tokens, for example:
```py
tokens = [
    "AAAAAAAAAAAAAAAAldhalkjhkf...",
    "AAAAAAAAAAAAAAAAasdyfjefsk...",
    "AAAAAAAAAAAAAAAAihflkheihk..."
]
```
Please note that the tokens listed above are not valid tokens. You should replace everything within the
quotation marks with the token provided by Twitter, including the ellipsis.

## Tweeters
Please create a guild/server where you want the bot to log tweets.
You may only add this bot to servers in which you have the `Administrator` permission.

Below the Twitter API tokens, you'll find a section like this:
```py
followed = {
    # "account_one": [
    #     channel_id_1,
    #     channel_id_2,
    #     channel_id_3
    # ],
}
```
In here, you will place your accounts and channel IDs.

To find your channel IDs, Please head into `Discord Settings` > `Advanced`, and make sure the `Developer Mode`
toggle is enabled.

To log your accounts, follow this structure:
```py
followed = {
    "elonmusk": [
        1095799624897396857,
        1086422873746448475,
        1083526259444809748
    ],
    "kde": [
        1094995987434573864,
        1094355177575813171,
        1083510015995949098
    ]
}
```
Where `elonmusk` and `kde` are the account names. The quotes are necessary.

To find the channel ID, right click on a channel and click on `channel ID` at the bottom of the menu.

The numbers are the channel ID. You can have as many or as little as you want, just make sure
every one is followed by a comma (the comma on the last channel is not important).
If you want to add more tweeters, simply follow the same structure as shown for `elonmusk`, including 
the comma at the ending `]`, before we get to `kde`'s account.

## Discord bot token
1. Visit the [Discord Developer Portal](https://discord.com/developers/applications)
2. Up by your profile picture in the top right, click on `Create Application`
3. Enter a name, like `TWITTER ;]` or something
4. Create the application
5. In the left panel, click on `Bot`
6. Click `Add Bot` on the right side
7. If necessary, enter your 2FA code
8. Scroll down to the `Privileged Gateway Intents` header, and check the following three switches
9. Scroll back up to the bot profile, change the PFP and name if you like
10. Click on `Copy` right below that
11. Below the previous segment, you'll find something like `BOT_TOKEN = "bot_token_here"`,
replace `bot_token_here` with your token. Keep the quote marks.
12. In the URL of that applications page, you'll find a section with your bot ID, like `1095824917032873995`
13. Copy that ID, and place it instead of `<bot_token_here>` in the following URL. Remove the angle brackets.
    - `https://discord.com/oauth2/authorize?client_id=`***`<bot_token_here>`***`&scope=bot&permissions=8`
14. Join the bot to whatever server you like

## Twitter link grabbing
This bot also supports you sending a link, then it will save the tweet.
After the previous segment, you will find something like this:
```py
# Which channels you can send a link to, the bot will save the tweet
tweet_link_grab_channels = [
]
```
Paste the channel IDs, so it follows this structure:
```py
# Which channels you can send a link to, the bot will save the tweet
tweet_link_grab_channels = [
    1085394872149745804,
    1095799624897396857
]
```

## Tweet timeout
Finally, you'll see this segment: `TWEET_TIMEOUT = 15`.
Change the 15 to whatever number. This is how often the bot will look for new tweets.

- If you have a low number of accounts, you may have a small number.
- If you have a high number of accounts, but a high number of Twitter API tokens (3+), you may have a small number.
- If you have a high number of accounts, but only a couple of Twitter API tokens, set it to something higher.

15 is a nice round number.

The bot will automatically switch tokens and wait 5 seconds if you hit the rate limit.

## Other notes
If you feel especially frisky, you can modify the code below the banner telling you not to.

By default, the footer of every embed will include `Logging by PRIZ ;]`. I would prefer if you didn't
change that, as that is a credit to my work. Additionally, the default footer icon is a neat recreation
of the Twitter icon in a neat drawing style. At smaller sizes, it just looks like the twitter icon.

# Licensing
This software is licensed under GPLv2; any modifications must remain
free and open source.

Importantly, this is **NOT** licensed under GPLv3. 

```
Twitter-Discord bot; Log your favorite Twitter accounts in Discord.
Copyright (C) 2023, PRIZ ;]
                   (aka VoxelPrismatic)

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation version 2.
The GNU General Public License version 3 does NOT apply to this
software.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
```

View full license under [LICENSE](https://github.com/VoxelPrismatic/twitter-logging/blob/master/LICENSE)
