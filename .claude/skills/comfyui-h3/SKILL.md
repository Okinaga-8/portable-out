---
name: comfyui-h3
description: ローカル ComfyUI の MiniMax H3 系（Hailuo H3 / 10Eros-Max などのファインチューン）に関する作業。モデルの選定・量子化の選び方・VRAM 試算・差し替え手順・生成設定・OOM 対処・実測ログの読み書きに使う。「H3」「MiniMax」「Hailuo」「10Eros」「10Eros-Max」「FL2VA」「Ref2VA」「ComfyUI で動画生成」などが出てきたら参照すること。LTX-Video / Wan / Krea など別アーキテクチャの話には使わない。
---

# MiniMax H3 系 ローカル運用（RTX 4080 16GB / RAM 64GB）

このリポジトリのオーナーの実機は **RTX 4080（VRAM 16GB, Ada, SM 8.9）+ RAM 64GB**。
数値や推奨は常にこの構成を前提に答えること。

## 既存の成果物

- `docs/minimax-h3-10eros-max.html` — 10Eros-Max 導入の判断シート（モデル候補表・VRAM・設定・実測ログ）。
  Artifact として公開済み。**更新するときは新規作成せず、この HTML を編集して同じ URL に再デプロイする。**
- `tools/h3_env_check.py` — 実機の GPU / ComfyUI バージョン / models 配下 / 空きディスクを Markdown で吐く。
  作業の起点。`python tools/h3_env_check.py --comfy <ComfyUI のパス>`

Artifact には `db` capability があり、次の 3 つが入っている。**具体的な相談を受けたら、
まず `read_db` でこれを読んでから答えること**（推測より実測が優先）。

| パス | 中身 |
|---|---|
| `env/pc` | 実機の ComfyUI/CUDA/torch バージョン、現在の DiT ファイル名、起動オプション |
| `runs`（コレクション） | 1 生成 1 ドキュメント。model / quant / mode / res / frames / steps / turbo / time_sec / peak_vram_gb / seed / note |
| `checks/state` | 導入チェックリストの進捗 |

## 押さえておく前提

**H3 は 4 点セット。** 1 つの checkpoint ではない。
`diffusion_models`(DiT) + `text_encoders`(Qwen3-VL-32B) + `vae`(video) + `vae`(audio) を別々のローダーで読む。
ファインチューンを試すときに差し替わるのは **DiT 1 本だけ**。TE と VAE は流用できる。

**モードは 2 つ。** `FL2VA`（画像 0/1/2 枚 → T2V/I2V/始点終点）と `Ref2VA`（画像 9・動画 3・音声 3 まで参照）。
DiT ファイルはモードごとに別。ユーザーが使っている側と揃える。

**ComfyUI は 0.30.0 以降が必須**（音声サンプラー修正）。0.31.0 で音声サンプリングの挙動が変わっており、
0.30.0 の音を戻す `ComfyUI-MiniMax-H3-LegacySampling` が存在する。

**audio VAE は fp32 のまま。** fp16 にすると映像と音がズレる。

## 10Eros / 10Eros-Max の見分け（頻出の取り違え）

| 名前 | ベース | 見分け方 |
|---|---|---|
| `TenStrip/10Eros-Max` | **MiniMax H3** | ファイル名に `h3` が入る。今の環境で動く |
| `TenStrip/LTX2.3-10Eros` | LTX-Video 2.3 | 別アーキテクチャ。TE(Gemma 3)も VAE も違う。流用不可 |

10Eros-Max は H3 の全 50 ブロックを保持し、block 0–31 の fused QKV のみ改変した派生。
特徴は「顔の一貫性」と「弾む・反応の速いモーション」。静かなカットでは差が出にくいので、
A/B は**動きのある題材**で行う。

## 16GB での量子化の選び方

| 形式 | サイズ目安 | 判定 |
|---|---|---|
| GGUF Q4_K_M | 約 11.6 GB | **第一候補。** `ComfyUI-GGUF`(city96) が要る |
| GGUF Q5_K_M | 約 14.1 GB | ぎりぎり。画質寄り |
| GGUF Q3_K_M | 約 8.9 GB | OOM 時の逃げ道 |
| INT8 ConvRot | 約 21 GB | 既存 H3 が INT8 で回っているなら同条件。カスタムノード不要 |
| NVFP4 | 10.9 / 13.6 GB | **要検証。** Ada にネイティブ FP4 演算はない。断定しないこと |
| bf16 | 40 GB 超 | 不可 |
| DT-sQKV | 21 GB | ComfyUI 本体パッチが要る。勧めない |

## 生成設定の既定値

cfg **1.0** / sampler **euler + simple**（または res_multistep）/ sigma shift **video 12, audio 3** /
steps **20〜32**（本番）・**4〜8**（Turbo 併用）/ 解像度 **0.2〜0.8 MP** / 最大 15 秒・24 fps。

## 罠（毎回確認する）

- ファイル名に `TURBO` が入る版は蒸留が焼き込み済み。**Turbo LoRA を重ねない。**
- `pruned` 版には pruned 用の Turbo LoRA を使う（フル版向けとは別物）。
- **Turbo は音を劣化させる。** 下書きに使い、採用シードは Turbo なしで本番を回す。
- **Turbo は VRAM を減らさない**（実測でピーク VRAM ほぼ同じ）。OOM 対策にはならない。
- 低 VRAM では SageAttention が逆効果になりうる。`--use-ck-attention` や sol-attn を先に試す。
- 生成が桁違いに遅いときは、モデルより先に **CUDA のバージョン**を疑う（12.6→13 で大幅改善の報告）。

## OOM の削り順

解像度 → フレーム数 → VAE Decode 前に Clean VRAM → `--lowvram` → 量子化を 1 段下げる → SageAttention を切る。

起動フラグ: `--lowvram` / `--disable-mmap`（Windows で 20GB 超を読むとき） /
`--disable-pinned-memory`（フリーズ時） / `--use-ck-attention`。

## 一次情報

- <https://github.com/wildminder/awesome-minimax-H3> — 量子化・LoRA・ノードの網羅リスト
- <https://github.com/wildminder/awesome-minimax-H3/blob/main/guides/minimax-h3-performance.md> — GPU 階級別の実測
- <https://docs.comfy.org/tutorials/video/minimax/minimax-h3> — 公式チュートリアル

数値を答える前に、この 2 つの一次情報を引き直すこと。10Eros-Max は beta 段階で
ファイル構成の入れ替わりが速く、**サイズと版番号はすぐ古くなる**。
