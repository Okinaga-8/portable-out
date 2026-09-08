# portable-out

Portable PJ: code drop-box. Request from iPhone, pick up from any browser (no login).

## 中身

| ファイル | 内容 |
|---|---|
| [`HANDOFF.md`](HANDOFF.md) | **現在地。** 作業を再開するときに最初に読む |
| [`docs/cloud-and-pc.html`](docs/cloud-and-pc.html) | **図解。** スマホのチャットと PC のチャットの違い、portable-out と GitHub の関係（git 初心者向け） |
| [`WORKFLOW.md`](WORKFLOW.md) | iPhone で依頼 → GitHub に反映 → PC で確認する手順／**出先で調べて自宅 PC で使う型** |
| [`docs/minimax-h3-10eros-max.html`](docs/minimax-h3-10eros-max.html) | **ComfyUI の MiniMax H3 環境に 10Eros-Max を追加する判断シート**（モデル候補・VRAM 試算・設定・実測ログ） |
| [`tools/h3_env_check.py`](tools/h3_env_check.py) | ComfyUI / GPU / モデルファイルの現状を Markdown で吐き出す |
| [`tools/h3_prompt_convert.py`](tools/h3_prompt_convert.py) | **日本語の場面メモ → MiniMax H3 プロンプト変換器。** ローカルの llama-server（177B）に繋ぐ |
| [`tools/h3_prompt_rules.md`](tools/h3_prompt_rules.md) | 変換器が読む知識パック。**知見が増えたらここを編集する** |
| [`templates/`](templates/) | 変換器の入力例（場面メモと中間形式）|
| `hello.py` | 動作確認用 |

## ComfyUI まわりの使い方

PC で最新を取り込んでから、環境チェックを回す:

```bash
git pull
python tools/h3_env_check.py --comfy "C:\path\to\ComfyUI"
```

出力をそのまま判断シートの「環境メモ」欄か、チャットに貼る。
判断シートはブラウザで直接開ける（Artifact 版は入力内容が保存され、次のチャットから読める）。

## プロンプト変換器の使い方

日本語で書いた場面メモを、H3 の公式フィールド（`integrated_multimodal_description` /
`overall_soundscape` / `non_diegetic_music`）に落とす。**ローカルの 177B を llama-server で
動かしておく**こと。

```bash
python tools/h3_prompt_convert.py check                        # 疎通確認
python tools/h3_prompt_convert.py auto templates/scene_example.md -o out/
```

段を分けて回すこともできる（中間形式を人が直してから清書する）:

```bash
python tools/h3_prompt_convert.py plan   scene.md   -o scene.yaml
python tools/h3_prompt_convert.py lint   scene.yaml            # LLM を使わない検査だけ
python tools/h3_prompt_convert.py render scene.yaml -o scene.prompt.md
```

**数値は変換器が計算する。**17k+5 のフレーム格子、25 秒（600f）の運用上限、
台詞のモーラ予算、タイミングマーカーの位置は Python 側が決め、LLM には散文しか書かせない。
`lint` は LLM を使わないので、llama-server が落ちていても走る。

> **ComfyUI と 177B は同時に載らない**（H3 は TE 15.7GB + DiT 21GB）。
> プロンプトをまとめて作ってから llama-server を落とし、ComfyUI を起動する。
