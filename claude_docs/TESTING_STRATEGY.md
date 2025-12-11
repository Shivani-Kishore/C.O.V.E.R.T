# C.O.V.E.R.T Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the C.O.V.E.R.T platform, covering unit tests, integration tests, end-to-end tests, security testing, and smart contract testing.

## Testing Philosophy

### Core Principles

1. **Security First**: Every feature must have security tests
2. **Privacy Preservation**: Tests must not compromise user anonymity
3. **Comprehensive Coverage**: Aim for >80% code coverage
4. **Automated**: All tests must be automated and run in CI/CD
5. **Fast Feedback**: Unit tests should run in <1 minute
6. **Realistic**: Integration tests should use realistic data

### Testing Pyramid

```
        /\
       /  \
      / E2E \         10% - End-to-End Tests
     /______\
    /        \
   /Integration\      30% - Integration Tests
  /____________\
 /              \
/   Unit Tests   \    60% - Unit Tests
/________________\
```

## Test Coverage Goals

### Overall Coverage Target: 80%+

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| Backend API | 85%+ | Critical |
| Smart Contracts | 100% | Critical |
| Encryption Services | 95%+ | Critical |
| Frontend Components | 75%+ | High |
| Utilities | 90%+ | High |
| UI Components | 70%+ | Medium |

## Technology Stack

### Frontend Testing

```json
{
  "testing-library/react": "^14.0.0",
  "testing-library/jest-dom": "^6.1.0",
  "testing-library/user-event": "^14.5.0",
  "vitest": "^1.0.0",
  "@vitest/ui": "^1.0.0",
  "jsdom": "^23.0.0",
  "msw": "^2.0.0"
}
```

### Backend Testing

```txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.0
faker==20.1.0
factory-boy==3.3.0
```

### Smart Contract Testing

```json
{
  "forge-std": "^1.7.0",
  "solidity-coverage": "^0.8.5"
}
```

### E2E Testing

```json
{
  "playwright": "^1.40.0",
  "@playwright/test": "^1.40.0"
}
```

## 1. Unit Testing

### Frontend Unit Tests

#### Component Testing Example

```typescript
// __tests__/components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/common/Button';
import { describe, it, expect, vi } from 'vitest';

describe('Button Component', () => {
  describe('Rendering', () => {
    it('renders with correct text', () => {
      render(<Button>Click me</Button>);
      expect(screen.getByRole('button')).toHaveTextContent('Click me');
    });

    it('applies primary variant styles by default', () => {
      render(<Button>Click me</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-primary-600');
    });

    it('renders with left icon', () => {
      const Icon = () => <span data-testid="icon">Icon</span>;
      render(<Button leftIcon={<Icon />}>Click me</Button>);
      expect(screen.getByTestId('icon')).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('calls onClick when clicked', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Click me</Button>);
      
      fireEvent.click(screen.getByRole('button'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not call onClick when disabled', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick} disabled>Click me</Button>);
      
      fireEvent.click(screen.getByRole('button'));
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    it('shows loading spinner when isLoading is true', () => {
      render(<Button isLoading>Click me</Button>);
      expect(screen.getByRole('button')).toBeDisabled();
    });

    it('hides button text when loading', () => {
      render(<Button isLoading>Click me</Button>);
      expect(screen.queryByText('Click me')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('is focusable', () => {
      render(<Button>Click me</Button>);
      const button = screen.getByRole('button');
      button.focus();
      expect(button).toHaveFocus();
    });

    it('has proper aria-disabled when disabled', () => {
      render(<Button disabled>Click me</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('disabled');
    });
  });
});
```

#### Hook Testing Example

```typescript
// __tests__/hooks/useEncryption.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useEncryption } from '@/hooks/useEncryption';
import { describe, it, expect } from 'vitest';

describe('useEncryption Hook', () => {
  it('encrypts and decrypts data correctly', async () => {
    const { result } = renderHook(() => useEncryption());
    
    const originalData = { message: 'Secret information' };
    
    const encrypted = await result.current.encrypt(originalData);
    expect(encrypted).not.toEqual(originalData);
    expect(encrypted.ciphertext).toBeDefined();
    expect(encrypted.iv).toBeDefined();
    expect(encrypted.salt).toBeDefined();
    
    const decrypted = await result.current.decrypt(encrypted);
    expect(decrypted).toEqual(originalData);
  });

  it('generates unique IVs for each encryption', async () => {
    const { result } = renderHook(() => useEncryption());
    
    const data = { message: 'Test' };
    const encrypted1 = await result.current.encrypt(data);
    const encrypted2 = await result.current.encrypt(data);
    
    expect(encrypted1.iv).not.toEqual(encrypted2.iv);
    expect(encrypted1.ciphertext).not.toEqual(encrypted2.ciphertext);
  });

  it('throws error on invalid decryption', async () => {
    const { result } = renderHook(() => useEncryption());
    
    const invalidData = {
      ciphertext: 'invalid',
      iv: 'invalid',
      salt: 'invalid'
    };
    
    await expect(result.current.decrypt(invalidData)).rejects.toThrow();
  });
});
```

### Backend Unit Tests

#### API Endpoint Testing

```python
# tests/test_reports_api.py
import pytest
from httpx import AsyncClient
from app.main import app
from app.models import Report
from tests.factories import ReportFactory

@pytest.mark.asyncio
class TestReportsAPI:
    async def test_submit_report_success(self, client: AsyncClient, db_session):
        """Test successful report submission"""
        payload = {
            "ipfs_cid": "QmTest123456789",
            "commitment_hash": "0x" + "a" * 64,
            "encrypted_category": "corruption",
            "visibility": "moderated",
            "chain_id": 80001
        }
        
        response = await client.post("/api/reports/submit", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["ipfs_cid"] == payload["ipfs_cid"]
        assert data["status"] == "pending"
        assert "id" in data
        
        # Verify database record
        report = await db_session.query(Report).filter_by(
            ipfs_cid=payload["ipfs_cid"]
        ).first()
        assert report is not None

    async def test_submit_report_duplicate_commitment(self, client: AsyncClient, db_session):
        """Test that duplicate commitment hashes are rejected"""
        commitment_hash = "0x" + "b" * 64
        
        # Create first report
        await ReportFactory.create(commitment_hash=commitment_hash)
        
        # Try to create duplicate
        payload = {
            "ipfs_cid": "QmDifferent",
            "commitment_hash": commitment_hash,
            "encrypted_category": "fraud",
            "visibility": "private",
            "chain_id": 80001
        }
        
        response = await client.post("/api/reports/submit", json=payload)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    async def test_get_report_by_id(self, client: AsyncClient):
        """Test retrieving a report by ID"""
        report = await ReportFactory.create()
        
        response = await client.get(f"/api/reports/{report.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(report.id)
        assert data["ipfs_cid"] == report.ipfs_cid

    async def test_get_report_not_found(self, client: AsyncClient):
        """Test 404 for non-existent report"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/reports/{fake_uuid}")
        assert response.status_code == 404

    async def test_list_reports_with_filters(self, client: AsyncClient):
        """Test listing reports with status filter"""
        await ReportFactory.create(status="pending")
        await ReportFactory.create(status="verified")
        await ReportFactory.create(status="pending")
        
        response = await client.get("/api/reports?status=pending")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert all(r["status"] == "pending" for r in data["items"])

    async def test_update_report_status_unauthorized(self, client: AsyncClient):
        """Test that non-moderators cannot update report status"""
        report = await ReportFactory.create()
        
        response = await client.patch(
            f"/api/reports/{report.id}/status",
            json={"status": "verified"}
        )
        
        assert response.status_code == 403
```

#### Service Layer Testing

```python
# tests/test_encryption_service.py
import pytest
from app.services.encryption import EncryptionService

class TestEncryptionService:
    def setup_method(self):
        self.service = EncryptionService()

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption are inverse operations"""
        plaintext = b"Sensitive whistleblower information"
        password = "strong_password_123"
        
        encrypted = self.service.encrypt(plaintext, password)
        decrypted = self.service.decrypt(encrypted, password)
        
        assert decrypted == plaintext

    def test_different_passwords_produce_different_ciphertexts(self):
        """Test that same plaintext with different passwords produces different ciphertexts"""
        plaintext = b"Secret data"
        
        encrypted1 = self.service.encrypt(plaintext, "password1")
        encrypted2 = self.service.encrypt(plaintext, "password2")
        
        assert encrypted1["ciphertext"] != encrypted2["ciphertext"]
        assert encrypted1["salt"] != encrypted2["salt"]

    def test_wrong_password_fails_decryption(self):
        """Test that wrong password fails to decrypt"""
        plaintext = b"Secret"
        encrypted = self.service.encrypt(plaintext, "correct_password")
        
        with pytest.raises(Exception):
            self.service.decrypt(encrypted, "wrong_password")

    def test_padding_obscures_length(self):
        """Test that file padding obscures actual file size"""
        small_file = b"A" * 100
        large_file = b"B" * 1000000
        
        padded_small = self.service.pad_file(small_file)
        padded_large = self.service.pad_file(large_file)
        
        # Both should be padded to nearest size threshold
        assert len(padded_small) > len(small_file)
        assert len(padded_small) in [1024 * 100, 1024 * 500, 1024 * 1024]
```

### Smart Contract Unit Tests

```solidity
// test/CommitmentRegistry.t.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/CommitmentRegistry.sol";

contract CommitmentRegistryTest is Test {
    CommitmentRegistry public registry;
    address public reporter = address(0x1);
    
    function setUp() public {
        registry = new CommitmentRegistry();
    }
    
    function testSubmitCommitment() public {
        bytes32 commitmentHash = keccak256("test_report");
        string memory ipfsCID = "QmTest123";
        
        vm.prank(reporter);
        registry.submitCommitment(commitmentHash, ipfsCID);
        
        assertTrue(registry.commitmentExists(commitmentHash));
        assertEq(registry.getIPFSCID(commitmentHash), ipfsCID);
    }
    
    function testCannotSubmitDuplicateCommitment() public {
        bytes32 commitmentHash = keccak256("test_report");
        string memory ipfsCID = "QmTest123";
        
        vm.prank(reporter);
        registry.submitCommitment(commitmentHash, ipfsCID);
        
        // Try to submit again
        vm.prank(reporter);
        vm.expectRevert("Commitment already exists");
        registry.submitCommitment(commitmentHash, ipfsCID);
    }
    
    function testEmitCommitmentEvent() public {
        bytes32 commitmentHash = keccak256("test_report");
        string memory ipfsCID = "QmTest123";
        
        vm.expectEmit(true, true, false, true);
        emit CommitmentRegistry.CommitmentSubmitted(
            commitmentHash,
            reporter,
            ipfsCID,
            block.timestamp
        );
        
        vm.prank(reporter);
        registry.submitCommitment(commitmentHash, ipfsCID);
    }
    
    function testGetCommitmentTimestamp() public {
        bytes32 commitmentHash = keccak256("test_report");
        string memory ipfsCID = "QmTest123";
        
        uint256 beforeTime = block.timestamp;
        
        vm.prank(reporter);
        registry.submitCommitment(commitmentHash, ipfsCID);
        
        uint256 recordedTime = registry.getCommitmentTimestamp(commitmentHash);
        assertEq(recordedTime, beforeTime);
    }
}
```

## 2. Integration Testing

### API Integration Tests

```python
# tests/integration/test_report_submission_flow.py
import pytest
from httpx import AsyncClient
from web3 import Web3

@pytest.mark.asyncio
class TestReportSubmissionFlow:
    async def test_complete_report_submission(
        self, 
        client: AsyncClient,
        web3: Web3,
        ipfs_client
    ):
        """Test complete flow from encryption to blockchain to backend"""
        
        # Step 1: Encrypt report data
        report_data = {
            "title": "Corruption in procurement",
            "description": "Detailed evidence...",
            "category": "corruption"
        }
        
        encrypted_data = await client.post(
            "/api/encryption/encrypt",
            json=report_data
        )
        assert encrypted_data.status_code == 200
        
        # Step 2: Upload to IPFS
        ipfs_response = await ipfs_client.upload(encrypted_data.json())
        ipfs_cid = ipfs_response["cid"]
        
        # Step 3: Submit commitment to blockchain
        commitment_hash = Web3.keccak(text=ipfs_cid).hex()
        tx_hash = await submit_to_blockchain(commitment_hash, ipfs_cid)
        
        # Step 4: Submit to backend
        payload = {
            "ipfs_cid": ipfs_cid,
            "commitment_hash": commitment_hash,
            "transaction_hash": tx_hash,
            "encrypted_category": "corruption",
            "visibility": "moderated",
            "chain_id": 80001
        }
        
        response = await client.post("/api/reports/submit", json=payload)
        assert response.status_code == 201
        
        # Verify report was created
        report_id = response.json()["id"]
        report = await client.get(f"/api/reports/{report_id}")
        assert report.status_code == 200
        assert report.json()["status"] == "pending"
```

### Database Integration Tests

```python
# tests/integration/test_database_operations.py
import pytest
from app.models import Report, Moderation, Moderator
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
class TestDatabaseOperations:
    async def test_report_moderation_relationship(self, db_session: AsyncSession):
        """Test relationships between reports and moderations"""
        # Create report
        report = Report(
            commitment_hash="0x" + "a" * 64,
            ipfs_cid="QmTest",
            status="pending"
        )
        db_session.add(report)
        await db_session.commit()
        
        # Create moderator
        moderator = Moderator(
            wallet_address="0x" + "b" * 40,
            reputation_score=100
        )
        db_session.add(moderator)
        await db_session.commit()
        
        # Create moderation
        moderation = Moderation(
            report_id=report.id,
            moderator_id=moderator.id,
            action="review_started"
        )
        db_session.add(moderation)
        await db_session.commit()
        
        # Verify relationships
        await db_session.refresh(report, ["moderations"])
        assert len(report.moderations) == 1
        assert report.moderations[0].action == "review_started"

    async def test_cascade_delete(self, db_session: AsyncSession):
        """Test that deleting report cascades to moderations"""
        report = Report(
            commitment_hash="0x" + "c" * 64,
            ipfs_cid="QmCascade"
        )
        db_session.add(report)
        await db_session.commit()
        
        moderation = Moderation(
            report_id=report.id,
            action="review_started"
        )
        db_session.add(moderation)
        await db_session.commit()
        
        # Delete report
        await db_session.delete(report)
        await db_session.commit()
        
        # Verify moderation was also deleted
        result = await db_session.query(Moderation).filter_by(
            report_id=report.id
        ).first()
        assert result is None
```

## 3. End-to-End Testing

### Playwright E2E Tests

```typescript
// tests/e2e/report-submission.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Report Submission Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test('complete report submission as anonymous user', async ({ page }) => {
    // Navigate to submit page
    await page.click('text=Submit Report');
    
    // Fill form - Step 1: Details
    await page.selectOption('select[name="category"]', 'corruption');
    await page.fill('input[name="title"]', 'Test corruption report');
    await page.fill(
      'textarea[name="description"]',
      'This is a detailed description of corruption that meets the minimum length requirement.'
    );
    await page.click('button:has-text("Next: Attachments")');
    
    // Step 2: Skip attachments
    await page.click('button:has-text("Next: Privacy Settings")');
    
    // Step 3: Privacy settings
    await page.click('input[value="moderated"]');
    
    // Submit
    await page.click('button:has-text("Submit Report")');
    
    // Wait for encryption and submission
    await page.waitForSelector('text=Report submitted successfully', {
      timeout: 10000
    });
    
    // Verify redirect to my reports
    await expect(page).toHaveURL(/.*my-reports/);
    
    // Verify report appears in list
    await expect(page.locator('text=Test corruption report')).toBeVisible();
  });

  test('shows validation errors for incomplete form', async ({ page }) => {
    await page.click('text=Submit Report');
    
    // Try to submit without filling
    await page.click('button:has-text("Next: Attachments")');
    
    // Should show validation errors
    await expect(page.locator('text=Category is required')).toBeVisible();
    await expect(page.locator('text=Title is required')).toBeVisible();
  });
});

test.describe('Moderator Review Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login as moderator
    await page.goto('http://localhost:3000/moderator/login');
    await page.click('button:has-text("Connect Wallet")');
    // Mock wallet connection
    await page.evaluate(() => {
      localStorage.setItem('auth-storage', JSON.stringify({
        isAuthenticated: true,
        role: 'moderator',
        address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb'
      }));
    });
  });

  test('moderator can review and accept report', async ({ page }) => {
    await page.goto('http://localhost:3000/moderator/queue');
    
    // Find first pending report
    const reportCard = page.locator('[data-testid="report-card"]').first();
    await reportCard.click('button:has-text("Review Report")');
    
    // Modal should open
    await expect(page.locator('text=Review Report')).toBeVisible();
    
    // Make decision
    await page.click('button:has-text("Accept")');
    await page.fill('textarea[name="notes"]', 'Report verified and credible');
    
    // Submit decision
    await page.click('button:has-text("Submit Decision")');
    
    // Should show success message
    await expect(
      page.locator('text=Decision submitted successfully')
    ).toBeVisible();
    
    // Report should be removed from queue
    await expect(reportCard).not.toBeVisible();
  });
});
```

## 4. Security Testing

### Security Test Suite

```python
# tests/security/test_authentication.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestAuthentication:
    async def test_unauthenticated_access_denied(self, client: AsyncClient):
        """Test that protected endpoints reject unauthenticated requests"""
        response = await client.get("/api/moderator/queue")
        assert response.status_code == 401

    async def test_expired_token_rejected(self, client: AsyncClient):
        """Test that expired JWT tokens are rejected"""
        expired_token = generate_expired_token()
        
        response = await client.get(
            "/api/moderator/queue",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401

    async def test_invalid_signature_rejected(self, client: AsyncClient):
        """Test that tokens with invalid signatures are rejected"""
        tampered_token = generate_token_with_invalid_signature()
        
        response = await client.get(
            "/api/moderator/queue",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )
        assert response.status_code == 401

    async def test_role_based_access_control(self, client: AsyncClient):
        """Test that reporters cannot access moderator endpoints"""
        reporter_token = generate_token(role="reporter")
        
        response = await client.get(
            "/api/moderator/queue",
            headers={"Authorization": f"Bearer {reporter_token}"}
        )
        assert response.status_code == 403
```

### Input Validation Tests

```python
# tests/security/test_input_validation.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestInputValidation:
    async def test_sql_injection_prevention(self, client: AsyncClient):
        """Test that SQL injection attempts are blocked"""
        malicious_input = "'; DROP TABLE reports; --"
        
        response = await client.post(
            "/api/reports/submit",
            json={
                "ipfs_cid": malicious_input,
                "commitment_hash": "0x" + "a" * 64,
                "encrypted_category": "test",
                "chain_id": 80001
            }
        )
        
        # Should be rejected due to validation
        assert response.status_code == 400

    async def test_xss_prevention(self, client: AsyncClient):
        """Test that XSS attempts are sanitized"""
        xss_payload = "<script>alert('XSS')</script>"
        
        response = await client.post(
            "/api/reports/submit",
            json={
                "ipfs_cid": "QmTest",
                "commitment_hash": "0x" + "a" * 64,
                "encrypted_category": xss_payload,
                "chain_id": 80001
            }
        )
        
        # Should be sanitized
        assert response.status_code in [201, 400]
        if response.status_code == 201:
            data = response.json()
            assert "<script>" not in data.get("encrypted_category", "")

    async def test_file_upload_validation(self, client: AsyncClient):
        """Test that dangerous file types are rejected"""
        # Attempt to upload .exe file
        files = {
            "file": ("malware.exe", b"MZ\x90\x00", "application/x-executable")
        }
        
        response = await client.post("/api/reports/upload", files=files)
        assert response.status_code == 400
        assert "file type" in response.json()["detail"].lower()
```

## 5. Performance Testing

### Load Testing with Locust

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between
import random

class ReporterUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        """Setup user session"""
        self.token = self.login()
    
    def login(self):
        """Authenticate user"""
        response = self.client.post("/api/auth/login", json={
            "address": f"0x{random.randbytes(20).hex()}"
        })
        return response.json()["token"]
    
    @task(3)
    def view_reports(self):
        """View list of reports"""
        self.client.get(
            "/api/reports",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def submit_report(self):
        """Submit new report"""
        payload = {
            "ipfs_cid": f"Qm{random.randbytes(23).hex()}",
            "commitment_hash": f"0x{random.randbytes(32).hex()}",
            "encrypted_category": "test",
            "visibility": random.choice(["private", "moderated", "public"]),
            "chain_id": 80001
        }
        
        self.client.post(
            "/api/reports/submit",
            json=payload,
            headers={"Authorization": f"Bearer {self.token}"}
        )

class ModeratorUser(HttpUser):
    wait_time = between(2, 8)
    
    @task
    def review_queue(self):
        """Check moderation queue"""
        self.client.get("/api/moderator/queue")
    
    @task
    def submit_decision(self):
        """Submit moderation decision"""
        # Implementation...
        pass
```

## 6. CI/CD Testing Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
        working-directory: ./frontend
      
      - name: Run unit tests
        run: npm run test:unit
        working-directory: ./frontend
      
      - name: Run coverage
        run: npm run test:coverage
        working-directory: ./frontend
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/coverage-final.json
          flags: frontend

  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: covert_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
        working-directory: ./backend
      
      - name: Run tests with coverage
        run: pytest --cov=app --cov-report=xml
        working-directory: ./backend
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/covert_test
          REDIS_URL: redis://localhost:6379
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend

  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Foundry
        uses: foundry-rs/foundry-toolchain@v1
      
      - name: Run tests
        run: forge test -vvv
        working-directory: ./contracts
      
      - name: Check coverage
        run: forge coverage
        working-directory: ./contracts

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright
        run: npx playwright install --with-deps
      
      - name: Run E2E tests
        run: npm run test:e2e
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Snyk security scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      
      - name: Run npm audit
        run: npm audit --audit-level=moderate
        working-directory: ./frontend
```

## 7. Test Data Management

### Factories for Test Data

```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from app.models import Report, Moderator, Moderation
from app.database import SessionLocal

class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = SessionLocal()
        sqlalchemy_session_persistence = "commit"

class ReportFactory(BaseFactory):
    class Meta:
        model = Report
    
    commitment_hash = factory.Faker('sha256')
    ipfs_cid = factory.Sequence(lambda n: f"Qm{n:064d}")
    status = "pending"
    visibility = "moderated"
    chain_id = 80001
    file_size = factory.Faker('random_int', min=1000, max=10000000)

class ModeratorFactory(BaseFactory):
    class Meta:
        model = Moderator
    
    wallet_address = factory.Faker('ethereum_address')
    reputation_score = factory.Faker('random_int', min=0, max=1000)
    tier = "silver"
    total_reviews = factory.Faker('random_int', min=0, max=100)
    is_active = True

class ModerationFactory(BaseFactory):
    class Meta:
        model = Moderation
    
    report = factory.SubFactory(ReportFactory)
    moderator = factory.SubFactory(ModeratorFactory)
    action = "review_started"
```

## Test Execution Commands

### Frontend

```bash
# Unit tests
npm run test:unit

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage

# E2E tests
npm run test:e2e

# E2E headed mode (see browser)
npm run test:e2e:headed
```

### Backend

```bash
# All tests
pytest

# Specific file
pytest tests/test_reports_api.py

# With coverage
pytest --cov=app --cov-report=html

# Verbose
pytest -v

# Stop on first failure
pytest -x

# Run only security tests
pytest -m security
```

### Smart Contracts

```bash
# All tests
forge test

# Verbose
forge test -vvv

# Specific test
forge test --match-test testSubmitCommitment

# Coverage
forge coverage

# Gas report
forge test --gas-report
```

## Coverage Reporting

### Coverage Thresholds

```json
{
  "coverageThreshold": {
    "global": {
      "branches": 75,
      "functions": 80,
      "lines": 80,
      "statements": 80
    },
    "./src/services/": {
      "branches": 90,
      "functions": 95,
      "lines": 95,
      "statements": 95
    }
  }
}
```

## Continuous Monitoring

### Test Metrics to Track

1. **Test Execution Time**: Should remain under 5 minutes for full suite
2. **Flaky Tests**: Identify and fix tests that fail intermittently
3. **Coverage Trends**: Monitor coverage over time
4. **Test-to-Code Ratio**: Maintain healthy ratio of test code to application code

### Reporting

- Generate coverage reports after each run
- Track test metrics in CI/CD dashboard
- Alert on coverage drops
- Weekly test health reports

---

This comprehensive testing strategy ensures C.O.V.E.R.T maintains high quality, security, and reliability throughout development and beyond.
