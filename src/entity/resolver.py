import re
from typing import Dict, Tuple
from src.utils.logging import setup_logger

logger = setup_logger("entity_resolver")

class EntityResolver:
    """High-throughput text resolution engine to deduplicate variation names deterministically."""
    
    def __init__(self):
        # Noise expressions to remove before standardizing comparisons
        self.noise_pattern = re.compile(
            r"\b(inc|incorporated|llc|corp|corporation|co|company|ltd|limited|labs|software|ai|tech)\b", 
            re.IGNORECASE
        )
        # Keeps track of all processed names and what they mapped to
        self.resolution_log: Dict[str, str] = {}
        # Stores the true canonical names we want to match against
        self.canonical_registry: Dict[str, str] = {}

    def clean_token(self, name: str) -> str:
        """Removes punctuation, spaces, and corporate noise suffixes."""
        if not name:
            return ""
        # Convert to lowercase and strip punctuation
        lowered = name.lower().strip()
        no_punct = re.sub(r"[^\w\s]", "", lowered)
        # Strip out corporate noise words
        no_noise = self.noise_pattern.sub("", no_punct)
        # Remove all remaining white space
        return "".join(no_noise.split())

    def resolve_entity(self, raw_name: str) -> Tuple[str, bool]:
        """Maps an unverified raw string name to a clean, canonical name.
        
        Returns:
            Tuple[str, bool]: The clean name, and a boolean indicating if it is a new entity.
        """
        if not raw_name:
            return "Unknown Entity", False
            
        token = self.clean_token(raw_name)
        if not token:
            return raw_name.strip(), False

        # Look for an existing match in our registry
        if token in self.canonical_registry:
            canonical_name = self.canonical_registry[token]
            self.resolution_log[raw_name.strip()] = canonical_name
            return canonical_name, False

        # If it's a brand new name, establish a clean capitalization format
        # Strip common trailing commas before saving
        clean_display = raw_name.strip().rstrip(",.")
        # Filter out obvious trailing noise from the presentation label
        clean_display = re.sub(r",?\s+(Inc|LLC|Corp|Ltd|AI|Tech)\.?$", "", clean_display, flags=re.IGNORECASE).strip()
        
        self.canonical_registry[token] = clean_display
        self.resolution_log[raw_name.strip()] = clean_display
        return clean_display, True
