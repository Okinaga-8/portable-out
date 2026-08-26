# MiniMax H3(Hailuo 03)プロンプト設計メモ

顔アップから全身ターンアラウンドまで、3ショット構成の映像を出すための
プロンプト設計メモ。

- 1〜6章: Shot 1(顔の正面を画面いっぱいに映す超クローズアップ)
- 7章: Shot 2(全身の立ち姿・3秒静止)
- 8章: Shot 3(回転して側面2秒静止 → さらに回転して3秒静止)
- 9章: Shot 1 → 2 → 3 を1本に通す全体プロンプト

---

## 1. なぜ「寄り」にならないのか

指定しても引いた絵になる原因は、だいたいこの2つ。

1. **カメラを指定しないと勝手に動く**
   H3 はカメラ指定がないと、継続的なドリフト(緩やかな移動)とリフレーミングを
   自分で入れる。「書かない＝おまかせ」ではなく「書かない＝勝手に動く」なので、
   固定したいなら固定と明記する。

2. **全身の情報を書くと、それを写そうとして引く**
   被写体定義に服装・靴・体型を書き込むと、クローズアップの指定が効かなくなる。
   顔アップにしたいときは、被写体の描写を顔の中だけに絞る。

---

## 2. 使う語彙

| 目的 | 書き方 |
|---|---|
| ショットサイズ | `extreme close-up`(顔が画面いっぱい)。`close-up` だと胸〜肩が入る |
| 画面を埋める明示 | `the face fills the entire frame edge to edge` / `occupies most of the frame` |
| さらに寄せる | `forehead and chin cropped by the frame edges` / `almost no headroom` / `shoulders out of frame` |
| 正面 | `straight-on frontal angle` / `facing the camera directly` / `eye level` / `symmetrical composition` |
| 視線 | `looking directly into the lens`(カメラ目線が欲しいとき) |
| カメラ固定 | `static shot, locked-off, no push in, no zoom, no pan — the frame never moves` |
| レンズ | `85mm lens, shallow depth of field`(広角だと顔が歪む。寄りたいだけなら 85〜135mm 相当) |

### ショットサイズの目安

```
medium shot          腰から上
medium close-up      胸から上
close-up             肩から上(顔以外もそこそこ入る)
extreme close-up     顔が画面を埋める  ← 目的はここ
macro                目や唇だけ
```

### 書かないこと

服装・靴・部屋・風景などの環境描写は、書くほど画角が引く。
描写するのは顔の中だけにする(肌の質感、毛穴、まつげ、眉、生え際、汗、瞳の映り込み)。

---

## 3. そのまま使えるプロンプト

### 静止・カメラ目線

```
Extreme close-up, straight-on frontal portrait, eye level. A woman in her
late twenties faces the camera directly, her face filling the entire frame
edge to edge — the top of her forehead and her chin are cropped by the frame
edges, almost no headroom, shoulders out of frame, background not visible.
Symmetrical composition, eyes on the horizontal centerline, looking directly
into the lens. Skin texture, fine hairs and pores clearly visible. She blinks
slowly once, then the corners of her mouth lift slightly.
Static shot, locked-off camera, no push in, no zoom, no pan — the frame never
moves. 85mm lens, shallow depth of field, soft even frontal key light.
```

### 引きから寄る(プッシュイン)

一発で寄り切らないときは、動きで寄せると安定する。

```
Close-up of the man's face, straight-on, eye level. The camera slowly pushes
in over three seconds until his face fills the entire frame, forehead and chin
cropped by the frame edges. He keeps looking directly into the lens, expression
unchanged. 85mm lens, shallow depth of field.
```

---

## 4. 構造化フォーマットで書く場合

自由文でも通るが、フィールドを分けた記法のほうが安定する。

```
[subject_definitions]
<Subject 1>: A woman in her late twenties. Face only: fair skin with visible
pores, thick straight eyebrows, dark brown eyes, black hair pulled back off
the forehead. Do not describe clothing or body.

[summary]
A locked-off extreme close-up of <Subject 1>'s face filling the frame,
looking straight into the lens.

[detailed_description]
[Shot 1] Extreme close-up, frontal, eye level. <Subject 1>'s face fills the
frame edge to edge; forehead and chin are cropped by the frame edges;
shoulders and background are not visible. She blinks once slowly, then the
corners of her mouth lift slightly. Static shot — the camera does not move.
85mm lens, shallow depth of field, soft frontal key light.

[overall_soundscape]
Quiet room tone, a faint breath.

[non_diegetic_music]
None.
```

**ポイント**: `subject_definitions` に顔の情報しか入れないこと。ここに服を書くと引く。

### 主なフィールド

| フィールド | 中身 |
|---|---|
| `subject_definitions` | 登場人物・オブジェクトの定義(参照画像がある場合はその対応づけも) |
| `summary` | ショット全体の一文要約 |
| `retention_analysis` | 参照素材から保持したい特徴(髪型・衣装・体型など) |
| `detailed_description` | ショット単位の詳細記述。`[Shot 1]` のように区切る |
| `overall_soundscape` | 環境音・実際に鳴っている音 |
| `non_diegetic_music` | BGM(観客にだけ聞こえる音楽)。不要なら不要と明記する |

シンプルな T2V/I2V では `integrated_multimodal_description` /
`overall_soundscape` / `non_diegetic_music` の3フィールド構成でも書ける。

---

## 5. 補足とハマりどころ

- **画像から生成(I2V)する場合**
  元画像がバストアップだと、それ以上寄らないことがある。確実なのは元画像を
  あらかじめ顔アップにトリミングしておくこと。難しければプッシュインで寄せる。

- **アスペクト比の影響が大きい**
  9:16(縦)は顔が自然に埋まる。16:9(横)は左右に余白が出るので、横で埋めたいなら
  `the face fills the frame horizontally, hair and ears touching both edges`
  のように横方向を明示する。

- **否定形より肯定形**
  `no background` より
  `the background is not visible, only skin fills the frame` のほうが通りやすい。

- **カメラ語彙は英語で**
  日本語プロンプトも通るが、`static shot` などの専門語は英語のほうが安定する。

- **公式ガイドのカメラ語彙**
  Zoom In/Out, Push In/Pull Out, Pan Left/Right, Truck Left/Right,
  Tilt Up/Down, Pedestal Up/Down, Arc Shot, Tracking Shot, Static Shot,
  Shake Slightly/Strongly, POV, Roll Clockwise/Counterclockwise
  この語彙の中の単語を使うと解釈が安定する。

- **寄りと引きを1本に混ぜない**
  クローズアップと引きを同居させたいときは、プロンプトを分けて2回生成するか、
  引きのあとにプッシュインで顔へ寄せる形にする。

- **まず5秒で試す**
  15秒の複雑なプロンプトをいきなり作らず、短尺で画角だけ確認してから伸ばすと
  原因の切り分けがしやすい。

---

## 6. うまくいかないときのチェックリスト

| 症状 | 対処 |
|---|---|
| 引いた絵になる | 服装・背景・環境の描写を削る。`extreme close-up` + 画面を埋める明示句を入れる |
| 画角が勝手に動く | `static shot, locked-off, the frame never moves` を明記する |
| 顔が斜めを向く | `straight-on frontal angle` `facing the camera directly` `symmetrical composition` を足す |
| 顔が歪む | レンズ指定を広角から `85mm` 〜 `135mm` に変える |
| 左右に余白が出る | 縦(9:16)にする、または横方向を埋める指定を足す |
| 途中で引いてしまう | 尺を短くする。カメラ固定を文中で繰り返す |

---

## 7. Shot 2:全身の立ち姿(3秒静止)

Shot 1(顔の超クローズアップ)から、一気に全身の立ち姿へ切り替える場合。
頭からつま先までが上下にわずかな余白を残して画角のほぼ全体に入り、
そのまま3秒間静止するショット。

### いちばん失敗するポイント

H3 は放っておくと**カットにならず、顔からズームアウトして全身に引いていく**。
「切り替わる」ではなく「引いていく」動きになるので、カットであることを
明示的に書いて潰す必要がある。

```
HARD CUT — an instant cut, not a transition. The camera does not pull out,
does not zoom out, does not travel from the face to the body. No dissolve,
no fade, no morph. One frame is the close-up, the next frame is the full
body shot.
```

### Shot 2 単体のプロンプト

```
Full body shot, straight-on frontal, camera at chest height, lens level
(not tilted down). The same woman stands facing the camera, her entire body
visible from the top of her head to the soles of her shoes. The figure fills
almost the full height of the frame — only a small margin of empty space above
her head and below her feet, nothing cropped at any edge.
She wears a plain white button-down shirt tucked into straight-leg indigo
jeans and white leather sneakers. Arms relaxed at her sides, feet
shoulder-width apart, weight even on both legs, chin level, looking directly
into the lens.
She holds this pose completely still for three seconds — no steps, no
gestures, no turning, no weight shift; only the faint rise and fall of her
breathing.
Static shot, locked-off camera, no push in, no pull out, no zoom, no pan, no
tilt — the frame never moves. 50mm lens, deep focus, plain seamless light grey
studio backdrop, soft even frontal light, full-length soft shadow on the floor.
```

### Shot 1 → Shot 2 を1本で繋ぐ場合

```
[Shot 1] Extreme close-up, straight-on frontal portrait, eye level. A woman in
her late twenties faces the camera directly, her face filling the entire frame
edge to edge — forehead and chin cropped by the frame edges, shoulders out of
frame. Looking directly into the lens. She blinks slowly once. Static shot,
locked-off, the frame never moves. 85mm lens, shallow depth of field.

HARD CUT — an instant cut, not a transition. The camera does not pull out,
does not zoom out, does not travel from the face to the body. No dissolve,
no fade, no morph. One frame is the close-up, the next frame is the full body
shot.

[Shot 2] Full body shot, straight-on frontal, camera at chest height, lens
level. The same woman stands facing the camera, her entire body visible from
the top of her head to the soles of her shoes, filling almost the full height
of the frame with a small margin above her head and below her feet. Plain white
button-down shirt, straight-leg indigo jeans, white sneakers. Arms relaxed at
her sides, feet shoulder-width apart, chin level, looking into the lens.
She holds the pose completely still for three seconds — only faint breathing.
Static shot, locked-off, the frame never moves. 50mm lens, deep focus, same
light grey backdrop and same lighting direction as Shot 1.
```

### 構造化フォーマット版

```
[subject_definitions]
<Subject 1>: A woman in her late twenties. Face: fair skin with visible pores,
thick straight eyebrows, dark brown eyes, black hair pulled back off the
forehead. Body and wardrobe (Shot 2 only): slim build, plain white
button-down shirt tucked into straight-leg indigo jeans, white leather sneakers.

[summary]
A locked-off extreme close-up of <Subject 1>'s face hard-cuts to a locked-off
full body shot of the same woman standing motionless, facing the camera.

[retention_analysis]
Keep <Subject 1>'s face, hairline, eyebrow shape and hair colour identical in
both shots. Same backdrop, same lighting direction, same colour grade.

[detailed_description]
[Shot 1] (顔の超クローズアップ / 上記のとおり)
[Shot 2] Hard cut — instant, no pull-out, no zoom, no dissolve between shots.
Full body shot, ... (上記のとおり) ... holds still for three seconds.

[overall_soundscape]
Quiet studio room tone.

[non_diegetic_music]
None.
```

### Shot 2 固有の注意点

- **服装は今度は書く**
  Shot 1 では全身の服装を書くと引いてしまうので削ったが、Shot 2 は逆。
  頭からつま先まで写すには靴まで含めて具体的に書いたほうが画角が安定する。
  `subject_definitions` に書くときは「Shot 2 only」と但し書きを付けて、
  Shot 1 側に効かないようにする。

- **アスペクト比の影響が Shot 1 以上に大きい**
  立ち姿を「画角のほぼ全体」にできるのは実質 9:16(縦)。
  16:9 では人物が細長く縦だけ埋まり、左右が大きく空く。横で撮るなら
  `the figure fills the full height of the frame; the empty space on both
  sides is part of the composition` のように左右の余白を意図として書き、
  勝手に寄って足が切れるのを防ぐ。

- **「完全静止」は指定しないと必ず動く**
  `holds the pose completely still` だけでは体が揺れる。
  `no steps, no gestures, no turning, no weight shift` と禁止する動作を並べ、
  `only the faint rise and fall of her breathing` で許可する動きを1つだけ
  明示するのが効く。呼吸も不要なら `she does not move at all` に置き換える。

- **カメラ高さは chest height**
  全身で `eye level` と書くとカメラが目線の高さから見下ろす形になり、
  脚が短く写る。胸の高さでレンズを水平に、と指定する。

- **1本にまとめるか、分けるか**
  クローズアップと引きを同じ生成に混ぜるのは H3 が最も苦手とする組み合わせ。
  ハードカット指定でも通らない場合は、Shot 1 と Shot 2 を別々に生成して
  編集で繋ぐほうが確実。1本でやるなら5秒では足りないので、15秒尺で
  「最初の4秒が Shot 1、カット後の3秒が Shot 2」のように秒数を明記する。

---

## 8. Shot 3:回転して側面 → 2秒静止 → さらに回転 → 3秒静止

Shot 2 の立ち姿から、体を回して側面をカメラに向けて2秒静止、
さらに同じ方向へ回して3秒静止するターンアラウンド。
ここでは 正面 → 右側面 → 背面 の90°刻みで組む。

### いちばん失敗するポイント

「回転」を**カメラが被写体の周りを回り込む動き(アークショット)**と解釈される。
公式カメラ語彙に `Arc Shot` があるため、`Static Shot` の指定だけでは足りず、
アークを名指しで否定する必要がある。

```
Only the woman turns — the camera does not orbit, does not arc, does not
circle her, does not pan, does not zoom, does not move at all.
```

### Shot 3 のプロンプト

```
Full body shot, camera at chest height, lens level. The same woman stands
centred in frame, her whole body visible from head to toe with a small margin
above her head and below her feet. She begins facing the camera.

Over about one second she rotates 90 degrees to her own left, pivoting on the
spot, her right shoulder swinging toward the camera, until her body is in full
profile facing screen right. Her head turns with her body — she does not look
back at the camera. She holds this profile pose completely still for two
seconds — no steps, no gestures, no weight shift; only faint breathing.

Then she rotates another 90 degrees in the same direction over about one
second, until her back is fully to the camera. She holds this pose completely
still for three seconds.

Only the woman turns — the camera does not orbit, does not arc, does not
circle her, does not pan, does not zoom, does not move at all. Static shot,
locked-off camera, the frame never moves. She pivots in place: no steps
forward or backward, she stays centred, her size in the frame does not change,
the head-to-toe framing stays identical throughout.
Her face, hairstyle, body proportions and clothing stay exactly the same in
every position — plain white button-down shirt, straight-leg indigo jeans,
white sneakers.
50mm lens, deep focus, plain seamless light grey studio backdrop, soft even
frontal light, full-length soft shadow on the floor.
```

### 構造化フォーマット版

```
[detailed_description]
[Shot 3] Full body shot, camera at chest height, lens level, static and
locked-off. <Subject 1> stands centred, head to toe in frame.
  0.0–1.0s : she rotates 90° to her own left, pivoting on the spot, right
             shoulder swinging toward the camera, head turning with the body.
  1.0–3.0s : full profile facing screen right. She holds completely still —
             no steps, no gestures, no weight shift, only faint breathing.
  3.0–4.0s : she rotates a further 90° in the same direction, still pivoting
             on the spot.
  4.0–7.0s : her back is fully to the camera. She holds completely still for
             three seconds.
The camera does not orbit, arc, pan, zoom or move at any point — the subject
turns, the camera does not. Framing, distance and subject size are identical
in all three positions.

[retention_analysis]
Keep <Subject 1>'s hairstyle, body proportions and wardrobe identical in the
front, profile and back positions. Same backdrop, same lighting direction,
same colour grade as the previous shots.
```

### 回転方向の指定

方向を書かないと途中で反転したり往復したりする。3つの言い方を重ねると安定する。

| 回す方向 | カメラに向く側 | 体の向き |
|---|---|---|
| `rotates 90° to her own left` | `right shoulder toward the camera` | `in profile facing screen right` |
| `rotates 90° to her own right` | `left shoulder toward the camera` | `in profile facing screen left` |

### 2回目の停止位置を変える場合

2回目の角度だけ差し替える。

| 到達点 | 書き方 |
|---|---|
| 背面 | `rotates another 90 degrees ... until her back is fully to the camera` |
| 後ろ斜め45° | `rotates another 45 degrees ... until she is seen from three-quarter rear, her far shoulder hidden` |
| 反対側の側面 | `rotates another 180 degrees ... until she is in full profile facing screen left` |
| 正面に戻る | `rotates another 270 degrees in the same direction, back to facing the camera` |

### Shot 3 固有の注意点

- **顔がカメラを追いかける**
  何も書かないと、体だけ回して顔はカメラ目線のまま、という不自然な絵になる。
  `her head turns with her body — she does not look back at the camera` を必ず入れる。
  逆に顔だけカメラに残す演出なら
  `her head stays turned toward the camera while her body turns away` と明示する。

- **回転の所要時間も書く**
  停止時間だけ指定すると、回転が一瞬で終わったり間延びしたりする。
  回転ごとに `over about one second` を添える。

- **尺は最低7秒**
  1秒 + 2秒 + 1秒 + 3秒 = 7秒。余裕をみて10秒尺で生成し、
  余った分は最後の静止を伸ばすか編集で切る。

- **Shot 2 との連続性は first frame で担保する**
  Shot 3 は Shot 2 の終わりと同じ立ち姿から始まるので、Shot 2 の最終フレームを
  Shot 3 の開始フレームとして渡す(first/last frame 機能)と、服や体型のブレが
  激減する。テキストだけで繋ぐより確実。

- **回転はキャラ崩れが最も出るショット**
  背面に回った瞬間に髪型や服が変わることがある。`retention_analysis` に
  髪型・体型・服を明記し、本文にも `stay exactly the same in every position` と
  重ねて書く。それでも崩れるなら90°ごとに分けて生成する。

- **足の処理**
  `she pivots on the spot, her feet turning with her body` を書かないと、
  歩いて向きを変えたり、フレームから出ていったりする。

---

## 9. 全体プロンプト(Shot 1 → 2 → 3 通し)

3ショットを1本の映像として通す場合の全体プロンプト。

### タイムライン(13秒)

```
 0.0– 3.0s  Shot 1  顔の超クローズアップ、静止
 3.0s       ─── ハードカット ───
 3.0– 6.0s  Shot 2  全身の立ち姿、正面、3秒静止
 6.0– 7.0s  Shot 3  90°回転
 7.0– 9.0s          右側面で2秒静止
 9.0–10.0s          さらに90°回転
10.0–13.0s          背面で3秒静止
```

H3 の上限は15秒なので収まる。

**カットは Shot 1 → Shot 2 の1回だけ**。Shot 2 と Shot 3 は同じ据え置きカメラの
連続した1テイクなので切らない。ここを混同すると Shot 3 の頭に余計なカットが入る。

**アスペクト比は 9:16(縦)を推奨**。Shot 2・3 で頭からつま先を画角いっぱいに
入れる必要があるため、全体を縦に統一するのがいちばん破綻しない。

### A. 構造化フォーマット版(推奨)

```
[subject_definitions]
<Subject 1>: A woman in her late twenties.
  Face: fair skin with visible pores, thick straight eyebrows, dark brown
  eyes, black hair pulled back off the forehead, no visible make-up.
  Body and wardrobe (visible from Shot 2 onward only): slim build, plain
  white button-down shirt tucked into straight-leg indigo jeans, white
  leather sneakers.

[summary]
A locked-off extreme close-up of <Subject 1>'s face hard-cuts to a locked-off
full body shot of the same woman, who holds a still front-facing pose, then
turns 90° to profile and holds, then turns a further 90° to her back and holds.

[retention_analysis]
<Subject 1>'s face, hairline, eyebrow shape and hair colour are identical in
every shot. Her wardrobe, proportions and height do not change once visible.
The backdrop, lighting direction and colour grade are the same throughout:
plain seamless light grey studio backdrop, soft even frontal key light.

[detailed_description]
[Shot 1] 0.0–3.0s. Extreme close-up, straight-on frontal portrait, eye level.
<Subject 1>'s face fills the entire frame edge to edge — the top of her
forehead and her chin are cropped by the frame edges, almost no headroom,
shoulders and clothing out of frame, background not visible. Symmetrical
composition, eyes on the horizontal centreline, looking directly into the
lens. Skin texture, fine hairs and pores clearly visible. She blinks slowly
once, then the corners of her mouth lift slightly. Static shot, locked-off
camera — no push in, no zoom, no pan, the frame never moves. 85mm lens,
shallow depth of field, light grey backdrop far out of focus behind her.

HARD CUT at 3.0s — an instant cut, not a transition. The camera does not pull
out, does not zoom out, does not travel from the face to the body. No
dissolve, no fade, no morph. One frame is the close-up, the next frame is the
full body shot.

[Shot 2] 3.0–6.0s. Full body shot, straight-on frontal, camera at chest
height, lens level (not tilted down). <Subject 1> stands centred, her entire
body visible from the top of her head to the soles of her shoes, filling
almost the full height of the frame — a small margin of empty space above her
head and below her feet, nothing cropped at any edge. Arms relaxed at her
sides, feet shoulder-width apart, weight even on both legs, chin level,
looking directly into the lens. She holds this pose completely still for
three seconds — no steps, no gestures, no turning, no weight shift; only the
faint rise and fall of her breathing. Static shot, locked-off camera, the
frame never moves. 50mm lens, deep focus, full-length soft shadow on the floor.

[Shot 3] 6.0–13.0s. NO CUT — the camera setup, framing and lighting are
exactly the same as Shot 2 and the action continues without interruption.
  6.0– 7.0s : she rotates 90 degrees to her own left, pivoting on the spot,
              her right shoulder swinging toward the camera, her feet turning
              with her body, her head turning with her body — she does not
              look back at the camera.
  7.0– 9.0s : full profile facing screen right. She holds completely still for
              two seconds — no steps, no gestures, no weight shift, only faint
              breathing.
  9.0–10.0s : she rotates a further 90 degrees in the same direction, still
              pivoting on the spot.
 10.0–13.0s : her back is fully to the camera. She holds completely still for
              three seconds. If the clip runs longer than 13 seconds she
              simply continues to hold this final pose until the end.
Only the woman turns — the camera does not orbit, does not arc, does not
circle her, does not pan, does not zoom, does not move at any point. She
pivots in place: no steps forward or backward, she stays centred, her size in
the frame does not change, the head-to-toe framing is identical in the front,
profile and back positions.

[overall_soundscape]
A quiet studio room tone throughout. A faint rustle of fabric on each turn.
No footsteps.

[non_diegetic_music]
None.
```

### B. 自由文一括版

フィールド記法が使えない UI 向けの、同じ内容の一枚テキスト。

```
Locked-off studio sequence of the same woman in her late twenties — fair skin,
thick straight eyebrows, dark brown eyes, black hair pulled back off the
forehead, plain white button-down shirt, straight-leg indigo jeans, white
sneakers. Plain seamless light grey backdrop, soft even frontal light, same
lighting and colour grade throughout.

First three seconds: extreme close-up, straight-on frontal, eye level. Her
face fills the entire frame edge to edge, forehead and chin cropped by the
frame edges, shoulders out of frame, looking directly into the lens. She
blinks slowly once, then the corners of her mouth lift slightly. Static,
locked-off, 85mm, shallow depth of field.

Then a hard cut — an instant cut, not a transition. The camera does not pull
out, zoom out or travel from the face to the body. No dissolve, no fade.

After the cut: full body shot, straight-on frontal, camera at chest height,
lens level. She stands centred, her whole body visible from head to toe,
filling almost the full height of the frame with a small margin above her head
and below her feet. Arms relaxed at her sides, feet shoulder-width apart,
chin level, looking into the lens. She holds this pose completely still for
three seconds — only faint breathing. Static, locked-off, 50mm, deep focus.

Then, with no cut and the same framing, she rotates 90 degrees to her own left
over about one second, pivoting on the spot, her right shoulder swinging
toward the camera, her head turning with her body — she does not look back at
the camera — until she is in full profile facing screen right. She holds that
profile completely still for two seconds. She then rotates a further 90
degrees in the same direction over about one second until her back is fully
to the camera, and holds completely still for three seconds.

Only the woman turns — the camera does not orbit, does not arc, does not
circle her, does not pan, does not zoom, does not move at any point. She
pivots in place: no steps forward or backward, she stays centred, her size in
the frame does not change, the head-to-toe framing is identical in the front,
profile and back positions. Her face, hairstyle, proportions and clothing stay
exactly the same throughout.
```

### C. 分割して繋ぐ場合(品質重視ならこちら)

13秒を一発で通すと後半ほどキャラが崩れる。仕上がりを優先するなら3本に分けて
編集で繋ぐ。

| | 内容 | 尺 | 開始フレーム |
|---|---|---|---|
| 1本目 | Shot 1 顔アップ | 5秒 | — |
| 2本目 | Shot 2 全身正面・静止 | 5秒 | — |
| 3本目 | Shot 3 回転 | 10秒 | 2本目の最終フレーム |

ポイントは3本目。**2本目の最終フレームを3本目の開始フレームに指定する**
(first/last frame 機能)と、服・体型・立ち位置が引き継がれ、繋いだときに
段差が出ない。1本目と2本目の間はもともとハードカットなので、編集で単純に
繋ぐだけで成立する。

### 通しで組むときの追加の注意

- **服装の記述場所が Shot 1 と Shot 2/3 で衝突する**
  `subject_definitions` に服を書くと Shot 1 が引く。上の版では
  `(visible from Shot 2 onward only)` と但し書きを付け、Shot 1 の本文に
  `shoulders and clothing out of frame` を入れて両側から押さえている。
  ここを省くと顔アップが甘くなる。

- **Shot 1 の背景を Shot 2/3 と揃える**
  顔アップ単体なら暗い背景が映えるが、通しで使うとカット後に背景が変わって
  別ロケに見える。上の版では全編を light grey studio backdrop に統一している。

- **識別用の参照画像があるなら使う**
  顔の同一性はテキストだけでは13秒もたない。参照画像を渡せる場合は
  `<Picture 1> controls <Subject 1>'s face and identity` のように役割を
  明示して `subject_definitions` に紐付ける。

- **まず5秒で画角だけ確認する**
  いきなり13秒を回さず、Shot 1 単体・Shot 2 単体を5秒で出して画角が
  意図どおりか見てから通しに入ると、原因の切り分けが早い。

---

## 参考

- [MiniMax H3 プロンプトガイドの翻訳(dskjal)](https://dskjal.com/deeplearning/minimax-h3-prompt-guide)
- [MiniMax H3 プロンプトガイド:公式プロンプト全45種のリバースエンジニアリング(Atlas Cloud)](https://www.atlascloud.ai/blog/tips/minimax-h3-prompt-guide)
- [MiniMax H3 のプロンプト書式(iPentec)](https://www.ipentec.com/document/ai-image/video-generation-minimax-h3-prompt-format)
- [MiniMax H3 プロンプトガイド: 公式の型と3つのモード(pixo)](https://pixo.video/blog/minimax-h3-prompt-guide)
- [Hailuo Video Prompt Guide: Camera Moves & Examples](https://minimax-ai.chat/guide/hailuo-video-prompts/)
- [MiniMax H3 Prompt Guide (RunDiffusion)](https://www.rundiffusion.com/minimax-h3-prompt-guide)
- [4面キャラシートは効かなかった — MiniMax H3で効いていたのは構造化プロンプト(Zenn)](https://zenn.dev/toki_mwc/articles/minimax-h3-structured-prompt-ab)
