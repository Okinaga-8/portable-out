# portable-out

Portable PJ: code drop-box. Request from iPhone, pick up from any browser (no login).

## 中身

| ファイル | 内容 |
|---|---|
| [`WORKFLOW.md`](WORKFLOW.md) | iPhone で依頼 → GitHub に反映 → PC で確認する手順 |
| [`docs/minimax-h3-10eros-max.html`](docs/minimax-h3-10eros-max.html) | **ComfyUI の MiniMax H3 環境に 10Eros-Max を追加する判断シート**（モデル候補・VRAM 試算・設定・実測ログ） |
| [`tools/h3_env_check.py`](tools/h3_env_check.py) | ComfyUI / GPU / モデルファイルの現状を Markdown で吐き出す |
| `hello.py` | 動作確認用 |

## ComfyUI まわりの使い方

PC で最新を取り込んでから、環境チェックを回す:

```bash
git pull
python tools/h3_env_check.py --comfy "C:\path\to\ComfyUI"
```

出力をそのまま判断シートの「環境メモ」欄か、チャットに貼る。
判断シートはブラウザで直接開ける（Artifact 版は入力内容が保存され、次のチャットから読める）。
