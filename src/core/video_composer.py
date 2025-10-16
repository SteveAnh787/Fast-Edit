"""Video Composer - build real FFmpeg pipelines for rendering scenes."""

from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.core.filter_presets import AUDIO_FILTER_PRESETS, VIDEO_FILTER_PRESETS


class VideoComposerError(RuntimeError):
    """Raised when rendering fails."""


@dataclass
class RenderResult:
    """Metadata about a rendered segment."""

    index: int
    audio_path: str
    image_path: str
    subtitle_path: Optional[str]
    output_path: str
    duration: float
    success: bool
    error: Optional[str] = None


@dataclass
class SubtitleStyle:
    """Subtitle burn-in styling parameters."""

    font_name: str = "Space Grotesk"
    font_size: int = 48
    primary_color: str = "#FFFFFF"
    outline_color: str = "#000000"
    outline_width: float = 2.0
    letter_spacing: float = 0.0
    # Subtitle position settings
    margin_bottom: int = 60  # Distance from bottom in pixels
    alignment: int = 2  # 1=left, 2=center, 3=right


@dataclass
class AnimationSettings:
    type: str = "none"  # none, zoom_in, zoom_out
    intensity: str = "medium"  # subtle, medium, strong


@dataclass
class TransitionSettings:
    type: str = "none"  # none, fade, dissolve, wipe_left...
    duration: float = 1.0


@dataclass
class RenderOptions:
    frame_rate: float = 30.0
    resolution: Tuple[int, int] = (1920, 1080)
    video_codec: str = "h264"  # h264 or hevc
    video_bitrate: str = "8000k"
    audio_bitrate: str = "192k"
    burn_subtitles: bool = False
    subtitle_style: SubtitleStyle = field(default_factory=SubtitleStyle)
    animation: AnimationSettings = field(default_factory=AnimationSettings)
    transition: TransitionSettings = field(default_factory=TransitionSettings)
    use_hardware_acceleration: bool = True
    keep_intermediate: bool = False
    combined_filename: str = "complete_video.mp4"
    video_filters: List[str] = field(default_factory=list)
    audio_filters: List[str] = field(default_factory=list)
    sync_mode: str = "standard"  # standard | sync_audio | sync_images
    # Background Music Settings
    background_music_directory: Optional[str] = None
    # Logo Settings
    logo_file: Optional[str] = None
    logo_enabled: bool = False
    logo_size: int = 15  # percentage
    logo_opacity: int = 80  # percentage
    logo_x: int = 50
    logo_y: int = 50
    logo_remove_background: bool = False


@dataclass
class RenderBatchResult:
    scenes: List[RenderResult] = field(default_factory=list)
    combined: Optional[RenderResult] = None


@dataclass
class SrtEntry:
    start: float
    end: float
    lines: List[str]


ProgressCallback = Optional[Callable[[str, float, Optional[str]], None]]


class VideoComposer:
    """High level interface for FFmpeg based rendering."""

    def __init__(self) -> None:
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        self.ffmpeg_available = self._command_available(["ffmpeg", "-version"])
        self.ffprobe_available = self._command_available(["ffprobe", "-version"])

    @staticmethod
    def _command_available(cmd: List[str]) -> bool:
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False

    def get_system_status(self) -> Dict[str, Any]:
        return {
            "ffmpeg_available": self.ffmpeg_available,
            "ffprobe_available": self.ffprobe_available,
            "ready_to_render": self.ffmpeg_available and self.ffprobe_available,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def render_project(
        self,
        audio_directory: str,
        image_directory: str,
        output_directory: str,
        subtitle_directory: Optional[str] = None,
        options: Optional[RenderOptions] = None,
        create_individual: bool = True,
        create_combined: bool = False,
        progress_callback: ProgressCallback = None,
    ) -> RenderBatchResult:
        if not self.ffmpeg_available:
            raise VideoComposerError("FFmpeg không khả dụng trên hệ thống.")
        if not self.ffprobe_available:
            raise VideoComposerError("FFprobe không khả dụng trên hệ thống.")

        options = options or RenderOptions()
        audio_dir = Path(audio_directory)
        image_dir = Path(image_directory)
        subtitle_dir = Path(subtitle_directory) if subtitle_directory else None
        output_dir = Path(output_directory)

        if not audio_dir.exists():
            raise VideoComposerError(f"Thư mục audio không tồn tại: {audio_directory}")
        if not image_dir.exists():
            raise VideoComposerError(f"Thư mục image không tồn tại: {image_directory}")
        output_dir.mkdir(parents=True, exist_ok=True)

        audio_files = self._find_audio_files(audio_dir)
        image_files = self._find_image_files(image_dir)

        if not audio_files:
            raise VideoComposerError("Không tìm thấy file audio.")
        if not image_files:
            raise VideoComposerError("Không tìm thấy file image.")

        audio_files.sort(key=lambda p: p.name.lower())
        image_files.sort(key=lambda p: p.name.lower())

        temp_dir = Path(tempfile.mkdtemp(prefix="vibe_render_"))
        batch_result = RenderBatchResult()
        segment_plan = self._build_segment_plan(
            audio_files=audio_files,
            image_files=image_files,
            subtitle_dir=subtitle_dir,
            options=options,
            temp_dir=temp_dir,
        )
        if not segment_plan:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise VideoComposerError("Không có cặp audio/image hợp lệ.")

        total_steps = len(segment_plan) + (1 if create_combined else 0)
        completed_steps = 0

        try:
            scene_outputs: List[Path] = []
            scene_durations: List[float] = []

            if create_individual or create_combined:
                for index, plan in enumerate(segment_plan, start=1):
                    if progress_callback:
                        progress_callback(
                            "scene",
                            completed_steps / max(total_steps, 1),
                            f"Rendering clip {index}/{len(segment_plan)}",
                        )
                    result = self._render_scene(
                        index=index,
                        audio_file=plan["audio"],
                        image_file=plan["image"],
                        subtitle_file=plan.get("subtitle"),
                        output_dir=output_dir,
                        temp_dir=temp_dir,
                        options=options,
                    )
                    batch_result.scenes.append(result)
                    if result.success:
                        scene_outputs.append(Path(result.output_path))
                        scene_durations.append(result.duration)
                    else:
                        raise VideoComposerError(result.error or "Render thất bại")

                    completed_steps += 1
                    if progress_callback:
                        progress_callback(
                            "scene",
                            completed_steps / max(total_steps, 1),
                            f"Hoàn thành clip {index}",
                        )

            if create_combined and scene_outputs:
                if progress_callback:
                    progress_callback(
                        "combined",
                        completed_steps / max(total_steps, 1),
                        "Đang ghép video hoàn chỉnh",
                    )
                combined_result = self._render_combined(
                    clips=scene_outputs,
                    durations=scene_durations,
                    output_dir=output_dir,
                    options=options,
                )
                batch_result.combined = combined_result
                completed_steps += 1
                if progress_callback:
                    progress_callback(
                        "combined",
                        completed_steps / max(total_steps, 1),
                        "Hoàn thành video ghép",
                    )

            if not options.keep_intermediate:
                self._cleanup_temp_outputs(scene_outputs, keep=create_individual)
                shutil.rmtree(temp_dir, ignore_errors=True)
            else:
                self._write_manifest(temp_dir, scene_outputs)

        except Exception as exc:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise

        return batch_result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _find_audio_files(self, directory: Path) -> List[Path]:
        return [
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
        ]

    def _find_image_files(self, directory: Path) -> List[Path]:
        return [
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif", ".webp"}
        ]

    def _build_segment_plan(
        self,
        audio_files: List[Path],
        image_files: List[Path],
        subtitle_dir: Optional[Path],
        options: RenderOptions,
        temp_dir: Path,
    ) -> List[Dict[str, Path]]:
        subtitle_lookup = self._build_subtitle_lookup(subtitle_dir)

        mode = (options.sync_mode or "standard").lower()
        subtitle_order = self._ordered_subtitle_list(subtitle_lookup)

        if mode == "sync_images":
            return self._build_plan_sync_images(audio_files, image_files, subtitle_lookup, subtitle_order, temp_dir)
        if mode == "sync_audio":
            return self._build_plan_sync_audio(audio_files, image_files, subtitle_lookup, subtitle_order, temp_dir)
        return self._build_plan_standard(audio_files, image_files, subtitle_lookup, subtitle_order)

    def _build_plan_standard(
        self,
        audio_files: List[Path],
        image_files: List[Path],
        subtitle_lookup: Dict[str, Path],
        subtitle_order: List[Path],
    ) -> List[Dict[str, Path]]:

        if not audio_files:
            return []

        pairs: List[Dict[str, Path]] = []
        max_pairs = min(len(audio_files), len(image_files))
        for index in range(max_pairs):
            audio_file = audio_files[index]
            image_file = image_files[index]
            subtitle_file = self._subtitle_for_audio(index, audio_file, subtitle_lookup, subtitle_order)
            plan_item: Dict[str, Path] = {
                "audio": audio_file,
                "image": image_file,
            }
            if subtitle_file:
                plan_item["subtitle"] = subtitle_file
            pairs.append(plan_item)
        return pairs

    def _build_subtitle_lookup(self, subtitle_dir: Optional[Path]) -> Dict[str, Path]:
        lookup: Dict[str, Path] = {}
        if subtitle_dir and subtitle_dir.exists():
            for path in subtitle_dir.glob("*.srt"):
                lookup[path.stem.lower()] = path
        return lookup

    def _build_plan_sync_images(
        self,
        audio_files: List[Path],
        image_files: List[Path],
        subtitle_lookup: Dict[str, Path],
        subtitle_order: List[Path],
        temp_dir: Path,
    ) -> List[Dict[str, Path]]:
        if not image_files or not audio_files:
            return []

        plan: List[Dict[str, Path]] = []
        image_count = len(image_files)
        if image_count == 0:
            return plan

        # Determine how many audio clips per image (rounded up)
        group_size = max(1, math.ceil(len(audio_files) / image_count))
        audio_index = 0

        for idx, image_file in enumerate(image_files):
            grouped_audio = audio_files[audio_index : audio_index + group_size]
            audio_index += len(grouped_audio)
            if not grouped_audio:
                break

            if len(grouped_audio) == 1:
                audio_path = grouped_audio[0]
            else:
                concat_path = temp_dir / f"sync_img_audio_{idx:03d}.wav"
                self._concat_audio_files(grouped_audio, concat_path)
                audio_path = concat_path

            subtitle_file: Optional[Path] = None
            combined_path = temp_dir / f"sync_img_sub_{idx:03d}.srt"
            combined = self._combine_group_subtitles(
                audio_group=grouped_audio,
                subtitle_lookup=subtitle_lookup,
                subtitle_order=subtitle_order,
                destination=combined_path,
                start_index=audio_index - len(grouped_audio),
            )
            if combined:
                subtitle_file = combined
            if subtitle_file is None and subtitle_order:
                subtitle_file = subtitle_order[idx % len(subtitle_order)]

            plan_item: Dict[str, Path] = {
                "audio": audio_path,
                "image": image_file,
            }
            if subtitle_file:
                plan_item["subtitle"] = subtitle_file
            plan.append(plan_item)

            if audio_index >= len(audio_files):
                break

        return plan

    def _build_plan_sync_audio(
        self,
        audio_files: List[Path],
        image_files: List[Path],
        subtitle_lookup: Dict[str, Path],
        subtitle_order: List[Path],
        temp_dir: Path,
    ) -> List[Dict[str, Path]]:
        if not image_files or not audio_files:
            return []

        if len(audio_files) == 1:
            full_audio_path = audio_files[0]
        else:
            full_audio_path = temp_dir / "sync_audio_full.wav"
            self._concat_audio_files(audio_files, full_audio_path)

        total_duration = self._probe_duration(full_audio_path)
        if total_duration <= 0:
            return []

        image_count = len(image_files)
        base_duration = total_duration / image_count

        plan: List[Dict[str, Path]] = []
        current_start = 0.0
        timeline_entries = self._collect_timeline_entries(audio_files, subtitle_lookup, subtitle_order)

        for idx, image_file in enumerate(image_files):
            # Ensure final segment uses remaining time to avoid rounding gaps
            if idx == image_count - 1:
                segment_duration = max(total_duration - current_start, 0.0)
            else:
                segment_duration = base_duration

            if segment_duration <= 0:
                continue

            trimmed_audio = temp_dir / f"sync_audio_segment_{idx:03d}.wav"
            self._extract_audio_segment(
                source=full_audio_path,
                start=current_start,
                duration=segment_duration,
                destination=trimmed_audio,
            )

            plan_item: Dict[str, Path] = {
                "audio": trimmed_audio,
                "image": image_file,
            }

            subtitle_file: Optional[Path] = None
            if timeline_entries:
                slice_path = temp_dir / f"sync_audio_sub_{idx:03d}.srt"
                if self._write_srt_slice(timeline_entries, current_start, current_start + segment_duration, slice_path):
                    subtitle_file = slice_path
            if subtitle_file is None and subtitle_order:
                subtitle_file = subtitle_order[idx % len(subtitle_order)]

            if subtitle_file:
                plan_item["subtitle"] = subtitle_file

            plan.append(plan_item)
            current_start += segment_duration

        return plan

    def _concat_audio_files(self, audio_paths: List[Path], output_path: Path) -> None:
        if len(audio_paths) == 1:
            shutil.copy(audio_paths[0], output_path)
            return

        list_path = output_path.with_suffix(".txt")
        with list_path.open("w", encoding="utf-8") as handle:
            for path in audio_paths:
                handle.write(f"file '{path.as_posix()}'\n")

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-c",
            "pcm_s16le",
            str(output_path),
        ]
        process = subprocess.run(cmd, capture_output=True, text=True)
        list_path.unlink(missing_ok=True)
        if process.returncode != 0:
            raise VideoComposerError(process.stderr.strip() or "Không thể nối file audio.")

    def _extract_audio_segment(self, source: Path, start: float, duration: float, destination: Path) -> None:
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            f"{max(start, 0.0):.6f}",
            "-t",
            f"{max(duration, 0.0):.6f}",
            "-i",
            str(source),
            "-acodec",
            "pcm_s16le",
            str(destination),
        ]
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0:
            raise VideoComposerError(process.stderr.strip() or "Không thể cắt đoạn audio.")

    def _ordered_subtitle_list(self, subtitle_lookup: Dict[str, Path]) -> List[Path]:
        return sorted(subtitle_lookup.values(), key=lambda p: p.name.lower()) if subtitle_lookup else []

    def _subtitle_for_audio(
        self,
        index: int,
        audio_file: Path,
        subtitle_lookup: Dict[str, Path],
        subtitle_order: List[Path],
    ) -> Optional[Path]:
        if subtitle_lookup:
            match = subtitle_lookup.get(audio_file.stem.lower())
            if match:
                return match
        if subtitle_order:
            return subtitle_order[index % len(subtitle_order)]
        return None

    def _combine_group_subtitles(
        self,
        audio_group: List[Path],
        subtitle_lookup: Dict[str, Path],
        subtitle_order: List[Path],
        destination: Path,
        start_index: int,
    ) -> Optional[Path]:
        entries: List[SrtEntry] = []
        offset = 0.0
        for idx, audio_file in enumerate(audio_group):
            srt_path = self._subtitle_for_audio(start_index + idx, audio_file, subtitle_lookup, subtitle_order)
            if srt_path and srt_path.exists():
                parsed = self._parse_srt_entries(srt_path)
                entries.extend(SrtEntry(entry.start + offset, entry.end + offset, entry.lines) for entry in parsed)
            offset += self._probe_duration(audio_file)

        if not entries:
            return None

        entries.sort(key=lambda e: e.start)
        self._write_srt_entries(entries, destination)
        return destination

    def _collect_timeline_entries(
        self,
        audio_files: List[Path],
        subtitle_lookup: Dict[str, Path],
        subtitle_order: List[Path],
    ) -> List[SrtEntry]:
        timeline: List[SrtEntry] = []
        offset = 0.0
        for index, audio_file in enumerate(audio_files):
            srt_path = self._subtitle_for_audio(index, audio_file, subtitle_lookup, subtitle_order)
            if srt_path and srt_path.exists():
                parsed = self._parse_srt_entries(srt_path)
                timeline.extend(SrtEntry(entry.start + offset, entry.end + offset, entry.lines) for entry in parsed)
            offset += self._probe_duration(audio_file)
        timeline.sort(key=lambda e: e.start)
        return timeline

    def _write_srt_slice(
        self,
        entries: List[SrtEntry],
        start: float,
        end: float,
        destination: Path,
    ) -> bool:
        slice_entries: List[SrtEntry] = []
        for entry in entries:
            if entry.end <= start or entry.start >= end:
                continue
            new_start = max(entry.start, start) - start
            new_end = min(entry.end, end) - start
            if new_end <= new_start:
                continue
            slice_entries.append(SrtEntry(new_start, new_end, entry.lines))

        if not slice_entries:
            return False

        self._write_srt_entries(slice_entries, destination)
        return True

    def _write_srt_entries(self, entries: List[SrtEntry], destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        entries_sorted = sorted(entries, key=lambda e: e.start)
        with destination.open("w", encoding="utf-8") as handle:
            for index, entry in enumerate(entries_sorted, start=1):
                start_str = self._seconds_to_srt(max(entry.start, 0.0))
                end_str = self._seconds_to_srt(max(entry.end, 0.0))
                handle.write(f"{index}\n{start_str} --> {end_str}\n")
                for line in entry.lines:
                    handle.write(f"{line}\n")
                handle.write("\n")

    def _parse_srt_entries(self, path: Path) -> List[SrtEntry]:
        entries: List[SrtEntry] = []
        if not path.exists():
            return entries

        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return entries

        raw = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not raw:
            return entries

        blocks = re.split(r"\n\s*\n", raw)
        for block in blocks:
            lines = [line for line in block.split("\n") if line.strip() != "" or line == ""]
            if not lines:
                continue
            lines = [line.strip("\ufeff") for line in lines]
            if re.match(r"^\d+$", lines[0].strip()):
                lines = lines[1:]
            if not lines:
                continue
            timing_line = lines[0].strip()
            if "-->" not in timing_line:
                continue
            start_text, end_text = [part.strip() for part in timing_line.split("-->")]
            try:
                start_sec = self._srt_time_to_seconds(start_text)
                end_sec = self._srt_time_to_seconds(end_text)
            except ValueError:
                continue
            text_lines = lines[1:] or [""]
            entries.append(SrtEntry(start=start_sec, end=end_sec, lines=text_lines))

        return entries

    def _srt_time_to_seconds(self, value: str) -> float:
        value = value.strip()
        value = value.replace(",", ".")
        match = re.match(r"(?:(\d+):)?(\d{2}):(\d{2})\.(\d{1,3})", value)
        if not match:
            raise ValueError("Invalid SRT timestamp")
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        milliseconds = int(match.group(4).ljust(3, "0"))
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0

    def _seconds_to_srt(self, value: float) -> str:
        value = max(value, 0.0)
        hours = int(value // 3600)
        minutes = int((value % 3600) // 60)
        seconds = int(value % 60)
        milliseconds = int(round((value - int(value)) * 1000))
        if milliseconds >= 1000:
            milliseconds -= 1000
            seconds += 1
        if seconds >= 60:
            seconds -= 60
            minutes += 1
        if minutes >= 60:
            minutes -= 60
            hours += 1
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def _render_scene(
        self,
        index: int,
        audio_file: Path,
        image_file: Path,
        subtitle_file: Optional[Path],
        output_dir: Path,
        temp_dir: Path,
        options: RenderOptions,
    ) -> RenderResult:
        duration = self._probe_duration(audio_file)
        if duration <= 0:
            return RenderResult(index, str(audio_file), str(image_file), str(subtitle_file) if subtitle_file else None, "", 0.0, False, "Không xác định được thời lượng audio")

        output_path = output_dir / f"clip_{index:03d}.mp4"
        temp_output = temp_dir / f"clip_{index:03d}.mp4"

        cmd: List[str] = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-framerate",
            f"{options.frame_rate}",
            "-i",
            str(image_file),  # Input 0: image
            "-i",
            str(audio_file),  # Input 1: audio
        ]

        # Track input indices
        current_input_index = 2
        logo_input_index = None
        music_input_index = None
        
        # Add logo input if enabled
        if options.logo_enabled and options.logo_file and Path(options.logo_file).exists():
            cmd.extend(["-i", str(options.logo_file)])
            logo_input_index = current_input_index
            current_input_index += 1

        # Add background music if provided
        background_music_file = None
        if options.background_music_directory:
            background_music_file = self._get_background_music(options.background_music_directory, duration)
            if background_music_file:
                cmd.extend(["-i", str(background_music_file)])
                music_input_index = current_input_index
                current_input_index += 1

        # Add subtitle file if not burning subtitles
        input_sub_index = None
        if subtitle_file and not options.burn_subtitles:
            cmd.extend(["-i", str(subtitle_file)])
            input_sub_index = current_input_index
            current_input_index += 1

        cmd.extend([
            "-t",
            f"{duration:.4f}",
            "-r",
            f"{options.frame_rate}",
        ])

        video_steps = self._video_filter_steps(
            options=options,
            duration=duration,
            frame_rate=options.frame_rate,
            resolution=options.resolution,
        )
        audio_chain = self._audio_filter_chain(options)

        # Determine what complex processing we need
        has_logo = logo_input_index is not None
        has_background_music = music_input_index is not None
        needs_complex_filter = has_logo or has_background_music or (options.burn_subtitles and subtitle_file)

        if needs_complex_filter:
            # Build complex filter with better error handling and debugging
            filter_parts = []

            # Start with base animation + filter chain for video
            base_chain = ",".join(step for step in video_steps if step)
            video_label_index = 0
            filter_parts.append(f"[0:v]{base_chain}[v{video_label_index}]")
            video_stream = f"[v{video_label_index}]"

            # Add logo overlay if enabled
            if has_logo:
                # First add logo preprocessing filters if needed
                logo_preprocessing = self._build_logo_preprocessing(options, logo_input_index)
                overlay_source = f"[{logo_input_index}:v]"
                if logo_preprocessing:
                    filter_parts.append(f"[{logo_input_index}:v]{logo_preprocessing}[logo_pre]")
                    overlay_source = "[logo_pre]"

                video_label_index += 1
                next_video_stream = f"[v{video_label_index}]"
                filter_parts.append(
                    f"{video_stream}{overlay_source}overlay={options.logo_x}:{options.logo_y}{next_video_stream}"
                )
                video_stream = next_video_stream

            # Add subtitle filter if burning subtitles
            if options.burn_subtitles and subtitle_file:
                subtitle_filter = self._build_subtitle_filter(subtitle_file, options.subtitle_style)
                video_label_index += 1
                next_video_stream = f"[v{video_label_index}]"
                filter_parts.append(f"{video_stream}{subtitle_filter}{next_video_stream}")
                video_stream = next_video_stream

            # Ensure consistent pixel format at the end
            video_label_index += 1
            final_video_stream = f"[v{video_label_index}]"
            filter_parts.append(f"{video_stream}format=yuv420p{final_video_stream}")
            video_stream = final_video_stream

            # Handle audio mixing
            audio_stream = "1:a"  # Default to original audio input (stream spec)
            audio_label_index = 0
            if has_background_music:
                music_duration = self._probe_duration(background_music_file)
                audio_mix_filter = self._build_audio_mix_filter_corrected(music_input_index, duration, music_duration)
                if audio_mix_filter:
                    filter_parts.append(audio_mix_filter)
                    audio_stream = "[aout]"

            if audio_chain:
                for expression in audio_chain:
                    audio_label_index += 1
                    target_label = f"[a{audio_label_index}]"
                    source_label = audio_stream if audio_stream.startswith("[") else f"[{audio_stream}]"
                    filter_parts.append(f"{source_label}{expression}{target_label}")
                    audio_stream = target_label

            # Combine all filters and add debug output
            complex_filter = ";".join(filter_parts)
            print(f"DEBUG: Has logo: {has_logo}, Logo enabled: {options.logo_enabled}, Logo file: {options.logo_file}")
            print(f"DEBUG: Logo input index: {logo_input_index}")
            print(f"DEBUG: Complex filter: {complex_filter}")
            print(f"DEBUG: Video stream: {video_stream}, Audio stream: {audio_stream}")
            
            cmd.extend(["-filter_complex", complex_filter])
            # Use proper mapping format
            if video_stream.startswith("["):
                cmd.extend(["-map", video_stream])
            else:
                cmd.extend(["-map", f"[{video_stream}]"])
            
            if audio_stream.startswith("["):
                cmd.extend(["-map", audio_stream])
            else:
                cmd.extend(["-map", audio_stream])
        else:
            # Simple processing - no complex filter needed
            vf_parts = list(video_steps) + ["format=yuv420p"]
            video_filter = ",".join(part for part in vf_parts if part)
            cmd.extend(["-vf", video_filter])
            if audio_chain:
                cmd.extend(["-af", ",".join(audio_chain)])

            cmd.extend(["-map", "0:v:0", "-map", "1:a:0"])

        cmd.extend(self._video_encoder_args(options))
        cmd.extend(["-c:a", "aac", "-b:a", options.audio_bitrate])

        # Add subtitle stream if not burning
        if input_sub_index is not None:
            cmd.extend(["-c:s", "mov_text"])
            cmd.extend(["-map", f"{input_sub_index}:0"])

        cmd.extend(["-shortest", "-movflags", "+faststart", str(temp_output)])

        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0:
            return RenderResult(
                index,
                str(audio_file),
                str(image_file),
                str(subtitle_file) if subtitle_file else None,
                str(temp_output),
                duration,
                False,
                process.stderr.strip() or "FFmpeg render failed",
            )

        shutil.move(str(temp_output), str(output_path))
        return RenderResult(
            index,
            str(audio_file),
            str(image_file),
            str(subtitle_file) if subtitle_file else None,
            str(output_path),
            duration,
            True,
        )

    def _render_combined(
        self,
        clips: List[Path],
        durations: List[float],
        output_dir: Path,
        options: RenderOptions,
    ) -> RenderResult:
        if not clips:
            raise VideoComposerError("Không có clip để ghép.")

        combined_path = output_dir / (options.combined_filename or "complete_video.mp4")
        
        # For combined video, we should NOT add background music again 
        # because individual clips already have it mixed in
        # We simply concatenate the pre-rendered clips
        
        # Always use simple concatenation for combined video to avoid complex filter issues
        return self._combine_without_transition(clips, durations, combined_path)

    def _combine_without_transition(
        self,
        clips: List[Path],
        durations: List[float],
        output_path: Path,
    ) -> RenderResult:
        concat_file = output_path.with_suffix(".txt")
        with concat_file.open("w", encoding="utf-8") as handle:
            for clip in clips:
                handle.write(f"file '{clip.as_posix()}'\n")

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(output_path),
        ]
        process = subprocess.run(cmd, capture_output=True, text=True)
        concat_file.unlink(missing_ok=True)
        if process.returncode != 0:
            raise VideoComposerError(process.stderr.strip() or "Ghép video thất bại")

        total_duration = sum(durations)
        return RenderResult(0, "", "", None, str(output_path), total_duration, True)

    def _build_transition_filter(
        self,
        count: int,
        durations: List[float],
        transition: str,
        transition_duration: float,
    ) -> Tuple[str, str, str, float]:
        video_label = "[0:v]"
        audio_label = "[0:a]"
        filter_parts: List[str] = []
        current_duration = durations[0]

        for idx in range(1, count):
            v_in = video_label
            a_in = audio_label
            next_v = f"[{idx}:v]"
            next_a = f"[{idx}:a]"
            v_out = f"[v{idx}]"
            a_out = f"[a{idx}]"

            offset = max(current_duration - transition_duration, 0.0)
            filter_parts.append(
                f"{v_in}{next_v}xfade=transition={transition}:duration={transition_duration:.4f}:offset={offset:.4f}{v_out}"
            )
            filter_parts.append(
                f"{a_in}{next_a}acrossfade=d={transition_duration:.4f}{a_out}"
            )
            video_label = v_out
            audio_label = a_out
            current_duration = current_duration + durations[idx] - transition_duration

        filter_expression = ";".join(filter_parts)
        return filter_expression, video_label, audio_label, max(current_duration, 0.0)

    def _probe_duration(self, audio_file: Path) -> float:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_file),
        ]
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0:
            return 0.0
        try:
            return float(process.stdout.strip())
        except ValueError:
            return 0.0

    def _build_animation_filter(
        self,
        animation: AnimationSettings,
        duration: float,
        frame_rate: float,
        resolution: Tuple[int, int],
    ) -> str:
        width, height = resolution
        frames = max(int(math.ceil(duration * frame_rate)), 1)
        base = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"  # scale to cover while preserving aspect
            f"crop={width}:{height}"  # then crop overflow
        )

        anim_type = (animation.type or "none").lower()
        intensity = (animation.intensity or "medium").lower()
        step_map = {"subtle": 0.0004, "medium": 0.0008, "strong": 0.0014}
        step = step_map.get(intensity, 0.0008)

        if anim_type == "zoom_in":
            zoom_expr = f"'min(1.0+{step}*on,1.5)'"
            return f"{base},zoompan=z={zoom_expr}:d={frames}:s={width}x{height}:fps={frame_rate},setsar=1"
        if anim_type == "zoom_out":
            start_zoom = 1.3 if intensity == "strong" else 1.2 if intensity == "medium" else 1.1
            zoom_expr = f"'max({start_zoom}-{step}*on,1.0)'"
            return f"{base},zoompan=z={zoom_expr}:d={frames}:s={width}x{height}:fps={frame_rate},setsar=1"
        if anim_type == "ken_burns":
            zoom_expr = f"'min(1.0+{step}*on,1.25)'"
            x_expr = "'(iw-iw/zoom)/2'"
            y_expr = "'(ih-ih/zoom)/2'"
            return (
                f"{base},zoompan=z={zoom_expr}:x={x_expr}:y={y_expr}:d={frames}:s={width}x{height}:fps={frame_rate},setsar=1"
            )
        if anim_type in {"pan_left", "pan_right", "pan_up", "pan_down"}:
            divisor = max(frames - 1, 1)
            x_expr = "'0'"
            y_expr = "'0'"
            if anim_type == "pan_left":
                x_expr = f"'(iw-ow)*on/{divisor}'"
            elif anim_type == "pan_right":
                x_expr = f"'(iw-ow)*(1-on/{divisor})'"
            elif anim_type == "pan_up":
                y_expr = f"'(ih-oh)*(1-on/{divisor})'"
            elif anim_type == "pan_down":
                y_expr = f"'(ih-oh)*on/{divisor}'"
            return (
                f"{base},zoompan=z='1.0':x={x_expr}:y={y_expr}:d={frames}:s={width}x{height}:fps={frame_rate},setsar=1"
            )

        return f"{base},setsar=1"

    def _build_subtitle_filter(self, subtitle_file: Path, style: SubtitleStyle) -> str:
        subtitle_path = str(subtitle_file).replace("\\", "/").replace(":", r"\\:")
        primary = self._hex_to_bgr(style.primary_color)
        outline = self._hex_to_bgr(style.outline_color)
        force_style = (
            f"FontName={style.font_name},FontSize={style.font_size},PrimaryColour={primary},"
            f"OutlineColour={outline},Outline={style.outline_width},Spacing={style.letter_spacing},"
            f"MarginV={style.margin_bottom},Alignment={style.alignment}"
        )
        return f"subtitles='{subtitle_path}':force_style='{force_style}'"

    def _video_encoder_args(self, options: RenderOptions) -> List[str]:
        hw = options.use_hardware_acceleration
        codec = options.video_codec.lower()
        if hw:
            encoder = "hevc_videotoolbox" if codec == "hevc" else "h264_videotoolbox"
            return [
                "-c:v",
                encoder,
                "-allow_sw",
                "1",
                "-b:v",
                options.video_bitrate,
                "-pix_fmt",
                "yuv420p",
            ]
        encoder = "libx265" if codec == "hevc" else "libx264"
        return [
            "-c:v",
            encoder,
            "-preset",
            "medium",
            "-b:v",
            options.video_bitrate,
            "-pix_fmt",
            "yuv420p",
        ]

    def _hex_to_bgr(self, hex_color: str) -> str:
        value = hex_color.lstrip("#")
        if len(value) != 6:
            value = "FFFFFF"
        r = int(value[0:2], 16)
        g = int(value[2:4], 16)
        b = int(value[4:6], 16)
        return f"&H00{b:02X}{g:02X}{r:02X}"

    def _cleanup_temp_outputs(self, clips: List[Path], keep: bool) -> None:
        if keep:
            return
        for clip in clips:
            clip.unlink(missing_ok=True)

    def _write_manifest(self, temp_dir: Path, clips: List[Path]) -> None:
        manifest = {
            "clips": [str(path) for path in clips],
            "note": "clip files preserved for debugging",
        }
        with (temp_dir / "manifest.json").open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, ensure_ascii=False)

    def _map_transition_name(self, transition: str) -> Optional[str]:
        mapping = {
            "none": None,
            "fade": "fade",
            "dissolve": "dissolve",
            "crossfade": "fade",
            "wipe_left": "wipeleft",
            "wipe_right": "wiperight",
            "wipe_up": "wipeup",
            "wipe_down": "wipedown",
            "slide_left": "slideleft",
            "slide_right": "slideright",
            "slide_up": "slideup",
            "slide_down": "slidedown",
            "smooth_left": "smoothleft",
            "smooth_right": "smoothright",
            "blur": "fadeblack",
            "fade_white": "fadewhite",
            "circle_open": "circleopen",
            "circle_close": "circleclose",
            "pixelize": "pixelize",
            "radial": "radial",
        }
        return mapping.get(transition, "fade" if transition else None)

    def _get_background_music(self, music_directory: str, target_duration: float) -> Optional[Path]:
        """Get background music file and prepare it to match target duration"""
        music_dir = Path(music_directory)
        if not music_dir.exists():
            return None
            
        # Find music files
        music_files = [
            path for path in music_dir.iterdir()
            if path.is_file() and path.suffix.lower() in {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
        ]
        
        if not music_files:
            return None
            
        # Use first music file found
        music_file = music_files[0]
        music_duration = self._probe_duration(music_file)
        
        if music_duration <= 0:
            return None
            
        # If music is longer than target, we'll trim it during ffmpeg processing
        # If music is shorter, we'll loop it during ffmpeg processing
        return music_file

    def _build_logo_preprocessing(self, options: RenderOptions, logo_input_index: int) -> Optional[str]:
        """Build logo preprocessing filters (scale/opacity) that apply to logo input alone"""
        logo_scale = options.logo_size / 100.0
        opacity = options.logo_opacity / 100.0
        
        # Build logo preprocessing filters
        logo_filters = []
        
        if logo_scale != 1.0:
            logo_filters.append(f"scale=iw*{logo_scale}:ih*{logo_scale}")
            
        if opacity < 1.0:
            logo_filters.append(f"format=rgba,colorchannelmixer=aa={opacity}")
        
        # Return preprocessing filter chain or None if no preprocessing needed
        return ",".join(logo_filters) if logo_filters else None

    def _build_audio_mix_filter_corrected(self, music_input_index: int, target_duration: float, music_duration: float) -> str:
        """Build corrected audio mixing filter with proper input indices"""
        # If music is shorter than target, loop it
        if music_duration > 0 and music_duration < target_duration:
            loops_needed = int(target_duration / music_duration) + 1
            sample_rate = 48000  # Standard sample rate
            loop_size = int(sample_rate * music_duration)
            music_filter = f"[{music_input_index}:a]aloop=loop={loops_needed}:size={loop_size}[bgm]"
            # Mix main audio with background music (30% background volume)
            mix_filter = "[1:a][bgm]amix=inputs=2:duration=first:weights='1 0.3'[aout]"
            return f"{music_filter};{mix_filter}"
        else:
            # Mix directly (music will be trimmed to match video duration by -shortest)
            return f"[1:a][{music_input_index}:a]amix=inputs=2:duration=first:weights='1 0.3'[aout]"

    def _video_filter_steps(
        self,
        options: RenderOptions,
        duration: float,
        frame_rate: float,
        resolution: Tuple[int, int],
    ) -> List[str]:
        steps: List[str] = [
            self._build_animation_filter(
                animation=options.animation,
                duration=duration,
                frame_rate=frame_rate,
                resolution=resolution,
            )
        ]
        for filter_id in options.video_filters:
            preset = VIDEO_FILTER_PRESETS.get(filter_id)
            if preset and preset.target == "video":
                steps.append(preset.expression)
        return [step for step in steps if step]

    def _audio_filter_chain(self, options: RenderOptions) -> List[str]:
        chain: List[str] = []
        for filter_id in options.audio_filters:
            preset = AUDIO_FILTER_PRESETS.get(filter_id)
            if preset and preset.target == "audio":
                chain.append(preset.expression)
        return chain
