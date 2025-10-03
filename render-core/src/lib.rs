#![allow(unused)]

pub mod monitor;
pub mod organize;
pub mod project;
pub mod render;
pub mod stitch;
pub mod subtitle;
pub mod timeline;

use anyhow::Result;

pub use organize::{batch_rename, batch_rename_for_kind, AssetKind, RenameOutcome, RenamePattern};
/// Re-exports for consumers.
pub use project::{Project, Scene};
pub use stitch::{stitch_assets, StitchJobResult, StitchOptions, VideoCodec};
pub use subtitle::{
    generate_subtitles, generate_subtitles_batch, SubtitleBatchItem, SubtitleGenerationOptions,
    SubtitleScript, SubtitleSegment,
};

/// High-level entry point for kicking off a render job.
pub fn render_project(project: &Project) -> Result<()> {
    tracing::info!(title = %project.metadata.title, "Starting render job");
    let composition = timeline::build_timeline(project)?;
    render::encode_project(project, composition)?;
    Ok(())
}

/// Snapshot the current system load to drive UI telemetry.
pub fn capture_system_status() -> monitor::SystemStatus {
    monitor::SystemStatus::gather()
}
