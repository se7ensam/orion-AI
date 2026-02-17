/**
 * HTML entity lookup table for faster decoding.
 * Pre-compiled regex for single-pass entity replacement.
 */
const HTML_ENTITIES: Record<string, string> = {
    'nbsp': ' ',
    'amp': '&',
    'lt': '<',
    'gt': '>',
    'quot': '"',
    '#39': "'",
    'apos': "'",
    'ldquo': '"',
    'rdquo': '"',
    'lsquo': "'",
    'rsquo': "'",
    'mdash': '—',
    'ndash': '–',
    'hellip': '...',
};

// Pre-compile regex for entity matching (compiled once, reused)
const ENTITY_REGEX = /&(nbsp|amp|lt|gt|quot|#39|apos|ldquo|rdquo|lsquo|rsquo|mdash|ndash|hellip);/g;

/**
 * Clean HTML by removing scripts, styles, and tags, then normalizing whitespace.
 * Optimized with pre-compiled regex and lookup table for entity decoding.
 */
export function cleanHtml(rawHtml: string): string {
    // Early return for empty input
    if (!rawHtml || rawHtml.length === 0) {
        return '';
    }

    // Combined single-pass regex for scripts and styles
    // Using combined pattern reduces regex engine overhead
    let text = rawHtml.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi, " ");

    // Remove all other HTML tags, replace with space to preserve word boundaries
    text = text.replace(/<[^>]+>/g, " ");

    // Decode HTML entities using lookup table (single pass, faster than multiple replace calls)
    text = text.replace(ENTITY_REGEX, (match, entity) => HTML_ENTITIES[entity] || match);

    // Normalize whitespace in single pass (multiple spaces/newlines/tabs -> single space)
    text = text.replace(/\s+/g, " ").trim();

    return text;
}

/**
 * Get statistics about HTML cleaning (for monitoring)
 */
export function getCleaningStats(rawHtml: string, cleanText: string) {
    return {
        originalSize: rawHtml.length,
        cleanedSize: cleanText.length,
        compressionRatio: (1 - cleanText.length / rawHtml.length) * 100,
        removedBytes: rawHtml.length - cleanText.length,
    };
}
