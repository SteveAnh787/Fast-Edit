use render_core::{batch_rename_for_kind, AssetKind, RenamePattern};
use std::fs;
use std::path::PathBuf;

fn main() -> anyhow::Result<()> {
    let temp_dir = tempfile::tempdir()?;
    let audio_dir = temp_dir.path().join("audio");
    fs::create_dir(&audio_dir)?;

    let filenames = ["clipB.wav", "clipA.wav", "clipC.wav"];
    for name in filenames {
        fs::write(audio_dir.join(name), b"example")?;
    }

    println!("Before:");
    print_dir_contents(&audio_dir)?;

    let outcomes = batch_rename_for_kind(&audio_dir, AssetKind::Audio, None)?;

    println!("\nAfter:");
    for outcome in &outcomes {
        println!(
            "{} -> {}",
            outcome.original.file_name().unwrap().to_string_lossy(),
            outcome.renamed.file_name().unwrap().to_string_lossy()
        );
    }

    print_dir_contents(&audio_dir)?;

    println!("\nCustom pattern:");
    let custom_pattern = RenamePattern::new("scene")
        .with_separator("_")
        .with_start_index(5)
        .with_pad_width(2);

    let outcomes = batch_rename_for_kind(&audio_dir, AssetKind::Image, Some(custom_pattern))?;
    for outcome in outcomes {
        println!("{}", outcome.renamed.file_name().unwrap().to_string_lossy());
    }

    Ok(())
}

fn print_dir_contents(dir: &PathBuf) -> anyhow::Result<()> {
    let mut entries: Vec<_> = fs::read_dir(dir)?
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.file_name().to_string_lossy().into_owned())
        .collect();
    entries.sort();
    for name in entries {
        println!(" - {}", name);
    }
    Ok(())
}
