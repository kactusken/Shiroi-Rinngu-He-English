# Patches

What the build changes besides text and images, one section per patch: what the original code
does, what changed, why it works, the tool that makes it, limits to respect, and whether it was
*verified in game*.

## dev-anim-viewer: Down+L opens the training animation viewer
*seen headless* (2026-11-12, Mesen, `build.py --unlocks dev-anim-viewer`; owner check pending)

- **Original:** the boot code calls the title routine with `JSL $07:D9BE` at `$04:8464`. The training
  animation viewer at `$04:FA62` ([HIDDEN_CONTENT.md](HIDDEN_CONTENT.md)) is never called.
- **Change:** that call goes to a 17-byte stub at `$22:FF00` (tools/asm/anim_viewer.asm, in an unused
  run of `$FF` in the original image). If controller 1 holds exactly Down+L (`$7E:2648` = `$0420`), it
  calls the viewer. Either way it then jumps to `$07:D9BE`, whose RTL returns to the boot code as before.
- **Limits:** the viewer has no exit: reset to leave it. Other buttons at power-on behave as in the
  original (Up+R match test, Up+L ring background viewer).
- In the default English build and the released patch (owner decision 2026-11-12).

## fix-kagono-loss: losing to Kotori Kagono no longer ends the story
*seen headless* (2026-11-12, Mesen 2.2.1, Carol-route September 1999 savestate with the heroine's stats
poked to 1: she lost, and the October 1999 scenes and menu followed; owner check pending)

- **Original:** on the Carol route the September 14, 1999 match against Kotori Kagono is followed on
  September 15 by event `0x0094`: on a win it calls `0x0095` (Kagono's s121, then October), on a loss
  it calls `0x0093`, the *pre-match* event. That replays s120 and books nothing, so October's scenes,
  the March 31, 2000 final and the ending never come; the game runs on past March 2000. Event `0x0096`
  (Kagono's loss scene s122, then October like a win) is never called.
- **Change:** the loss call's event number, file offset `0x0D2302` (`$1A:A302`), `93` -> `96`.
- Always on in the English build (`ALWAYS_GROUPS`; owner decision 2026-11-12); `--no-translation` and
  the control build leave it out.
