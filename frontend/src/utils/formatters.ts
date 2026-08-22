/**
 * Shared utility for normalizing and formatting confidence values.
 * 
 * Rules:
 * - If the value is missing, return 'Not Available'
 * - If the value is a normalized float (<= 1.0), multiply by 100
 * - If the value is already a percentage (> 1.0), cap it at 100
 * - Ensures values like 5000%, 230%, or 0.83% are never displayed.
 */
export const formatConfidence = (val: number | string | undefined | null): string => {
  if (val === undefined || val === null || val === 'UNAVAILABLE' || val === 'DATA_UNAVAILABLE') return 'Not Available';
  if (typeof val === 'string') return val; // If it's a valid string but not UNAVAILABLE, pass it through
  let norm = val;
  if (norm <= 1) {
    norm = norm * 100;
  }
  
  if (norm > 100) norm = 100;
  if (norm < 0) norm = 0;
  
  return `${norm.toFixed(0)}%`;
};

/**
 * Returns the normalized numeric value (0-100) for use in progress bars.
 */
export const getNormalizedConfidenceValue = (val: number | string | undefined | null): number => {
  if (val === undefined || val === null || val === 'UNAVAILABLE' || val === 'DATA_UNAVAILABLE') return 0;
  let norm = typeof val === 'string' ? parseFloat(val) || 0 : val;
  if (norm <= 1) norm = norm * 100;
  if (norm > 100) norm = 100;
  if (norm < 0) norm = 0;
  return norm;
};
