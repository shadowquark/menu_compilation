from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_fonts import CSS, OUTPUT, FONTS, FontSpec, collect_characters, generate_fonts, validate_fonts


def tiny_font(path, width=600):
    mapping = {32: "space", 65: "A", ord("一"): "uni4E00", ord("二"): "uni4E8C", ord("三"): "uni4E09"}
    order = [".notdef", *mapping.values()]
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap(mapping)
    glyphs = {}
    for name in order:
        pen = TTGlyphPen(None)
        if name != "space":
            pen.moveTo((50, 0)); pen.lineTo((width - 50, 0)); pen.lineTo((width - 50, 700)); pen.closePath()
        glyphs[name] = pen.glyph()
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics({name: (width, 50) for name in order})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": "SubsetFixture", "styleName": "Regular", "psName": "SubsetFixture-Regular"})
    builder.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    builder.setupPost()
    builder.setupMaxp()
    builder.save(path)


class FontBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="menu-font-test-")
        self.root = Path(self.temp.name)
        (self.root / "fonts").mkdir()
        tiny_font(self.root / "fonts/Tiny.ttf")
        self.specs = tuple(FontSpec(spec.role, spec.family, "Tiny.ttf") for spec in FONTS)
        self.book = {"items": [{"Chapter": {"name": "三", "content": "# A\n\n一", "sub_items": []}}]}

    def tearDown(self):
        self.temp.cleanup()

    def build(self, book=None):
        return generate_fonts(book or self.book, "A", self.root, self.specs)

    def test_extracts_markdown_html_entities_and_nested_chapters(self):
        book = deepcopy(self.book)
        book["items"][0]["Chapter"]["sub_items"] = [{"Chapter": {
            "name": "二", "content": "## 三\n\n<h3>一&nbsp;二</h3>\n\n二\n---", "sub_items": []}}]
        chars = collect_characters(book, "A", "三")
        self.assertTrue({ord("一"), ord("二"), ord("三"), 160} <= chars["heading"])
        self.assertIn(ord("三"), chars["directory"])
        self.assertIn(ord("一"), chars["body"])
        self.assertIn(ord("Z"), chars["body"])

    def test_new_character_updates_font_url_and_coverage(self):
        first = self.build()
        book = deepcopy(self.book)
        book["items"][0]["Chapter"]["content"] += "二"
        second = self.build(book)
        self.assertNotEqual(first["fonts"][0]["file"], second["fonts"][0]["file"])
        self.assertEqual(first["fonts"][1]["file"], second["fonts"][1]["file"])
        self.assertIn(ord("二"), second["fonts"][0]["codepoints"])
        self.assertFalse((self.root / OUTPUT / first["fonts"][0]["file"]).exists())
        validate_fonts(self.root, self.specs)

    def test_unchanged_build_uses_cache_and_leaves_mtimes_unchanged(self):
        self.build()
        files = [self.root / CSS, *(self.root / OUTPUT).iterdir()]
        times = {p: p.stat().st_mtime_ns for p in files}
        with patch("fontTools.subset.Subsetter.subset", side_effect=AssertionError("Unexpected recompression")):
            self.build()
        self.assertEqual(times, {p: p.stat().st_mtime_ns for p in files})

    def test_corrupted_cached_font_is_detected_and_rebuilt(self):
        result = self.build()
        (self.root / OUTPUT / result["fonts"][0]["file"]).write_bytes(b"corrupt")
        with self.assertRaises(ValueError):
            validate_fonts(self.root, self.specs)
        self.build()
        validate_fonts(self.root, self.specs)

    def test_source_font_change_invalidates_cache(self):
        first = self.build()
        tiny_font(self.root / "fonts/Tiny.ttf", width=700)
        second = self.build()
        self.assertNotEqual(first["fonts"][0]["file"], second["fonts"][0]["file"])

    def test_clean_rebuild_produces_the_same_content_hashes(self):
        first = self.build()
        shutil.rmtree(self.root / OUTPUT)
        (self.root / CSS).unlink()
        second = self.build()
        self.assertEqual([f["sha256"] for f in first["fonts"]], [f["sha256"] for f in second["fonts"]])

    def test_original_glyph_bounds_are_not_recalculated(self):
        source_path = self.root / "fonts/Tiny.ttf"
        with TTFont(source_path, recalcBBoxes=False) as font:
            name = font.getBestCmap()[ord("一")]
            font["glyf"][name].xMin -= 1
            expected = font["glyf"][name].xMin
            font.save(source_path)
        result = self.build()
        with TTFont(self.root / OUTPUT / result["fonts"][0]["file"]) as target:
            self.assertEqual(target["glyf"][target.getBestCmap()[ord("一")]].xMin, expected)

    def test_glyph_outlines_and_metrics_are_preserved(self):
        result = self.build()
        source = TTFont(self.root / "fonts/Tiny.ttf")
        target = TTFont(self.root / OUTPUT / result["fonts"][0]["file"])
        for point in result["fonts"][0]["codepoints"]:
            drawings, metrics = [], []
            for font in [source, target]:
                name = font.getBestCmap()[point]
                glyphs = font.getGlyphSet()
                pen = DecomposingRecordingPen(glyphs)
                glyphs[name].draw(pen)
                drawings.append(pen.value)
                metrics.append(font["hmtx"][name])
            self.assertEqual(drawings[0], drawings[1])
            self.assertEqual(metrics[0], metrics[1])
        self.assertEqual(source["hhea"].ascent, target["hhea"].ascent)
        self.assertEqual(source["hhea"].descent, target["hhea"].descent)
        source.close(); target.close()


if __name__ == "__main__":
    unittest.main()
