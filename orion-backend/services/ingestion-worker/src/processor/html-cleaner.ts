export function cleanHtml(rawHtml: string): string {
    // Optimized HTML cleaning with single-pass where possible
    // 1. Remove scripts and styles (non-greedy, case-insensitive)
    let text = rawHtml.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "");
    text = text.replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, "");

    // 2. Remove all other HTML tags, replace with space to preserve word boundaries
    text = text.replace(/<[^>]+>/g, " ");

    // 3. Normalize whitespace (replace multiple spaces/newlines with single space)
    text = text.replace(/\s+/g, " ").trim();

    return text;
}
