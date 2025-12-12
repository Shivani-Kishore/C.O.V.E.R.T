import re
import html
import logging
from typing import Any, Dict, Optional
import bleach
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    pass


class ValidationError(Exception):
    pass


class InputSanitizer:
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bEXEC\b|\bEXECUTE\b)",
        r"(\bOR\b\s+['\"]?1['\"]?\s*=\s*['\"]?1)",
        r"(\';.*--)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<embed",
        r"<object",
    ]

    ALLOWED_HTML_TAGS = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'ul', 'ol', 'li', 'a']
    ALLOWED_HTML_ATTRIBUTES = {'a': ['href', 'title']}

    MAX_STRING_LENGTH = 10000
    MAX_TEXT_LENGTH = 50000

    def __init__(self):
        self.validators = {
            'report_content': self._validate_report,
            'report_title': self._validate_title,
            'report_description': self._validate_description,
            'moderator_notes': self._validate_notes,
            'username': self._validate_username,
            'email': self._validate_email,
        }

    def sanitize(self, input_type: str, data: Any, strict: bool = True) -> Any:
        if data is None:
            return None

        if isinstance(data, str):
            if len(data) > self.MAX_TEXT_LENGTH:
                raise ValidationError(f"Input exceeds maximum length of {self.MAX_TEXT_LENGTH}")

            cleaned = self._remove_null_bytes(data)
            cleaned = self._normalize_unicode(cleaned)

            if strict:
                cleaned = self._check_sql_injection(cleaned)
                cleaned = self._check_xss(cleaned)

            validator = self.validators.get(input_type)
            if validator:
                if not validator(cleaned):
                    raise ValidationError(f"Input validation failed for type: {input_type}")

            return cleaned

        elif isinstance(data, dict):
            return {k: self.sanitize(input_type, v, strict) for k, v in data.items()}

        elif isinstance(data, list):
            return [self.sanitize(input_type, item, strict) for item in data]

        return data

    def sanitize_html(self, data: str, allowed_tags: Optional[list] = None) -> str:
        if allowed_tags is None:
            allowed_tags = self.ALLOWED_HTML_TAGS

        return bleach.clean(
            data,
            tags=allowed_tags,
            attributes=self.ALLOWED_HTML_ATTRIBUTES,
            strip=True
        )

    def _remove_null_bytes(self, data: str) -> str:
        return data.replace('\x00', '')

    def _normalize_unicode(self, data: str) -> str:
        import unicodedata
        return unicodedata.normalize('NFKC', data)

    def _check_sql_injection(self, data: str) -> str:
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, data, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {pattern}")
                raise SecurityError("Potentially malicious input detected")
        return data

    def _check_xss(self, data: str) -> str:
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, data, re.IGNORECASE):
                logger.warning(f"Potential XSS detected: {pattern}")
                raise SecurityError("Potentially malicious input detected")
        return data

    def _validate_report(self, data: str) -> bool:
        if len(data) < 10:
            return False
        if len(data) > self.MAX_TEXT_LENGTH:
            return False
        return True

    def _validate_title(self, data: str) -> bool:
        if len(data) < 5:
            return False
        if len(data) > 200:
            return False
        if re.search(r'[<>{}]', data):
            return False
        return True

    def _validate_description(self, data: str) -> bool:
        if len(data) < 10:
            return False
        if len(data) > 5000:
            return False
        return True

    def _validate_notes(self, data: str) -> bool:
        if len(data) > 5000:
            return False
        return True

    def _validate_username(self, data: str) -> bool:
        if len(data) < 3 or len(data) > 50:
            return False
        if not re.match(r'^[a-zA-Z0-9_-]+$', data):
            return False
        return True

    def _validate_email(self, data: str) -> bool:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, data))

    def escape_html(self, data: str) -> str:
        return html.escape(data)

    def sanitize_filename(self, filename: str) -> str:
        filename = re.sub(r'[^\w\s.-]', '', filename)
        filename = re.sub(r'[\s]+', '_', filename)
        filename = filename[:255]
        if not filename:
            return 'unnamed_file'
        return filename

    def validate_wallet_address(self, address: str) -> bool:
        if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
            raise ValidationError("Invalid Ethereum wallet address")
        return True

    def validate_ipfs_cid(self, cid: str) -> bool:
        if len(cid) < 46 or len(cid) > 100:
            raise ValidationError("Invalid IPFS CID length")
        if not re.match(r'^[a-zA-Z0-9]+$', cid):
            raise ValidationError("Invalid IPFS CID format")
        return True


input_sanitizer = InputSanitizer()
