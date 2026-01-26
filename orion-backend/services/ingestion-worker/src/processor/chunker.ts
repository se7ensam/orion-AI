export class Chunker {
    /**
     * Chunk text into fixed-size pieces.
     * Optimized with pre-allocated array for better performance.
     * 
     * @param text - The text to chunk
     * @param chunkSize - Size of each chunk in characters (default: 1000)
     * @returns Array of text chunks
     */
    static chunkText(text: string, chunkSize: number = 1000): string[] {
        // Early return for empty input
        if (!text || text.length === 0) {
            return [];
        }

        // Validate chunk size
        if (chunkSize <= 0) {
            throw new Error('Chunk size must be positive');
        }
        
        // Pre-allocate array with exact size for optimal performance
        // Math.ceil ensures we have enough space for the last partial chunk
        const numChunks = Math.ceil(text.length / chunkSize);
        const chunks: string[] = new Array(numChunks);
        
        let chunkIndex = 0;
        for (let i = 0; i < text.length; i += chunkSize) {
            chunks[chunkIndex++] = text.slice(i, i + chunkSize);
        }
        
        // No need to slice - our calculation is exact and chunkIndex === numChunks
        return chunks;
    }
}
