# MiniMax H3 (ComfyUI) R2V 版プロンプト — 「紙袋を拾う女性」

T2V 版は `minimax-h3-paper-bag.md`。こちらは **R2V（reference-to-video / 参照画像方式）** 用。

参照画像の想定:
- **Ref A**: 女性のバストアップ（顔情報用）
- **Ref B**: 女性の立ち姿・全身（体型と全身プロポーション用）
- 両方とも「同一人物の別アングル」として渡す。

## T2V 版からの変更方針

| 項目 | T2V 版 | R2V 版 |
| --- | --- | --- |
| 髪型・服・年齢・顔立ち | プロンプトに明記 | **全部削除**（参照画像と競合して似せ精度が落ちる） |
| 人物の呼び方 | `A woman in her late twenties with...` | `The woman from the reference image` |
| 服装 | 具体的に指定 | `wearing exactly the same clothes as the reference` のみ |
| 環境 | 任意 | **明記必須**（参照画像の背景が漏れてくるため上書きする） |
| 小道具（紙袋） | 軽く描写 | **やや詳しく描写**（参照に写っていない＝テキスト駆動のため） |
| 2クリップの一貫性 | クリップ1の最終フレームを I2V 入力に | **同じ参照画像を両クリップに使うだけ**（R2V の利点） |

---

## クリップ1（6秒 / 固定・斜め全身）

参照は **Ref B（立ち姿・全身）を主**に。Ref A も併用可。

```
The woman from the reference image, wearing exactly the same clothes and hairstyle
as the reference, alone in a quiet, sparsely furnished apartment with a wooden
floor and a plain wall behind her. Live-action cinematic footage, filmed in full
body from a three-quarter oblique angle at chest height. She slowly bends her knees
and lowers herself straight down into a deep crouch, spine staying upright, heels
close to the floor, one hand reaching toward a plain brown kraft paper bag lying on
the floor beside her feet. Her fingers close around the crumpled rim of the bag and
she lifts it off the floor, holding it in front of her chest. The movement is slow,
deliberate and weighted, with a natural shift of body weight. The camera is locked
off on a tripod and holds the identical three-quarter full-body framing for the
entire shot. Soft natural window light from the left, muted neutral color grade,
shallow depth of field, realistic skin texture, 24fps.
```

## クリップ2（6〜10秒 / 手元への寄り＋表情変化）

参照は **Ref A（バストアップ）を主**に。寄りで顔が崩れるのを防ぐ。

```
The woman from the reference image, wearing exactly the same clothes and hairstyle
as the reference, alone in the same quiet apartment with a wooden floor, crouching
and holding a plain brown kraft paper bag in both hands in front of her chest.
Live-action cinematic footage. The camera pushes in smoothly and steadily from a
three-quarter angle, travelling from her upper body to a tight close shot that keeps
both of her hands on the rim of the bag and her whole face in the same frame. The
lens stays level with the rim of the bag, slightly below it, so only the crumpled
outer paper of the bag faces camera; the opening of the bag is angled away from the
lens toward her face alone, and its inside stays in deep shadow. She tilts her head
down and looks into the bag. Her eyes narrow sharply, her brows draw together and
her lips press thin into an angry, disgusted expression, held for a beat. Then her
shoulders drop as she exhales, the tension leaves her face and her mouth curves into
a small, tired, resigned smile while her eyes stay sad. Soft natural window light,
muted neutral color grade, shallow depth of field, realistic skin texture, subtle
handheld micro-movement, 24fps.
```

---

## 1クリップ版（10秒 / カットなしのワンテイク・参照2枚同時）

引き→寄りを1テイクで通す。R2V に2枚（顔＋全身）を渡す構成が最も噛み合うパターン。

```
The woman from the reference images, wearing exactly the same clothes and hairstyle
as the reference, alone in a quiet, sparsely furnished apartment with a wooden floor.
Live-action cinematic footage, one continuous take. She stands seen in full body from
a three-quarter oblique angle, then slowly bends her knees and lowers herself into a
deep crouch, reaching down and picking up a plain brown kraft paper bag from the floor
by its crumpled rim. As she lifts it in front of her chest, the camera begins a slow,
smooth push in from the full-body framing to a close shot of her hands on the rim of
the bag with her whole face in frame. The lens stays level with the rim of the bag, so
only the crumpled outer paper faces camera and the opening is angled away from the lens
toward her face alone, its inside in deep shadow. She looks down into the bag; her eyes
narrow sharply and her brows draw together into an angry, disgusted expression, then her
shoulders drop as she exhales and her mouth curves into a small, tired, resigned smile.
Soft natural window light from the left, muted neutral color grade, shallow depth of
field, realistic skin texture, 24fps.
```

### 参照画像のインデックス指定について

ノード／モデル側が `[Image 1]` `@subject1` のような参照トークンをサポートしている場合は、
冒頭の `The woman from the reference image(s)` をその記法に差し替える。例:

```
[Image 1] the woman, wearing exactly the same clothes as the reference, alone in ...
```

サポートしていない（画像入力を繋ぐだけの）ノードなら、上記のプレーンな書き方のままでよい。
**どちらの場合も「参照は同一人物の別アングル」であることを外見描写の重複で示さない**こと。

---

## 参照画像の準備（R2V はここで9割決まる）

- **Ref A / Ref B で服・髪型・アクセサリを完全に一致**させる。ズレると生成中に服が変形する。
- **表情はニュートラル、口は閉じ、目は開ける。** 参照が笑顔だとクリップ2の「怒り」に入りにくい。
- Ref A（バストアップ）: 顔が大きく・ピントが合っている・顔に濃い影や前髪の被りがない・マスクやサングラス無し。
- Ref B（立ち姿）: 頭頂から**足先まで**入れる。しゃがみ動作で脚と靴が映るため、足が切れていると崩れる。
- **紙袋やそれに似た小道具を参照画像に写さない。** 被写体の一部として学習され、常時手に持ち続けることがある。
- **手を隠さない**（ポケットに入れた立ち姿などは避ける）。R2V は手の形も参照から引く。
- 背景は無地・単純に。参照の背景は生成側に染み出すので、プロンプト側の環境描写で上書きする前提。
- 照明方向を2枚で揃える（両方とも順光、など）。

## ComfyUI 側の設定

| 項目 | 推奨 |
| --- | --- |
| reference images | クリップ1=Ref B 主 / クリップ2=Ref A 主 / 1クリップ版=A+B 両方 |
| `prompt_optimizer` | **false**（書き換えで外見描写が足され、参照と競合するため） |
| duration | クリップ1: 6s / クリップ2: 10s（表情3拍のため） / 1クリップ版: 10s |
| resolution | 1080P（寄りでの顔の破綻を抑える） |
| seed | 固定して回し、当たりから微修正 |

## R2V 特有の崩れと対処

| 症状 | 対処 |
| --- | --- |
| 女性が2人出る／途中で別人に入れ替わる | ノードが2枚を「別人物」と解釈している。参照を1枚に減らすか、冒頭に `a single woman, alone in the room` を追加 |
| 寄ったときに顔が別人になる | クリップ2の参照を Ref A のみにする。寄りの終点を「顔全体が入る」までに留め、目だけのドアップにしない |
| 参照画像の背景が出てしまう | 環境描写（`a quiet apartment with a wooden floor and a plain wall`）を文の**前半**に移動し、より具体的に |
| 服や髪が途中で変わる | `wearing exactly the same clothes and hairstyle as the reference` を1文目に置く。それでも駄目なら参照2枚の服の不一致を疑う |
| 表情が変わらない／笑顔のまま | 参照画像が笑顔になっている可能性が高い。無表情の参照に差し替える。それでも駄目なら「怒り」クリップと「微笑」クリップに割って繋ぐ |
| しゃがまず前かがみになる | `lowers herself into a deep crouch` → `squats all the way down, knees fully bent, hips low near her heels` |
| 紙袋の中が映る | `The lens stays level with the rim` → `The camera stays at floor level, looking slightly up at her` に変更 |
| 紙袋の形が安定しない | `a plain brown kraft paper bag with twisted paper handles` のように形状語を1つ足す |

---

# 続きのシーン（クリップ3・4） — 「おもちゃのヘビを取り出して観察する」

元シーン:
3. 女性が紙袋の中から、子供のおもちゃのヘビを引っ張り出す。
4. 引っ張り出したヘビを、手を動かしながら黙って観察する。

## このカット固有の方針

- **最大のリスクは「本物のヘビ」になること。** おもちゃであることを
  ①材質（`soft rubber` / `hollow plastic`）
  ②造形（`cartoonish painted face`）
  ③動き（`limp and lifeless, moves only from her hand`）
  の3方向から縛る。1つだけだと生きたヘビとして自走する。
- **「黙って」は明示しないと喋る。** 動画生成モデルは放っておくと口を動かすので
  `her lips stay closed and she says nothing` を必ず入れる。
- おもちゃは参照画像に写っていないので、**色・長さ・質感を具体的に固定**してクリップ間で揃える。
- 姿勢はクリップ2から継続（しゃがんだまま）。

## クリップ3（6秒 / 紙袋からヘビを引っ張り出す）

参照は **Ref A（バストアップ）**。

```
The woman from the reference image, wearing exactly the same clothes and hairstyle
as the reference, alone in a quiet apartment with a wooden floor, crouching and
holding a plain brown kraft paper bag against her chest with one hand. Live-action
cinematic footage, close shot from a three-quarter angle that keeps her hands on the
bag and her whole face in frame. She reaches into the bag with her other hand and
slowly pulls out a children's toy snake, about forty centimetres long, made of soft
bright green rubber with a yellow belly and a cartoonish painted face with a red
mouth. The toy is completely limp and lifeless: it bends and sways only from the
movement of her hand as she draws it out and lifts it clear of the bag, hanging down
from her fingers like a piece of rubber hose. Her lips stay closed and she says
nothing. The camera holds a steady three-quarter close framing, tilting up just
enough to follow the toy as she raises it, and the lens stays level with the rim of
the bag so only the outer paper of the bag faces camera. Soft natural window light,
muted neutral color grade, shallow depth of field, realistic skin texture, 24fps.
```

## クリップ4（6〜10秒 / 手を動かしながら黙って観察）

参照は **Ref A（バストアップ）**。

```
The woman from the reference image, wearing exactly the same clothes and hairstyle
as the reference, alone in a quiet apartment with a wooden floor, crouching and
holding up a children's toy snake in front of her, about forty centimetres long,
made of soft bright green rubber with a yellow belly and a cartoonish painted face.
Live-action cinematic footage, close shot from a three-quarter angle that keeps both
of her hands and her whole face in frame. She studies the toy in silence, turning it
slowly over in her hands, rotating it to see the other side, letting it dangle and
swing from her fingers, lifting it closer to her eyes and then holding it further
away, running her fingertips along its rubber body. The toy stays limp and lifeless,
bending and swinging only from her own hand movements. Her lips stay closed and she
says nothing; her face is calm and unreadable, her eyes tracking the toy, her head
tilting slightly. The camera is almost static with subtle handheld micro-movement and
stays in the close shot for the entire take. Soft natural window light, muted neutral
color grade, shallow depth of field, realistic skin texture, 24fps.
```

## 1クリップ版（10秒 / 取り出し〜観察を通しで）

```
The woman from the reference images, wearing exactly the same clothes and hairstyle
as the reference, alone in a quiet apartment with a wooden floor, crouching and
holding a plain brown kraft paper bag against her chest with one hand. Live-action
cinematic footage, one continuous take, close shot from a three-quarter angle that
keeps her hands and her whole face in frame. She reaches into the bag and slowly
pulls out a children's toy snake, about forty centimetres long, made of soft bright
green rubber with a yellow belly and a cartoonish painted face with a red mouth,
lifting it clear of the bag where it hangs limply from her fingers. She lowers the
bag out of frame and takes the toy in both hands, then studies it in silence: turning
it slowly over, rotating it to see the other side, letting it dangle and swing,
lifting it closer to her eyes and then holding it further away. The toy stays limp
and lifeless, bending and swinging only from the movement of her hands. Her lips stay
closed and she says nothing; her face is calm and unreadable, her eyes tracking the
toy. The camera stays in the close framing for the whole take with subtle handheld
micro-movement. Soft natural window light, muted neutral color grade, shallow depth
of field, realistic skin texture, 24fps.
```

## おもちゃの参照画像を足す選択肢

ノードが**物体の参照画像**に対応している場合、Ref A / Ref B に加えて
**Ref C: おもちゃのヘビ単体の写真（白背景）** を渡すと、色・造形がクリップ間で完全に揃う。

- 利点: 「本物のヘビ化」がほぼ完全に止まる。プロンプト側の材質描写を減らせる。
- 注意: ノードによっては Ref C を「2人目の被写体」と解釈して人物が増えることがある。
  その場合は Ref C を外し、プロンプトの材質描写だけで縛る。

## このカットの崩れと対処

| 症状 | 対処 |
| --- | --- |
| 本物のヘビになる／自分でうねる・鎌首をもたげる | `hollow rubber toy` を追加し、`its body stays completely still except when her hand moves it` を末尾に足す。それでも駄目なら Ref C（おもちゃ単体写真）を投入 |
| 女性が喋る／口が動く | `her lips stay closed and she says nothing` を文の**前半**へ移動。`silent, no dialogue` も併記 |
| ヘビが手から消える／落ちる | `holding it firmly in both hands` に固定し、`dangle` を削る |
| ヘビの色・長さがクリップ間で変わる | 数値と色を全クリップで**同一文字列**にする（`about forty centimetres long, bright green with a yellow belly`）。または Ref C を使う |
| 女性が驚く・怖がる表情になる | `calm and unreadable, no strong expression, she is simply examining it` を追加 |
| カメラが勝手に引く | `the camera stays in the close shot for the entire take` を残す。Director 系なら `[Static shot]` |
| 紙袋の中が映ってしまう | クリップ3の `the lens stays level with the rim of the bag` を維持。不要なら削ってよい（ヘビが出た後は中身が論点ではないため） |

---

# 着替えのシーン — 2つのアプローチ

同じドラマ上のビート（脱ぐ → 床から拾う → 身につける）を、
**版A: 靴下に置き換え（斜め全身を維持）** と
**版B: 上半身フレーム＋フレーム外動作** の2通りで書いたもの。

| | 版A（靴下） | 版B（上半身フレーム） |
| --- | --- | --- |
| カメラ | 斜め全身・固定（元の指定どおり） | 腰から上・固定（全身は捨てる） |
| 主参照 | **Ref B（立ち姿・全身）** | **Ref A（バストアップ）** ※全身参照は画角を引かせるので使わない |
| 難所 | 足と手の描画崩れ、片足バランス | カメラが勝手に引いて全身になる |
| 衣類の指定 | 具体的に指定する | **一切名前を出さない**（後述） |

---

## 版A: 靴下バージョン（斜め全身・固定カメラ）

### クリップ5（6秒 / 片方の靴下を脱ぐ）

```
The woman from the reference image, wearing exactly the same clothes and hairstyle
as the reference, alone in a quiet, sparsely furnished apartment with a wooden floor
and a plain wall behind her. Live-action cinematic footage, filmed in full body from
a three-quarter oblique angle at chest height. She stands still, then bends forward
at the waist and reaches down with both hands to her left foot, hooking her fingers
into the cuff of a white cotton crew sock and peeling it down over her heel and off
her toes. She straightens back up holding the sock in one hand, then opens her
fingers and lets it drop to the wooden floor beside her bare left foot. The movement
is unhurried and slightly off balance, with small natural corrections of her weight.
The camera is locked off on a tripod and holds the identical three-quarter full-body
framing for the entire shot. Soft natural window light from the left, muted neutral
color grade, shallow depth of field, realistic skin texture, 24fps.
```

### クリップ6（6秒 / もう片方の靴下を脱ぐ）

```
The woman from the reference image, wearing exactly the same clothes and hairstyle
as the reference, alone in the same quiet apartment with a wooden floor, standing
barefoot on her left foot with one white cotton crew sock already lying on the floor
beside her. Live-action cinematic footage, filmed in full body from a three-quarter
oblique angle at chest height. She bends forward at the waist again and reaches down
with both hands to her right foot, hooking her fingers into the cuff of the second
white cotton crew sock and peeling it down over her heel and off her toes. She
straightens back up holding it, then lets it fall to the floor next to the first one.
Her weight sways slightly and she corrects her balance naturally. The camera is
locked off on a tripod and holds the identical three-quarter full-body framing for
the entire shot. Soft natural window light from the left, muted neutral color grade,
shallow depth of field, realistic skin texture, 24fps.
```

### クリップ7（6〜10秒 / 床の靴下を拾って履く）

拾う靴下は**色を変える**と「履き替えた」ことが画で読める。

```
The woman from the reference image, wearing exactly the same clothes and hairstyle
as the reference, standing barefoot on the wooden floor of the same quiet apartment.
Live-action cinematic footage, filmed in full body from a three-quarter oblique angle
at chest height. She bends down and picks up a single grey wool sock lying on the
floor near her feet, then straightens up and stretches its mouth open with both
hands. She leans forward, raises her right heel and balances on the toes of that
foot, guides the sock over her toes and pulls it up over her heel and around her
ankle, then straightens up and settles her weight down onto the foot. Unhurried,
slightly clumsy, with small natural balance corrections. The camera is locked off on
a tripod and holds the identical three-quarter full-body framing for the entire shot.
Soft natural window light from the left, muted neutral color grade, shallow depth of
field, realistic skin texture, 24fps.
```

### 版A・1クリップ版（10秒）

3ビートを10秒に詰めると動作が早回しになりやすい。**2ビートに削るほうが確実**
（両方脱ぐ→片方履く、ではなく「片方脱ぐ→拾って履く」）。以下は3ビート版。

```
The woman from the reference images, wearing exactly the same clothes and hairstyle
as the reference, alone in a quiet, sparsely furnished apartment with a wooden floor.
Live-action cinematic footage, one continuous take, filmed in full body from a
three-quarter oblique angle at chest height. She stands still, then bends forward and
peels a white cotton crew sock off her left foot and drops it on the floor, then
bends again and peels the second white sock off her right foot and drops it beside
the first. She then picks up a single grey wool sock from the floor, stretches its
mouth open with both hands, leans forward and pulls it over the toes and heel of her
right foot, and straightens up settling her weight onto it. Unhurried and slightly
clumsy, with small natural balance corrections throughout. The camera is locked off
on a tripod and holds the identical three-quarter full-body framing for the entire
shot. Soft natural window light from the left, muted neutral color grade, shallow
depth of field, realistic skin texture, 24fps.
```

### 版Aの崩れと対処

| 症状 | 対処 |
| --- | --- |
| 足の指・手の指が破綻する | 最大の難所。1080P必須。`her bare foot clearly visible, five toes` などと足を強調するのは**逆効果**（注目されて余計に崩れる）。むしろ足の描写を減らし、`peeling the sock off her foot` だけに留めるほうが安定する |
| 靴下が消える／手の中で溶ける | `a white cotton crew sock` の材質語を保持し、床に落とす動作を `opens her fingers and lets it drop` と分解して書く |
| 途中で座り込む | `standing` を文の前半に置き、`she stays standing throughout` を末尾に追加 |
| 片足立ちで崩壊する | クリップ7の `raises her right heel and balances on the toes of that foot` を `sits down on a chair` 前提に変えるか、`bends forward` 主体の動作に統一する |
| 靴下の色が読めない | 床が木目なので白は読める。暗い床なら `a bright white sock` / `a bright red sock` に変更 |
| 「拾って履いた」が伝わらない | 脱ぐ靴下と履く靴下の色を必ず変える（white → grey / white → striped） |

---

## 版B: 上半身フレーム＋フレーム外動作

### 設計の要点

- **衣類の名前を一切書かない。** これが最重要。脱ぐ対象を名指しすると、モデルは
  「それを見せなければ」と判断して画角を引いたり、フレーム内に描画したりする。
  **フレームの中にあるものだけを描写する**（肩・腕・肘・重心・表情）。
- 参照は **Ref A（バストアップ）のみ**。立ち姿の全身参照を渡すと画角が引っ張られる。
- 「腰から下でやっている」ことは、**重心移動と片足バランス**で観客に伝わる。
- カメラ指示は否定形（`never tilt down`）より、**下端の位置を肯定形で固定**するほうが効く。

### クリップB-1（6秒）

```
The woman from the reference image, wearing exactly the same clothes and hairstyle
as the reference, alone in a quiet, sparsely furnished apartment with a plain wall
behind her. Live-action cinematic footage, a locked-off medium shot from a
three-quarter oblique angle, framing her from the waist up with the bottom edge of
frame at her waistline. She stands still, then looks down and her shoulders roll
forward as both arms reach straight down and her hands pass below the bottom edge of
the frame. Her elbows move in small steady arcs and her upper body dips slightly as
she works with her hands out of view. She shifts her weight from one foot to the
other, her torso swaying and correcting as she briefly balances, then settles. She
straightens back up, her empty hands returning into frame, and smooths the hem of her
top. Her lips stay closed and she says nothing. The camera is locked off on a tripod
and holds the identical waist-up framing for the entire shot, the bottom edge of
frame staying at her waistline. Soft natural window light from the left, muted
neutral color grade, shallow depth of field, realistic skin texture, 24fps.
```

### クリップB-2（6秒）

同じ動作の反復に見えないよう、**壁に片手をついて支える**動きで差をつける。

```
The woman from the reference image, wearing exactly the same clothes and hairstyle
as the reference, alone in the same quiet apartment with a plain wall behind her.
Live-action cinematic footage, a locked-off medium shot from a three-quarter oblique
angle, framing her from the waist up with the bottom edge of frame at her waistline.
She reaches out and steadies herself with one hand flat against the wall, looks down,
and lowers her other arm straight down until her hand passes below the bottom edge of
the frame. Her shoulder drops and rotates in small movements as she works out of
view, her weight lifting onto one leg so her whole torso tilts and corrects. She
brings her hand back up into frame, takes her palm off the wall and straightens up,
exhaling. Her lips stay closed and she says nothing. The camera is locked off on a
tripod and holds the identical waist-up framing for the entire shot, the bottom edge
of frame staying at her waistline. Soft natural window light from the left, muted
neutral color grade, shallow depth of field, realistic skin texture, 24fps.
```

### クリップB-3（6〜10秒 / 床から拾って身につける）

```
The woman from the reference image, wearing exactly the same clothes and hairstyle
as the reference, alone in the same quiet apartment with a plain wall behind her.
Live-action cinematic footage, a locked-off medium shot from a three-quarter oblique
angle, framing her from the waist up with the bottom edge of frame at her waistline.
She looks down at the floor, then bends forward and down until her head and shoulders
drop out of the bottom of the frame for a moment. She rises back up into frame, her
hands staying below the bottom edge, her forearms tensing as she works out of view.
Her weight lifts onto one leg and her torso tilts and corrects, then lifts onto the
other leg and corrects again. Finally she straightens up to her full height, her
empty hands returning into frame, and smooths the hem of her top with both hands. Her
lips stay closed and she says nothing. The camera is locked off on a tripod and holds
the identical waist-up framing for the entire shot, the bottom edge of frame staying
at her waistline. Soft natural window light from the left, muted neutral color grade,
shallow depth of field, realistic skin texture, 24fps.
```

### 版B・1クリップ版（10秒）

```
The woman from the reference image, wearing exactly the same clothes and hairstyle
as the reference, alone in a quiet, sparsely furnished apartment with a plain wall
behind her. Live-action cinematic footage, one continuous take, a locked-off medium
shot from a three-quarter oblique angle, framing her from the waist up with the
bottom edge of frame at her waistline. She stands still, then looks down and both
arms reach straight down until her hands pass below the bottom edge of the frame; her
elbows move in small arcs and she shifts her weight from one foot to the other,
swaying and correcting her balance. She steadies herself with one hand against the
wall and repeats the movement, her shoulder dropping and rotating out of view. Then
she bends forward and down until her head drops out of the bottom of the frame for a
moment, rises back into frame with her hands still below the edge, and her weight
lifts onto one leg and then the other as her forearms tense. Finally she straightens
up to her full height, her empty hands returning into frame, and smooths the hem of
her top. Her lips stay closed and she says nothing. The camera is locked off on a
tripod and holds the identical waist-up framing for the entire shot, the bottom edge
of frame staying at her waistline. Soft natural window light from the left, muted
neutral color grade, shallow depth of field, realistic skin texture, 24fps.
```

### 版Bの崩れと対処

| 症状 | 対処 |
| --- | --- |
| カメラが引いて全身になる | 参照から Ref B（立ち姿・全身）を外し Ref A のみにする。`the bottom edge of frame staying at her waistline` を文頭にも重ねる。Director 系なら `[Static shot]` |
| モデルが勝手に衣類を描く | プロンプト内に衣類の名詞が残っていないか確認する。`hem of her top` 以外の衣類語は全部消す |
| 手がフレーム外に出ず、宙で動く | `her hands pass below the bottom edge of the frame` を動作ごとに毎回書く。1回だけだと戻ってくる |
| 何をしているか伝わらない | 重心移動の記述を増やす（`her weight lifts onto one leg and her torso tilts and corrects`）。これが唯一の手がかりになる |
| フレームアウトしたまま戻らない | `rises back up into frame` `straightens up to her full height` を明示 |
| 喋りだす | `her lips stay closed and she says nothing` を前半へ |

---

# テーブルのシーン — サラミ

構図: テーブルに座った女性、斜め方向からの固定・胸から上のミディアムショット。
主参照は **Ref A（バストアップ）**。

小道具はサラミ。参照画像に写っていないので、**寸法・色・質感を全クリップで同一文字列に固定**する:
`a thick dry-cured salami sausage, deep red with a pale dusty white rind, firm and rigid`

## クリップ8（6〜10秒 / 一口食べて味わう）

```
The woman from the reference image, wearing exactly the same clothes and hairstyle
as the reference, sitting at a plain wooden table in a quiet, sparsely furnished
apartment. Live-action cinematic footage, a locked-off medium shot from a
three-quarter oblique angle, framing her from the chest up with the edge of the table
across the bottom of frame. She holds a thick dry-cured salami sausage in both hands,
deep red with a pale dusty white rind, firm and rigid. She raises it to her mouth and
bites a piece off the end, then lowers the salami back down to the table and chews
slowly. Her eyes close for a moment, her eyebrows lift and her cheeks round as she
savours the taste, and she nods slightly and breaks into a satisfied, contented
smile. The camera is locked off on a tripod and holds the identical framing for the
entire shot. Soft natural window light from the left, muted neutral color grade,
shallow depth of field, realistic skin texture, 24fps.
```

## クリップ9（6秒 / 横咥え・両端がはみ出る・イタズラっぽい表情）

要点は3つ。
1. **「口より長い」ことを比較で明示**する。寸法だけ書いても口の中に収めてしまう。
2. **`like a dog holding a stick crosswise`** という比喩が最も効く。既知の絵として理解される。
3. **両手をテーブルに下ろさせる**。手の行き先を指定しないと、手が消えるか画面外で溶ける。

```
The woman from the reference image, wearing exactly the same clothes and hairstyle
as the reference, sitting at a plain wooden table in the same quiet apartment.
Live-action cinematic footage, a locked-off medium shot from a three-quarter oblique
angle, framing her from the chest up. She lifts a thick dry-cured salami sausage,
deep red with a pale dusty white rind, firm and rigid, turns it sideways and grips it
crosswise between her teeth, like a dog holding a stick in its mouth. The salami is
far longer than her mouth is wide, so both of its ends stick out well past the
corners of her lips on either side of her face. She lowers both hands flat onto the
table and holds the salami still, clamped between her teeth. She turns her face
towards the lens, her eyes widening and brightening, her eyebrows lifting and the
corners of her mouth pulling back into a mischievous grin around the salami. The
camera is locked off on a tripod and holds the identical framing for the entire shot.
Soft natural window light from the left, muted neutral color grade, shallow depth of
field, realistic skin texture, 24fps.
```

## 1クリップ版（10秒 / 味わう〜横咥え）

```
The woman from the reference image, wearing exactly the same clothes and hairstyle
as the reference, sitting at a plain wooden table in a quiet, sparsely furnished
apartment. Live-action cinematic footage, one continuous take, a locked-off medium
shot from a three-quarter oblique angle, framing her from the chest up with the edge
of the table across the bottom of frame. She holds a thick dry-cured salami sausage
in both hands, deep red with a pale dusty white rind, firm and rigid. She raises it,
bites a piece off the end and chews slowly, her eyes closing for a moment and her
eyebrows lifting into a satisfied, contented smile as she savours the taste. Then she
turns the salami sideways and grips it crosswise between her teeth, like a dog
holding a stick in its mouth; it is far longer than her mouth is wide, so both ends
stick out well past the corners of her lips on either side of her face. She lowers
both hands flat onto the table and turns her face towards the lens, her eyes widening
and her mouth pulling back into a mischievous grin around the salami. The camera is
locked off on a tripod and holds the identical framing for the entire shot. Soft
natural window light from the left, muted neutral color grade, shallow depth of
field, realistic skin texture, 24fps.
```

## このシーンの崩れと対処

| 症状 | 対処 |
| --- | --- |
| 口元・歯が破綻する | 最大の難所。**これ以上寄らない**（胸から上のミディアムを維持）。1080P 必須。`her teeth` を主語にした描写は増やさない — 注目させると崩れる |
| サラミが口に収まってしまう | `far longer than her mouth is wide` と `like a dog holding a stick` の両方を残す。それでも駄目なら `a 30 cm long salami` と数値を足す |
| サラミがゴムのように曲がる | `firm and rigid` `dry-cured` を保持し、`it stays perfectly straight and does not bend` を末尾に追加 |
| 咥えたまま食べ進める／飲み込む | `holds the salami still, clamped between her teeth` を明示。`chews` の語をクリップ9からは完全に消す |
| 手が消える／溶ける | `lowers both hands flat onto the table` のように**手の最終位置を必ず指定**する |
| 表情が「イタズラっぽく」ならない | `mischievous` 単体は弱い。`eyes widening and brightening` `eyebrows lifting` `corners of her mouth pulling back` と**筋肉の動きに分解**して書く |
| サラミの色・太さがクリップ間で変わる | 全クリップで同一文字列を使う。ノードが物体参照に対応していれば、サラミ単体の白背景写真を Ref C として追加 |
| カメラが寄る／引く | `the camera is locked off on a tripod and holds the identical framing` を維持。Director 系なら `[Static shot]` |
