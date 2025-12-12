import pytest
from app.security.input_sanitizer import InputSanitizer, SecurityError, ValidationError


class TestInputSanitizer:
    @pytest.fixture
    def sanitizer(self):
        return InputSanitizer()

    def test_sql_injection_detection(self, sanitizer):
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "1' UNION SELECT * FROM passwords--",
            "1; DELETE FROM reports WHERE 1=1",
        ]

        for input_str in malicious_inputs:
            with pytest.raises(SecurityError, match="malicious input"):
                sanitizer.sanitize('report_title', input_str, strict=True)

    def test_xss_detection(self, sanitizer):
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            "javascript:alert(1)",
            "<iframe src='evil.com'></iframe>",
            "<img src=x onerror=alert(1)>",
        ]

        for input_str in malicious_inputs:
            with pytest.raises(SecurityError, match="malicious input"):
                sanitizer.sanitize('report_description', input_str, strict=True)

    def test_sanitize_html(self, sanitizer):
        html_input = "<p>Hello <strong>World</strong></p><script>alert('xss')</script>"
        cleaned = sanitizer.sanitize_html(html_input)

        assert '<script>' not in cleaned
        assert '<p>' in cleaned
        assert '<strong>' in cleaned

    def test_null_byte_removal(self, sanitizer):
        input_with_null = "test\x00data"
        cleaned = sanitizer._remove_null_bytes(input_with_null)

        assert '\x00' not in cleaned
        assert cleaned == "testdata"

    def test_unicode_normalization(self, sanitizer):
        input_str = "Caf\u00e9"
        normalized = sanitizer._normalize_unicode(input_str)

        assert isinstance(normalized, str)

    def test_title_validation(self, sanitizer):
        assert sanitizer._validate_title("Valid Title")
        assert not sanitizer._validate_title("abc")
        assert not sanitizer._validate_title("a" * 300)
        assert not sanitizer._validate_title("Title<script>")

    def test_email_validation(self, sanitizer):
        assert sanitizer._validate_email("test@example.com")
        assert sanitizer._validate_email("user.name+tag@example.co.uk")
        assert not sanitizer._validate_email("invalid.email")
        assert not sanitizer._validate_email("@example.com")

    def test_username_validation(self, sanitizer):
        assert sanitizer._validate_username("user123")
        assert sanitizer._validate_username("test-user")
        assert not sanitizer._validate_username("ab")
        assert not sanitizer._validate_username("user@name")
        assert not sanitizer._validate_username("a" * 100)

    def test_filename_sanitization(self, sanitizer):
        assert sanitizer.sanitize_filename("test.txt") == "test.txt"
        assert sanitizer.sanitize_filename("test file.pdf") == "test_file.pdf"
        assert sanitizer.sanitize_filename("../../etc/passwd") == "..etcpasswd"
        assert sanitizer.sanitize_filename("<script>.exe") == "script.exe"

    def test_wallet_address_validation(self, sanitizer):
        valid_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        invalid_addresses = [
            "0x123",
            "742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "0xZZZZ35Cc6634C0532925a3b844Bc9e7595f0bEb",
        ]

        assert sanitizer.validate_wallet_address(valid_address)

        for addr in invalid_addresses:
            with pytest.raises(ValidationError):
                sanitizer.validate_wallet_address(addr)

    def test_ipfs_cid_validation(self, sanitizer):
        valid_cid = "QmXg9Pp2ytZ14xgmQjYEiHjVjMFXzCVVEcRTWJBmLgR39V"
        invalid_cids = [
            "short",
            "QmInvalid!@#$%",
            "a" * 200,
        ]

        assert sanitizer.validate_ipfs_cid(valid_cid)

        for cid in invalid_cids:
            with pytest.raises(ValidationError):
                sanitizer.validate_ipfs_cid(cid)

    def test_max_length_enforcement(self, sanitizer):
        long_input = "a" * 100000

        with pytest.raises(ValidationError, match="exceeds maximum length"):
            sanitizer.sanitize('report_content', long_input)

    def test_escape_html(self, sanitizer):
        html = "<div>Test & 'quotes'</div>"
        escaped = sanitizer.escape_html(html)

        assert '&lt;' in escaped
        assert '&gt;' in escaped
        assert '&amp;' in escaped

    def test_sanitize_dict(self, sanitizer):
        data = {
            'title': 'Test Title',
            'description': 'Test Description'
        }

        result = sanitizer.sanitize('report_content', data, strict=False)

        assert isinstance(result, dict)
        assert result['title'] == 'Test Title'

    def test_sanitize_list(self, sanitizer):
        data = ['item1', 'item2', 'item3']

        result = sanitizer.sanitize('report_content', data, strict=False)

        assert isinstance(result, list)
        assert len(result) == 3

    def test_sanitize_none(self, sanitizer):
        result = sanitizer.sanitize('report_content', None)
        assert result is None
