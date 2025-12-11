"""
C.O.V.E.R.T - IPFS Service Tests

Tests for IPFS upload, retrieval, and pinning operations
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.ipfs_service import IPFSService, IPFSError


@pytest.fixture
def ipfs_service():
    """Create IPFS service instance for testing"""
    service = IPFSService()
    service.pinata_api_key = "test-pinata-key"
    service.pinata_secret_key = "test-pinata-secret"
    service.web3_storage_token = "test-web3-token"
    return service


@pytest.fixture
def sample_encrypted_blob():
    """Sample encrypted report blob"""
    return json.dumps({
        "version": 1,
        "encrypted_payload": {
            "ciphertext": "base64encrypteddata==",
            "iv": "base64iv==",
            "authTag": "",
            "version": 1,
            "algorithm": "AES-256-GCM"
        },
        "metadata": {
            "originalSize": 1024,
            "paddedSize": 65536,
            "timestamp": "2024-01-15T10:30:00Z",
            "fileCount": 1
        }
    }).encode()


class TestIPFSServiceUpload:
    """Tests for IPFS upload functionality"""

    @pytest.mark.asyncio
    async def test_upload_to_pinata_success(self, ipfs_service, sample_encrypted_blob):
        """Test successful upload to Pinata"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "IpfsHash": "QmTestCID123",
            "PinSize": len(sample_encrypted_blob),
            "Timestamp": "2024-01-15T10:30:00Z"
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance

            result = await ipfs_service.upload(
                sample_encrypted_blob,
                filename="test_report.json",
                metadata={"encrypted": "true"}
            )

            assert result["cid"] == "QmTestCID123"
            assert result["size"] == len(sample_encrypted_blob)
            assert "gateway_url" in result
            assert "pin_status" in result

    @pytest.mark.asyncio
    async def test_upload_fallback_to_web3_storage(self, ipfs_service, sample_encrypted_blob):
        """Test fallback to web3.storage when Pinata fails"""
        pinata_response = MagicMock()
        pinata_response.raise_for_status.side_effect = Exception("Pinata error")

        web3_response = MagicMock()
        web3_response.status_code = 200
        web3_response.raise_for_status = MagicMock()
        web3_response.json.return_value = {"cid": "bafyWeb3CID"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.post.side_effect = [
                pinata_response,  # Pinata fails
                web3_response,   # web3.storage succeeds
            ]
            mock_client.return_value = mock_instance

            result = await ipfs_service.upload(sample_encrypted_blob)

            assert result["cid"] == "bafyWeb3CID"
            assert result["pin_status"]["web3storage"] is True

    @pytest.mark.asyncio
    async def test_upload_fallback_to_local_ipfs(self, ipfs_service, sample_encrypted_blob):
        """Test fallback to local IPFS when all services fail"""
        # Remove API keys to skip Pinata and web3.storage
        ipfs_service.pinata_api_key = ""
        ipfs_service.web3_storage_token = ""

        local_response = MagicMock()
        local_response.status_code = 200
        local_response.raise_for_status = MagicMock()
        local_response.json.return_value = {
            "Hash": "QmLocalCID",
            "Size": "1024"
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.post.return_value = local_response
            mock_client.return_value = mock_instance

            result = await ipfs_service.upload(sample_encrypted_blob)

            assert result["cid"] == "QmLocalCID"
            assert result["pin_status"]["local"] is True

    @pytest.mark.asyncio
    async def test_upload_all_methods_fail(self, ipfs_service, sample_encrypted_blob):
        """Test error when all upload methods fail"""
        ipfs_service.pinata_api_key = ""
        ipfs_service.web3_storage_token = ""

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.post.side_effect = Exception("Connection failed")
            mock_client.return_value = mock_instance

            with pytest.raises(IPFSError) as exc_info:
                await ipfs_service.upload(sample_encrypted_blob)

            assert exc_info.value.code == "UPLOAD_FAILED"


class TestIPFSServiceRetrieval:
    """Tests for IPFS content retrieval"""

    @pytest.mark.asyncio
    async def test_retrieve_success(self, ipfs_service, sample_encrypted_blob):
        """Test successful retrieval from gateway"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.content = sample_encrypted_blob

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.get.return_value = mock_response
            mock_client.return_value = mock_instance

            result = await ipfs_service.retrieve("QmTestCID")

            assert result == sample_encrypted_blob

    @pytest.mark.asyncio
    async def test_retrieve_fallback_gateways(self, ipfs_service, sample_encrypted_blob):
        """Test fallback to alternative gateways"""
        fail_response = MagicMock()
        fail_response.raise_for_status.side_effect = Exception("Gateway error")

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.raise_for_status = MagicMock()
        success_response.content = sample_encrypted_blob

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            # First gateway fails, second succeeds
            mock_instance.get.side_effect = [fail_response, success_response]
            mock_client.return_value = mock_instance

            result = await ipfs_service.retrieve("QmTestCID")

            assert result == sample_encrypted_blob

    @pytest.mark.asyncio
    async def test_retrieve_all_gateways_fail(self, ipfs_service):
        """Test error when all gateways fail"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.get.side_effect = Exception("All gateways down")
            mock_client.return_value = mock_instance

            with pytest.raises(IPFSError) as exc_info:
                await ipfs_service.retrieve("QmTestCID")

            assert exc_info.value.code == "RETRIEVAL_FAILED"


class TestIPFSServicePinning:
    """Tests for IPFS pinning operations"""

    @pytest.mark.asyncio
    async def test_pin_to_pinata_success(self, ipfs_service):
        """Test successful pinning to Pinata"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "hashToPin": "QmTestCID",
            "pinataHash": "QmTestCID"
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance

            result = await ipfs_service.pin("QmTestCID")

            assert result["cid"] == "QmTestCID"
            assert result["is_pinned"] is True
            assert "pinned_at" in result

    @pytest.mark.asyncio
    async def test_get_pin_status(self, ipfs_service):
        """Test checking pin status"""
        local_response = MagicMock()
        local_response.status_code = 200

        pinata_response = MagicMock()
        pinata_response.status_code = 200
        pinata_response.json.return_value = {
            "count": 1,
            "rows": [{"ipfs_pin_hash": "QmTestCID"}]
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.post.return_value = local_response
            mock_instance.get.return_value = pinata_response
            mock_client.return_value = mock_instance

            result = await ipfs_service.get_pin_status("QmTestCID")

            assert result["cid"] == "QmTestCID"
            assert result["is_pinned"] is True
            assert "providers" in result


class TestIPFSServiceValidation:
    """Tests for CID validation and hashing"""

    def test_validate_cid_v0(self, ipfs_service):
        """Test validation of CIDv0"""
        valid_cid = "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG"
        assert ipfs_service.validate_cid(valid_cid) is True

    def test_validate_cid_v1(self, ipfs_service):
        """Test validation of CIDv1"""
        valid_cid = "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi"
        assert ipfs_service.validate_cid(valid_cid) is True

    def test_validate_invalid_cid(self, ipfs_service):
        """Test validation rejects invalid CID"""
        invalid_cid = "invalid-cid-format"
        assert ipfs_service.validate_cid(invalid_cid) is False

    def test_validate_short_cid(self, ipfs_service):
        """Test validation rejects too short CID"""
        short_cid = "Qm123"
        assert ipfs_service.validate_cid(short_cid) is False

    def test_compute_cid_hash(self, ipfs_service):
        """Test computing CID hash for blockchain"""
        cid = "QmTestCID123"
        hash_result = ipfs_service.compute_cid_hash(cid)

        # Should be 0x prefixed 64-char hex
        assert hash_result.startswith("0x")
        assert len(hash_result) == 66

    def test_cid_hash_consistency(self, ipfs_service):
        """Test CID hash produces consistent results"""
        cid = "QmTestCID123"

        hash1 = ipfs_service.compute_cid_hash(cid)
        hash2 = ipfs_service.compute_cid_hash(cid)

        assert hash1 == hash2

    def test_different_cids_different_hashes(self, ipfs_service):
        """Test different CIDs produce different hashes"""
        hash1 = ipfs_service.compute_cid_hash("QmCID1")
        hash2 = ipfs_service.compute_cid_hash("QmCID2")

        assert hash1 != hash2


class TestIPFSServiceRetry:
    """Tests for retry logic"""

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self, ipfs_service, sample_encrypted_blob):
        """Test automatic retry on transient failures"""
        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Transient error")
            response = MagicMock()
            response.status_code = 200
            response.raise_for_status = MagicMock()
            response.json.return_value = {"Hash": "QmRetryCID"}
            return response

        ipfs_service.pinata_api_key = ""
        ipfs_service.web3_storage_token = ""

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.post = mock_post
            mock_client.return_value = mock_instance

            result = await ipfs_service.upload(sample_encrypted_blob)

            assert result["cid"] == "QmRetryCID"
            assert call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
