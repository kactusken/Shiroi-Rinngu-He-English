#!/usr/bin/env python3
"""Variable-width English text: the code and letter table the build puts into the ROM, and pixel measures.

  vwf.py sheet PNG            the letter table as the game draws it
  vwf.py width 'some text'    pixels the text takes

The game's message loop draws 12 px cells. tools/asm/vwf.asm hooks it (at 00:B2DB): a run of English letters
(ASCII bytes, one-byte tokens, full-width Latin) is drawn proportionally into a line in RAM, cut into 12 px
cells, and each cell is cached in RAM under a virtual Shift-JIS code that the loop then draws, stores and
redraws like any Japanese character (the glyph lookup 00:BB41 is hooked to hand out cached cells).
Where things go (all in the ROM expanded to 2 MB):
  3F:8000 (file 0x1F8000)  the code              3F:A000 (0x1FA000)  letter table, 16 bytes per letter 0x20-0x7F:
                                                   advance, 12 rows (leftmost pixel = bit 7), 3 spare
  00:BB41 (0x3B41)         JML bb41 replacing PHP / PHD / REP #$20
  00:B2DB (0x32DB)         JML 3F:8000 replacing  BEQ B309 / BRA B312
  05:C94E (0x2C94E)        JSL namedel / BRA C967: the name keyboard's delete redraws the name (proportional)
Window text is 16 cells = 192 px wide; the build wraps lines at LINE_PX.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asm65816  # noqa: E402
import enfont  # noqa: E402
import paths  # noqa: E402

CODE_AT = 0x1F8000
TABLE_AT = 0x1FA000
GLYPH_AT = 0x3B41      # 00:BB41 the glyph lookup (PHP / PHD / REP #$20) -> JML bb41: cached English cells
GLYPH_ORIGINAL = bytes([0x08, 0x0B, 0xC2, 0x20])
HOOK_AT = 0x32DB
LEN_AT = 0x387E        # 00:B87E..B895, the game's message length (strlen): every byte but 0A 0D 07 06 counted 2 (Shift-JIS); the next message is found with it
LEN_ORIGINAL = bytes.fromhex('c8c90a00f0f3c90d00f0eec90700f0e9c90600f0e4c880e1')
LEN_NEW = bytes.fromhex('c8c98000' '90f3' 'c8' '80f0') + b'\xea' * 15     # below 0x80 = one byte (English), 0x80+ = two bytes (Shift-JIS)
WAIT_AT = 0x295DF       # 05:95DF LDA #$001E / PHA: the wait after an automatic message (30 frames) becomes msgwait
WAIT_ORIGINAL = bytes.fromhex('a91e0048')
FMT_AT = 0x39C1        # 00:B9C1 the formatter's plain copy (LDA [$1B] / STA $0000,Y / INC $1B x2 / INY x2): two bytes a step -> fmtc
FMT_ORIGINAL = bytes.fromhex('a71b990000e61be61bc8c8')
FMTS_AT = 0x390B       # 00:B90B the formatter's %s copy loop, two bytes a step -> scopy
FMTS_ORIGINAL = bytes.fromhex('a71129ff00f00da711')
FLUSH_AT = 0x3437      # 00:B437 BNE (D0 04): the end of a message skipped its final upload when the game's per-letter wait was on
HOOK_ORIGINAL = bytes([0xF0, 0x2C, 0x80, 0x33])
NAMEDEL_AT = 0x2C94E   # 05:C94E..C966 name keyboard delete: cursor to column letters+4 -> JSL namedel (column 4, redraw the name) / BRA C967
NAMEDEL_ORIGINAL = bytes.fromhex('a9000048a90400186f37787e48224a9a00a83b186904001b98')
LINE_PX = 190          # widest dialogue line (the window is 192 px)
NAME_PX = 72           # room kept for the heroine's name ({name}: 6 full-width letters)
PAGE_ROWS = 4
TOKENS_AT = 0x1FA800   # one-byte tokens: 4 bytes each (up to 3 letters), codes 0xA0-0xDF and 0xF0-0xFE
MAX_TOKENS = 79


def token_code(i):
    return 0xA0 + i if i < 64 else 0xF0 + (i - 64)


def tokens_file():
    return paths.TEXT / 'pairs.lst'


def load_tokens():
    p = tokens_file()
    if not p.exists():
        return []
    out = []
    for ln in p.read_text().splitlines():
        if ln and not ln.startswith('#'):
            out.append(ln.replace('_', ' '))
    return out[:MAX_TOKENS]


def compress(text, toks=None):
    """Fewest bytes for plain text using the one-byte tokens (DP); returns bytes."""
    toks = load_tokens() if toks is None else toks
    codes = {t: token_code(i) for i, t in enumerate(toks)}
    n = len(text)
    best = [None] * (n + 1)
    best[0] = (0, None)
    for i in range(n):
        if best[i] is None:
            continue
        for L in (1, 2, 3):
            if i + L > n:
                break
            t = text[i:i + L]
            if L == 1 or t in codes:
                c = best[i][0] + 1
                if best[i + L] is None or c < best[i + L][0]:
                    best[i + L] = (c, i)
    out, i = [], n
    while i > 0:
        j = best[i][1]
        t = text[j:i]
        out.append(bytes([codes[t]]) if len(t) > 1 else t.encode('ascii'))
        i = j
    return b''.join(reversed(out))


def choose_tokens(strings):
    """Pick the MAX_TOKENS letter runs (2-3 characters, inside words) that save the most bytes."""
    import collections
    import re
    cnt = collections.Counter()
    for s in strings:
        for w in re.findall(r"[A-Za-z']+", s):
            for L in (2, 3):
                for i in range(len(w) - L + 1):
                    cnt[w[i:i + L]] += 1
    best = sorted(cnt, key=lambda t: (-cnt[t] * (len(t) - 1), t))[:MAX_TOKENS]
    tokens_file().write_text('# one-byte tokens (tools/vwf.py choose); _ = space\n' + '\n'.join(t.replace(' ', '_') for t in best) + '\n')
    return best


def adv(ch):
    return enfont.advance(ch)


def width(text):
    """Pixels of plain text (advances, the last gap not counted)."""
    return sum(adv(c) for c in text) - (1 if text and text[-1] != ' ' else 0)


def table():
    out = bytearray()
    for code in range(0x20, 0x80):
        ch = chr(code)
        if ch in enfont._ART or ch == ' ':
            w, rows = enfont.letter(ch)
            a = adv(ch)
            body = bytearray(12)
            for y, bits in rows.items():
                if y < 12:
                    body[y] = sum(1 << (7 - i) for i, c in enumerate(bits) if c == '#')
            out += bytes([a]) + body + bytes(3)
        else:
            out += bytes([0]) + bytes(15)
    return bytes(out)


def code(labels=False):
    src = (Path(__file__).resolve().parent / 'asm' / 'vwf.asm').read_text()
    out, lab = asm65816.assemble(src, 0x3F8000)
    return (out, lab) if labels else out


def apply(rom):
    """Write the code, table, stub and hook into a (2 MB) ROM bytearray."""
    if len(rom) < 0x200000:
        raise SystemExit('vwf.apply: the ROM must be expanded to 2 MB first')
    c, lab = code(True)
    t = table()
    if len(c) > TABLE_AT - CODE_AT:
        raise SystemExit(f'vwf code is {len(c)} bytes, too long for its space')
    if bytes(rom[HOOK_AT:HOOK_AT + 4]) != HOOK_ORIGINAL:
        raise SystemExit('vwf.apply: the hook site does not hold the original bytes')
    if bytes(rom[GLYPH_AT:GLYPH_AT + 4]) != GLYPH_ORIGINAL:
        raise SystemExit('vwf.apply: the glyph lookup does not hold the original bytes')
    rom[CODE_AT:CODE_AT + len(c)] = c
    tt = bytearray(MAX_TOKENS * 4)
    for i, tok in enumerate(load_tokens()):
        for k, ch in enumerate(tok):
            tt[i * 4 + k] = ord(ch)
    rom[TOKENS_AT:TOKENS_AT + len(tt)] = tt
    rom[TABLE_AT:TABLE_AT + len(t)] = t
    rom[GLYPH_AT:GLYPH_AT + 4] = bytes([0x5C]) + lab['bb41'].to_bytes(3, 'little')
    rom[HOOK_AT:HOOK_AT + 4] = bytes([0x5C, 0x00, 0x80, 0x3F])
    if bytes(rom[LEN_AT:LEN_AT + 24]) != LEN_ORIGINAL:
        raise SystemExit('vwf.apply: the message length routine does not hold the original bytes')
    rom[LEN_AT:LEN_AT + 24] = LEN_NEW
    if bytes(rom[WAIT_AT:WAIT_AT + 4]) != WAIT_ORIGINAL:
        raise SystemExit('vwf.apply: the message wait site does not hold the original bytes')
    rom[WAIT_AT:WAIT_AT + 4] = bytes([0x22]) + lab['msgwait'].to_bytes(3, 'little')
    if bytes(rom[FLUSH_AT:FLUSH_AT + 2]) != b'\xd0\x04':
        raise SystemExit('vwf.apply: the end-of-message site does not hold the original bytes')
    rom[FLUSH_AT:FLUSH_AT + 2] = b'\xea\xea'
    if bytes(rom[NAMEDEL_AT:NAMEDEL_AT + len(NAMEDEL_ORIGINAL)]) != NAMEDEL_ORIGINAL:
        raise SystemExit('vwf.apply: the name keyboard delete does not hold the original bytes')
    rom[NAMEDEL_AT:NAMEDEL_AT + 6] = bytes([0x22]) + lab['namedel'].to_bytes(3, 'little') + b'\x80\x13'
    for at, orig, name in ((FMT_AT, FMT_ORIGINAL, 'fmtc'), (FMTS_AT, FMTS_ORIGINAL, 'scopy')):
        if bytes(rom[at:at + len(orig)]) != orig:
            raise SystemExit(f'vwf.apply: the formatter ({name}) does not hold the original bytes')
        rom[at:at + 4] = bytes([0x5C]) + lab[name].to_bytes(3, 'little')     # always upload the last letters (they were left out of the window)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ['width']:
        print(width(argv[1]))
    elif argv[:1] == ['choose']:
        import csv
        strs = []
        for name in ('system.csv', 'moves.csv'):
            with open(paths.TEXT / name, encoding='utf-8', newline='') as f:
                strs += [r['english'] for r in csv.DictReader(ln for ln in f if not ln.startswith('#')) if r['english'].strip() and 'keep:' not in (r['notes'] or '')]
        print(choose_tokens(strs))
    elif argv[:1] == ['sheet']:
        from PIL import Image
        t = table()
        im = Image.new('L', (16 * 10, 6 * 14), 255)
        for i in range(96):
            for y in range(12):
                for x in range(8):
                    if t[i * 16 + 1 + y] >> (7 - x) & 1:
                        im.putpixel(((i % 16) * 10 + x, (i // 16) * 14 + y), 0)
        im.resize((im.width * 5, im.height * 5), Image.NEAREST).save(argv[1])
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
