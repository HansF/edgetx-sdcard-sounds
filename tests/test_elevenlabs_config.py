from pathlib import Path

from voice_generation_config import ELEVENLABS_VOICE_JOBS


def test_elevenlabs_jobs_reference_existing_csvs():
    for job in ELEVENLABS_VOICE_JOBS:
        assert job.csv_path.exists(), job.csv_file
        assert job.model
        assert 0 <= job.stability <= 1


def test_scripts_jobs_use_scripts_csv():
    for job in ELEVENLABS_VOICE_JOBS:
        assert job.langdir.endswith("/SCRIPTS") == job.csv_path.name.endswith("_scripts.csv"), job.langdir


def test_dutch_csv_matches_english_rows():
    import csv

    def rows(p):
        with open(p, newline="", encoding="utf-8") as f:
            return [(r["String ID"], r["Path"], r["Filename"]) for r in csv.DictReader(f)]

    assert rows(Path("voices/nl-NL.csv")) == rows(Path("voices/en-GB.csv"))
    assert rows(Path("voices/nl-NL_scripts.csv")) == rows(Path("voices/en-GB_scripts.csv"))
