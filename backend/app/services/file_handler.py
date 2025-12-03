import os
import uuid
from pathlib import Path
from typing import List
from fastapi import UploadFile, HTTPException, status

class FileHandler:
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
        
    def validate_file(self, file: UploadFile) -> None:
        """Validate file extension"""
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_ext} not allowed. Allowed: {self.allowed_extensions}"
            )
    
    def save_file(self, file: UploadFile, subfolder: str = "cases") -> str:
        """Save uploaded file and return file path"""
        self.validate_file(file)
        
        # Create subfolder
        folder_path = self.upload_dir / subfolder
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = folder_path / unique_filename
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
            return str(file_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
    
    def save_multiple_files(self, files: List[UploadFile], subfolder: str = "cases") -> List[str]:
        """Save multiple files"""
        file_paths = []
        for file in files:
            file_path = self.save_file(file, subfolder)
            file_paths.append(file_path)
        return file_paths
