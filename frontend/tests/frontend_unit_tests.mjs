// Frontend Unit Tests using Node 20+ built-in test runner
import test from 'node:test';
import assert from 'node:assert';
import { formatINR, truncateHash, formatIST } from '../src/utils/formatters.js';

test('formatINR formats currency according to Indian numbering system', () => {
  assert.strictEqual(formatINR('1000.00'), '₹ 1,000.00');
  assert.strictEqual(formatINR('4500000.00'), '₹ 45,00,000.00');
  assert.strictEqual(formatINR('124567890.00'), '₹ 12,45,67,890.00');
  assert.strictEqual(formatINR('-500000.00'), '- ₹ 5,00,000.00');
  assert.strictEqual(formatINR(''), '—');
});

test('truncateHash shortens SHA-256 hashes gracefully', () => {
  const hash = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';
  assert.strictEqual(truncateHash(hash, 8, 6), 'e3b0c442...52b855');
  assert.strictEqual(truncateHash('short'), 'short');
});

test('formatIST formats ISO date with IST timezone', () => {
  const iso = '2024-04-12T10:15:00Z';
  const formatted = formatIST(iso);
  assert.ok(formatted.includes('IST'), 'Must include IST timezone designation');
});
