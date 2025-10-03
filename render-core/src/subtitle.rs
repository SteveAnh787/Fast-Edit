use anyhow::{anyhow, bail, Context, Result};
use hound::{SampleFormat, WavReader};
use natord::compare;
use serde::Serialize;
use std::ffi::OsStr;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Duration;
use tempfile::TempDir;
use whisper_rs::{
    convert_integer_to_float_audio, FullParams, SamplingStrategy, WhisperContext,
    WhisperContextParameters,
};

const TARGET_SAMPLE_RATE: u32 = 16_000;

/// Options controlling subtitle generation through Whisper.
#[derive(Debug, Clone)]
pub struct SubtitleGenerationOptions {
    pub model_path: PathBuf,
    pub language: Option<String>,
    pub translate_to_english: bool,
    pub threads: Option<usize>,
    pub output_path: Option<PathBuf>,
}

impl SubtitleGenerationOptions {
    pub fn new(model_path: impl Into<PathBuf>) -> Self {
        Self {
            model_path: model_path.into(),
            language: None,
            translate_to_english: false,
            threads: None,
            output_path: None,
        }
    }

    pub fn with_language(mut self, language: impl Into<String>) -> Self {
        self.language = Some(language.into());
        self
    }

    pub fn translate_to_english(mut self, translate: bool) -> Self {
        self.translate_to_english = translate;
        self
    }

    pub fn with_threads(mut self, threads: usize) -> Self {
        self.threads = Some(threads.max(1));
        self
    }

    pub fn write_to(mut self, output_path: impl Into<PathBuf>) -> Self {
        self.output_path = Some(output_path.into());
        self
    }
}

/// Represents a single subtitle segment.
#[derive(Debug, Clone, Serialize)]
pub struct SubtitleSegment {
    pub index: usize,
    pub start: Duration,
    pub end: Duration,
    pub text: String,
}

/// Aggregated subtitle payload.
#[derive(Debug, Clone, Serialize)]
pub struct SubtitleScript {
    pub segments: Vec<SubtitleSegment>,
}

impl SubtitleScript {
    /// Serialise the subtitle script into SRT format.
    pub fn to_srt(&self) -> String {
        self.segments
            .iter()
            .map(|segment| {
                format!(
                    "{}\n{} --> {}\n{}\n\n",
                    segment.index,
                    format_timestamp(segment.start),
                    format_timestamp(segment.end),
                    segment.text
                )
            })
            .collect()
    }

    /// Persist the subtitle script as an SRT file.
    pub fn write_srt(&self, path: impl AsRef<Path>) -> Result<()> {
        fs::write(path.as_ref(), self.to_srt()).with_context(|| {
            format!(
                "Failed to write subtitle file to '{}'.",
                path.as_ref().display()
            )
        })
    }
}

/// Represents the output of a batch subtitle generation run.
#[derive(Debug, Clone, Serialize)]
pub struct SubtitleBatchItem {
    pub audio_path: PathBuf,
    pub subtitle_path: Option<PathBuf>,
    pub preview_lines: Vec<String>,
}

/// Execute a Whisper transcription to produce subtitle segments from an audio file.
pub fn generate_subtitles(
    audio_path: impl AsRef<Path>,
    options: &SubtitleGenerationOptions,
) -> Result<SubtitleScript> {
    whisper_rs::install_logging_hooks();

    let audio_path = audio_path.as_ref();
    let context = load_whisper_context(options)?;
    let script = run_transcription(&context, options, audio_path)?;

    if let Some(path) = &options.output_path {
        write_srt_and_preview(&script, path)?;
    }

    Ok(script)
}

/// Execute Whisper inference for every WAV file inside `audio_dir`, writing SRT files to
/// `output_dir`. Returns the list of generated subtitle assets.
pub fn generate_subtitles_batch(
    audio_dir: impl AsRef<Path>,
    options: &SubtitleGenerationOptions,
    output_dir: impl AsRef<Path>,
) -> Result<Vec<SubtitleBatchItem>> {
    whisper_rs::install_logging_hooks();

    let audio_dir = audio_dir.as_ref();
    if !audio_dir.exists() || !audio_dir.is_dir() {
        bail!("Audio directory '{}' does not exist", audio_dir.display());
    }

    let output_dir = output_dir.as_ref();
    fs::create_dir_all(output_dir).with_context(|| {
        format!(
            "Failed to create or access subtitle output directory '{}'.",
            output_dir.display()
        )
    })?;

    let mut entries: Vec<_> = fs::read_dir(audio_dir)
        .with_context(|| format!("Failed to read audio directory '{}'.", audio_dir.display()))?
        .filter_map(|entry| entry.ok())
        .filter(|entry| entry.file_type().map(|ft| ft.is_file()).unwrap_or(false))
        .collect();

    entries.sort_by(|a, b| {
        compare(
            &a.file_name().to_string_lossy(),
            &b.file_name().to_string_lossy(),
        )
    });

    let context = load_whisper_context(options)?;
    let mut results = Vec::new();

    for entry in entries {
        let audio_path = entry.path();
        if !is_supported_audio(&audio_path) {
            continue;
        }

        let stem = match audio_path.file_stem().and_then(|stem| stem.to_str()) {
            Some(stem) => stem,
            None => continue,
        };

        match prepare_audio_for_whisper(&audio_path) {
            Ok(prepared) => {
                let subtitle_path = output_dir.join(format!("{stem}.srt"));
                let script = run_transcription(&context, options, prepared.path())?;
                let preview_lines = write_srt_and_preview(&script, &subtitle_path)?;

                results.push(SubtitleBatchItem {
                    audio_path: audio_path.clone(),
                    subtitle_path: Some(subtitle_path),
                    preview_lines,
                });
                // `prepared` is dropped here, cleaning up any temp files.
            }
            Err(error) => {
                println!(
                    "Skipping '{}' because it could not be converted: {}",
                    audio_path.display(),
                    error
                );
                continue;
            }
        }
    }

    if results.is_empty() {
        bail!(
            "No supported audio files (wav/mp3/m4a/aac/flac/ogg) were found in '{}'.",
            audio_dir.display()
        );
    }

    Ok(results)
}

struct PreparedAudio {
    path: PathBuf,
    _temp_dir: Option<TempDir>,
}

impl PreparedAudio {
    fn borrowed(path: &Path) -> Self {
        Self {
            path: path.to_path_buf(),
            _temp_dir: None,
        }
    }

    fn converted(temp_dir: TempDir, path: PathBuf) -> Self {
        Self {
            path,
            _temp_dir: Some(temp_dir),
        }
    }

    fn path(&self) -> &Path {
        &self.path
    }
}

fn prepare_audio_for_whisper(original_path: &Path) -> Result<PreparedAudio> {
    if is_wav_16k(original_path)? {
        return Ok(PreparedAudio::borrowed(original_path));
    }

    let temp_dir = TempDir::new()?;
    let output_path = temp_dir.path().join(
        original_path
            .file_stem()
            .unwrap_or_else(|| OsStr::new("track"))
            .to_string_lossy()
            .to_string()
            + "_whisper.wav",
    );

    convert_audio_with_ffmpeg(original_path, &output_path)?;

    Ok(PreparedAudio::converted(temp_dir, output_path))
}

fn is_wav_16k(path: &Path) -> Result<bool> {
    if let Some(ext) = path.extension().and_then(|ext| ext.to_str()) {
        if !ext.eq_ignore_ascii_case("wav") {
            return Ok(false);
        }
    } else {
        return Ok(false);
    }

    let mut reader = WavReader::open(path)
        .with_context(|| format!("Failed to open audio file '{}'.", path.display()))?;
    let spec = reader.spec();

    Ok(spec.sample_rate == TARGET_SAMPLE_RATE
        && spec.channels == 1
        && ((spec.sample_format == SampleFormat::Int && spec.bits_per_sample == 16)
            || (spec.sample_format == SampleFormat::Float && spec.bits_per_sample == 32)))
}

fn convert_audio_with_ffmpeg(input: &Path, output: &Path) -> Result<()> {
    let status = Command::new("ffmpeg")
        .args([
            "-y",
            "-i",
            input
                .to_str()
                .ok_or_else(|| anyhow!("Audio path contains invalid UTF-8 characters."))?,
            "-ac",
            "1",
            "-ar",
            &TARGET_SAMPLE_RATE.to_string(),
            "-sample_fmt",
            "s16",
            output
                .to_str()
                .ok_or_else(|| anyhow!("Output path contains invalid UTF-8 characters."))?,
        ])
        .status()
        .context("Failed to spawn ffmpeg process")?;

    if !status.success() {
        bail!(
            "ffmpeg conversion for '{}' failed with status {:?}.",
            input.display(),
            status.code()
        );
    }

    Ok(())
}

fn is_supported_audio(path: &Path) -> bool {
    path.extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| {
            matches!(
                ext.to_ascii_lowercase().as_str(),
                "wav" | "mp3" | "m4a" | "aac" | "flac" | "ogg"
            )
        })
        .unwrap_or(false)
}
fn load_whisper_context(options: &SubtitleGenerationOptions) -> Result<WhisperContext> {
    let model_path = options
        .model_path
        .to_str()
        .ok_or_else(|| anyhow!("Model path contains invalid UTF-8 characters."))?;

    WhisperContext::new_with_params(model_path, WhisperContextParameters::default()).with_context(
        || {
            format!(
                "Failed to load Whisper model at '{}'.",
                options.model_path.display()
            )
        },
    )
}

fn run_transcription(
    context: &WhisperContext,
    options: &SubtitleGenerationOptions,
    audio_path: &Path,
) -> Result<SubtitleScript> {
    let samples = load_audio_mono(audio_path)?;

    let mut state = context
        .create_state()
        .context("Failed to create Whisper state.")?;

    let mut params = FullParams::new(SamplingStrategy::Greedy { best_of: 1 });
    params.set_n_threads(options.threads.unwrap_or_else(num_cpus::get) as i32);
    params.set_translate(options.translate_to_english);
    params.set_language(options.language.as_deref());
    params.set_print_special(false);
    params.set_print_progress(false);
    params.set_print_realtime(false);
    params.set_print_timestamps(false);
    params.set_token_timestamps(false);

    state
        .full(params, &samples)
        .context("Whisper inference failed.")?;

    let mut segments = Vec::new();
    for (idx, segment) in state.as_iter().enumerate() {
        let text = segment
            .to_str_lossy()
            .map_err(|err| anyhow!(err))?
            .trim()
            .to_string();

        if text.is_empty() {
            continue;
        }

        let start = centiseconds_to_duration(segment.start_timestamp());
        let mut end = centiseconds_to_duration(segment.end_timestamp());
        if end < start {
            end = start;
        }
        segments.push(SubtitleSegment {
            index: segments.len() + 1,
            start,
            end,
            text,
        });
    }

    Ok(SubtitleScript { segments })
}

fn write_srt_and_preview(script: &SubtitleScript, path: &Path) -> Result<Vec<String>> {
    let srt = script.to_srt();
    fs::write(path, srt.as_bytes())
        .with_context(|| format!("Failed to write subtitle file to '{}'.", path.display()))?;

    let preview_lines = srt
        .lines()
        .filter(|line| !line.trim().is_empty())
        .take(4)
        .map(|line| line.to_string())
        .collect();

    Ok(preview_lines)
}

fn load_audio_mono(path: &Path) -> Result<Vec<f32>> {
    let mut reader = WavReader::open(path)
        .with_context(|| format!("Failed to open audio file '{}'.", path.display()))?;
    let spec = reader.spec();

    if spec.sample_rate != TARGET_SAMPLE_RATE {
        bail!(
            "Expected {} Hz audio but found {} Hz. Please resample before transcription.",
            TARGET_SAMPLE_RATE,
            spec.sample_rate
        );
    }

    if spec.channels == 0 {
        bail!("Audio file reports zero channels.");
    }

    let channels = spec.channels as usize;

    match spec.sample_format {
        SampleFormat::Int => {
            if spec.bits_per_sample != 16 {
                bail!(
                    "Only 16-bit PCM WAV files are supported for integer samples (found {} bits).",
                    spec.bits_per_sample
                );
            }

            let raw: Vec<i16> = reader
                .samples::<i16>()
                .map(|sample| sample.with_context(|| "Invalid 16-bit PCM sample"))
                .collect::<Result<_, _>>()?;

            if raw.len() % channels != 0 {
                bail!("Unexpected sample count - audio data is not aligned to channels.");
            }

            let mut float_buffer = vec![0.0f32; raw.len()];
            convert_integer_to_float_audio(&raw, &mut float_buffer)
                .context("Failed to convert audio samples to floating point")?;

            Ok(downmix_to_mono(&float_buffer, channels))
        }
        SampleFormat::Float => {
            if spec.bits_per_sample != 32 {
                bail!(
                    "Only 32-bit float WAV files are supported for floating point samples (found {} bits).",
                    spec.bits_per_sample
                );
            }

            let raw: Vec<f32> = reader
                .samples::<f32>()
                .map(|sample| sample.with_context(|| "Invalid 32-bit float sample"))
                .collect::<Result<_, _>>()?;

            if raw.len() % channels != 0 {
                bail!("Unexpected sample count - audio data is not aligned to channels.");
            }

            Ok(downmix_to_mono(&raw, channels))
        }
    }
}

fn downmix_to_mono(samples: &[f32], channels: usize) -> Vec<f32> {
    match channels {
        1 => samples.to_vec(),
        2 => samples
            .chunks_exact(2)
            .map(|chunk| (chunk[0] + chunk[1]) * 0.5)
            .collect(),
        _ => samples
            .chunks(channels)
            .map(|chunk| chunk.iter().sum::<f32>() / channels as f32)
            .collect(),
    }
}

fn centiseconds_to_duration(cs: i64) -> Duration {
    if cs <= 0 {
        return Duration::from_millis(0);
    }
    Duration::from_millis((cs as u64) * 10)
}

fn format_timestamp(duration: Duration) -> String {
    let total_millis = duration.as_millis();
    let hours = total_millis / 3_600_000;
    let minutes = (total_millis % 3_600_000) / 60_000;
    let seconds = (total_millis % 60_000) / 1_000;
    let millis = total_millis % 1_000;

    format!("{:02}:{:02}:{:02},{:03}", hours, minutes, seconds, millis)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn format_timestamp_renders_correctly() {
        let duration = Duration::from_millis(3_726_045);
        assert_eq!(format_timestamp(duration), "01:02:06,045");
    }

    #[test]
    fn centiseconds_to_duration_clamps_negative() {
        let duration = centiseconds_to_duration(-50);
        assert_eq!(duration, Duration::from_millis(0));
    }
}
