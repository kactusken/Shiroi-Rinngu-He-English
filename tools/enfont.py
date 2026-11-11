#!/usr/bin/env python3
"""The English letters: a small proportional pixel font (widths 1-5 px, 12 rows) for the variable-width renderer.

  enfont.py sheet PNG              every letter, 6x, to check by eye
  enfont.py text PNG 'some text'   a line with the game's advances

tools/vwf.py turns these letters into the ROM table the renderer draws from (16 bytes per letter: advance, 12 rows).
Metrics: capitals 7 rows (rows 2-8), x-height 5 (rows 4-8), baseline after row 8, descenders rows 9-10.
Each letter is followed by a 1 px gap; a space advances 3 px.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

CELL = 12
CENTER = True    # centre a token in its cell (spreads the unused pixels to both sides)
SPACE = 3
TOP = 2          # row of the first pixel row of a 7-row letter

# Letters as pixel rows. '.' blank, '#' ink. Each entry: the rows from the letter's top downward;
# `TOP` is added unless the entry starts with '>' + n (a drop of n rows from TOP, for x-height
# letters).
_ART = {}


def _def(ch, rows, drop=0):
    _ART[ch] = (rows, drop)


# ---- lowercase (x-height letters start 2 rows lower: drop=2)
_def('a', ['.##.', '...#', '.###', '#..#', '.###'], 2)
_def('b', ['#...', '#...', '###.', '#..#', '#..#', '#..#', '###.'])
_def('c', ['.###', '#...', '#...', '#...', '.###'], 2)
_def('d', ['...#', '...#', '.###', '#..#', '#..#', '#..#', '.###'])
_def('e', ['.##.', '#..#', '####', '#...', '.###'], 2)
_def('f', ['.##', '#..', '###', '#..', '#..', '#..', '#..'])
_def('g', ['.###', '#..#', '#..#', '#..#', '.###', '...#', '.##.'], 2)
_def('h', ['#...', '#...', '#.#.', '##.#', '#..#', '#..#', '#..#'])
_def('i', ['#', '.', '#', '#', '#', '#', '#'])
_def('j', ['.#', '..', '.#', '.#', '.#', '.#', '.#', '.#', '#.'])
_def('k', ['#...', '#...', '#..#', '#.#.', '##..', '#.#.', '#..#'])
_def('l', ['#', '#', '#', '#', '#', '#', '#'])
_def('m', ['##.#.', '#.#.#', '#.#.#', '#.#.#', '#.#.#'], 2)
_def('n', ['#.#.', '##.#', '#..#', '#..#', '#..#'], 2)
_def('o', ['.##.', '#..#', '#..#', '#..#', '.##.'], 2)
_def('p', ['###.', '#..#', '#..#', '#..#', '###.', '#...', '#...'], 2)
_def('q', ['.###', '#..#', '#..#', '#..#', '.###', '...#', '...#'], 2)
_def('r', ['#.#', '##.', '#..', '#..', '#..'], 2)
_def('s', ['.###', '#...', '.##.', '...#', '###.'], 2)
_def('t', ['.#.', '###', '.#.', '.#.', '.#.', '..#'], 1)
_def('u', ['#..#', '#..#', '#..#', '#..#', '.###'], 2)
_def('v', ['#...#', '#...#', '.#.#.', '.#.#.', '..#..'], 2)
_def('w', ['#...#', '#...#', '#.#.#', '#.#.#', '.#.#.'], 2)
_def('x', ['#...#', '.#.#.', '..#..', '.#.#.', '#...#'], 2)
_def('y', ['#..#', '#..#', '#..#', '.###', '...#', '...#', '.##.'], 2)
_def('z', ['####', '...#', '.##.', '#...', '####'], 2)
# ---- capitals
_def('A', ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'])
_def('B', ['####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'])
_def('C', ['.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'])
_def('D', ['####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'])
_def('E', ['#####', '#....', '#....', '####.', '#....', '#....', '#####'])
_def('F', ['#####', '#....', '#....', '####.', '#....', '#....', '#....'])
_def('G', ['.###.', '#...#', '#....', '#.###', '#...#', '#...#', '.###.'])
_def('H', ['#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'])
_def('I', ['###', '.#.', '.#.', '.#.', '.#.', '.#.', '###'])
_def('J', ['..###', '....#', '....#', '....#', '....#', '#...#', '.###.'])
_def('K', ['#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'])
_def('L', ['#....', '#....', '#....', '#....', '#....', '#....', '#####'])
_def('M', ['#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#'])
_def('N', ['#...#', '##..#', '#.#.#', '#.#.#', '#..##', '#...#', '#...#'])
_def('O', ['.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'])
_def('P', ['####.', '#...#', '#...#', '####.', '#....', '#....', '#....'])
_def('Q', ['.###.', '#...#', '#...#', '#...#', '#.#.#', '#..#.', '.##.#'])
_def('R', ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'])
_def('S', ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'])
_def('T', ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'])
_def('U', ['#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'])
_def('V', ['#...#', '#...#', '#...#', '#...#', '.#.#.', '.#.#.', '..#..'])
_def('W', ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '##.##', '#...#'])
_def('X', ['#...#', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '#...#'])
_def('Y', ['#...#', '#...#', '.#.#.', '..#..', '..#..', '..#..', '..#..'])
_def('Z', ['#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'])
# ---- digits
_def('0', ['.##.', '#..#', '#..#', '#..#', '#..#', '#..#', '.##.'])
_def('1', ['.#.', '##.', '.#.', '.#.', '.#.', '.#.', '###'])
_def('2', ['.##.', '#..#', '...#', '..#.', '.#..', '#...', '####'])
_def('3', ['.##.', '#..#', '...#', '.##.', '...#', '#..#', '.##.'])
_def('4', ['..#.', '.##.', '#.#.', '#.#.', '####', '..#.', '..#.'])
_def('5', ['####', '#...', '###.', '...#', '...#', '#..#', '.##.'])
_def('6', ['.##.', '#...', '###.', '#..#', '#..#', '#..#', '.##.'])
_def('7', ['####', '...#', '..#.', '..#.', '.#..', '.#..', '.#..'])
_def('8', ['.##.', '#..#', '#..#', '.##.', '#..#', '#..#', '.##.'])
_def('9', ['.##.', '#..#', '#..#', '.###', '...#', '...#', '.##.'])
# ---- punctuation (rows given from the row they start on, via drop)
_def('.', ['#'], 6)
_def(',', ['.#', '#.'], 6)
_def('!', ['#', '#', '#', '#', '#', '.', '#'])
_def('?', ['.##.', '#..#', '...#', '..#.', '.#..', '....', '.#..'])
_def("'", ['#', '#'])
_def('"', ['#.#', '#.#'])
_def(':', ['#', '.', '.', '.', '#'], 2 + 0)
_def(';', ['#', '.', '.', '.', '#', '#'], 2)
_def('-', ['###'], 4)
_def('(', ['.#', '#.', '#.', '#.', '#.', '#.', '.#'])
_def(')', ['#.', '.#', '.#', '.#', '.#', '.#', '#.'])
_def('/', ['..#', '..#', '.#.', '.#.', '.#.', '#..', '#..'])
_def('&', ['.##..', '#..#.', '.##..', '#.#.#', '#..#.', '#..#.', '.##.#'])
_def('%', ['#...#', '#..#.', '...#.', '..#..', '.#...', '.#..#', '#...#'])
_def('+', ['.#.', '.#.', '###', '.#.', '.#.'], 2)
_def('*', ['#.#', '.#.', '#.#'], 3)
_def('#', ['.#.#.', '#####', '.#.#.', '#####', '.#.#.'], 2)
_def('=', ['####', '....', '####'], 3)
_def('<', ['..#', '.#.', '#..', '.#.', '..#'], 2)
_def('>', ['#..', '.#.', '..#', '.#.', '#..'], 2)
_def('_', ['####'], 8)
_def('~', ['.#.#', '#.#.'], 4)
_def('^', ['.#.', '#.#'])
_def('@', ['.###.', '#...#', '#.###', '#.#.#', '#.###', '#....', '.###.'])
_def('$', ['.###', '#.#.', '.##.', '..#.', '###.', '..#.'])
_def('[', ['##', '#.', '#.', '#.', '#.', '#.', '##'])
_def(']', ['##', '.#', '.#', '.#', '.#', '.#', '##'])
_def('…', ['...'], 0)            # placeholder, replaced below
_def('♥', ['.#.#.', '#####', '#####', '.###.', '..#..'], 2)   # heart
_def('★', ['..#..', '.###.', '#####', '.###.', '#.#.#'], 2)   # star
_ART['…'] = (['#.#.#'], 6)       # ellipsis: three dots on the baseline, 5 wide
_ART[' '] = ([], 0)


def letter(ch):
    """(width, {row: bits}) of one letter; bits as a string of '#'/'.'."""
    if ch == ' ':
        return SPACE - 1, {}
    rows, drop = _ART[ch]
    w = max(len(r) for r in rows)
    return w, {TOP + drop + i: r for i, r in enumerate(rows)}


def advance(ch):
    return SPACE if ch == ' ' else letter(ch)[0] + 1


def letters():
    return sorted(_ART)


def width(token):
    """Pixels a token takes (advances; the last gap is not counted)."""
    return sum(advance(c) for c in token) - (0 if token.endswith(' ') else 1)


def fits(token):
    return sum(advance(c) for c in token) <= CELL


def bitmap(token):
    """12 rows of 12 bits for a token (letters left to right from pixel 0)."""
    out = [0] * 12
    x = 0
    for ch in token:
        w, rows = letter(ch)
        for y, bits in rows.items():
            if y >= 12:
                continue
            for i, c in enumerate(bits):
                if c == '#':
                    out[y] |= 1 << (11 - (x + i))
        x += advance(ch)
    if x > CELL:
        raise ValueError(f'token {token!r} is {x} px wide (limit {CELL})')
    if CENTER:
        slack = CELL - x
        sh = slack // 2
        out = [r >> sh for r in out]
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    from PIL import Image
    if argv and argv[0] == 'sheet':
        chars = [c for c in letters() if c != ' ']
        cols = 16
        rows = (len(chars) + cols - 1) // cols
        im = Image.new('L', (cols * 14, rows * 14), 255)
        for i, ch in enumerate(chars):
            for y, r in enumerate(bitmap(ch)):
                for x in range(12):
                    if r >> (11 - x) & 1:
                        im.putpixel(((i % cols) * 14 + x, (i // cols) * 14 + y), 0)
        im.resize((im.width * 6, im.height * 6), Image.NEAREST).save(argv[1])
        return
    if argv and argv[0] == 'text':
        text = argv[2]
        im = Image.new('L', (len(text) * 6 + 8, 14), 255)
        x = 0
        for ch in text:
            for yy, r in letter(ch)[1].items():
                for i, c in enumerate(r):
                    if c == '#' and x + i < im.width:
                        im.putpixel((x + i, yy), 0)
            x += advance(ch)
        im.resize((im.width * 6, im.height * 6), Image.NEAREST).save(argv[1])
        return
    sys.exit(__doc__)


if __name__ == '__main__':
    main()
