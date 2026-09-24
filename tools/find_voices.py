#!/usr/bin/env python3
"""Search the ElevenLabs shared voice library for the funny characters and build a listen-page.

    uv run tools/find_voices.py                      # all characters, top 8 per search term
    uv run tools/find_voices.py butler arcade        # some characters
    uv run tools/find_voices.py --add OWNER VOICE    # add a library voice to your account (needed before generating)

Writes ~/funny-voice-previews/index.html (open it in a browser: every candidate has an audio player,
its voice id and its licence flags) and downloads the preview MP3s next to it. Searching and previews are free.
"""
import argparse
import html
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
API = "https://api.elevenlabs.io/v1"
OUT = Path.home() / "funny-voice-previews"

# slug -> (title, [(search, gender or None)])
QUERIES = {
    "pit-crew": ("Cyberpunk Pit Crew", [("radio operator", None), ("cyberpunk", None), ("gritty", None), ("sci-fi", None), ("futuristic", None), ("intense", "female"), ("hacker", None)]),
    "fighter-pilot": ("Overconfident Fighter Pilot", [("action movie trailer", "male"), ("military pilot", "male"), ("deep confident american", "male")]),
    "butler": ("Extremely British Butler", [("butler", None), ("posh british", "male"), ("refined british", "male")]),
    "race-engineer": ("Unhinged Race Engineer", [("energetic sports commentator", "male"), ("excited", None), ("commentator", None), ("shouting", None), ("energetic", "male"), ("intense", "male")]),
    "arcade": ("Retro Arcade Announcer", [("video game announcer", None), ("trailer voice", "male"), ("arcade", None)]),
    "gloomy-mechanic": ("Depressed Drone Mechanic", [("tired", "male"), ("deadpan sarcastic", None), ("grumpy", "male")]),
    "bunker-computer": ("Nuclear Bunker Computer", [("robot computer", None), ("monotone", None), ("vintage announcer", None)]),
    "evil-ai": ("Evil Spaceship AI", [("calm villain", None), ("ai assistant", None), ("sinister smooth", None)]),
    "nature-narrator": ("Nature Documentary Narrator", [("documentary narrator", None), ("soft british narrator", None), ("wildlife", None)]),
}


def key() -> str:
    k = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("elevenlabs")
    if not k:
        sys.exit("ELEVENLABS_API_KEY is not set (put it in .env)")
    return k


def search(k: str, text: str, gender: str | None, n: int) -> list[dict]:
    params = {"search": text, "language": "en", "page_size": n, "sort": "usage_character_count_1y"}
    if gender:
        params["gender"] = gender
    r = requests.get(f"{API}/shared-voices", params=params, headers={"xi-api-key": k}, timeout=60)
    r.raise_for_status()
    return r.json().get("voices", [])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("characters", nargs="*")
    ap.add_argument("--add", nargs=2, metavar=("OWNER_ID", "VOICE_ID"))
    ap.add_argument("--name", help="name to give the added voice")
    ap.add_argument("-n", type=int, default=8)
    a = ap.parse_args()
    k = key()
    if a.add:
        r = requests.post(f"{API}/voices/add/{a.add[0]}/{a.add[1]}", headers={"xi-api-key": k},
                          json={"new_name": a.name or a.add[1]}, timeout=60)
        print(r.status_code, r.text[:300])
        return
    chars = a.characters or list(QUERIES)
    OUT.mkdir(exist_ok=True)
    seen, sections = set(), []
    for slug in chars:
        title, qs = QUERIES[slug]
        cards = []
        for text, gender in qs:
            for v in search(k, text, gender, a.n):
                if v["voice_id"] in seen or not v.get("preview_url"):
                    continue
                seen.add(v["voice_id"])
                mp3 = OUT / slug / f"{v['voice_id']}.mp3"
                mp3.parent.mkdir(exist_ok=True)
                if not mp3.exists():
                    mp3.write_bytes(requests.get(v["preview_url"], timeout=60).content)
                meta = " · ".join(str(x) for x in (v.get("gender"), v.get("age"), v.get("accent"), v.get("descriptive"), v.get("use_case")) if x)
                flags = ("free-tier OK" if v.get("free_users_allowed") else "paid only") + (" · commercial OK" if v.get("category") != "professional" or v.get("free_users_allowed") else "")
                cards.append(f'<div class="c"><b>{html.escape(v["name"])}</b> <small>({html.escape(text)})</small><br>'
                             f'<audio controls preload="none" src="{slug}/{v["voice_id"]}.mp3"></audio><br>'
                             f'<small>{html.escape(meta)}<br>{flags}<br><code>{v["voice_id"]}</code> owner <code>{v.get("public_owner_id", "")}</code></small></div>')
        sections.append(f"<h2>{html.escape(title)} <small>({slug})</small></h2><div class=g>{''.join(cards) or 'no results'}</div>")
        print(f"{slug}: {len(cards)} candidates")
    (OUT / "index.html").write_text(
        "<meta charset=utf-8><title>Funny voice candidates</title><style>body{font:15px system-ui;margin:24px;background:#111;color:#eee}"
        ".g{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}.c{background:#1c1c1c;padding:12px;border-radius:10px}"
        "audio{width:100%;margin:6px 0}small{color:#9a9a9a}code{color:#ffb454}h2{margin-top:36px}</style>" + "".join(sections), encoding="utf-8")
    print(f"open {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
