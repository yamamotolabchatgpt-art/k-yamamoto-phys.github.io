"""確認済みのarXiv書誌情報から、論文一覧と日英の活動欄に項目を追加する。"""

import argparse
from datetime import date
from difflib import unified_diff
import json
from pathlib import Path
import re

import yaml

from sort_presentation import DATA_DIR, date_key


def insert_entry(source, entries, index, block):
    """既存のYAMLを再出力せず、項目とその直前のコメントの間に割り込まない。"""
    lines = source.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if re.match(r"^-\s", line)]
    if len(starts) != len(entries):
        raise ValueError("トップレベルの項目境界を確認してください")
    line = starts[index] if index < len(starts) else len(lines)
    if 0 < index < len(starts):
        while lines[line - 1].startswith("#"):
            line -= 1
    before = "".join(lines[:line])
    separator = "\n" if before and not before.endswith("\n") else ""
    result = before + separator + block + "".join(lines[line:])
    expected = entries[:index] + yaml.safe_load(block) + entries[index:]
    if yaml.safe_load(result) != expected:
        raise ValueError("追加後のYAMLが予定していた内容と一致しません")
    return result


def unique_match(entries, matches, path):
    found = [entry for entry in entries if matches(entry)]
    if len(found) > 1:
        raise ValueError(f"{path}: 同じarXiv IDの項目が複数あります")
    return found[0] if found else None


def paper_update(source, path, args):
    entries = yaml.safe_load(source) or []
    # 既存データには、末尾のゼロがYAMLの数値変換で落ちるIDもある。
    def matches(entry):
        value = entry.get("arXiv")
        return value == args.arxiv_id or (isinstance(value, float) and value == float(args.arxiv_id))

    existing = unique_match(entries, matches, path)
    if existing is not None:
        if existing["journal"] is not None:
            raise ValueError(f"{path}: この論文は掲載誌付きで登録されています")
        return source

    # 数値にすると末尾の桁が落ちるIDだけを引用符で囲み、リンク先を保つ。
    arxiv = args.arxiv_id if str(float(args.arxiv_id)) == args.arxiv_id else json.dumps(args.arxiv_id)
    authors = args.authors
    try:
        plain_authors = yaml.safe_load(f"authors: {authors}\n") == {"authors": authors}
    except yaml.YAMLError:
        plain_authors = False
    if not plain_authors:
        authors = json.dumps(authors, ensure_ascii=False)

    block = (
        f"- title: {json.dumps(args.title, ensure_ascii=False)}\n"
        f"  authors: {authors}\n"
        f"  note: null\n  arXiv: {arxiv}\n  year: {args.year}\n  journal: null\n"
    )
    index = next((i for i, entry in enumerate(entries) if entry["year"] <= args.year), len(entries))
    return insert_entry(source, entries, index, block)


def activity_update(source, path, args):
    entries = yaml.safe_load(source) or []
    link = re.compile(rf"https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/{re.escape(args.arxiv_id)}(?:v\d+)?(?![\w])")

    def matches(entry):
        return entry["label"] == "publication" and any(
            link.search(content or "") for content in entry["content"].values()
        )

    existing = unique_match(entries, matches, path)
    if existing is not None:
        if not all(existing["content"].get(lang) for lang in ("ja", "en")):
            raise ValueError(f"{path}: 既存の記事の日英両版を確認してください")
        return source

    url = f"https://arxiv.org/abs/{args.arxiv_id}"
    block = (
        f'- date: "{args.activity_date.isoformat()}"\n'
        f'  label: publication\n  content:\n    ja: >\n'
        f'      原著論文 "{args.title}" を [**arXiv**]({url}) に投稿しました\n'
        f'    en: >\n'
        f'      Original paper "{args.title}" has appeared on [**arXiv**]({url})\n'
    )
    index = next((i for i, entry in enumerate(entries) if date_key(entry) < args.activity_date), len(entries))
    return insert_entry(source, entries, index, block)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arxiv_id", help="版番号なしのarXiv ID")
    parser.add_argument("--title", required=True, help="arXivで確認した論文タイトル")
    parser.add_argument("--authors", required=True, help="掲載順の著者名を連記")
    parser.add_argument("--year", type=int, required=True, help="初回投稿年")
    parser.add_argument("--activity-date", type=date.fromisoformat, required=True, help="活動欄の掲載日（YYYY-MM-DD）")
    parser.add_argument("--site", choices=("both", "personal", "group"), default="both", help="掲載先。既定は両サイト")
    parser.add_argument("--dry-run", action="store_true", help="書き込まずに差分を表示")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]{2}(?:0[1-9]|1[0-2])\.[0-9]{4,5}", args.arxiv_id):
        parser.error("版番号なしの新形式のarXiv IDを指定してください")
    args.title = " ".join(args.title.split())
    args.authors = " ".join(args.authors.split())
    if not args.title or not args.authors or not 1000 <= args.year <= 9999:
        parser.error("タイトル・著者名・4桁の初回投稿年を指定してください")

    changes = []
    sites = ("personal", "group") if args.site == "both" else (args.site,)
    try:
        for site in sites:
            for filename, update in (("paper_regular.yml", paper_update), ("activity.yml", activity_update)):
                path = DATA_DIR / site / filename
                name = str(path.relative_to(DATA_DIR.parent))
                source = path.read_text(encoding="utf-8")
                result = update(source, name, args)
                if source != result:
                    changes.append((path, name, source, result))
    except (OSError, ValueError, yaml.YAMLError) as error:
        parser.error(str(error))

    # 全掲載先の差分を作ってから書き込む。
    for path, name, source, result in changes:
        if args.dry_run:
            diff = unified_diff(source.splitlines(keepends=True), result.splitlines(keepends=True), name, name)
            print("".join(diff), end="")
        else:
            path.write_text(result, encoding="utf-8")
            print(f"更新: {name}")
    if not changes:
        print(f"登録済み: arXiv:{args.arxiv_id}")


if __name__ == "__main__":
    main()
