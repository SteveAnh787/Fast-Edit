"""
Subtitle Generator - Xử lý sinh phụ đề tự động bằng Whisper AI
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import requests
import tempfile

@dataclass
class SubtitleResult:
    """Kết quả sinh phụ đề cho một file audio"""
    audio_path: str
    subtitle_path: Optional[str]
    preview_lines: List[str]
    success: bool
    error: Optional[str] = None

class WhisperModel:
    """Thông tin về model Whisper"""
    def __init__(self, model_id: str, name: str, filename: str, url: str, size_bytes: int, recommended: bool = False):
        self.id = model_id
        self.name = name
        self.filename = filename
        self.url = url
        self.size_bytes = size_bytes
        self.recommended = recommended
        self.available = False

class SubtitleGenerator:
    """Class xử lý sinh phụ đề tự động"""
    
    # Whisper models catalog
    MODELS = [
        WhisperModel(
            "ggml-tiny-en",
            "Whisper Tiny (English)",
            "ggml-tiny.en.bin",
            "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin",
            75_000_000
        ),
        WhisperModel(
            "ggml-base",
            "Whisper Base",
            "ggml-base.bin", 
            "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
            142_000_000,
            recommended=True
        ),
        WhisperModel(
            "ggml-small-en",
            "Whisper Small (English)",
            "ggml-small.en.bin",
            "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin",
            465_000_000
        ),
        WhisperModel(
            "ggml-medium",
            "Whisper Medium",
            "ggml-medium.bin",
            "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
            1_550_000_000
        )
    ]
    
    def __init__(self):
        self.models_dir = self._get_models_directory()
        self._check_model_availability()
        
    def _get_models_directory(self) -> Path:
        """Lấy thư mục lưu trữ models"""
        # Use user's home directory for model storage
        models_dir = Path.home() / ".vibe_render_tool" / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        return models_dir
        
    def _check_model_availability(self):
        """Kiểm tra models nào đã được tải về"""
        for model in self.MODELS:
            model_path = self.models_dir / model.filename
            model.available = model_path.exists()
            
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Lấy danh sách models có sẵn"""
        models_info = []
        for model in self.MODELS:
            models_info.append({
                "id": model.id,
                "name": model.name,
                "path": str(self.models_dir / model.filename),
                "size_bytes": model.size_bytes,
                "recommended": model.recommended,
                "available": model.available
            })
        return models_info
        
    def download_model(self, model_id: str, progress_callback=None) -> bool:
        """
        Tải về model Whisper
        
        Args:
            model_id: ID của model
            progress_callback: Callback để báo cáo tiến độ
            
        Returns:
            True nếu thành công
        """
        model = next((m for m in self.MODELS if m.id == model_id), None)
        if not model:
            return False
            
        model_path = self.models_dir / model.filename
        if model_path.exists():
            model.available = True
            return True
            
        try:
            # Download with progress tracking
            response = requests.get(model.url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
            
            model.available = True
            return True
            
        except Exception as e:
            print(f"Lỗi tải model {model.name}: {e}")
            if model_path.exists():
                model_path.unlink()
            return False
            
    def generate_subtitle(
        self,
        audio_path: str,
        output_path: str,
        model_id: str = "ggml-base",
        language: Optional[str] = None,
        translate_to_english: bool = False,
        threads: Optional[int] = None
    ) -> SubtitleResult:
        """
        Sinh phụ đề cho một file audio
        
        Args:
            audio_path: Đường dẫn file audio
            output_path: Đường dẫn file phụ đề đầu ra
            model_id: ID model Whisper
            language: Ngôn ngữ (vi, en, ...)
            translate_to_english: Có dịch sang tiếng Anh không
            threads: Số threads
            
        Returns:
            SubtitleResult
        """
        try:
            audio_file = Path(audio_path)
            if not audio_file.exists():
                return SubtitleResult(
                    audio_path, None, [], False, 
                    f"File audio không tồn tại: {audio_path}"
                )
            
            # Check if model is available
            model = next((m for m in self.MODELS if m.id == model_id), None)
            if not model:
                return SubtitleResult(
                    audio_path, None, [], False,
                    f"Model không tồn tại: {model_id}"
                )
                
            if not model.available:
                # Try to download model
                if not self.download_model(model_id):
                    return SubtitleResult(
                        audio_path, None, [], False,
                        f"Không thể tải model: {model.name}"
                    )
            
            # For now, create a mock subtitle file as placeholder
            # TODO: Integrate with actual Whisper implementation
            subtitle_content = self._generate_mock_subtitle(audio_file.stem)
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(subtitle_content)
            
            # Extract preview lines
            preview_lines = subtitle_content.split('\n')[:6]  # First 6 lines
            preview_lines = [line.strip() for line in preview_lines if line.strip()]
            
            return SubtitleResult(
                audio_path,
                str(output_file),
                preview_lines,
                True
            )
            
        except Exception as e:
            return SubtitleResult(
                audio_path, None, [], False,
                f"Lỗi sinh phụ đề: {str(e)}"
            )
            
    def generate_subtitles_batch(
        self,
        audio_directory: str,
        subtitle_directory: str,
        model_id: str = "ggml-base",
        language: Optional[str] = None,
        translate_to_english: bool = False,
        threads: Optional[int] = None
    ) -> List[SubtitleResult]:
        """
        Sinh phụ đề hàng loạt cho thư mục audio
        
        Args:
            audio_directory: Thư mục chứa file audio
            subtitle_directory: Thư mục đầu ra cho phụ đề
            model_id: ID model Whisper
            language: Ngôn ngữ
            translate_to_english: Có dịch sang tiếng Anh không
            threads: Số threads
            
        Returns:
            List SubtitleResult
        """
        results = []
        
        try:
            audio_dir = Path(audio_directory)
            if not audio_dir.exists():
                return [SubtitleResult("", None, [], False, f"Thư mục audio không tồn tại: {audio_directory}")]
            
            subtitle_dir = Path(subtitle_directory)
            subtitle_dir.mkdir(parents=True, exist_ok=True)
            
            # Find audio files
            audio_extensions = {'.wav', '.mp3', '.m4a', '.aac', '.flac', '.ogg'}
            audio_files = []
            
            for file_path in audio_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                    audio_files.append(file_path)
            
            # Sort files
            audio_files.sort(key=lambda x: x.name.lower())
            
            # Process each audio file
            for audio_file in audio_files:
                subtitle_filename = audio_file.stem + '.srt'
                subtitle_path = subtitle_dir / subtitle_filename
                
                result = self.generate_subtitle(
                    str(audio_file),
                    str(subtitle_path),
                    model_id,
                    language,
                    translate_to_english,
                    threads
                )
                
                results.append(result)
                
        except Exception as e:
            results.append(SubtitleResult("", None, [], False, f"Lỗi xử lý batch: {str(e)}"))
            
        return results
        
    def _generate_mock_subtitle(self, filename: str) -> str:
        """Tạo file phụ đề mẫu (placeholder cho Whisper thật)"""
        return f"""1
00:00:00,000 --> 00:00:03,000
Phụ đề được tạo từ {filename}

2
00:00:03,000 --> 00:00:06,000
Đây là nội dung mẫu cho demo

3
00:00:06,000 --> 00:00:09,000
Whisper AI sẽ được tích hợp sau này

4
00:00:09,000 --> 00:00:12,000
Chất lượng phụ đề sẽ rất cao và chính xác
"""