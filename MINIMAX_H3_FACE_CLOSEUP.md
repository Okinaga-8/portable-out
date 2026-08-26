# MiniMax H3(Hailuo 03)で顔を画面いっぱいに映すプロンプトの書き方

顔の正面を、ほぼ画面いっぱいの画角で映したいときのプロンプト設計メモ。
1〜6章が Shot 1(顔の超クローズアップ)、7章が Shot 2(全身の立ち姿・3秒静止)。

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

## 参考

- [MiniMax H3 プロンプトガイドの翻訳(dskjal)](https://dskjal.com/deeplearning/minimax-h3-prompt-guide)
- [MiniMax H3 プロンプトガイド:公式プロンプト全45種のリバースエンジニアリング(Atlas Cloud)](https://www.atlascloud.ai/blog/tips/minimax-h3-prompt-guide)
- [MiniMax H3 のプロンプト書式(iPentec)](https://www.ipentec.com/document/ai-image/video-generation-minimax-h3-prompt-format)
- [MiniMax H3 プロンプトガイド: 公式の型と3つのモード(pixo)](https://pixo.video/blog/minimax-h3-prompt-guide)
- [Hailuo Video Prompt Guide: Camera Moves & Examples](https://minimax-ai.chat/guide/hailuo-video-prompts/)
- [MiniMax H3 Prompt Guide (RunDiffusion)](https://www.rundiffusion.com/minimax-h3-prompt-guide)
- [4面キャラシートは効かなかった — MiniMax H3で効いていたのは構造化プロンプト(Zenn)](https://zenn.dev/toki_mwc/articles/minimax-h3-structured-prompt-ab)
