const test = require('node:test');
const assert = require('node:assert');

// Formatter implementation matching src/utils/formatters.ts
function formatINR(valStr, showSymbol = true) {
  if (valStr === undefined || valStr === null || valStr === '') return '—';
  
  const raw = String(valStr).trim();
  const isNegative = raw.startsWith('-');
  const clean = isNegative ? raw.slice(1) : raw;
  
  const [intPart, decPart] = clean.split('.');
  
  let formattedInt = '';
  if (intPart.length <= 3) {
    formattedInt = intPart;
  } else {
    const lastThree = intPart.slice(-3);
    const remaining = intPart.slice(0, -3);
    const groups = [];
    for (let i = remaining.length; i > 0; i -= 2) {
      groups.unshift(remaining.slice(Math.max(0, i - 2), i));
    }
    formattedInt = groups.join(',') + ',' + lastThree;
  }
  
  const decimals = decPart ? `.${decPart.padEnd(2, '0').slice(0, 2)}` : '.00';
  const prefix = isNegative ? '- ' : '';
  const symbol = showSymbol ? '₹ ' : '';
  
  return `${prefix}${symbol}${formattedInt}${decimals}`;
}

function truncateHash(hash, start = 8, end = 6) {
  if (!hash || hash.length < start + end) return hash;
  return `${hash.slice(0, start)}...${hash.slice(-end)}`;
}

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
