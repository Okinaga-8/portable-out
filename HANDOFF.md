# HANDOFF — 現在地

**最終更新: 2026-09-05 / 更新者: ローカル(自宅 PC)セッション**

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
2026-09-05 に `env/pc` と `checks/state` を実測値で更新済み。`runs` はまだ空。

---

## 実機の状態（2026-09-05 実測 / `tools/h3_env_check.py`）

- **ComfyUI 0.33.1**（windows portable）— 0.33.0 以降の要件はクリア
- **RTX 4080 / VRAM 16,376 MiB / sm_89**、RAM 64GB、driver 610.62、torch 2.13.0+cu130、Python 3.13.14
- 起動オプション: `--windows-standalone-build --disable-pinned-memory --use-ck-attention`
- 空きディスク **578.2 GB**（GGUF Q4_K_M も INT8 も置ける）
- `models/diffusion_models/` に 3 本 — `ref2va_pruned_int8_convrot`（主用途 / 19.53GB）、
  `fl2va_pruned_int8_convrot`、**`PinkCherry_fl2va_..._pruned_int8_convrot-beta-0.6`**
  → **派生モデルを DiT だけ差し替えて回した実績がすでにある**（`PiCh_Try_01.json`）
- `models/loras/` に 3 本 — `ref2v_turbo_4step_v0.1` / `fl2v_turbo_8step_v1.0` / `fl2v_turbo_4step_v1.0_768p`
- **`custom_nodes/` が空**（stock の `example_node.py.example` と `websocket_image_save.py` のみ）

---

## 確定していること

- **GPU: RTX 4080 / VRAM 16GB（Ada, SM 8.9）、RAM 64GB、CUDA 13**
- **DiT: `minimax_h3_ref2va_pruned_int8_convrot.safetensors`**（Ref2VA / **pruned** / INT8 ConvRot / 19.53GB）
  → 19.53GB が 16GB で回っている = offload が効いた状態で成立済み
- 主用途 **Ref2VA**、FL2VA も併用

### ★ 前回の「確定」を 1 つ撤回する（2026-09-05 / キー照合による実測）

前回のシート・HANDOFF は
**「pruned には Full 向け Turbo LoRA が効かない（AdaLN が 2688 次元 vs 8 次元で別構造）」
「pruned Ref2VA の高速化は PDD-Acc 経路のみ」**
と書いていた。**この環境の実ファイルには当てはまらない。**

safetensors のヘッダを直接読んで照合した結果:

| | 実測 |
|---|---|
| ワークフローの組み合わせ | **モード一致で正しい**。`ref2va` DiT + `ref2v_turbo_4step_v0.1` 1.00 ／ `fl2va` DiT + `fl2v_turbo_8step_v1.0` 1.00 |
| Turbo LoRA の対象モジュール | **208 個** = `blocks.0-49` × (`attn.qkv_proj` / `attn.out_proj` / `mlp.fc1` / `mlp.fc2`) + `token_refiner.blocks.0-1` × 同 4 種 |
| pruned INT8 DiT との一致 | **208 / 208 が `.weight` で厳密一致。ミス 0** |
| LoRA 内の adaln 系キー | **0 本** |
| DiT 側の adaln | pruned 形（`blocks.N.adaln_proj.linear` F16 [96768, 8] + `adaln_t_table` F32 [1025, 8]／50 + `final_layer` = 51 本） |

**LoRA はそもそも AdaLN を対象にしていない**ので、「AdaLN が黙って落とされている」状態ではない。
DiT 側が pruned 形の AdaLN を持っていても、LoRA は触りに行かない。

- → **PDD-Acc は「唯一の高速化経路」ではない。** 既存の Turbo は実測でも効いている（8step で 1.95 倍）。
- → ただし **「キーが全部当たる」＝「pruned に最適」ではない。**
  LoRA の metadata の `base_model` は `minimax_h3_fl2va_bf16.safetensors`（= full bf16）なので、
  当たり先は揃っていても学習元は full。**数値的な最適性までは保証しない。**
  PDD-Acc は「壊れているものの修理」ではなく「別の加速手段」として評価すべき。

### そのほか確定

- **`pruned` 用変換 LoRA は FL2VA 側にしか存在しない**（配布状況の話。上の実測とは別）
- ComfyUI 0.33.1 なので **PDD-Acc の版要件（0.33.0+）は満たす**

---

## 未確定 — 次の一手はこれ

1. **ブロッカー: `custom_nodes/` が空。ComfyUI-Manager も入っていない。**
   方針の 1 本目（GGUF Q4_K_M）は **ComfyUI-GGUF を手動で入れないと始まらない**。
   → **ローカル作業フォルダに道具を用意済み**（2026-09-05。`.bat` はローカル専用、public には置かない）:

   | 順 | 道具 | 中身 |
   |---|---|---|
   | 1 | `12_install_comfyui_gguf.bat` | city96/ComfyUI-GGUF を clone + `gguf` パッケージ導入。**この PC の git は openssl バックエンドで証明書エラーになるので `http.sslBackend=schannel` を指定してある** |
   | 2 | `13_probe_10eros_gguf.bat` | **先頭 2MB だけ**落として GGUF ヘッダを読み、テンソル名が実機の H3 DiT と一致するか判定（`scripts/gguf_probe.py`） |
   | 3 | `14_download_10eros_max.bat` | Q4_K_M 11.6GB / Q3_K_M 8.9GB / Q5_K_M 14.1GB から選んで `models/unet` へ。resume + バイト数検証 |

   **なぜ probe を挟むか**: 上流の city96/ComfyUI-GGUF には **`minimax` の参照が 1 件も無い**
   （GitHub コード検索で 0 件。同リポジトリは fork ではないのでインデックス済み）。
   ComfyUI 本体が H3 を知っているので、ローダーが素通しならそのまま読める見込みはあるが、
   **確証は無い。** 11.6GB を捨てる前に 2MB で判定する。
   モデルカードは「ComfyUI-GGUF（city96）を Manager で入れて `Unet Loader (GGUF)` を使う」
   「`ComfyUI/models/unet` に置く」と書いている。

   ファイル名とサイズは 2026-09-05 に Hugging Face API で現物確認済み:
   `10Eros-Max-Ref2VA-Beta2-Pruned-Q4_K_M.gguf` = 11,564,180,576 bytes。
   **`Q4_K_S` と `Q5_K_S` は `Q4_K_M` / `Q5_K_M` とバイト数が完全同一**で、
   配布側の取り違えが疑わしい。K_M 側だけを候補に出してある。
2. **基準線（Q2）はまだ測っていない。** ただし**いま測っても A/B には使えない。**
   計測の鉄則 0「比較したい 2 条件は連続して測る」と鉄則 1「暖機してから測る」により、
   **モデルを落として node を入れたあと、暖機してから base と 10Eros を背中合わせで測る**のが正しい。
   数時間離れた Run を引き算すると、過去に一度誤った結論を出している。
3. GGUF を `models/unet` と `models/diffusion_models` のどちらに置くか（Q4）は
   ComfyUI-GGUF を入れてからでないと判定できない。

## 決まっている方針

- **1 本目**: Abiray `10Eros-Max-ref2va-Beta2-GGUF` の **Q4_K_M（約 11.6GB）** + ComfyUI-GGUF。
  非 Turbo 焼き込みなので、いまの運用を変えずに DiT だけ差し替えられる
- **既存ファイルは消さない。** ワークフローを複製し、DiT ローダーだけ差し替える（同一シード A/B のため）
  → **`PiCh_Try_01.json` が同じ形の先例**なので、それを複製するのが早い
- **2 本目**: beta4 `TURBO-hybrid` INT8（約 19.5〜21GB）。**Turbo LoRA は外す**、euler/simple 6〜8 step、
  **i2v 形式では使わない**（参照 or t2va 形式で）
- A/B は**動きのある題材**で。参照画像の枚数も揃える

## 保留

- NVFP4 版が Ada で動くか（FL2VA 版しか無いので主用途から外れる。優先度低）
- beta4 INT8 の正確なサイズ（配布ページに 19.53GB と 21GB の両方の記載あり。落とす直前に現物確認）
- PDD-Acc（`ComfyUI-MiniMax-H3-PDD-Acc` + `MiniMax-H3-Ref2VA-Acc-8Step.safetensors` 1.28GB）。
  **版要件は満たしている**が、既存 Turbo が機能している以上、10Eros-Max より優先度は低い。
  やるなら 10Eros-Max の A/B が終わってから、変数を 1 つだけ動かして測る

---

## 注意

- **このリポジトリは public。** ワークフロー JSON にはプロンプト全文とローカル絶対パスが入るので、
  そのまま push しない。private 化するか、プロンプトを削ってから置く
- 10Eros-Max は beta 段階でファイル構成の入れ替わりが速い。**サイズと版番号はすぐ古くなる**ので、
  落とす直前に配布ページの現物を見ること
- ローカル PC 側は `.bat` をダブルクリックで回す運用。新しい道具を足すときはその形に合わせる
  （番号付き `.bat` / ASCII のみ / CRLF）
