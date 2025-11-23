/**
 * Utility functions
 */

/**
 * Format CIK with leading zeros
 */
export function formatCik(cik: string | number): string {
    return String(cik).padStart(10, '0');
}

