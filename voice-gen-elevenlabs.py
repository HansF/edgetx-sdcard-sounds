#!/usr/bin/env python3
"""Generate EdgeTX voice packs with ElevenLabs text-to-speech.

    uv run ./voice-gen-elevenlabs.py                 # every job in ELEVENLABS_VOICE_JOBS
    uv run ./voice-gen-elevenlabs.py --only nl       # one language folder
    uv run ./voice-gen-elevenlabs.py --dry-run       # count the characters it would spend
    uv run ./voice-gen-elevenlabs.py --verify        # also transcribe each new clip and compare
    uv run ./voice-gen-elevenlabs.py --recheck nl    # re-verify existing clips, regenerate mismatches

Every generated file is recorded in SOUNDS/<lang>/.elevenlabs.json with the text, voice,
model and settings it was made from, so a changed translation or voice setting regenerates
only that file and nothing is paid for twice. Set ELEVENLABS_API_KEY (or put it in .env).
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeElapsedColumn

from voice_generation_config import ELEVENLABS_VOICE_JOBS, ElevenLabsVoiceJob

load_dotenv()
API = "https://api.elevenlabs.io/v1"
SCRIPT_DIR = Path(__file__).resolve().parent
SOUNDS = SCRIPT_DIR / "SOUNDS"
MANIFEST = ".elevenlabs.json"
# Same trim as release.py, then EdgeTX's preferred 32 kHz mono 16-bit.
TRIM = ("silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB,"
        "areverse,silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB,areverse")
console = Console()


def api_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("elevenlabs")
    if not key:
        raise SystemExit('ELEVENLABS_API_KEY is not set. Put ELEVENLABS_API_KEY=... in .env or the environment.')
    return key


def read_rows(csv_path: Path) -> list[dict]:
    import csv

    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = []
        for row in csv.DictReader(f):
            if not row.get("Filename") or (row.get("String ID") or "").startswith("#"):
                continue
            if not (row.get("Translation") or "").strip():
                continue
            rows.append(row)
        return rows


def settings_of(job: ElevenLabsVoiceJob) -> dict:
    return {"stability": job.stability, "similarity_boost": job.similarity, "style": job.style,
            "use_speaker_boost": True, "speed": job.speed}


def fingerprint(job: ElevenLabsVoiceJob, text: str) -> str:
    blob = json.dumps({"t": spoken(text), "v": job.voice_id, "m": job.model, "s": settings_of(job)}, sort_keys=True)
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def load_manifest(lang_root: Path) -> dict:
    p = lang_root / MANIFEST
    return json.loads(p.read_text()) if p.exists() else {}


def save_manifest(lang_root: Path, m: dict) -> None:
    lang_root.mkdir(parents=True, exist_ok=True)
    (lang_root / MANIFEST).write_text(json.dumps(m, indent=1, ensure_ascii=False, sort_keys=True) + "\n")


def synth(key: str, job: ElevenLabsVoiceJob, text: str, mp3: Path) -> None:
    body = {"text": spoken(text), "model_id": job.model, "voice_settings": settings_of(job)}
    if job.language and job.model != "eleven_multilingual_v2":
        body["language_code"] = job.language
    for attempt in range(4):
        r = requests.post(f"{API}/text-to-speech/{job.voice_id}", params={"output_format": "mp3_44100_128"},
                          headers={"xi-api-key": key}, json=body, timeout=120)
        if r.status_code == 200:
            mp3.write_bytes(r.content)
            return
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(2 ** attempt)
            continue
        raise RuntimeError(f"{r.status_code}: {r.text[:300]}")
    raise RuntimeError("gave up after 4 attempts")


def to_wav(mp3: Path, wav: Path, skip: str) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", skip or "0", "-i", str(mp3),
                    "-af", TRIM, "-ar", "32000", "-ac", "1", "-sample_fmt", "s16", str(wav)], check=True)
    norm = shutil.which("ffmpeg-normalize") or str(Path(sys.executable).parent / "ffmpeg-normalize")
    subprocess.run([norm, str(wav), "-o", str(wav), "-f", "-nt", "peak", "-t", "-1"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def transcribe(key: str, wav: Path, lang3: str) -> str:
    with wav.open("rb") as f:
        r = requests.post(f"{API}/speech-to-text", headers={"xi-api-key": key},
                          data={"model_id": "scribe_v1", "language_code": lang3}, files={"file": f}, timeout=120)
    return r.json().get("text", "") if r.status_code == 200 else f"<stt {r.status_code}>"


def spoken(text: str) -> str:
    """What is actually sent: a full sentence. One-word inputs come out mumbled without the stop."""
    return text if text[-1] in ".!?" else text + "."


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("-", " ")
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()


EN_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
           "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
EN_TENS = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty", 6: "sixty", 7: "seventy", 8: "eighty", 9: "ninety"}
NL_ONES = ["nul", "een", "twee", "drie", "vier", "vijf", "zes", "zeven", "acht", "negen", "tien", "elf", "twaalf",
           "dertien", "veertien", "vijftien", "zestien", "zeventien", "achttien", "negentien"]
NL_TENS = {2: "twintig", 3: "dertig", 4: "veertig", 5: "vijftig", 6: "zestig", 7: "zeventig", 8: "tachtig", 9: "negentig"}


def num_words(n: int, lang: str) -> str:
    """0..999 as words, so a transcriber's "21" and our "twenty one" compare equal."""
    if n >= 1000:
        return str(n)
    ones, tens = (NL_ONES, NL_TENS) if lang.startswith("nl") else (EN_ONES, EN_TENS)
    h, r = divmod(n, 100)
    out = ""
    if h:
        out = ones[h] + ("honderd" if lang.startswith("nl") else " hundred") if not (h == 1 and lang.startswith("nl")) else "honderd"
        if r == 0:
            return out
        out += "" if lang.startswith("nl") else " "
    if r < 20:
        return out + ones[r]
    t, o = divmod(r, 10)
    if lang.startswith("nl"):
        return out + (ones[o] + ("en" if ones[o][-1] not in "e" else "en") + tens[t] if o else tens[t])
    return out + (tens[t] + (" " + ones[o] if o else ""))


def norm(s: str, lang: str = "en") -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("-", " ")
    s = s.replace("%", " procent " if lang.startswith("nl") else " percent ")
    s = re.sub(r"\bmw\b", "milliwatt", s)
    s = re.sub(r"\d+", lambda m: num_words(int(m.group()), lang), s)
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.replace("milliwatts", "milliwatt")


def similarity(expected: str, heard: str, lang: str = "en") -> float:
    return difflib.SequenceMatcher(None, norm(expected, lang), norm(heard, lang)).ratio()


def run_job(key: str, job: ElevenLabsVoiceJob, args) -> tuple[int, int, list]:
    rows = read_rows(job.csv_path)
    lang_root = SOUNDS / job.langdir.split("/")[0]
    out_root = SOUNDS / job.langdir
    manifest = load_manifest(lang_root)
    todo, chars = [], 0
    for row in rows:
        text = row["Translation"].strip()
        rel = str(Path(job.langdir.split("/", 1)[1] if "/" in job.langdir else "") / row["Path"] / row["Filename"]).lstrip("/")
        rel = rel.replace("\\", "/")
        wav = out_root / row["Path"] / row["Filename"]
        fp = fingerprint(job, text)
        entry = manifest.get(rel)
        fresh = wav.exists() and entry and entry.get("fp") == fp
        if fresh and not args.force and not (args.recheck and entry.get("stt_ok") is False):
            continue
        todo.append((row, text, rel, wav, fp))
        chars += len(text)
    console.print(f"[bold]{job.langdir}[/bold]  {job.csv_path.name}: {len(rows)} phrases, "
                  f"{len(todo)} to generate, {chars} characters")
    if args.dry_run or not todo:
        return 0, chars, []
    if args.limit:
        todo = todo[: args.limit]
    flagged = []
    lock = threading.Lock()

    def one(item):
        row, text, rel, wav, fp = item
        wav.parent.mkdir(parents=True, exist_ok=True)
        mp3 = wav.with_suffix(".mp3")
        try:
            synth(key, job, text, mp3)
            to_wav(mp3, wav, row.get("Skip") or "0")
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]{rel}: {exc}[/red]")
            return
        finally:
            mp3.unlink(missing_ok=True)
        entry = {"text": text, "voice": job.voice_id, "model": job.model, "fp": fp}
        if args.verify or args.recheck:
            heard = transcribe(key, wav, job.stt_language)
            score = max(similarity(text, heard, job.language), similarity(row.get("Source text", ""), heard, job.language))
            entry.update(stt=heard, stt_score=round(score, 2), stt_ok=score >= 0.72)
            if not entry["stt_ok"]:
                with lock:
                    flagged.append((rel, text, heard, score))
        with lock:
            manifest[rel] = entry
            save_manifest(lang_root, manifest)

    with Progress(TextColumn("[blue]{task.description}"), BarColumn(), TaskProgressColumn(), TimeElapsedColumn(),
                  console=console) as progress:
        task = progress.add_task(job.langdir, total=len(todo))
        with ThreadPoolExecutor(args.threads) as ex:
            for _ in ex.map(one, todo):
                progress.advance(task)
    return len(todo), chars, flagged


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated language folders (nl, nl-emma, en_gb-daniel)")
    ap.add_argument("--dry-run", action="store_true", help="only count characters")
    ap.add_argument("--force", action="store_true", help="regenerate even if up to date")
    ap.add_argument("--verify", action="store_true", help="transcribe every new clip and flag mismatches")
    ap.add_argument("--recheck", action="store_true", help="regenerate clips whose last transcription mismatched")
    ap.add_argument("--limit", type=int, help="stop after N files per job (for testing)")
    ap.add_argument("--rescore", action="store_true", help="recompute the transcription verdicts from the manifests, no API calls")
    ap.add_argument("--threads", type=int, default=3, help="parallel requests (ElevenLabs Starter allows 3)")
    args = ap.parse_args()
    os.chdir(SCRIPT_DIR)

    jobs = [j for j in ELEVENLABS_VOICE_JOBS if not args.only or j.langdir.split("/")[0] in args.only.split(",")]
    if not jobs:
        raise SystemExit(f"no jobs match --only {args.only}")
    if args.rescore:
        for job in jobs:
            if "/" in job.langdir:
                continue
            lang_root = SOUNDS / job.langdir
            m = load_manifest(lang_root)
            src = {}
            for j in jobs:
                if j.langdir.split("/")[0] == job.langdir:
                    for row in read_rows(j.csv_path):
                        rel = ("SCRIPTS/" if "/" in j.langdir else "") + (row["Path"] + "/" if row["Path"] else "") + row["Filename"]
                        src[rel] = row.get("Source text", "")
            bad = 0
            for rel, e in m.items():
                if "stt" not in e:
                    continue
                score = max(similarity(e["text"], e["stt"], job.language), similarity(src.get(rel, ""), e["stt"], job.language))
                e["stt_score"], e["stt_ok"] = round(score, 2), score >= 0.72
                bad += not e["stt_ok"]
            save_manifest(lang_root, m)
            console.print(f"{job.langdir}: {len(m)} clips, {bad} still flagged")
        return 0
    key = api_key() if not args.dry_run else ""
    total_files = total_chars = 0
    flagged_all = []
    for job in jobs:
        n, c, flagged = run_job(key, job, args)
        total_files += n
        total_chars += c
        flagged_all += [(job.langdir.split("/")[0], *f) for f in flagged]
    console.print(f"[green]{total_files} files generated, {total_chars} characters[/green]" if not args.dry_run
                  else f"[yellow]dry run: {total_chars} characters would be spent[/yellow]")
    if flagged_all:
        console.print(f"[red]{len(flagged_all)} clips did not transcribe back cleanly:[/red]")
        for lang, rel, text, heard, score in flagged_all:
            console.print(f"  {lang}/{rel}: wanted {text!r}, heard {heard!r} ({score:.2f})")
    if not args.dry_run:
        r = requests.get(f"{API}/user/subscription", headers={"xi-api-key": key}, timeout=30)
        if r.ok:
            s = r.json()
            console.print(f"ElevenLabs quota: {s['character_count']}/{s['character_limit']} characters used this period")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        console.print("[yellow]Interrupted.[/yellow]")
        raise SystemExit(130)
