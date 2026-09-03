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
