# HANDOFF — 現在地

**最終更新: 2026-09-05 / 更新者: クラウド側セッション**

ローカル(自宅 PC)の Claude Code で作業を再開するときに、**最初に読むファイル**。
会話ログは引き継がない。ここと、リポジトリと、Artifact の 3 つで状態が完結するようにしてある。

---

## 進行中のタスク

**ComfyUI の MiniMax H3 環境に 10Eros-Max を追加して、Ref2VA の作風を比較する**

| 場所 | 中身 |
|---|---|
| `docs/minimax-h3-10eros-max.html` | 判断シート本体（モデル候補・VRAM・設定・確定/要検証） |
| Artifact 版 | https://claude.ai/code/artifact/f9ac898a-cf81-4c0b-a630-98d890e2c532 |
| `.claude/skills/comfyui-h3/SKILL.md` | H3 系の前提知識。ローカルセッションはこれを読めば追いつく |
| `tools/h3_env_check.py` | 実機の状態を Markdown で吐く |

Artifact の db に `env/pc`（実機の状態）、`runs`（実測ログ）、`checks/state`（進捗）がある。
**Artifact ツールの `read_db` で読める。** 推測より実測を優先すること。

---

## 確定していること

- **GPU: RTX 4080 / VRAM 16GB（Ada, SM 8.9）、RAM 64GB、CUDA 13**
- **DiT: `minimax_h3_ref2va_pruned_int8_convrot.safetensors`**（Ref2VA / **pruned** / INT8 ConvRot / 19.53GB）
  → 19.53GB が 16GB で回っている = offload が効いた状態で成立済み
- 主用途 **Ref2VA**、FL2VA も併用
- **pruned には Full 向け Turbo LoRA が効かない**（AdaLN が 2688 次元 vs 8 次元 `adaln_t_table` で構造が別）。
  pruned 用変換版は **FL2VA 側にしか存在しない**
- **pruned Ref2VA の高速化は PDD-Acc 経路のみ**（要 ComfyUI 0.33.0+）

## 未確定 — 次の一手はこれ

1. **`ComfyUI/models/loras/` の中身**と、ワークフローに LoRA ローダーノードが実際にあるか
2. **ComfyUI のバージョンが 0.33.0 以上か** → PDD-Acc が使えるかの分かれ目
3. **基準線**: 現行 H3 の同一条件での生成時間とピーク VRAM（10Eros-Max を入れる**前**に測る）

ローカルセッションなら 1 と 2 は直接見られる:

```
python tools/h3_env_check.py --comfy "C:\path\to\ComfyUI"
```

## 決まっている方針

- **1 本目**: Abiray `10Eros-Max-ref2va-Beta2-GGUF` の **Q4_K_M（約 11.6GB）** + ComfyUI-GGUF。
  非 Turbo 焼き込みなので、いまの運用を変えずに DiT だけ差し替えられる
- **既存ファイルは消さない。** ワークフローを複製し、DiT ローダーだけ差し替える（同一シード A/B のため）
- **2 本目**: beta4 `TURBO-hybrid` INT8（約 19.5〜21GB）。**Turbo LoRA は外す**、euler/simple 6〜8 step、
  **i2v 形式では使わない**（参照 or t2va 形式で）
- A/B は**動きのある題材**で。参照画像の枚数も揃える

## 保留

- NVFP4 版が Ada で動くか（FL2VA 版しか無いので主用途から外れる。優先度低）
- beta4 INT8 の正確なサイズ（配布ページに 19.53GB と 21GB の両方の記載あり。落とす直前に現物確認）

---

## 注意

- **このリポジトリは public。** ワークフロー JSON にはプロンプト全文とローカル絶対パスが入るので、
  そのまま push しない。private 化するか、プロンプトを削ってから置く
- 10Eros-Max は beta 段階でファイル構成の入れ替わりが速い。**サイズと版番号はすぐ古くなる**ので、
  落とす直前に配布ページの現物を見ること
