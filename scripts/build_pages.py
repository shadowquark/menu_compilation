#!/usr/bin/env python3
"""Apply the shared layouts to the pages listed in SUMMARY.md."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import html
from pathlib import Path, PurePosixPath
import posixpath
import re
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


@dataclass
class Page:
    depth: int
    title: str
    path: PurePosixPath
    children: list[Page] = field(default_factory=list)

    @property
    def name(self):
        return re.sub(r"^第[一二三四五六七八九十]+[编章]\s*", "", self.title)

    @property
    def recipe_count(self):
        return 1 if self.depth >= 3 else sum(child.recipe_count for child in self.children)


def load_pages(source_dir=SRC):
    pages, stack = [], []
    for line in (source_dir / "SUMMARY.md").read_text().splitlines():
        match = re.fullmatch(r"([ \t]*)- \[([^\]]+)\]\((.*)\)\s*", line)
        if not match:
            continue
        page = Page(len(match[1].expandtabs(4)) // 4, match[2],
                    PurePosixPath(match[3].removeprefix("./")))
        if not (source_dir / page.path).is_file():
            raise FileNotFoundError(f"Missing SUMMARY target: {page.path}")
        while stack and stack[-1].depth >= page.depth:
            stack.pop()
        if stack:
            stack[-1].children.append(page)
        stack.append(page)
        pages.append(page)
    return pages


def html_link(markdown_path):
    return quote(PurePosixPath(markdown_path).with_suffix(".html").as_posix())


def relative_page_link(page, target):
    return posixpath.relpath(target.path.as_posix(), page.path.parent.as_posix())


def render_category_page(title, recipes):
    """recipes contains (display name, relative Markdown path) pairs."""
    links = "\n".join(
        f'<li><a href="{html_link(path)}">{html.escape(name)}</a></li>'
        for name, path in recipes
    )
    return f'''# {title}

<div class="recipe-filter" hidden>
<input id="category-filter" type="search" placeholder="搜索菜名" aria-label="搜索菜名" autocomplete="off" aria-controls="category-recipes">
<span id="category-result-count" role="status"></span>
</div>

<ul id="category-recipes" class="recipe-grid">
{links}
</ul>
<p id="category-empty" class="empty-message" hidden>没有找到这个菜名，试试更短的关键词。</p>
'''


def render_recipe_page(title, text):
    # Remove only repetitions of this dish's title; retain every source version.
    body = re.sub(r"^#[ \t]+" + re.escape(title) + r"[ \t]*(?:\n|$)",
                  "", text, flags=re.M).strip("\r\n")
    return f"# {title}\n\n{body}".rstrip("\r\n") + "\n"


def render_child_cards(page):
    return "\n".join(
        f'<li><a href="{html_link(relative_page_link(page, child))}">'
        f'<span class="category-name">{html.escape(child.name)}</span>'
        f'<span class="category-count">{child.recipe_count} 道菜</span></a></li>'
        for child in page.children
    )


def render_cuisine_page(page, text):
    match = re.search(r"^#{1,2} 参考书目[ \t]*\n", text, re.M)
    references = text[match.end():].strip() if match else ""
    output = f'''# {page.name}

<div class="collection-stats"><span>{page.recipe_count} 道菜</span><span>{len(page.children)} 个类别</span></div>

<ul class="cuisine-grid">
{render_child_cards(page)}
</ul>
'''
    if references:
        output += f"\n## 参考书目\n\n{references}\n"
    return output


def render_section_page(page, text):
    body = re.split(r"^## 按菜系浏览[ \t]*\n", text, maxsplit=1, flags=re.M)[0]
    body = re.sub(r"^#[ \t]+[^\n]*(?:\n|$)", "", body, count=1).strip()
    return f'''# {page.name}

{body}

## 按菜系浏览

<ul class="cuisine-grid">
{render_child_cards(page)}
</ul>
'''


def generate_pages(source_dir=SRC, check=False):
    pages = load_pages(source_dir)
    changed = []
    counts = {"sections": 0, "cuisines": 0, "categories": 0, "recipes": 0}
    for page in pages:
        path = source_dir / page.path
        original = path.read_text()
        if page.depth >= 3:
            rendered = render_recipe_page(page.title, original)
            counts["recipes"] += 1
        elif page.depth == 2:
            rendered = render_category_page(page.title, [
                (child.title, relative_page_link(page, child)) for child in page.children
            ])
            counts["categories"] += 1
        elif page.depth == 1 and page.children:
            rendered = render_cuisine_page(page, original)
            counts["cuisines"] += 1
        elif page.depth == 0 and page.children:
            rendered = render_section_page(page, original)
            counts["sections"] += 1
        else:
            # Keep the preface, epilogue, and uncollected cuisines as authored.
            continue
        rendered = rendered.rstrip("\r\n") + "\n"
        if rendered != original:
            changed.append(str(page.path))
            if not check:
                path.write_text(rendered)
    print(
        f"Pages: {counts['sections']} sections, {counts['cuisines']} cuisines, "
        f"{counts['categories']} categories, {counts['recipes']} recipes; "
        f"{'outdated' if check else 'updated'}: {len(changed)}."
    )
    if check and changed:
        for path in changed[:20]:
            print(f"Outdated: {path}")
        raise SystemExit(1)
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report outdated pages without writing them")
    generate_pages(check=parser.parse_args().check)


if __name__ == "__main__":
    main()
