import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.zkp.verifier import ZKProofVerifier, VerificationResult


class TestZKProofVerifier:
    @pytest.fixture
    def mock_verification_key(self):
        return {
            "protocol": "groth16",
            "curve": "bn128",
            "nPublic": 3,
            "vk_alpha_1": ["1", "2"],
            "vk_beta_2": [["1", "2"], ["3", "4"]],
            "vk_gamma_2": [["1", "2"], ["3", "4"]],
            "vk_delta_2": [["1", "2"], ["3", "4"]],
            "IC": [["1", "2"], ["3", "4"], ["5", "6"]]
        }

    @pytest.fixture
    def verifier(self, tmp_path, mock_verification_key):
        vkey_path = tmp_path / "verification_key.json"
        import json
        with open(vkey_path, 'w') as f:
            json.dump(mock_verification_key, f)

        return ZKProofVerifier(str(vkey_path))

    @pytest.fixture
    def valid_proof(self):
        return {
            "pi_a": ["1", "2"],
            "pi_b": [["1", "2"], ["3", "4"]],
            "pi_c": ["5", "6"],
            "protocol": "groth16",
            "curve": "bn128"
        }

    @pytest.fixture
    def public_signals(self):
        return [
            "12345678901234567890",
            "98765432109876543210",
            "1"
        ]

    def test_load_verification_key_success(self, verifier, mock_verification_key):
        assert verifier.verification_key is not None
        assert verifier.verification_key["protocol"] == "groth16"

    def test_load_verification_key_not_found(self, tmp_path):
        verifier = ZKProofVerifier(str(tmp_path / "nonexistent.json"))
        assert verifier.verification_key is None

    @pytest.mark.asyncio
    async def test_verify_proof_no_vkey(self, valid_proof, public_signals):
        verifier = ZKProofVerifier("/nonexistent/path")
        result = await verifier.verify_proof(valid_proof, public_signals)

        assert not result.is_valid
        assert "Verification key not loaded" in result.error

    @pytest.mark.asyncio
    async def test_verify_proof_with_snarkjs_success(self, verifier, valid_proof, public_signals):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="OK! Proof verified successfully"
            )

            result = await verifier.verify_proof(valid_proof, public_signals)

            assert result.is_valid
            assert result.commitment == public_signals[0]
            assert result.nullifier_hash == public_signals[1]
            assert result.error is None

    @pytest.mark.asyncio
    async def test_verify_proof_with_snarkjs_failure(self, verifier, valid_proof, public_signals):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="FAIL! Invalid proof"
            )

            result = await verifier.verify_proof(valid_proof, public_signals)

            assert not result.is_valid

    @pytest.mark.asyncio
    async def test_verify_proof_timeout(self, verifier, valid_proof, public_signals):
        import subprocess
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("snarkjs", 30)):
            result = await verifier.verify_proof(valid_proof, public_signals)

            assert not result.is_valid

    def test_verify_nullifier_uniqueness_new(self, verifier):
        mock_db = Mock()
        mock_db.query().filter_by().first.return_value = None

        is_unique = verifier.verify_nullifier_uniqueness("0x1234", mock_db)
        assert is_unique

    def test_verify_nullifier_uniqueness_existing(self, verifier):
        mock_db = Mock()
        mock_db.query().filter_by().first.return_value = Mock()

        is_unique = verifier.verify_nullifier_uniqueness("0x1234", mock_db)
        assert not is_unique

    def test_check_rate_limit_no_record(self, verifier):
        mock_db = Mock()
        mock_db.query().filter_by().first.return_value = None

        within_limit = verifier.check_rate_limit("0x1234", mock_db)
        assert within_limit

    def test_check_rate_limit_under_limit(self, verifier):
        from datetime import date

        mock_nullifier = Mock()
        mock_nullifier.daily_report_count = 3
        mock_nullifier.last_daily_reset = date.today()

        mock_db = Mock()
        mock_db.query().filter_by().first.return_value = mock_nullifier

        within_limit = verifier.check_rate_limit("0x1234", mock_db)
        assert within_limit

    def test_check_rate_limit_at_limit(self, verifier):
        from datetime import date

        mock_nullifier = Mock()
        mock_nullifier.daily_report_count = 5
        mock_nullifier.last_daily_reset = date.today()

        mock_db = Mock()
        mock_db.query().filter_by().first.return_value = mock_nullifier

        within_limit = verifier.check_rate_limit("0x1234", mock_db)
        assert not within_limit

    def test_check_rate_limit_reset_needed(self, verifier):
        from datetime import date, timedelta

        mock_nullifier = Mock()
        mock_nullifier.daily_report_count = 5
        mock_nullifier.last_daily_reset = date.today() - timedelta(days=1)

        mock_db = Mock()
        mock_db.query().filter_by().first.return_value = mock_nullifier

        within_limit = verifier.check_rate_limit("0x1234", mock_db)
        assert within_limit
        assert mock_nullifier.daily_report_count == 0
