; English text for the message loop of Shiroi Ring e (LoROM), drawn as the game's own 12 px cells.
; Assembled at $3F:8000. Two hooks:
;   $00:B2DB  JML hook  (the loop has the byte in A, 0-255; X = pointer, DB = the text's bank; M/X 16-bit)
;   $00:BB41  JML bb41  (the glyph lookup: Shift-JIS/JIS -> 24-bit address of a 12x12 glyph)
;
; A run of English (ASCII 0x20-0x7F, one-byte tokens 0xA0-0xDF/0xF0-0xFE = up to 3 letters from $3F:A800,
; and full-width Latin 82 4F..82 9A, the typed name) is drawn proportionally into a 1 bpp line in RAM,
; cut into 12 px cells, and each cell picture is kept in a glyph cache under a virtual code
; (bytes E0+(i>>7), 80+(i&7F); i = 0..511). The loop is then pointed at the list of codes and draws,
; stores (char pool / grid), advances and wraps them like Japanese characters; byte 03 after the list
; returns it to the text after the run. Redraws, window close/open and highlights replay the stored codes;
; bb41 hands the game the cached picture. When the cache runs low, entries no window holds are freed
; (mark: the grid 7E:74AF-76B6 and the char pool from the handle at 7E:76E5; private/work/textengine).
;
; RAM (bank 7F, unused by the game - write traces): C000-EFFF cache (512 x 24 B), F000 hash heads (512 w),
; F400 next links (512 w), F800-FC7F line (12 rows x 96 B, 768 px), FC80 code list, FD10-FF0F used flags,
; FF10.. variables, FF80 cell, FFE0-FFEF msgwait.
.m16
.x16

hook:
  CMP #$0007
  BNE h1
  JML $00B309
h1:
  PHA
  LDA.l $7FFF10
  BEQ h_noem
  ; drawing a code list: only while the loop really reads it (a skipped message leaves the flag)
  PHB
  SEP #$20
  PLA
  CMP #$7F
  REP #$20
  BNE h_stale
  CPX #$FC80
  BCC h_stale
  CPX #$FD04
  BCS h_stale
  PLA
  CMP #$0003
  BEQ h_ret
  JML $00B312
h_stale:
  LDA #$0000
  STA.l $7FFF10
h_noem:
  PLA
  CMP #$0020
  BCC h_orig
  CMP #$0080
  BCC h_run
  CMP #$00A0
  BCC h_fw
  CMP #$00E0
  BCC h_run
  CMP #$00F0
  BCC h_orig
  CMP #$00FF
  BCC h_run
h_orig:
  JML $00B312
h_fw:
  JSR fwchar
  BEQ h_orig
h_run:
  BRL run
h_ret:
  LDA #$0000
  STA.l $7FFF10
  LDA.l $7FFF12
  TAX
  SEP #$20
  LDA.l $7FFF14
  PHA
  PLB
  REP #$20
  JML $00B2C3

; X -> a full-width Latin letter or digit (82 4F-58, 82 60-79, 82 81-9A)? A = its ASCII, else A = 0 (Z set)
fwchar:
  LDA $0000,X
  AND #$00FF
  CMP #$0082
  BNE fw_no
  LDA $0001,X
  AND #$00FF
  CMP #$004F
  BCC fw_no
  CMP #$0059
  BCC fw_dig
  CMP #$0060
  BCC fw_no
  CMP #$007A
  BCC fw_up
  CMP #$0081
  BCC fw_no
  CMP #$009B
  BCC fw_lo
fw_no:
  LDA #$0000
  RTS
fw_dig:
  SEC
  SBC #$001F
  RTS
fw_up:
  SEC
  SBC #$001F
  RTS
fw_lo:
  SEC
  SBC #$0020
  RTS

; ---------------------------------------------------------------- a run of English
run:
  ; full-width letters alone (a keyboard page, one key per cell) stay as they are, except the typed name
  ; itself (7E:7E00-7E1F); with English letters in the run they are drawn as English
  PHX
rs1:
  LDA $0000,X
  AND #$00FF
  CMP #$0020
  BCC rs_fw
  CMP #$0080
  BCC rs_yes
  CMP #$00A0
  BCC rs_f
  CMP #$00E0
  BCC rs_yes
  CMP #$00F0
  BCC rs_fw
  CMP #$00FF
  BCC rs_yes
  BRA rs_fw
rs_f:
  JSR fwchar
  BEQ rs_fw
  INX
  INX
  BRA rs1
rs_fw:
  PLX
  PHB
  SEP #$20
  PLA
  CMP #$7E
  REP #$20
  BNE rs_orig
  CPX #$7E00
  BCC rs_orig
  CPX #$7E20
  BCS rs_orig
  BRA rs_go
rs_orig:
  JML $00B312
rs_yes:
  PLX
rs_go:
  TXA
  STA.l $7FFF38           ; where the run starts
  JSR chk_init
  PHB
  SEP #$20
  PLA
  STA.l $7FFF14           ; the text's bank
  REP #$20
  PHX
  LDX #$0000
  LDA #$0000
rc1:
  STA.l $7FF800,X
  INX
  INX
  CPX #$0480
  BNE rc1
  PLX
  LDA #$0000
  STA.l $7FFF16           ; pen
  BRA r_loop
r_endj:
  BRL r_end
r_loop:
  LDA.l $7FFF16
  CMP #$02E8
  BCS r_endj
  LDA $0000,X
  AND #$00FF
  CMP #$0020
  BCC r_endj
  CMP #$0080
  BCC r_letter
  CMP #$00A0
  BCC r_fw
  CMP #$00E0
  BCC r_tokj
  CMP #$00F0
  BCC r_endj
  CMP #$00FF
  BCC r_tokj
  BRA r_endj
r_tokj:
  BRL r_tok
r_letter:
  CMP #$0020
  BNE rl_put
  LDA $0001,X
  AND #$00FF
  CMP #$0020
  BEQ r_tab
  LDA #$0020
rl_put:
  JSR put
  INX
  BRA r_loop
r_fw:
  JSR fwchar
  BEQ rf_sp
  JSR put
  INX
  INX
  BRL r_loop
rf_sp:
  ; a full-width space padding a number (the game's %d) inside English takes no room (after a column stop
  ; the number was already right-aligned in its cells, r_tab)
  LDA $0000,X
  CMP #$4081
  BNE rf_end
  INX
  INX
  LDA $0000,X
  CMP #$4081
  BEQ rf_ok
  JSR fwchar
  CMP #$0030
  BCC rf_back
  CMP #$003A
  BCS rf_back
rf_ok:
  BRL r_loop
rf_back:
  DEX
  DEX
rf_end:
  BRL r_end
r_tab:
  ; two or more spaces = a column stop: the text after them starts at cell (bytes from the run start) / 2,
  ; where the Japanese had it (templates keep the Japanese byte layout), or the next free cell
  INX
  LDA $0000,X
  AND #$00FF
  CMP #$0020
  BEQ r_tab
  LDA.l $7FFF16
  CLC
  ADC #$000B
  JSR div12
  STA.l $7FFF28
  TXA
  SEC
  SBC.l $7FFF38
  LSR A
  CMP.l $7FFF28
  BCS rtb1
  LDA.l $7FFF28
rtb1:
  CMP #$003C
  BCC rtb2
  LDA #$003C
rtb2:
  ASL A
  ASL A
  STA.l $7FFF28
  ASL A
  CLC
  ADC.l $7FFF28
  STA.l $7FFF16
  ; a number field (the game's %d: full-width spaces and digits) right after the stop ends where the
  ; Japanese one did: k cells from the stop, so the digits start at k*12 - digits*width('0')
  PHX
  LDA #$0000
  STA.l $7FFF28
rtn1:
  LDA $0000,X
  CMP #$4081
  BEQ rtn_sp
  JSR fwchar
  CMP #$0030
  BCC rtn_e
  CMP #$003A
  BCS rtn_e
  LDA.l $3FA100           ; advance of '0'
  AND #$00FF
  EOR #$FFFF
  INC A
  CLC
  ADC #$000C
  BRA rtn2
rtn_sp:
  LDA #$000C
rtn2:
  CLC
  ADC.l $7FFF28
  STA.l $7FFF28
  INX
  INX
  BRA rtn1
rtn_e:
  PLX
  LDA.l $7FFF28
  CLC
  ADC.l $7FFF16
  STA.l $7FFF16
  BRL r_loop
r_tok:
  CMP #$00F0
  BCC rt1
  SEC
  SBC #$00B0
  BRA rt2
rt1:
  SEC
  SBC #$00A0
rt2:
  ASL A
  ASL A
  STA.l $7FFF30           ; token offset
  LDA #$0000
  STA.l $7FFF32           ; letters done
rt3:
  PHX
  LDA.l $7FFF30
  CLC
  ADC.l $7FFF32
  TAX
  LDA.l $3FA800,X
  PLX
  AND #$00FF
  BEQ rt4
  JSR put
  LDA.l $7FFF32
  INC A
  STA.l $7FFF32
  CMP #$0003
  BNE rt3
rt4:
  INX
  BRL r_loop
r_end:
  LDA.l $7FFF16
  CLC
  ADC #$000B
  JSR div12
  STA.l $7FFF1A           ; cells
  ; a menu row padded with spaces to the Japanese byte length (tools/gametext.py fit_lines) takes as many
  ; cells as the Japanese (bytes / 2), so a shorter English row covers the longer row it replaces on scroll
  LDA $0000,X
  AND #$00FF
  CMP #$0020
  BCS r_p9                ; the run did not end at a control byte
  DEX
  LDA $0000,X
  INX
  AND #$00FF
  CMP #$0020
  BNE r_p9                ; no trailing space
  TXA
  SEC
  SBC.l $7FFF38
  INC A
  LSR A
  CMP #$003C
  BCC r_p0
  LDA #$003C
r_p0:
  STA.l $7FFF28           ; wanted cells
  LDA.l $7E6CD1
  AND #$00FF
  BEQ r_p2
  LDA.l $7E2663           ; wrapping window: no further than its right edge
  AND #$00FF
  STA.l $7FFF38
  LDA.l $7E6CCD
  AND #$00FF
  SEC
  SBC.l $7FFF38
  BCC r_p9
  CMP.l $7FFF28
  BCC r_p1
r_p2:
  LDA.l $7FFF28
r_p1:
  CMP.l $7FFF1A
  BCC r_p9
  STA.l $7FFF1A
r_p9:
  ; a run that reaches the window's right edge is wrapped by the game (6CD1): then a line break right
  ; after it would leave an empty line, so it is skipped
  LDA.l $7E6CD1
  AND #$00FF
  BEQ r_e1
  LDA.l $7E2663
  AND #$00FF
  CLC
  ADC.l $7FFF1A
  PHA
  LDA.l $7E6CCD
  AND #$00FF
  STA.l $7FFF28
  PLA
  CMP.l $7FFF28
  BCC r_e1
  LDA $0000,X
  AND #$00FF
  CMP #$000A
  BEQ r_e0
  CMP #$000D
  BNE r_e1
r_e0:
  INX
r_e1:
  TXA
  STA.l $7FFF12           ; where the loop goes on after the run
  SEP #$20
  LDA #$7F
  PHA
  PLB
  REP #$20
  LDA $FF1E
  CMP #$0040
  BCS r_ok
  JSR gc
r_ok:
  STZ $FF1C
r_cell:
  LDA $FF1C
  CMP $FF1A
  BCS r_emit
  JSR cut
  JSR intern
  PHA
  LDA $FF1C
  ASL A
  TAX
  PLA
  STA $FC80,X
  INC $FF1C
  BRA r_cell
r_emit:
  LDA $FF1C
  ASL A
  TAX
  LDA #$0003
  STA $FC80,X
  LDA #$0001
  STA $FF10
  LDX #$FC80
  JML $00B2C3

; A = a letter 0x20-0x7F: OR it into the line at the pen, pen += its advance. X kept.
; Letter table $3F:A000, 16 bytes a letter: advance, 12 rows (leftmost pixel = bit 7).
put:
  PHX
  SEC
  SBC #$0020
  AND #$007F
  ASL A
  ASL A
  ASL A
  ASL A
  TAX
  LDA.l $3FA000,X
  AND #$00FF
  STA.l $7FFF26           ; advance
  LDA.l $7FFF16
  AND #$0007
  STA.l $7FFF36           ; shift
  LDA.l $7FFF16
  LSR A
  LSR A
  LSR A
  STA.l $7FFF2A           ; byte in the line
  LDY #$000C
pl1:
  LDA.l $3FA001,X
  AND #$00FF
  BEQ pl3
  XBA
  PHY
  PHA
  LDA.l $7FFF36
  TAY
  PLA
pl2:
  CPY #$0000
  BEQ pl2e
  LSR A
  DEY
  BRA pl2
pl2e:
  XBA
  PLY
  PHX
  PHA
  LDA.l $7FFF2A
  TAX
  PLA
  ORA.l $7FF800,X
  STA.l $7FF800,X
  PLX
pl3:
  LDA.l $7FFF2A
  CLC
  ADC #$0060
  STA.l $7FFF2A
  INX
  DEY
  BNE pl1
  LDA.l $7FFF16
  CLC
  ADC.l $7FFF26
  STA.l $7FFF16
  PLX
  RTS

; ---------------------------------------------------------------- cells (DB = 7F from here on)
; cell FF1C of the line -> FF80 (12 words, leftmost pixel = bit 15, as the ROM font)
cut:
  LDA $FF1C
  LSR A
  CLC
  ADC $FF1C
  TAX
  LDY #$0000
ct1:
  LDA $F800,X
  XBA
  PHA
  LDA $FF1C
  AND #$0001
  BEQ ct2
  PLA
  ASL A
  ASL A
  ASL A
  ASL A
  BRA ct3
ct2:
  PLA
ct3:
  AND #$FFF0
  STA $FF80,Y
  TXA
  CLC
  ADC #$0060
  TAX
  INY
  INY
  CPY #$0018
  BNE ct1
  RTS

; FF80 -> A = its code word (found, or a new cache entry; 8140 if the cache is full)
intern:
  JSR hash
  STA $FF24
  TAX
  LDA $F000,X
in1:
  CMP #$FFFF
  BEQ in_new
  STA $FF34
  JSR cmpcell
  BEQ in_found
  LDA $FF34
  ASL A
  TAX
  LDA $F400,X
  BRA in1
in_new:
  JSR alloc
  CMP #$FFFF
  BNE in_n1
  LDA #$4081
  RTS
in_n1:
  STA $FF34
  JSR addr24
  LDY #$0000
in_c:
  LDA $FF80,Y
  STA $0000,X
  INX
  INX
  INY
  INY
  CPY #$0018
  BNE in_c
  LDA $FF34
  ASL A
  TAX
  LDY $FF24
  LDA $F000,Y
  STA $F400,X
  LDA $FF34
  STA $F000,Y
in_found:
  LDA $FF34
  PHA
  AND #$007F
  ORA #$0080
  XBA
  STA $FF26
  PLA
  LSR A
  LSR A
  LSR A
  LSR A
  LSR A
  LSR A
  LSR A
  CLC
  ADC #$00E0
  ORA $FF26
  RTS

; entry FF34 == FF80? Z set if equal
cmpcell:
  LDA $FF34
  JSR addr24
  LDY #$0000
cc1:
  LDA $0000,X
  CMP $FF80,Y
  BNE cc2
  INX
  INX
  INY
  INY
  CPY #$0018
  BNE cc1
  LDA #$0000
cc2:
  RTS

; A = entry -> X = its glyph address ($C000 + 24 * entry)
addr24:
  ASL A
  ASL A
  ASL A
  STA $FF28
  ASL A
  CLC
  ADC $FF28
  CLC
  ADC #$C000
  TAX
  RTS

; FF80 -> A = 2 * hash (0-511)
hash:
  LDA #$0000
  LDY #$0000
hs1:
  EOR $FF80,Y
  ASL A
  ADC #$0000
  INY
  INY
  CPY #$0018
  BNE hs1
  STA $FF28
  XBA
  AND #$00FF
  EOR $FF28
  AND #$01FF
  ASL A
  RTS

; a free entry -> A (marked used), or FFFF
alloc:
  LDA $FF1E
  BEQ al_none
  LDX $FF20
al1:
  LDA $FD10,X
  AND #$00FF
  BEQ al_got
  INX
  CPX #$0200
  BCC al1
  LDX #$0000
  BRA al1
al_got:
  SEP #$20
  LDA #$01
  STA $FD10,X
  REP #$20
  DEC $FF1E
  TXA
  INC A
  AND #$01FF
  STA $FF20
  TXA
  RTS
al_none:
  LDA #$FFFF
  RTS

; free every entry no window holds; rebuild the hash
gc:
  LDX #$0000
  LDA #$0000
g1:
  STA $FD10,X
  INX
  INX
  CPX #$0200
  BNE g1
  LDX #$74AF
g2:
  LDA.l $7E0000,X
  JSR mark
  INX
  INX
  CPX #$76B7
  BCC g2
  LDA.l $7E76E5
  TAX
  LDA.l $7E0002,X
  CMP #$007F
  BNE g4
  LDA.l $7E0004,X
  CMP #$0801
  BCS g4
  STA $FF28
  LDA.l $7E0000,X
  TAX
  CLC
  ADC $FF28
  STA $FF2E
g3:
  CPX $FF2E
  BCS g4
  LDA $0000,X
  JSR mark
  INX
  INX
  BRA g3
g4:
  LDX #$0000
  LDA #$FFFF
g5:
  STA $F000,X
  INX
  INX
  CPX #$0400
  BNE g5
  LDA #$0200
  STA $FF1E
  STZ $FF34
g6:
  LDX $FF34
  LDA $FD10,X
  AND #$00FF
  BEQ g7
  DEC $FF1E
  LDA $FF34
  JSR addr24
  LDY #$0000
g6c:
  LDA $0000,X
  STA $FF80,Y
  INX
  INX
  INY
  INY
  CPY #$0018
  BNE g6c
  JSR hash
  TAY
  LDA $FF34
  ASL A
  TAX
  LDA $F000,Y
  STA $F400,X
  LDA $FF34
  STA $F000,Y
g7:
  INC $FF34
  LDA $FF34
  CMP #$0200
  BNE g6
  RTS

; A = a stored word: a virtual code? mark its entry used. X kept.
mark:
  PHA
  AND #$00FF
  CMP #$00E0
  BCC mk_no
  CMP #$00E4
  BCS mk_no
  SEC
  SBC #$00E0
  STA $FF26
  PLA
  XBA
  AND #$00FF
  CMP #$0080
  BCC mk_r
  AND #$007F
  STA $FF2C
  LDA $FF26
  ASL A
  ASL A
  ASL A
  ASL A
  ASL A
  ASL A
  ASL A
  ORA $FF2C
  PHX
  TAX
  SEP #$20
  LDA #$01
  STA $FD10,X
  REP #$20
  PLX
mk_r:
  RTS
mk_no:
  PLA
  RTS

; first use (or RAM from before this code): empty cache
chk_init:
  LDA.l $7FFF22
  CMP #$4E43
  BNE ci0
  LDA.l $7FFF3E
  CMP #$5657
  BNE ci0
  RTS
ci0:
  PHX
  LDX #$0000
  LDA #$FFFF
ci1:
  STA.l $7FF000,X
  INX
  INX
  CPX #$0400
  BNE ci1
  LDX #$0000
  LDA #$0000
ci2:
  STA.l $7FFD10,X
  INX
  INX
  CPX #$0200
  BNE ci2
  STA.l $7FFF10
  STA.l $7FFF20
  LDA #$0200
  STA.l $7FFF1E
  LDA #$4E43
  STA.l $7FFF22
  LDA #$5657
  STA.l $7FFF3E
  PLX
  RTS

; ---------------------------------------------------------------- glyph lookup hook (00:BB41, JSR'd)
; Stack: S+1 return, S+3 JIS, S+5 the Shift-JIS word (lead, trail - 1: B713 decrements a trail >= 80
; in place). A virtual code ->
; A = $7F, X = its cached glyph, straight back to the caller; else the original routine.
bb41:
  LDA $05,S
  AND #$00FF
  CMP #$00E0
  BCC bb_o
  CMP #$00E4
  BCS bb_o
  SEC
  SBC #$00E0
  ASL A
  ASL A
  ASL A
  ASL A
  ASL A
  ASL A
  ASL A
  STA.l $7FFF3A
  LDA $06,S               ; the trail byte, already decremented by the Shift-JIS conversion (00:B727)
  AND #$00FF
  CMP #$007F
  BCC bb_o
  SEC
  SBC #$007F
  ORA.l $7FFF3A
  ASL A
  ASL A
  ASL A
  STA.l $7FFF3C
  ASL A
  CLC
  ADC.l $7FFF3C
  CLC
  ADC #$C000
  TAX
  LDA #$007F
  JML $00BBAC
bb_o:
  PHP
  PHD
  REP #$20
  JML $00BB45

; ---------------------------------------------------------------- helpers
div12:
  PHY
  LDY #$0000
dv1:
  CMP #$000C
  BCC dv2
  SEC
  SBC #$000C
  INY
  BRA dv1
dv2:
  TYA
  PLY
  RTS

; ---------------------------------------------------------------- reading time after a message
; Called (JSL) from 05:95DF in place of "LDA #$001E / PHA": the wait the script engine takes after a
; message that runs by itself (the opening). The Japanese text is typed slowly enough to be read while it
; types; English is typed faster, so wait 30 frames + 1.5 frames per byte of the message (at most 600).
; Leaves the wait pushed on the caller's stack (as the PHA did).
msgwait:
  REP #$30
  PLA
  STA.l $7FFFE2           ; return address
  SEP #$20
  PLA
  STA.l $7FFFE4           ; return bank
  REP #$30
  LDY #$0000
mw1:
  SEP #$20
  LDA [$15],Y
  REP #$20
  BEQ mw2
  INY
  CPY #$0400
  BNE mw1
mw2:
  ; 30 frames + 1.5 per byte for the first 60 bytes + 0.25 per byte after, at most 240 (4 s)
  TYA
  CMP #$003C
  BCC mw2a
  SEC
  SBC #$003C
  LSR A
  LSR A
  CLC
  ADC #$0078
  BRA mw2b
mw2a:
  STA.l $7FFFE6
  LSR A
  CLC
  ADC.l $7FFFE6
  CLC
  ADC #$001E
mw2b:
  CMP #$00F0
  BCC mw3
  LDA #$00F0
mw3:
  PHA
  SEP #$20
  LDA.l $7FFFE4
  PHA
  REP #$20
  LDA.l $7FFFE2
  PHA
  RTL

; ---------------------------------------------------------------- the game's formatter (00:B8A0, %s %d)
; it copied the template and %s strings two bytes at a time (Shift-JIS), so a % at an odd byte was missed and
; an odd-length English name swallowed its end mark. One byte for English (below 81, A0-DF tokens, F0-FF).
fmtc:
  LDA [$1B]
  STA $0000,Y
  AND #$00FF
  BEQ fc_end
  JSR fbytes
  BCS fc_two
  INC $1B
  INY
  JML $00B8C0
fc_two:
  INC $1B
  INC $1B
  INY
  INY
  JML $00B8C0
fc_end:
  INC $1B
  INC $1B
  INY
  INY
  JML $00B9D4
scopy:
  LDA [$11]
  AND #$00FF
  BEQ sc_end
  LDA [$11]
  STA $0000,Y
  AND #$00FF
  JSR fbytes
  BCS sc_two
  INC $11
  INY
  BRA scopy
sc_two:
  INC $11
  INC $11
  INY
  INY
  BRA scopy
sc_end:
  JML $00B91F
fbytes:
  ; carry set = a Shift-JIS lead byte (81-9F, E0-EF)
  CMP #$0081
  BCC fb1
  CMP #$00A0
  BCC fb2
  CMP #$00E0
  BCC fb1
  CMP #$00F0
  BCC fb2
fb1:
  CLC
  RTS
fb2:
  SEC
  RTS

; ---------------------------------------------------------------- name keyboard: delete
; Called (JSL) from 05:C94E, the keyboard's delete. The game drew the cursor "＿" and a blank at the
; full-width column (letters + 4) without redrawing the name, which left the deleted letter on screen
; because the typed name is drawn proportionally (fewer cells). Like typing (05:C7A9), this goes to
; column 4 and redraws the name, so the game's "＿" and blank that follow land right after it.
namedel:
  LDA #$0000
  PHA
  LDA #$0004
  PHA
  JSL $009A4A             ; column 4, row 0
  PLA
  PLA
  SEP #$20
  LDA #$7E
  PHA
  PLB
  REP #$20
  LDA #$0000
  PHA
  LDA #$0001
  PHA
  LDA #$007E
  PHA
  LDA #$7E01
  PHA
  JSL $00B287             ; the name (7E:7E01)
  PLA
  PLA
  PLA
  PLA
  RTL
