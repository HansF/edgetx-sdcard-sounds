#!/usr/bin/env python3
"""Write voices/en-fun-<slug>.csv (+ _scripts.csv) for every character in voices/funny_lines.py.

Each file is voices/en-GB.csv with the event phrases replaced by the character's lines.
    uv run tools/make_funny_csv.py            # write all
    uv run tools/make_funny_csv.py --check    # exit 1 if any file is out of date
"""
import argparse
import csv
import io
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOICES = ROOT / "voices"
sys.path.insert(0, str(VOICES))
from funny_lines import ALIASES, CHARACTERS, LINES  # noqa: E402


def render(slug: str) -> str:
    lines = dict(LINES[slug])
    for alias, target in ALIASES.items():
        lines.setdefault(alias, lines[target])
    with (VOICES / "en-GB.csv").open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        out, used = io.StringIO(), set()
        w = csv.DictWriter(out, fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writeheader()
        for row in reader:
            key = (row["Path"] + "/" if row["Path"] else "") + row["Filename"][:-4]
            if key in lines:
                row["Translation"] = lines[key]
                used.add(key)
            w.writerow(row)
    missing = set(lines) - used
    if missing:
        raise SystemExit(f"{slug}: not in en-GB.csv: {sorted(missing)}")
    return out.getvalue()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    stale = False
    for slug in CHARACTERS:
        main_p, scripts_p = VOICES / f"en-fun-{slug}.csv", VOICES / f"en-fun-{slug}_scripts.csv"
        text = render(slug)
        if a.check:
            stale |= not main_p.exists() or main_p.read_text(encoding="utf-8") != text
            continue
        main_p.write_text(text, encoding="utf-8")
        shutil.copyfile(VOICES / "en-GB_scripts.csv", scripts_p)     # Lua-script phrases stay plain
        print(f"{slug}: {main_p.name}")
    if a.check and stale:
        sys.exit("funny CSVs are out of date: run tools/make_funny_csv.py")


if __name__ == "__main__":
    main()
