"""Build data/BSB chapter JSON from data/bsb/bsb.txt (Berean Standard Bible)."""

from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "bsb" / "bsb.txt"
OUT = ROOT / "data" / "BSB"

# Protestant order — matches WEB / Korean data book ids
BOOK_ORDER = [
    "Genesis",
    "Exodus",
    "Leviticus",
    "Numbers",
    "Deuteronomy",
    "Joshua",
    "Judges",
    "Ruth",
    "1 Samuel",
    "2 Samuel",
    "1 Kings",
    "2 Kings",
    "1 Chronicles",
    "2 Chronicles",
    "Ezra",
    "Nehemiah",
    "Esther",
    "Job",
    "Psalms",
    "Proverbs",
    "Ecclesiastes",
    "Song of Solomon",
    "Isaiah",
    "Jeremiah",
    "Lamentations",
    "Ezekiel",
    "Daniel",
    "Hosea",
    "Joel",
    "Amos",
    "Obadiah",
    "Jonah",
    "Micah",
    "Nahum",
    "Habakkuk",
    "Zephaniah",
    "Haggai",
    "Zechariah",
    "Malachi",
    "Matthew",
    "Mark",
    "Luke",
    "John",
    "Acts",
    "Romans",
    "1 Corinthians",
    "2 Corinthians",
    "Galatians",
    "Ephesians",
    "Philippians",
    "Colossians",
    "1 Thessalonians",
    "2 Thessalonians",
    "1 Timothy",
    "2 Timothy",
    "Titus",
    "Philemon",
    "Hebrews",
    "James",
    "1 Peter",
    "2 Peter",
    "1 John",
    "2 John",
    "3 John",
    "Jude",
    "Revelation",
]

# Normalize BSB labels to WEB book names
NAME_MAP = {
    "Psalm": "Psalms",
}

REF_RE = re.compile(r"^(.+?)\s+(\d+):(\d+)$")


def load_verses() -> dict[str, dict[int, list[dict]]]:
    by_book: dict[str, dict[int, list[dict]]] = defaultdict(lambda: defaultdict(list))
    with SRC.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i < 3:
                continue
            line = line.rstrip("\n\r")
            if not line.strip():
                continue
            ref, text = line.split("\t", 1)
            m = REF_RE.match(ref.strip())
            if not m:
                raise ValueError(f"Bad ref on line {i + 1}: {ref!r}")
            raw_name, chapter_s, verse_s = m.groups()
            name = NAME_MAP.get(raw_name, raw_name)
            by_book[name][int(chapter_s)].append(
                {"verse": int(verse_s), "text": text.strip()}
            )
    return by_book


def main() -> None:
    if not SRC.is_file():
        raise FileNotFoundError(SRC)

    by_book = load_verses()

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    books_meta = []
    file_count = 0
    for book_id, name in enumerate(BOOK_ORDER, start=1):
        if name not in by_book:
            raise KeyError(f"Missing book in BSB source: {name}")
        chapters_map = by_book[name]
        chapter_nums = sorted(chapters_map)
        book_dir = OUT / str(book_id)
        book_dir.mkdir()
        for ch in chapter_nums:
            verses_sorted = sorted(chapters_map[ch], key=lambda x: x["verse"])
            payload = {"chapter": ch, "verses": verses_sorted}
            (book_dir / f"{ch}.json").write_text(
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            file_count += 1
        books_meta.append(
            {
                "id": book_id,
                "name": name,
                "chapters": chapter_nums,
            }
        )

    unknown = set(by_book) - set(BOOK_ORDER)
    if unknown:
        raise ValueError(f"Unexpected books in BSB source: {sorted(unknown)}")

    index = {"version": "BSB", "books": books_meta}
    (OUT / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"BSB: {len(books_meta)} books, {file_count} chapter files")


if __name__ == "__main__":
    main()
