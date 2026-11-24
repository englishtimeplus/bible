from pathlib import Path
import json
import sys

ver = sys.argv[1] if len(sys.argv) > 1 else "KorHKJV"
root = Path(__file__).resolve().parents[1] / "data" / ver / "66"
for i in range(1, 23):
    d = json.loads((root / f"{i}.json").read_text(encoding="utf-8"))
    print(f"===== Ch {i} =====")
    for v in d["verses"]:
        print(f'{v["verse"]:2d}|{v["text"]}')
