"""Build data/WEB chapter JSON from source OT/NT World English Bible files."""

from __future__ import annotations

import json
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "WEB"

# Protestant order — matches Korean data book ids
SLUG_ORDER = [
    "genesis",
    "exodus",
    "leviticus",
    "numbers",
    "deuteronomy",
    "joshua",
    "judges",
    "ruth",
    "1-samuel",
    "2-samuel",
    "1-kings",
    "2-kings",
    "1-chronicles",
    "2-chronicles",
    "ezra",
    "nehemiah",
    "esther",
    "job",
    "psalms",
    "proverbs",
    "ecclesiastes",
    "song-of-solomon",
    "isaiah",
    "jeremiah",
    "lamentations",
    "ezekiel",
    "daniel",
    "hosea",
    "joel",
    "amos",
    "obadiah",
    "jonah",
    "micah",
    "nahum",
    "habakkuk",
    "zephaniah",
    "haggai",
    "zechariah",
    "malachi",
    "matthew",
    "mark",
    "luke",
    "john",
    "acts",
    "romans",
    "1-corinthians",
    "2-corinthians",
    "galatians",
    "ephesians",
    "philippians",
    "colossians",
    "1-thessalonians",
    "2-thessalonians",
    "1-timothy",
    "2-timothy",
    "titus",
    "philemon",
    "hebrews",
    "james",
    "1-peter",
    "2-peter",
    "1-john",
    "2-john",
    "3-john",
    "jude",
    "revelation",
]


def load_verses() -> list[dict]:
    verses = []
    for name in ("old-testament.json", "new-testament.json"):
        data = json.loads((ROOT / "source" / name).read_text(encoding="utf-8"))
        verses.extend(data["verses"])
    return verses


def main() -> None:
    verses = load_verses()
    by_book: dict[str, dict[int, list[dict]]] = defaultdict(lambda: defaultdict(list))
    names: dict[str, str] = {}

    for v in verses:
        slug = v["book"]
        names[slug] = v["bookName"]
        by_book[slug][v["chapter"]].append(
            {"verse": v["verse"], "text": v["text"]}
        )

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    books_meta = []
    file_count = 0
    for book_id, slug in enumerate(SLUG_ORDER, start=1):
        if slug not in by_book:
            raise KeyError(f"Missing book in source: {slug}")
        chapters_map = by_book[slug]
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
                "name": names[slug],
                "chapters": chapter_nums,
            }
        )

    index = {"version": "WEB", "books": books_meta}
    (OUT / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"WEB: {len(books_meta)} books, {file_count} chapter files")


if __name__ == "__main__":
    main()
