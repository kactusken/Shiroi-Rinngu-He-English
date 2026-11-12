# Shiroi Rinngu He - Twinkle Little Star Story — English Translation

An English translation patch for **Shiroi Rinngu He - Twinkle Little Star Story** (女子プロレスSTORY 白いリングへ, Pony Canyon / Opera House, 1995, SNES, released only in Japan).

A women's wrestling career story starring the real joshi wrestlers of 1995. You create a rookie who joins
LLPW, trains under Rumi Kazama alongside Harley Saito, Eagle Sawai, Carol Midori and Kurenai Yasha, and
spends six years working toward a Tokyo Dome main event against Shinobu Kandori. One route takes you to
FMW, where Atsushi Onita, Megumi Kudo and Combat Toyoda become your training partners.

Everything is in English: every story scene on all three routes, the menus, status and training screens,
317 move names, the wrestler and arena names, match announcements and the endings. The game had no way to
draw half-width letters, so the patch adds a variable-width text renderer and a proportional font, and moves
the script into an expanded 2 MB ROM.

**[See screenshots](docs/SCREENSHOTS.md)** of the patched game.

**[Player's guide](https://kactusken.github.io/Shiroi-Rinngu-He-English/guide/)**: how to play, every system and data table, and the [story on every route](https://kactusken.github.io/Shiroi-Rinngu-He-English/guide/story/).

> **Status: v1.0, complete.** All text is translated and the English game has been play-tested on every
> route. Please report anything that looks wrong ([how to report](#reporting-problems)).
> [CHANGELOG.md](CHANGELOG.md) lists what's in each release.

## Downloads

Get the latest zip from the [Releases](../../releases) page. It contains one patch:

| Patch | What you get |
|---|---|
| **Shiroi Rinngu He - Twinkle Little Star Story (English)** | The translation, with the game otherwise unchanged. |

## How to patch

**[Follow the step-by-step guide](docs/HOW_TO_PATCH.md).** You apply the `.bps` patch to your ROM with
[Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/) in a web browser, or with
[Flips](https://github.com/Alcaro/Flips). The patched file can have any name.

You need your own copy of the original Japanese cartridge ROM. ROMs are not provided here.

- The ROM must match: `Shiroi Rinngu He - Twinkle Little Star Story (J).smc` (No-Intro: *Shiroi Ring e - Twinkle
  Little Star (Japan)*), 1572864 bytes with no copier header, CRC32 `534824f0`,
  SHA-1 `efb2756402dda3a0e5e5285f6f16dd6e0b773d9a`.

Tested in Mesen 2.

## Notes for players

- **Names.** The real wrestlers keep their real names in Western order (Shinobu Kandori, Megumi Kudo,
  Atsushi Onita). Honorifics are dropped. Kazama is "President", Yoshiaki Fujiwara is "Boss".
- **What's still in Japanese.** The title logo, the name-entry kana keyboards (the game's own Latin
  keyboard works for an English name), the ending staff roll, and the 月/日 (month/day) and 人
  (attendance) signs drawn as graphics on a few screens.
- **Story fix.** In the original, losing to Kotori Kagono in September 1999 on the Carol route stopped the
  story for good: no final and no ending. The patch plays the game's unused loss scene there and the story
  carries on ([details](docs/PATCHES.md)).
- **Saves.** Start a new game with the patch; saves from the Japanese version haven't been tested.
- **Hidden content.** Hold Down+L at power-on for the developers' unused training animation viewer (reset
  to leave). More in [docs/HIDDEN_CONTENT.md](docs/HIDDEN_CONTENT.md).
- **Patches don't stack.** Always patch a clean copy of the original ROM.

## Reporting problems

Open an [issue](../../issues) with:

- a screenshot,
- which patch you used,
- where you were: the mode and menu, or roughly what had just happened.

Text that is cut off, overlaps, or still shows Japanese is especially helpful.

## For ROM hackers and contributors

Everything needed to rebuild the patches from the original ROM is in this repository: the
translated text, the patching code (Python 3, no dependencies for the build) and documentation of
the game's formats.

| Document | What's in it |
|---|---|
| [docs/HOW_TO_PATCH.md](docs/HOW_TO_PATCH.md) | The simplest way to patch your game, with no renaming |
| [docs/BUILDING.md](docs/BUILDING.md) | Setting up, building, making patches, and the checking tools |
| [docs/TRANSLATION.md](docs/TRANSLATION.md) | Text file formats, scope, style guide, glossary, and naming decisions |
| [docs/EDITING.md](docs/EDITING.md) | Editing the in-game text graphics |
| [docs/PATCHES.md](docs/PATCHES.md) | How each code patch works |
| [docs/guide/](docs/guide/index.html) | The player's guide (published with GitHub Pages) and its [story walkthrough](docs/guide/story/index.html); data from `tools/guidedata.py` |
| [docs/GAMEPLAY.md](docs/GAMEPLAY.md) | How character creation, training partners and days off work, with advice and tables |
| [docs/TECHNICAL.md](docs/TECHNICAL.md) | The game's ROM layout, text engine, compression, data formats, and memory map |
| [docs/PLATFORM.md](docs/PLATFORM.md) | SNES pitfalls for this kind of work |
| [docs/HIDDEN_CONTENT.md](docs/HIDDEN_CONTENT.md) | Unlockables, debug features, and unused and cut content |
| [tools/README.md](tools/README.md) | Every tool, what it's for and how to run it |

Quick start:

```sh
python3 tools/extract.py                 # unpack the ROM in rom/ into extracted/
python3 build.py                         # -> build/Shiroi Rinngu He - Twinkle Little Star Story (English).smc
python3 make_patches.py --version v1.0   # -> release/*.bps and a zip
```

## AI disclosure

AI assisted with the translation.

## Legal

This is a non-commercial fan translation, not affiliated with or endorsed by the game's developers
or publishers. It contains no copyrighted game data that would let
anyone play without owning the game. The patches only work on your own copy of the game.
Shiroi Rinngu He - Twinkle Little Star Story and its contents belong to their respective owners. The Japanese text in this
repository is included for translation and reference.

The code in this repository is released under the [MIT License](LICENSE).
