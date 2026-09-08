#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""h3_prompt_convert.py — 日本語の場面メモ → MiniMax H3 プロンプト変換器

ローカルの llama-server（llama.cpp）に繋ぎ、2 段で変換する。

    段1  plan    日本語の場面メモ  →  YAML 中間形式（人が直せる）
    段2  render  YAML 中間形式     →  H3 プロンプト（5 層 / 公式フィールド名）

設計の要:
  **数値は Python 側が持つ。LLM には散文しか書かせない。**
  フレーム格子（length %% 17 == 5）、尺の上限（25 秒 = 600f）、モーラ予算、
  タイミングマーカーの位置は、すべてこちらで計算して LLM に渡す。
  LLM が返した数値は採用せず、こちらの値で上書きする。

知識は tools/h3_prompt_rules.md にある。知見が増えたらそちらを編集する。

使い方:
    python tools/h3_prompt_convert.py check
    python tools/h3_prompt_convert.py plan   scene.md   -o scene.yaml
    python tools/h3_prompt_convert.py render scene.yaml -o scene.prompt.md
    python tools/h3_prompt_convert.py auto   scene.md   -o out/
    python tools/h3_prompt_convert.py lint   scene.yaml
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES_DEFAULT = HERE / "h3_prompt_rules.md"

# --------------------------------------------------------------------------
# 1. フレーム格子と尺 —— すべて実測値。docs/minimax-h3-video-concat.html §8c
# --------------------------------------------------------------------------

FPS = 24
GRID_STEP = 17          # length % 17 == 5 の格子
GRID_REM = 5

FRAMES_MIN = 107        # 4.458 s — 公式仕様の下限 4 s の次の格子点
FRAMES_SPEC_MAX = 362   # 15.083 s — 公式仕様の上限
FRAMES_OPERATIONAL = 600  # 25.000 s — 実測で 20 秒と同じ性格。運用はここで固定
FRAMES_CLIFF = 736      # 30.667 s — 完走するが 3 指標が同時に曲がる（VRAM 余裕 694 MiB）

MORA_PER_SEC = 6.0      # 話速の目安。台帳 §6b
MORA_LINE_MIN = 20      # 1 発話あたりの目安（3.5〜4.5 秒 ぶん）
MORA_LINE_MAX = 27

SPEECH_TAIL_SEC = 0.22
DEAD_AIR_TOLERANCE = 2.5  # 台詞から出した必要尺をこれ以上超えたら「余り」とみなす  # セリフはクリップ終端のこれだけ手前に張り付く（実測 3 本）


def frames_for_seconds(seconds: float, fps: int = FPS) -> int:
    """秒数を 17k+5 格子の次の格子点に切り上げる。"""
    target = seconds * fps
    k = math.ceil((target - GRID_REM) / GRID_STEP)
    return GRID_STEP * max(k, 0) + GRID_REM


def seconds_for_frames(frames: int, fps: int = FPS) -> float:
    return frames / float(fps)


def on_grid(frames: int) -> bool:
    return frames % GRID_STEP == GRID_REM


def grid_neighbours(frames: int) -> tuple[int, int]:
    """格子から外れた値の、下と上のいちばん近い格子点。"""
    k = (frames - GRID_REM) / GRID_STEP
    lo = GRID_STEP * max(int(math.floor(k)), 0) + GRID_REM
    hi = GRID_STEP * max(int(math.ceil(k)), 0) + GRID_REM
    return lo, hi


def fmt_timecode(seconds: float) -> str:
    """00:03.000 形式。H3 のタイミングマーカーはこの書式。"""
    seconds = max(0.0, seconds)
    mm = int(seconds // 60)
    ss = seconds - mm * 60
    return f"{mm:02d}:{ss:06.3f}"


# --------------------------------------------------------------------------
# 2. モーラ計算 —— 台詞の実尺を見積もる
# --------------------------------------------------------------------------

_SMALL_KANA = set("ぁぃぅぇぉゃゅょゎゕゖァィゥェォャュョヮヵヶ")
_SKIP = set(" 　\t\n。、，．,.!！?？「」『』（）()…‥ー-−―~〜:：;；\"'")
# ー（長音）は 1 モーラなので _SKIP から除く
_SKIP.discard("ー")


def _is_kana(ch: str) -> bool:
    o = ord(ch)
    return 0x3041 <= o <= 0x309F or 0x30A1 <= o <= 0x30FF


def _is_kanji(ch: str) -> bool:
    o = ord(ch)
    return 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF


def count_mora(text: str) -> tuple[int, bool]:
    """モーラ数と「かなだけで数えきれたか」を返す。

    拗音（ゃゅょ等）は直前と合体して 1 モーラ。っ・ん・ー は 1 モーラ。
    漢字が残っていると読みが確定しないので概算になる（1 字 = 2 モーラ仮置き）。
    """
    mora = 0
    exact = True
    for ch in text:
        if ch in _SKIP:
            continue
        if ch in _SMALL_KANA:
            continue
        if _is_kana(ch):
            mora += 1
        elif _is_kanji(ch):
            mora += 2
            exact = False
        elif ch.isalnum():
            mora += 1
            exact = False
        # それ以外の記号は無視
    return mora, exact


def speech_seconds(text: str) -> tuple[float, bool]:
    mora, exact = count_mora(text)
    return mora / MORA_PER_SEC, exact


# --------------------------------------------------------------------------
# 3. llama-server クライアント（stdlib のみ）
# --------------------------------------------------------------------------

class LlamaServerError(RuntimeError):
    pass


class LlamaServer:
    """llama.cpp の llama-server が出す OpenAI 互換エンドポイントを叩く。"""

    def __init__(self, base_url: str, model: str = "local",
                 timeout: int = 1800, api_key: str | None = None):
        self.base = base_url.rstrip("/")
        if self.base.endswith("/v1"):
            self.base = self.base[:-3]
        self.model = model
        self.timeout = timeout
        self.api_key = api_key or os.environ.get("LLAMA_API_KEY")

    # -- 低レベル ----------------------------------------------------------
    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _get(self, path: str, timeout: int = 10):
        req = urllib.request.Request(self.base + path, headers=self._headers())
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))

    # -- 疎通 --------------------------------------------------------------
    def probe(self) -> dict:
        """起動しているか、何が載っているかを調べる。落ちていても例外にしない。"""
        info: dict = {"base_url": self.base, "reachable": False}
        try:
            info["health"] = self._get("/health")
            info["reachable"] = True
        except Exception as exc:            # noqa: BLE001 — 表示するだけ
            info["health_error"] = str(exc)
        for path, key in (("/props", "props"), ("/v1/models", "models")):
            try:
                info[key] = self._get(path)
                info["reachable"] = True
            except Exception as exc:        # noqa: BLE001
                info[key + "_error"] = str(exc)
        props = info.get("props") or {}
        info["model_path"] = props.get("model_path") or props.get("model") or ""
        info["n_ctx"] = (props.get("default_generation_settings") or {}).get("n_ctx") \
            or props.get("n_ctx")
        return info

    # -- 生成 --------------------------------------------------------------
    def chat(self, system: str, user: str, *, temperature: float = 0.4,
             top_p: float = 0.9, max_tokens: int = 4096, seed: int | None = None,
             stream: bool = True, progress=None) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": bool(stream),
        }
        if seed is not None:
            payload["seed"] = seed
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.base + "/v1/chat/completions",
                                     data=data, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if not stream:
                    body = json.loads(resp.read().decode("utf-8"))
                    return body["choices"][0]["message"]["content"]
                return self._read_stream(resp, progress)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:800]
            raise LlamaServerError(
                f"llama-server が {exc.code} を返した: {detail}") from exc
        except urllib.error.URLError as exc:
            raise LlamaServerError(
                f"llama-server ({self.base}) に繋がらない: {exc.reason}\n"
                f"  llama-server を起動してから、もう一度実行してください。") from exc

    @staticmethod
    def _read_stream(resp, progress) -> str:
        chunks: list[str] = []
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            body = line[5:].strip()
            if body == "[DONE]":
                break
            try:
                obj = json.loads(body)
            except json.JSONDecodeError:
                continue
            for choice in obj.get("choices", []):
                piece = (choice.get("delta") or {}).get("content") or ""
                if piece:
                    chunks.append(piece)
                    if progress:
                        progress(piece)
        return "".join(chunks)


# --------------------------------------------------------------------------
# 4. YAML / JSON の入出力
# --------------------------------------------------------------------------

try:
    import yaml  # type: ignore
    HAVE_YAML = True
except ImportError:                          # pragma: no cover
    yaml = None                              # type: ignore
    HAVE_YAML = False


def load_struct(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if stripped.startswith("{"):
        return json.loads(text)
    if HAVE_YAML:
        return yaml.safe_load(text) or {}
    raise SystemExit(
        f"[!] {path.name} は YAML ですが PyYAML が入っていません。\n"
        f"    どちらかにしてください:\n"
        f"      1) pip install pyyaml\n"
        f"      2) ComfyUI 同梱の python を使う（PyYAML が入っています）:\n"
        f"         ComfyUI_windows_portable\\python_embeded\\python.exe "
        f"tools\\h3_prompt_convert.py ...\n"
        f"      3) --json を付けて中間形式を JSON にする")


def dump_struct(obj: dict, path: Path, as_json: bool = False) -> None:
    if as_json or not HAVE_YAML:
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    else:
        path.write_text(
            yaml.safe_dump(obj, allow_unicode=True, sort_keys=False,
                           default_flow_style=False, width=100),
            encoding="utf-8")


def extract_block(text: str, langs=("yaml", "yml", "json")) -> str:
    """LLM の返答からコードフェンスの中身を取り出す。無ければ全体を返す。"""
    fence = re.compile(r"```(?:" + "|".join(langs) + r")?\s*\n(.*?)```",
                       re.DOTALL | re.IGNORECASE)
    blocks = fence.findall(text)
    if blocks:
        return max(blocks, key=len).strip()
    return text.strip()


def parse_struct_text(text: str) -> dict:
    body = extract_block(text)
    stripped = body.lstrip()
    if stripped.startswith("{"):
        return json.loads(body)
    if HAVE_YAML:
        return yaml.safe_load(body) or {}
    raise SystemExit("[!] モデルが YAML を返しましたが PyYAML がありません。"
                     " --json を付けて実行してください。")


# --------------------------------------------------------------------------
# 5. 中間形式（plan）の正規化 —— ここが「数値は Python が持つ」の実体
# --------------------------------------------------------------------------

RETENTIONS = ("fully_preserved", "partially_preserved",
              "attribute_transfer", "weak_reference")
USED_AS = ("reference", "storyboard", "first_frame", "last_frame",
           "key_frame", "continue_from", "edit")
MODES = ("ref2va", "t2va", "fl2va")

NEGATIONS = re.compile(
    r"\b(no|not|non|never|without|avoid|avoids|avoiding|nothing|none of|"
    r"don't|doesn't|do not|does not|shouldn't|won't|absent|lack of|free of)\b",
    re.IGNORECASE)


def _as_list(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def normalize_plan(plan: dict, *, allow_cliff: bool = False,
                   fit_dialogue: bool = False) -> dict:
    """LLM が返した plan の数値をこちらの計算で上書きする。

    LLM に秒数やフレーム数を計算させると必ずずれる。格子・上限・台詞の位置は
    すべてここで決め直す。
    """
    plan.setdefault("fps", FPS)
    plan.setdefault("mode", "ref2va")
    plan.setdefault("language", "Japanese")
    plan.setdefault("non_diegetic_music", "None")
    fps = int(plan.get("fps") or FPS)

    ceiling = FRAMES_CLIFF if allow_cliff else FRAMES_OPERATIONAL

    for idx, clip in enumerate(_as_list(plan.get("clips")), start=1):
        clip.setdefault("id", f"C{idx:02d}")

        # --- 尺: 秒 → 17k+5 格子 → 上限で頭打ち -------------------------
        # 黙って直さない。直したことは clip["adjusted"] に残して lint で報告する。
        notes: list[str] = []
        want = clip.get("seconds")
        asked = clip.get("frames")
        frames = asked
        if frames and on_grid(int(frames)):
            frames = int(frames)
        elif want:
            frames = frames_for_seconds(float(want), fps)
            if asked:
                notes.append(f"frames {int(asked)} は 17k+5 格子に乗らないので "
                             f"seconds {want} から引き直した")
        elif frames:
            snapped = frames_for_seconds(float(frames) / fps, fps)
            notes.append(f"{int(frames)}f は格子に乗らないので {snapped}f に合わせた")
            frames = snapped
        else:
            frames = FRAMES_OPERATIONAL
        # --- 台詞: モーラ → 秒 ------------------------------------------
        lines = _as_list(clip.get("dialogue"))
        for line in lines:
            text = str(line.get("text", "")).strip()
            yomi = str(line.get("yomi", "") or "").strip()
            mora, exact = count_mora(yomi or text)
            line["mora"] = mora
            line["mora_exact"] = bool(yomi) and exact
            line["est_seconds"] = round(mora / MORA_PER_SEC, 2)
            line.setdefault("speaker", "S1")

        # --- 台詞から尺を決め直す（--fit-dialogue）------------------------
        need = dialogue_span_seconds(lines)
        clip["dialogue_span"] = round(need, 3)
        if fit_dialogue and need > 0:
            fitted = max(frames_for_seconds(need, fps), FRAMES_MIN)
            if fitted != frames:
                notes.append(f"--fit-dialogue: 台詞の実尺 {need:.2f}s から "
                             f"{frames}f → {fitted}f に決め直した")
            frames = fitted

        if frames > ceiling:
            notes.append(
                f"{frames}f ({seconds_for_frames(frames, fps):.3f}s) は上限を超えるので "
                f"{ceiling}f ({seconds_for_frames(ceiling, fps):.3f}s) で頭打ちにした"
                + ("" if allow_cliff else "。--allow-cliff で 736f まで許せる"))
        clip["frames"] = min(frames, ceiling)
        clip["seconds"] = round(seconds_for_frames(clip["frames"], fps), 3)
        if notes:
            clip["adjusted"] = notes

        # --- 台詞の位置は終端寄せ ----------------------------------------
        _place_dialogue(lines, clip["seconds"])

        # --- クリップ内カット割りのタイミングマーカー --------------------
        shots = _as_list(clip.get("shots"))
        for n, shot in enumerate(shots, start=1):
            at = float(shot.get("at", 0.0))
            shot["at"] = round(min(max(at, 0.0), clip["seconds"]), 3)
            shot["marker"] = f"[Shot {n}] at {fmt_timecode(shot['at'])}"
        clip["shots"] = shots
    return plan


DIALOGUE_LEAD_IN = 1.0   # 最初の発話までの間
DIALOGUE_GAP = 0.30      # 発話と発話の間


def dialogue_span_seconds(lines: list, lead_in: float = DIALOGUE_LEAD_IN,
                          gap: float = DIALOGUE_GAP) -> float:
    """台詞から必要なクリップ長を出す。

    台帳の第一則「クリップ長は台詞の長さから決める」の実体。尺が余ると H3 は
    残りを雑音で埋め、キャラがその雑音にリップシンクする（音を消しても口は動く）。
    """
    if not lines:
        return 0.0
    speech = sum(float(l.get("est_seconds") or 0.0) for l in lines)
    return lead_in + speech + gap * (len(lines) - 1) + SPEECH_TAIL_SEC


def _place_dialogue(lines: list, clip_seconds: float, gap: float = 0.30) -> None:
    """`at` が無い台詞を終端寄せで並べる。

    実測: セリフはクリップの終端 0.20〜0.24 秒前に張り付く。伸ばして増えるのは
    発話「前」の無音なので、後ろから詰めるのが実際の挙動に合う。
    """
    if not lines:
        return
    if all(ln.get("at") is not None for ln in lines):
        for ln in lines:
            ln["at"] = round(min(max(float(ln["at"]), 0.0), clip_seconds), 3)
    else:
        cursor = clip_seconds - SPEECH_TAIL_SEC
        for ln in reversed(lines):
            dur = float(ln.get("est_seconds") or 0.0)
            start = cursor - dur
            ln["at"] = round(max(start, 0.0), 3)
            cursor = start - gap
    for ln in lines:
        ln["marker"] = f"at {fmt_timecode(float(ln['at']))}"
        ln["ends_at"] = round(float(ln["at"]) + float(ln.get("est_seconds") or 0.0), 3)


def dialogue_line_text(line: dict, language: str = "Japanese") -> str:
    """H3 の発話書式そのもの。話者と喋り方はタグの外、中は言語と台詞だけ。"""
    speaker = str(line.get("speaker", "S1")).strip()
    delivery = str(line.get("delivery", "") or "").strip().rstrip(".")
    text = str(line.get("text", "")).strip()
    head = f"({speaker})"
    if delivery:
        head += f" {delivery}"
    return f"{head}: <d>[{language}]{text}</d>"


# --------------------------------------------------------------------------
# 6. lint —— 機械で検査できることは全部ここで見る
# --------------------------------------------------------------------------

class Finding:
    __slots__ = ("level", "where", "message")

    def __init__(self, level: str, where: str, message: str):
        self.level, self.where, self.message = level, where, message

    def __str__(self) -> str:
        mark = {"error": "[!]", "warn": "[~]", "info": "[i]"}[self.level]
        return f"{mark} {self.where}: {self.message}"


def lint_plan(plan: dict, *, allow_cliff: bool = False) -> list[Finding]:
    out: list[Finding] = []
    add = lambda lv, wh, ms: out.append(Finding(lv, wh, ms))  # noqa: E731

    mode = str(plan.get("mode", "")).lower()
    if mode not in MODES:
        add("error", "mode", f"{mode!r} は不正。{MODES} のどれかにする")
    if mode == "i2v":
        add("error", "mode", "hybrid/beta4 は i2v で使わない。ref2va か t2va")

    # --- 参照 ---------------------------------------------------------
    refs = plan.get("references") or {}
    images = _as_list(refs.get("images"))
    if len(images) > 7:
        add("error", "references.images",
            f"{len(images)} 枚。参照 9 枠は Location と継続アンカーに食われて"
            f"実質 7 枠で、超えた分は黙って落ちる")
    elif len(images) > 3:
        add("warn", "references.images",
            f"{len(images)} 枚。枚数を増やすほど品質が落ちる。1 枚のシートに集約できないか")
    for im in images:
        if str(im.get("retention", "")) not in RETENTIONS:
            add("warn", f"image {im.get('id')}",
                f"retention が未指定/不正。{RETENTIONS} から選ぶ")
        if str(im.get("used_as", "reference")) not in USED_AS:
            add("warn", f"image {im.get('id')}", "used_as が不正")
        if str(im.get("used_as", "")) == "key_frame":
            add("info", f"image {im.get('id')}",
                "key_frame は精度が保証されない（公式）")

    audio = _as_list(refs.get("audio"))
    if len(audio) > 3:
        add("error", "references.audio", f"{len(audio)} 本。公式上限は 3 本")
    total = 0.0
    for a in audio:
        sec = float(a.get("seconds") or 0)
        total += sec
        if sec and not (2.0 <= sec <= 15.0):
            add("error", f"audio {a.get('id')}", f"{sec} 秒。各 2〜15 秒でなければならない")
        elif sec and not (5.0 <= sec <= 10.0):
            add("info", f"audio {a.get('id')}", f"{sec} 秒。実用的な長さは 5〜10 秒")
    if total > 15.0:
        add("error", "references.audio", f"合計 {total:.1f} 秒。上限は 15 秒")

    # --- BGM / サウンドスケープ ---------------------------------------
    ndm = str(plan.get("non_diegetic_music", "")).strip()
    if not ndm:
        add("error", "non_diegetic_music",
            "空。BGM 不要なら 'None' と明記する（未指定だと継ぎ目で音楽が合わない）")
    elif ndm.lower() not in ("none", "n/a") and _sentences(ndm) > 2:
        add("warn", "non_diegetic_music", f"{_sentences(ndm)} 文。1〜2 文に収める")

    # --- エンティティ --------------------------------------------------
    ent_ids = {str(e.get("id")) for e in _as_list(plan.get("entities"))}
    voiced = {str(e.get("id")) for e in _as_list(plan.get("entities"))
              if str(e.get("voice", "") or "").strip()}
    img_ids = {str(i.get("id")) for i in images}
    for e in _as_list(plan.get("entities")):
        src = str(e.get("from", "") or "")
        if src and src not in img_ids:
            add("warn", f"entity {e.get('id')}", f"from: {src} が references.images に無い")
        if str(e.get("retention", "")) == "attribute_transfer":
            desc = str(e.get("description", ""))
            if "faceless" not in desc.lower() and "no face" not in desc.lower():
                add("warn", f"entity {e.get('id')}",
                    "顔の移植では受け手を faceless と記述する。書かないとモデルが勝手に顔を描く")

    # --- クリップ ------------------------------------------------------
    clips = _as_list(plan.get("clips"))
    if not clips:
        add("error", "clips", "1 本も無い")
    ceiling = FRAMES_CLIFF if allow_cliff else FRAMES_OPERATIONAL
    for clip in clips:
        cid = clip.get("id", "?")
        f = int(clip.get("frames") or 0)
        sec = seconds_for_frames(f)
        for note in _as_list(clip.get("adjusted")):
            add("warn", cid, f"変換器が尺を直した — {note}")
        if not on_grid(f):
            lo, hi = grid_neighbours(f)
            add("error", cid, f"{f}f は 17k+5 格子に乗らない。{lo}f か {hi}f にする")
        if f < FRAMES_MIN:
            add("error", cid, f"{f}f ({sec:.2f}s) は公式下限 4 秒を割る。{FRAMES_MIN}f 以上に")
        if f > FRAMES_CLIFF:
            add("error", cid, f"{f}f ({sec:.2f}s) は未計測領域。{FRAMES_CLIFF}f を超えている")
        elif f > FRAMES_OPERATIONAL:
            add("warn", cid,
                f"{f}f ({sec:.2f}s) は運用上限 {FRAMES_OPERATIONAL}f (25.000s) 超。"
                f"30 秒は完走するが VRAM 余裕が 694 MiB しかない")
        elif f > FRAMES_SPEC_MAX:
            add("info", cid,
                f"{f}f ({sec:.2f}s) は公式仕様 4〜15 秒の外だが、実測で破綻無しを確認済み")

        # 台詞と尺の噛み合わせ
        lines = _as_list(clip.get("dialogue"))
        speech = sum(float(l.get("est_seconds") or 0) for l in lines)
        for l in lines:
            if not str(l.get("yomi", "") or "").strip():
                add("warn", f"{cid}/{l.get('speaker')}",
                    "yomi が無い。モーラ数が概算になり、TTS 差し替えにも使えない")
            m = int(l.get("mora") or 0)
            if m and not (MORA_LINE_MIN <= m <= MORA_LINE_MAX):
                lvl = "warn" if m > MORA_LINE_MAX else "info"
                add(lvl, f"{cid}/{l.get('speaker')}",
                    f"{m} モーラ ({l.get('est_seconds')}s)。1 発話の目安は "
                    f"{MORA_LINE_MIN}〜{MORA_LINE_MAX} モーラ")
            ent = str(l.get("entity", "") or "")
            if ent and ent not in ent_ids:
                add("warn", f"{cid}/{l.get('speaker')}", f"entity {ent} が定義されていない")
            elif ent and ent not in voiced:
                add("error", f"{cid}/{l.get('speaker')}",
                    f"entity {ent} に voice の記述が無い。声を記述して初めて話者になる")
            if float(l.get("ends_at") or 0) > sec:
                add("error", f"{cid}/{l.get('speaker')}",
                    f"台詞が {l.get('ends_at')}s に終わり、クリップ長 {sec:.2f}s を超える")
        # 台帳の第一則: クリップ長は台詞の実尺から決める。
        # 判定は「台詞から出した必要尺をどれだけ超えているか」で見る（割合ではなく差）。
        if lines:
            need = float(clip.get("dialogue_span") or dialogue_span_seconds(lines))
            excess = sec - need
            if excess > DEAD_AIR_TOLERANCE:
                silence = _positive_silence(clip, plan)
                fit_f = max(frames_for_seconds(need), FRAMES_MIN)
                if silence:
                    remedy = "（無音を肯定形で書いてあるので可）"
                elif fit_f >= f:
                    remedy = (f"。すでに下限 {FRAMES_MIN}f (4 秒) なのでこれ以上は詰められない。"
                              f"無音を肯定形で描写する"
                              f"（「lips closed, silently waiting」など）")
                else:
                    remedy = (f"。台詞から決めるなら {fit_f}f "
                              f"({seconds_for_frames(fit_f):.3f}s) — `--fit-dialogue` で自動。"
                              f"伸ばすなら無音を肯定形で描写する")
                add("info" if silence else "warn", cid,
                    f"台詞 {speech:.1f}s（間を含めて {need:.1f}s 必要）に対しクリップ "
                    f"{sec:.2f}s。余りが {excess:.1f}s ある。余った時間は雑音で埋まり、"
                    f"キャラがその雑音にリップシンクする" + remedy)
        if not lines and not _positive_silence(clip, plan):
            add("warn", cid,
                "台詞が無いのに無音の描写も無い。H3 は音を出したがる。"
                "「lips closed, silently deep in thought」のように肯定形で書く")

        # ショットのタイミングマーカー
        prev = -1.0
        for shot in _as_list(clip.get("shots")):
            at = float(shot.get("at", 0))
            if at <= prev:
                add("error", cid, f"タイミングマーカーが増加していない: {shot.get('marker')}")
            if at >= sec:
                add("error", cid, f"{shot.get('marker')} がクリップ長 {sec:.2f}s の外")
            prev = at

    # --- 連鎖するクリップの揃え ----------------------------------------
    mps = {clip.get("megapixels", plan.get("megapixels")) for clip in clips}
    if len(mps) > 1:
        add("error", "clips", f"解像度が揃っていない: {mps}。連鎖する全クリップで揃える")

    # --- 否定形 --------------------------------------------------------
    for field, text in _english_fields(plan):
        hits = sorted({m.group(0).lower() for m in NEGATIONS.finditer(text)})
        if hits:
            add("warn", field,
                f"否定形 {hits} が入っている。H3 は否定を扱えない。肯定形で状態を描写する")
    return out


def _sentences(text: str) -> int:
    return len([s for s in re.split(r"[.!?。]+", text) if s.strip()])


# 「無音を肯定形で描写してあるか」の判定。
# 部屋が quiet なのと、人物が黙っているのは別の話なので、口・唇に係る表現だけを見る。
_SILENCE_PATTERNS = (
    r"\b(lips|mouth|jaw)\b[^.]{0,60}\b(closed|shut|still|unmoving|sealed|together)\b",
    r"\b(closed|shut|still|unmoving)\b[^.]{0,40}\b(lips|mouth|jaw)\b",
    r"\bsilently\b[^.]{0,60}"
    r"\b(thought|thinking|watch\w*|stand\w*|sit\w*|breath\w*|listen\w*|wait\w*)\b",
    r"\bin silence\b",
    r"\bwordless(ly)?\b",
)


def _positive_silence(clip: dict, plan: dict) -> bool:
    blob = " ".join(str(x) for x in (
        clip.get("description", ""), clip.get("camera", ""),
        clip.get("soundscape", ""), plan.get("soundscape", ""),
        " ".join(map(str, _as_list(clip.get("constraints")))),
        " ".join(map(str, _as_list(plan.get("constraints")))))).lower()
    return any(re.search(pat, blob) for pat in _SILENCE_PATTERNS)


def _english_fields(plan: dict):
    yield from (("summary", str(plan.get("summary", ""))),
                ("soundscape", str(plan.get("soundscape", ""))),
                ("non_diegetic_music", str(plan.get("non_diegetic_music", ""))))
    for c in _as_list(plan.get("constraints")):
        yield "constraints", str(c)
    for e in _as_list(plan.get("entities")):
        yield f"entity {e.get('id')}", str(e.get("description", ""))
    for clip in _as_list(plan.get("clips")):
        cid = clip.get("id", "?")
        yield f"{cid}.description", str(clip.get("description", ""))
        yield f"{cid}.camera", str(clip.get("camera", ""))
        yield f"{cid}.soundscape", str(clip.get("soundscape", ""))
        for c in _as_list(clip.get("constraints")):
            yield f"{cid}.constraints", str(c)


# --------------------------------------------------------------------------
# 7. LLM への指示（system prompt）
# --------------------------------------------------------------------------

PLAN_SCHEMA = """\
title: 作品名
mode: ref2va            # ref2va | t2va | fl2va（i2v は使わない）
megapixels: 0.4
language: Japanese
summary: >-             # 層2。英語。動画の種類・総尺・読み順・アクションの連鎖
  ...
soundscape: >-          # 全クリップ共通の環境音。英語。1〜4 文
  ...
non_diegetic_music: None   # BGM。不要なら None。要るなら楽器とテンポを 1〜2 文
constraints:            # 層5。英語。すべて肯定形で書く
  - ...
references:
  images:
    - id: image1
      role: character sheet — face, hair and wardrobe
      used_as: reference          # reference|storyboard|first_frame|last_frame|key_frame
      retention: fully_preserved  # fully_preserved|partially_preserved|attribute_transfer|weak_reference
  audio:
    - id: audio1
      role: voice reference for subject1
      seconds: 8
entities:               # 層1。人物・服・場所・小道具・画風を別オブジェクトとして
  - id: subject1
    name: Aoi
    kind: person        # person|wardrobe|location|prop|style
    from: image1
    retention: fully_preserved
    description: ...    # 英語
    voice: a low, steady female voice, unhurried   # 空だと無言になり台詞を持てない
    voice_from: audio1
clips:
  - id: C01
    seconds: 25.0       # 希望値。17k+5 格子への丸めは変換器がやる
    camera: ...         # 英語
    description: ...    # 層4。英語。起きる順に、動作と状態だけを書く
    shots:              # クリップ内のカット割り。要らなければ省略
      - at: 12.0
        note: cut to a tight close shot of her hands
    dialogue:
      - speaker: S1
        entity: subject1
        text: なにこれ。            # 日本語のまま
        yomi: なにこれ              # かな読み。必須
        delivery: in a low, flat voice   # 英語。タグの外に出る
"""

PLAN_SYSTEM = """\
あなたは MiniMax H3（動画+音声生成モデル）のプロンプト設計者です。
日本語で書かれた場面メモを読み、下のスキーマどおりの YAML を 1 つだけ出力します。

{rules}

## 出力の決まり

- **YAML だけを ```yaml フェンスで囲んで出力する。** 前後に説明を書かない。
- **プロンプトに載る記述はすべて英語で書く。** 例外は台詞の `text` と `yomi` だけ。
- **台詞には必ず `yomi`（かな読み）を付ける。** 日本語 TTS への差し替えに使う。
- **否定形を使わない。** 「音を出さない」ではなく「唇を閉じて黙考している」と書く。
- **秒数・フレーム数を自分で計算しない。** `seconds` に希望値を書くだけでよい。
  17k+5 格子への丸めと上限の適用は変換器がやる。
- 台詞を持つ人物には必ず `voice` を書く。書かないとその人物は無言になる。
- 場面メモに書かれていないことを勝手に足さない。足すなら撮影上の当たり前
  （光・レンズ・グレーディング）に留める。

## スキーマ

```yaml
{schema}
```
"""

RENDER_SYSTEM = """\
あなたは MiniMax H3 のプロンプト清書係です。渡された設計データを、H3 の公式
フィールドに落とした散文にします。

{rules}

## 出力の決まり

- **JSON だけを ```json フェンスで囲んで出力する。** 前後に説明を書かない。
- 形は `{{"clips": {{"C01": {{"integrated_multimodal_description": "...",
  "overall_soundscape": "...", "non_diegetic_music": "..."}}}}}}`。
- **本文は英語。台詞だけ日本語**（`<d>[Japanese]…</d>` の中）。
- **渡された `dialogue_lines` と `shot_markers` の文字列は、1 文字も変えずに
  そのまま本文へ埋め込む。** 話者 ID・タグ・タイムコードを書き換えない。
- `integrated_multimodal_description` は、被写体 → 環境 → カメラ → 起きる順の
  アクション → 台詞（マーカー付き）→ その瞬間の音、の順で書く。段落 1 つ。
- `overall_soundscape` は 1〜4 文の連続した段落。
- `non_diegetic_music` は 1〜2 文。BGM 不要なら `None` の 1 語だけ。
- **否定形を使わない。** 状態は肯定形で描写する。
- 形容詞を盛らない。動作と状態を、起きる順に書く。
"""


def build_reference_roles(plan: dict) -> str:
    """プロンプト冒頭の「各参照に役割を割り当てる行」を機械的に作る。"""
    refs = plan.get("references") or {}
    ent_by_src: dict[str, list] = {}
    for e in _as_list(plan.get("entities")):
        ent_by_src.setdefault(str(e.get("from", "") or ""), []).append(e)

    parts: list[str] = []
    for im in _as_list(refs.get("images")):
        rid = str(im.get("id", "image"))
        tag = f"<{_spaced(rid)}>"
        owners = ent_by_src.get(rid, [])
        who = ", ".join(str(e.get("name") or e.get("id")) for e in owners)
        keep = str(im.get("retention", "fully_preserved")).replace("_", " ")
        used = str(im.get("used_as", "reference")).replace("_", " ")
        role = str(im.get("role", "")).strip().rstrip(".")
        bit = f"{tag} is used as {used}"
        if role:
            bit += f" — {role}"
        if who:
            bit += f", defining {who}"
        bit += f" ({keep})."
        parts.append(bit)
    for a in _as_list(refs.get("audio")):
        tag = f"<{_spaced(str(a.get('id', 'audio')))}>"
        role = str(a.get("role", "voice reference")).strip().rstrip(".")
        parts.append(f"{tag} is the {role} — it sets timbre and delivery only.")
    return " ".join(parts)


def _spaced(ident: str) -> str:
    """image1 → image 1（公式プロンプトは三角括弧に番号付きで書く）"""
    m = re.match(r"^([a-zA-Z]+)(\d+)$", ident)
    return f"{m.group(1)} {m.group(2)}" if m else ident


def clip_brief(plan: dict, clip: dict) -> dict:
    """LLM に渡す 1 クリップぶんの材料。数値はすべて確定済み。"""
    lang = str(plan.get("language", "Japanese"))
    return {
        "id": clip.get("id"),
        "frames": clip.get("frames"),
        "seconds": clip.get("seconds"),
        "fps": plan.get("fps", FPS),
        "mode": plan.get("mode"),
        "camera": clip.get("camera", ""),
        "action": clip.get("description", ""),
        "entities": [
            {k: e.get(k) for k in ("id", "name", "kind", "from", "retention",
                                   "description", "voice") if e.get(k)}
            for e in _as_list(plan.get("entities"))],
        "reference_roles": build_reference_roles(plan),
        "shot_markers": [s.get("marker") for s in _as_list(clip.get("shots"))],
        "shot_notes": [{"marker": s.get("marker"), "note": s.get("note", "")}
                       for s in _as_list(clip.get("shots"))],
        "dialogue_lines": [
            {"marker": ln.get("marker"),
             "line": dialogue_line_text(ln, lang),
             "seconds": ln.get("est_seconds")}
            for ln in _as_list(clip.get("dialogue"))],
        "soundscape_hint": clip.get("soundscape") or plan.get("soundscape", ""),
        "non_diegetic_music": clip.get("non_diegetic_music",
                                       plan.get("non_diegetic_music", "None")),
        "constraints": _as_list(clip.get("constraints")) + _as_list(plan.get("constraints")),
        "summary": plan.get("summary", ""),
    }


# --------------------------------------------------------------------------
# 8. レンダリング結果の検査
# --------------------------------------------------------------------------

def lint_rendered(plan: dict, rendered: dict) -> list[Finding]:
    out: list[Finding] = []
    lang = str(plan.get("language", "Japanese"))
    clips = {str(c.get("id")): c for c in _as_list(plan.get("clips"))}

    for cid, clip in clips.items():
        got = (rendered.get("clips") or {}).get(cid)
        if not got:
            out.append(Finding("error", cid, "レンダリング結果に含まれていない"))
            continue
        body = str(got.get("integrated_multimodal_description", ""))
        if not body.strip():
            out.append(Finding("error", cid, "integrated_multimodal_description が空"))

        for ln in _as_list(clip.get("dialogue")):
            want = dialogue_line_text(ln, lang)
            if want not in body:
                out.append(Finding("error", cid,
                                   f"台詞がそのまま入っていない: {want}"))
            if str(ln.get("marker", "")) not in body:
                out.append(Finding("warn", cid,
                                   f"台詞のタイミングマーカーが無い: {ln.get('marker')}"))
        for shot in _as_list(clip.get("shots")):
            if str(shot.get("marker", "")) not in body:
                out.append(Finding("warn", cid,
                                   f"ショットのマーカーが無い: {shot.get('marker')}"))

        # 台詞タグの整合
        for tag_open, tag_close in ((body.count("<d>"), body.count("</d>")),):
            if tag_open != tag_close:
                out.append(Finding("error", cid,
                                   f"<d> {tag_open} 個に対し </d> {tag_close} 個"))
        for m in re.finditer(r"<d>(?!\[)", body):
            out.append(Finding("error", cid,
                               "<d> の直後に [言語] が無い。<d>[Japanese]… の形にする"))
            break
        stray = re.search(r"<d>\[[^\]]+\][^<]*\((S\d)\)", body)
        if stray:
            out.append(Finding("error", cid,
                               f"話者 ID {stray.group(1)} がタグの中にある。外に出す"))

        sc = str(got.get("overall_soundscape", ""))
        n = _sentences(sc)
        if not sc.strip():
            out.append(Finding("error", cid, "overall_soundscape が空"))
        elif n > 4:
            out.append(Finding("warn", cid, f"overall_soundscape が {n} 文。1〜4 文に収める"))

        ndm = str(got.get("non_diegetic_music", "")).strip()
        if not ndm:
            out.append(Finding("error", cid,
                               "non_diegetic_music が空。不要なら None と書く"))
        elif ndm.lower() not in ("none", "n/a") and _sentences(ndm) > 2:
            out.append(Finding("warn", cid,
                               f"non_diegetic_music が {_sentences(ndm)} 文。1〜2 文に"))

        for field in ("integrated_multimodal_description", "overall_soundscape",
                      "non_diegetic_music"):
            text = str(got.get(field, ""))
            # 台詞（日本語）は否定形検査から外す
            english = re.sub(r"<d>\[[^\]]*\][^<]*</d>", " ", text)
            hits = sorted({m.group(0).lower() for m in NEGATIONS.finditer(english)})
            if hits:
                out.append(Finding("warn", f"{cid}.{field}",
                                   f"否定形 {hits}。H3 は否定を扱えない。肯定形にする"))
    return out


# --------------------------------------------------------------------------
# 9. 出力（貼れる形の Markdown）
# --------------------------------------------------------------------------

def render_markdown(plan: dict, rendered: dict, findings: list[Finding]) -> str:
    lang = str(plan.get("language", "Japanese"))
    fps = plan.get("fps", FPS)
    clips = _as_list(plan.get("clips"))
    total_f = sum(int(c.get("frames") or 0) for c in clips)

    L: list[str] = []
    add = L.append
    add(f"# {plan.get('title', 'MiniMax H3 プロンプト')}")
    add("")
    add(f"`tools/h3_prompt_convert.py` が生成。**数値は変換器が計算したもの**"
        f"（17k+5 格子 / 25 秒上限 / モーラ予算）。")
    add("")
    add("| 項目 | 値 |")
    add("|---|---|")
    add(f"| モード | `{plan.get('mode')}` |")
    add(f"| クリップ数 | {len(clips)} 本（継ぎ目 {max(len(clips) - 1, 0)}）|")
    add(f"| 合計 | {total_f} フレーム / **{seconds_for_frames(total_f, fps):.3f} 秒** |")
    add(f"| 解像度 | {plan.get('megapixels', 0.4)} MP |")
    add(f"| サンプラ | `euler` / `simple` / **6 step** / turbo LoRA バイパス |")
    add(f"| `prompt_optimizer` | **false** |")
    add("")
    add("> beta4 (`10Eros_Max_h3_TURBO-hybrid_beta4_int8_convrot`) の設定です。"
        "base に戻すなら turbo LoRA 有効 / `res_multistep` / 8 step。**混ぜると二重掛け**。")
    add("")

    roles = build_reference_roles(plan)
    if roles:
        add("## 参照の割り当て")
        add("")
        add("プロンプト冒頭に置く行（各クリップの本文にも含まれています）。")
        add("")
        add("```text")
        add(roles)
        add("```")
        add("")

    for clip in clips:
        cid = str(clip.get("id"))
        got = (rendered.get("clips") or {}).get(cid, {})
        f = int(clip.get("frames") or 0)
        sec = seconds_for_frames(f, fps)
        k = (f - GRID_REM) // GRID_STEP
        add(f"## {cid} — {f} フレーム / {sec:.3f} 秒")
        add("")
        add(f"`length = 17×{k}+5 = {f}` / {fps}fps。"
            + ("**運用上限の 25.000 秒**。" if f == FRAMES_OPERATIONAL else "")
            + ("公式仕様 4〜15 秒の外ですが実測で破綻無しを確認済み。"
               if FRAMES_SPEC_MAX < f <= FRAMES_OPERATIONAL else ""))
        add("")
        for field in ("integrated_multimodal_description", "overall_soundscape",
                      "non_diegetic_music"):
            add(f"**`{field}`**")
            add("")
            add("```text")
            add(str(got.get(field, "")).strip() or "(空)")
            add("```")
            add("")

        lines = _as_list(clip.get("dialogue"))
        if lines:
            add("### 台詞 — 日本語 TTS 差し替え用")
            add("")
            add("| 位置 | 話者 | 台詞 | かな読み | モーラ | 推定尺 |")
            add("|---|---|---|---|---|---|")
            for ln in lines:
                exact = "" if ln.get("mora_exact") else "≈"
                add(f"| {fmt_timecode(float(ln.get('at', 0)))} | {ln.get('speaker')} "
                    f"| {ln.get('text')} | {ln.get('yomi', '')} "
                    f"| {exact}{ln.get('mora')} | {ln.get('est_seconds')}s |")
            speech = sum(float(l.get("est_seconds") or 0) for l in lines)
            add("")
            add(f"台詞の合計 **{speech:.2f} 秒** / クリップ {sec:.3f} 秒。"
                f"最後の発話は {fmt_timecode(float(lines[-1].get('ends_at', 0)))} に終わり、"
                f"終端まで {sec - float(lines[-1].get('ends_at', 0)):.2f} 秒。")
            add("")
            add("> **出力音声は常に合成されます**（公式）。渡した波形はそのまま出てきません。"
                "日本語のアクセントを確実にするなら、上のかな読みで TTS"
                "（Style-BERT-VITS2 / AivisSpeech / VOICEVOX）を作り、"
                "**最終出力の音声トラックを差し替えて**ください。")
            add("")

    add("## 検査結果")
    add("")
    if not findings:
        add("問題なし。")
    else:
        for lv, label in (("error", "要修正"), ("warn", "注意"), ("info", "参考")):
            items = [f for f in findings if f.level == lv]
            if items:
                add(f"### {label}（{len(items)}）")
                add("")
                for f in items:
                    add(f"- **{f.where}** — {f.message}")
                add("")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------
# 10. キャッシュ（177B はどのみち遅いので、同じ入力は 2 度投げない）
# --------------------------------------------------------------------------

class Cache:
    def __init__(self, root: Path | None):
        self.root = root
        if root:
            root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(*parts: str) -> str:
        h = hashlib.sha256()
        for p in parts:
            h.update(p.encode("utf-8"))
            h.update(b"\x00")
        return h.hexdigest()[:32]

    def get(self, key: str) -> str | None:
        if not self.root:
            return None
        p = self.root / f"{key}.txt"
        return p.read_text(encoding="utf-8") if p.exists() else None

    def put(self, key: str, value: str) -> None:
        if self.root:
            (self.root / f"{key}.txt").write_text(value, encoding="utf-8")


# --------------------------------------------------------------------------
# 11. 実行
# --------------------------------------------------------------------------

def _progress(piece: str) -> None:
    sys.stderr.write(piece)
    sys.stderr.flush()


def _ask(srv: LlamaServer, system: str, user: str, args, cache: Cache,
         label: str) -> str:
    ck = Cache.key(system, user, srv.model, str(args.temp), str(args.top_p),
                   str(args.seed))
    hit = cache.get(ck)
    if hit is not None:
        print(f"[i] {label}: キャッシュを使いました", file=sys.stderr)
        return hit
    print(f"[i] {label}: llama-server に送信中 …", file=sys.stderr)
    t0 = time.time()
    out = srv.chat(system, user, temperature=args.temp, top_p=args.top_p,
                   max_tokens=args.max_tokens, seed=args.seed,
                   stream=not args.no_stream,
                   progress=_progress if (args.verbose and not args.no_stream) else None)
    if args.verbose and not args.no_stream:
        sys.stderr.write("\n")
    print(f"[i] {label}: {time.time() - t0:.1f} 秒", file=sys.stderr)
    cache.put(ck, out)
    return out


def do_plan(args, srv: LlamaServer, cache: Cache) -> dict:
    rules = Path(args.rules).read_text(encoding="utf-8")
    memo = Path(args.input).read_text(encoding="utf-8")
    system = PLAN_SYSTEM.format(rules=rules, schema=PLAN_SCHEMA)
    user = (f"## 場面メモ\n\n{memo}\n\n"
            f"## 変換器からの指定\n\n"
            f"- 1 クリップの既定の尺: **{args.seconds} 秒**"
            f"（{frames_for_seconds(args.seconds)} フレームに丸まります）\n"
            f"- 運用上の尺の上限: **25.000 秒 = 600 フレーム**\n"
            f"- 解像度: {args.megapixels} MP / モード: {args.mode}\n\n"
            f"この場面メモを、スキーマどおりの YAML にしてください。")
    raw = _ask(srv, system, user, args, cache, "段1 plan")
    plan = parse_struct_text(raw)
    plan.setdefault("mode", args.mode)
    plan.setdefault("megapixels", args.megapixels)
    return normalize_plan(plan, allow_cliff=args.allow_cliff,
                          fit_dialogue=args.fit_dialogue)


def do_render(args, srv: LlamaServer, cache: Cache, plan: dict) -> dict:
    rules = Path(args.rules).read_text(encoding="utf-8")
    system = RENDER_SYSTEM.format(rules=rules)
    briefs = [clip_brief(plan, c) for c in _as_list(plan.get("clips"))]
    user = ("## 設計データ（数値は確定済み。変えないこと）\n\n```json\n"
            + json.dumps(briefs, ensure_ascii=False, indent=2)
            + "\n```\n\nこの各クリップを H3 の 3 フィールドに清書してください。")

    raw = _ask(srv, system, user, args, cache, "段2 render")
    rendered = parse_struct_text(raw)
    findings = lint_rendered(plan, rendered)

    for attempt in range(1, args.repair + 1):
        errors = [f for f in findings if f.level == "error"]
        if not errors:
            break
        print(f"[i] 修正 {attempt}/{args.repair}: 要修正 {len(errors)} 件を差し戻します",
              file=sys.stderr)
        fix = (user + "\n\n## 前回の出力\n\n```json\n"
               + json.dumps(rendered, ensure_ascii=False, indent=2)
               + "\n```\n\n## 検査で見つかった要修正点\n\n"
               + "\n".join(f"- {f.where}: {f.message}" for f in errors)
               + "\n\nこれらだけを直した JSON を、同じ形で出し直してください。")
        raw = _ask(srv, system, fix, args, cache, f"段2 修正{attempt}")
        rendered = parse_struct_text(raw)
        findings = lint_rendered(plan, rendered)
    return rendered


def print_findings(findings: list[Finding]) -> int:
    for f in findings:
        print(str(f))
    n_err = sum(1 for f in findings if f.level == "error")
    n_warn = sum(1 for f in findings if f.level == "warn")
    print(f"\n要修正 {n_err} / 注意 {n_warn} / 参考 "
          f"{sum(1 for f in findings if f.level == 'info')}")
    return n_err


def cmd_check(args, srv: LlamaServer) -> int:
    info = srv.probe()
    print(f"接続先        : {info['base_url']}")
    if not info["reachable"]:
        print("状態          : **繋がりません**")
        print(f"  {info.get('health_error') or info.get('props_error')}")
        print("\nllama-server を起動してください。例:")
        print("  llama-server -m <177B の gguf> -c 16384 -ngl 99 "
              "--host 127.0.0.1 --port 8080 --jinja")
        return 1
    print("状態          : 応答あり")
    if info.get("model_path"):
        print(f"モデル        : {info['model_path']}")
    for m in (info.get("models") or {}).get("data", []) or []:
        print(f"  /v1/models  : {m.get('id')}")
    if info.get("n_ctx"):
        print(f"コンテキスト  : {info['n_ctx']} トークン")
        if int(info["n_ctx"]) < 8192:
            print("  [~] 8192 未満です。ルールと設計データが入りきらない可能性があります")
    print("\n[i] ComfyUI と 177B は**同時に載りません**"
          "（H3 は TE 15.7GB + DiT 21GB）。プロンプトを先にまとめて作り、"
          "llama-server を落としてから ComfyUI を起動してください。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="h3_prompt_convert.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="日本語の場面メモ → MiniMax H3 プロンプト（ローカル llama-server 経由）",
        epilog=__doc__.split("使い方:")[-1])
    p.add_argument("command",
                   choices=("check", "plan", "render", "auto", "lint"),
                   help="check=疎通確認 / plan=メモ→YAML / render=YAML→プロンプト "
                        "/ auto=両方 / lint=検査だけ")
    p.add_argument("input", nargs="?", help="入力ファイル")
    p.add_argument("-o", "--out", help="出力先（auto ではディレクトリ）")

    g = p.add_argument_group("llama-server")
    g.add_argument("--url", default=os.environ.get("H3_LLAMA_URL",
                                                   "http://127.0.0.1:8080"),
                   help="既定 http://127.0.0.1:8080（環境変数 H3_LLAMA_URL でも指定可）")
    g.add_argument("--model", default="local", help="モデル名（llama-server では任意）")
    g.add_argument("--temp", type=float, default=0.4)
    g.add_argument("--top-p", type=float, default=0.9)
    g.add_argument("--max-tokens", type=int, default=8192)
    g.add_argument("--seed", type=int, default=None)
    g.add_argument("--timeout", type=int, default=1800,
                   help="秒。177B は CPU オフロードで遅いので既定 30 分")
    g.add_argument("--no-stream", action="store_true")

    d = p.add_argument_group("変換")
    d.add_argument("--rules", default=str(RULES_DEFAULT), help="知識パック")
    d.add_argument("--seconds", type=float, default=25.0,
                   help="1 クリップの既定の尺。既定 25.0（運用上限）")
    d.add_argument("--megapixels", type=float, default=0.4)
    d.add_argument("--mode", default="ref2va", choices=MODES)
    d.add_argument("--allow-cliff", action="store_true",
                   help="25 秒を超えて 30.667 秒(736f)まで許す。VRAM 余裕 694 MiB")
    d.add_argument("--fit-dialogue", action="store_true",
                   help="クリップ長を台詞の実尺から決める（台帳の第一則）。"
                        "尺が余ると H3 は雑音で埋め、キャラがそれにリップシンクする")
    d.add_argument("--repair", type=int, default=2,
                   help="検査で要修正が出たとき差し戻す回数。既定 2")
    d.add_argument("--json", action="store_true", help="中間形式を JSON にする")
    d.add_argument("--cache-dir", default=".h3_cache", help="空文字でキャッシュ無効")
    d.add_argument("--no-cache", action="store_true")
    d.add_argument("-v", "--verbose", action="store_true", help="生成中の文字を流す")
    return p


def main(argv: list[str] | None = None) -> int:
    # フラグを位置引数の間に書けるようにする（lint --fit-dialogue scene.yaml）
    args = build_parser().parse_intermixed_args(argv)
    srv = LlamaServer(args.url, model=args.model, timeout=args.timeout)
    cache = Cache(None if (args.no_cache or not args.cache_dir)
                  else Path(args.cache_dir))

    if args.command == "check":
        return cmd_check(args, srv)

    if not args.input:
        print("[!] 入力ファイルを指定してください", file=sys.stderr)
        return 2
    src = Path(args.input)
    if not src.exists():
        print(f"[!] {src} がありません", file=sys.stderr)
        return 2

    ext = ".json" if args.json else ".yaml"

    if args.command == "lint":
        plan = normalize_plan(load_struct(src), allow_cliff=args.allow_cliff,
                          fit_dialogue=args.fit_dialogue)
        return 1 if print_findings(lint_plan(plan, allow_cliff=args.allow_cliff)) else 0

    if args.command == "plan":
        plan = do_plan(args, srv, cache)
        out = Path(args.out) if args.out else src.with_suffix(ext)
        dump_struct(plan, out, args.json)
        print(f"[✓] {out}")
        print_findings(lint_plan(plan, allow_cliff=args.allow_cliff))
        print("\n中身を確認・修正してから render にかけてください。")
        return 0

    if args.command == "render":
        plan = normalize_plan(load_struct(src), allow_cliff=args.allow_cliff,
                          fit_dialogue=args.fit_dialogue)
        rendered = do_render(args, srv, cache, plan)
        findings = lint_plan(plan, allow_cliff=args.allow_cliff) \
            + lint_rendered(plan, rendered)
        out = Path(args.out) if args.out else src.with_suffix(".prompt.md")
        out.write_text(render_markdown(plan, rendered, findings), encoding="utf-8")
        print(f"[✓] {out}")
        return 1 if print_findings(findings) else 0

    # auto
    outdir = Path(args.out) if args.out else src.parent / (src.stem + "_h3")
    outdir.mkdir(parents=True, exist_ok=True)
    plan = do_plan(args, srv, cache)
    plan_path = outdir / f"{src.stem}{ext}"
    dump_struct(plan, plan_path, args.json)
    print(f"[✓] {plan_path}")
    rendered = do_render(args, srv, cache, plan)
    findings = lint_plan(plan, allow_cliff=args.allow_cliff) \
        + lint_rendered(plan, rendered)
    md = outdir / f"{src.stem}.prompt.md"
    md.write_text(render_markdown(plan, rendered, findings), encoding="utf-8")
    print(f"[✓] {md}")
    return 1 if print_findings(findings) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LlamaServerError as exc:
        print(f"\n[!] {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n中断しました", file=sys.stderr)
        sys.exit(130)
