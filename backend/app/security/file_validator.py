import magic
import logging
from typing import Optional, Tuple
from pathlib import Path
from PIL import Image
import io

logger = logging.getLogger(__name__)


class FileValidationError(Exception):
    pass


class FileValidator:
    ALLOWED_MIME_TYPES = {
        'application/pdf': ['.pdf'],
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/gif': ['.gif'],
        'video/mp4': ['.mp4'],
        'video/quicktime': ['.mov'],
        'application/zip': ['.zip'],
        'text/plain': ['.txt'],
        'application/json': ['.json'],
    }

    MAX_FILE_SIZE = 100 * 1024 * 1024
    MAX_IMAGE_DIMENSION = 10000
    MAX_VIDEO_DURATION = 3600

    DANGEROUS_EXTENSIONS = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr',
        '.vbs', '.js', '.jar', '.sh', '.php', '.asp',
        '.aspx', '.dll', '.so', '.dylib'
    ]

    def __init__(self):
        self.magic = magic.Magic(mime=True)

    def validate_file(
        self,
        file_data: bytes,
        filename: str,
        claimed_mime_type: Optional[str] = None
    ) -> Tuple[bool, str]:
        try:
            actual_mime_type = self.magic.from_buffer(file_data)

            if claimed_mime_type and actual_mime_type != claimed_mime_type:
                raise FileValidationError(
                    f"File type mismatch: claimed {claimed_mime_type}, actual {actual_mime_type}"
                )

            if actual_mime_type not in self.ALLOWED_MIME_TYPES:
                raise FileValidationError(f"File type not allowed: {actual_mime_type}")

            extension = Path(filename).suffix.lower()
            if extension in self.DANGEROUS_EXTENSIONS:
                raise FileValidationError(f"Dangerous file extension: {extension}")

            allowed_extensions = self.ALLOWED_MIME_TYPES[actual_mime_type]
            if extension not in allowed_extensions:
                raise FileValidationError(
                    f"Extension {extension} not valid for type {actual_mime_type}"
                )

            if len(file_data) > self.MAX_FILE_SIZE:
                raise FileValidationError(
                    f"File size {len(file_data)} exceeds maximum {self.MAX_FILE_SIZE}"
                )

            if actual_mime_type.startswith('image/'):
                self._validate_image(file_data, actual_mime_type)

            logger.info(f"File validation passed: {filename} ({actual_mime_type})")
            return True, actual_mime_type

        except FileValidationError as e:
            logger.warning(f"File validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"File validation error: {e}")
            raise FileValidationError(f"File validation error: {str(e)}")

    def _validate_image(self, file_data: bytes, mime_type: str):
        try:
            with Image.open(io.BytesIO(file_data)) as img:
                width, height = img.size

                if width > self.MAX_IMAGE_DIMENSION or height > self.MAX_IMAGE_DIMENSION:
                    raise FileValidationError(
                        f"Image dimensions {width}x{height} exceed maximum {self.MAX_IMAGE_DIMENSION}"
                    )

                if img.format.lower() not in ['jpeg', 'png', 'gif']:
                    raise FileValidationError(f"Invalid image format: {img.format}")

                img.verify()

        except FileValidationError:
            raise
        except Exception as e:
            raise FileValidationError(f"Invalid image file: {str(e)}")

    def strip_image_metadata(self, file_data: bytes) -> bytes:
        try:
            with Image.open(io.BytesIO(file_data)) as img:
                data_without_exif = img.convert('RGB')

                output = io.BytesIO()
                data_without_exif.save(output, format='JPEG', quality=95)
                return output.getvalue()

        except Exception as e:
            logger.error(f"Failed to strip image metadata: {e}")
            return file_data

    def strip_pdf_metadata(self, file_data: bytes) -> bytes:
        try:
            from PyPDF2 import PdfReader, PdfWriter

            reader = PdfReader(io.BytesIO(file_data))
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            writer.remove_images = False

            output = io.BytesIO()
            writer.write(output)
            return output.getvalue()

        except Exception as e:
            logger.warning(f"Failed to strip PDF metadata: {e}")
            return file_data

    def calculate_file_hash(self, file_data: bytes) -> str:
        import hashlib
        return hashlib.sha256(file_data).hexdigest()

    def scan_for_malicious_patterns(self, file_data: bytes) -> bool:
        malicious_patterns = [
            b'<script>',
            b'javascript:',
            b'<?php',
            b'<%',
            b'<%=',
        ]

        for pattern in malicious_patterns:
            if pattern in file_data:
                logger.warning(f"Malicious pattern detected: {pattern}")
                return True

        return False


file_validator = FileValidator()
