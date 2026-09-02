# MiniMax H3 (ComfyUI) 用プロンプト — 「紙袋を拾う女性」

元の日本語シーン記述を、MiniMax 系動画モデルで意図どおりに出やすい形へ変換したもの。

## 元シーン
1. 女性が立位からゆっくりしゃがみ込み、床の紙袋を拾い上げる。カメラは斜め方向から全身をとらえる（固定）。
2. カメラが手元に寄る。紙袋の中を見た女性は目がキツくなり、嫌悪まじりの怒った表情 → あきらめたような微笑。紙袋の中は一切見えない。

## 方針
- 2ショット構成なので **クリップを2本に分けて生成**（1クリップ内カットは破綻しやすい）。
- 否定表現（"don't show", "no ..."）は効きにくいので、**「中身が見えない」を肯定文と物理条件で表現**する
  （カメラ高さを袋の口より低く／口の向きを被写体側へ／内部は影）。
- 表情は「3拍」を時系列で明示（beat 1: 目が細まる怒り → beat 2: 保持 → beat 3: 力の抜けた微笑）。
- 人物の外見記述は2クリップで**完全に同一の文字列**にする。

---

## クリップ1（6秒 / カメラ固定・斜め全身）

```
Cinematic live-action footage. A woman in her late twenties with shoulder-length
dark hair, wearing a plain beige knit sweater and dark trousers, stands on a
wooden floor in a quiet, sparsely furnished apartment. Filmed in full body from a
three-quarter oblique angle at chest height. She slowly bends her knees and lowers
herself straight down into a deep crouch, spine staying upright, heels close to the
floor, one hand reaching toward a brown paper bag lying on the floor beside her
feet. Her fingers close around the folded top of the bag and she lifts it off the
floor, holding it in front of her. The movement is slow, deliberate and weighted.
The camera is locked off on a tripod and holds the identical three-quarter full-body
framing for the entire shot. Soft natural window light from the left, muted neutral
color grade, shallow depth of field, 35mm film look, realistic skin texture, 24fps.
```

## クリップ2（6〜10秒 / 手元への寄り＋表情変化）

```
Cinematic live-action footage. The same woman in her late twenties with
shoulder-length dark hair, wearing a plain beige knit sweater and dark trousers,
crouching on the wooden floor of the same quiet apartment, holding a brown paper
bag in both hands in front of her chest. The camera pushes in smoothly and steadily
from a three-quarter angle, travelling from her upper body to a tight close shot
that keeps both of her hands on the rim of the bag and her face in the same frame.
The lens stays level with the bag, slightly below its folded rim, so only the
crumpled outer paper of the bag faces camera; the mouth of the bag is angled away
from the lens toward her face alone, and its inside stays in deep shadow. She tilts
her head down and looks into the bag. Her eyes narrow sharply, her brows draw
together and her lips press thin into an angry, disgusted expression, held for a
beat. Then her shoulders drop as she exhales, the tension leaves her face and her
mouth curves into a small, tired, resigned smile while her eyes stay sad. Soft
natural window light, muted neutral color grade, shallow depth of field, 35mm film
look, subtle handheld micro-movement, 24fps.
```

Director 系（カメラ指示ブラケット対応）モデルを使う場合は先頭に `[Push in]`、
クリップ1は `[Static shot]` を付けると効きが安定する。

---

## 1クリップ通しで撮る場合（10秒 / カットなしのワンテイク）

```
Cinematic live-action, one continuous take, 10 seconds. A woman in her late
twenties with shoulder-length dark hair, wearing a plain beige knit sweater and
dark trousers, stands on the wooden floor of a quiet apartment, seen in full body
from a three-quarter oblique angle. She slowly bends her knees and lowers herself
into a deep crouch, reaching down and picking up a brown paper bag from the floor.
As she lifts it, the camera begins a slow, smooth push in from the full-body framing
to a close shot of her hands on the rim of the bag with her face in frame. The lens
stays level with the folded rim of the bag, so only the crumpled outer paper faces
camera and the mouth of the bag is angled away from the lens toward her face alone,
its inside in deep shadow. She looks down into the bag; her eyes narrow sharply,
her brows draw together into an angry, disgusted expression, then her shoulders drop
and her mouth curves into a small, tired, resigned smile. Soft natural window light,
muted neutral color grade, shallow depth of field, 35mm film look, 24fps.
```

---

## ComfyUI 側の設定

| 項目 | 推奨 | 理由 |
| --- | --- | --- |
| `prompt_optimizer` | **false** | 自動書き換えで「袋の中身を見せる」描写が足されるのを防ぐ |
| duration | クリップ1: 6s / クリップ2: 10s（可能なら） | 表情3拍は6秒だと詰まりやすい |
| resolution | 1080P | 表情の微差が潰れないように |
| seed | 固定して回す | 当たりseedから微修正する運用 |
| クリップ間の連結 | クリップ1の最終フレームを書き出し、クリップ2の I2V 入力画像にする | 服・髪・部屋・袋の一致 |

## 出目が崩れたときの調整

| 症状 | 対処 |
| --- | --- |
| しゃがまず前かがみ・膝を曲げるだけ | `lowers herself into a deep crouch` → `squats all the way down, knees fully bent, hips low near her heels` に強調 |
| 紙袋の中が映る | カメラ高さの記述を `slightly below its folded rim` → `at floor level, looking up at her` に。袋も `a paper bag with its top folded over` と描写 |
| 表情が変わらない／1種類のまま | 10秒に延長。それでも駄目なら「怒り」だけのクリップと「微笑」だけのクリップに割って繋ぐ |
| カメラが勝手に動く（クリップ1） | `locked off on a tripod` を文頭にも重ねる／Director系なら `[Static shot]` |
| 寄りが速すぎる（クリップ2） | `pushes in smoothly and steadily` → `pushes in very slowly over the whole shot` |

## 補足
- MiniMax 系は英語プロンプトが最も安定するため本文は英語。日本語入力も通るが、カメラ用語の解釈精度が落ちる。
- ComfyUI の MiniMax API ノードにはネガティブプロンプト欄が無いため、除外したい要素（＝袋の中身）は
  上記のとおり肯定文の構図条件で潰している。
