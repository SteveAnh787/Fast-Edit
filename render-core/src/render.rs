use anyhow::{bail, Result};
use tracing::info;

use crate::{project::Project, timeline::TimelineComposition};

/// TODO: replace with actual AVFoundation/Metal pipeline.
pub fn encode_project(_project: &Project, timeline: TimelineComposition) -> Result<()> {
    if timeline.scenes.is_empty() {
        bail!("No scenes provided");
    }

    info!(
        scene_count = timeline.scenes.len(),
        "Pretending to render project"
    );
    // In the real implementation this will:
    // 1. Allocate Metal textures for each scene.
    // 2. Configure AVAssetWriter + VTCompressionSession for hardware encode.
    // 3. Stream frames and audio buffers into the encoder.
    Ok(())
}
