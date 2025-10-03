# Architecture Draft

## Rendering Pipeline Overview
1. Load project JSON describing scenes, media assets, subtitle styles, and transitions.
2. Build an AVFoundation timeline (`AVMutableComposition`) representing clips, audio tracks, and overlays.
3. Generate per-scene Metal render passes for image transformations (zoom, dissolve) and subtitle rasterization.
4. Encode final output via VideoToolbox (`VTCompressionSession`) targeting H.264/H.265 with hardware acceleration.
5. Stream progress updates back to the UI through Tauri events.

## Modules
- `render_core::project` – data structures for projects/scenes/effects.
- `render_core::timeline` – conversion from project model to AVFoundation compositions.
- `render_core::render` – orchestrates Metal pipelines and encoding.
- `render_core::monitor` – system telemetry (CPU/GPU/RAM) for UI display.

## UI Flow (Tauri + React)
- Scene list panel with thumbnails, audio/subtitle indicators.
- Subtitle style editor with live preview (Canvas/WebGL).
- Render controls: output settings, progress bar, logs.

## Milestones
- [ ] Define project JSON schema and parser.
- [ ] Implement minimal timeline assembly for image+audio scenes.
- [ ] Expose Tauri command to trigger render and report progress.
- [ ] Build React components for scene list and subtitle editor.
