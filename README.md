# Vibe Render Tool

High-performance desktop tool for batch-generating subtitle-rich video content using a native Rust/Metal/AVFoundation pipeline with a Tauri-based UI.

## Goals
- GPU-accelerated rendering via Metal + VideoToolbox for maximum export speed.
- Flexible scene management, subtitle styling, logo overlays, and transitions.
- Cross-platform-ready UI (macOS primary) built with Tauri + React, communicating with Rust backend commands.
- Project configuration stored as JSON for portability and automation.

## Project Layout
- `Cargo.toml` (workspace)
- `render-core/` – Rust crate handling project parsing, timeline assembly, Metal shader coordination, and VideoToolbox export.
- `app/` – Tauri desktop application (React front end) providing scene editor, previews, and render control.
- `docs/` – Architecture notes, render pipeline diagrams, and future specifications.

## Development Setup
1. Install Rust toolchain (`rustup`), Node.js (>=18), pnpm (preferred) or npm, and ffmpeg (for reference testing).
2. On macOS, ensure Command Line Tools are installed: `xcode-select --install`.
3. Clone repository, run `pnpm install` inside `app/`, and `cargo build` at workspace root.

## Next Steps
- Flesh out `render-core` with data structures for scenes, subtitles, and effect graphs.
- Provide native bindings to AVFoundation/Metal.
- Implement Tauri commands to trigger render jobs and stream progress updates.
