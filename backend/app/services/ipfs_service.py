"""
C.O.V.E.R.T - IPFS Service

Handles IPFS integration, pinning, and content retrieval
"""

import asyncio
import hashlib
import logging
from typing import Optional
from datetime import datetime

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class IPFSError(Exception):
    """IPFS operation error"""

    def __init__(self, code: str, message: str, retry_count: int = 0):
        self.code = code
        self.message = message
        self.retry_count = retry_count
        super().__init__(message)


class IPFSService:
    """
    IPFS integration service for managing encrypted blob storage
    """

    def __init__(self):
        self.local_api_url = self._multiaddr_to_http(settings.IPFS_API_URL)
        self.gateway_url = settings.IPFS_GATEWAY_URL
        self.pinata_api_key = settings.PINATA_API_KEY
        self.pinata_secret_key = settings.PINATA_SECRET_KEY
        self.web3_storage_token = settings.WEB3_STORAGE_TOKEN
        self.max_retries = 3
        self.retry_delay = 1.0
        self.timeout = 300.0

    @staticmethod
    def _multiaddr_to_http(addr: str) -> str:
        """Convert multiaddr like /ip4/127.0.0.1/tcp/5001 to http://127.0.0.1:5001"""
        if addr.startswith("http"):
            return addr.rstrip("/")
        parts = addr.strip("/").split("/")
        if len(parts) >= 4 and parts[0] == "ip4" and parts[2] == "tcp":
            return f"http://{parts[1]}:{parts[3]}"
        return f"http://127.0.0.1:5001"

    async def upload(
        self,
        data: bytes,
        filename: str = "encrypted_report.json",
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Upload data to IPFS with multi-tier pinning

        Args:
            data: Bytes to upload
            filename: Name for the file
            metadata: Optional metadata for pinning services

        Returns:
            dict with cid, gateway_url, and pin_status
        """
        cid = None
        pin_results = {}

        # Try Pinata first (has both upload and pin)
        if self.pinata_api_key and self.pinata_secret_key:
            try:
                result = await self._upload_to_pinata(data, filename, metadata)
                cid = result["IpfsHash"]
                pin_results["pinata"] = True
                logger.info(f"Uploaded to Pinata: {cid}")
            except Exception as e:
                logger.warning(f"Pinata upload failed: {e}")

        # Try web3.storage as backup
        if not cid and self.web3_storage_token:
            try:
                result = await self._upload_to_web3_storage(data, filename)
                cid = result["cid"]
                pin_results["web3storage"] = True
                logger.info(f"Uploaded to web3.storage: {cid}")
            except Exception as e:
                logger.warning(f"web3.storage upload failed: {e}")

        # Try local IPFS as last resort
        if not cid:
            try:
                result = await self._upload_to_local_ipfs(data)
                cid = result["Hash"]
                pin_results["local"] = True
                logger.info(f"Uploaded to local IPFS: {cid}")
            except Exception as e:
                logger.error(f"Local IPFS upload failed: {e}")
                raise IPFSError(
                    "UPLOAD_FAILED",
                    "All IPFS upload methods failed",
                    retry_count=self.max_retries,
                )

        # Pin to additional services for redundancy
        if cid:
            if self.pinata_api_key and "pinata" not in pin_results:
                try:
                    await self._pin_to_pinata(cid)
                    pin_results["pinata"] = True
                except Exception as e:
                    logger.warning(f"Pinata pinning failed: {e}")

        return {
            "cid": cid,
            "gateway_url": f"https://nftstorage.link/ipfs/{cid}",
            "size": len(data),
            "pin_status": pin_results,
            "uploaded_at": datetime.utcnow().isoformat(),
        }

    async def retrieve(self, cid: str) -> bytes:
        """
        Retrieve content from IPFS using multiple gateways

        Args:
            cid: Content identifier

        Returns:
            Content bytes
        """
        gateways = [
            f"https://nftstorage.link/ipfs/{cid}",
            f"https://w3s.link/ipfs/{cid}",
            f"https://ipfs.io/ipfs/{cid}",
            f"https://cloudflare-ipfs.com/ipfs/{cid}",
            f"{self.gateway_url}/ipfs/{cid}",
        ]

        last_error = None

        for gateway_url in gateways:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(gateway_url)
                    response.raise_for_status()
                    return response.content
            except Exception as e:
                logger.warning(f"Failed to retrieve from {gateway_url}: {e}")
                last_error = e
                continue

        raise IPFSError(
            "RETRIEVAL_FAILED",
            f"Failed to retrieve CID {cid} from all gateways",
        )

    async def pin(self, cid: str) -> dict:
        """
        Pin a CID to ensure persistence

        Args:
            cid: Content identifier to pin

        Returns:
            Pin status dict
        """
        pin_results = {}

        # Pin to Pinata
        if self.pinata_api_key and self.pinata_secret_key:
            try:
                await self._pin_to_pinata(cid)
                pin_results["pinata"] = True
            except Exception as e:
                logger.warning(f"Pinata pinning failed: {e}")
                pin_results["pinata"] = False

        # Pin to local IPFS
        try:
            await self._pin_to_local_ipfs(cid)
            pin_results["local"] = True
        except Exception as e:
            logger.warning(f"Local IPFS pinning failed: {e}")
            pin_results["local"] = False

        if not any(pin_results.values()):
            raise IPFSError("PIN_FAILED", f"Failed to pin CID {cid}")

        return {
            "cid": cid,
            "is_pinned": any(pin_results.values()),
            "providers": pin_results,
            "pinned_at": datetime.utcnow().isoformat(),
        }

    async def unpin(self, cid: str) -> None:
        """
        Unpin a CID

        Args:
            cid: Content identifier to unpin
        """
        # Unpin from local IPFS
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.local_api_url}/api/v0/pin/rm?arg={cid}"
                )
                response.raise_for_status()
        except Exception as e:
            logger.warning(f"Failed to unpin from local IPFS: {e}")

        # Note: Unpinning from Pinata requires different API call
        # Most services keep content pinned for redundancy

    async def get_pin_status(self, cid: str) -> dict:
        """
        Check pin status for a CID

        Args:
            cid: Content identifier

        Returns:
            Pin status information
        """
        is_pinned = False
        providers = {}

        # Check local IPFS
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.local_api_url}/api/v0/pin/ls?arg={cid}"
                )
                if response.status_code == 200:
                    is_pinned = True
                    providers["local"] = True
        except Exception:
            providers["local"] = False

        # Check Pinata
        if self.pinata_api_key:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        f"https://api.pinata.cloud/data/pinList?hashContains={cid}",
                        headers={
                            "pinata_api_key": self.pinata_api_key,
                            "pinata_secret_api_key": self.pinata_secret_key,
                        },
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("count", 0) > 0:
                            is_pinned = True
                            providers["pinata"] = True
                        else:
                            providers["pinata"] = False
            except Exception:
                providers["pinata"] = False

        return {
            "cid": cid,
            "is_pinned": is_pinned,
            "providers": providers,
        }

    def validate_cid(self, cid: str) -> bool:
        """
        Validate CID format

        Args:
            cid: Content identifier to validate

        Returns:
            True if valid, False otherwise
        """
        # CIDv0 starts with Qm and is 46 characters
        if cid.startswith("Qm") and len(cid) == 46:
            return True

        # CIDv1 starts with bafy (or other multibase prefixes)
        if cid.startswith("bafy") or cid.startswith("bafk"):
            return True

        return False

    def compute_cid_hash(self, cid: str) -> str:
        """
        Compute SHA-256 hash of CID for blockchain storage

        Args:
            cid: Content identifier

        Returns:
            Hex-encoded hash with 0x prefix
        """
        hash_bytes = hashlib.sha256(cid.encode()).digest()
        return "0x" + hash_bytes.hex()

    # ===== Private Methods =====

    async def _upload_to_pinata(
        self, data: bytes, filename: str, metadata: Optional[dict] = None
    ) -> dict:
        """Upload to Pinata"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            files = {"file": (filename, data)}

            options = {
                "pinataMetadata": {
                    "name": filename,
                    "keyvalues": metadata or {"encrypted": "true"},
                },
            }

            response = await client.post(
                "https://api.pinata.cloud/pinning/pinFileToIPFS",
                headers={
                    "pinata_api_key": self.pinata_api_key,
                    "pinata_secret_api_key": self.pinata_secret_key,
                },
                files=files,
                data={"pinataOptions": str(options)},
            )
            response.raise_for_status()
            return response.json()

    async def _upload_to_web3_storage(self, data: bytes, filename: str) -> dict:
        """Upload to web3.storage"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                "https://api.web3.storage/upload",
                headers={
                    "Authorization": f"Bearer {self.web3_storage_token}",
                    "X-Name": filename,
                },
                content=data,
            )
            response.raise_for_status()
            return response.json()

    async def _upload_to_local_ipfs(self, data: bytes) -> dict:
        """Upload to local IPFS node"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            files = {"file": ("data", data)}
            response = await client.post(
                f"{self.local_api_url}/api/v0/add",
                files=files,
            )
            response.raise_for_status()
            return response.json()

    async def _pin_to_pinata(self, cid: str) -> dict:
        """Pin CID to Pinata"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.pinata.cloud/pinning/pinByHash",
                headers={
                    "pinata_api_key": self.pinata_api_key,
                    "pinata_secret_api_key": self.pinata_secret_key,
                    "Content-Type": "application/json",
                },
                json={"hashToPin": cid},
            )
            response.raise_for_status()
            return response.json()

    async def _pin_to_local_ipfs(self, cid: str) -> dict:
        """Pin CID to local IPFS node"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.local_api_url}/api/v0/pin/add?arg={cid}"
            )
            response.raise_for_status()
            return response.json()


# Singleton instance
ipfs_service = IPFSService()
