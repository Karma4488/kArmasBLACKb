#!/usr/bin/env python3
"""
kArmasBLACKb - Username & Email OSINT Recon Tool
Inspired by Blackbird | Part of the kArmas Suite
We Are Legion. We Do Not Forget. We Do Not Forgive.

Usage:
  python3 kArmasBLACKb.py -u <username>
  python3 kArmasBLACKb.py -e <email>
  python3 kArmasBLACKb.py -u <username> --save
  python3 kArmasBLACKb.py -u <username> --timeout 10 --threads 50
"""

import sys
import os
import time
import random
import argparse
import json
import csv
import threading
import queue
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import quote

# ──────────────────────────────────────────────────────────────────────────────
#  ANSI COLOURS
# ──────────────────────────────────────────────────────────────────────────────
R  = "\033[0m"
G  = "\033[92m"      # bright green
Y  = "\033[93m"      # yellow
C  = "\033[96m"      # cyan
RE = "\033[91m"      # red
M  = "\033[95m"      # magenta
DG = "\033[32m"      # dark green  (matrix)
W  = "\033[97m"      # white
B  = "\033[90m"      # bold grey

def clr(text, colour): return f"{colour}{text}{R}"

# ──────────────────────────────────────────────────────────────────────────────
#  MATRIX RAIN INTRO
# ──────────────────────────────────────────────────────────────────────────────
MATRIX_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%^&*()_+-=[]{}|;':,./<>?ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"

def matrix_rain(duration: float = 2.5, cols: int = 70):
    """Render a short matrix rain burst to stdout."""
    rows = 14
    end = time.time() + duration
    try:
        while time.time() < end:
            line = ""
            for _ in range(cols):
                ch = random.choice(MATRIX_CHARS)
                shade = random.choice([DG, G, W])
                line += f"{shade}{ch}"
            sys.stdout.write(line + R + "\n")
            sys.stdout.flush()
            time.sleep(0.045)
    except KeyboardInterrupt:
        pass
    sys.stdout.write(R)

# ──────────────────────────────────────────────────────────────────────────────
#  BANNER
# ──────────────────────────────────────────────────────────────────────────────
BANNER = f"""
{DG}██╗  ██╗ █████╗ ██████╗ ███╗   ███╗ █████╗ ███████╗{R}
{DG}██║ ██╔╝██╔══██╗██╔══██╗████╗ ████║██╔══██╗██╔════╝{R}
{G}█████╔╝ ███████║██████╔╝██╔████╔██║███████║███████╗{R}
{G}██╔═██╗ ██╔══██║██╔══██╗██║╚██╔╝██║██╔══██║╚════██║{R}
{G}██║  ██╗██║  ██║██║  ██║██║ ╚═╝ ██║██║  ██║███████║{R}
{DG}╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝{R}

{M}██████╗ ██╗      █████╗  ██████╗██╗  ██╗██╗  ██╗██████╗ {R}
{M}██╔══██╗██║     ██╔══██╗██╔════╝██║ ██╔╝██║  ██║██╔══██╗{R}
{C}██████╔╝██║     ███████║██║     █████╔╝ ███████║██████╔╝{R}
{C}██╔══██╗██║     ██╔══██║██║     ██╔═██╗ ██╔══██║██╔══██╗{R}
{C}██████╔╝███████╗██║  ██║╚██████╗██║  ██╗██║  ██║██████╔╝{R}
{B}╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ {R}

  {Y}[ kArmas Suite — Username & Email OSINT Recon ]{R}
  {DG}We Are Legion. We Do Not Forget. We Do Not Forgive.{R}
"""

SKULL = f"""
{DG}        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░{R}
{DG}        ░░░░░▄▄████████████▄▄░░░░░░░░░░░░{R}
{G}        ░░░▄█████████████████████▄░░░░░░░{R}
{G}        ░░▄███████████████████████▄░░░░░░{R}
{G}        ░█████████████████████████████░░░{R}
{G}        ░████████░░░░░░░░░████████████░░░{R}
{C}        ░███████░  ██  ██  ░███████████░░░{R}
{C}        ░███████░  ██  ██  ░████  ██░░░░░{R}
{C}        ░████████░░░░░░░░░████████████░░░{R}
{M}        ░░████████████████████████████░░░{R}
{M}        ░░░░░████████████████████░░░░░░░░{R}
{M}        ░░░░░░░░████████████░░░░░░░░░░░░░{R}
{DG}        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░{R}
"""

# ──────────────────────────────────────────────────────────────────────────────
#  PLATFORM DATABASE  (username-based)
#  Format: { "name": str, "url": str with {u} placeholder, "valid_code": int }
# ──────────────────────────────────────────────────────────────────────────────
USERNAME_PLATFORMS = [
    {"name":"GitHub",          "url":"https://github.com/{u}",                          "valid":200},
    {"name":"GitLab",          "url":"https://gitlab.com/{u}",                          "valid":200},
    {"name":"Twitter/X",       "url":"https://x.com/{u}",                               "valid":200},
    {"name":"Instagram",       "url":"https://www.instagram.com/{u}/",                  "valid":200},
    {"name":"TikTok",          "url":"https://www.tiktok.com/@{u}",                     "valid":200},
    {"name":"Reddit",          "url":"https://www.reddit.com/user/{u}",                 "valid":200},
    {"name":"Pinterest",       "url":"https://www.pinterest.com/{u}/",                  "valid":200},
    {"name":"Twitch",          "url":"https://www.twitch.tv/{u}",                       "valid":200},
    {"name":"YouTube",         "url":"https://www.youtube.com/@{u}",                    "valid":200},
    {"name":"LinkedIn",        "url":"https://www.linkedin.com/in/{u}",                 "valid":200},
    {"name":"Medium",          "url":"https://medium.com/@{u}",                         "valid":200},
    {"name":"Dev.to",          "url":"https://dev.to/{u}",                              "valid":200},
    {"name":"Hashnode",        "url":"https://hashnode.com/@{u}",                       "valid":200},
    {"name":"Keybase",         "url":"https://keybase.io/{u}",                          "valid":200},
    {"name":"Patreon",         "url":"https://www.patreon.com/{u}",                     "valid":200},
    {"name":"Replit",          "url":"https://replit.com/@{u}",                         "valid":200},
    {"name":"Codepen",         "url":"https://codepen.io/{u}",                          "valid":200},
    {"name":"HackerNews",      "url":"https://news.ycombinator.com/user?id={u}",        "valid":200},
    {"name":"ProductHunt",     "url":"https://www.producthunt.com/@{u}",                "valid":200},
    {"name":"Behance",         "url":"https://www.behance.net/{u}",                     "valid":200},
    {"name":"Dribbble",        "url":"https://dribbble.com/{u}",                        "valid":200},
    {"name":"Flickr",          "url":"https://www.flickr.com/people/{u}",               "valid":200},
    {"name":"SoundCloud",      "url":"https://soundcloud.com/{u}",                      "valid":200},
    {"name":"Bandcamp",        "url":"https://{u}.bandcamp.com",                        "valid":200},
    {"name":"Spotify",         "url":"https://open.spotify.com/user/{u}",               "valid":200},
    {"name":"Last.fm",         "url":"https://www.last.fm/user/{u}",                    "valid":200},
    {"name":"Mixcloud",        "url":"https://www.mixcloud.com/{u}/",                   "valid":200},
    {"name":"Steam",           "url":"https://steamcommunity.com/id/{u}",               "valid":200},
    {"name":"Chess.com",       "url":"https://www.chess.com/member/{u}",                "valid":200},
    {"name":"Lichess",         "url":"https://lichess.org/@/{u}",                       "valid":200},
    {"name":"Duolingo",        "url":"https://www.duolingo.com/profile/{u}",            "valid":200},
    {"name":"Fiverr",          "url":"https://www.fiverr.com/{u}",                      "valid":200},
    {"name":"Upwork",          "url":"https://www.upwork.com/freelancers/~{u}",         "valid":200},
    {"name":"HackerOne",       "url":"https://hackerone.com/{u}",                       "valid":200},
    {"name":"Bugcrowd",        "url":"https://bugcrowd.com/{u}",                        "valid":200},
    {"name":"Wattpad",         "url":"https://www.wattpad.com/user/{u}",                "valid":200},
    {"name":"Quora",           "url":"https://www.quora.com/profile/{u}",               "valid":200},
    {"name":"Disqus",          "url":"https://disqus.com/by/{u}/",                      "valid":200},
    {"name":"WordPress",       "url":"https://{u}.wordpress.com",                       "valid":200},
    {"name":"Blogger",         "url":"https://{u}.blogspot.com",                        "valid":200},
    {"name":"Tumblr",          "url":"https://{u}.tumblr.com",                          "valid":200},
    {"name":"Ask.fm",          "url":"https://ask.fm/{u}",                              "valid":200},
    {"name":"VK",              "url":"https://vk.com/{u}",                              "valid":200},
    {"name":"OK.ru",           "url":"https://ok.ru/{u}",                               "valid":200},
    {"name":"Telegram",        "url":"https://t.me/{u}",                                "valid":200},
    {"name":"Signal",          "url":"https://signal.me/#p/{u}",                        "valid":200},
    {"name":"Mastodon",        "url":"https://mastodon.social/@{u}",                    "valid":200},
    {"name":"Bluesky",         "url":"https://bsky.app/profile/{u}.bsky.social",        "valid":200},
    {"name":"Threads",         "url":"https://www.threads.net/@{u}",                    "valid":200},
    {"name":"Snapchat",        "url":"https://www.snapchat.com/add/{u}",                "valid":200},
    {"name":"Linktree",        "url":"https://linktr.ee/{u}",                           "valid":200},
    {"name":"About.me",        "url":"https://about.me/{u}",                            "valid":200},
    {"name":"Gravatar",        "url":"https://en.gravatar.com/{u}",                     "valid":200},
    {"name":"Trello",          "url":"https://trello.com/{u}",                          "valid":200},
    {"name":"AngelList",       "url":"https://angel.co/u/{u}",                          "valid":200},
    {"name":"Crunchbase",      "url":"https://www.crunchbase.com/person/{u}",           "valid":200},
    {"name":"Docker Hub",      "url":"https://hub.docker.com/u/{u}",                    "valid":200},
    {"name":"npm",             "url":"https://www.npmjs.com/~{u}",                      "valid":200},
    {"name":"PyPI",            "url":"https://pypi.org/user/{u}/",                      "valid":200},
    {"name":"RubyGems",        "url":"https://rubygems.org/profiles/{u}",               "valid":200},
    {"name":"Packagist",       "url":"https://packagist.org/users/{u}/",                "valid":200},
    {"name":"SourceForge",     "url":"https://sourceforge.net/u/{u}/profile/",          "valid":200},
    {"name":"Bitbucket",       "url":"https://bitbucket.org/{u}/",                      "valid":200},
    {"name":"Codecademy",      "url":"https://www.codecademy.com/profiles/{u}",         "valid":200},
    {"name":"Codeforces",      "url":"https://codeforces.com/profile/{u}",              "valid":200},
    {"name":"LeetCode",        "url":"https://leetcode.com/{u}/",                       "valid":200},
    {"name":"HackerRank",      "url":"https://www.hackerrank.com/{u}",                  "valid":200},
    {"name":"Kaggle",          "url":"https://www.kaggle.com/{u}",                      "valid":200},
    {"name":"ResearchGate",    "url":"https://www.researchgate.net/profile/{u}",        "valid":200},
    {"name":"Academia.edu",    "url":"https://independent.academia.edu/{u}",            "valid":200},
    {"name":"SlideShare",      "url":"https://www.slideshare.net/{u}",                  "valid":200},
    {"name":"Scribd",          "url":"https://www.scribd.com/{u}",                      "valid":200},
    {"name":"Goodreads",       "url":"https://www.goodreads.com/{u}",                   "valid":200},
    {"name":"Letterboxd",      "url":"https://letterboxd.com/{u}/",                     "valid":200},
    {"name":"IMDb",            "url":"https://www.imdb.com/user/{u}/",                  "valid":200},
    {"name":"DeviantArt",      "url":"https://www.deviantart.com/{u}",                  "valid":200},
    {"name":"ArtStation",      "url":"https://www.artstation.com/{u}",                  "valid":200},
    {"name":"Newgrounds",      "url":"https://{u}.newgrounds.com",                      "valid":200},
    {"name":"Etsy",            "url":"https://www.etsy.com/shop/{u}",                   "valid":200},
    {"name":"eBay",            "url":"https://www.ebay.com/usr/{u}",                    "valid":200},
    {"name":"Amazon",          "url":"https://www.amazon.com/gp/profile/amzn1.account.{u}", "valid":200},
    {"name":"Airbnb",          "url":"https://www.airbnb.com/users/show/{u}",           "valid":200},
    {"name":"Yelp",            "url":"https://www.yelp.com/user_details?userid={u}",    "valid":200},
    {"name":"Foursquare",      "url":"https://foursquare.com/{u}",                      "valid":200},
    {"name":"Untappd",         "url":"https://untappd.com/user/{u}",                    "valid":200},
    {"name":"Strava",          "url":"https://www.strava.com/athletes/{u}",             "valid":200},
    {"name":"Runkeeper",       "url":"https://runkeeper.com/user/{u}/profile",           "valid":200},
    {"name":"Garmin Connect",  "url":"https://connect.garmin.com/modern/profile/{u}",   "valid":200},
    {"name":"MyFitnessPal",    "url":"https://www.myfitnesspal.com/profile/{u}",        "valid":200},
    {"name":"Venmo",           "url":"https://account.venmo.com/u/{u}",                 "valid":200},
    {"name":"Cash App",        "url":"https://cash.app/${u}",                           "valid":200},
    {"name":"Ko-fi",           "url":"https://ko-fi.com/{u}",                           "valid":200},
    {"name":"Buy Me a Coffee", "url":"https://buymeacoffee.com/{u}",                    "valid":200},
    {"name":"Substack",        "url":"https://{u}.substack.com",                        "valid":200},
    {"name":"Ghost",           "url":"https://{u}.ghost.io",                            "valid":200},
    {"name":"Notion",          "url":"https://www.notion.so/{u}",                       "valid":200},
    {"name":"Carrd",           "url":"https://{u}.carrd.co",                            "valid":200},
    {"name":"Weebly",          "url":"https://{u}.weebly.com",                          "valid":200},
    {"name":"Wix",             "url":"https://{u}.wixsite.com",                         "valid":200},
    {"name":"Squarespace",     "url":"https://{u}.squarespace.com",                     "valid":200},
    {"name":"500px",           "url":"https://500px.com/p/{u}",                         "valid":200},
    {"name":"Unsplash",        "url":"https://unsplash.com/@{u}",                       "valid":200},
    {"name":"Imgur",           "url":"https://imgur.com/user/{u}",                      "valid":200},
    {"name":"VSCO",            "url":"https://vsco.co/{u}/gallery",                     "valid":200},
    {"name":"Snapfish",        "url":"https://www.snapfish.com/snapfish/quF/framed?page=photos&with=member&membername={u}", "valid":200},
    {"name":"Clubhouse",       "url":"https://www.clubhouse.com/@{u}",                  "valid":200},
    {"name":"Periscope",       "url":"https://www.periscope.tv/{u}/",                   "valid":200},
    {"name":"Vimeo",           "url":"https://vimeo.com/{u}",                           "valid":200},
    {"name":"Dailymotion",     "url":"https://www.dailymotion.com/{u}",                 "valid":200},
    {"name":"Rumble",          "url":"https://rumble.com/user/{u}",                     "valid":200},
    {"name":"Odysee",          "url":"https://odysee.com/@{u}",                         "valid":200},
    {"name":"BitChute",        "url":"https://www.bitchute.com/channel/{u}/",           "valid":200},
    {"name":"Gab",             "url":"https://gab.com/{u}",                             "valid":200},
    {"name":"Parler",          "url":"https://parler.com/{u}",                          "valid":200},
    {"name":"MeWe",            "url":"https://mewe.com/i/{u}",                          "valid":200},
    {"name":"Wire",            "url":"https://wire.com/en/",                            "valid":200},
    {"name":"Viber",           "url":"https://chats.viber.com/{u}",                     "valid":200},
    {"name":"WeChat",          "url":"https://weixin.qq.com/{u}",                       "valid":200},
    {"name":"LINE",            "url":"https://line.me/ti/p/~{u}",                       "valid":200},
    {"name":"KakaoTalk",       "url":"https://open.kakao.com/o/{u}",                    "valid":200},
    {"name":"Discord",         "url":"https://discord.com/users/{u}",                   "valid":200},
    {"name":"Slack",           "url":"https://{u}.slack.com",                           "valid":200},
    {"name":"Microsoft Teams", "url":"https://teams.microsoft.com/l/team/{u}",          "valid":200},
    {"name":"Zoom",            "url":"https://zoom.us/j/{u}",                           "valid":200},
    {"name":"Skype",           "url":"https://join.skype.com/invite/{u}",               "valid":200},
    {"name":"Xing",            "url":"https://www.xing.com/profile/{u}",                "valid":200},
    {"name":"Viadeo",          "url":"https://fr.viadeo.com/fr/profile/{u}",            "valid":200},
    {"name":"Badoo",           "url":"https://badoo.com/profile/{u}",                   "valid":200},
    {"name":"Tinder",          "url":"https://www.gotinder.com/@{u}",                   "valid":200},
    {"name":"Bumble",          "url":"https://bumble.com/en/profile/{u}",               "valid":200},
    {"name":"OkCupid",         "url":"https://www.okcupid.com/profile/{u}",             "valid":200},
    {"name":"Match",           "url":"https://www.match.com/profile/shared/{u}",        "valid":200},
    {"name":"Roblox",          "url":"https://www.roblox.com/user.aspx?username={u}",   "valid":200},
    {"name":"Minecraft",       "url":"https://namemc.com/profile/{u}",                  "valid":200},
    {"name":"Fortnite",        "url":"https://fortnitetracker.com/profile/all/{u}",     "valid":200},
    {"name":"PSN",             "url":"https://my.playstation.com/profile/{u}",          "valid":200},
    {"name":"Xbox",            "url":"https://xboxgamertag.com/search/{u}",             "valid":200},
    {"name":"Nintendo",        "url":"https://www.nintendo.com/en-US/search/#q={u}",    "valid":200},
    {"name":"osu!",            "url":"https://osu.ppy.sh/users/{u}",                    "valid":200},
    {"name":"Speedrun.com",    "url":"https://www.speedrun.com/user/{u}",               "valid":200},
    {"name":"GameFAQs",        "url":"https://gamefaqs.gamespot.com/community/{u}",     "valid":200},
    {"name":"Itch.io",         "url":"https://{u}.itch.io",                             "valid":200},
    {"name":"IndieDB",         "url":"https://www.indiedb.com/members/{u}",             "valid":200},
    {"name":"Instructables",   "url":"https://www.instructables.com/member/{u}/",       "valid":200},
    {"name":"Hackaday",        "url":"https://hackaday.io/{u}",                         "valid":200},
    {"name":"Thingiverse",     "url":"https://www.thingiverse.com/{u}",                 "valid":200},
    {"name":"Printables",      "url":"https://www.printables.com/@{u}",                 "valid":200},
    {"name":"Stack Overflow",  "url":"https://stackoverflow.com/users/{u}",             "valid":200},
    {"name":"Stack Exchange",  "url":"https://stackexchange.com/users/{u}",             "valid":200},
    {"name":"Experts Exchange","url":"https://www.experts-exchange.com/members/{u}/",   "valid":200},
    {"name":"Codecanyon",      "url":"https://codecanyon.net/user/{u}",                 "valid":200},
    {"name":"ThemeForest",     "url":"https://themeforest.net/user/{u}",                "valid":200},
    {"name":"Envato",          "url":"https://www.envato.com/{u}",                      "valid":200},
    {"name":"Freelancer",      "url":"https://www.freelancer.com/u/{u}",                "valid":200},
    {"name":"Toptal",          "url":"https://www.toptal.com/resume/{u}",               "valid":200},
    {"name":"99designs",       "url":"https://99designs.com/profiles/{u}",              "valid":200},
    {"name":"Guru",            "url":"https://www.guru.com/freelancers/{u}/",           "valid":200},
    {"name":"PeoplePerHour",   "url":"https://www.peopleperhour.com/freelancer/{u}",    "valid":200},
    {"name":"Clarity.fm",      "url":"https://clarity.fm/{u}",                          "valid":200},
    {"name":"Snapchat",        "url":"https://snapchat.com/add/{u}",                    "valid":200},
]

# ──────────────────────────────────────────────────────────────────────────────
#  USER AGENT POOL
# ──────────────────────────────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 14; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
]

def random_ua() -> str:
    return random.choice(USER_AGENTS)

# ──────────────────────────────────────────────────────────────────────────────
#  HTTP HEAD CHECK
# ──────────────────────────────────────────────────────────────────────────────
def check_url(url: str, timeout: int = 8) -> tuple:
    """Return (status_code, final_url) or (None, url) on error."""
    try:
        req = Request(url, headers={
            "User-Agent": random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }, method="HEAD")
        with urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.url
    except HTTPError as e:
        return e.code, url
    except (URLError, Exception):
        return None, url

# ──────────────────────────────────────────────────────────────────────────────
#  WORKER THREAD
# ──────────────────────────────────────────────────────────────────────────────
found_lock  = threading.Lock()
print_lock  = threading.Lock()
found_list  = []

def worker(job_queue: queue.Queue, username: str, timeout: int, results: list):
    while True:
        try:
            platform = job_queue.get_nowait()
        except queue.Empty:
            break

        url = platform["url"].replace("{u}", quote(username))
        code, final_url = check_url(url, timeout)

        with print_lock:
            name_pad = platform["name"].ljust(20)
            if code == 200:
                print(f"  {G}[+]{R} {C}{name_pad}{R} → {G}{url}{R}")
                with found_lock:
                    results.append({
                        "platform": platform["name"],
                        "url": url,
                        "status": code,
                    })
            elif code in (301, 302, 303, 307, 308):
                print(f"  {Y}[~]{R} {Y}{name_pad}{R} → {Y}{url}{R}  {B}(redirect){R}")
                with found_lock:
                    results.append({
                        "platform": platform["name"],
                        "url": url,
                        "status": code,
                    })
            elif code == 404:
                print(f"  {RE}[-]{R} {B}{name_pad}{R} → {B}not found{R}")
            elif code is None:
                print(f"  {B}[!]{R} {B}{name_pad}{R} → {B}timeout/error{R}")
            else:
                print(f"  {B}[?]{R} {B}{name_pad}{R} → {B}HTTP {code}{R}")

        job_queue.task_done()

# ──────────────────────────────────────────────────────────────────────────────
#  SEARCH RUNNER
# ──────────────────────────────────────────────────────────────────────────────
def run_username_search(username: str, timeout: int, threads: int) -> list:
    results = []
    q = queue.Queue()
    seen_names = set()
    for p in USERNAME_PLATFORMS:
        if p["name"] not in seen_names:
            q.put(p)
            seen_names.add(p["name"])

    total = q.qsize()
    print(f"\n  {C}[*]{R} Scanning {G}{total}{R} platforms for username: {Y}{username}{R}\n")

    pool = []
    for _ in range(min(threads, total)):
        t = threading.Thread(target=worker, args=(q, username, timeout, results), daemon=True)
        t.start()
        pool.append(t)

    for t in pool:
        t.join()

    return results

# ──────────────────────────────────────────────────────────────────────────────
#  EMAIL SEARCH (passive: construct known email-login URLs + OSINT aggregators)
# ──────────────────────────────────────────────────────────────────────────────
EMAIL_RESOURCES = [
    {"name":"Gravatar",      "url":"https://en.gravatar.com/{hash}",                  "note":"MD5 of email"},
    {"name":"HaveIBeenPwned","url":"https://haveibeenpwned.com/account/{e}",           "note":"breach check"},
    {"name":"Hunter.io",     "url":"https://hunter.io/email-finder?email={e}",        "note":"email intel"},
    {"name":"Epieos",        "url":"https://epieos.com/?q={e}&type=email",            "note":"OSINT aggregator"},
    {"name":"GHunt (ref)",   "url":"https://github.com/mxrch/GHunt",                  "note":"Google account OSINT"},
    {"name":"Skype",         "url":"https://join.skype.com/invite/{e}",               "note":"login check"},
    {"name":"Snapchat",      "url":"https://www.snapchat.com/",                       "note":"email registration check"},
    {"name":"LinkedIn",      "url":"https://www.linkedin.com/uas/login",              "note":"email sign-in"},
    {"name":"Twitter/X",     "url":"https://x.com/i/flow/login",                      "note":"email sign-in"},
    {"name":"Facebook",      "url":"https://www.facebook.com/login/",                 "note":"email sign-in"},
]

def run_email_search(email: str) -> list:
    import hashlib
    print(f"\n  {C}[*]{R} Passive email OSINT for: {Y}{email}{R}\n")
    results = []
    email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()

    for r in EMAIL_RESOURCES:
        url = r["url"].replace("{e}", quote(email)).replace("{hash}", email_hash)
        note = r["note"]
        name_pad = r["name"].ljust(20)
        print(f"  {G}[→]{R} {C}{name_pad}{R} {B}({note}){R}")
        print(f"      {G}{url}{R}")
        results.append({"platform": r["name"], "url": url, "note": note})

    return results

# ──────────────────────────────────────────────────────────────────────────────
#  EXPORT
# ──────────────────────────────────────────────────────────────────────────────
def save_results(target: str, results: list, mode: str = "username"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = target.replace("@","_").replace(".","_")
    base = f"kArmasBLACKb_{safe}_{ts}"

    # JSON
    json_path = f"{base}.json"
    with open(json_path, "w") as f:
        json.dump({"target": target, "mode": mode, "timestamp": ts, "results": results}, f, indent=2)

    # CSV
    csv_path = f"{base}.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()) if results else ["platform","url","status"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n  {G}[✔]{R} Results saved:")
    print(f"      {C}JSON{R} → {Y}{json_path}{R}")
    print(f"      {C}CSV {R} → {Y}{csv_path}{R}")

# ──────────────────────────────────────────────────────────────────────────────
#  SUMMARY
# ──────────────────────────────────────────────────────────────────────────────
def print_summary(target: str, results: list, elapsed: float, mode: str):
    found  = [r for r in results if r.get("status") in (200, 301, 302, 303, 307, 308)]
    total  = len(USERNAME_PLATFORMS) if mode == "username" else len(EMAIL_RESOURCES)
    print(f"\n{DG}{'─'*60}{R}")
    print(f"  {M}kArmasBLACKb — Scan Complete{R}")
    print(f"  {C}Target   :{R} {Y}{target}{R}")
    print(f"  {C}Mode     :{R} {Y}{mode}{R}")
    print(f"  {C}Checked  :{R} {G}{total}{R} platforms")
    print(f"  {C}Found    :{R} {G}{len(found)}{R} accounts")
    print(f"  {C}Elapsed  :{R} {Y}{elapsed:.2f}s{R}")
    print(f"{DG}{'─'*60}{R}")

    if found:
        print(f"\n  {G}[FOUND ACCOUNTS]{R}")
        for r in found:
            print(f"    {G}✓{R} {C}{r['platform']}{R} → {r['url']}")

    print(f"\n  {DG}We Are Legion. We Do Not Forget. We Do Not Forgive.{R}\n")

# ──────────────────────────────────────────────────────────────────────────────
#  AUTHORISATION GATE
# ──────────────────────────────────────────────────────────────────────────────
def auth_gate(target: str):
    print(f"\n{Y}{'═'*60}{R}")
    print(f"  {RE}[!] AUTHORISATION REQUIRED{R}")
    print(f"{Y}{'═'*60}{R}")
    print(f"""
  {W}kArmasBLACKb performs passive reconnaissance.
  You are responsible for ensuring you have lawful
  authority to research the target: {Y}{target}{R}

  {C}Unauthorised use may violate:
  • Computer Fraud and Abuse Act (CFAA)
  • GDPR / data protection laws
  • Platform terms of service{R}
""")
    print(f"  {Y}Type {G}\"I AGREE\"{Y} to confirm authorised use, or Ctrl+C to exit.{R}")
    print(f"{Y}{'═'*60}{R}")
    try:
        answer = input(f"\n  {C}> {R}").strip()
    except KeyboardInterrupt:
        print(f"\n\n  {RE}Aborted.{R}\n")
        sys.exit(0)
    if answer != "I AGREE":
        print(f"\n  {RE}[✘] Authorisation not confirmed. Exiting.{R}\n")
        sys.exit(1)
    print(f"\n  {G}[✔] Authorisation confirmed. Initiating recon...{R}")

# ──────────────────────────────────────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="kArmasBLACKb",
        description="Username & Email OSINT Recon Tool — kArmas Suite",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("-u", "--username",  help="Target username to search")
    parser.add_argument("-e", "--email",     help="Target email address to search")
    parser.add_argument("--save",            action="store_true",
                        help="Save results to JSON + CSV")
    parser.add_argument("--timeout",         type=int, default=8,
                        help="HTTP request timeout in seconds (default: 8)")
    parser.add_argument("--threads",         type=int, default=30,
                        help="Number of threads (default: 30)")
    parser.add_argument("--no-matrix",       action="store_true",
                        help="Skip matrix rain intro")
    parser.add_argument("--list-platforms",  action="store_true",
                        help="List all supported platforms and exit")

    args = parser.parse_args()

    # ── list platforms
    if args.list_platforms:
        print(f"\n{C}Supported Platforms ({len(USERNAME_PLATFORMS)}){R}\n")
        for i, p in enumerate(USERNAME_PLATFORMS, 1):
            print(f"  {G}{i:>3}.{R} {C}{p['name']}{R}")
        print()
        sys.exit(0)

    if not args.username and not args.email:
        parser.print_help()
        sys.exit(1)

    # ── intro
    if not args.no_matrix:
        matrix_rain(duration=2.0)

    print(BANNER)
    print(SKULL)

    target = args.username or args.email

    # ── auth gate
    auth_gate(target)

    start = time.time()

    # ── search
    if args.username:
        results = run_username_search(args.username, args.timeout, args.threads)
        mode = "username"
    else:
        results = run_email_search(args.email)
        mode = "email"

    elapsed = time.time() - start

    # ── summary
    print_summary(target, results, elapsed, mode)

    # ── save
    if args.save and results:
        save_results(target, results, mode)
    elif args.save and not results:
        print(f"  {Y}[!]{R} No results to save.\n")

if __name__ == "__main__":
    main()
