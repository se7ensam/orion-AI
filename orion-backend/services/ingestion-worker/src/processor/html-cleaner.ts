export function cleanHtml(rawHtml: string): string {
    // Basic regex to remove HTML tags but preserve text
    // 1. Remove scripts and styles
    let text = rawHtml.replace(/<script\b[^>]*>([\s\S]*?)<\/script>/gim, "");
    text = text.replace(/<style\b[^>]*>([\s\S]*?)<\/style>/gim, "");

    // 2. Remove all other tags
    text = text.replace(/<[^>]+>/g, "\n");

    // 3. Normalize whitespace
    text = text.replace(/\s+/g, " ").trim();

    return text;
}
