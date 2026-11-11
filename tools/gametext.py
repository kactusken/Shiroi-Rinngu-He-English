#!/usr/bin/env python3
"""Build steps that put the English into the ROM: the story script (relocated into the expanded ROM),
the in-place system strings, and the variable-width renderer (tools/vwf.py); also the lint hooks.

English is plain ASCII, one byte per letter, drawn by the hook in tools/asm/vwf.asm.

  gametext.py width 'some english'     pixels a line takes
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blocks  # noqa: E402
import enfont  # noqa: E402
import gamescript  # noqa: E402
import paths  # noqa: E402
import systext  # noqa: E402
import vwf  # noqa: E402

ROM = '/rom.sfc'
NEW_SIZE = 0x200000            # expanded ROM: banks $30-$3F; scenes from 0x180000, code and font at 0x1F8000
SCRIPT_AT = 0x180000
AUTO_FROM = 297                # scenes from here on have no page wait (07) in the Japanese: cut-scenes that run by themselves, where a 07 jumps ahead


def expand(rom):
    if len(rom) < NEW_SIZE:
        rom.extend(b'\xff' * (NEW_SIZE - len(rom)))


def english_text(lines):
    return ' '.join(ln.strip() for ln in lines if ln.strip())


# ------------------------------------------------------------------ layout (pixels)

def line_px(line):
    """Pixels of a line that may hold {name} and other codes."""
    total = 0
    for part in re.split(r'(\{[^{}]*\})', line):
        if part == '{name}':
            total += vwf.NAME_PX
        elif part.startswith('{'):
            continue
        elif part:
            total += sum(vwf.adv(c) for c in part.replace('…', '...'))
    return total - 1 if total else 0


def wrap(text, limit=vwf.LINE_PX):
    lines = []
    for para in text.split('{n}'):
        cur = ''
        for w in para.split():
            trial = w if not cur else cur + ' ' + w
            if line_px(trial) <= limit:
                cur = trial
            else:
                if not cur:
                    raise ValueError(f'word {w!r} is wider than a line')
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def ascii_bytes(text):
    out = bytearray()
    for part in re.split(r'(\{[^{}]*\})', text):
        if part == '{name}':
            out.append(0x06)
        elif part.startswith('{'):
            raise ValueError(f'unknown code {part}')
        else:
            for c in part.replace('…', '...'):
                if not (0x20 <= ord(c) < 0x7F) or c not in enfont._ART:
                    raise ValueError(f'no letter shape for {c!r}')
                out.append(ord(c))
    return bytes(out)


def message(text, rows=vwf.PAGE_ROWS, autoscroll=False):
    """Story text with {p} page breaks and {n} line breaks -> message bytes (0x0A between lines,
    0x0A 0x07 between pages). The window has 4 rows and the game scrolls it when a line break lands
    below the last row, so a page that is followed by another holds at most 3 lines (the break and
    the wait then leave all of it on screen); the message's last page may take 4."""
    if autoscroll:        # a cut-scene narration (the intro): the game scrolls it by itself, a button press would skip it
        return b'\x0a'.join(ascii_bytes(ln) for ln in wrap(text.replace('{p}', '{n}')))
    pages = [wrap(p.strip()) if p.strip() else [] for p in text.split('{p}')]
    chunks = []
    for pi, lines in enumerate(pages):
        last_page = pi == len(pages) - 1
        k = 0
        while k < max(len(lines), 1):
            rest = len(lines) - k
            take = rest if (last_page and rest <= rows) else min(rest, rows - 1)
            chunks.append(lines[k:k + take])
            k += max(take, 1)
    out = bytearray()
    for chunk in chunks:
        if out:
            out += b'\x0a\x07'
        out += b'\x0a'.join(ascii_bytes(ln) for ln in chunk)
    return bytes(out)


# ------------------------------------------------------------------ story script

def scripts_step(path, files):
    rom = files.get(ROM)
    expand(rom)
    scenes = gamescript.read_scenes(bytes(rom))
    done, auto = {}, set()
    for p in sorted(Path(path).glob('s*.txt')):
        for b in blocks.BlockFile(p).blocks:
            if b.english:
                done[b.id] = english_text(b.english)
            if any('autoscroll' in c for c in b.tagged('#')):
                auto.add(b.id)
    at, nenglish = SCRIPT_AT, 0
    for sc in scenes:
        parts = [bytes([0xFF, sc.id, sc.group])]
        for n, m in enumerate(sc.msgs):
            bid = gamescript.block_id(sc, n)
            if bid in done:
                try:
                    body = message(done[bid], autoscroll=bid in auto or sc.index >= AUTO_FROM)
                except ValueError as e:
                    raise SystemExit(f'{bid}: {e}')
                nenglish += 1
            else:
                body = m.text
            parts.append(bytes([m.spk, m.face]) + body + b'\x00')
        data = b''.join(parts)
        if len(data) > 0x7F00:
            raise SystemExit(f'scene {sc.index} is {len(data)} bytes: too long for one bank')
        if at % 0x8000 + len(data) > 0x8000:
            at += 0x8000 - at % 0x8000
        if at + len(data) > vwf.CODE_AT:
            raise SystemExit('the expanded ROM is full')
        rom[at:at + len(data)] = data
        cpu_off = at + 1                      # points at the id byte, after the FF
        bank, a = cpu_off >> 15, (cpu_off & 0x7FFF) | 0x8000
        t = gamescript.TABLE + 4 * sc.index
        rom[t:t + 4] = bytes([a & 0xFF, a >> 8, bank, 0])
        at += len(data)
    files.put(ROM, rom)
    print(f'script: {nenglish} of {sum(len(s.msgs) for s in scenes)} messages in English, '
          f'{at - SCRIPT_AT:#x} bytes in the expanded ROM')


# ------------------------------------------------------------------ system strings

CODE_SPLIT = re.compile(r'(\\n|\\r|\{x[0-9A-Fa-f]{2}\}|%[-0-9.]*[sdx])')


def encode_line(text):
    """One English string -> bytes (without the terminator)."""
    out = bytearray()
    for part in CODE_SPLIT.split(text):
        if part == '\\n':
            out.append(0x0A)
        elif part == '\\r':
            out.append(0x0D)
        elif part.startswith('{x'):
            out.append(int(part[2:4], 16))
        elif part.startswith('%'):
            out += part.encode('ascii')
        elif part:
            out += ascii_bytes(part)
    return bytes(out)


def encode_fit(text, maxb):
    """encode_line, with the one-byte tokens (tools/vwf.py) when the plain text is longer than maxb."""
    data = encode_line(text)
    if len(data) <= maxb:
        return data
    out = bytearray()
    for part in CODE_SPLIT.split(text):
        if part == '\\n':
            out.append(0x0A)
        elif part == '\\r':
            out.append(0x0D)
        elif part.startswith('{x'):
            out.append(int(part[2:4], 16))
        elif part.startswith('%'):
            out += part.encode('ascii')
        elif part:
            ascii_bytes(part)
            out += vwf.compress(part)
    return bytes(out)


def fit_lines(en, jp):
    """A multi-line system string with every line padded with spaces to the byte length of the Japanese
    line, or None when it has a different number of lines or a line is longer than its Japanese line.
    Menus and lists are walked by byte count (a window shows N rows = N * row bytes, a scroll step is
    one row of bytes): rows of a different length pull the following rows into the window (the VS
    menu drew Tag Match, Delete Wrestler ... all over its third row)."""
    en_l, jp_l = re.split(r'(\\n|\\r)', en), re.split(r'(\\n|\\r)', jp)
    if len(en_l) != len(jp_l) or len(jp_l) < 3:
        return None
    out = bytearray()
    for e, j in zip(en_l, jp_l):
        if e in ('\\n', '\\r'):
            out.append(0x0A if e == '\\n' else 0x0D)
            continue
        room = len(systext.to_bytes(j))
        d = encode_fit(e, room)
        if len(d) > room:
            return None
        out += d + b' ' * (room - len(d))
    return bytes(out)


def line_widths(text):
    """[pixels] per line of a system string (%3d = 3 digits, %s = a name)."""
    res = []
    for ln in re.split(r'\\n|\\r', text):
        px = 0
        for part in CODE_SPLIT.split(ln):
            m = re.match(r'%-?(\d*)d', part)
            if m:
                px += 5 * int(m.group(1) or 1)
            elif part.startswith('%s'):
                px += 36                       # a stat or item name, usually short
            elif part.startswith('{x') or not part:
                continue
            else:
                px += sum(vwf.adv(c) for c in part.replace('…', '...'))
        res.append(px)
    return res


def jp_line_room(jp):
    """[pixels] per line: 12 per Japanese character of the line."""
    return [12 * (len(systext.to_bytes(ln)) // 2) for ln in re.split(r'\\n|\\r', jp)]


def system_rows():
    for name in ('system.csv', 'moves.csv'):
        p = paths.TEXT / name
        if not p.exists():
            continue
        with open(p, encoding='utf-8', newline='') as f:
            lines = [ln for ln in f if not ln.startswith('#')]
        for r in csv.DictReader(lines):
            yield name, r


def system_step(path, files):
    rom = files.get(ROM)
    n, problems = 0, []
    # fixed records: a section whose rows all have one size, some filled with full-width spaces (signs, clubs):
    # every row of it is padded, also the ones the Japanese fills exactly (Libra after Scorpio kept 'io')
    sizes, padded = {}, set()
    for name, r in system_rows():
        sizes.setdefault((name, r['section']), set()).add(r['max_bytes'])
        if r['japanese'].endswith('　'):
            padded.add((name, r['section']))
    fixed = {k for k in padded if len(sizes[k]) == 1}
    for name, r in system_rows():
        en = r['english'].strip()
        if not en or 'keep:' in (r['notes'] or ''):
            continue
        off, maxb = int(r['offset'], 16), int(r['max_bytes'])
        try:
            data = encode_fit(r['english'].rstrip(), maxb)
        except ValueError as e:
            raise SystemExit(f'{name} {r["offset"]}: {e}')
        if len(data) > maxb:
            problems.append(f'{name} {r["offset"]}: {en!r} takes {len(data)} bytes, room is {maxb} ({r["japanese"]!r})')
            continue
        if bytes(rom[off:off + maxb]) != systext.to_bytes(r['japanese']):
            raise SystemExit(f'{name} {r["offset"]}: the ROM does not hold the Japanese any more')
        fill = b' ' if '# pad:' in (r['notes'] or '') else b'\x00'      # packed strings the game walks by length: spaces keep the length
        if r['japanese'].endswith('　') or (name, r['section']) in fixed:
            # a record the Japanese fills with full-width spaces: list rows are redrawn over each other on
            # scroll, so the English keeps the full width (tools/asm/vwf.asm draws trailing spaces as cells)
            fill = b' '
        lines = fit_lines(r['english'].rstrip(), r['japanese']) if name == 'system.csv' else None
        if lines is not None and len(lines) <= maxb:
            data, fill = lines, b' '
        rom[off:off + maxb] = data + fill * (maxb - len(data))
        n += 1
    if problems:
        raise SystemExit('\n'.join(problems) + f'\n{len(problems)} strings do not fit')
    files.put(ROM, rom)
    print(f'system text: {n} strings in place')


# ------------------------------------------------------------------ renderer

def vwf_step(path, files):
    rom = files.get(ROM)
    expand(rom)
    vwf.apply(rom)
    files.put(ROM, rom)
    print('renderer: variable-width hook, letter table')


# ------------------------------------------------------------------ lint hooks

def glyph_problems(text):
    plain = re.sub(r'\{[^{}]*\}|\\[nr]|%[-0-9.]*[sdx]', '', text.replace('\n', ''))
    return sorted({c for c in plain.replace('…', '...') if c not in enfont._ART})


def lint_check(e):
    """lint hook: [(severity, kind, message)]; widths in pixels."""
    out = []
    en = e.english
    if 'keep:' in (e.notes or ''):
        return out
    bad = glyph_problems(en)
    if bad:
        return [('error', 'chars', f'no letter shape for {bad}')]
    if e.file.parent.name == 'script':
        text = ' '.join(ln.strip() for ln in en.split('\n') if ln.strip())
        try:
            wrap(text.replace('{p}', '{n}'))
        except ValueError as ex:
            out.append(('error', 'room', str(ex)))
        return out
    try:
        if len(encode_fit(en.rstrip(), len(systext.to_bytes(e.source)))) > len(systext.to_bytes(e.source)):
            out.append(('error', 'bytes', f'does not fit its {len(systext.to_bytes(e.source))} bytes even with tokens'))
    except ValueError:
        pass
    jp_room = jp_line_room(e.source.replace('\n', ''))
    jp_lines = re.split(r'\\n|\\r', e.source.replace('\n', ''))
    widths = line_widths(en)
    for i, w in enumerate(widths):
        room = jp_room[i] if i < len(jp_room) else (jp_room[-1] if jp_room else 0)
        if '# layout:' in (e.notes or '') or len(widths) != len(jp_room):
            room = max(jp_room) if jp_room else room
        if i < len(jp_lines) and '%' in jp_lines[i]:
            continue                       # a line with inserted text: the window is wider than the Japanese
        if w > room:
            out.append(('error', 'room', f'line {i + 1}: {w} px, room for {room}: {en!r}'))
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ['width']:
        print(line_px(argv[1]))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
