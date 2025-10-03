use anyhow::Result;
use tracing::debug;

use crate::project::{Project, Scene};

/// Placeholder representation of an AVFoundation composition graph.
#[derive(Debug, Clone)]
pub struct TimelineComposition {
    pub scenes: Vec<SceneComposition>,
}

#[derive(Debug, Clone)]
pub struct SceneComposition {
    pub scene_id: String,
    pub duration_secs: f32,
}

/// Convert the high-level project into a Metal/AVFoundation-ready composition.
pub fn build_timeline(project: &Project) -> Result<TimelineComposition> {
    debug!(
        scene_count = project.scenes.len(),
        "Building timeline composition"
    );

    let scenes = project
        .scenes
        .iter()
        .map(|scene| SceneComposition {
            scene_id: scene.id.clone(),
            duration_secs: scene.duration_secs,
        })
        .collect();

    Ok(TimelineComposition { scenes })
}
