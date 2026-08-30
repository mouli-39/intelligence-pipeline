EXTRACTION_SYSTEM_PROMPT = """You are a precise data extraction AI. 
Your job is to extract structured entities from raw web text.
Return ONLY a valid JSON object matching the requested schema. 
Do not include markdown blocks, explanation text, or conversational commentary.
If information for a field is completely missing, use null."""

STARTUP_EXTRACTION_PROMPT = """Extract startup entities from this text.
Target Schema Object keys:
- entityName (string, name of the startup)
- employeeCount (integer, total headcount or null)

Text to process:
{text_content}
"""
