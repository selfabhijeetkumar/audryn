// Indian Locale (en-IN) formatters and exact Decimal string helpers

/**
 * Formats a numeric string in Indian Rupees (₹) with Indian digit grouping (Lakhs / Crores).
 * Avoids JavaScript floating point math.
 */
export function formatINR(valStr: string | number, showSymbol = true): string {
  if (valStr === undefined || valStr === null || valStr === '') return '—';
  
  const raw = String(valStr).trim();
  const isNegative = raw.startsWith('-');
  const clean = isNegative ? raw.slice(1) : raw;
  
  const [intPart, decPart] = clean.split('.');
  
  // Indian numbering: last 3 digits, then groups of 2
  let formattedInt = '';
  if (intPart.length <= 3) {
    formattedInt = intPart;
  } else {
    const lastThree = intPart.slice(-3);
    const remaining = intPart.slice(0, -3);
    const groups: string[] = [];
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

/**
 * Truncates SHA-256 hash for tabular display while retaining accessibility
 */
export function truncateHash(hash: string, start = 8, end = 6): string {
  if (!hash || hash.length < start + end) return hash;
  return `${hash.slice(0, start)}...${hash.slice(-end)}`;
}

/**
 * Formats ISO timestamp to Indian Standard Time (IST) display
 */
export function formatIST(isoDateStr: string): string {
  try {
    const d = new Date(isoDateStr);
    return d.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    }) + ' IST';
  } catch {
    return isoDateStr;
  }
}
