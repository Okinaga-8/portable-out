# HANDOFF — 現在地

**最終更新: 2026-09-06 / 更新者: ローカル(自宅 PC)セッション**

ローカル(自宅 PC)の Claude Code で作業を再開するときに、**最初に読むファイル**。
会話ログは引き継がない。ここと、リポジトリと、Artifact の 3 つで状態が完結するようにしてある。

---

## 進行中のタスク

**ComfyUI の MiniMax H3 環境に 10Eros-Max を追加して、Ref2VA の作風を比較する**

| 場所 | 中身 |
|---|---|
| `docs/minimax-h3-10eros-max.html` | 判断シート本体（モデル候補・VRAM・設定・確定/要検証） |
| Artifact 版 | https://claude.ai/code/artifact/f9ac898a-cf81-4c0b-a630-98d890e2c532 |
| `.claude/skills/comfyui-h3/SKILL.md` | H3 系の前提知識 |
| `tools/h3_env_check.py` | 実機の状態を Markdown で吐く |

Artifact の db に `env/pc`・`runs`・`checks/state` がある。**2026-09-06 に実測 4 件を `runs` に記録済み。**

---

## ★ 結論から: GGUF 経路は見送り。beta4 INT8 に進む

**1 本目（Abiray beta2 ref2va GGUF Q4_K_M / 11.6GB）は実測の結果、採用しない。**

| | H3 base（現行） | 10Eros-Max GGUF Q4_K_M |
|---|---|---|
| 生成時間（0.4MP/5秒/6step/参照3枚） | **53.0〜59.8 秒** | **93.7〜137.3 秒** |
| s/it | 6.1〜6.6 | 11.2〜19.3 |
| ピーク VRAM | 15,098〜15,776 MiB | **15,873〜15,965 MiB（97.5%）** |
| 画質差 | — | **SSIM Y 0.745 / 0.750**（n=2） |
| 音 | Peak -37.6 / Entropy 0.452 | Peak -39.2 / Entropy 0.437（同等） |
| 顔 | — | ユーザー判定「一長一短」 |

**1.8〜2.6 倍遅く、VRAM はむしろ増え、変化量は step を 8→6 にするより小さい。割に合わない。**

### なぜ遅いのか — 今回いちばん重要な発見

**決め手はファイルサイズではなく、Dynamic VRAM に乗るかどうか。**

```
base : Model MiniMaxH3 prepared for dynamic VRAM loading. 19995MB Staged. 208 patches attached.
GGUF : Requested to load MiniMaxH3
       loaded partially; 10957.44 MB usable, 10854.08 MB loaded, 468.31 MB offloaded
```

- **19.53GB の INT8 が 16GB で快適に回っていたのは Dynamic VRAM（comfy-aimdo）のおかげ**
- **GGUF はその経路に乗らず、ComfyUI 従来の部分ロードに落ちる**
- ファイルを 11.6GB に小さくして得たものより、仕組みから降りて失ったもののほうが大きい
- `gguf qtypes: F32 (324), Q4_K (208)` — 量子化されているのは 208 テンソルだけ。残り 324 は F32。
  その 208 は Turbo LoRA の対象と完全に同じ集合で、毎ステップ bf16 に展開される

**→ 以後、候補は「safetensors で標準ローダーが読む形式か」で選ぶこと。** サイズは二の次。

### 潰した疑問

- **Turbo LoRA は GGUF にもちゃんと当たっている。** LoRA あり／なしで SSIM Y 0.662（同一なら 1.000）。
  外すと音が生焼けになる（Peak -47.3 dB / Entropy 0.327 対 -39.2 / 0.437）。**映像だけ見ると気づけない。**
- **サーマルではない。** 温度は最大 72C（4080 のスロットリングは 83C 前後）
- **未解明**: 10Eros の実行が回を追って遅くなることがある（93.7 → 137.3 秒）。
  ログ上はオフロード量が減っているのに遅い。VRAM 逼迫（余裕 411MiB）を疑うが**確証なし**

---

## 実機の状態（2026-09-05 実測）

- **ComfyUI 0.33.1**（windows portable）／ **RTX 4080 16,376 MiB / sm_89** / RAM 64GB
- driver 610.62 / torch 2.13.0+cu130 / Python 3.13.14 / 空き 578.2 GB
- 起動: `--windows-standalone-build --disable-pinned-memory --use-ck-attention`
- **`custom_nodes/ComfyUI-GGUF` 導入済み**（gguf 0.19.0）。UI では `Unet Loader (GGUF)` として出る。
  **標準の「拡散モデルを読み込む」には .gguf は絶対に出ない**（拡張子が対象外。別ノードが要る）

### Turbo LoRA — 前回の「確定」を撤回済み（2026-09-05）

シートは「pruned には Full 向け Turbo LoRA が効かない（AdaLN が別構造）」「高速化は PDD-Acc のみ」と
していたが、**この環境の実ファイルには当てはまらない。**

- Turbo LoRA の対象は **208 モジュール**（`blocks.0-49` × attn.qkv_proj / attn.out_proj / mlp.fc1 / mlp.fc2
  ＋ `token_refiner.blocks.0-1` × 同 4 種）
- pruned INT8 DiT と **208/208 が厳密一致。ミス 0**
- **LoRA 内に adaln 系キーは 0 本** → 落ちるものが無い
- 実行ログの `208 patches attached` とも一致
- → **PDD-Acc は「唯一の高速化経路」ではない。**優先度は低い

---

## 次の一手

**`15_download_10eros_beta4.bat`（ローカル作業フォルダ）を実行する。**

| 選択 | ファイル | サイズ | 位置づけ |
|---|---|---|---|
| 1 | `10Eros_Max_h3_TURBO-hybrid_beta4_int8_convrot.safetensors` | **20,967,637,320 bytes** | **本命。**いまのモデルとほぼ同サイズ・同形式なので Dynamic VRAM に乗るはず |
| 2 | `10Eros_Max_h3_TURBO-hybrid_beta4_w4a8.safetensors` | **12,538,134,464 bytes** | 軽いが未検証。ComfyUI 0.31.0+ のネイティブ W4A8 ローダー（要件は満たす） |

**保留だった「beta4 は 19.53GB か 21GB か」は解決。**同じファイルの GiB 表記と GB 表記だった
（20,967,637,320 bytes = 19.53 GiB = 20.97 GB）。

**シートに無い新情報**: beta4 の W4A8 版が存在する（berryber09）。シートは beta3 版しか把握していなかった。

### beta4 の使い方は現行と違う（重要）

1. **Turbo LoRA を外す。** beta4 は焼き込み済み。`ref2v_turbo_4step_v0.1` を付けたままだと二重掛け
2. **euler / simple / 6〜8 step**（作者記述: "For beta_4 use euler/simple 6-8 steps on all modes"）
3. **i2v 形式では使わない。** 参照（ref2va）形式か t2va 形式で
4. **既存ファイルは消さない**

### 落としたあとの測り方

**鉄則 0（比較する 2 条件は連続して測る）と鉄則 1（暖機）を守ること。**
`scripts/ab_run.py` が API 経由で全部やる。UI 操作は不要。

```
python scripts/ab_run.py --plan full          # 暖機 + base 2 本 + 対象 2 本
python scripts/ab_run.py --plan recover       # 3 本（LoRA なし検証を含む）
python scripts/ab_run.py --dry-run            # 投げずに計画だけ表示
```

beta4 用には `ab_run.py` の `GGUF` 定数と `make_payload` を書き換える必要がある
（beta4 は safetensors なので `UNETLoader` のまま `unet_name` を変えるだけ。GGUF より単純）。
**LoRA を外す実行は `use_lora=False` で既に対応済み**（`strip_lora` がノードを削って配線を張り替える）。

---

## ローカル作業フォルダの道具（public には置かない）

`.bat` は絶対パス直書きなのでリポジトリに入れていない。すべて ASCII + CRLF。

| ファイル | 中身 |
|---|---|
| `12_install_comfyui_gguf.bat` | ComfyUI-GGUF 導入（**この PC の git は `http.sslBackend=schannel` が要る**）|
| `13_probe_10eros_gguf.bat` | 先頭 2MB だけ落として GGUF ヘッダを検証 |
| `14_download_10eros_max.bat` | beta2 GGUF（Q4_K_M / Q3_K_M / Q5_K_M）|
| **`15_download_10eros_beta4.bat`** | **beta4 INT8 ConvRot / W4A8。次はこれ** |
| `scripts/gguf_probe.py` | GGUF ヘッダ解析 |
| `scripts/ab_run.py` | **API 駆動の A/B ランナー**（時間・ピーク VRAM・温度・クロック記録）|

---

## 注意

- **このリポジトリは public。** ワークフロー JSON にはプロンプト全文とローカル絶対パスが入るので
  そのまま push しない
- **`filename_prefix` の末尾にスラッシュを付けない。** 連番が効かず上書きされる（一度これで実測を失った）
- 10Eros-Max は beta 段階でファイル構成の入れ替わりが速い。落とす直前に配布ページの現物を見ること
- ローカル PC 側は `.bat` をダブルクリックで回す運用。新しい道具はその形に合わせる
