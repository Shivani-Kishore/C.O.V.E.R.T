/**
 * Test setup file for Vitest
 */

import { afterEach } from 'vitest';

// Clean up after each test
afterEach(() => {
  // Clear localStorage
  localStorage.clear();
});

// Mock Web Crypto API if not available in test environment
if (!globalThis.crypto || !globalThis.crypto.subtle) {
  const { Crypto } = require('@peculiar/webcrypto');
  globalThis.crypto = new Crypto();
}
