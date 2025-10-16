"""Subtitle generation powered by OpenAI Whisper."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import whisper


@dataclass
class SubtitleResult:
    """Thông tin kết quả sinh phụ đề cho một file audio."""

    audio_path: str
    subtitle_path: Optional[str]
    preview_lines: List[str]
    success: bool
    error: Optional[str] = None


@dataclass
class WhisperModel:
    """Metadata mô tả từng model Whisper hỗ trợ."""

    id: str
    name: str
    size_mb: int
    recommended: bool = False
    available: bool = False


class SubtitleGenerator:
    """Sinh phụ đề hàng loạt sử dụng thư viện openai-whisper."""

    MODELS = [
        WhisperModel("tiny", "Whisper Tiny", 75),
        WhisperModel("base", "Whisper Base", 142, recommended=True),
        WhisperModel("small", "Whisper Small", 465),
        WhisperModel("medium", "Whisper Medium", 1500),
    ]

    SUPPORTED_AUDIO_EXTENSIONS = {
        ".wav",
        ".mp3",
        ".m4a",
        ".aac",
        ".flac",
        ".ogg",
    }

    def __init__(self) -> None:
        self._model_cache: Dict[str, whisper.Whisper] = {}
        self._refresh_model_availability()

    # ------------------------------------------------------------------
    # Model handling
    # ------------------------------------------------------------------
    def _refresh_model_availability(self) -> None:
        cache_dir = self._cache_directory()
        for model in self.MODELS:
            model_path = cache_dir / f"{model.id}.pt"
            model.available = model_path.exists()

    def get_available_models(self) -> List[Dict[str, Any]]:
        self._refresh_model_availability()
        return [
            {
                "id": model.id,
                "name": model.name,
                "size_mb": model.size_mb,
                "recommended": model.recommended,
                "available": model.available,
            }
            for model in self.MODELS
        ]

    def download_model(self, model_id: str) -> bool:
        if model_id not in whisper._MODELS:  # type: ignore[attr-defined]
            return False

        cache_dir = self._cache_directory()

        try:
            whisper._download(  # type: ignore[attr-defined]
                whisper._MODELS[model_id],  # type: ignore[attr-defined]
                str(cache_dir),
                in_memory=False,
            )
        except Exception as exc:  # pragma: no cover - network issues
            print(f"Failed to download Whisper model '{model_id}': {exc}")
            return False

        self._refresh_model_availability()
        return True

    def _get_model(self, model_id: str) -> whisper.Whisper:
        if model_id not in self._model_cache:
            try:
                self._model_cache[model_id] = whisper.load_model(model_id)
            except Exception:
                # Try downloading once then retry load
                if not self.download_model(model_id):
                    raise
                self._model_cache[model_id] = whisper.load_model(model_id)
        return self._model_cache[model_id]

    # ------------------------------------------------------------------
    # Subtitle generation
    # ------------------------------------------------------------------
    def generate_subtitle(
        self,
        audio_path: str,
        output_path: str,
        model_id: str = "base",
        language: Optional[str] = None,
        translate_to_english: bool = False,
        threads: Optional[int] = None,
    ) -> SubtitleResult:
        audio_file = Path(audio_path)
        if not audio_file.exists():
            return SubtitleResult(audio_path, None, [], False, "File audio không tồn tại")

        try:
            model = self._get_model(model_id)
        except Exception as exc:
            return SubtitleResult(audio_path, None, [], False, f"Không thể tải model: {exc}")

        options: Dict[str, Any] = {
            "task": "translate" if translate_to_english else "transcribe",
            "fp16": False,
        }
        if language:
            options["language"] = language

        try:
            result = model.transcribe(str(audio_file), **options)
        except Exception as exc:  # pragma: no cover - whisper internal errors
            return SubtitleResult(audio_path, None, [], False, f"Lỗi Whisper: {exc}")

        segments = result.get("segments", [])
        text = result.get("text", "").strip()

        subtitle_content = self._segments_to_srt(segments) if segments else text

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(subtitle_content, encoding="utf-8")

        preview_lines = [line.strip() for line in text.splitlines() if line.strip()][:6]

        return SubtitleResult(audio_path, str(output_file), preview_lines, True)

    def generate_subtitles_batch(
        self,
        audio_directory: str,
        subtitle_directory: str,
        model_id: str = "base",
        language: Optional[str] = None,
        translate_to_english: bool = False,
        threads: Optional[int] = None,
    ) -> List[SubtitleResult]:
        audio_dir = Path(audio_directory)
        if not audio_dir.exists():
            return [SubtitleResult("", None, [], False, "Thư mục audio không tồn tại")]

        subtitle_dir = Path(subtitle_directory)
        subtitle_dir.mkdir(parents=True, exist_ok=True)

        audio_files = sorted(
            [
                path
                for path in audio_dir.iterdir()
                if path.is_file() and path.suffix.lower() in self.SUPPORTED_AUDIO_EXTENSIONS
            ],
            key=lambda p: p.name.lower(),
        )

        results: List[SubtitleResult] = []
        for index, audio_file in enumerate(audio_files, start=1):
            subtitle_name = f"subtitle_{index:03d}.srt"
            subtitle_path = subtitle_dir / subtitle_name
            result = self.generate_subtitle(
                str(audio_file),
                str(subtitle_path),
                model_id=model_id,
                language=language,
                translate_to_english=translate_to_english,
                threads=threads,
            )
            results.append(result)

        if not results:
            results.append(SubtitleResult("", None, [], False, "Không tìm thấy file audio hợp lệ"))

        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _cache_directory(self) -> Path:
        default_cache_root = Path(os.path.expanduser("~")) / ".cache"
        cache_root = Path(os.getenv("XDG_CACHE_HOME", default_cache_root))
        return cache_root / "whisper"

    def _segments_to_srt(self, segments: List[Dict[str, Any]]) -> str:
        lines: List[str] = []
        for idx, segment in enumerate(segments, start=1):
            start = self._format_timestamp(segment.get("start", 0.0))
            end = self._format_timestamp(segment.get("end", 0.0))
            text = (segment.get("text") or "").strip()
            lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
        return "\n".join(lines).strip() + "\n"

    @staticmethod
    def _format_timestamp(value: float) -> str:
        milliseconds = int(round(value * 1000))
        hours, remainder = divmod(milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        seconds, millis = divmod(remainder, 1_000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
