"""Tag speech spans on Korean chapter JSON from WEB source files.

- NT Jesus (red): source/new-testament.json segments[].jesus (wj)
- OT God (gold): source/old-testament.json — no publisher markers, so
  quotes are extracted after divine speech attributions (God/Yahweh said…)
- Mixed/partial quotes: English char ratios mapped onto Korean text
- Local data only — does not deploy
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ("KorHKJV", "KorRV", "WEB")

BOOK_SLUG_TO_ID = {
    "genesis": 1,
    "exodus": 2,
    "leviticus": 3,
    "numbers": 4,
    "deuteronomy": 5,
    "joshua": 6,
    "judges": 7,
    "ruth": 8,
    "1-samuel": 9,
    "2-samuel": 10,
    "1-kings": 11,
    "2-kings": 12,
    "1-chronicles": 13,
    "2-chronicles": 14,
    "ezra": 15,
    "nehemiah": 16,
    "esther": 17,
    "job": 18,
    "psalms": 19,
    "proverbs": 20,
    "ecclesiastes": 21,
    "song-of-solomon": 22,
    "isaiah": 23,
    "jeremiah": 24,
    "lamentations": 25,
    "ezekiel": 26,
    "daniel": 27,
    "hosea": 28,
    "joel": 29,
    "amos": 30,
    "obadiah": 31,
    "jonah": 32,
    "micah": 33,
    "nahum": 34,
    "habakkuk": 35,
    "zephaniah": 36,
    "haggai": 37,
    "zechariah": 38,
    "malachi": 39,
    "matthew": 40,
    "mark": 41,
    "luke": 42,
    "john": 43,
    "acts": 44,
    "romans": 45,
    "1-corinthians": 46,
    "2-corinthians": 47,
    "galatians": 48,
    "ephesians": 49,
    "philippians": 50,
    "colossians": 51,
    "1-thessalonians": 52,
    "2-thessalonians": 53,
    "1-timothy": 54,
    "2-timothy": 55,
    "titus": 56,
    "philemon": 57,
    "hebrews": 58,
    "james": 59,
    "1-peter": 60,
    "2-peter": 61,
    "1-john": 62,
    "2-john": 63,
    "3-john": 64,
    "jude": 65,
    "revelation": 66,
}

OPEN = "\u201c"
CLOSE = "\u201d"
DIVINE = r"(?:Yahweh(?:\s+God)?|God|the\s+LORD(?:\s+God)?)"

# Divine attribution + opening quote (excludes naming like: God called the light “day”)
GOD_INTRO = re.compile(
    rf"\b{DIVINE}\b"
    rf"(?:(?!\b(?:said|spoke|answered|commanded|saying)\b).){{0,100}}?"
    rf"(?:"
    rf"\b(?:said|spoke|answered|commanded)\b"
    rf"|\bcalled\s+to\b"
    rf")"
    rf"(?:(?!{re.escape(OPEN)}).){{0,80}}?"
    rf"{re.escape(OPEN)}",
    re.I | re.S,
)

GOD_SAYING = re.compile(
    rf"\b{DIVINE}\b(?:(?!{re.escape(OPEN)}).){{0,120}}?\bsaying\b[,:]?\s*{re.escape(OPEN)}",
    re.I | re.S,
)


def merge_ratios(ranges: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not ranges:
        return []
    ranges = sorted(ranges)
    out = [list(ranges[0])]
    for a, b in ranges[1:]:
        if a <= out[-1][1] + 1e-12:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def jesus_ratio_ranges(verse: dict) -> list[tuple[float, float]]:
    text = verse.get("text") or ""
    if not text:
        return []
    total = len(text)
    ranges: list[tuple[float, float]] = []
    pos = 0
    for seg in verse.get("segments") or []:
        chunk = seg.get("text") or ""
        start, end = pos, pos + len(chunk)
        pos = end
        if not chunk.strip():
            continue
        if seg.get("jesus"):
            ranges.append((start / total, end / total))
    return merge_ratios(ranges)


def find_quote_close(text: str, start: int) -> int:
    i = start + 1
    while i < len(text):
        if text[i] == CLOSE:
            return i + 1
        i += 1
    return len(text)


def god_char_ranges(text: str) -> list[tuple[int, int]]:
    opens: set[int] = set()
    for rx in (GOD_INTRO, GOD_SAYING):
        for m in rx.finditer(text):
            opens.add(m.end() - 1)
    ranges = []
    for op in sorted(opens):
        if op < 0 or op >= len(text) or text[op] != OPEN:
            continue
        ranges.append((op, find_quote_close(text, op)))
    if not ranges:
        return []
    ranges.sort()
    out = [list(ranges[0])]
    for a, b in ranges[1:]:
        if a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def god_ratio_ranges(verse: dict) -> list[tuple[float, float]]:
    text = verse.get("text") or ""
    if not text:
        return []
    total = len(text)
    return merge_ratios([(a / total, b / total) for a, b in god_char_ranges(text)])


def ratios_to_spans(
    text: str, ranges: list[tuple[float, float]], speaker: str
) -> list[dict]:
    n = len(text)
    if n == 0 or not ranges:
        return []
    if len(ranges) == 1 and ranges[0][0] <= 1e-9 and ranges[0][1] >= 1 - 1e-9:
        return [{"start": 0, "end": n, "speaker": speaker}]

    raw = []
    for a, b in ranges:
        start = int(round(a * n))
        end = int(round(b * n))
        start = max(0, min(start, n))
        end = max(start, min(end, n))
        if end > start:
            raw.append([start, end])
    if not raw:
        return []
    raw.sort()
    merged = [raw[0]]
    for start, end in raw[1:]:
        if start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [{"start": s, "end": e, "speaker": speaker} for s, e in merged]


def merge_span_dicts(spans: list[dict]) -> list[dict]:
    """Merge overlapping spans with the same speaker; keep different speakers."""
    if not spans:
        return []
    by_speaker: dict[str, list[list[int]]] = {}
    for s in spans:
        by_speaker.setdefault(s["speaker"], []).append([s["start"], s["end"]])
    out: list[dict] = []
    for speaker, ranges in by_speaker.items():
        ranges.sort()
        merged = [ranges[0]]
        for a, b in ranges[1:]:
            if a <= merged[-1][1] + 1:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        out.extend({"start": a, "end": b, "speaker": speaker} for a, b in merged)
    out.sort(key=lambda s: (s["start"], s["end"], s["speaker"]))
    return out


def load_nt_speech_map() -> dict[tuple[int, int, int], list[tuple[float, float]]]:
    data = json.loads((ROOT / "source" / "new-testament.json").read_text(encoding="utf-8"))
    out: dict[tuple[int, int, int], list[tuple[float, float]]] = {}
    missing = set()
    for v in data["verses"]:
        book_id = BOOK_SLUG_TO_ID.get(v["book"])
        if book_id is None:
            missing.add(v["book"])
            continue
        ranges = jesus_ratio_ranges(v)
        if ranges:
            out[(book_id, v["chapter"], v["verse"])] = ranges
    if missing:
        raise KeyError(f"Unmapped book slugs: {sorted(missing)}")
    return out


def load_ot_god_speech_map() -> dict[tuple[int, int, int], list[tuple[float, float]]]:
    data = json.loads((ROOT / "source" / "old-testament.json").read_text(encoding="utf-8"))
    out: dict[tuple[int, int, int], list[tuple[float, float]]] = {}
    missing = set()
    for v in data["verses"]:
        book_id = BOOK_SLUG_TO_ID.get(v["book"])
        if book_id is None:
            missing.add(v["book"])
            continue
        ranges = god_ratio_ranges(v)
        if ranges:
            out[(book_id, v["chapter"], v["verse"])] = ranges
    if missing:
        raise KeyError(f"Unmapped book slugs: {sorted(missing)}")
    return out


def write_json(path: Path, data: dict) -> None:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    for attempt in range(5):
        try:
            path.write_text(payload, encoding="utf-8")
            return
        except OSError:
            time.sleep(0.4 * (attempt + 1))
    path.write_text(payload, encoding="utf-8")


def clear_all_spans(version: str) -> int:
    cleared = 0
    base = ROOT / "data" / version
    for path in base.rglob("*.json"):
        if path.name == "index.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for verse in data.get("verses") or []:
            if "spans" in verse:
                verse.pop("spans", None)
                changed = True
                cleared += 1
        if changed:
            write_json(path, data)
    return cleared


def apply_speech(
    version: str,
    speech_map: dict[tuple[int, int, int], list[tuple[float, float]]],
    speaker: str,
    *,
    merge: bool = False,
) -> int:
    tagged = 0
    base = ROOT / "data" / version
    chapters: dict[tuple[int, int], list[tuple[int, list]]] = {}
    for (book_id, chapter, verse), ranges in speech_map.items():
        chapters.setdefault((book_id, chapter), []).append((verse, ranges))

    for (book_id, chapter), items in chapters.items():
        path = base / str(book_id) / f"{chapter}.json"
        if not path.exists():
            print(f"WARN missing {path}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        by_verse = {v["verse"]: v for v in data["verses"]}
        changed = False
        for verse_num, ranges in items:
            verse = by_verse.get(verse_num)
            if not verse:
                print(f"WARN missing verse {version} {book_id}:{chapter}:{verse_num}")
                continue
            spans = ratios_to_spans(verse["text"], ranges, speaker)
            if not spans:
                continue
            if merge and verse.get("spans"):
                verse["spans"] = merge_span_dicts(list(verse["spans"]) + spans)
            else:
                verse["spans"] = spans
            tagged += 1
            changed = True
        if changed:
            write_json(path, data)
    return tagged


def main() -> None:
    jesus_map = load_nt_speech_map()
    god_map = load_ot_god_speech_map()
    print(f"NT jesus verses: {len(jesus_map)}")
    print(f"OT god quote verses: {len(god_map)}")

    for ver in VERSIONS:
        cleared = clear_all_spans(ver)
        j = apply_speech(ver, jesus_map, "jesus", merge=False)
        g = apply_speech(ver, god_map, "god", merge=True)
        print(f"{ver}: cleared={cleared}, jesus={j}, god={g}")


if __name__ == "__main__":
    main()
