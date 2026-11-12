# Gameplay mechanics - Shiroi Rinngu He - Twinkle Little Star Story

How character creation and monthly training work, read from the game's code. It is written as
source material for a player's guide: the first half explains the rules and gives advice, and the
reference tables and memory addresses follow.

**How sure this is:** everything here is *from the code* (the original ROM) unless it says otherwise.
Two training months (Carol Midori and Miki Handa as partners) were run in a headless emulator, and
every stat change in them matched these rules (*checked in an emulator run*). Nothing here has been
confirmed in normal play yet.

Stat names follow the English patch: **HP** (体力), **Str** (筋力), **Figure** (プロポーション).

## Contents
- [Stats in brief](#stats-in-brief) · [Character creation](#character-creation) · [The month schedule](#the-month-schedule)
- [A training day](#a-training-day) · [Days off](#days-off) · [Recommendations](#recommendations)
- [What each stat does](#what-each-stat-does) · [Matches](#matches) · [Story, routes and endings](#story-routes-and-endings)
- [Reference tables](#reference-tables) · [Technical reference](#technical-reference) · [Open questions](#open-questions)

## Stats in brief
- **HP and Str are averages of hidden body-part stats.** Six body parts (right/left arm, right/left leg,
  head, body) each have their own HP and Str. The HP shown is the average of the six part HPs, and Str
  the average of the six part Strs. Training and clubs raise the parts, not HP/Str directly.
- **Stamina** is spent by training and can never be higher than HP.
- **Height** = 150 + (hidden growth value ÷ 5). **Weight** = (HP + Str) ÷ 16 + (hidden growth + hidden
  weight) ÷ 8 + 45. These are recalculated after each month.
- **Wrestler type:** five type values, Strong, Entertainment, Babyface, Power and Heel. In the game's
  advice scene Harley Saito explains that training with someone pulls you toward her type. Your zodiac
  sign and your partners' daily bonuses raise these values.
- **Stress** rises when a training day is lost. **Focus** is the stress limit: while Stress is higher
  than Focus, you cannot train.
- Every stat is held between 0 and 255.

## Character creation
At the end of the profile screen the game builds the wrestler as follows:

1. Almost every stat starts at **10**.
2. **Club history:** each school year (Gr.1-6, JH1-3) adds its club's bonuses. These are mostly ±1 or ±2,
   and the nine years add up. A stat pushed below 0 becomes 0.
3. **Zodiac sign:** adds wrestler-type points (table below).
4. **Blood type:** adds +30 to one hidden value, one per type (A, B, O or AB). **Blood type has no
   effect on play.** Nothing in the game ever reads these values. It is only shown on the profile
   screen. See [Blood type](#blood-type) for how this was checked.
5. Stress is set to 0, HP, Str, Height and Weight are calculated, and **Stamina is filled to HP**.

**Clubs matter most**, because they set your starting HP, and HP limits how much you can train (see
[Days off](#days-off)). Nine years of Soccer Club add +72 to the body-part HPs, which gives a starting
HP and Stamina of about 22 instead of 10. The full club list is in the [reference tables](#clubs).

Best clubs for body stats (per school year, summed over the six body parts):

| Club | Part HP (sum) | Part Str (sum) | Also |
|---|---|---|---|
| Soccer Club | **+8** | +6 | +1 Speed, +1 Jumping |
| Swim Club | +7 | **+12** | −1 Figure |
| Tennis | +6 | +8 | |
| Gymnastics, Basketball | +6 | +6 | +1 Speed, +1 Jumping (Basketball: +2 hidden growth, so taller) |
| Wrestling, Judo, Karate, Taekwondo, Old Martial Arts, Trekking | +6 | +6 | small Guts/Fame/Figure changes |

Club bonuses to Max Calm are lost: the first story event sets Max Calm to 100.
Clubs for other stats: Focus (Archery +3; Calligraphy, Tea Ceremony and Movie Club +2), Fame
(Student Council +4, Light Music +2), Singing (Chorus +4), Acting (Drama +3), Figure (Aerobics +3).

**Go-Home Club** (no club) adds nothing. If every year is Go-Home, training keeps a +10% success
bonus. That is a poor trade, because training succeeds 80-90% of the time early on anyway.

### Zodiac signs

| Sign | Bonus | Sign | Bonus |
|---|---|---|---|
| Aries | +10 Entertainment | Libra | +15 Entertainment |
| Taurus | +8 Babyface | Scorpio | +10 Strong |
| Gemini | +5 Babyface, +5 Power | Sagittarius | +7 Babyface, +8 Heel |
| Cancer | +15 Heel | Capricorn | +10 Strong, +10 Babyface |
| Leo | +20 Strong | Aquarius | +20 Strong |
| Virgo | +10 Babyface | Pisces | +15 Heel |

### Blood type
*From the code*, with one emulator check. Blood type is stored twice: as the profile choice at `$7E:7E16`
(0-3 for A, B, O, AB) and as +30 on hidden stat 98, 99, 100 or 101, via the effect lists at `$1F:A18B`.
The April save (type A) holds 30 in stat 98 and 0 in the other three. Neither copy is used by the game:

- **The profile choice** is read only by the profile screen (`$05:D29D`-`$05:D412`) and by wrestler
  setup (`$05:E2BC`, which adds the +30).
- **No code reads the four hidden stats directly**, in any addressing mode, and nothing reaches them
  through a base pointer plus offset.
- **Every routine that reads stats by a computed index** was traced to where its index comes from:
  - the training check, the stat command and the monthly results only cover stats 0-66;
  - the status screens ask for stats 0-4 and 48-59;
  - the club setup uses the list at `$1F:A7C3`;
  - new-wrestler initialisation sets 0-44 and 76-79 to 10 and leaves 98-101 alone.
- **Matches** copy the heroine's stats into the fighter record from the list at `$1F:C855` (both at
  `$06:8658` and `$07:95D0`). That list holds stats 0-44, 49 and 50 only, so the match code never
  sees blood type.
- **Event scripts** (`$1A:8000`, run by `$05:9FE5`) can compare or change any stat by index. Across
  banks `$1A`-`$1C`, every compare tests one of the special values (`$7E:7E74` or `$7E:7E78`), never a
  stat, and no set/add/subtract command touches stats 98-101.
- **A traced month** (April, with training, Sundays and the day-29 event) never read them.

The stat block also has unused "birth month", "birth day" and "blood type" label slots (7-9), which
suggests the same record layout is shared with other wrestlers. Blood-type compatibility or personality
may have been planned and never connected.

## The month schedule
At the start of each month you set a **training partner for each week**. Every weekday is a training
day with that week's partner. Sundays and holidays are **days off**, where you choose a place to go.
Some days hold fixed events.

**Who you can train with** is set by story events (*from the code*; the route each later event belongs
to is read from its scenes):
- **Start (April):** Carol Midori, Miki Handa, Mikiko Futagami, Michiko Omukai, Harley Saito, Keiko Aono.
  Futagami leaves the list early in the first year.
- **The joint heel/babyface training month:** Eagle Sawai, Mizuki Endo, Kurenai Yasha and Noriyo Tateno
  join for that month only.
- **Kurenai's group:** later, Sawai, Endo, Kurenai and Tateno replace Carol's group. Yoshiaki Fujiwara
  and Yuki Ishikawa join after the scene where Eagle Sawai scolds you.
- **FMW route:** Atsushi Onita, Megumi Kudo, Yukie Nabeno, Kaori Nakayama, Nurse Nakamura and Miwa Sato.
  Great Sasuke, Super Delfin and Jinsei Shinzaki join during the Michinoku Pro stay. Combat Toyoda,
  Crusher Maedomari, Yukari Ishikura and Keiko Iwami join later on that route.

## A training day
1. **Can you train at all?** The day is **lost** if any of these is true:
   - Stamina is lower than the partner's daily cost;
   - Stress is higher than Focus;
   - any body part has an injury level of 3 or more.

   A lost day gives nothing except **Stress +1** and a small boost to the next day's success chance.
   *(checked in an emulator run)*
2. **Partner bonus.** On every day you train, the partner's daily bonus is applied whatever happens
   next. These bonuses are mostly wrestler-type and technique points.
3. **Exercises.** The partner's exercises are tried in her order, and each one rolls for success:

   chance (%) = min(80, (200 − S) ÷ 2) + 10 (all Go-Home only) + 5 × (lost days in a row) − 10 × (Stress ÷ 50)

   Here S is the exercise's main stat, the first stat in its effect list. So the chance is 80% (90%)
   until that stat passes 40, then drops: 50% at 100, 10% at 180. **Once one exercise succeeds, it and
   every later exercise in the list apply automatically.** Exercises before the first success are lost
   for that day. If none succeeds, Stress +1.
4. **Stamina cost.** The partner's daily cost is subtracted from Stamina.

**Game bug: the Stamina cost is read one slot off.** The game charges the cost of the *next*
exercise in its table instead of the one done. That makes Carol Midori cost 3 a day (her own exercises
add up to 8) and Miki Handa 5 (her own: 4). A partner whose list includes Running also picks up an
unpredictable extra amount, read from unrelated memory (it was 0 when checked). The partner table
lists the real cost. *(checked in an emulator run for Carol and Handa)*

**End of the week: exhaustion.** After each training week, if Stamina is below half of HP, the hidden
weight drops by 10 (`$04:F953`; *checked in an emulator run*, where it fell 10 → 0 in the first week).
Training always runs until Stamina is below the partner's cost, so you almost always finish the week
under half HP. In practice the hidden weight stays near 0, whatever clubs or Dining add.

## Days off
**Stamina only comes back on days off**, and only from these choices. It does not refill at the end of
the month *(checked in an emulator run)*.

| Day off | Stamina |
|---|---|
| Full Rest | + HP ÷ 2 |
| Movies | + HP ÷ 16 |
| Running | −20, then + HP ÷ 32 |
| Kick Gym, Judo Dojo, Karate Dojo, Pool | −20 |
| Sambo Club | −15 (see the bug note below) |
| Aerobics Gym | −5 |
| anything else | no change |

After a day off, Stamina is capped at HP. The other effects of each place are in the
[reference tables](#day-off-places). For Stress: Karaoke Box −20, Dining and Shopping −10, Movies −5.
Shopping (+5) and Movies (+2) also raise Focus permanently.

**Which places are open.** The list grows with each in-game year, counted from April. Each year opens
the next places in the order of the reference table:

| Year | Places open | New this year |
|---|---|---|
| 1 (from the first April) | 4 | Dining, Movies, Running, Full Rest |
| 2 | 9 | Kick Gym, Judo Dojo, Karate Dojo, Swimsuit Shop, Hair Salon |
| 3 | 10 | Karaoke Box |
| 4 | 12 | Pool, Shopping |
| 5 | 13 | Sambo Club |
| 6 | 14 | Aerobics Gym |

So in the first year the only ways to lower Stress are **Dining (−10)** and **Movies (−5)**. *Year 1
seen in an emulator run; the later years are from the code.* If any of six body-part values (stats
80-85, probably match damage) is above 0, Running, the Kick Gym, both dojos, the Sambo Club and the
Aerobics Gym are removed; if the highest of them is 4, only Full Rest is left *(from the code)*.

**Game bug:** the Sambo Club entry is missing its end marker, so it also applies Aerobics Gym's effects
(−5 Stamina, +2 Flex, +5 Figure) on top of its own.

## Recommendations
Based on everything above (*from the code*; no strategy has been play-tested yet).

**What to aim for.** The ending depends only on your route and on winning the March 31 Tokyo Dome
match. Matches are automatic and end only by pin or submission (see [Matches](#matches)). They are
won with **Pro Wrestling** first, then **head and body HP**, **Str** and **Suplexes** (the throws that
lead to pins), and **Flex** and **Speed** (each opponent miss is a counter for her). Pro Wrestling
unlocks most moves (requirements are typically around 100, up to 250) and adds to both attacking and
dodging. Str unlocks the strongest moves (requirements around 150). For the final against Kandori,
add **Guts** and arm, leg and head HP: her moves are mostly holds. **Ignore** Figure, Height, Weight, Singing, Acting, Calm, Justice,
Babyface, Power and Heel: nothing uses them.

### Character creation
- **Clubs** can't raise Pro Wrestling or Flex. What they can give is **body-part HP and Str, Speed and
  Jumping**, and starting HP is what sets your training pace. The bonuses simply add up, so take a
  strong club every year:
  - **Soccer Club** (+8 HP, +6 Str, +1 Speed, +1 Jumping per year; +2 each to head and body HP) is the
    best all-round pick. Nine years give HP ≈ 22 and Str ≈ 19 at the start, instead of 10 and 10.
  - **Swim Club** (+7 HP, +12 Str) for a few years if you want more Str. For example, 6 Soccer + 3 Swim
    gives HP ≈ 21 and Str ≈ 22.
  - Basketball, Gymnastics, Tennis, Volleyball and the martial-arts clubs are close behind (+5 to +6
    each, Tennis +8 Str). Basketball also gives +1 Focus.
  - Skip clubs for Max Calm (always reset to 100), Fame, Figure, Singing, Acting or weight.
  - It isn't confirmed that every club is offered in every school year; if Soccer is missing, take the
    next one on this list.
- **Zodiac sign** matters very little. In a match, only Strong vs Entertainment counts (Heel style if
  Entertainment is higher, otherwise Strong), and only for who moves first. Pick the sign you like.
- **Blood type** does nothing.

### Training plan
Real Stamina cost per day is in brackets. For each partner, the table shows the daily gain in the stats
that matter when every exercise applies.

| Partner (cost) | Pro Wres | Flex | Speed | Suplexes | Part HP | Part Str | Use for |
|---|---|---|---|---|---|---|---|
| Carol Midori (3) | 0 | +1 | +1 | +1 | **+8** | +1 | HP early: cheapest and best HP per Stamina |
| Miki Handa (5) | +1 | +2 | −1 | **+3** | +6 | 0 | Suplexes, Flex, HP |
| Harley Saito (8) | +2 | +3 | +1 | +2 | +7 | +2 | Best all-round April partner |
| Mikiko Futagami (7+) | **+3** | +2 | +2 | +1 | +2 | +6 | Pro Wrestling (leaves early) |
| Michiko Omukai (10) | 0 | 0 | +1 | 0 | −2 | **+15** | Str, once HP is high |
| Keiko Aono (10) | +1 | +2 | 0 | 0 | +2 | 0 | Poor value |

1. **First months: Carol only**, with **Full Rest** every Sunday. She is the only partner a starting
   wrestler can afford several times a week, and her +8 part HP a day raises both the Stamina cap and
   the Full Rest refill. If Futagami is still there and you can afford her for a week, her Pro
   Wrestling is worth taking before she leaves.
2. **Once HP is about 20-25: Harley and Handa.** Harley gives the best mix of Pro Wrestling, Flex,
   Suplexes and HP; Handa is cheaper and leads on Suplexes. Put Carol back in for a week whenever
   Stamina is running short.
3. **Once HP is about 40 or more: add Omukai** for Str (+15 part Str ≈ +2.5 Str a day), balanced with HP
   partners, because she lowers HP.
4. **Later partners**, depending on route:
   - **Kurenai's group:** Eagle Sawai and Mizuki Endo (+2 Pro Wrestling, big Str, but they lower HP);
     Noriyo Tateno and Yuki Ishikawa (+12 to +14 HP, +3 or +4 Flex); Yoshiaki Fujiwara (cheap, 4: +1 Pro
     Wrestling).
   - **FMW route:** Megumi Kudo (5: +12 HP, +3 Flex, +1 Pro Wrestling) is excellent. Atsushi Onita
     costs only 1 a day for +4 part Str. Kaori Nakayama gives +2 Pro Wrestling for 5. Michiko
     Nagashima gives +15 HP and +3 Flex for 6.
   - **Michinoku Pro:** Jinsei Shinzaki gives +2 Pro Wrestling for about 1 Stamina (the best Pro
     Wrestling per Stamina in the game); Great Sasuke gives +2 Pro Wrestling, +2 Flex, +2 Speed and
     +10 HP for 6.
   - Partners with high Flex (Rumi Kazama +5, Ishikawa, Super Delfin and Tsuppari Mac +4) cover
     defence.
5. **Exercise order matters a little:** exercises before the first successful roll in a day are lost.
   That rarely matters while the main stats are under about 100, because each roll then succeeds
   50-80% of the time.

### Days off
- **Full Rest** by default: it is the only real Stamina refill (+HP ÷ 2). It does not lower Stress.
- **Stress:** training stops while Stress is above Focus. Stress is on the status screen, but Focus
  is hidden, so keep a running count (see the Stress, Focus row in [What each stat does](#what-each-stat-does)). Which fix you have depends on the year
  (see [which places are open](#days-off)):
  - **Year 1:** only **Dining** (−10 Stress; its +5 weight and −1 Figure don't matter) and **Movies**
    (−5 Stress, +2 Focus for good, a little Stamina). Take Movies early in the year to raise the
    limit, and Dining when Stress is about to pass Focus. Matches also give +3 Focus.
  - **Karaoke Box** (year 3 on): −20 Stress, for when Stress is well over the limit.
  - **Shopping** (year 4 on): −10 Stress and +5 Focus for good, the best of them.
- Avoid the −20 Stamina places (the dojos, Kick Gym, the Pool and the Running place).

## What each stat does
Every finding in this section is *from the code*. No match has been run in an emulator yet, so the
match formulas are direct readings of the code and have not been seen in play.

**The short version:** the story never checks a stat. Stats matter because they **win matches**, and
match results pick the route events and the ending (see [Story, routes and endings](#story-routes-and-endings)).
Inside a match, the stats that count most are **Pro Wrestling**, **Flex**, **Speed**, the
**body-part HPs** and **Str**. Several stats shown on the status
screen do nothing at all.

| Stat | What the game uses it for | Value to the player |
|---|---|---|
| **Pro Wrestling** | Adds to hit chance in 181 moves and to evasion in 158; adds damage in 55; is a requirement for 234 moves | **The most important stat.** It unlocks most moves and helps both attack and defence |
| **Flex** | Evasion in 115 moves | The main defence stat |
| **Speed** | Hit chance in 51 moves, evasion in 34. (Its first-attack tie-break only applies between two Entertainment wrestlers, never to her) | Strong all-rounder |
| **Dex** | Hit chance in 29 moves; decides who attacks first only in Strong vs Strong | Minor |
| **Str** (and body-part Str) | Hit chance in 73 moves, damage in 41 | Main attack stat |
| **Body-part HP** | Each body part's health in a match. Damage comes off the part a move targets (mostly head and body; holds also hit arms and legs). Head and body HP at 0 or below invite a pin and slow kick-outs; a hold that takes a part to 0 starts the submission check. Their average, HP, caps Stamina for training | **Essential**: survival in matches and training capacity |
| **HP** (the average) | Training Stamina cap and refill only; no move uses it | See body-part HP |
| **Hidden weight** | Damage in 47+ moves | Would help, but the weekly exhaustion rule keeps it near 0 (see [A training day](#a-training-day)); not worth chasing |
| **Suplexes, Jumping, Falls** | Suplexes: hit in 52 moves, damage in 35. Jumping: damage in 21. Falls: evasion in 28 | Useful technique stats |
| **Punch, Kicks, Aerial, Holds, Karate, Judo, Sambo, Kickboxing, Lucha, Fujiwara-gumi, FMW, Rough** | Requirements that unlock moves of their style, plus hit and damage in those moves | Choose by the moves you want |
| **Guts** | Submission escape: when a hold leaves a body part at 0 HP or less, she holds on with a chance of (Guts ÷ 2 + 1) out of 150, checked again every turn the hold continues | Important against holds, above all in the final against Kandori |
| **Max Calm** | Starting **Calm** in a match. Most moves cost the attacker Calm. While she has Calm left and her head and body HP are above 0 she kicks out of pins at once. If the attacker's Calm is higher than the defender's, her landed moves can't be countered. Computer wrestlers unlock their strongest moves as their Calm runs down | Important, but **always 100**: the first story event sets it to 100, which wipes out the clubs' Max Calm bonuses, and nothing raises it later. Opponents start with 160-250 |
| **Fame** | Used by one move; decides the first attack only between two Babyface wrestlers (never her). Changes: +10 per win, −5 per loss, +2 for landing a move with a hit chance of 10% or less, +5 when the winning move is her registered finisher | No real match effect; no story effect |
| **Strong, Entertainment** | Pick her in-match style: **Heel if Entertainment > Strong, otherwise Strong** (a game bug: the other three types are never considered). Style only decides the first attack, from a 5×5 table. Strong is also in 3 defence lists | Small |
| **Babyface, Power, Heel, Justice** | Power appears in 10 moves, Heel in 1. Babyface and Justice are used nowhere | Almost nothing |
| **Stamina** | Training only (cost and the lost-day check). Not used in matches | Training resource |
| **Stress, Focus** | Training only: no training while Stress > Focus. Every match gives Focus +3. **Focus is hidden**: no status page or monthly report shows it *(status pages seen in an emulator run)*. It starts at 10 plus club bonuses (Archery +3; Movie Club, Calligraphy, Tea Ceremony +2; several +1; Street Gang −1). After that only Movies (+2), Running (+1), Shopping (+5) and matches (+3) raise it | Training resource |
| **Injuries** | Any body part at 3 or more blocks training. Matches don't add injuries | Avoid |
| **Figure, Height, Weight, Singing, Acting, Calm** | Only shown on the status screen. Nothing reads them | **No effect** |
| **Blood type** | Never read (see [Blood type](#blood-type)) | **No effect** |
| **Move counts, "Move / Counter / Fav Finish"** | The move counts are recalculated from the moves you've unlocked. Nothing reads the three labelled stats | Display only |

**Moves are unlocked purely by stats.** Every time she is loaded into a match, the game rebuilds her
move list from every move whose stat requirements she meets. Raising Pro Wrestling and the technique
stats is how you learn moves; no event teaches them.

## Matches
*From the code (three separate readings of bank `$06`, each checked against the others); no match has been
traced in an emulator yet, except where marked. Notes with every address: `private/work/match/`.*

**The player only watches.** Matches play out automatically for both sides; there is no command, move
or counter input (*the owner saw no prompts in the first story match*). The match loop (`$06:DE19`)
and the move choice (`$06:8F28`) read no buttons. Training, partners and days off decide how she fights.

### How a match runs
1. **Who attacks first.** Each wrestler has a style (0-4); a 5×5 table (`$1F:AFB2`) either names
   the first attacker or names a stat to compare: Dex for Strong vs Strong, Speed for Entertainment vs
   Entertainment, Fame for Babyface vs Babyface, Str for Power vs Power (ties are a coin flip). The
   heroine's style is only ever Strong or Heel (see the stat table). The computer wrestlers' style is
   loaded from the wrong byte (bug), so for 27 of the 28 the result comes from unrelated memory. This
   only decides the very first attack.
2. **The attacker keeps attacking until she is countered.** Turns do not alternate: each turn the
   current attacker picks a move, and the roles only swap when the defender counters. In tag matches the
   side that has just taken over may tag in her partner at that moment.
3. **Move choice**, in this order, the same for both sides unless noted:
   - **Hold in progress:** if the defender is caught in a hold, the attacker repeats the hold. A hold
     keeps going, turn after turn, until the defender counters.
   - **Forced pin:** if the defender is down and her head or body HP is 0 or less, the attacker goes for
     Pin or Side Cradle (50/50).
   - **Otherwise:** a random move from her usable list that fits the current positions, never the move
     that just landed, with a 10% chance of picking one of her favourite moves instead.
     - **The heroine** uses every move whose stat requirements she meets, with no Calm limit.
     - **A computer wrestler** has a fixed list in which each move has a Calm threshold. She may use a
       move only once her Calm has fallen to its threshold, so her strongest moves and finishers come
       late in the match. Her list also includes the basic moves anyone can use (Pin, Side Cradle,
       Dodge, Roll, Endure and others), so she can also go for a pin at random.
4. **Calm cost.** Most moves cost the attacker Calm; a few (24) take it from the defender instead. It is
   paid whether the move lands or not.
5. **Hit roll and counter.** Hit chance = the move's base + the attacker's hit stats − the defender's
   evasion stats, capped at 99%. A roll of 1-100 decides hit or miss. Then:
   - The defender looks for a **counter**: a move in the attacked move's counter list that she can use
     (her own usable moves, or the basic counters everyone has: Lift, Fall, Endure, Dodge, Roll, Inch,
     Free, Stop, Flip, Pin, Side Cradle). If there are several, one is picked at random.
   - **On a miss**, she counters whenever she has one.
   - **On a hit**, she counters only if a second roll succeeds: the counter's own hit chance ÷ 4, so at
     most about 24%. And if the attacker's Calm (after paying for the move) is higher than the
     defender's, a landed move can't be countered at all.
   - **A miss that can't be countered still lands** (bug, or deliberate: the hit roll is never read
     again). So every move either lands or is countered. A low hit chance doesn't make a move fail; it
     makes a counter likely.
6. **Damage.** If the move lands, damage = the sum of the move's power stats × their percentages (at
   least 1), taken off each targeted body part's current HP (which can go below 0). No stat reduces
   damage taken. If it is countered, the counter's damage goes to the original attacker instead, and
   the counterer becomes the attacker. Dodge, Roll and Stop do no damage of their own: the attacker
   takes the missed move's self-damage.
7. **Submission.** When a hold leaves its target part at 0 HP or less, the victim gives up unless she
   passes a Guts check: she holds on with a chance of (Guts ÷ 2 + 1) out of 150, at most 85% at Guts
   255. A hold repeats every turn until it is countered, so each turn means a new check. In tag
   matches the partner may break it up. **A submission ends the match.**
8. **Pin.** About 78 moves leave the opponent in a pinnable position: suplexes, drivers, many top-rope
   moves, Pin, Roll-Up and Side Cradle. After such a move lands, the referee counts:
   - With **Calm 1 or more** and head and body HP both above 0, she kicks out at once.
   - With Calm left but head or body HP at 0 or less, those parts recover 1/32 of their maximum every
     3 ticks while the referee counts 1 every 10 ticks. She kicks out once both are above 0. In
     practice she survives a deficit of up to about 28% of her maximum HP.
   - With **Calm 0 or less**, her Calm recovers instead (1/32 of maximum body or head HP per 3 ticks),
     and she kicks out as soon as it reaches 1, whatever her HP.
   - **Count 3 ends the match.**
9. **How a match ends.** Only by **pinfall** or **submission**. There is no KO, count-out, time limit or
   draw; the turn counter only feeds the match time shown afterwards. The winner is the side attacking
   when it ends, which is the side that made the pin or the hold.

### What wins matches
- **Opponents don't get stronger.** Each computer wrestler's record is fixed in the ROM and loaded
  unchanged for every match, from the debut (year 2, July 24, against Aono) to the final (year 7,
  March 31, Kandori at the Tokyo Dome). The table below lists the main story opponents.
- **Her biggest handicap is Calm.** Her Max Calm is always 100, while the computer wrestlers start
  with 160-250. As long as an opponent's Calm is higher than hers, the opponent's landed moves can't be
  countered, while her own landed moves can be. Nothing the player does changes this. Her own
  advantage is a full move list from the start, while the opponent unlocks her strongest moves only as
  her Calm runs down.
- **Pro Wrestling is worth the most.** It is a hit stat in 181 moves (fewer misses means fewer counters
  against her), an evasion stat in 158 (more misses by the opponent means more counters for her), and
  the main requirement for moves, which gives her more moves and more counters. A full training plan
  reaches 255 around the debut.
- **Head and body HP** absorb the damage that sets up pins (forced pins and kick-outs both look at head
  and body HP), and a higher maximum recovers faster during a count.
- **Str and Suplexes** unlock and power the throws and drivers that end in pins: that is how she wins.
  **Holds** win by submission, but most opponents have high Guts.
- **Flex, Speed and Falls** are evasion stats: each miss by the opponent is a guaranteed counter for
  her if she has one.
- **For the final against Kandori:** her moves are mostly holds on the **right arm, right leg and head**
  (armbars, heel holds, sleepers), with Tiger Driver as her only pin move once her Calm is 50 or less.
  **Guts** and **arm, leg and head HP** decide whether the heroine taps out.
- **Not worth chasing for matches:** Dex (only the first attack, and only Strong vs Strong), Fame,
  the registered counter (its +20 bonus is bugged, see below), Calm (fixed), and the stats listed as
  having no effect.

**Main story opponents** (record values; PW = Pro Wrestling):

| Wrestler | PW | Speed | Flex | Dex | Head HP | Body HP | Max Calm | Moves |
|---|---|---|---|---|---|---|---|---|
| Aono | 100 | 200 | 120 | 110 | 150 | 220 | 200 | 25 |
| Shimamura | 150 | 140 | 200 | 130 | 180 | 213 | 230 | 23 |
| Endo | 170 | 60 | 90 | 80 | 200 | 230 | 210 | 32 |
| Carol | 190 | 180 | 200 | 180 | 200 | 220 | 200 | 31 |
| Nakayama | 130 | 220 | 140 | 120 | 160 | 200 | 200 | 23 |
| Kurenai | 210 | 150 | 180 | 190 | 200 | 230 | 210 | 29 |
| Handa | 230 | 190 | 220 | 200 | 180 | 200 | 230 | 28 |
| Harley | 230 | 230 | 200 | 200 | 220 | 230 | 200 | 26 |
| Kudo | 240 | 220 | 240 | 250 | 200 | 230 | 240 | 32 |
| Tateno | 250 | 200 | 180 | 190 | 160 | 200 | 220 | 34 |
| Kagono | 140 | 200 | 220 | 210 | 200 | 200 | 220 | 15 |
| **Kandori** (final) | 150 | 200 | 200 | 200 | 210 | 220 | 200 | 19 |

Kandori also has Guts 250 and Holds 250.

### Bugs (from the code)
- A negative hit chance passes the 99% cap as a huge number, so it becomes 99%.
- A miss with no counter available still lands.
- The counter chance on a hit is worked out with the roles swapped: the countered wrestler's stats are
  added and the counterer's subtracted. A strong attacker is countered slightly more often on her hits.
- The registered counter's +20 is checked against the attacker's registered counter, so the heroine's
  own registered counter never gets it.
- Calm costs paid through counters have no floor, so Calm can go below 0.
- Computer wrestlers' Str is loaded as the average of the wrong bytes, and their style from the wrong
  byte (the first attacker then comes from unrelated memory). Heel vs Heel also reads unrelated memory.
- The heroine's style check considers only Strong and Entertainment.
- *Uncertain:* some moves need positions that no code seems to produce (all Avalanche moves, Back
  Elbow, Knee Lift and others), so they may never be used; and a pin made by a counter (Pin, Roll-Up,
  Side Cradle) may never start a count. Both need a check in an emulator.

## Story, routes and endings
*From the code: all 386 events were parsed. Not yet seen in play.*

- **No story event tests a stat.** Every branch in the event scripts tests one of two things: **which
  side won the last match**, or **the last menu choice**. Fame, wrestler type, Figure, Singing and so on
  never lock or unlock anything.
- **Route choices:**
  - After turning pro (April), you choose whose attendant to be: **Carol Midori** or **Kurenai Yasha**.
  - On the Kurenai route, **winning** the March match leads to an offer to transfer to **FMW**. Staying
    continues the Kurenai route; transferring starts the FMW route. A later FMW-route choice (go to
    Michinoku Pro, or not) only changes scenes.
  - Story events also change who appears in your partner list.
- **Endings:** every route ends on March 31 at the Tokyo Dome against Shinobu Kandori. The shared ending
  text and staff roll follow, then one of **four epilogues**:

  | Route | Final match | Epilogue scene |
  |---|---|---|
  | Carol or Kurenai | won | s192 (Kandori passes on "strongest"; JWWF and LLPW reunite) |
  | Carol or Kurenai | lost | s193 |
  | FMW | won | s194 |
  | FMW | lost | s195 ("changing of the guard") |

  So the endings are locked only by the **route** and by **winning the final match**. Stats decide the
  ending only by deciding whether you win.
- **Possible story bug:** on the Carol route, losing the September 15 match against Kotori Kagono calls
  the wrong follow-up event. It replays the pre-match scene and books the same match again, so the
  story may loop until you win. The other routes handle their equivalent correctly. *Needs an emulator
  test.*
- **Cut content:** an event chain (scenes s165, s179-s183) that nothing starts, and nine scenes no event
  plays (s083, s085, s118, s133, s166, s173-s175, s186).
- **Possible debug inputs (unverified):**
  - Holding exactly Up+R on controller 1 at the right moment runs event 0xFFFF, which sets the stats
    to 200 (`$04:83C7`).
  - Holding exactly Y+Down+R during a match ends it after the current turn (`$06:F01C`, checked once
    per turn). The winner is the side that made the last move (`$06:F210`: `$7E:7E74` = attacker
    slot ÷ 2), so it is not an automatic win for the heroine.

## Reference tables

Effects use the stat names above. "R Arm HP" and the like are the hidden body-part stats that make
up HP and Str. "Hidden growth" and "hidden weight" feed the Height and Weight formulas.

### Exercises
"Listed cost" is the exercise's own Stamina cost (see the bug above for what is really charged).

| # | Exercise | Listed cost | Effects on success |
|---|---|---|---|
| 1 | Side Raise | 2 | +2 R Arm Str, −1 Flex, +1 Stress, −1 R Arm HP, −1 L Arm HP, +2 L Arm Str |
| 2 | Push-ups | 1 | +2 R Arm HP, −1 Speed, +1 Flex, +1 Stress, +2 L Arm HP, −1 R Arm Str, −1 L Arm Str |
| 3 | Front Raise | 1 | +3 R Arm Str, −1 Speed, −1 Dex, −2 R Arm HP, −2 L Arm HP, +3 L Arm Str |
| 4 | Rope Climbing | 4 | +3 R Arm HP, +3 L Arm HP, +1 Flex, −2 R Arm Str, −2 L Arm Str, +1 Aerial |
| 5 | Bridge | 1 | +2 Head Str, +2 Flex, +2 Head HP, +1 Suplexes |
| 6 | Cable Crunch | 2 | +2 Body Str, −1 Flex, −1 Body HP |
| 7 | Sit-ups | 2 | +3 Body HP, −1 Dex, +1 Figure, +1 Body Str |
| 8 | Punch | 1 | +1 Punch, +1 Dex |
| 9 | Hindu Squats | 2 | +2 R Leg Str, +2 L Leg Str, +1 Speed, +1 Stress, −1 R Leg HP, −1 L Leg HP, +1 Body HP |
| 10 | Jump Rope | 1 | +2 R Leg HP, +2 L Leg HP, +1 Speed, +1 Dex, +1 Body HP, −1 R Leg Str, −1 L Leg Str |
| 11 | Kicks | 2 | +1 Kicks, +1 Flex |
| 12 | Aerobics | 3 | +2 Figure, +1 Speed, +1 Flex, +2 Body HP |
| 13 | Sparring | 3 | +1 Dex, +1 Flex, +1 Guts, +1 Pro Wrestling, +1 Holds, +1 Falls |
| 14 | Falls | 2 | +1 Falls, −1 Flex |
| 15 | Abdominal Tap | 2 | +2 Body HP |
| 16 | Running | 3 | +1 Body HP, −2 hidden weight, +1 Speed, +1 Guts |


### Partners
"Real cost" is the Stamina actually charged per training day ("+?" = plus an unpredictable amount, see the bug above). "Part HP / Str" is the total change to the six body parts on a day when every exercise applies. Ids are the game's person ids.

| Id | Partner | Real cost | Body HP / Str per day | Exercises (in order) | Daily bonus |
|---|---|---|---|---|---|
| 0 | Carol Midori | 3 | +8 / +1 | Rope Climbing, Sit-ups, Hindu Squats | +1 Aerial, +1 Lucha, +1 Suplexes, +1 Entertainment |
| 1 | Combat Toyoda | 7 | −1 / +8 | Side Raise, Hindu Squats, Falls, Abdominal Tap | +1 Pro Wrestling, +1 Rough, +1 Power, +1 Heel |
| 2 | Crusher Maedomari | 6 | +3 / +5 | Push-ups, Front Raise, Sit-ups | +1 FMW, +1 Rough, +1 Power |
| 8 | Eagle Sawai | 8+? | −4 / +8 | Front Raise, Cable Crunch, Punch, Running | +2 Pro Wrestling, +1 Rough, +1 Power, +1 Heel |
| 9 | Mizuki Endo | 9 | −7 / +12 | Side Raise, Front Raise, Cable Crunch, Punch | +2 Pro Wrestling, +1 Falls, +1 Power |
| 10 | Miki Handa | 5 | +6 / +0 | Push-ups, Bridge, Falls | +1 Pro Wrestling, +1 Falls, +2 Suplexes, +1 Babyface |
| 12 | Yukari Ishikura | 4+? | +7 / −4 | Rope Climbing, Kicks, Running | +1 Karate, +1 Lucha, +1 Entertainment, −1 Strong |
| 13 | Keiko Iwami | 3 | +2 / +0 | Aerobics | +1 Punch, +1 Karate, +1 Babyface, +1 Heel |
| 14 | Jenne Yukari | 9 | +2 / +2 | Bridge, Punch, Kicks, Sparring | +1 Kicks, +1 Kickboxing, +1 Strong, +1 Entertainment, −1 Power |
| 15 | Shinobu Kandori | 7 | +2 / +0 | Punch, Sparring, Abdominal Tap | +1 Judo, +1 Holds, +1 Strong, −1 Babyface |
| 16 | Megumi Kudo | 5+? | +12 / −2 | Push-ups, Bridge, Jump Rope, Running | +1 Pro Wrestling, +1 Aerial, +1 Strong, −1 Entertainment |
| 17 | Kurenai Yasha | 9 | −6 / +12 | Front Raise, Cable Crunch, Hindu Squats, Sparring | +2 Rough, +1 Heel |
| 18 | Leo Kitamura | 8+? | +14 / −6 | Rope Climbing, Punch, Jump Rope, Abdominal Tap, Running | +2 Aerial, +1 Lucha, +1 Entertainment |
| 19 | Yukie Nabeno | 3+? | +7 / −4 | Rope Climbing, Falls, Running | +1 FMW, +1 Strong |
| 20 | Michiko Nagashima | 6 | +15 / −8 | Push-ups, Rope Climbing, Jump Rope, Sparring | +1 Aerial, +2 Rough, +1 Strong, +1 Heel, −1 Power |
| 21 | Kaori Nakayama | 5 | +4 / −2 | Push-ups, Sparring, Falls | +1 Pro Wrestling, +1 Aerial, +1 Entertainment |
| 22 | Nurse Nakamura | 10 | +1 / +4 | Front Raise, Jump Rope, Sparring, Falls | +1 Pro Wrestling, +1 Entertainment |
| 23 | Mikiko Futagami | 7+? | +2 / +6 | Bridge, Hindu Squats, Sparring, Falls, Running | +2 Pro Wrestling, +1 Strong, +1 Power |
| 24 | Michiko Omukai | 10 | −2 / +15 | Side Raise, Front Raise, Sit-ups, Hindu Squats, Aerobics | +1 Punch, +1 Aerial, +1 Babyface |
| 25 | Harley Saito | 8 | +7 / +2 | Rope Climbing, Bridge, Hindu Squats, Sparring, Falls | +1 Pro Wrestling, +1 Kicks, +1 Karate, +1 Suplexes, +1 Justice, +1 Strong |
| 26 | Miwa Sato | 6 | +6 / +3 | Side Raise, Sit-ups, Jump Rope, Falls | +1 Falls, +1 Babyface |
| 27 | Mayumi Shimizu | 8 | +7 / −2 | Jump Rope, Kicks, Aerobics | +1 Sambo, +1 Holds, +1 Strong |
| 28 | Rumi Kazama | 9 | +7 / +2 | Rope Climbing, Bridge, Hindu Squats, Kicks, Sparring | — |
| 29 | Shark Tsuchiya | 8 | +4 / +3 | Cable Crunch, Sit-ups, Punch, Abdominal Tap | +1 FMW, +1 Rough, +1 Strong |
| 30 | Noriyo Tateno | 6 | +12 / −4 | Push-ups, Rope Climbing, Bridge, Falls | +1 Pro Wrestling, +1 Aerial, +1 Suplexes, +1 Rough, +1 Strong, +1 Entertainment |
| 31 | Tsuppari Mac | 9 | +11 / +1 | Push-ups, Bridge, Sit-ups, Punch, Aerobics | +1 Rough, +1 Heel, −1 Babyface |
| 32 | Yoshiaki Fujiwara | 4 | +0 / +0 | Sparring, Falls | +3 Fujiwara-gumi, +1 Entertainment, −1 Power |
| 34 | Yuki Ishikawa | 6 | +14 / +1 | Push-ups, Rope Climbing, Bridge, Sit-ups, Hindu Squats | +1 Holds, +1 Strong, −1 Heel |
| 35 | Atsushi Onita | 1 | −1 / +4 | Hindu Squats | +3 FMW, +1 Strong, +1 Babyface |
| 36 | Jun Yamashita | 0 | +0 / +0 | — | +2 Aerial, +1 Babyface |
| 37 | Keiko Aono | 10 | +2 / +0 | Punch, Kicks, Sparring, Abdominal Tap | +1 Punch, +1 Kicks, +1 Kickboxing, +1 Strong |
| 38 | Hatsumi Tawada | 0 | +0 / +0 | — | +1 Rough, +1 Strong, −1 Babyface |
| 39 | Tarzan Goto | 0 | +0 / +0 | — | +1 FMW, +1 Falls, +1 Rough, +1 Power |
| 43 | Great Sasuke | 6 | +10 / −2 | Rope Climbing, Hindu Squats, Jump Rope, Sparring | +1 Pro Wrestling, +3 Lucha, +1 Strong, −1 Heel |
| 44 | Super Delfin | 6 | +12 / −4 | Push-ups, Rope Climbing, Bridge, Punch | +2 Lucha, +2 Suplexes, +1 Entertainment, −1 Strong |
| 45 | Jinsei Shinzaki | 0+? | +1 / +0 | Running | +2 Pro Wrestling, +1 Power, −1 Babyface |


### Day-off places

| Place | Effects |
|---|---|
| Dining | +5 hidden weight, −1 Figure, −10 Stress |
| Movies | +1 R Arm HP, +1 Fame, −5 Stress, +3 Acting, +2 Focus |
| Running | −20 Stamina, +3 Speed, +1 Guts, +2 R Leg HP, +2 L Leg HP, +1 Focus |
| Full Rest | — |
| Kick Gym | −20 Stamina, +3 Punch, +2 Kicks, +5 Kickboxing, −1 Falls |
| Judo Dojo | −20 Stamina, +1 Guts, +5 Judo, +3 Holds, +3 Falls |
| Karate Dojo | −20 Stamina, +3 Punch, +2 Kicks, +5 Karate |
| Swimsuit Shop | — |
| Hair Salon | +1 Figure |
| Karaoke Box | −20 Stress, +5 Singing |
| Pool | −20 Stamina, −1 Flex, +10 Figure, +5 Body HP |
| Shopping | −10 Stress, +2 Dex, +5 Focus |
| Sambo Club | −10 Stamina, +3 Body HP, +8 Sambo, +2 Holds, +1 Suplexes, −5 Stamina, +2 Flex, +5 Figure |
| Aerobics Gym | −5 Stamina, +2 Flex, +5 Figure |


### Clubs
Per school year.

| Club | Part HP / Str (sum) | Other effects |
|---|---|---|
| Go-Home Club | +0 / +0 | — |
| Track Club | +3 / +0 | +1 Speed, +1 Guts, −1 hidden weight, −1 Figure, +1 Jumping |
| Bodybuilding | +0 / +6 | −1 Speed, +1 hidden weight, +1 Figure, −1 Jumping, +1 Power |
| Table Tennis | +1 / +1 | +1 Speed |
| Yoga Club | +0 / +0 | +1 Focus, −1 hidden weight, +1 Figure, +2 Max Calm |
| Archery Club | +0 / +3 | +3 Focus, +3 Max Calm |
| Street Gang | −1 / +0 | −1 Focus, +5 Guts, −1 Fame, −2 Max Calm, −2 Justice, +1 Heel |
| Idol | +6 / −6 | +1 Fame, +1 Figure, −1 Acting, +1 Singing, +1 Entertainment |
| Student Council | +0 / +0 | +1 Guts, +4 Fame, +1 Max Calm, +1 Justice, +1 Acting |
| Volleyball | +5 / +5 | +1 Speed, +4 hidden growth, +1 Jumping |
| Movie Club | +0 / +0 | −1 Speed, +2 Focus, +4 hidden weight, −1 Jumping |
| Aerobics | +6 / +0 | +1 Speed, −1 hidden weight, +3 Figure, +1 Jumping, +1 Acting |
| Taekwondo | +6 / +6 | −1 Fame, +1 Jumping, +1 Max Calm |
| Boxing Club | +6 / +0 | +1 Speed, −1 Fame, −1 Figure |
| Aikido Club | +6 / +0 | +1 Focus, −1 Fame, −1 Figure, +1 Max Calm |
| Wrestling | +6 / +6 | −1 Fame, −1 Figure |
| Gymnastics | +6 / +6 | +1 Speed, −1 hidden weight, +1 Jumping, +1 Acting |
| Abacus Club | +1 / +1 | — |
| Hiking Club | +3 / +0 | — |
| Cooking Club | +0 / +0 | +1 hidden weight |
| Pottery Club | +2 / +2 | — |
| Basketball | +6 / +6 | +1 Speed, +1 Focus, +2 hidden growth, −2 Figure, +1 Jumping |
| Kendo Club | +0 / +0 | +1 Focus, +1 Max Calm |
| Calligraphy | +0 / +0 | +2 Focus, +1 Max Calm |
| Ethics Club | +2 / +0 | −2 Fame, −1 Max Calm, +2 Justice |
| Drama Club | +6 / +0 | +3 Acting, +1 Entertainment |
| Chorus Club | +4 / +0 | +4 Singing |
| Judo Club | +6 / +6 | −1 Fame, +2 hidden weight, −1 Figure |
| Karate Club | +6 / +6 | +1 Guts, −1 Fame, −1 Figure |
| Kung Fu Club | +6 / +0 | +1 Speed, −1 Fame, +1 Jumping, +1 Max Calm |
| Ballet Club | +6 / +0 | +1 Speed, −1 Fame, +1 Jumping, +1 Acting |
| Softball | +6 / +3 | +2 Jumping |
| Soccer Club | +8 / +6 | +1 Speed, +1 Jumping |
| Trekking | +6 / +6 | +1 Guts, −1 Figure, +1 Max Calm |
| Rhythmic Gym | +6 / +0 | +1 Speed, +1 Jumping, +1 Acting |
| Swim Club | +7 / +12 | −1 Figure |
| Cheerleading | +6 / +0 | −1 hidden weight, +1 Jumping, +1 Singing, +1 Entertainment |
| Tennis | +6 / +8 | — |
| Arm Wrestling | +1 / +5 | −1 Speed, +1 Focus, −1 Figure, +1 Power |
| Light Music | +0 / +0 | +2 Fame, +2 Singing |
| Brass Band | +2 / +3 | +1 Singing |
| Art Club | +0 / +2 | +1 Focus |
| Manga Club | +0 / +0 | −1 Speed, +1 Focus, −1 Justice |
| Tea Ceremony | +0 / +0 | +2 Focus, +2 Max Calm |
| Ikebana | +0 / +0 | +1 Focus, +1 Max Calm |
| Shrines&Temples | +2 / +0 | +1 Guts, −1 Fame |
| Handicrafts | +2 / +0 | +1 Guts |
| Japanese Studies | +1 / +1 | +1 Focus, +1 Singing |
| Gardening | +1 / +1 | −1 Fame |
| Old Martial Arts | +6 / +6 | +1 Guts, −1 Fame, −1 Figure, +1 Max Calm |

## Technical reference
CPU addresses (LoROM). The game is compiled C: functions use a stack frame, and data is reached through
24-bit pointer variables kept in ROM around `$1F:E3C7`-`$1F:E50F`.

**RAM**
- Heroine stats: 16-bit words at `$7E:791D + 2 × index`. Labels: pointer table `$1F:B7FC` (same index).
  Indices: 0 Speed, 1 Flex, 2 Dex, 3 Guts, 4 Fame, 5 hidden growth, 6 hidden weight, 10-15 part HP
  (R arm, L arm, R leg, L leg, head, body), 16-21 part Str, 22-37 techniques and styles, 38 Max Calm,
  39 Justice, 40 Strong, 41 Entertainment, 42 Babyface, 43 Power, 44 Heel, 48 Stamina, 49 HP, 50 Str,
  51 Height, 52 Weight, 53 Figure, 54 Stress, 55-59 move counts, 61-66 injuries, 76 Calm, 77 Acting,
  78 Singing, 79 Focus, 98-101 blood-type values (never read), 104 lost-day streak (no label).
- Month day records: `$7E:7CD1`, 8 bytes each `{day, weekday, type, param}`. Type 2 = training (param =
  partner id, 255 = not set), 8 = day off, 1 = event.
- Profile: `$7E:7E16` blood type (A, B, O, AB = 0-3), `$7E:7E1A` zodiac sign (0-11), `$7E:7E22` club
  history (10 × u16 club index; the screen shows nine years).

**Code**
- `$04:E29C` month of training: copies the stats to `$7E:7B1D`, calls `$04:DAD1` per week, recalculates
  derived stats (`$05:B568`) and prints the changes for the stats flagged in `$1F:BE08`.
- `$04:DAD1` one week: the rules in [A training day](#a-training-day). The cost loop indexes the
  exercise table with the 1-based list byte without subtracting 1 (the apply loop does subtract it),
  which is the cost bug; byte 16 (Running) reads the pointer past the table, `$10:0202`, a WRAM mirror.
- `$04:CE11` applies an effect list `{op, stat, amount}…, 0`: op 1 set, 2 add, 3 subtract; bit 7 makes
  the amount random (`rand × amount >> 8`). `$04:CD43(cmd 0x28/0x29/0x2A, stat, value)` = set / add
  (capped at 255) / subtract (floored at 0).
- `$04:E8D2` day off: applies the place's effect list, then the Stamina refill, capped at HP.
- `$05:D9E6` new wrestler (end of the profile screen): clubs, sign, blood type, then Stamina = HP.

**Data**
- Exercises: `$1F:B382`, 16 pointers to `{cost, effects…, 0}`. Names: `$1F:B4CE`.
- Partner exercise lists: `$1F:AFD0`, 46 pointers (by person id) to 1-based exercise bytes ending in 0.
- Partner daily bonus: `$1F:B12E`, 46 pointers to effect lists.
- Day-off places: `$1F:A053`, 14 pointers to effect lists, in the menu's order. Open places:
  `$04:E709` sets the flags at `$7E:7C85` (one word per place) for the first N places, N = the byte
  at `$1F:A015` + (year `$7E:7E68` − 94, minus 1 in January-March; month `$7E:7E6C`), then clears
  some of them by the six words at `$7E:79BD`. The menu (`$04:E9CC`) lists the flagged places.
- Clubs: `$1F:A7FD`, 29 signed bytes per club, added to the stats listed (u16 indices) at `$1F:A7C3`.
  Afterwards any of those stats at 128 or more (or below 0) is set to 0.
- Zodiac signs: `$1F:A122`, 12 effect lists. Blood types: `$1F:A18B`, 4 effect lists.

**Matches** (bank `$06`)
- `$05:F78C` calls the match loop `$06:DB26`. Wrestler ids go in `$7E:7E84/86/88/8A`: slots 0-1 are
  side A and 2-3 side B; the heroine is id `0x0B`. The fighter records are loaded by `$06:801A`; for
  the heroine, `$06:86AB` copies her stats into `$7E:7F70 + 0x80 × slot` in the order of the list
  `$1F:C855`. Per-slot state: `$7E:7F3C + 10 × slot`.
- Turn `$06:CB61`: move choice `8F28`, hit chance `8C6C`, counter choice `A1DE`, counter chance `A02B`,
  damage and submission `AC76`, pin count `D7DA`. Usable moves are rebuilt by `$06:8984` from the stat
  requirements. Her in-match style is set at `$06:88BA`, and the who-moves-first table is `$1F:AFB2`.
- Loop `$06:DE19`: `$19` = submission (`DE42`, from `CB61`/`AC76`), `$1B` = pin count 3 (`EDD9`, count
  `D7DA`, started when the defender's posture (state+2) is 6, `ED43`); sides swap after a counter
  (`DF2B`); tag-in `E7A2`. Winner `$06:F210`: `$7E:7E74` = attacker slot ÷ 2.
- Hit roll `CB97`, counter gate and flags `CDA9`-`CF77` (`$7E:83E0` landed, `$83E4` countered, `$83DC`
  counter id); common counters `$1D:EC5B`. Computer move lists: `$1D:8010` → `$1D:F31D`, 4-byte
  pointers by wrestler id to {move, Calm threshold} pairs. Computer records: `$1D:800C` → `$1D:EC89`,
  50-byte records (+2C registered counter).
- Move table `$1D:8014`, 41-byte records; names via `$1D:D10D`. Fields: +04 requirements, +08 damage
  targets, +0C power list (stat, %), +10 base chance, +11 attacker hit stats, +15 defender evade stats,
  +19 counters, +21 Calm cost, +26/+27 posture before and after. Stat codes map to stat words via
  `$1F:C805`.
- Result: `$06:F213` sets `$7E:7E74` = the winning side. Fame changes: `$06:D117` (+2), `$06:F0FA` (+5),
  `$06:FAB5` (+10 win), `$06:FAD2` (−5 loss).
- `$07:95D0` / `$06:8658` save and load the heroine in the versus-mode wrestler bank (SRAM `$70:1000`,
  `0x91` bytes each).

**Events** (story script)
- Table `$1A:8000` (0x400 × 24-bit pointers; 386 used), run by `$05:9FE5`. An event is a 2-byte id, then
  entries `{length, opcode, operands}` up to `$FF`. Opcodes:
  - `11` backdrop, `12` scene, `13` two-option menu (result → `$7E:7E78`), `14` music.
  - `15` queue an event on a date (queue `$7E:7E8C`), `16` call an event.
  - `17`-`19` message window, `1A` screen effect, `1B` the event uses up the day, `1C` sound, `1D` wait.
  - `28`/`29`/`2A` set/add/subtract, by class (`$05:9DB1`): `20` heroine stat, `21` a person's talk
    scene, `22` partner availability (`$7E:78C1[person]`), `23` make a calendar day a match day, `24`
    match card slot, `3A` `$7E:7E78`.
  - `30` compare (op `31` ==, `32` >, `33` >=, `34` <, `35` <=, `36` !=; variable `38` = `$7E:7E74`, `39` =
    date, `3A` = `$7E:7E78`, else a stat): a false test skips the next entry.
- Event `E000` (the first after character creation) sets Max Calm to 100 and makes Carol, Handa,
  Futagami, Omukai, Harley and Aono available as partners.
- Ending: after the final match `$05:F827` sets stat 125 to stat 126 (the heroine is first on the winning
  side) or stat 127; `$06:F33E` then runs `$07:C394`, which shows the ending pages (`$1F:CA46`) and runs
  event `0x258 + stat 125`.

## Open questions
- Confirm the match rules and bugs listed under [Matches](#matches) in a real match (no match savestate
  yet), above all that an uncountered miss lands, and the moves that may never be used.
- Confirm the possible Carol-route loop after losing on September 15, and the two debug inputs.
- Whether every club is offered in every school year.
- What the Swimsuit Shop and Hair Salon change, beyond Figure, and what the Advice menu changes (likely
  only which dialogue plays).
