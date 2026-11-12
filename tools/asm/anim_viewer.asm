; Patch group dev-anim-viewer: a way into the game's own training animation viewer ($04:FA62), which
; nothing in the original calls. Assembled at $22:FF00 (end of an unused 0x5000-byte run of $FF).
; Hook: $04:8464, the boot code's JSL $07:D9BE (title flow, which itself checks Up+L for the arena
; viewer), becomes JSL here. Holding exactly Down+L on controller 1 at power-on runs the viewer; anything
; else goes on to the title as before ($7E:2648 = controller 1 held, the copy $00:93AE returns).
.m16
.x16

hook:
  LDA.l $7E2648
  CMP #$0420
  BNE title
  JSL $04FA62
title:
  JML $07D9BE
