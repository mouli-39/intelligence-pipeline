from typing import List

class IntelligentChunker:
    """Handles HTTP 413 errors by chunking large pages into smaller pieces."""
    
    @staticmethod
    def chunk_text_by_words(text: str, max_words: int = 1500) -> List[str]:
        """Splits large scraped text blocks safely by word boundaries."""
        words = text.split()
        if len(words) <= max_words:
            return [text]
            
        chunks = []
        for i in range(0, len(words), max_words):
            chunk_words = words[i:i + max_words]
            chunks.append(" ".join(chunk_words))
        return chunks
