/**
 * Clean HTML by removing scripts, styles, and tags, then normalizing whitespace.
 * Optimized to minimize regex passes and memory allocations.
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

    // Decode common HTML entities for better text quality
    text = text
        .replace(/&nbsp;/g, " ")
        .replace(/&amp;/g, "&")
        .replace(/&lt;/g, "<")
        .replace(/&gt;/g, ">")
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&apos;/g, "'");

    // Normalize whitespace in single pass (multiple spaces/newlines/tabs -> single space)
    text = text.replace(/\s+/g, " ").trim();

    return text;
}
