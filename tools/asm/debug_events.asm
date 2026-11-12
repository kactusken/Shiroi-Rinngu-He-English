; TEST BUILDS ONLY (build.py group debug-events, never released): play any story event on demand.
; Assembled at $3E:8000 (free space in the expanded ROM). Hook: $05:8000, the game's "wait for a button"
; routine (dialogue pages, menus), whose first 4 bytes PHP / PHD / REP #$20 are replaced by JML dbg.
; When the word at $7F:FFF0 is not 0, it is cleared and that event id is run through the event
; interpreter $05:9FE5 (as the game's own debug start at $04:83E3 does), then the wait goes on.
; Used by private/work/late/ (the scene sweep and the savestate ladder): poke $7F:FFF0, reach any wait.
.m16
.x16

dbg:
  PHP
  REP #$30
  PHA
  LDA.l $7FFFF0
  BEQ done
  PHA
  LDA #$0000
  STA.l $7FFFF0
  JSL $059FE5
  PLA
done:
  PLA
  PLP
  PHP
  PHD
  REP #$20
  JML $058004
