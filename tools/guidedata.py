#!/usr/bin/env python3
"""The data blocks of the player's guide (docs/guide/index.html and story/index.html), decoded from the original ROM.

  python3 tools/guidedata.py              fill the page's data block
  python3 tools/guidedata.py --check      only check the page is up to date (exit 1 if not)
  python3 tools/guidedata.py --json OUT   write the data to OUT instead of the page
  python3 tools/guidedata.py --summary    print the tables and their row counts

Every number comes from the original ROM's tables (never retyped); every name is the English the
patch shows, from translation/text/moves.csv and system.csv (promotions: the FACTIONS table, from the story). Tables:

  moves       the move table $1D:8014 (41-byte records), names via $1D:D10D, category $1F:D2AD
  wrestlers   computer wrestlers: records $1D:EC89 (50 bytes), move lists $1D:F31D, plus their roles
              in the story matches
  common      the moves every computer wrestler can also use ($1D:EC5B)
  exercises   $1F:B382 (cost, effects), names $1F:B4CE
  partners    exercise lists $1F:AFD0, daily bonuses $1F:B12E; the cost the game really charges
  places      day-off places $1F:A053
  clubs       29 signed bytes per club at $1F:A7FD onto the stats listed at $1F:A7C3
  zodiac      $1F:A122;  blood  $1F:A18B
  story       the event scripts at $1A:8000 walked along each route with every match won
  names       Japanese names of everyone the guide names, from translation/glossary.csv
Formats and findings: docs/GAMEPLAY.md; field notes in private/work/guide/data.md.
Standard library only.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402
import snes  # noqa: E402

HEROINE = 0x0B
KANDORI = 0x0F                        # the final's opponent ($05:F790)
MOVES = range(1, 318)                 # 0 is a dummy; the table ends at 317
PART_HP = range(10, 16)               # stat ids of the six part HPs (R Arm .. Body); +6 = part Str
TECH = range(22, 38)                  # Jumping .. Rough
TYPES = range(40, 45)                 # Strong, Entertainment, Babyface, Power, Heel
HIDDEN = {5: 'hidden growth', 6: 'hidden weight'}   # labelled Ht/Wt in the ROM, never shown
# posture of a wrestler as a target (move +26 needs it, move +27 leaves it); names describe what the
# moves that need or make each value have in common (docs/GAMEPLAY.md "How a match runs")
POSTURE = {0: 'standing', 1: 'down', 2: 'bent over', 3: 'state 3', 4: 'state 4',
           5: 'in a hold', 6: 'pinnable', 7: 'state 7', 8: 'state 8'}


class Data:
    """The original ROM and the patch's English names."""

    def __init__(self):
        if not paths.ROM.is_file():
            sys.exit(f'guidedata: no original ROM at {paths.show(paths.ROM)} - put '
                     f'"{paths.ORIGINAL_NAME}" in rom/ or pass --rom PATH')
        raw = paths.ROM.read_bytes()
        if hashlib.sha1(raw).hexdigest() != paths.ORIGINAL['sha1']:
            sys.exit(f'guidedata: {paths.show(paths.ROM)} is not the original (SHA-1 differs) - '
                     'the tables must come from the unpatched ROM; pass --rom PATH')
        self.rom = snes.Rom.open(paths.ROM)
        self.d = self.rom.data
        self.sys = self._csv(paths.TEXT / 'system.csv')
        self.mv = self._csv(paths.TEXT / 'moves.csv')
        self.labels = [self.text(self.ptr(0x1FB7FC + 4 * i)) for i in range(112)]
        self.people = self.section('names of people', 46)
        self.people[HEROINE] = self.people[HEROINE] or 'Heroine'
        self.c805 = self.d[self.off(0x1FC805):self.off(0x1FC805) + 80]
        self.c855 = self.d[self.off(0x1FC855):self.off(0x1FC855) + 44]

    @staticmethod
    def _csv(path):
        if not path.is_file():
            sys.exit(f'guidedata: {paths.show(path)} is missing - run tools/systext.py dump')
        rows = {}
        with open(path, encoding='utf-8', newline='') as f:
            for r in csv.reader(f):
                if len(r) > 4 and r[0].startswith('0x'):
                    rows[int(r[0], 16)] = r
        return rows

    # --- ROM access (24-bit CPU addresses)
    def off(self, addr):
        return self.rom.to_file(addr)

    def u8(self, addr):
        return self.d[self.off(addr)]

    def u16(self, addr):
        o = self.off(addr)
        return self.d[o] | self.d[o + 1] << 8

    def ptr(self, addr):
        o = self.off(addr)
        return self.d[o] | self.d[o + 1] << 8 | self.d[o + 2] << 16

    def bytelist(self, addr, end=0xFF):
        out = []
        while self.u8(addr) != end:
            out.append(self.u8(addr))
            addr += 1
        return out

    def pairs(self, addr):
        """{byte, byte} pairs up to FF."""
        out = []
        while self.u8(addr) != 0xFF:
            out.append((self.u8(addr), self.u8(addr + 1)))
            addr += 2
        return out

    def words(self, addr, step=2):
        """u16 values (step 2) or {u16, u16} pairs (step 4) up to FFFF."""
        out = []
        while self.u16(addr) != 0xFFFF:
            out.append(self.u16(addr) if step == 2 else (self.u16(addr), self.u16(addr + 2)))
            addr += step
        return out

    # --- English names
    def text(self, addr, table=None):
        o = self.off(addr)
        for t in (table,) if table else (self.sys, self.mv):
            if o in t:
                return t[o][4].replace('\\r', '').strip()
        sys.exit(f'guidedata: no row for the string at ${addr:06X} (offset {o:#x}) in translation/text - '
                 'run tools/systext.py dump')

    def section(self, name, count):
        rows = [r for o, r in sorted(self.sys.items()) if r[2].startswith(name)]
        if len(rows) != count:
            sys.exit(f'guidedata: system.csv section "{name}" has {len(rows)} rows, expected {count}')
        return [r[4].replace('\\r', '').strip() for r in rows]

    def stat(self, i):
        """English label of stat id i (the label table $1F:B7FC)."""
        return HIDDEN.get(i) or self.labels[i]

    def code(self, c):
        """A move-table stat code -> (fighter word, readable name)."""
        w = self.c805[c]
        if w == 0xFF:
            sys.exit(f'guidedata: stat code {c} has no fighter word - the move table changed?')
        if w < 44:
            return w, self.stat(self.c855[w])
        return w, self.stat(PART_HP[w - 44]).replace(' HP', '') + ' (current HP)'

    def part(self, c):
        """A target code (current part HP) -> part name."""
        w = self.c805[c]
        return self.stat(PART_HP[w - 44]).replace(' HP', '') if 44 <= w < 50 else self.code(c)[1]

    def move_name(self, i):
        o = self.off(self.ptr(0x1DD10D + 4 * i))
        return self.mv[o][4].strip() if o in self.mv else None


# ------------------------------------------------------------------ moves
def moves(D):
    labels_cat = {c: D.stat(55 + c) for c in range(5)}   # $06:F2B8: category c counts into stat 55+c
    rows = []
    for i in MOVES:
        a = 0x1D8014 + 41 * i
        r = D.d[D.off(a):D.off(a) + 41]
        cat = D.u8(0x1FD2AD + i)
        cost = r[0x21]
        name = D.move_name(i)
        rows.append({
            'id': i,
            'name': name or '',
            'cat': labels_cat.get(cat, 'Other'),
            'base': r[0x10],
            'att': [D.code(c)[1] for c in D.bytelist(D.ptr(a + 0x11))],
            'def': [D.code(c)[1] for c in D.bytelist(D.ptr(a + 0x15))],
            'req': [[D.code(c)[1], v] for c, v in D.pairs(D.ptr(a + 0x04))],
            'power': [[D.code(c)[1], v] for c, v in D.pairs(D.ptr(a + 0x0C))],
            'targets': [D.part(c) for c in D.bytelist(D.ptr(a + 0x08))],
            'calm_self': cost & 0x7F if cost & 0x80 else 0,
            'calm_opp': 0 if cost & 0x80 else cost,
            'needs': POSTURE.get(r[0x26], str(r[0x26])),
            'leaves': POSTURE.get(r[0x27], str(r[0x27])),
            'pin': r[0x27] == 6,
            'hold': r[0x27] == 5,
            'counters': [D.move_name(v) for v in D.words(D.ptr(a + 0x19)) if v < 0xFFF0],
            'dodge': D.u16(D.ptr(a + 0x19)) == 0xFFFE,
            'miss_cost': [[D.code(c)[1], v] for c, v in D.pairs(D.ptr(a + 0x1D))],
            'positions': D.bytelist(D.ptr(a + 0x22)),
        })
    reachable = {0} | {r for r in range(9) if any(m['leaves'] == POSTURE[r] for m in rows)}
    for m in rows:
        m['learnable'] = bool(m['req'])     # $06:8984 leaves moves without requirements out
        m['never_attack'] = m['needs'] not in {POSTURE[r] for r in reachable}
    return rows


# ------------------------------------------------------------------ wrestlers
# Who belongs where, as the story places them (docs/guide/story/: Kazama's two camps at LLPW, the JWWF
# departures of January 1995, FMW's rosters). Not in the ROM; wrestlers the story never places are left out.
FACTIONS = {
    'LLPW, regular army': ['Carol Midori', 'Harley Saito', 'Miki Handa', 'Michiko Omukai', 'Keiko Aono'],
    "LLPW, Eagle's army": ['Eagle Sawai', 'Kurenai Yasha', 'Mizuki Endo', 'Noriyo Tateno'],
    'LLPW': ['Yuka Shimamura'],
    'JWWF': ['Shinobu Kandori', 'Kotori Kagono', 'Mikiko Futagami'],
    'FMW': ['Megumi Kudo', 'Combat Toyoda', 'Shark Tsuchiya', 'Crusher Maedomari', 'Kaori Nakayama', 'Yukie Nabeno',
            'Miwa Sato', 'Nurse Nakamura', 'Yukari Ishikura', 'Keiko Iwami', 'Mayumi Shimizu'],
}


def promotions(D):
    """Faction by English name (FACTIONS above)."""
    return {n: f for f, names in FACTIONS.items() for n in names}


def wrestlers(D, story):
    roles = {}
    for route, ms in story.items():
        for m in ms:
            for k, who in (('opponent', m['opp']), ('partner', [m['partner']] if m['partner'] else [])):
                for n in who:
                    roles.setdefault(n, {}).setdefault(k, set()).add(route)
    promo = promotions(D)
    rows = []
    for i in range(46):
        o = D.off(D.ptr(0x1DEC89 + 4 * i))
        r = D.d[o:o + 50]
        if not any(r[:42]):
            continue                       # the heroine and the people who never wrestle
        stat = {D.c855[w]: r[w] for w in range(42)}
        name = D.people[i]
        mv = lambda k: D.move_name(r[k] | r[k + 1] << 8)
        rows.append({
            'id': i,
            'name': name,
            'promotion': promo.get(name, ''),
            'style': D.stat(TYPES[r[0x30]]) if r[0x30] < 5 else '',
            'types': {D.stat(s): stat[s] for s in TYPES},
            'stats': {D.stat(s): stat[s] for s in (0, 1, 2, 3, 4)},
            'hp': sum(r[7:13]) // 6,
            'str': sum(r[6:12]) // 6,                     # what the loader computes ($06:801A)
            'str_parts': sum(r[13:19]) // 6,
            'parts': {D.stat(s).replace(' HP', ''): [stat[s], stat[s + 6]] for s in PART_HP},
            'tech': {D.stat(s): stat[s] for s in TECH},
            'max_calm': stat[38],
            'justice': stat[39],
            'move': mv(0x2A),
            'counter': mv(0x2C),
            'finisher': mv(0x2E),
            'moves': [[D.move_name(m), m, t] for m, t in D.words(D.ptr(0x1DF31D + 4 * i), 4)],
            'roles': {k: sorted(v) for k, v in sorted(roles.get(name, {}).items())},
        })
    return rows


def common(D):
    return [[D.move_name(m), m] for m, _ in D.words(D.ptr(0x1D8008), 4)]


# ------------------------------------------------------------------ training
def effects(D, addr):
    """{op, stat, amount} triples up to 0 -> ([[stat, value], ...], end address).
    op 2 add, 3 subtract, 1 set; bit 7 = a random amount 0..amount-1."""
    out = []
    while D.u8(addr):
        op, st, am = D.u8(addr), D.u8(addr + 1), D.u8(addr + 2)
        e = [D.stat(st), {2: am, 3: -am}.get(op & 0x7F, f'={am}')]
        if op & 0x80:
            e.append('random')
        out.append(e)
        addr += 3
    return out


def effect_lists(D, table, n):
    """n effect lists by pointer; a list running into the next one's start (no end marker) is split
    there, the rest kept as 'runs_on'."""
    starts = [D.ptr(table + 4 * k) for k in range(n)]
    out = []
    for k, a in enumerate(starts):
        own, a0 = [], a
        while D.u8(a) and not (a != a0 and a in starts):
            own.append(a)
            a += 3
        e = effects(D, a0)
        out.append((e[:len(own)], e[len(own):], starts.index(a) if a in starts and D.u8(a) else None))
    return out


def part_sums(eff, D):
    hp = {D.stat(s) for s in PART_HP}
    st = {D.stat(s + 6) for s in PART_HP}
    return (sum(v for s, v, *_ in eff if s in hp and isinstance(v, int)),
            sum(v for s, v, *_ in eff if s in st and isinstance(v, int)))


def training(D):
    names = [D.text(D.ptr(0x1FB4CE + 4 * i)) for i in range(16)]
    recs = [D.ptr(0x1FB382 + 4 * i) for i in range(16)]
    cost = [D.u8(a) for a in recs]
    ex = []
    for i in range(16):
        e = effects(D, recs[i] + 1)
        hp, st = part_sums(e, D)
        ex.append({'n': i + 1, 'name': names[i], 'cost': cost[i], 'check': e[0][0], 'effects': e,
                   'part_hp': hp, 'part_str': st})
    partners = []
    for p in range(46):
        lst = D.bytelist(D.ptr(0x1FAFD0 + 4 * p), 0)
        bonus = effects(D, D.ptr(0x1FB12E + 4 * p))
        if not lst and not bonus:
            continue
        # $04:DAD1 indexes the cost table with the 1-based exercise number: the cost of the NEXT
        # exercise is charged; Running (16) reads a pointer past the table (a RAM byte, $7E:0202)
        real = sum(cost[b] for b in lst if b < 16)
        hp = sum(ex[b - 1]['part_hp'] for b in lst)
        st = sum(ex[b - 1]['part_str'] for b in lst)
        partners.append({'id': p, 'name': D.people[p], 'cost': real, 'cost_extra': 16 in lst,
                         'cost_listed': sum(cost[b - 1] for b in lst), 'part_hp': hp, 'part_str': st,
                         'exercises': [names[b - 1] for b in lst], 'bonus': bonus})
    pnames = D.section('places to go', 14)
    places = []
    for k, (own, runs, into) in enumerate(effect_lists(D, 0x1FA053, 14)):
        row = {'name': pnames[k], 'effects': own}
        if runs:
            row['runs_on'] = {'into': pnames[into], 'effects': runs}
        places.append(row)
    cnames = D.section('school clubs', 50)
    smap = [D.u8(0x1FA7C3 + 2 * i) for i in range(29)]
    clubs = []
    for c, name in enumerate(cnames):
        eff = [[D.stat(smap[j]), b - 256 if b >= 128 else b]
               for j, b in enumerate(D.d[D.off(0x1FA7FD + 29 * c):D.off(0x1FA7FD + 29 * c) + 29]) if b]
        hp, st = part_sums(eff, D)
        parts = {D.stat(s) for s in PART_HP} | {D.stat(s + 6) for s in PART_HP}
        clubs.append({'name': name, 'part_hp': hp, 'part_str': st,
                      'other': [e for e in eff if e[0] not in parts]})
    return ex, partners, places, clubs


def creation(D):
    signs = D.section('zodiac signs', 12)
    z = effect_lists(D, 0x1FA122, 12)
    zodiac = [{'name': signs[k], 'effects': own + runs} for k, (own, runs, _) in enumerate(z)]
    blood_row = next(r for o, r in sorted(D.sys.items()) if r[2] == 'profile screen' and r[3] == 'Ａ\\nＢ\\nＯ\\nＡＢ')
    bnames = blood_row[4].split('\\n')
    blood = []
    for k in range(4):                      # +30 on hidden stat 98-101, which nothing reads
        a = D.ptr(0x1FA18B + 4 * k)
        blood.append({'name': bnames[k], 'hidden_stat': D.u8(a + 1), 'value': D.u8(a + 2), 'used': False})
    return zodiac, blood


# ------------------------------------------------------------------ story matches
ROUTES = {'carol': [0], 'kurenai': [1, 0], 'fmw': [1, 1, 1], 'fmw-michinoku': [1, 1, 0]}


def events(D):
    ev = {}
    for i in range(0x400):
        a = 0x1A8000 + 4 * i
        e = D.d[D.off(a):D.off(a) + 4]
        if e[0] & e[1] & e[2] == 0xFF:
            break
        p = D.off(e[2] << 16 | e[0] | e[1] << 8)
        eid = D.d[p] | D.d[p + 1] << 8
        p += 2
        ents = []
        while D.d[p] != 0xFF:
            ents.append(bytes(D.d[p:p + D.d[p]]))
            p += D.d[p]
        ev[eid] = ents
    return ev


def route(D, ev, choices, arenas):
    """Walk the event scripts along one route, winning every match (the rules: opcode 15 queues an
    event, 16 calls one, 13 is a choice, 30 a compare; set-commands 28/29/2A on 23 mark a match day
    (param = arena) and on 24 fill a card slot; the card is cleared after every match, $1F:FEFE)."""
    choices = list(choices)
    y, m, d = 1, 4, 0
    queue = [((1, 4, 1), 0)]
    card = [0xFF] * 4
    days, matches, state = {}, [], {'winside': 0, 'choice': 0}

    def play_until(t):
        for dd in sorted(days):
            if (y, m, dd) < t:
                ar = days.pop(dd)
                side = 0 if HEROINE in card[:2] else 1
                state['winside'] = side
                a = [i for i in card[:2] if i != 0xFF]
                b = [i for i in card[2:] if i != 0xFF]
                mine, theirs = (a, b) if side == 0 else (b, a)
                her = HEROINE in mine
                row = {'year': y, 'month': m, 'day': dd, 'arena': arenas[ar], 'heroine': her,
                       'partner': next((D.people[i] for i in mine if i != HEROINE), '') if her else '',
                       'opp': [D.people[i] for i in theirs] if her else [],
                       'result_matters': False,
                       # $05:F790: a singles match of the heroine against Kandori is the final
                       'final': her and len(mine) == 1 and theirs == [KANDORI]}
                if not her:                # a match she doesn't wrestle in: both sides
                    row['sides'] = [[D.people[i] for i in a], [D.people[i] for i in b]]
                matches.append(row)
                card[:] = [0xFF] * 4

    def run(eid):
        skip = False
        for x in ev[eid]:
            if skip:
                skip = False
                continue
            op, a = x[1], x[2:]
            if op == 0x15:
                em, ed = a[0], a[1]
                queue.append(((y + (1 if (em, ed) < (m, d) else 0), em, ed), a[2] | a[3] << 8))
            elif op == 0x16:
                run(a[0] | a[1] << 8)
            elif op == 0x13:
                state['choice'] = choices.pop(0) if choices else 0
            elif op == 0x30:
                var = {0x38: state['winside'], 0x3A: state['choice']}.get(a[1])
                if var is None:
                    continue
                if a[1] == 0x38 and matches:
                    matches[-1]['result_matters'] = True
                v, c = a[2], a[0]
                skip = not {0x31: var == v, 0x36: var != v, 0x32: var > v, 0x33: var >= v,
                            0x34: var < v, 0x35: var <= v}[c]
            elif op in (0x28, 0x29, 0x2A) and a[0] == 0x23:
                days[a[1]] = a[2]
            elif op in (0x28, 0x29, 0x2A) and a[0] == 0x24:
                card[a[1]] = a[2]
            elif op == 0x28 and a[0] == 0x3A:
                state['choice'] = a[1]

    steps = 0
    while queue and steps < 3000:
        queue.sort(key=lambda q: q[0])
        (ny, nm, nd), eid = queue.pop(0)
        if (ny, nm) != (y, m):
            play_until((ny, nm, 0))
            days.clear()
        play_until((ny, nm, nd))
        y, m, d = ny, nm, nd
        run(eid)
        steps += 1
        if y > 9:
            sys.exit('guidedata: the story walk did not end (event scripts changed?)')
    play_until((y + 9, 1, 1))
    return matches


def story(D):
    arenas = D.section('arenas', 40)
    ev = events(D)
    return {r: route(D, ev, c, arenas) for r, c in ROUTES.items()}


# ------------------------------------------------------------------ names
CAST = ['Rumi Kazama', 'Atsushi Onita', 'Yoshiaki Fujiwara', 'Great Sasuke', 'Super Delfin', 'Jinsei Shinzaki',
        'Nagi Akizuki', 'Naomi Iwashita', 'Kayo Nakamura', 'Mr. Takenaka']


def names(people):
    """Japanese and English of every person the guide names (wrestlers, partners, the cast), from the glossary."""
    want = set(people) | set(CAST)
    out = []
    with open(paths.GLOSSARY, encoding='utf-8', newline='') as f:
        for r in csv.reader(f):
            if len(r) > 1 and r[1] in want and r[1] not in {o[0] for o in out}:
                out.append([r[1], r[0].replace('\u3000', ' ').strip()])
    return sorted(out, key=lambda o: o[0].split()[-1] if o[0] != 'Mr. Takenaka' else 'Takenaka')


def build():
    D = Data()
    st = story(D)
    ex, partners, places, clubs = training(D)
    zodiac, blood = creation(D)
    return {
        'game': paths.GAME,
        'postures': [POSTURE[k] for k in sorted(POSTURE)],
        'moves': moves(D),
        'common_moves': common(D),
        'wrestlers': wrestlers(D, st),
        'exercises': ex,
        'partners': partners,
        'places': places,
        'clubs': clubs,
        'zodiac': zodiac,
        'blood': blood,
        'routes': {'carol': 'Carol', 'kurenai': 'Kurenai (stay)', 'fmw': 'FMW (transfer)',
                   'fmw-michinoku': 'FMW, then Michinoku Pro'},
        'story': st,
        'names': names([w['name'] for w in wrestlers(D, st)] + [p['name'] for p in partners]),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], epilog=paths.FOLDER_HELP,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help="only check the page's data is up to date")
    ap.add_argument('--json', type=Path, metavar='OUT', help='write the data to OUT instead of the page')
    ap.add_argument('--summary', action='store_true', help='print the row count of every table')
    args = ap.parse_args(paths.configure(sys.argv[1:] if argv is None else argv))
    data = build()
    if args.summary:
        for k, v in data.items():
            n = sum(len(x) for x in v.values()) if k == 'story' else len(v) if isinstance(v, (list, dict)) else v
            print(f'{k:13} {n}')
    if args.json:
        args.json.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print(f'{paths.show(args.json)}: written')
        return
    if args.summary and not args.check:
        return
    import pagedata
    story_keys = ('game', 'routes', 'story', 'wrestlers', 'names')       # the story page needs only these
    pages = [(paths.DOCS / 'guide' / 'index.html', data),
             (paths.DOCS / 'guide' / 'story' / 'index.html', {k: data[k] for k in story_keys})]
    for page, part in pages:
        if not page.is_file():
            sys.exit(f'guidedata: {paths.show(page)} does not exist yet - make the guide page first '
                     '(the kit\'s guide/starter.html), or write the data to a file with --json OUT')
        if pagedata.write(page, part, check=args.check) and args.check:
            print(f'{paths.show(page)}: data up to date')

if __name__ == '__main__':
    main()
