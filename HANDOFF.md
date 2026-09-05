# HANDOFF — 現在地

**最終更新: 2026-09-06 06:18 / 更新者: ローカル(自宅 PC)セッション**

ローカル(自宅 PC)の Claude Code で作業を再開するときに、**最初に読むファイル**。
会話ログは引き継がない。ここと、リポジトリと、Artifact の 3 つで状態が完結するようにしてある。

---

## 進行中のタスク

**ComfyUI の MiniMax H3 環境に 10Eros-Max を追加して、Ref2VA の作風を比較する**

| 場所 | 中身 |
|---|---|
| `docs/minimax-h3-10eros-max.html` | 判断シート本体。**beta4 の実測で全面改訂済み（2026-09-06）**|
| Artifact 版 | https://claude.ai/code/artifact/f9ac898a-cf81-4c0b-a630-98d890e2c532 |
| `.claude/skills/comfyui-h3/SKILL.md` | H3 系の前提知識 |
| `tools/h3_env_check.py` | 実機の状態を Markdown で吐く |

Artifact の db に `env/pc`・`runs`・`checks/state`。**`runs` は 9 件**
（r01-r04 が GGUF 検証、r05 / r06 が beta4 の実測、r07 が 6step 対 8step、
**r08 / r09 が本番画質 1.0MP × 10 秒**）。

---

## ★ 結論から: beta4 INT8 は速度・VRAM で base に勝った。採否は絵と音の判定待ち

**GGUF は見送り済み。beta4 INT8 ConvRot は「形式で選べ」という前回の教訓どおりの結果になった。**

同一セッションで連続計測（両側に暖機を 1 本ずつ入れ、19.5GiB のモデルロードを計測から外した）。

| | H3 base（現行） | 10Eros-Max beta4 INT8 |
|---|---|---|
| 設定 | turbo LoRA / res_multistep / 6 step | turbo 焼き込み / **euler** / 6 step |
| 生成時間（0.4MP・5秒・参照3枚） | 55.79 / 59.54 秒 | **49.08 / 49.18 秒** |
| s/it | 6.09〜6.89 | **5.29〜5.46** |
| ピーク VRAM | 15,554〜15,792 MiB | **15,116〜15,252 MiB** |
| ロード経路 | `19995MB Staged. 208 patches` | **`19995MB Staged. 0 patches`** |
| 温度 | 72〜73C | 74C |

**約 13% 速く、VRAM は 300〜670 MiB 少ない。** GGUF（1.8〜2.6 倍遅く VRAM 増）とは正反対。

### 絵と音 — ここだけ未決。ユーザーの目と耳で決める

- **SSIM Y = 0.699（seed 20260829）/ 0.695（seed 20260830）**
- **ものさしを取り直した。** 同一シーン・同一ワークフローで **seed だけ変えた base 同士が 0.683**。
  → **beta4 は seed を変えるのとほぼ同じだけ絵が変わる。** GGUF（0.745〜0.750）より変化が大きい。
  （`runs/r04` にある「seed変更 0.393」は**別シーンの値なので本件には使えない**。取り違え注意）
- 音は beta4 が明確に大きく、情報量も多い

| | base | beta4 |
|---|---|---|
| Peak dB | -37.6 / -26.3 | **-24.9 / -21.1** |
| Entropy | 0.452 / 0.580 | 0.613 / 0.663 |
| HF_ratio | 0.0008 | 0.0002 / 0.0007 |
| Flat_factor | 0.00 | 0.00（クリップなし）|

**渡した実物**（数値だけで決めない）:

- `compare/B4_s20260829_top-base_bottom-beta4.png`
- `compare/B4_s20260830_top-base_bottom-beta4.png`
- `compare/B4_audio_spec.png`
- 動画 4 本 `ComfyUI/output/video/B4_{base,beta4}_s2026082{9,30}_00001_.mp4`

---

## step 数 — 6 step で回すこと（n=3）

作者は「euler/simple 6〜8 step」と言っているので両方測った。

| | 6 step | 8 step |
|---|---|---|
| 生成時間（seed 20260829 / 30 / 31）| 53.04 / 58.53 / 52.68 秒 | **65.18 / 65.01 / 64.61 秒** |
| s/it | 5.82〜5.91 | 5.85〜5.90 |
| ピーク VRAM | 14,942〜15,471 MiB | 14,804〜15,222 MiB |

**s/it は 6 と 8 で変わらない。** だから 8 step のコストは単純に 2 ステップ分、**約 +11.9 秒（+22%）**。

**そして base（6 step）が 55.8〜59.5 秒なので、beta4 を 8 step で回すと base より 10〜16% 遅い。**
**beta4 の速度優位は 6 step で回してこそ。**

絵の差は seed 依存が大きい: SSIM Y = **0.701**（s20260829）/ 0.804（s20260830）/ **0.836**（s20260831）。
音はほぼ同一（Peak -24.9 対 -24.0 / Entropy 0.613 対 0.629）。

比較画像: `compare/B4s_s20260829_top-6step_bottom-8step.png` /
`compare/B4s_s20260831_top-6step_bottom-8step.png`

### ★ このパイプラインは完全に決定的

別セッション・同 seed・同設定で回した 2 本が **SSIM Y = 1.000000**。
A/B の前提が実測で裏づけられた。**差が出たらそれは本当に条件の差**。

### 計測を汚す事故と、その検出

1 回目の s20260830 6step が 98.85 秒（他は 53 秒前後）になった。原因は**計測中に手動で
8188 にプロンプトを投げたこと**。ログに `Cancelling pending prompt` が残る。

- **s/it は正常のままだった**（5.92）。壊れるのは wall / reported だけ
- **絵は無傷**（上記 SSIM 1.000000 で証明済み）
- `ab_run.py` は 1 回の実行ログに `got prompt` が 2 つ以上、または `Cancelling pending prompt` が
  あれば **`[!] CONTAMINATED`** と印字し、JSON にも `contaminated` として残すようにした
- 汚染された回は捨てて測り直す。`--tag` を付ければファイル名が衝突しない

---

## 本番画質 1.0MP × 10 秒 — 通った

| 項目 | 値 |
|---|---|
| 解像度 / 尺 | **1376 × 768 / 243 フレーム / 10.125 秒 @24fps** |
| step | 6（euler / simple / LoRA なし）|
| **合計時間** | **401.20 秒（6 分 41 秒）** |
| s/it | 55.44 / 55.55 |
| ピーク VRAM | 15,238 MiB（93.1%）|
| 温度 | 最大 79C（スロットリング 83C 手前）|
| 出力 | 2.90 MB。音も 10.125 秒フル（Peak -26.0 dB / Flat 0.00）|

**OOM なし。**`compare/HQ_beta4_1p0MP_10s_f36-96-156-216.png`

### ★★ VRAM ピークは OOM 接近の指標にならない

ピーク 15,238 MiB は**テキストエンコード時**（`MiniMaxH3TEModel_ 14956MB Staged`）の値。
**サンプリング中は 20 秒間隔の nvidia-smi でずっと 13,066〜13,115 MiB（80%）だった。**

0.4MP のときは同じサンプリング中に 15.1〜15.8 GiB 使っている。
つまり **Dynamic VRAM が活性化領域の大きさに合わせて常駐重みを減らしている**。
解像度と尺を上げるほど、重みは VRAM から降りて活性化に場所を譲る。

**→「0.4MP で 96.3%」は「高解像度で危ない」を意味しない。仕組みが自動で釣り合いを取る。**
**→ W4A8 を検討する唯一残っていた理由（VRAM が足りなくなったときの逃げ道）も消えた。**

### 決着: 逆転していなかった。外れ値はアーカイブのほう

base を同じ 1.0MP × 10 秒で連続計測した（どちらも 6 step、それぞれの正しい回し方）。

| | base | beta4 |
|---|---|---|
| 合計時間 | 403.85 秒 | **401.20 秒** |
| s/it | 56.88 / 57.09 | **55.44 / 55.55** |
| サンプリング中 VRAM | 13,404〜13,476 MiB | 13,066〜13,115 MiB |
| 温度 | 79C | 79C |

**beta4 のほうが 2.6% 速い。負けていない。**
疑いの出所だったアーカイブ Run #10 の 48.23 s/it は、**いまの base（57.0）より 18% 速い**。
つまり外れているのは beta4 ではなくアーカイブの数字。
**別セッションの数字と比べてはいけない**（鉄則 0）実例がもう 1 つ増えた。

### ★ ただし beta4 の速度優位は高解像度で縮む

| | 0.4MP × 5 秒 | 1.0MP × 10 秒 |
|---|---|---|
| beta4 の s/it 優位 | **−13%** | **−2.6%** |
| 総時間 | 49.1 対 55.8〜59.5 秒 | 401.20 対 403.85 秒（**実質互角**）|

turbo LoRA の 208 patches は 1 ステップあたり固定のオーバーヘッドなので、
長いシーケンスのアテンション量に対して相対的に小さくなる、と読める。

**→ 本番画質（1.0MP × 10 秒）では、beta4 を選ぶ理由は速度ではなく作風になる。**

### 1.0MP での画質・音

- **SSIM Y = 0.592**（0.4MP では 0.699）。**解像度が上がるほど両者は離れる**
- 音: base `Peak -30.3 / RMS -47.5 / Entropy 0.474 / HF_ratio 0.0026`
  beta4 `Peak -26.0 / RMS -37.6 / Entropy 0.601 / HF_ratio 0.0003`
  → **beta4 は大きくて高域ノイズが 1/9**
- 比較画像: `compare/HQ_1p0MP_10s_top-base_bottom-beta4.png`

---

## 検証済みの事実（推測ではない）

### ダウンロード

`10Eros_Max_h3_TURBO-hybrid_beta4_int8_convrot.safetensors`
= **20,967,637,320 bytes、バイト一致で完了**。置き場は `models/diffusion_models`。

### 形式は base とほぼ同型 — だから Dynamic VRAM に乗った

`scripts/st_probe.py` でヘッダだけ読んで比較した結果:

- base の **932 テンソルすべてが beta4 にも同名・同 shape で存在**。shape 不一致 0
- 量子化レイアウトも同一（I8 x200 = 17.94GiB ＋ U8 スケール x200）
- 差分は **追加キー 2 本**（`adaln_basis` [8,2688] / `adaln_mean` [2688]）と **dtype 112 本**（F16/F32 → BF16）
- メタデータ: `"H3 LoRA merge (orthogonal=False, global_normalize=True)"` — turbo 焼き込みの裏付け
- ロード時に `[WARNING] unet unexpected: ['adaln_basis', 'adaln_mean']` が出るが、
  **base 側の必要キーは全部揃っているので実害なし**（diffusers 変換の残骸）

### beta4 の回し方（現行と違う。守らないと二重掛けになる）

1. **Turbo LoRA を外す。** ログの `0 patches attached` が外れている証拠
2. **euler / simple / 6〜8 step**
3. **i2v 形式では使わない。** ref2va か t2va
4. **既存モデルは消さない**

---

## 実機の状態

- **ComfyUI 0.33.1**（windows portable）／ **RTX 4080 16,376 MiB / sm_89** / RAM 64GB
- driver 610.62 / torch 2.13.0+cu130 / Python 3.13.14
- 起動: `--windows-standalone-build --disable-pinned-memory --use-ck-attention`
- 起動ログに `DynamicVRAM support detected and enabled` / `Using Comfy Kitchen attention`
- comfy-aimdo 0.4.13 / comfy-kitchen 0.2.31
- `custom_nodes/ComfyUI-GGUF` 導入済み（GGUF は見送ったが残してある）

---

## 次の一手

**まずユーザーの判定を待つ。** 速度・VRAM は beta4 の勝ちで確定しているので、
残っているのは「この絵とこの声を採るか」だけ。

**step 数は決着（6 step）。本番画質も通った。W4A8 は不要と判断済み**
（メリット 3 つのうち、解像度・尺の余裕は上限到達済みで潰れ、VRAM の逃げ道も
Dynamic VRAM の挙動で潰れた。残るのは「全部載れば更に速いかも」だけで、
速度で困っていない）。

**この検討は完了。ユーザーは beta4 を採用し、しばらく実運用に入る。**

残っているのは運用中に出てくる話だけ:

- **実運用で作風が合わなければ base に戻す。**両方 `models/diffusion_models/` に置いてある。
  ワークフローは `H3_R2V_KM01_yomi_A.json`（base）と `..._beta4.json`（beta4）が並んでいる
- **より重い条件で OOM したら W4A8 が再浮上する。**それまでは不要（シート 08 節）
- 1.0MP を超える解像度・10 秒を超える尺は未計測

判定が「採らない」なら、`docs/minimax-h3-10eros-max.html` に beta4 の結果を書いて締める。
どちらにせよ**シートと Artifact の HTML はまだ beta4 を反映していない**ので、更新が要る。

---

## beta4 実運用の状態（2026-09-06 時点）

- **採用ファイル**: `10Eros_Max_h3_TURBO-hybrid_beta4_int8_convrot.safetensors`
  （`models/diffusion_models/`、標準の「拡散モデルを読み込む」で読む）
- **回し方**: turbo LoRA をバイパス／euler／simple／**6 step**／ref2va か t2va（i2v では使わない）
- **ワークフロー**
  - `H3_R2V_10E_Max_Trial.json` — beta4 用。**2 件修正済み**（steps 8→6、`filename_prefix`
    の末尾スラッシュ削除）。`.bak` あり
  - `H3_R2V_KM01_yomi_A_beta4.json` — **新規生成**。本番用（1.0MP × 10 秒）の beta4 版。
    元の `H3_R2V_KM01_yomi_A.json` は base のまま無傷
  - **yomi_B / C / D はまだ base 設定。**必要になったら
    `python scripts/wf_beta4_check.py WF.json --to-beta4`
- **ComfyUI は停止済み**（VRAM 解放を確認）

---

## 道具（今回追加・更新した分）

作業フォルダ `MiniMaxH3_work/`。`.bat` は絶対パス直書きなのでリポジトリに入れていない。

| ファイル | 中身 |
|---|---|
| `scripts/ab_run.py` | **API 駆動の A/B ランナー。beta4 対応済み。**モデルごとの sampler / step / LoRA 既定値を `MODELS` 表に持ち、`--plan` で計画を選ぶ。実行前に ComfyUI にファイルの有無を問い合わせる。**割り込みを受けた回を `[!] CONTAMINATED` で自動検出。**`--tag` でファイル名の衝突を回避 |
| `scripts/st_probe.py` | **新規。**safetensors のヘッダだけ読んで 2 ファイルを差分比較する。20GB でも数 MB しか読まない |
| `scripts/ab_grid.py` | **新規。**2 本の動画を同じ時刻で上下に並べた 1 枚を作る。左端に参照画像 |
| `scripts/wf_beta4_check.py` | **新規。**保存済みワークフロー（UI 形式 JSON）を beta4 の要件で検査。`--fix` で steps と末尾スラッシュを修正、`--to-beta4` で base 用から `*_beta4.json` を生成（元ファイルは触らない）|
| `ab_run.py --megapixels / --seconds` | 解像度と尺の上書き。`--seconds 10.0` で 243 フレーム、`--megapixels 1.0` で 1376x768 |
| `ab_run.py --plan solo --model X` | 1 モデル 1 本だけ。「この条件で通るか」の確認用（比較には使わない）|
| `r2v/scripts/audio_probe.py` | 音を数値で見る（Peak / RMS / Flat / Entropy / HF_ratio ＋スペクトログラム）|
| `15_download_10eros_beta4.bat` | beta4 INT8 ConvRot / W4A8。**INT8 は取得済み** |
| `12_install_comfyui_gguf.bat` | ComfyUI-GGUF 導入（この PC の git は `http.sslBackend=schannel` が要る）|
| `40_run_comfyui_h3_ck.bat` | 計測に使った起動 bat |

`ab_run.py` の使い方の要点:

- モデルは**それぞれの正しい回し方で**走らせる（base は LoRA + res_multistep、beta4 は焼き込み + euler）。
  設定を無理に揃えないのは、決めたいのが「どちらを使うか」だから
- `--plan beta4` は**両側に暖機を 1 本ずつ**入れる。チェックポイント切替の 19.5GiB ロードを
  候補側の 1 本目に押し付けると、ありもしない遅さを作ってしまう

---

## 注意

- **このリポジトリは public。** ワークフロー JSON にはプロンプト全文とローカル絶対パスが入るので
  そのまま push しない
- **`filename_prefix` の末尾にスラッシュを付けない。** 連番が効かず上書きされる
- **heredoc にバックスラッシュを書かない。** 今回も `\n` が潰れてパッチが空振りした。`chr(92)` で組む
- 10Eros-Max は beta 段階でファイル構成の入れ替わりが速い。落とす直前に配布ページの現物を見ること
- ローカル PC 側は `.bat` をダブルクリックで回す運用。新しい道具はその形に合わせる
- **ComfyUI は起動したまま。** 追加計測しないなら閉じてよい
