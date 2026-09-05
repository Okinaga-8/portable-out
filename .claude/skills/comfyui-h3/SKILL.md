---
name: comfyui-h3
description: ローカル ComfyUI の MiniMax H3 系（Hailuo H3 / 10Eros-Max などのファインチューン）に関する作業。モデルの選定・量子化の選び方・Turbo LoRA の選択・VRAM 試算・差し替え手順・生成設定・OOM 対処・実測ログの読み書きに使う。「H3」「MiniMax」「Hailuo」「10Eros」「10Eros-Max」「FL2VA」「Ref2VA」「turbo」「ComfyUI で動画生成」などが出てきたら参照すること。LTX-Video / Wan / Krea など別アーキテクチャの話には使わない。
---

# MiniMax H3 系 ローカル運用（RTX 4080 16GB / RAM 64GB）

## この環境の確定情報

- **GPU: RTX 4080 / VRAM 16GB（Ada, SM 8.9）** — NVFP4 のネイティブ演算は無い
- **RAM 64GB** — offload ボトルネックの根本的な解決になる容量
- **CUDA 13** — 4080 系で最も効いた既知の改善策は適用済み。速度問題で CUDA を疑う必要はない
- **主用途 Ref2VA、FL2VA も併用。Turbo LoRA 使用中**

数値や推奨は常にこの構成を前提に答えること。

## 最初に読むもの

**`HANDOFF.md`（リポジトリ直下）** — 現在地・確定事項・未確定・次の一手。
セッションをまたいだ作業はここから始める。作業を終えるときは更新して push する。

## 既存の成果物

- `docs/minimax-h3-10eros-max.html` — 10Eros-Max 導入の判断シート。Artifact として公開済み。
  **更新するときは新規作成せず、この HTML を編集して同じ URL に再デプロイする。**
- `tools/h3_env_check.py` — 実機の GPU / ComfyUI バージョン / models 配下 / 空きディスクを Markdown で吐く。

Artifact には `db` capability がある。**具体的な相談を受けたら、まず `read_db` で読んでから答えること**
（推測より実測が優先）。

| パス | 中身 |
|---|---|
| `env/pc` | ComfyUI/CUDA/torch バージョン、現在の DiT ファイル名、起動オプション |
| `runs`（コレクション） | 1 生成 1 ドキュメント。model / quant / mode / res / frames / steps / turbo / shift / time_sec / peak_vram_gb / seed / note |
| `checks/state` | 導入チェックリストの進捗 |

## 押さえておく前提

**H3 は 4 点セット。** `diffusion_models`(DiT) + `text_encoders`(Qwen3-VL-32B) + `vae`(video) + `vae`(audio)。
ファインチューンを試すときに差し替わるのは **DiT 1 本だけ**。

**FL2VA と Ref2VA は別モデル。** DiT も **Turbo LoRA も共有しない**。
設計上 **Ref2VA は FL2VA より素の画質・音質が落ちる**（参照条件付けの対価）。VRAM も時間も重い。

**hybrid** は FL2VA をベースに、50 ブロックのうち一部の `adaln_proj` だけを Ref2VA から取るマージ。
**hybrid は i2v モードで使わない** — 参照(ref2va)形式か t2va 形式で使う。画像 1 枚でも参照として渡す。

**ComfyUI は 0.30.0 以降が必須**（音声サンプラー修正）。W4A8 ローダーは 0.31.0 以降。
0.31.0 で音声サンプリングの挙動が変わっており、0.30.0 の音を戻す `ComfyUI-MiniMax-H3-LegacySampling` がある。

**audio VAE は fp32 のまま。** fp16 にすると映像と音がズレる。

## 10Eros / 10Eros-Max の見分け（頻出の取り違え）

| 名前 | ベース | 見分け方 |
|---|---|---|
| `TenStrip/10Eros-Max` | **MiniMax H3** | ファイル名に `h3` が入る |
| `TenStrip/LTX2.3-10Eros` | LTX-Video 2.3 | 別アーキテクチャ。TE(Gemma 3)も VAE も違う。流用不可 |

10Eros-Max は H3 の全 50 ブロックを保持し、block 0–31 の fused QKV のみ改変。
特徴は「顔の一貫性」と「弾む・反応の速いモーション」。**静かなカットでは差が出にくい**ので、
A/B は動きのある題材で、参照画像の枚数も揃えて行う。

## 10Eros-Max の版の系譜

| 版 | Turbo | モード | 16GB で入手できる形 |
|---|---|---|---|
| **beta2** | 焼き込みなし | fl2va / ref2va 別ファイル | GGUF Q3〜Q8（Abiray）、NVFP4 |
| test4 pruned | 焼き込みなし | fl2va | GGUF Q3〜Q8（Abiray 無印リポジトリ） |
| beta3 | 焼き込みあり | 実質 t2v のみ（作者「やや壊れている」） | W4A8 11.68GB（berryber09） |
| **beta4** | 焼き込みあり | ref + t2va の hybrid 1 本 | INT8 ConvRot 約 19.5〜21GB。GGUF なし |

**beta4 に非 Turbo 版は存在しない**（作者が「非 Turbo 版は出来が悪い」として作っていない）。
したがって「焼き込み有無」の純粋比較はできない — beta2 と比べると世代・モード構成も同時に変わる。

推奨順（Ref2VA 主用途）: **beta2 ref2va GGUF Q4_K_M（11.6GB）** → beta4 TURBO-hybrid INT8 → beta2 fl2va。

## 16GB での量子化の選び方

| 形式 | サイズ目安 | 判定 |
|---|---|---|
| GGUF Q4_K_M | 約 11.6 GB | **第一候補。** `ComfyUI-GGUF`(city96) が要る |
| W4A8 ConvRot | 11.68 GB | 焼き込み版を小さく試せる唯一の道（ただし beta3 由来） |
| GGUF Q5_K_M | 約 14.1 GB | ぎりぎり。画質寄り |
| GGUF Q3_K_M | 約 8.9 GB | OOM 時の逃げ道 |
| INT8 ConvRot | 約 20〜21 GB | offload 前提。カスタムノード不要 |
| NVFP4 | 10.9 / 13.6 GB | **要検証。** Ada にネイティブ FP4 演算はない。FL2VA 版のみ |
| bf16 | 37.5 GB 超 | 不可 |
| DT-sQKV | 21 GB | ComfyUI 本体パッチが要る。勧めない |

## Turbo LoRA（lightx2v / ModelTC 公式）

| モード | ファイル | 推奨 NFE | 学習解像度 | shift (video/audio) |
|---|---|---|---|---|
| **Ref2VA** | `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16` | 4 | 544p | 12 / 3 |
| FL2VA/T2VA | `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16` | 8 / 4 | 544p | 12 / 3 |
| FL2VA/T2VA | `minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16` | 8 | 768p | 6 / 3 |
| FL2VA/T2VA | `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16` | 4 | 768p | 6 / 3 |

**Ref2VA 用は 4-step v0.1 の 1 種類しかない。** FL2VA 用を流用してはいけない。
**step だけ変えても成立しない** — shift もその LoRA の行に合わせる。
Ref2VA では参照画像のリサイズ方針を **`match`** にする（蒸留学習時と同じ）。
ModelTC が Ref2VA 用ワークフロー JSON（`video_minimax_h3_ref2v_lightx2v_turbo.json`、既定 960×544）を配布。

## 生成設定の既定値

cfg **1.0** / sampler **euler + simple**（10Eros-Max beta4 は LCM/simple 6〜8 step も可）/
sigma shift は上表 / steps **20〜32**（素）・**4〜8**（Turbo）・**6〜8**（beta4）/
解像度 **0.2〜0.8 MP** / 最大 15 秒・24 fps。

## 罠（毎回確認する）

- **Ref2VA に FL2VA 用の Turbo LoRA を当てていないか。** 最頻の事故。
- ファイル名に `TURBO` が入る版は蒸留が焼き込み済み。**Turbo LoRA を重ねない。**
- `pruned` 版には pruned 用の Turbo LoRA を使う（フル版向けとは別物）。
- **Turbo は音を劣化させる。** 下書きに使い、採用シードは Turbo なしで本番を回す。
- **Turbo は VRAM を減らさない。** OOM 対策にはならない。
- **hybrid を i2v で使わない。**
- 低 VRAM では SageAttention が逆効果になりうる。`--use-ck-attention` や sol-attn を先に試す。

## OOM の削り順

解像度 → フレーム数 → VAE Decode 前に Clean VRAM → `--lowvram` → 量子化を 1 段下げる → SageAttention を切る。

起動フラグ: `--lowvram` / `--disable-mmap`（Windows で 20GB 超を読むとき） /
`--disable-pinned-memory`（フリーズ時） / `--use-ck-attention`。

## 一次情報

- <https://github.com/wildminder/awesome-minimax-H3> — 量子化・LoRA・ノードの網羅リスト
- <https://github.com/wildminder/awesome-minimax-H3/blob/main/guides/minimax-h3-performance.md> — GPU 階級別の実測
- <https://github.com/ModelTC/Minimax-H3-Turbo> — Turbo LoRA の公式仕様（モード別・NFE・shift・リサイズ方針）
- <https://docs.comfy.org/tutorials/video/minimax/minimax-h3> — 公式チュートリアル

数値を答える前に、この一次情報を引き直すこと。10Eros-Max は beta 段階で
ファイル構成の入れ替わりが速く、**サイズと版番号はすぐ古くなる**。
