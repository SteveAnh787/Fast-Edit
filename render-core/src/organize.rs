use anyhow::{bail, Context, Result};
use natord::compare;
use serde::Serialize;
use std::ffi::OsStr;
use std::fs;
use std::path::{Path, PathBuf};

/// Represents the kind of asset being processed.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AssetKind {
    Audio,
    Image,
}

impl AssetKind {
    /// Default naming pattern for a given asset kind.
    pub fn default_pattern(self) -> RenamePattern {
        match self {
            AssetKind::Audio => RenamePattern::new("audio")
                .with_separator("_")
                .with_pad_width(3)
                .lowercase_extension(true),
            AssetKind::Image => RenamePattern::new("image")
                .with_separator("_")
                .with_pad_width(3)
                .lowercase_extension(true),
        }
    }
}

/// Configuration describing how files should be renamed.
#[derive(Debug, Clone)]
pub struct RenamePattern {
    prefix: String,
    separator: String,
    start_index: usize,
    pad_width: Option<usize>,
    lowercase_extension: bool,
}

impl RenamePattern {
    /// Create a new pattern with the supplied prefix.
    pub fn new(prefix: impl Into<String>) -> Self {
        Self {
            prefix: prefix.into(),
            separator: " ".into(),
            start_index: 1,
            pad_width: None,
            lowercase_extension: false,
        }
    }

    /// Override the separator between prefix and index.
    pub fn with_separator(mut self, separator: impl Into<String>) -> Self {
        self.separator = separator.into();
        self
    }

    /// Override the prefix component.
    pub fn with_prefix(mut self, prefix: impl Into<String>) -> Self {
        self.prefix = prefix.into();
        self
    }

    /// Set the starting index (defaults to 1).
    pub fn with_start_index(mut self, start_index: usize) -> Self {
        self.start_index = start_index.max(1);
        self
    }

    /// Force padding width. When omitted the width is inferred from file count.
    pub fn with_pad_width(mut self, pad_width: usize) -> Self {
        self.pad_width = Some(pad_width.max(1));
        self
    }

    /// Control whether extensions should be coerced to lowercase.
    pub fn lowercase_extension(mut self, enabled: bool) -> Self {
        self.lowercase_extension = enabled;
        self
    }

    fn pad_width(&self, item_count: usize) -> usize {
        if let Some(width) = self.pad_width {
            return width;
        }

        let last_index = self.start_index + item_count.saturating_sub(1);
        digit_count(last_index)
    }

    fn build_file_name(&self, index: usize, extension: Option<&OsStr>, width: usize) -> String {
        let stem = format!(
            "{}{}{}",
            self.prefix,
            if self.separator.is_empty() {
                ""
            } else {
                &self.separator
            },
            format_number(index, width)
        );

        match extension.and_then(|ext| ext.to_str()) {
            Some(ext) if !ext.is_empty() => {
                let ext = if self.lowercase_extension {
                    ext.to_ascii_lowercase()
                } else {
                    ext.to_string()
                };
                format!("{}.{}", stem, ext)
            }
            _ => stem,
        }
    }
}

/// Result of a rename operation for a single asset.
#[derive(Debug, Clone, Serialize)]
pub struct RenameOutcome {
    pub original: PathBuf,
    pub renamed: PathBuf,
    pub changed: bool,
}

/// Rename every file directly under `directory` according to the supplied pattern.
///
/// Returns a list of outcomes reflecting the rename operation.
pub fn batch_rename(
    directory: impl AsRef<Path>,
    pattern: &RenamePattern,
) -> Result<Vec<RenameOutcome>> {
    let directory = directory.as_ref();
    if !directory.exists() || !directory.is_dir() {
        bail!("Directory '{}' does not exist", directory.display());
    }

    let mut entries: Vec<_> = fs::read_dir(directory)
        .with_context(|| format!("Failed to read directory '{}'.", directory.display()))?
        .filter_map(|entry| entry.ok())
        .filter(|entry| entry.file_type().map(|ft| ft.is_file()).unwrap_or(false))
        .collect();

    if entries.is_empty() {
        return Ok(Vec::new());
    }

    entries.sort_by(|a, b| {
        let a_name = a.file_name();
        let b_name = b.file_name();
        compare(&a_name.to_string_lossy(), &b_name.to_string_lossy())
    });

    let width = pattern.pad_width(entries.len());
    let mut index = pattern.start_index;
    let mut outcomes = Vec::with_capacity(entries.len());

    for entry in entries {
        let original_path = entry.path();
        let extension = original_path.extension();
        let target_name = pattern.build_file_name(index, extension, width);
        let target_path = directory.join(&target_name);

        let changed = if target_path == original_path {
            false
        } else {
            if target_path.exists() {
                bail!(
                    "Cannot rename '{}' to '{}' because the destination already exists.",
                    original_path.display(),
                    target_path.display()
                );
            }

            fs::rename(&original_path, &target_path).with_context(|| {
                format!(
                    "Failed to rename '{}' to '{}'.",
                    original_path.display(),
                    target_path.display()
                )
            })?;
            true
        };

        outcomes.push(RenameOutcome {
            original: original_path,
            renamed: target_path,
            changed,
        });

        index += 1;
    }

    Ok(outcomes)
}

/// Convenience helper that applies a default pattern derived from [`AssetKind`].
pub fn batch_rename_for_kind(
    directory: impl AsRef<Path>,
    kind: AssetKind,
    overrides: Option<RenamePattern>,
) -> Result<Vec<RenameOutcome>> {
    let pattern = overrides.unwrap_or_else(|| kind.default_pattern());
    batch_rename(directory, &pattern)
}

fn digit_count(mut value: usize) -> usize {
    if value == 0 {
        return 1;
    }
    let mut digits = 0;
    while value > 0 {
        digits += 1;
        value /= 10;
    }
    digits
}

fn format_number(index: usize, width: usize) -> String {
    if width == 0 {
        return index.to_string();
    }
    format!("{:0width$}", index, width = width)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::tempdir;

    fn create_file(path: &Path) {
        let mut file = fs::File::create(path).expect("create file");
        writeln!(file, "test").expect("write file");
    }

    #[test]
    fn renames_with_default_pattern() {
        let dir = tempdir().unwrap();
        let audio_dir = dir.path();

        create_file(&audio_dir.join("clipB.wav"));
        create_file(&audio_dir.join("clipA.wav"));
        create_file(&audio_dir.join("clipC.wav"));

        let results = batch_rename_for_kind(audio_dir, AssetKind::Audio, None).unwrap();
        let names: Vec<_> = results
            .iter()
            .map(|res| {
                res.renamed
                    .file_name()
                    .unwrap()
                    .to_string_lossy()
                    .into_owned()
            })
            .collect();

        assert_eq!(
            names,
            vec!["audio_001.wav", "audio_002.wav", "audio_003.wav"]
        );
    }

    #[test]
    fn honours_custom_separator() {
        let dir = tempdir().unwrap();
        let image_dir = dir.path();

        create_file(&image_dir.join("b.png"));
        create_file(&image_dir.join("a.png"));

        let pattern = RenamePattern::new("image")
            .with_separator(" ")
            .with_start_index(10)
            .with_pad_width(2);

        let results = batch_rename(image_dir, &pattern).unwrap();
        let names: Vec<_> = results
            .iter()
            .map(|res| {
                res.renamed
                    .file_name()
                    .unwrap()
                    .to_string_lossy()
                    .into_owned()
            })
            .collect();

        assert_eq!(names, vec!["image 10.png", "image 11.png"]);
    }

    #[test]
    fn skips_when_name_unchanged() {
        let dir = tempdir().unwrap();
        let path = dir.path();

        create_file(&path.join("audio_001.wav"));

        let pattern = RenamePattern::new("audio")
            .with_separator("_")
            .with_pad_width(3);
        let results = batch_rename(path, &pattern).unwrap();

        assert_eq!(results[0].changed, false);
        assert_eq!(
            results[0]
                .renamed
                .file_name()
                .unwrap()
                .to_string_lossy()
                .as_ref(),
            "audio_001.wav"
        );
    }
}
