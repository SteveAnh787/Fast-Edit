"""
Batch Rename - Xử lý đổi tên hàng loạt file audio/image
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class RenameResult:
    """Kết quả đổi tên một file"""
    original_path: str
    new_path: str
    success: bool
    error: Optional[str] = None

class BatchRenamer:
    """Class xử lý đổi tên hàng loạt"""
    
    # Supported file extensions
    AUDIO_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.aac', '.flac', '.ogg'}
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp'}
    
    def __init__(self):
        pass
        
    def rename_files(
        self,
        directory: str,
        asset_type: str = "audio",
        prefix: str = "",
        start_index: int = 1,
        pad_width: int = 3,
        separator: str = "_",
        lowercase_extension: bool = True
    ) -> List[RenameResult]:
        """
        Đổi tên hàng loạt các file trong thư mục
        
        Args:
            directory: Đường dẫn thư mục
            asset_type: Loại file ("audio" hoặc "image")
            prefix: Tiền tố cho tên file mới
            start_index: Số bắt đầu
            pad_width: Độ rộng padding cho số
            separator: Ký tự phân cách
            lowercase_extension: Có viết thường extension không
            
        Returns:
            List các RenameResult
        """
        results = []
        
        try:
            directory_path = Path(directory)
            if not directory_path.exists():
                return [RenameResult("", "", False, f"Thư mục không tồn tại: {directory}")]
                
            # Get supported extensions
            if asset_type.lower() == "audio":
                extensions = self.AUDIO_EXTENSIONS
                default_prefix = prefix or "audio"
            elif asset_type.lower() == "image":
                extensions = self.IMAGE_EXTENSIONS
                default_prefix = prefix or "image"
            else:
                return [RenameResult("", "", False, f"Loại file không hỗ trợ: {asset_type}")]
            
            # Find matching files
            files = []
            for file_path in directory_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in extensions:
                    files.append(file_path)
            
            # Sort files by name
            files.sort(key=lambda x: x.name.lower())
            
            # Rename files
            current_index = start_index
            for file_path in files:
                try:
                    # Build new filename
                    extension = file_path.suffix
                    if lowercase_extension:
                        extension = extension.lower()
                    
                    padded_number = str(current_index).zfill(pad_width)
                    new_filename = f"{default_prefix}{separator}{padded_number}{extension}"
                    new_path = file_path.parent / new_filename
                    
                    # Check if rename is needed
                    if file_path.name == new_filename:
                        results.append(RenameResult(
                            str(file_path),
                            str(new_path),
                            True
                        ))
                    else:
                        # Perform rename
                        if new_path.exists():
                            results.append(RenameResult(
                                str(file_path),
                                str(new_path),
                                False,
                                f"File đích đã tồn tại: {new_filename}"
                            ))
                        else:
                            file_path.rename(new_path)
                            results.append(RenameResult(
                                str(file_path),
                                str(new_path),
                                True
                            ))
                    
                    current_index += 1
                    
                except Exception as e:
                    results.append(RenameResult(
                        str(file_path),
                        "",
                        False,
                        f"Lỗi đổi tên: {str(e)}"
                    ))
                    
        except Exception as e:
            results.append(RenameResult("", "", False, f"Lỗi xử lý thư mục: {str(e)}"))
            
        return results
        
    def get_file_count(self, directory: str, asset_type: str = "audio") -> Dict[str, Any]:
        """
        Đếm số file trong thư mục
        
        Args:
            directory: Đường dẫn thư mục
            asset_type: Loại file
            
        Returns:
            Dict chứa thông tin về số file
        """
        try:
            directory_path = Path(directory)
            if not directory_path.exists():
                return {"total": 0, "error": "Thư mục không tồn tại"}
                
            if asset_type.lower() == "audio":
                extensions = self.AUDIO_EXTENSIONS
            elif asset_type.lower() == "image":
                extensions = self.IMAGE_EXTENSIONS
            else:
                return {"total": 0, "error": "Loại file không hỗ trợ"}
            
            count = 0
            for file_path in directory_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in extensions:
                    count += 1
                    
            return {"total": count, "error": None}
            
        except Exception as e:
            return {"total": 0, "error": str(e)}