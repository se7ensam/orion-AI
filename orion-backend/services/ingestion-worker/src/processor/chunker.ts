export class Chunker {
    /**
     * Chunk text into fixed-size pieces.
     * Optimized to pre-allocate array size for better performance.
     */
    static chunkText(text: string, chunkSize: number = 1000): string[] {
        if (text.length === 0) {
            return [];
        }
        
        // Pre-allocate array with known size for better performance
        const estimatedChunks = Math.ceil(text.length / chunkSize);
        const chunks: string[] = new Array(estimatedChunks);
        
        let chunkIndex = 0;
        for (let i = 0; i < text.length; i += chunkSize) {
            chunks[chunkIndex++] = text.slice(i, i + chunkSize);
        }
        
        // Trim array if we over-allocated (shouldn't happen, but safe)
        return chunks.slice(0, chunkIndex);
    }
}
