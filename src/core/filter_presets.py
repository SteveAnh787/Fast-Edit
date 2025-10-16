"""
Preset definitions for FFmpeg-based video and audio filters used by the UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class FilterPreset:
    """Describes a reusable FFmpeg filter expression."""

    id: str
    name: str
    expression: str
    target: str  # "video" or "audio"
    description: str = ""
    category: str = "general"


def _ordered_dict(presets: Iterable[FilterPreset]) -> Dict[str, FilterPreset]:
    return {preset.id: preset for preset in presets}


VIDEO_FILTER_PRESETS: Dict[str, FilterPreset] = _ordered_dict(
    [
        FilterPreset(
            id="warm_tone",
            name="Warm Cinematic",
            expression="eq=contrast=1.08:brightness=0.03:saturation=1.12",
            target="video",
            description="Boosts contrast and saturation slightly for a warm cinematic look.",
            category="color",
        ),
        FilterPreset(
            id="cool_teal",
            name="Teal & Orange",
            expression="curves=preset=teal_orange",
            target="video",
            description="Classic teal/orange colour grade via curves preset.",
            category="color",
        ),
        FilterPreset(
            id="b_and_w",
            name="Black & White",
            expression="hue=s=0",
            target="video",
            description="Desaturates frame entirely for monochrome effect.",
            category="color",
        ),
        FilterPreset(
            id="sharp_pop",
            name="Sharpen",
            expression="unsharp=5:5:0.8:5:5:0.0",
            target="video",
            description="Adds crispness to details with mild sharpening.",
            category="detail",
        ),
        FilterPreset(
            id="soft_glow",
            name="Soft Glow",
            expression="gblur=sigma=8,eq=saturation=1.1:contrast=1.05",
            target="video",
            description="Applies gaussian blur with gentle contrast lift for dreamy look.",
            category="atmosphere",
        ),
        FilterPreset(
            id="vignette_focus",
            name="Vignette",
            expression="vignette=PI/5",
            target="video",
            description="Darkens corners to draw attention to centre.",
            category="atmosphere",
        ),
        FilterPreset(
            id="film_grain",
            name="Film Grain",
            expression="noise=alls=20:allf=t",
            target="video",
            description="Adds temporal grain for vintage feel.",
            category="texture",
        ),
        FilterPreset(
            id="motion_blur",
            name="Motion Blur",
            expression="tblend=all_mode='average':all_opacity=0.7",
            target="video",
            description="Blends frames for light motion blur.",
            category="motion",
        ),
    ]
)


AUDIO_FILTER_PRESETS: Dict[str, FilterPreset] = _ordered_dict(
    [
        FilterPreset(
            id="voice_clarity",
            name="Voice Clarity",
            expression="anequalizer=f=120:t=q:w=1.0:g=3,anequalizer=f=3000:t=q:w=1.5:g=4",
            target="audio",
            description="Boosts presence frequencies suited for narration/dialogue.",
            category="speech",
        ),
        FilterPreset(
            id="bass_boost",
            name="Bass Boost",
            expression="bass=g=5:f=110:w=0.4",
            target="audio",
            description="Adds low-end body to music tracks.",
            category="music",
        ),
        FilterPreset(
            id="treble_air",
            name="Airy Treble",
            expression="treble=g=4:f=6000:w=0.5",
            target="audio",
            description="Enhances high-end sparkle.",
            category="music",
        ),
        FilterPreset(
            id="broadcast_comp",
            name="Broadcast Compressor",
            expression="acompressor=threshold=-18dB:ratio=3:attack=20:release=260",
            target="audio",
            description="Smooths dynamics with gentle compression.",
            category="mastering",
        ),
        FilterPreset(
            id="loudness_norm",
            name="Loudness Normalise",
            expression="loudnorm=I=-16:LRA=11:TP=-1.5",
            target="audio",
            description="EBU R128 style loudness normalisation.",
            category="mastering",
        ),
        FilterPreset(
            id="clean_highpass",
            name="Voice High-pass",
            expression="highpass=f=80",
            target="audio",
            description="Removes low rumble for cleaner speech.",
            category="speech",
        ),
    ]
)


def video_presets_list() -> List[FilterPreset]:
    return list(VIDEO_FILTER_PRESETS.values())


def audio_presets_list() -> List[FilterPreset]:
    return list(AUDIO_FILTER_PRESETS.values())
