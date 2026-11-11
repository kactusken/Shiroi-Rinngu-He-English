# Technical notes - Shiroi Rinngu He - Twinkle Little Star Story

**Conventions:** numbers in hex with `0x`; addresses are RAM addresses unless marked as file
offsets; `u16`/`u32` little-endian unless marked BE. Findings are marked *verified in game* or
*from the code*.

## Contents
- [Image](#image) · [Disc layout](#disc-layout) · [Executable and memory](#executable-and-memory)
- [Archives and compression](#archives-and-compression) · [Text](#text) · [Images](#images)
- [Open questions](#open-questions)

## Image
`Shiroi Rinngu He - Twinkle Little Star Story (J).smc`, 1572864 bytes, SHA-1 `efb2756402dda3a0e5e5285f6f16dd6e0b773d9a`.

## Disc layout
| | |
|---|---|
| Title | `SIROI RINNGU HE` |
| Map | LoROM (`$20`), header at `0x7fc0` |
| Size | 0x180000 bytes (12 Mbit), 48 banks of 32 KB |
| ROM | $00:8000 - $2F:FFFF |
| Cart | type `$02`, SRAM 8 KB |
| Reset | $00:8FD1 |
| Checksum | `0x916a` (fixed by tools/disc.py on every build) |

Runs of `$00`/`$FF` of 1 KB or more (free space candidates - verify nothing reads them):

| Offset | CPU | Bytes | Fill |
|---|---|---|---|
| `0x01b946` | $03:B946 | 0x416 | `$00` |
| `0x02f9e2` | $05:F9E2 | 0x61e | `$ff` |
| `0x037b0e` | $06:FB0E | 0x4f2 | `$ff` |
| `0x03fb16` | $07:FB16 | 0x4ea | `$ff` |
| `0x067bfe` | $0C:FBFE | 0x402 | `$ff` |
| `0x075824` | $0E:D824 | 0x7dc | `$00` |
| `0x0ae33e` | $15:E33E | 0x1cc2 | `$00` |
| `0x0d0608` | $1A:8608 | 0x9f8 | `$ff` |
| `0x0d45f3` | $1A:C5F3 | 0x3a0e | `$00` |
| `0x0d84fc` | $1B:84FC | 0xb04 | `$ff` |
| `0x0df8e0` | $1B:F8E0 | 0x720 | `$00` |
| `0x0e76f6` | $1C:F6F6 | 0x90a | `$00` |
| `0x113000` | $22:B000 | 0x5000 | `$ff` |

## Executable and memory

## Archives and compression

## Text
How text is drawn: does the game draw ASCII? fixed or proportional width? which glyphs exist? how
much of the visible text is images? *(answer these first)*

## Images

## Open questions
-

## Prior art
- No English translation, tools or Data Crystal / TCRF pages found by web search (2026-11-09).
  Sources checked: Wikipedia and mirrors, RAWG, Giant Bomb, LaunchBox. Release day disagrees:
  1995-12-27 (Wikipedia) vs 1995-10-27 (RAWG).

## Text engine (found 2026-11-09; verified in game unless marked from the code)
- Text is Shift-JIS pairs; the message loop (00:B2A0, from the code) converts each to JIS (00:B713) and a glyph
  number (00:BB41, table 00:BBAD), draws a 12 px cell. No half-width path. Font in ROM at file 0x8000-0x1B930:
  glyph n at 0x8000 + (n // 0x555) * 0x8000 + (n % 0x555) * 24, 12 rows of one little-endian 16-bit word,
  leftmost pixel bit 15 (tools/jisfont.py). Rows 0x21,0x23,0x24,0x25 and kanji rows 0x30-0x4F (level 1).
- English = proportional text drawn as the game's own cells (2026-11-10, replaces the pixel-pen renderer and its
  line recorder; tools/asm/vwf.asm, tools/vwf.py; *seen headless*, owner check pending). The message loop is hooked
  at 00:B2DB (JML 3F:8000). A run of English (ASCII bytes, one-byte tokens 0xA0-0xDF / 0xF0-0xFE = up to 3 letters
  from 3F:A800, and full-width Latin 82 4F-82 9A when the run also has English letters or comes from the typed name
  at 7E:7E00) is drawn from the letter table (3F:A000, 16 bytes: advance + 12 rows) into a 1 bpp line in RAM, cut
  into 12 px cells, and each cell picture is kept in a glyph cache under a virtual Shift-JIS code: bytes
  E0+(i>>7), 80+(i&7F), i = 0..511 (lead bytes E0-E3 are never drawn by the original). The loop is pointed at
  the list of codes (7F:FC80, DB=7F) and stores, draws, advances and wraps them like Japanese characters; byte 03
  after the list sends it back to the text after the run. The glyph lookup 00:BB41 is hooked (JML bb41): a
  virtual code returns bank 7F and the cached glyph, so redraws, window close/open and highlighted rows repaint
  English through the game's own path. A run that reaches the window's right edge is wrapped by the game (6CD1),
  so a line break right after it is skipped. Lists redraw a row over the row before it (scrolling), and the
  Japanese fixed records (signs, clubs, ...) are filled to full width with full-width spaces; English records are
  padded with spaces (tools/gametext.py) and a run ending in spaces before a control byte takes at least bytes / 2
  cells, so the old row is covered (*seen headless*, 2026-11-10). Every row of a fixed-record section is padded.
- Formatter (*from the code*): 00:B8A0 expands %s / %Nd / %0Nd from a template into 7F:0000 and prints it; %d
  writes full-width digits with leading full-width spaces. It walked the template and %s strings two bytes at a time,
  so English % at odd bytes was missed and odd-length names lost their end mark; the build steps one byte for
  English (vwf.py FMT_AT 00:B9C1, FMTS_AT 00:B90B). In English text two or more spaces are a column stop at cell
  (bytes from the run start) / 2, and a number after a stop is right-aligned in the cells the Japanese gave it;
  elsewhere a full-width space before a digit takes no room. Status templates keep the Japanese byte layout.
- Glyph lookup / draw (*from the code*): 00:BB41 returns A = glyph bank (1-3), X = address; 00:BC0F (one caller,
  B393) draws from that 24-bit pointer, attr bit 0 = cell parity, bits 1-7 = draw mode. 00:B713 (Shift-JIS to
  JIS) decrements the stacked trail byte in place when it is 0x80 or more, so BB41 sees trail - 1 (*seen headless*).
  Every text-layer string goes through 00:B287 (40 callers in banks 00, 04-07); B65F / B53F scroll pixels only.
- Window manager (*from the code*, details in the private notes): records of 0x12 bytes at 7E:76E9 (x, y, w, h,
  frame offsets, z at +C (FF hidden), char buffer offset at +E); each window keeps its characters in a char pool on
  the bank-7F heap (handle address at 7E:76E5: {addr, bank, size}); D69B stores a drawn character there (only
  when 7E:6CCF is set). Opening/closing a window copies the visible windows' buffers into the screen grid
  7E:74AF-76B6 (20 x 13 words), clears the text bitmap (00:B245) and replays the grid through the message loop.
  The cache is collected when fewer than 64 entries are free: entries whose code is in the grid or the char pool stay.
- RAM used by the renderer: 7F:C000-EFFF cache (512 x 24 B), F000/F400 hash heads/links, F800-FC7F line,
  FC80 code list, FD10-FF0F used flags, FF10-FF3F variables, FF80 cell, FFE0-FFEF message wait. Bank 7F
  C000-FFFF had no writes from the original game in about 22,000 frames (title, versus menus, profile form, name
  keyboard, story, first days of the main game; write trace on the original). Matches and the ending not traced yet.
- The text buffer is the game's own: 2bpp strips 8 px x 16 rows (32 bytes, (plane0, plane1) per row) at 7E:39C1,
  30 per text row, 13 rows; plane1 = plane0 shifted right 1 px (drop shadow).
- Message length (00:B86D, used by the script engine at 05:960E to find the NEXT message, and for the name): counts
  every byte except 0A 0D 07 06 as half of a 2-byte Shift-JIS character, so one-byte English letters made the engine
  step twice as far and land inside later messages (the intro conversation played twice, messages skipped). The build
  patches it (tools/vwf.py LEN_AT): bytes below 0x80 count 1. Also the end of a message skipped its final screen upload
  when the game's per-letter wait is on (00:B437 patched, FLUSH_AT). *verified in game (emulator)*.
- Story script: 319 scenes via a table of 4-byte pointers at 0xD8000, scenes 0xD9000-0xE76xx
  ([FF] id group, then spk face text 00 per message); the bank-05 script engine copies a message to 7F:0000;
  window 16 cells x 4 rows (7E:6CCB..6CCE). 0x0A newline, 0x07 page wait, 0x06 heroine name. Speaker ids index
  the people table at 0xF97FF (16 bytes + NUL). The build moves the scenes to 0x180000 (ROM expanded to 2 MB)
  and repoints the table: verified in game for the intro scene.
- System text (menus, names, stats, places, moves) is NUL-terminated Shift-JIS in 0xD3412, 0xEB303-0xEEC4A,
  0xF8000-0xFCD00, written back in place (tools/systext.py, translation/text/system.csv and moves.csv).
- Name entry already has a Latin tab (A) with full-width letters; the keyboard page keeps one letter per cell, the typed
  name is drawn proportionally (owner decision 2026-11-10).
- Name keyboard: typing (05:C7A9) goes to column 4, draws the whole name (7E:7E01, length 7E:7837, at most 8) and then
  "＿". Delete (05:C8C7) only drew "＿" and a blank at column length+4, which left the deleted letter of a proportional
  name on screen; the build calls namedel there (tools/vwf.py NAMEDEL_AT), which redraws the name from column 4 first.
  *verified in game*.
- The opening title cards (labels F801A..F807A) are packed strings the game walks by length: English labels are padded with SPACES to the Japanese byte length (notes `# pad: spaces`), not NULs, or the next card reads the wrong string.
