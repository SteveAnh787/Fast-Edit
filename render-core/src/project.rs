use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Project {
    pub metadata: Metadata,
    pub output: OutputSettings,
    pub scenes: Vec<Scene>,
    pub subtitle_style: SubtitleStyle,
    pub logo: Option<OverlayAsset>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Metadata {
    pub title: String,
    pub author: Option<String>,
    pub created_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutputSettings {
    pub resolution: Resolution,
    pub frame_rate: f32,
    pub format: OutputFormat,
    pub bitrate: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Resolution {
    pub width: u32,
    pub height: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OutputFormat {
    H264,
    H265,
    ProRes,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Scene {
    pub id: String,
    pub duration_secs: f32,
    pub media: MediaAsset,
    pub audio: Option<AudioAsset>,
    pub subtitle: Option<SubtitleTrack>,
    pub transitions: Vec<Transition>,
    pub effects: Vec<Effect>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MediaAsset {
    Image { path: String },
    Video { path: String },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AudioAsset {
    pub path: String,
    pub gain_db: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubtitleTrack {
    pub path: String,
    pub offset_secs: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubtitleStyle {
    pub font_family: String,
    pub font_size: f32,
    pub color: Color,
    pub outline: Option<Outline>,
    pub background: Option<Background>,
    pub alignment: SubtitleAlignment,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SubtitleAlignment {
    Bottom,
    Middle,
    Top,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Outline {
    pub color: Color,
    pub width: f32,
    pub opacity: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Background {
    pub color: Color,
    pub opacity: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OverlayAsset {
    pub path: String,
    pub position: Anchor,
    pub scale: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Anchor {
    TopLeft,
    TopRight,
    BottomLeft,
    BottomRight,
    Center,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transition {
    pub kind: TransitionKind,
    pub duration_secs: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TransitionKind {
    Dissolve,
    HardCut,
    Slide,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Effect {
    Zoom { start_scale: f32, end_scale: f32 },
    KenBurns { pan_x: f32, pan_y: f32, zoom: f32 },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Color {
    pub r: f32,
    pub g: f32,
    pub b: f32,
    pub a: f32,
}

impl Default for SubtitleStyle {
    fn default() -> Self {
        Self {
            font_family: "Arial".to_string(),
            font_size: 48.0,
            color: Color::white(),
            outline: Some(Outline {
                color: Color::black(),
                width: 2.0,
                opacity: 1.0,
            }),
            background: None,
            alignment: SubtitleAlignment::Bottom,
        }
    }
}

impl Color {
    pub fn white() -> Self {
        Self {
            r: 1.0,
            g: 1.0,
            b: 1.0,
            a: 1.0,
        }
    }

    pub fn black() -> Self {
        Self {
            r: 0.0,
            g: 0.0,
            b: 0.0,
            a: 1.0,
        }
    }
}
