"""Split monolithic Bible JSON into per-chapter files for faster loading."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE = ROOT / "source"
VERSIONS = ["KorHKJV", "KorRV"]


def split_version(ver: str) -> None:
    src = DATA / f"{ver}.json"
    if not src.exists():
        src = SOURCE / f"{ver}.json"
    if not src.exists():
        raise FileNotFoundError(f"Missing source for {ver}")

    with open(src, encoding="utf-8") as f:
        payload = json.load(f)

    out_dir = DATA / ver
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    books_meta = []
    for bi, book in enumerate(payload["books"], start=1):
        book_dir = out_dir / str(bi)
        book_dir.mkdir()
        chapter_nums = []
        for ch in book["chapters"]:
            ch_num = ch["chapter"]
            chapter_nums.append(ch_num)
            slim = {
                "chapter": ch_num,
                "verses": [{"verse": v["verse"], "text": v["text"]} for v in ch["verses"]],
            }
            with open(book_dir / f"{ch_num}.json", "w", encoding="utf-8") as cf:
                json.dump(slim, cf, ensure_ascii=False, separators=(",", ":"))
        books_meta.append({"id": bi, "name": book["name"], "chapters": chapter_nums})

    with open(out_dir / "index.json", "w", encoding="utf-8") as jf:
        json.dump({"version": ver, "books": books_meta}, jf, ensure_ascii=False, separators=(",", ":"))

    SOURCE.mkdir(exist_ok=True)
    orig = DATA / f"{ver}.json"
    if orig.exists():
        dest = SOURCE / f"{ver}.json"
        if dest.exists():
            dest.unlink()
        shutil.move(str(orig), str(dest))

    files = list(out_dir.rglob("*.json"))
    total = sum(p.stat().st_size for p in files)
    print(f"{ver}: {len(files)} files, {total / 1024 / 1024:.2f} MB")


def main() -> None:
    for ver in VERSIONS:
        split_version(ver)


if __name__ == "__main__":
    main()
