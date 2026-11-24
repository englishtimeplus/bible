"""Deprecated wrapper — run tag-speech.py for full NT red-letter tagging."""

from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("tag-speech.py")), run_name="__main__")
