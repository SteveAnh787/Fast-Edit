#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use anyhow::Result;
use render_core::{
    batch_rename_for_kind, capture_system_status, generate_subtitles_batch, render_project,
    stitch_assets, AssetKind, Project, StitchOptions, SubtitleBurnStyle, SubtitleGenerationOptions,
    VideoCodec,
};
use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};
use std::fs;
use std::io::copy;
use std::path::{Path, PathBuf};
use tauri::{AppHandle, Emitter, Manager};
use tauri_plugin_dialog::{DialogExt, FilePath};

#[derive(Debug, Deserialize)]
struct RenameOptions {
    prefix: Option<String>,
    separator: Option<String>,
    start_index: Option<usize>,
    pad_width: Option<usize>,
    lowercase_extension: Option<bool>,
}

#[derive(Debug, Serialize)]
struct RenameReport {
    original: String,
    renamed: String,
    changed: bool,
}

#[derive(Debug, Serialize)]
struct SubtitleBatchReportItem {
    audio_path: String,
    subtitle_path: Option<String>,
    preview_lines: Vec<String>,
}

#[derive(Debug, Serialize)]
struct WhisperModelInfo {
    id: String,
    name: String,
    path: String,
    size_bytes: u64,
    recommended: bool,
    available: bool,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct SubtitleBatchArgs {
    audio_directory: String,
    subtitle_directory: Option<String>,
    model_id: String,
    language: Option<String>,
    translate_to_english: bool,
    threads: Option<usize>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct StitchArgs {
    audio_directory: String,
    image_directory: String,
    subtitle_directory: Option<String>,
    output_directory: String,
    frame_rate: f32,
    codec: Option<String>,
    audio_bitrate: Option<String>,
    burn_subtitles: bool,
    subtitle_style: Option<SubtitleStyleArgs>,
}

#[derive(Debug, Serialize)]
struct StitchReportItem {
    index: u32,
    audio_path: String,
    image_path: String,
    subtitle_path: Option<String>,
    output_path: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct SubtitleStyleArgs {
    font_name: Option<String>,
    font_size: Option<f32>,
    primary_color: Option<String>,
    outline_color: Option<String>,
    outline_width: Option<f32>,
    letter_spacing: Option<f32>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct PickDialogFilter {
    name: String,
    extensions: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct PickDialogOptions {
    kind: PickDialogKind,
    title: Option<String>,
    default_path: Option<String>,
    file_name: Option<String>,
    filters: Option<Vec<PickDialogFilter>>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "lowercase")]
enum PickDialogKind {
    Directory,
    File,
    Save,
}

struct ModelSpec {
    id: &'static str,
    display_name: &'static str,
    filename: &'static str,
    url: &'static str,
    recommended: bool,
    size_bytes: u64,
}

const MODEL_CATALOG: &[ModelSpec] = &[
    ModelSpec {
        id: "ggml-tiny-en",
        display_name: "Whisper Tiny (English)",
        filename: "ggml-tiny.en.bin",
        url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin",
        recommended: false,
        size_bytes: 75_000_000,
    },
    ModelSpec {
        id: "ggml-base",
        display_name: "Whisper Base",
        filename: "ggml-base.bin",
        url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
        recommended: true,
        size_bytes: 142_000_000,
    },
    ModelSpec {
        id: "ggml-small-en",
        display_name: "Whisper Small (English)",
        filename: "ggml-small.en.bin",
        url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin",
        recommended: false,
        size_bytes: 465_000_000,
    },
    ModelSpec {
        id: "ggml-medium",
        display_name: "Whisper Medium",
        filename: "ggml-medium.bin",
        url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
        recommended: false,
        size_bytes: 1_550_000_000,
    },
];

#[tauri::command]
fn command_render(project: Project, app_handle: AppHandle) -> Result<(), String> {
    tauri::async_runtime::spawn(async move {
        let result = render_project(&project);
        if let Err(error) = result {
            let _ = app_handle.emit("render-error", error.to_string());
        } else {
            let _ = app_handle.emit("render-finished", project.metadata.title);
        }
    });

    Ok(())
}

#[tauri::command]
fn command_system_status() -> Result<String, String> {
    let status = capture_system_status();
    serde_json::to_string(&status).map_err(|err| err.to_string())
}

fn parse_asset_kind(kind: &str) -> Result<AssetKind, String> {
    match kind.to_lowercase().as_str() {
        "audio" => Ok(AssetKind::Audio),
        "image" => Ok(AssetKind::Image),
        other => Err(format!(
            "Unsupported asset kind '{other}'. Use 'audio' or 'image'."
        )),
    }
}

fn models_directory(app_handle: &AppHandle) -> Result<PathBuf, anyhow::Error> {
    let base = app_handle
        .path()
        .app_local_data_dir()
        .map_err(|err| anyhow::anyhow!("Failed to resolve application data directory: {err}"))?;
    let dir = base.join("models");
    fs::create_dir_all(&dir)?;
    Ok(dir)
}

fn ensure_model_available(spec: &ModelSpec, dir: &Path) -> Result<PathBuf, anyhow::Error> {
    let destination = dir.join(spec.filename);
    if destination.exists() {
        return Ok(destination);
    }

    let tmp_destination = destination.with_extension("download");
    if tmp_destination.exists() {
        fs::remove_file(&tmp_destination)?;
    }

    println!("Downloading Whisper model '{}'...", spec.display_name);
    let client = Client::builder().build()?;
    let mut response = client.get(spec.url).send()?;
    if !response.status().is_success() {
        return Err(anyhow::anyhow!(
            "Failed to download model '{}' (status: {})",
            spec.display_name,
            response.status()
        ));
    }

    let mut file = fs::File::create(&tmp_destination)?;
    copy(&mut response, &mut file)?;
    drop(file);

    fs::rename(tmp_destination, &destination)?;
    println!(
        "Downloaded model '{}' to {}",
        spec.display_name,
        destination.display()
    );

    Ok(destination)
}

fn resolve_model_path(models_dir: &Path, model_id: &str) -> Result<PathBuf, anyhow::Error> {
    if let Some(spec) = MODEL_CATALOG.iter().find(|spec| spec.id == model_id) {
        return ensure_model_available(spec, models_dir);
    }

    let provided = PathBuf::from(model_id);
    if provided.exists() {
        Ok(provided)
    } else {
        Err(anyhow::anyhow!(
            "Model identifier '{}' not recognised and file not found.",
            model_id
        ))
    }
}

#[tauri::command]
async fn command_batch_rename(
    directory: String,
    kind: String,
    options: Option<RenameOptions>,
) -> Result<Vec<RenameReport>, String> {
    let directory_path = PathBuf::from(directory);
    let asset_kind = parse_asset_kind(&kind)?;

    let reports = tauri::async_runtime::spawn_blocking(
        move || -> Result<Vec<RenameReport>, anyhow::Error> {
            let mut pattern = asset_kind.default_pattern();

            if let Some(opts) = options {
                if let Some(prefix) = opts.prefix {
                    pattern = pattern.with_prefix(prefix);
                }
                if let Some(separator) = opts.separator {
                    pattern = pattern.with_separator(separator);
                }
                if let Some(start_index) = opts.start_index {
                    pattern = pattern.with_start_index(start_index);
                }
                if let Some(pad_width) = opts.pad_width {
                    pattern = pattern.with_pad_width(pad_width);
                }
                if let Some(lowercase) = opts.lowercase_extension {
                    pattern = pattern.lowercase_extension(lowercase);
                }
            }

            let outcomes = batch_rename_for_kind(directory_path, asset_kind, Some(pattern))?;
            let reports = outcomes
                .into_iter()
                .map(|outcome| RenameReport {
                    original: outcome.original.display().to_string(),
                    renamed: outcome.renamed.display().to_string(),
                    changed: outcome.changed,
                })
                .collect();
            Ok(reports)
        },
    )
    .await
    .map_err(|err| err.to_string())?
    .map_err(|err| err.to_string())?;

    Ok(reports)
}

#[tauri::command]
async fn command_pick_path(
    app_handle: AppHandle,
    options: PickDialogOptions,
) -> Result<Option<String>, String> {
    tauri::async_runtime::spawn_blocking(move || -> Result<Option<String>, anyhow::Error> {
        let mut builder = app_handle.dialog().file();

        if let Some(dir) = options
            .default_path
            .as_deref()
            .filter(|path| !path.is_empty())
        {
            builder = builder.set_directory(dir);
        }

        if let Some(file_name) = options.file_name.as_deref().filter(|name| !name.is_empty()) {
            builder = builder.set_file_name(file_name);
        }

        if let Some(title) = options.title.as_deref().filter(|value| !value.is_empty()) {
            builder = builder.set_title(title);
        }

        if let Some(filters) = options.filters.as_ref() {
            for filter in filters {
                let extensions: Vec<&str> =
                    filter.extensions.iter().map(|ext| ext.as_str()).collect();
                builder = builder.add_filter(&filter.name, &extensions);
            }
        }

        fn resolve_path(path: FilePath) -> Result<String, anyhow::Error> {
            Ok(path.into_path()?.display().to_string())
        }

        let selection = match options.kind {
            PickDialogKind::Directory => builder
                .blocking_pick_folder()
                .map(resolve_path)
                .transpose()?,
            PickDialogKind::File => builder.blocking_pick_file().map(resolve_path).transpose()?,
            PickDialogKind::Save => builder.blocking_save_file().map(resolve_path).transpose()?,
        };

        Ok(selection)
    })
    .await
    .map_err(|err| err.to_string())?
    .map_err(|err| err.to_string())
}

#[tauri::command]
async fn command_list_models(app_handle: AppHandle) -> Result<Vec<WhisperModelInfo>, String> {
    tauri::async_runtime::spawn_blocking(move || -> Result<Vec<WhisperModelInfo>, anyhow::Error> {
        let models_dir = models_directory(&app_handle)?;
        let mut infos = Vec::new();

        for spec in MODEL_CATALOG {
            let path = models_dir.join(spec.filename);
            let metadata = fs::metadata(&path).ok();
            let available = metadata.is_some();
            let size_bytes = metadata.map(|meta| meta.len()).unwrap_or(spec.size_bytes);

            infos.push(WhisperModelInfo {
                id: spec.id.to_string(),
                name: spec.display_name.to_string(),
                path: path.display().to_string(),
                size_bytes,
                recommended: spec.recommended,
                available,
            });
        }

        infos.sort_by(|a, b| match (a.recommended, b.recommended) {
            (true, false) => std::cmp::Ordering::Less,
            (false, true) => std::cmp::Ordering::Greater,
            _ => a.name.cmp(&b.name),
        });

        Ok(infos)
    })
    .await
    .map_err(|err| err.to_string())?
    .map_err(|err| err.to_string())
}

#[tauri::command]
async fn command_generate_subtitles_batch(
    app_handle: AppHandle,
    args: SubtitleBatchArgs,
) -> Result<Vec<SubtitleBatchReportItem>, String> {
    tauri::async_runtime::spawn_blocking(
        move || -> Result<Vec<SubtitleBatchReportItem>, anyhow::Error> {
            let SubtitleBatchArgs {
                audio_directory,
                subtitle_directory,
                model_id,
                language,
                translate_to_english,
                threads,
            } = args;

            if audio_directory.trim().is_empty() {
                return Err(anyhow::anyhow!("Audio directory is required."));
            }

            let audio_dir = PathBuf::from(&audio_directory);
            if !audio_dir.exists() {
                return Err(anyhow::anyhow!(
                    "Audio directory '{}' does not exist.",
                    audio_directory
                ));
            }

            let models_dir = models_directory(&app_handle)?;
            let model_path = resolve_model_path(&models_dir, &model_id)?;

            let subtitle_dir = subtitle_directory
                .filter(|value| !value.trim().is_empty())
                .map(PathBuf::from)
                .unwrap_or_else(|| audio_dir.join("subtitles"));

            let mut options = SubtitleGenerationOptions::new(model_path);
            if let Some(lang) = language.filter(|value| !value.trim().is_empty()) {
                options = options.with_language(lang);
            }
            options = options.translate_to_english(translate_to_english);
            if let Some(count) = threads {
                options = options.with_threads(count);
            }

            let items = generate_subtitles_batch(audio_dir, &options, &subtitle_dir)?;

            Ok(items
                .into_iter()
                .map(|item| SubtitleBatchReportItem {
                    audio_path: item.audio_path.display().to_string(),
                    subtitle_path: item
                        .subtitle_path
                        .as_ref()
                        .map(|path| path.display().to_string()),
                    preview_lines: item.preview_lines,
                })
                .collect())
        },
    )
    .await
    .map_err(|err| err.to_string())?
    .map_err(|err| err.to_string())
}

#[tauri::command]
async fn command_stitch_assets(args: StitchArgs) -> Result<Vec<StitchReportItem>, String> {
    tauri::async_runtime::spawn_blocking(move || -> Result<Vec<StitchReportItem>, anyhow::Error> {
        if args.audio_directory.trim().is_empty() {
            return Err(anyhow::anyhow!("Audio directory is required."));
        }
        if args.image_directory.trim().is_empty() {
            return Err(anyhow::anyhow!("Image directory is required."));
        }
        if args.output_directory.trim().is_empty() {
            return Err(anyhow::anyhow!("Output directory is required."));
        }
        if args.frame_rate <= 0.0 {
            return Err(anyhow::anyhow!("Frame rate must be greater than zero."));
        }

        let codec = match args.codec.as_deref() {
            Some("hevc") => VideoCodec::Hevc,
            _ => VideoCodec::H264,
        };

        let subtitle_style = args.subtitle_style.map(|style| SubtitleBurnStyle {
            font_name: style.font_name,
            font_size: style.font_size,
            primary_color: style.primary_color,
            outline_color: style.outline_color,
            outline_width: style.outline_width,
            letter_spacing: style.letter_spacing,
        });

        let options = StitchOptions {
            audio_dir: PathBuf::from(&args.audio_directory),
            image_dir: PathBuf::from(&args.image_directory),
            subtitle_dir: args
                .subtitle_directory
                .as_ref()
                .filter(|value| !value.trim().is_empty())
                .map(PathBuf::from),
            output_dir: PathBuf::from(&args.output_directory),
            frame_rate: args.frame_rate,
            codec,
            audio_bitrate: args
                .audio_bitrate
                .filter(|value| !value.trim().is_empty())
                .unwrap_or_else(|| "192k".to_string()),
            burn_subtitles: args.burn_subtitles,
            subtitle_style,
        };

        let results = stitch_assets(&options)?;
        Ok(results
            .into_iter()
            .map(|job| StitchReportItem {
                index: job.index,
                audio_path: job.audio_path.display().to_string(),
                image_path: job.image_path.display().to_string(),
                subtitle_path: job.subtitle_path.as_ref().map(|s| s.display().to_string()),
                output_path: job.output_path.display().to_string(),
            })
            .collect())
    })
    .await
    .map_err(|err| err.to_string())?
    .map_err(|err| err.to_string())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            command_render,
            command_system_status,
            command_pick_path,
            command_list_models,
            command_batch_rename,
            command_generate_subtitles_batch,
            command_stitch_assets
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
