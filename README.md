# Vibe Render Tool - Python Version

High-performance desktop tool for batch-generating subtitle-rich video content using Python with PySide6 UI and FFmpeg backend.

## Goals
- GPU-accelerated rendering via FFmpeg for maximum export speed
- Flexible scene management, subtitle styling, logo overlays, and transitions  
- Cross-platform desktop UI built with PySide6 + Python backend
- Simple, maintainable codebase with single language (Python)
- Project configuration and batch processing capabilities

## Project Layout
- `main.py` - Application entry point
- `requirements.txt` - Python dependencies
- `src/ui/` - PySide6 user interface components
- `src/core/` - Core business logic (batch rename, subtitle generation, video composition)
- `src/utils/` - Utility functions and helpers

## Features
### Tab 1: Tự động hoá
- **Batch Rename**: Rename audio/image files with custom patterns
- **Subtitle Generation**: Auto-generate subtitles using Whisper AI models

### Tab 2: Ghép & render  
- **Video Composition**: Stitch audio + image + subtitles into videos
- **Subtitle Styling**: Real-time preview with font, size, color, outline customization
- **Format Support**: H.264/HEVC codecs with configurable settings

## Development Setup
1. **Install Python 3.9+** and ensure pip is available
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Install FFmpeg**: Required for video processing
   - macOS: `brew install ffmpeg`
   - Windows: Download from https://ffmpeg.org/
   - Linux: `sudo apt install ffmpeg`
4. **Run application**: `python main.py`

## Dependencies
- **PySide6**: Modern Qt-based GUI framework
- **OpenAI Whisper**: AI-powered speech recognition for subtitles
- **FFmpeg-python**: Video processing and rendering
- **Pillow**: Image processing capabilities
- **Requests**: HTTP client for model downloads

## Technology Stack
- **Frontend**: PySide6 (Qt6 for Python)
- **Backend**: Pure Python with core libraries
- **Video Processing**: FFmpeg via subprocess calls
- **AI Models**: Whisper for subtitle generation
- **Styling**: Qt CSS for professional dark theme

## Architecture Benefits
- ✅ **Single Language**: Python only, easier to maintain
- ✅ **Rapid Development**: Faster iteration vs Rust+React  
- ✅ **Rich Ecosystem**: Access to AI/ML libraries
- ✅ **Cross Platform**: Native look on Windows/macOS/Linux
- ✅ **Professional UI**: PySide6 provides native desktop experience

## Next Steps
- Integrate real Whisper implementation for subtitle generation
- Add actual FFmpeg video rendering (currently mock implementation)
- Implement progress tracking for long-running operations
- Add video preview capabilities
- Expand codec and format support
