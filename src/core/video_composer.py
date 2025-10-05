"""
Video Composer - Xử lý ghép video và render với subtitle styling
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import json

@dataclass
class RenderResult:
    """Kết quả render một video"""
    index: int
    audio_path: str
    image_path: str
    subtitle_path: Optional[str]
    output_path: str
    success: bool
    error: Optional[str] = None

@dataclass
class SubtitleStyle:
    """Cấu hình style cho subtitle"""
    font_name: str = "Arial"
    font_size: int = 48
    primary_color: str = "#FFFFFF"
    outline_color: str = "#000000"
    outline_width: float = 2.0
    letter_spacing: float = 0.0

class VideoComposer:
    """Class xử lý ghép video và render"""
    
    def __init__(self):
        self._check_dependencies()
        
    def _check_dependencies(self):
        """Kiểm tra các dependencies cần thiết"""
        # Check if ffmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
            self.ffmpeg_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.ffmpeg_available = False
            
        try:
            subprocess.run(['ffprobe', '-version'], 
                         capture_output=True, check=True)
            self.ffprobe_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.ffprobe_available = False
            
    def get_system_status(self) -> Dict[str, Any]:
        """Lấy thông tin trạng thái hệ thống"""
        return {
            "ffmpeg_available": self.ffmpeg_available,
            "ffprobe_available": self.ffprobe_available,
            "ready_to_render": self.ffmpeg_available and self.ffprobe_available
        }
        
    def stitch_assets(
        self,
        audio_directory: str,
        image_directory: str,
        output_directory: str,
        subtitle_directory: Optional[str] = None,
        frame_rate: float = 30.0,
        video_codec: str = "h264",
        audio_bitrate: str = "192k",
        burn_subtitles: bool = False,
        subtitle_style: Optional[SubtitleStyle] = None
    ) -> List[RenderResult]:
        """
        Ghép audio, image và subtitle thành video
        
        Args:
            audio_directory: Thư mục chứa file audio
            image_directory: Thư mục chứa file image  
            output_directory: Thư mục đầu ra
            subtitle_directory: Thư mục chứa file subtitle (optional)
            frame_rate: Frame rate của video
            video_codec: Video codec (h264, hevc)
            audio_bitrate: Audio bitrate
            burn_subtitles: Có burn subtitle vào video không
            subtitle_style: Style cho subtitle
            
        Returns:
            List RenderResult
        """
        results = []
        
        try:
            # Validate directories
            audio_dir = Path(audio_directory)
            image_dir = Path(image_directory)
            output_dir = Path(output_directory)
            
            if not audio_dir.exists():
                return [RenderResult(0, "", "", None, "", False, 
                                   f"Thư mục audio không tồn tại: {audio_directory}")]
                                   
            if not image_dir.exists():
                return [RenderResult(0, "", "", None, "", False,
                                   f"Thư mục image không tồn tại: {image_directory}")]
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            subtitle_dir = None
            if subtitle_directory and subtitle_directory.strip():
                subtitle_dir = Path(subtitle_directory)
                if not subtitle_dir.exists():
                    subtitle_dir = None
            
            # Find matching assets
            audio_files = self._find_audio_files(audio_dir)
            image_files = self._find_image_files(image_dir)
            
            if not audio_files:
                return [RenderResult(0, "", "", None, "", False, "Không tìm thấy file audio")]
                
            if not image_files:
                return [RenderResult(0, "", "", None, "", False, "Không tìm thấy file image")]
            
            # Sort files
            audio_files.sort(key=lambda x: x.name.lower())
            image_files.sort(key=lambda x: x.name.lower())
            
            # Match assets by index
            asset_pairs = self._match_assets(audio_files, image_files, subtitle_dir)
            
            # Process each pair
            for index, (audio_file, image_file, subtitle_file) in enumerate(asset_pairs, 1):
                output_filename = f"output_{str(index).zfill(3)}.mp4"
                output_path = output_dir / output_filename
                
                result = self._render_single_video(
                    audio_file,
                    image_file,
                    output_path,
                    subtitle_file,
                    frame_rate,
                    video_codec,
                    audio_bitrate,
                    burn_subtitles,
                    subtitle_style,
                    index
                )
                
                results.append(result)
                
        except Exception as e:
            results.append(RenderResult(0, "", "", None, "", False, f"Lỗi xử lý: {str(e)}"))
            
        return results
        
    def _find_audio_files(self, directory: Path) -> List[Path]:
        """Tìm các file audio trong thư mục"""
        audio_extensions = {'.wav', '.mp3', '.m4a', '.aac', '.flac', '.ogg'}
        files = []
        
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                files.append(file_path)
                
        return files
        
    def _find_image_files(self, directory: Path) -> List[Path]:
        """Tìm các file image trong thư mục"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp'}
        files = []
        
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                files.append(file_path)
                
        return files
        
    def _match_assets(
        self, 
        audio_files: List[Path], 
        image_files: List[Path], 
        subtitle_dir: Optional[Path]
    ) -> List[Tuple[Path, Path, Optional[Path]]]:
        """Ghép các assets theo thứ tự"""
        pairs = []
        
        # Match by index (use shorter list as limit)
        max_pairs = min(len(audio_files), len(image_files))
        
        for i in range(max_pairs):
            audio_file = audio_files[i]
            image_file = image_files[i]
            
            # Try to find matching subtitle file
            subtitle_file = None
            if subtitle_dir:
                # Try exact match first
                subtitle_name = audio_file.stem + '.srt'
                subtitle_path = subtitle_dir / subtitle_name
                
                if subtitle_path.exists():
                    subtitle_file = subtitle_path
                else:
                    # Try index-based match
                    subtitle_files = list(subtitle_dir.glob('*.srt'))
                    if i < len(subtitle_files):
                        subtitle_files.sort(key=lambda x: x.name.lower())
                        subtitle_file = subtitle_files[i]
            
            pairs.append((audio_file, image_file, subtitle_file))
            
        return pairs
        
    def _render_single_video(
        self,
        audio_file: Path,
        image_file: Path,
        output_path: Path,
        subtitle_file: Optional[Path],
        frame_rate: float,
        video_codec: str,
        audio_bitrate: str,
        burn_subtitles: bool,
        subtitle_style: Optional[SubtitleStyle],
        index: int
    ) -> RenderResult:
        """Render một video từ audio + image + subtitle"""
        try:
            if not self.ffmpeg_available:
                return RenderResult(
                    index, str(audio_file), str(image_file), 
                    str(subtitle_file) if subtitle_file else None,
                    str(output_path), False,
                    "FFmpeg không khả dụng. Vui lòng cài đặt FFmpeg."
                )
            
            # Get audio duration
            duration = self._get_audio_duration(audio_file)
            if duration <= 0:
                return RenderResult(
                    index, str(audio_file), str(image_file),
                    str(subtitle_file) if subtitle_file else None,
                    str(output_path), False,
                    f"Không thể đọc thời lượng audio: {audio_file.name}"
                )
            
            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(
                audio_file, image_file, output_path, subtitle_file,
                duration, frame_rate, video_codec, audio_bitrate,
                burn_subtitles, subtitle_style
            )
            
            # For demo purposes, create a mock output file
            # TODO: Replace with actual FFmpeg execution
            self._create_mock_video(output_path, duration)
            
            return RenderResult(
                index, str(audio_file), str(image_file),
                str(subtitle_file) if subtitle_file else None,
                str(output_path), True
            )
            
        except Exception as e:
            return RenderResult(
                index, str(audio_file), str(image_file),
                str(subtitle_file) if subtitle_file else None,
                str(output_path), False,
                f"Lỗi render: {str(e)}"
            )
            
    def _get_audio_duration(self, audio_file: Path) -> float:
        """Lấy thời lượng của file audio"""
        try:
            if not self.ffprobe_available:
                return 10.0  # Default duration for demo
                
            # TODO: Use actual ffprobe to get duration
            # For now, return mock duration
            return 15.0  # Mock 15 seconds
            
        except Exception:
            return 10.0
            
    def _build_ffmpeg_command(
        self,
        audio_file: Path,
        image_file: Path,
        output_path: Path,
        subtitle_file: Optional[Path],
        duration: float,
        frame_rate: float,
        video_codec: str,
        audio_bitrate: str,
        burn_subtitles: bool,
        subtitle_style: Optional[SubtitleStyle]
    ) -> List[str]:
        """Build FFmpeg command"""
        cmd = [
            'ffmpeg', '-y',  # Overwrite output
            '-loop', '1',    # Loop image
            '-i', str(image_file),  # Input image
            '-i', str(audio_file),  # Input audio
            '-t', str(duration),    # Duration
            '-r', str(frame_rate),  # Frame rate
        ]
        
        # Video codec settings
        if video_codec.lower() == 'hevc':
            cmd.extend(['-c:v', 'libx265'])
        else:
            cmd.extend(['-c:v', 'libx264'])
            
        # Audio settings
        cmd.extend([
            '-c:a', 'aac',
            '-b:a', audio_bitrate,
        ])
        
        # Subtitle handling
        if subtitle_file and burn_subtitles and subtitle_style:
            # Build subtitle filter
            subtitle_filter = self._build_subtitle_filter(subtitle_file, subtitle_style)
            cmd.extend(['-vf', subtitle_filter])
        elif subtitle_file and not burn_subtitles:
            # Soft subtitle
            cmd.extend(['-i', str(subtitle_file), '-c:s', 'mov_text'])
            
        # Output
        cmd.append(str(output_path))
        
        return cmd
        
    def _build_subtitle_filter(self, subtitle_file: Path, style: SubtitleStyle) -> str:
        """Build FFmpeg subtitle filter string"""
        # Escape special characters in path
        subtitle_path = str(subtitle_file).replace(':', '\\:').replace('\\', '/')
        
        filter_parts = [
            f"subtitles='{subtitle_path}'",
            f"force_style='FontName={style.font_name}",
            f"FontSize={style.font_size}",
            f"PrimaryColour={self._hex_to_bgr(style.primary_color)}",
            f"OutlineColour={self._hex_to_bgr(style.outline_color)}",
            f"Outline={style.outline_width}",
            f"Spacing={style.letter_spacing}'"
        ]
        
        return ":".join(filter_parts)
        
    def _hex_to_bgr(self, hex_color: str) -> str:
        """Convert hex color to BGR format for FFmpeg"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            return "&H00FFFFFF"  # Default white
            
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # FFmpeg uses BGR format
        return f"&H00{b:02X}{g:02X}{r:02X}"
        
    def _create_mock_video(self, output_path: Path, duration: float):
        """Tạo file video mẫu (placeholder)"""
        # Create a simple text file as placeholder
        # In real implementation, this would be actual video
        with open(output_path, 'w') as f:
            f.write(f"Mock video file - Duration: {duration}s\n")
            f.write(f"Created: {output_path.name}\n")
            f.write("This would be actual MP4 video in production version.")
            
    def get_supported_codecs(self) -> List[Dict[str, str]]:
        """Lấy danh sách codec được hỗ trợ"""
        return [
            {"id": "h264", "name": "H.264 (VideoToolbox)", "description": "Tương thích cao, kích thước vừa phải"},
            {"id": "hevc", "name": "HEVC H.265 (VideoToolbox)", "description": "Nén tốt hơn, kích thước nhỏ hơn"}
        ]