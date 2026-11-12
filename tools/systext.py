#!/usr/bin/env python3
"""The game's other text - menus, names, stats, moves, places - as in-place strings in the ROM.

  systext.py dump      write translation/text/system.csv and moves.csv (keeps English and notes)
  systext.py check     every row's offset still holds its Japanese bytes

Layout (from the ROM; the strings are NUL-terminated Shift-JIS, mostly in fixed 16-byte records or
packed menus; English goes back IN PLACE, so every English string has at most the Japanese string's
bytes - as cells, tools/tokens.py - and is padded with full-width spaces when the original was):
  0xD0000-0xD8000   choice menus in the event scripts: opcode 25 13 <count>, then the items (\\n
                    between them, NUL at the end); found by the opcode (4 menus)
  0xEB303-0xEEC4A   wrestling move names (about 370)
  0xF8000-0xFCD00   menus, messages, names of people and places, stats, clubs, help text, ending text
Rows: offset, max_bytes (the Japanese string's length), section, japanese, english, notes. In the
text `\\n` is a line break (0x0A), `\\r` a carriage return (0x0D, used as the line break in some boxes),
`{xNN}` any other byte, `%s %2d` format codes stay as they are.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

ASC = set(b'%sd 0123456789')
EXTRA = [0xFBF4C, 0xFC504, 0xFC5CC]          # strings the scanner can't take (see docs/TECHNICAL.md)
EVENTS = (0xD0000, 0xD8000)                  # event scripts: choice menus are opcode 25 13 <count> + text
REGIONS = [(0xD3000, 0xD4000), (0xEB000, 0xF0000), (0xF8000, 0xFD000)]

# section names: (first offset, name); a row belongs to the last one at or before its offset
SECTIONS = [
    (0xD0000, 'choices (event script menus)'),
    (0xEB000, 'finishing moves (move names)'),
    (0xED000, 'moves (move names)'),
    (0xF8000, 'credits (staff roll labels: keep Japanese)'),
    (0xF8080, 'custom wrestler bank save/delete menus (versus mode)'),
    (0xF8500, 'schedule, training and status menus'),
    (0xF8600, 'save and load'),
    (0xF8711, 'title menu'),
    (0xF8755, 'profile screen'),
    (0xF8814, 'training result messages'),
    (0xF88B8, 'swimsuit shop and hair salon'),
    (0xF8A28, 'injury notice'),
    (0xF9071, 'calendar: holidays'),
    (0xF91AB, 'zodiac signs'),
    (0xF97FF, 'names of people (speaker ids 0-45, in order)'),
    (0xF9B45, 'status screens (templates: keep the line structure)'),
    (0xF9F19, 'places to go (fixed 16 byte lines)'),
    (0xFA471, 'school clubs (fixed 16 byte records)'),
    (0xFAE63, 'numbering'),
    (0xFB50E, 'training exercises'),
    (0xFB9BC, 'statistics and skill names (labels)'),
    (0xFBE7B, 'help and prompts'),
    (0xFC18C, 'arenas (fixed 16 byte records)'),
    (0xFC454, 'name entry keyboards (kana, latin)'),
    (0xFCA86, 'ending story and staff roll (staff roll: keep Japanese)'),
]
KEEP_FROM = {0xF8018: 0xF8080, 0xFCB30: 0xFD000}     # credit ranges kept in Japanese (first, end)


def section(off):
    name = SECTIONS[0][1]
    for o, n in SECTIONS:
        if o <= off:
            name = n
    return name


def is_lead(b):
    return 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEF


def strings(rom):
    out = {}
    for lo, hi in REGIONS:
        i = lo
        while i < hi:
            b = rom[i]
            if not (is_lead(b) and 0x40 <= rom[i + 1] <= 0xFC and rom[i + 1] != 0x7F) and b != 0x25:
                i += 1
                continue
            j, pairs = i, 0
            while j < hi:
                b = rom[j]
                if is_lead(b) and j + 1 < hi and 0x40 <= rom[j + 1] <= 0xFC and rom[j + 1] != 0x7F:
                    j += 2
                    pairs += 1
                elif b in (0x0A, 0x0D) or b in ASC:
                    j += 1
                else:
                    break
            if pairs >= 2 and j < hi and rom[j] == 0:
                out[i] = j
            i = j if j > i else i + 1
    lo, hi = EVENTS
    i = rom.find(b'\x25\x13', lo, hi)
    while i >= 0:
        a = i + 3
        if 1 <= rom[i + 2] <= 8 and is_lead(rom[a]):
            out[a] = rom.index(b'\x00', a)
        i = rom.find(b'\x25\x13', i + 1, hi)
    for a in EXTRA:
        j = a
        while rom[j] != 0 and not (rom[j] in (1, 2, 3, 4, 5) and rom[j + 1] == 0):
            j += 2 if is_lead(rom[j]) else 1
        out[a] = j
    inside = [(a, out[a]) for a in EXTRA]
    out = {k: v for k, v in out.items() if k in EXTRA or not any(a < k < b for a, b in inside)}
    return dict(sorted(out.items()))


def to_text(b):
    out, i = [], 0
    while i < len(b):
        c = b[i]
        if is_lead(c):
            out.append(bytes(b[i:i + 2]).decode('cp932'))
            i += 2
        elif c == 0x0A:
            out.append('\\n')
            i += 1
        elif c == 0x0D:
            out.append('\\r')
            i += 1
        elif 0x20 <= c < 0x7F:
            out.append(chr(c))
            i += 1
        else:
            out.append('{x%02X}' % c)
            i += 1
    return ''.join(out)


def to_bytes(s):
    out, i = bytearray(), 0
    while i < len(s):
        if s[i] == '\\' and s[i + 1] in 'nr':
            out.append(0x0A if s[i + 1] == 'n' else 0x0D)
            i += 2
        elif s[i] == '{' and s[i + 1] == 'x':
            out.append(int(s[i + 2:i + 4], 16))
            i += 5
        elif ord(s[i]) < 0x80:
            out.append(ord(s[i]))
            i += 1
        else:
            out += s[i].encode('cp932')
            i += 1
    return bytes(out)


def rows(rom):
    res = []
    for s, e in strings(rom).items():
        res.append((s, e - s, section(s), to_text(rom[s:e])))
    return res


def dump():
    rom = paths.ROM.read_bytes()
    paths.TEXT.mkdir(parents=True, exist_ok=True)
    groups = {'system.csv': [], 'moves.csv': []}
    for s, n, sec, jp in rows(rom):
        groups['moves.csv' if 'move names' in sec else 'system.csv'].append((s, n, sec, jp))
    for name, items in groups.items():
        p = paths.TEXT / name
        old = {}
        if p.exists():
            with open(p, encoding='utf-8', newline='') as f:
                lines = [ln for ln in f if not ln.startswith('#')]
            for r in csv.DictReader(lines):
                old[r['offset']] = r
        head = [f'# {"Move names" if name == "moves.csv" else "Menus, messages, names, stats, places, clubs, help and ending text"}: '
                'written back IN PLACE (see tools/systext.py).',
                '# english: at most as many cells as japanese has characters (max_bytes / 2); a tool checks the fit.',
                '# `\\n` / `\\r` are line breaks, `%s` `%2d` `{xNN}` stay as they are. Fixed-width fields are padded by the build.',
                '# Rows whose notes hold "# keep:" stay Japanese (copy the Japanese into english).']
        with open(p, 'w', encoding='utf-8', newline='') as f:
            for ln in head:
                f.write(ln + '\n')
            w = csv.writer(f, lineterminator='\n')
            w.writerow(['offset', 'max_bytes', 'section', 'japanese', 'english', 'notes'])
            for s, n, sec, jp in items:
                o = old.get(f'0x{s:06X}', {})
                note = o.get('notes', '') or f'# section: {sec}'
                if not o and any(a <= s < b for a, b in KEEP_FROM.items()):   # new rows only: keep hand edits
                    note = '# keep: credits'
                    o = dict(o, english=jp)
                w.writerow([f'0x{s:06X}', n, sec, jp, o.get('english', ''), note])
        print(f'{name}: {len(items)} rows')


def check():
    rom = paths.ROM.read_bytes()
    bad = 0
    for name in ('system.csv', 'moves.csv'):
        with open(paths.TEXT / name, encoding='utf-8', newline='') as f:
            lines = [ln for ln in f if not ln.startswith('#')]
        for r in csv.DictReader(lines):
            o, n = int(r['offset'], 16), int(r['max_bytes'])
            if to_bytes(r['japanese']) != rom[o:o + n]:
                bad += 1
                print('differs at', r['offset'])
    print('ok' if not bad else f'{bad} rows differ')
    return not bad


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ['dump']:
        dump()
    elif argv[:1] == ['check']:
        sys.exit(0 if check() else 1)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
