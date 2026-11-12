#!/usr/bin/env python3
"""The story script: 319 scene blocks of dialogue, read from the ROM, dumped to translation/script/,
and written back (relocated to the expanded ROM) with English.

  gamescript.py dump       write translation/script/sNNN.txt (keeps English and hand comments)
  gamescript.py check      parse the original, re-encode it, compare byte for byte
  gamescript.py show N     print scene N

Format (from the code and the ROM, verified in game for the intro):
  - a table of 319 four-byte entries at file 0xD8000 (CPU 1B:8000): 24-bit pointer + 0, one per
    scene, in ROM order; every scene sits behind a 0xFF marker byte in banks 1B-1C (0xD9000-0xE76xx)
  - a scene: id byte, group byte, then messages: speaker byte, face byte, Shift-JIS text, 0x00
    (the first message of the first scene: 00 00 1C 02 text ...). 0xFF follows the last message.
  - in the text: 0x0A new line, 0x07 wait for a button ({p}; the text then scrolls on, the window is not cleared), 0x06 the
    heroine's name ({name}); everything else is Shift-JIS pairs. The loader (bank 05) copies the
    message to 7F:0000; the window is 16 cells x 4 lines (7E:6CCD, 6CCE) and wraps by itself.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blocks  # noqa: E402
import paths  # noqa: E402

TABLE = 0xD8000
COUNT = 319
END = 0xE7700            # past the last scene (free 0xFF after)
CODES = {0x0A: '\n', 0x07: '{p}', 0x06: '{name}'}
CODE_BYTES = {v: k for k, v in CODES.items()}


def ptr_off(rom, i):
    return (rom[i + 2] & 0x7F) * 0x8000 + ((rom[i + 1] << 8 | rom[i]) & 0x7FFF)


class Message:
    def __init__(self, spk, face, text):
        self.spk, self.face, self.text = spk, face, bytes(text)


class Scene:
    def __init__(self, index, off, ident, group, msgs):
        self.index, self.off, self.id, self.group, self.msgs = index, off, ident, group, msgs


def is_lead(b):
    return 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEF


def read_scenes(rom):
    offs = [ptr_off(rom, TABLE + 4 * k) for k in range(COUNT)]
    ends = offs[1:] + [END]
    scenes = []
    for k, (s, e) in enumerate(zip(offs, ends)):
        while e > s and rom[e - 1] == 0xFF:
            e -= 1
        msgs, i = [], s + 2
        while i < e:
            spk, face, j = rom[i], rom[i + 1], i + 2
            while j < e and rom[j] != 0:
                j += 2 if is_lead(rom[j]) else 1
            msgs.append(Message(spk, face, rom[i + 2:j]))
            i = j + 1
        while len(msgs) > 1 and not msgs[-1].text:      # padding after the last real message
            msgs.pop()
        scenes.append(Scene(k, s, rom[s], rom[s + 1], msgs))
    return scenes


def jp_text(b):
    """Message bytes -> display string with {p} {name} \\n and {xNN} for other control bytes."""
    out, i = [], 0
    while i < len(b):
        c = b[i]
        if is_lead(c):
            out.append(bytes(b[i:i + 2]).decode('cp932'))
            i += 2
        elif c in CODES:
            out.append(CODES[c])
            i += 1
        elif 0x20 <= c < 0x7F:
            out.append(chr(c))
            i += 1
        else:
            out.append('{x%02X}' % c)
            i += 1
    return ''.join(out)


def jp_bytes(s):
    out, i = bytearray(), 0
    while i < len(s):
        if s[i] == '{':
            j = s.index('}', i)
            code = s[i:j + 1]
            out.append(CODE_BYTES[code] if code in CODE_BYTES else int(code[2:-1], 16))
            i = j + 1
        elif s[i] == '\n':
            out.append(0x0A)
            i += 1
        elif ord(s[i]) < 0x80:
            out.append(ord(s[i]))
            i += 1
        else:
            out += s[i].encode('cp932')
            i += 1
    return bytes(out)


def scene_bytes(scene, text_of):
    """The scene's bytes as stored: FF id group (spk face text 00)... ; text_of(msg) gives the message bytes."""
    out = bytearray([0xFF, scene.id, scene.group])
    for m in scene.msgs:
        out += bytes([m.spk, m.face]) + text_of(scene, m) + b'\x00'
    return bytes(out)


def block_id(scene, n):
    return f'{scene.index:03d}.{n:02d}'


HEADER = [
    '# Story dialogue: one block per message window; one file per scene.',
    '# JP is the original. Write the English as EN lines: they are joined with a space and laid out by',
    '# the build (the window is 16 cells wide, 4 lines; see docs/TRANSLATION.md). Codes:',
    '#   {p}      wait for a button (a beat; the build adds the other waits, ending screens at sentence ends)',
    '#   {name}   the heroine\'s name (typed by the player), up to 6 letters',
    '#   {n}      force a new line (rare)',
    '# `spk` is the speaker id (also picks the face picture); `face` the expression. Not for editing.',
]


def speaker_names(rom):
    """Speaker id -> name, from the people table (46 records of 16 bytes + NUL at 0xF97FF)."""
    out = {}
    for i in range(46):
        o = 0xF97FF + 17 * i
        out[i] = rom[o:o + 16].decode('cp932').replace('\u3000', ' ').strip()
    return out


def dump(rom=None):
    rom = rom or paths.ROM.read_bytes()
    names = speaker_names(rom)
    paths.SCRIPT.mkdir(parents=True, exist_ok=True)
    for sc in read_scenes(rom):
        head = HEADER + [f'# scene {sc.index} id={sc.id:02x} group={sc.group:02x} original at {sc.off:#x}']
        items = []
        for n, m in enumerate(sc.msgs):
            text = jp_text(m.text)
            who = names.get(m.spk, '')
            items.append((block_id(sc, n), f'spk={m.spk:02x} face={m.face:02x}', text.split('\n'),
                          [f'# speaker: {who}'] if who and m.spk else []))
        blocks.merge(paths.SCRIPT / f's{sc.index:03d}.txt', head, items, quiet=True)
    print(f'{COUNT} scene files in {paths.show(paths.SCRIPT)}')


def check(rom=None):
    rom = rom or paths.ROM.read_bytes()
    bad = 0
    for sc in read_scenes(rom):
        for m in sc.msgs:
            if jp_bytes(jp_text(m.text)) != m.text:
                bad += 1
                print('roundtrip fails', sc.index, m.text[:20].hex())
    # whole-scene bytes against the ROM
    for sc in read_scenes(rom):
        data = scene_bytes(sc, lambda s, m: m.text)
        if bytes(rom[sc.off:sc.off + len(data) - 1]) != data[1:]:
            bad += 1
            print('scene bytes differ', sc.index)
    print('ok' if not bad else f'{bad} problems')
    return not bad


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ['dump']:
        dump()
    elif argv[:1] == ['check']:
        sys.exit(0 if check() else 1)
    elif argv[:1] == ['show'] and len(argv) > 1:
        rom = paths.ROM.read_bytes()
        sc = read_scenes(rom)[int(argv[1])]
        for n, m in enumerate(sc.msgs):
            print(block_id(sc, n), f'spk={m.spk:02x} face={m.face:02x}', repr(jp_text(m.text)))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
