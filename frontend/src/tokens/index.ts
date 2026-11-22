// Design Tokens for AUDRYN
// Governed by Gate 1 & Gate 2 Design Specifications

export const COLORS = {
  // Paper Environment (Default)
  paper: {
    base: '#F6F3EB',
    surface: '#FDFBF7',
    border: '#E8E4DC',
  },
  // Stage Environment (Dark)
  stage: {
    base: '#121110',
    surface: '#1A1816',
    border: '#2A2724',
    subtle: '#3A3632',
  },
  // Ink Hierarchy
  ink: {
    primary: '#1A1714',     // 16.10:1 on Paper (PASS SC 1.4.3)
    secondary: '#5C5752',   // 6.44:1 on Paper (PASS SC 1.4.3)
    muted: '#7A746A',       // UI borders (SC 1.4.11 UI >= 3:1)
    border: '#D8D4CC',
    disabled: '#9C968F',    // Decorative / disabled ONLY
  },
  // Signal Accents
  signal: {
    red: '#C0392B',         // Anomaly (4.90:1 on Paper)
    amber: '#B77F0A',       // Warning (3.13:1 on Paper - bold/large only)
    green: '#1A7A40',       // Clear / verified (4.85:1 on Paper)
  },
  // Brass — Human Sign-Off ONLY
  brass: {
    dark: '#7A5F2B',        // Brass text on Paper (5.41:1 PASS SC 1.4.3)
    light: '#B08D4F',       // Brass accent on Stage (6.08:1 PASS SC 1.4.3)
  },
} as const;

export const TYPOGRAPHY = {
  display: 'Newsreader, Georgia, serif',
  sans: 'IBM Plex Sans, -apple-system, sans-serif',
  mono: 'IBM Plex Mono, Menlo, monospace',
} as const;

export const MOTION = {
  duration: {
    micro: 120,
    state: 240,
    spatial: 480,
    hold: 700,
  },
  easing: {
    standard: 'cubic-bezier(0.2, 0.0, 0.0, 1.0)',
    exit: 'cubic-bezier(0.4, 0.0, 1.0, 1.0)',
  },
} as const;
