#!/usr/bin/env python3
"""The game's 12x12 font: Shift-JIS code -> glyph -> ROM bytes, and back.

  jisfont.py sheet CODE_FROM COUNT PNG   draw COUNT glyphs starting at the SJIS code (hex), labelled
  jisfont.py info                        layout summary

How the game draws a character (from the code, verified in game):
  - the message loop (00:B2A0 ...) takes a 2-byte Shift-JIS code from the string, converts it to a
    JIS X 0208 code (00:B713), then to a glyph number (00:BB41) from a table of per-row bases
    (00:BBAD, indexed by JIS high byte - 0x20): rows 0x21 (symbols), 0x23 (digits, Latin), 0x24
    (hiragana), 0x25 (katakana) and the level-1 kanji rows 0x30-0x4F are present, 94 glyphs a row;
  - glyph n lives in bank 1 + n // 0x555 at offset 0x8000 + (n % 0x555) * 24: 12 rows of one little-endian 16-bit word,
    the leftmost pixel in bit 15, only the top 12 bits used (kanji use 11). As a file offset: glyph n at
    0x8000 + (n // 0x555) * 0x8000 + (n % 0x555) * 24.
  - every character cell is 12 pixels wide on screen (cells step 12 px, so tiles shift by 0/4).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

GLYPH_BYTES = 24
PER_BANK = 0x555
FONT_BASE = 0x8000          # file offset of glyph 0 (bank 1)
# JIS rows present in the font, in glyph order; each has 94 glyphs
ROWS = [0x21, 0x23, 0x24, 0x25] + list(range(0x30, 0x50))
KANJI_LAST = 0x4F53         # last JIS level-1 code in the font (腕)


def glyph_count():
    n = 0
    for row in ROWS:
        n += 94
    return n - (0x7E - 0x53)      # row 0x4F stops at 0x53


ROW_START = {}
_n = 0
for _row in ROWS:
    ROW_START[_row] = _n
    _n += 94


def sjis_to_jis(code):
    """Shift-JIS double-byte code (int) -> JIS X 0208 (int); the game's own arithmetic."""
    hi, lo = code >> 8, code & 0xFF
    hi -= 0x81 if hi <= 0x9F else 0xC1
    if lo >= 0x80:
        lo -= 1
    row = hi * 2 + 0x21
    if lo >= 0x9E:
        row += 1
        lo -= 0x7D
    else:
        lo -= 0x1F
    return (row << 8) | lo


def jis_to_sjis(jis):
    row, col = jis >> 8, jis & 0xFF
    hi = (row - 0x21) // 2 + 0x81
    if hi > 0x9F:
        hi += 0x40
    if row & 1:
        lo = col + 0x1F
        if lo >= 0x7F:
            lo += 1
    else:
        lo = col + 0x7E
    return (hi << 8) | lo


def glyph_index(jis):
    row, col = jis >> 8, jis & 0xFF
    if row not in ROW_START or not 0x21 <= col <= 0x7E:
        return None
    n = ROW_START[row] + col - 0x21
    return n if n < glyph_count() else None


def glyph_of_sjis(code):
    return glyph_index(sjis_to_jis(code))


def sjis_of_glyph(n):
    for row in ROWS:
        if ROW_START[row] <= n < ROW_START[row] + 94:
            return jis_to_sjis((row << 8) | (n - ROW_START[row] + 0x21))
    return None


def offset(n):
    return FONT_BASE + (n // PER_BANK) * 0x8000 + (n % PER_BANK) * GLYPH_BYTES


def read(rom, n):
    """12 rows as ints of 12 bits (leftmost pixel = bit 11)."""
    o = offset(n)
    return [(rom[o + 2 * y] | (rom[o + 2 * y + 1] << 8)) >> 4 for y in range(12)]


def write(rom, n, rows):
    o = offset(n)
    for y in range(12):
        v = (rows[y] & 0xFFF) << 4
        rom[o + 2 * y], rom[o + 2 * y + 1] = v & 0xFF, v >> 8


def char_of_glyph(n):
    s = sjis_of_glyph(n)
    return bytes([s >> 8, s & 0xFF]).decode('sjis', 'replace') if s else '?'


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    import paths
    if not argv or argv[0] == 'info':
        print(f'{glyph_count()} glyphs, rows {[hex(r) for r in ROWS]}, last glyph at file '
              f'{offset(glyph_count() - 1):#x}')
        return
    if argv[0] == 'sheet':
        from PIL import Image, ImageDraw
        rom = bytearray(paths.ROM.read_bytes())
        start, count, out = int(argv[1], 16), int(argv[2]), argv[3]
        n0 = glyph_of_sjis(start)
        cols = 16
        rows = (count + cols - 1) // cols
        im = Image.new('RGB', (cols * 14, rows * 14), 'white')
        for i in range(count):
            for y, row in enumerate(read(rom, n0 + i)):
                for x in range(12):
                    if row >> (11 - x) & 1:
                        im.putpixel(((i % cols) * 14 + x, (i // cols) * 14 + y), (0, 0, 0))
        im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(out)
        return
    sys.exit(__doc__)


if __name__ == '__main__':
    main()
