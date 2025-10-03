use std::collections::BTreeMap;
use std::ffi::OsStr;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

use anyhow::{anyhow, bail, Context, Result};
use natord::compare;

#[derive(Debug, Clone)]
pub struct SubtitleBurnStyle {
    pub font_name: Option<String>,
    pub font_size: Option<f32>,
    pub primary_color: Option<String>,
    pub outline_color: Option<String>,
    pub outline_width: Option<f32>,
    pub letter_spacing: Option<f32>,
}

#[derive(Debug, Clone, Copy)]
pub enum VideoCodec {
    H264,
    Hevc,
}

impl VideoCodec {}

#[derive(Debug, Clone)]
pub struct StitchOptions {
    pub audio_dir: PathBuf,
    pub image_dir: PathBuf,
    pub subtitle_dir: Option<PathBuf>,
    pub output_dir: PathBuf,
    pub frame_rate: f32,
    pub codec: VideoCodec,
    pub audio_bitrate: String,
    pub burn_subtitles: bool,
    pub subtitle_style: Option<SubtitleBurnStyle>,
}

#[derive(Debug, Clone)]
pub struct StitchJobResult {
    pub index: u32,
    pub audio_path: PathBuf,
    pub image_path: PathBuf,
    pub subtitle_path: Option<PathBuf>,
    pub output_path: PathBuf,
}

pub fn stitch_assets(options: &StitchOptions) -> Result<Vec<StitchJobResult>> {
    if options.frame_rate <= 0.0 {
        bail!("Frame rate must be greater than zero");
    }

    let audio_map = collect_indexed_files(&options.audio_dir, &AUDIO_EXTENSIONS)?;
    let image_map = collect_indexed_files(&options.image_dir, &IMAGE_EXTENSIONS)?;
    let subtitle_map = if let Some(dir) = &options.subtitle_dir {
        collect_indexed_files(dir, &SUBTITLE_EXTENSIONS)?
    } else {
        BTreeMap::new()
    };

    if audio_map.is_empty() {
        bail!(
            "No audio files (.wav/.mp3/.m4a/.aac/.flac/.ogg) were found in '{}'.",
            options.audio_dir.display()
        );
    }

    let mut paired_indices = Vec::new();
    for (index, audio_path) in &audio_map {
        if let Some(image_path) = image_map.get(index) {
            let subtitle_path = subtitle_map.get(index).cloned();
            paired_indices.push((
                *index,
                audio_path.clone(),
                image_path.clone(),
                subtitle_path,
            ));
        }
    }

    if paired_indices.is_empty() {
        bail!(
            "No matching audio/image pairs found between '{}' and '{}'.",
            options.audio_dir.display(),
            options.image_dir.display()
        );
    }

    fs::create_dir_all(&options.output_dir).with_context(|| {
        format!(
            "Failed to create output directory '{}'.",
            options.output_dir.display()
        )
    })?;

    let mut results = Vec::new();
    for (index, audio_path, image_path, subtitle_path) in paired_indices {
        let output_path = options.output_dir.join(format!("scene_{:03}.mp4", index));
        let subtitle_ref = subtitle_path.as_ref().map(|buf| buf.as_path());
        run_ffmpeg_job(
            &audio_path,
            &image_path,
            subtitle_ref,
            &output_path,
            options,
        )?;

        results.push(StitchJobResult {
            index,
            audio_path,
            image_path,
            subtitle_path,
            output_path,
        });
    }

    Ok(results)
}

fn collect_indexed_files(dir: &Path, allowed_exts: &[&str]) -> Result<BTreeMap<u32, PathBuf>> {
    if !dir.exists() || !dir.is_dir() {
        bail!("Directory '{}' does not exist", dir.display());
    }

    let mut entries: Vec<_> = fs::read_dir(dir)
        .with_context(|| format!("Failed to read directory '{}'.", dir.display()))?
        .filter_map(|entry| entry.ok())
        .filter(|entry| entry.file_type().map(|ft| ft.is_file()).unwrap_or(false))
        .collect();

    entries.sort_by(|a, b| {
        compare(
            &a.file_name().to_string_lossy(),
            &b.file_name().to_string_lossy(),
        )
    });

    let mut map = BTreeMap::new();
    for entry in entries {
        let path = entry.path();
        if let Some(ext) = path.extension().and_then(|ext| ext.to_str()) {
            if !allowed_exts
                .iter()
                .any(|allowed| ext.eq_ignore_ascii_case(allowed))
            {
                continue;
            }
        } else {
            continue;
        }

        if let Some(index) = extract_index(&path) {
            map.insert(index, path);
        }
    }

    Ok(map)
}

fn extract_index(path: &Path) -> Option<u32> {
    let stem = path.file_stem()?.to_string_lossy();
    let mut digits = String::new();
    for ch in stem.chars().rev() {
        if ch.is_ascii_digit() {
            digits.insert(0, ch);
        } else if !digits.is_empty() {
            break;
        }
    }

    if digits.is_empty() {
        None
    } else {
        digits.parse().ok()
    }
}

fn run_ffmpeg_job(
    audio_path: &Path,
    image_path: &Path,
    subtitle_path: Option<&Path>,
    output_path: &Path,
    options: &StitchOptions,
) -> Result<()> {
    let mut last_error: Option<anyhow::Error> = None;
    for (encoder, pix_fmt, label, is_fallback) in encoder_candidates(options.codec) {
        match run_ffmpeg_with_encoder(
            encoder,
            pix_fmt,
            label,
            audio_path,
            image_path,
            subtitle_path,
            output_path,
            options,
        ) {
            Ok(()) => {
                if is_fallback {
                    println!(
                        "Falling back to encoder '{}' for audio '{}'",
                        label,
                        audio_path.display()
                    );
                }
                return Ok(());
            }
            Err(err) => {
                println!(
                    "ffmpeg attempt with '{}' failed for '{}' và '{}': {}",
                    label,
                    audio_path.display(),
                    image_path.display(),
                    err
                );
                last_error = Some(err);
            }
        }
    }

    Err(last_error.unwrap_or_else(|| {
        anyhow!(
            "ffmpeg failed for audio '{}' và hình '{}'.",
            audio_path.display(),
            image_path.display()
        )
    }))
}

fn encoder_candidates(codec: VideoCodec) -> Vec<(&'static str, &'static str, &'static str, bool)> {
    match codec {
        VideoCodec::H264 => vec![
            ("h264_videotoolbox", "yuv420p", "h264_videotoolbox", false),
            ("libx264", "yuv420p", "libx264", true),
        ],
        VideoCodec::Hevc => vec![
            ("hevc_videotoolbox", "yuv420p", "hevc_videotoolbox", false),
            ("libx265", "yuv420p", "libx265", true),
        ],
    }
}

fn run_ffmpeg_with_encoder(
    encoder: &str,
    pix_fmt: &str,
    label: &str,
    audio_path: &Path,
    image_path: &Path,
    subtitle_path: Option<&Path>,
    output_path: &Path,
    options: &StitchOptions,
) -> Result<()> {
    let frame_rate_str = options.frame_rate.to_string();
    let audio_bitrate = options.audio_bitrate.as_str();

    let mut filters = vec![format!("fps={}", options.frame_rate)];
    if options.burn_subtitles {
        if let Some(sub) = subtitle_path {
            let mut filter = format!("subtitles={}", escape_subtitle_path(sub));
            if let Some(style) = options
                .subtitle_style
                .as_ref()
                .and_then(|style| build_force_style(style))
            {
                filter.push_str(":force_style=");
                filter.push_str(&escape_force_style(&style));
            }
            filters.push(filter);
        }
    }

    let mut cmd = Command::new("ffmpeg");
    cmd.arg("-y")
        .arg("-hide_banner")
        .arg("-loglevel")
        .arg("error")
        .arg("-loop")
        .arg("1")
        .arg("-framerate")
        .arg(&frame_rate_str)
        .arg("-i")
        .arg(image_path)
        .arg("-i")
        .arg(audio_path);

    if let Some(sub) = subtitle_path {
        cmd.arg("-i").arg(sub);
    }

    cmd.arg("-vf")
        .arg(filters.join(","))
        .arg("-c:v")
        .arg(encoder)
        .arg("-pix_fmt")
        .arg(pix_fmt)
        .arg("-b:v")
        .arg("6000k")
        .arg("-c:a")
        .arg("aac")
        .arg("-b:a")
        .arg(audio_bitrate)
        .arg("-shortest")
        .arg("-movflags")
        .arg("faststart")
        .arg("-map")
        .arg("0:v:0")
        .arg("-map")
        .arg("1:a:0");

    if !options.burn_subtitles && subtitle_path.is_some() {
        cmd.arg("-map").arg("2:s:0");
        cmd.arg("-c:s").arg("mov_text");
    }

    cmd.arg(output_path);

    let output = cmd
        .output()
        .with_context(|| format!("Failed to spawn ffmpeg ({})", label))?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(anyhow!(
            "Encoder '{}' failed with status {:?}\n{}",
            label,
            output.status.code(),
            stderr.trim()
        ));
    }

    Ok(())
}

const AUDIO_EXTENSIONS: [&str; 6] = ["wav", "mp3", "m4a", "aac", "flac", "ogg"];
const IMAGE_EXTENSIONS: [&str; 6] = ["jpg", "jpeg", "png", "webp", "bmp", "tiff"];
const SUBTITLE_EXTENSIONS: [&str; 3] = ["srt", "ass", "vtt"];

fn escape_subtitle_path(path: &Path) -> String {
    let raw = path.to_string_lossy();
    let escaped = raw
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("\"", "\\\"")
        .replace("'", "\\'")
        .replace(",", "\\,");
    format!("'{}'", escaped)
}

fn build_force_style(style: &SubtitleBurnStyle) -> Option<String> {
    let mut entries = Vec::new();

    if let Some(font) = style.font_name.as_ref().map(|s| s.trim()).filter(|s| !s.is_empty()) {
        entries.push(format!("FontName={}", escape_force_style_value(font)));
    }

    if let Some(size) = style.font_size.filter(|value| *value > 0.0) {
        entries.push(format!("FontSize={}", size));
    }

    if let Some(color) = style
        .primary_color
        .as_ref()
        .and_then(|hex| ass_color_from_hex(hex))
    {
        entries.push(format!("PrimaryColour={}", color));
    }

    if let Some(color) = style
        .outline_color
        .as_ref()
        .and_then(|hex| ass_color_from_hex(hex))
    {
        entries.push(format!("OutlineColour={}", color));
    }

    if let Some(outline) = style.outline_width.filter(|value| *value >= 0.0) {
        entries.push(format!("Outline={}", outline));
    }

    if let Some(spacing) = style.letter_spacing.filter(|value| *value != 0.0) {
        entries.push(format!("Spacing={}", spacing));
    }

    if entries.is_empty() {
        None
    } else {
        Some(entries.join(","))
    }
}

fn escape_force_style(value: &str) -> String {
    let escaped = value
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace(":", "\\:");
    format!("'{}'", escaped)
}

fn escape_force_style_value(value: &str) -> String {
    value
        .replace(",", "\\,")
        .replace(":", "\\:")
        .replace("'", "\\'")
}

fn ass_color_from_hex(input: &str) -> Option<String> {
    let trimmed = input.trim().trim_start_matches('#');
    if trimmed.len() != 6 {
        return None;
    }

    let r = u8::from_str_radix(&trimmed[0..2], 16).ok()?;
    let g = u8::from_str_radix(&trimmed[2..4], 16).ok()?;
    let b = u8::from_str_radix(&trimmed[4..6], 16).ok()?;

    Some(format!("&H00{:02X}{:02X}{:02X}&", b, g, r))
}
