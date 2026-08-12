import re
import duckdb
from pathlib import Path
from datetime import datetime

PROMPTS_DIR = Path(__file__).parent / "Prompts"
DB_PATH = Path(__file__).parent / "Prompts.duckdb"


def parse_frontmatter(content: str) -> tuple[dict, str]:
    if not content.startswith("---"):
        return {}, content
    end = content.find("---", 3)
    if end == -1:
        return {}, content
    frontmatter_block = content[3:end].strip()
    body = content[end + 3:].strip()
    meta = {}
    for line in frontmatter_block.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"')
    return meta, body


def load_prompts() -> list[dict]:
    prompts = []
    for path in sorted(PROMPTS_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        prompts.append({
            "title": meta.get("title") or path.stem,
            "category": meta.get("category") or "Other",
            "content": body,
        })
    return prompts


con = duckdb.connect(str(DB_PATH))

prompts = load_prompts()
now = datetime.now()
inserted = 0

next_id = (con.execute("SELECT COALESCE(MAX(id), 0) FROM prompts").fetchone()[0] or 0) + 1

for p in prompts:
    existing = con.execute(
        "SELECT id FROM prompts WHERE title = ? AND category = ?",
        [p["title"], p["category"]]
    ).fetchone()
    if existing:
        print(f"Skipped (already exists): {p['title']}")
    else:
        con.execute(
            "INSERT INTO prompts (id, title, category, content, created_at) VALUES (?, ?, ?, ?, ?)",
            [next_id, p["title"], p["category"], p["content"], now]
        )
        next_id += 1
        inserted += 1
        print(f"Inserted: {p['title']}")

con.close()
print(f"\nDone. {inserted} prompt(s) inserted, {len(prompts) - inserted} skipped.")
