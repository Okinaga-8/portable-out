#!/usr/bin/env python3
"""ComfyUI / MiniMax H3 環境チェッカー

10Eros-Max を試す前に、いまの環境を Markdown で吐き出す。
標準ライブラリだけで動く（torch があれば追加情報も出す）。

使い方:
    python tools/h3_env_check.py --comfy "C:\\path\\to\\ComfyUI"
    python tools/h3_env_check.py --comfy ~/ComfyUI --out report.md

--comfy を省略すると、よくある場所を順に探す。
出力はそのまま docs/minimax-h3-10eros-max.html の「環境メモ」欄か、
チャットに貼り付けられる形式。
"""

from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

# models 配下で拾うフォルダと、H3 関連として強調する語
MODEL_DIRS = ["diffusion_models", "unet", "text_encoders", "clip", "vae", "loras"]
H3_HINTS = (
    "minimax", "h3", "10eros", "eros", "qwen3vl", "qwen3_vl",
    "hailuo", "turbo", "lightx2v", "convrot", "nvfp4",
)
# 導入されていると挙動に効くカスタムノード
NODE_HINTS = (
    "gguf", "minimax", "h3", "kjnodes", "sage", "sol-attn", "solattn",
    "spectrum", "easycache", "cache", "turbo", "orbitquant", "clipproj",
)


def run(cmd: list[str]) -> str:
    """外部コマンドを叩いて stdout を返す。失敗したら空文字。"""
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=20, check=False
        )
        return out.stdout.strip()
    except Exception:
        return ""


def human(nbytes: int) -> str:
    gb = nbytes / (1024 ** 3)
    if gb >= 1:
        return f"{gb:.2f} GB"
    return f"{nbytes / (1024 ** 2):.0f} MB"


def find_comfy(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.is_dir() else None
    home = Path.home()
    candidates = [
        Path.cwd(),
        home / "ComfyUI",
        home / "Documents" / "ComfyUI",
        home / "Desktop" / "ComfyUI",
        home / "AppData" / "Roaming" / "ComfyUI",
        Path("C:/ComfyUI"),
        Path("C:/ComfyUI_windows_portable/ComfyUI"),
        Path("D:/ComfyUI"),
        Path("D:/ComfyUI_windows_portable/ComfyUI"),
    ]
    for c in candidates:
        try:
            if (c / "models").is_dir() and (c / "comfy").is_dir():
                return c
        except OSError:
            continue
    return None


def comfy_version(root: Path) -> str:
    """ComfyUI のバージョンを、置いてありそうな場所から拾う。"""
    vf = root / "comfyui_version.py"
    if vf.is_file():
        m = re.search(r"__version__\s*=\s*[\"']([^\"']+)", vf.read_text(errors="ignore"))
        if m:
            return m.group(1)
    pj = root / "pyproject.toml"
    if pj.is_file():
        m = re.search(r"^version\s*=\s*[\"']([^\"']+)", pj.read_text(errors="ignore"), re.M)
        if m:
            return m.group(1)
    head = run(["git", "-C", str(root), "describe", "--tags", "--always"])
    return head or "不明"


def gpu_block() -> list[str]:
    lines: list[str] = []
    q = run([
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,memory.used",
        "--format=csv,noheader",
    ])
    if q:
        for row in q.splitlines():
            lines.append(f"- GPU: `{row.strip()}`")
    else:
        lines.append("- GPU: `nvidia-smi が見つからない / 実行できない`")

    smi = run(["nvidia-smi"])
    m = re.search(r"CUDA Version:\s*([\d.]+)", smi)
    lines.append(f"- ドライバが報告する CUDA: `{m.group(1) if m else '不明'}`")

    try:
        import torch  # type: ignore

        lines.append(f"- PyTorch: `{torch.__version__}`")
        lines.append(f"- PyTorch のビルド CUDA: `{getattr(torch.version, 'cuda', None) or '不明'}`")
        lines.append(f"- torch.cuda.is_available(): `{torch.cuda.is_available()}`")
        if torch.cuda.is_available():
            cap = torch.cuda.get_device_capability(0)
            total = torch.cuda.get_device_properties(0).total_memory
            lines.append(f"- Compute capability: `sm_{cap[0]}{cap[1]}`（NVFP4 のネイティブ演算は sm_100 以降）")
            lines.append(f"- VRAM: `{human(total)}`")
    except Exception:
        lines.append("- PyTorch: `この Python からは import できない`"
                     "（ComfyUI 同梱の Python で実行すると出ます）")
    return lines


def models_block(root: Path) -> list[str]:
    lines: list[str] = []
    models = root / "models"
    if not models.is_dir():
        return ["- `models/` が見つかりません"]

    for sub in MODEL_DIRS:
        d = models / sub
        if not d.is_dir():
            continue
        try:
            files = [f for f in d.iterdir() if f.is_file() and f.suffix.lower() in
                     (".safetensors", ".gguf", ".ckpt", ".pt", ".sft", ".bin")]
        except OSError:
            continue
        if not files:
            continue
        files.sort(key=lambda f: f.name.lower())
        lines.append(f"\n**models/{sub}/**\n")
        for f in files:
            try:
                size = human(f.stat().st_size)
            except OSError:
                size = "?"
            low = f.name.lower()
            mark = " ← H3 関連" if any(h in low for h in H3_HINTS) else ""
            lines.append(f"- `{f.name}` — {size}{mark}")
    return lines or ["- モデルファイルが見つかりません"]


def nodes_block(root: Path) -> list[str]:
    d = root / "custom_nodes"
    if not d.is_dir():
        return ["- `custom_nodes/` が見つかりません"]
    try:
        names = sorted(p.name for p in d.iterdir() if p.is_dir() and not p.name.startswith("."))
    except OSError:
        return ["- `custom_nodes/` を読めません"]
    if not names:
        return ["- カスタムノードなし"]
    lines = []
    for n in names:
        low = n.lower()
        mark = " ← 関連" if any(h in low for h in NODE_HINTS) else ""
        lines.append(f"- `{n}`{mark}")
    return lines


def disk_block(root: Path) -> list[str]:
    try:
        usage = shutil.disk_usage(root)
    except OSError:
        return ["- 空き容量を取得できません"]
    free_gb = usage.free / (1024 ** 3)
    verdict = "GGUF Q4_K_M(約12GB)も INT8(約22GB)も置ける"
    if free_gb < 15:
        verdict = "**GGUF Q4_K_M(約12GB)がぎりぎり。INT8 は不足**"
    elif free_gb < 27:
        verdict = "GGUF Q4_K_M は可。INT8(約22GB)は余裕がない"
    return [
        f"- ドライブ: `{root.anchor or root}`",
        f"- 空き: `{free_gb:.1f} GB` / 全体 `{usage.total / (1024 ** 3):.0f} GB`",
        f"- 判定: {verdict}",
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="ComfyUI / MiniMax H3 環境チェッカー")
    ap.add_argument("--comfy", help="ComfyUI のルートフォルダ")
    ap.add_argument("--out", help="Markdown の書き出し先（省略時は標準出力のみ）")
    args = ap.parse_args()

    root = find_comfy(args.comfy)

    out: list[str] = []
    out.append("# ComfyUI / MiniMax H3 環境レポート\n")
    out.append(f"- 生成: `{platform.node()}` / `{platform.platform()}`")
    out.append(f"- Python: `{sys.version.split()[0]}` (`{sys.executable}`)")
    out.append("")

    out.append("## GPU / ドライバ\n")
    out += gpu_block()
    out.append("")

    if root is None:
        out.append("## ComfyUI\n")
        out.append("- **見つかりませんでした。** `--comfy` でパスを指定して再実行してください。")
        out.append("  例: `python tools/h3_env_check.py --comfy \"C:\\ComfyUI\"`")
    else:
        out.append("## ComfyUI\n")
        out.append(f"- ルート: `{root}`")
        out.append(f"- バージョン: `{comfy_version(root)}`（10Eros-Max には 0.30.0 以降が必要）")
        out.append("")
        out.append("## ディスク\n")
        out += disk_block(root)
        out.append("")
        out.append("## モデルファイル\n")
        out += models_block(root)
        out.append("")
        out.append("## カスタムノード\n")
        out += nodes_block(root)

    out.append("")
    out.append("---")
    out.append("次に確認すること: 上の `models/diffusion_models`（または `unet`）にある H3 の "
               "DiT ファイル名を見て、`fl2va` か `ref2va` か、`pruned` が付くかを控える。"
               "それが 10Eros-Max のどの版を落とすかを決めます。")

    text = "\n".join(out)
    print(text)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"\n[書き出しました: {args.out}]", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
