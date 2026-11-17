#!/usr/bin/env python3
"""Validate generated page titles and local HTML/CSS links before deployment."""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import tomllib
from urllib.parse import unquote, urlsplit

from build_pages import ROOT, SRC, load_pages
from build_fonts import OUTPUT as FONT_OUTPUT, validate_fonts


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        for attr in ("href", "src"):
            if attrs.get(attr):
                self.links.append(attrs[attr])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_dir", nargs="?", type=Path, default=ROOT / "book")
    build = parser.parse_args().build_dir.resolve()
    config = tomllib.loads((ROOT / "book.toml").read_text())
    site_path = urlsplit(config.get("output", {}).get("html", {}).get("site-url", "/")).path
    pages = load_pages()
    errors = []
    fonts = validate_fonts()
    for font in fonts["fonts"]:
        target = build / "assets/fonts" / font["file"]
        if not target.is_file():
            errors.append(f"Missing published WOFF2: {font['file']}")
    if any(build.rglob("*.ttf")):
        errors.append("The published book still contains original TTF files")
    for page in pages:
        source = (SRC / page.path).read_text()
        if len(re.findall(r"^#[ \t]+", source, re.M)) != 1:
            errors.append(f"Expected one page title: {page.path}")
        if not (build / page.path.with_suffix(".html")).is_file():
            errors.append(f"Missing HTML page: {page.path}")
    documents = {p.resolve(): Document(p.read_text()) for p in build.rglob("*.html")}
    stylesheets = set()
    checked = 0

    def resolve(source, href):
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc:
            return None, ""
        path = unquote(parsed.path)
        if not path:
            target = source
        elif path.startswith("/"):
            if site_path != "/" and path.startswith(site_path):
                path = path[len(site_path):]
            target = build / path.lstrip("/")
        else:
            target = source.parent / path
        if target.is_dir():
            target /= "index.html"
        return target.resolve(), unquote(parsed.fragment)

    for source, doc in documents.items():
        for href in doc.links:
            target, fragment = resolve(source, href)
            if target is None:
                continue
            checked += 1
            if not target.is_file():
                errors.append(f"Missing target in {source.relative_to(build)}: {href}")
            elif fragment and target in documents and fragment not in documents[target].ids:
                errors.append(f"Missing anchor in {source.relative_to(build)}: {href}")
            if target.suffix == ".css":
                stylesheets.add(target)
    for source in stylesheets:
        if not source.is_file():
            continue
        for match in re.finditer(r"url\(\s*['\"]?([^'\"\s)]+)", source.read_text()):
            target, _ = resolve(source, match[1])
            if target is not None and not target.is_file():
                errors.append(f"Missing CSS asset in {source.relative_to(build)}: {match[1]}")
    if errors:
        for error in errors[:40]:
            print(error)
        raise SystemExit(f"Validation failed: {len(errors)} errors")
    print(f"Validated {len(pages)} source pages, {len(documents)} HTML pages, and {checked} local links/resources.")


if __name__ == "__main__":
    main()
