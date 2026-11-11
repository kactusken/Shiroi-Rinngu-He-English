#!/usr/bin/env python3
"""Recursive-descent 65816 disassembly: follow the code from its entry points. Standard library only.

  walk65816.py walk ROM OUT [--entry ADDR[=FLAGS]]... [--switch ADDR]... [--banks C0-CF]
      write OUT/<bank>.lst (one instruction a line, `;<-` = who jumps here, `; ---- gap` = bytes
      nothing reached), OUT/tables.txt (jump tables found) and OUT/conflicts.txt
  walk65816.py flags OUT [--ram 0000-1FFF]...
      RAM read but never written, written but never read (cut features, leftover debug switches)
  walk65816.py pad OUT [RANGE]...
      every button mask tested against the controller registers ($4218-$421F) and the game's own
      copies of them (RANGE, e.g. 0846-086E): input codes, hidden menus

Start from the reset, NMI and IRQ vectors, each with 8-bit M and X. --entry adds a start, with
FLAGS 8, 16 or m8x16: routines nothing reaches (from `; ---- gap` code or a Mesen trace), or the
vectors again with their real flags. `dis65816.py` shows one spot; this maps a whole game.

What it follows: JMP/JML/JSR/JSL/branches; REP/SEP and PHP/PLP; `JMP (table,X)` and `JSR (table,X)`;
`LDA table,X` ... `JMP ($nn)`, a table of 16-bit targets; --switch ADDR, a routine whose callers put
a 16-bit word table right after the JSR (the table is walked and the call doesn't come back). A walk
prints the routines that look like one; add them and walk again, as each can open up more code.
A call is assumed to return with the flags it was made with, and a routine to start with its
caller's. Where two paths reach an address with different flags the first wins and conflicts.txt
names it: a nonsense listing after such an address means --entry with the right flags. Tables end
at a word below $0400 or off the ROM, at code already walked, or at the lowest target; the table
guess takes the code's own bank (a game can set another data bank), so read tables.txt critically.

flags reads absolute and long operands with the direct page at 0 and low RAM in reach, so give
--ram only for what the game addresses that way; arrays are allowed for by ignoring a neighbour.
Everything is *from the code*: unreached code isn't in the listings, so check a find in the ROM.
"""
import argparse
import collections
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dis65816  # noqa: E402
import snes  # noqa: E402

MAX_TABLE = 300
LINE = re.compile(r'([0-9A-F]{2}):([0-9A-F]{4}) .. (\S+)(?: (.*?))?(?: ;<-.*)?$')
OPERAND = re.compile(r'\$([0-9A-F]{2,6})(?:,[XY])?$')
WRITES = {'STA', 'STZ', 'STX', 'STY', 'INC', 'DEC', 'ASL', 'LSR', 'ROL', 'ROR', 'TSB', 'TRB'}
READS = {'LDA', 'LDX', 'LDY', 'CMP', 'CPX', 'CPY', 'AND', 'ORA', 'EOR', 'BIT', 'ADC', 'SBC', 'INC', 'DEC', 'TSB', 'TRB'}
PAD_OPS = {'LDA', 'BIT', 'AND', 'ORA', 'CMP', 'EOR'}


def mapped(rom, addr):
    """File offset of CPU address `addr`, or None when it isn't ROM."""
    try:
        return rom.to_file(addr & 0xffffff)
    except ValueError:
        return None


def read_table(rom, at, bank, seen):
    """The 16-bit targets of a table at CPU address `at`, each in `bank` (bank << 16)."""
    out, low = [], None
    for i in range(MAX_TABLE):
        p = at + i * 2
        o = mapped(rom, p)
        if o is None or o + 2 > len(rom.data) or (i and o in seen) or (low is not None and p & 0xffff >= low):
            break
        w = int.from_bytes(rom.data[o:o + 2], 'little')
        if w < 0x400 or mapped(rom, bank | w) is None:
            break
        out.append(bank | w)
        if w > at & 0xffff:
            low = w if low is None else min(low, w)
    return out


def walk(rom, entries, switches=(), banks=None):
    """entries [(addr, m8, x8)]. {'seen': {offset: (length, text, m8, x8)}, 'xref': {offset: {cpu
    address}}, 'tables': {cpu address: (table address, [targets])}, 'conflicts': {offset: (m8, x8)}}"""
    seen, xref, tables, conflicts = {}, collections.defaultdict(set), {}, {}
    stops = {mapped(rom, s) for s in switches}
    work = [(a, m, x, ()) for a, m, x in entries]

    def jump(target, source, m, x, stack):
        o = mapped(rom, target)
        if o is not None:
            xref[o].add(source)
            work.append((target, m, x, stack))

    while work:
        a, m, x, stack = work.pop()
        table = None                                        # from LDA table,X, for JMP ($nn)
        while True:
            off = mapped(rom, a)
            if off is None or (banks and not banks[0] <= rom.to_cpu(off) >> 16 <= banks[1]):
                break
            if off in seen:
                if seen[off][2:] != (m, x):
                    conflicts.setdefault(off, (m, x))
                break
            code = bytes(rom.data[off:off + 4]).ljust(4, b'\0')
            st = dis65816.State(m, x)
            n, text, target = dis65816.decode(code, a, st)
            seen[off] = (n, text, m, x)
            mn, m, x = text.split()[0], st.m8, st.x8
            if mn == 'PHP':
                stack += ((m, x),)
            elif mn == 'PLP' and stack:
                (m, x), stack = stack[-1], stack[:-1]
            if target is not None:
                jump(target, a, m, x, stack)
            bank = a & 0xff0000
            if code[0] in (0x7c, 0xfc):                     # JMP/JSR (table,X)
                at = bank | int.from_bytes(code[1:3], 'little')
                tables[a] = (at, read_table(rom, at, bank, seen))
                for t in tables[a][1]:
                    jump(t, a, m, x, stack)
            if mn in ('JSR', 'JSL') and target is not None and mapped(rom, target) in stops:
                at = bank | (a + n) & 0xffff
                tables[a] = (at, read_table(rom, at, bank, seen))
                for t in tables[a][1]:
                    jump(t, a, m, x, stack)
                break
            if mn == 'JMP' and '($' in text and table is not None:
                tables[a] = (table, read_table(rom, table, bank, seen))
                for t in tables[a][1]:
                    jump(t, a, m, x, stack)
            hit = re.fullmatch(r'LDA \$([0-9A-F]{4}|[0-9A-F]{6}),X', text)
            if hit:
                v = int(hit[1], 16)
                table = v if v > 0xffff else bank | v
                table = table if v >= 0x2000 and mapped(rom, table) is not None else None     # low RAM isn't a table
            elif mn != 'STA':
                table = None
            if mn in ('RTS', 'RTL', 'RTI', 'BRK', 'STP', 'JML', 'JMP', 'BRA', 'BRL'):
                break
            a = bank | (a + n) & 0xffff
    return {'seen': seen, 'xref': xref, 'tables': tables, 'conflicts': conflicts}


def possible_switches(rom, result):
    """CPU addresses of called routines that pull their return address at once: --switch candidates."""
    seen, out = result['seen'], []
    for off in result['xref']:
        first = seen.get(off)
        second = seen.get(off + first[0]) if first else None
        pulls = ('PLA', 'PLX', 'PLY')
        if first and (first[1] in pulls or (first[1][:3] in ('REP', 'SEP') and second and second[1] in pulls)):
            out.append(rom.to_cpu(off))
    return sorted(out)


def vectors(rom):
    """The cartridge's reset, native NMI and native IRQ entries."""
    out = []
    for at in (0xfffc, 0xffea, 0xffee):
        v = int.from_bytes(rom.read_cpu(at, 2), 'little')
        if v >= 0x8000:
            out.append((v, True, True))
    return out


def listing(rom, result):
    """{bank: [lines]} in the format flags() and pad() read."""
    seen, xref = result['seen'], result['xref']
    out = collections.defaultdict(list)
    prev = {}
    for off in sorted(seen, key=rom.to_cpu):
        n, text, m, x = seen[off]
        cpu = rom.to_cpu(off)
        bank = cpu >> 16
        if prev.get(bank) not in (None, off):
            out[bank].append(f'; ---- gap {rom.to_cpu(prev[bank]) & 0xffff:04X}-{cpu & 0xffff:04X}')
        who = ''
        if off in xref:
            who = ' ;<-' + ','.join(f'{q & 0xffff:04X}' for q in sorted(xref[off])[:6])
        out[bank].append(f'{bank:02X}:{cpu & 0xffff:04X} {"m" if m else "M"}{"x" if x else "X"} {text}{who}')
        prev[bank] = off + n
    return out


def write(rom, result, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for bank, lines in listing(rom, result).items():
        (out / f'{bank:02X}.lst').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    (out / 'tables.txt').write_text(''.join(
        f'{snes.fmt(k)} table {snes.fmt(at)} n={len(t)}: {" ".join(f"{q & 0xffff:04X}" for q in t)}\n'
        for k, (at, t) in sorted(result['tables'].items())), encoding='utf-8', newline='\n')
    (out / 'conflicts.txt').write_text(''.join(
        f'{snes.fmt(rom.to_cpu(off))} walked as m{8 if result["seen"][off][2] else 16}x{8 if result["seen"][off][3] else 16}, '
        f'also reached as m{8 if m else 16}x{8 if x else 16}\n'
        for off, (m, x) in sorted(result['conflicts'].items())), encoding='utf-8', newline='\n')


def lines_of(out):
    files = sorted(Path(out).glob('*.lst'))
    if not files:
        raise SystemExit(f'{out}: no .lst files - run `walk65816.py walk ROM {out}` first')
    return [ln for f in files for ln in f.read_text(encoding='utf-8').splitlines()]


def parse_ranges(given):
    ranges = []
    for s in given:
        m = re.fullmatch(r'([0-9A-Fa-f]{1,4})-([0-9A-Fa-f]{1,4})', s)
        if not m:
            raise SystemExit(f'{s}: give a RAM range like 0846-086E')
        ranges.append((int(m[1], 16), int(m[2], 16)))
    return ranges


def ram_operand(operand):
    """The 16-bit RAM address of a direct, absolute or long operand, or None."""
    m = OPERAND.fullmatch(operand or '')
    if not m or len(m[1]) % 2:
        return None
    if len(m[1]) == 6 and m[1][:2] not in ('00', '7E'):
        return None
    return int(m[1][-4:], 16)


def flags(lines, ranges=((0, 0x1fff),)):
    """([(address, [readers])] read and never written, [(address, [writers])] written and never read)."""
    reads, writes = collections.defaultdict(list), collections.defaultdict(list)
    for ln in lines:
        m = LINE.match(ln)
        v = ram_operand(m[4]) if m else None
        if v is None or not any(a <= v <= b for a, b in ranges):
            continue
        where = f'{m[1]}:{m[2]}'
        if m[3] in WRITES:
            writes[v].append(where)
        if m[3] in READS:
            reads[v].append(where)
    never_set = [(v, reads[v]) for v in sorted(reads)
                 if v not in writes and not any(v - k in writes for k in range(1, 16))]
    never_used = [(v, writes[v]) for v in sorted(writes)
                  if v not in reads and not any(v - k in reads for k in range(1, 8))]
    return never_set, never_used


def pad(lines, ranges=()):
    """[(where, address, operation, mask)]: each read of a pad word with the mask tested next to it."""
    ranges = [(0x4218, 0x421f), *ranges]
    out = []
    for i, ln in enumerate(lines):
        m = LINE.match(ln)
        v = ram_operand(m[4]) if m and m[3] in PAD_OPS else None
        if v is None or not any(a <= v <= b for a, b in ranges):
            continue
        mask = ''
        for near in lines[i + 1:i + 4]:
            hit = re.search(r' (AND|BIT|CMP) #\$([0-9A-F]+)', near)
            if hit:
                mask = f'{hit[1]} {hit[2]}'
                break
        if not mask and i and m[3] == 'BIT':                # LDA #mask / BIT pad
            hit = re.search(r' LDA #\$([0-9A-F]+)', lines[i - 1])
            mask = f'LDA {hit[1]}' if hit else ''
        out.append((f'{m[1]}:{m[2]}', v, m[3], mask))
    return out


def parse_entry(s):
    addr, _, fl = s.partition('=')
    m = re.fullmatch(r'(?:m(8|16)x(8|16)|(8|16))', fl or '8')
    if not m:
        raise SystemExit(f'{s}: flags are 8, 16 or m8x16')
    return snes.parse_addr(addr), (m[1] or m[3]) == '8', (m[2] or m[3]) == '8'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split('\n', 2)[2])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('walk')
    p.add_argument('rom')
    p.add_argument('out')
    p.add_argument('--entry', action='append', default=[], help='ADDR or ADDR=FLAGS (8, 16, m8x16)')
    p.add_argument('--switch', action='append', default=[], help='a routine with a word table after each call')
    p.add_argument('--banks', help='only these banks, e.g. C0-CF')
    p = sub.add_parser('flags')
    p.add_argument('out')
    p.add_argument('--ram', action='append', default=[], help='a range, e.g. 7000-7FFF (default 0000-1FFF)')
    p = sub.add_parser('pad')
    p.add_argument('out')
    p.add_argument('ranges', nargs='*', help="the game's copies of the pad words, e.g. 0846-086E")
    a = ap.parse_args(argv)
    if a.cmd == 'walk':
        rom = snes.Rom.open(a.rom)
        banks = None
        if a.banks:
            banks = tuple(int(b, 16) for b in a.banks.split('-'))
        r = walk(rom, vectors(rom) + [parse_entry(e) for e in a.entry], [snes.parse_addr(s) for s in a.switch], banks)
        write(rom, r, a.out)
        print(f'{len(r["seen"])} instructions, {sum(v[0] for v in r["seen"].values())} bytes, '
              f'{len(r["tables"])} tables, {len(r["conflicts"])} flag conflicts: {a.out}')
        maybe = [m for m in possible_switches(rom, r) if m not in [snes.parse_addr(s) for s in a.switch]]
        if maybe:
            print('pull their return address, so maybe --switch:', ' '.join(snes.fmt(m) for m in maybe))
    elif a.cmd == 'flags':
        unset, unused = flags(lines_of(a.out), parse_ranges(a.ram) or [(0, 0x1fff)])
        text = ['read, never written:'] + [f'{v:04X} {" ".join(w[:6])}' for v, w in unset]
        text += ['written, never read:'] + [f'{v:04X} {" ".join(w[:6])}' for v, w in unused]
        (Path(a.out) / 'flags.txt').write_text('\n'.join(text) + '\n', encoding='utf-8', newline='\n')
        print(f'{len(unset)} read but never written, {len(unused)} written but never read: {a.out}/flags.txt')
    else:
        found = pad(lines_of(a.out), parse_ranges(a.ranges))
        counts = collections.Counter((v, mask) for _, v, _, mask in found)
        text = [f'{v:04X} {mask or "?"}: {n}' for (v, mask), n in sorted(counts.items())]
        text += ['', *(f'{w} {v:04X} {op} {mask}' for w, v, op, mask in found)]
        (Path(a.out) / 'pad.txt').write_text('\n'.join(text) + '\n', encoding='utf-8', newline='\n')
        print(f'{len(found)} reads, {len(counts)} address and mask pairs: {a.out}/pad.txt')


if __name__ == '__main__':
    main()
