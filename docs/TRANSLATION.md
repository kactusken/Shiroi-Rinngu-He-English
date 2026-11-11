# Translation

## Where the text is

| File | Holds | Checked by |
|---|---|---|
| `translation/script/sNNN.txt` | story dialogue, one file per scene (319), 768 messages | `tools/lint.py` |
| `translation/text/system.csv` | menus, messages, names, stats, places, clubs, help, ending text (in place) | `tools/lint.py` |
| `translation/text/moves.csv` | wrestling move names (in place) | `tools/lint.py` |
| `translation/text/pairs.lst` | one-byte letter-run tokens for tight system strings (`tools/vwf.py choose`) | build |
| `translation/glossary.csv` | names and terms | lint warnings |
| `translation/graphics.csv` | images with text (none catalogued yet) | `tools/check.py` |

## File formats
Story blocks: `@ NNN.MM spk=.. face=..`, `JP` lines, `EN` lines (joined with a space and laid out by the
build: 16 cells x 4 lines, page breaks added automatically). CSV rows: `offset,max_bytes,section,
japanese,english,notes`; the English goes back in place and may not take more cells than the Japanese
had characters. `# keep:` in the notes = left Japanese (credits, name-entry keyboards).

Control codes: `{p}` page wait (0x07), `{name}` the heroine's name (0x06), `{n}` forced line break,
`\n` `\r` line breaks in system strings, `%s %2d %3d` inserted by the game, `{xNN}` raw bytes.

## How English is drawn
A variable-width renderer (tools/asm/vwf.asm) draws plain ASCII text at pixel positions with a small proportional
pixel font (`tools/enfont.py`). Story windows are 190 px per line, 4 lines per page, laid out by the build.
System strings are written in place: at most the Japanese string's bytes (English is one byte per letter, two per
Japanese character) and at most 12 px per Japanese character per line; a few overflowing strings use one-byte
letter-run tokens automatically. Lint checks both.

## Style guide (provisional - decided by the lead for the first test build)
- Western name order (Yuka Shimamura), Hepburn without macrons; surname-only forms kept as the Japanese has them.
- Honorifics dropped; 社長 = "President" ("President Onita"); 組長 (Fujiwara, yakuza undertone) = "Boss" (owner, 2026-11-11).
- Quotes: double quotes; ellipsis `...`; `!` `?`; no curly quotes or long dashes (no glyphs).
- Menus and labels in Title Case; dialogue in sentence case; wrestling terms in their usual English.
- Heroine: `{name}` with no honorific.

## Glossary
`translation/glossary.csv`; readings of invented names are guesses (see QUESTIONS.md).

## Decisions
| Decision | Who / why |
|---|---|
| True variable-width renderer hooked into the message loop; system text in place; scenes relocated to a 2 MB ROM | lead, 2026-11-09, after the owner found the first (token) approach too gappy |
| Staff credits (the ending staff roll) and the name-entry keyboards stay Japanese; the 5 opening title cards (role labels + names) are translated, names stay Japanese | owner asked for credits to stay; the game already has a Latin tab |
| ニールキック = Neil Kick (the puroresu name of the jumping scissor kick); 正規軍 = "regular army", 〜軍 = "army" (how Japanese wrestling factions are named); ending s192: the heroine suspects Kandori lost on purpose, then rejects it; ring announcements keep their varied wording (may differ by promotion) | owner, 2026-11-11 |
| メルブレ dropped (s025: "I'm Takenaka, from LLPW management"); アルメテット路線 = "the Ultimate route" (LLPW's real 1995 L-1 shoot tournament); 華激 = "Glam-Extreme" (pun on FMW's 過激 "extreme") | owner, 2026-11-11 |
| Wrestler types capitalised in dialogue (Babyface, Heel, Strong, Entertainment, Power); 脇固め = armbar; 特撮出演 = Hero Show; "TR" (top rope) in move names OK | owner, 2026-11-11 |
| Stats: 体力 = HP, 筋力 = Strength (Str in short labels), 柔軟性 = Flex; 3禁 joke (s012) rendered as "no dating ban" | owner, 2026-11-11 |
| Names, boss/chief, move-name abbreviations | lead, provisional - QUESTIONS.md |

## What stays untranslated
Staff credits (rows `# keep:`), name-entry kana keyboards, the title logo pictures.
