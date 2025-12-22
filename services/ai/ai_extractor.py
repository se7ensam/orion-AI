"""
AI-based Entity and Relationship Extractor

Uses LLM to extract person-company relationships from EDGAR filings.
"""

import json
import os
import subprocess
import time
import logging
from typing import Dict, List, Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger(__name__)


class AIRelationshipExtractor:
    """Extract person-company relationships using AI."""
    
    def __init__(self, model_name: str = "llama3.2", base_url: Optional[str] = None):
        """
        Initialize AI extractor.
        
        Args:
            model_name: Name of the Ollama model to use (default: "llama3.2")
            base_url: Base URL for Ollama API (default: http://localhost:11434)
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name
        
        # Initialize parser and prompt template (always needed)
        self.json_parser = JsonOutputParser()
        
        # Prompt template for extracting person-company relationships
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Extract person-company employment relationships from SEC EDGAR filing text.

CRITICAL: Return ONLY valid JSON array, no other text. Format:
[
  {{"name": "Full Name", "title": "Job Title", "company": "Company Name", "role_type": "CEO|Director|Officer|Executive|Signatory|Contact|Other"}}
]

Rules:
- Extract signatories, executives, directors, officers, contacts
- Use exact names/titles from document
- If company not mentioned, use filing company
- Return [] if none found
- Return ONLY the JSON array, no explanations or markdown
- Ensure all JSON is properly closed with brackets"""),
            ("human", """Company Information:
- Filing Company: {company_name}
- CIK: {cik}

Filing Content:
{content}

Extract all person-company employment relationships from this filing.""")
        ])
        
        # Ensure model is available, download if needed
        # This may update self.model_name if fallback is used
        if not self._ensure_model_available(model_name):
            logger.warning("Could not ensure model availability. LLM may not work.")
        
        try:
            self.llm = ChatOllama(
                model=self.model_name,  # Use potentially updated model name
                base_url=self.base_url,
                temperature=0.0,  # Zero temperature for faster, more deterministic responses
                num_ctx=2048,  # Reduce context window for faster processing
            )
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                logger.warning(f"Model '{self.model_name}' not found. Attempting download...")
                if self._ensure_model_available(self.model_name):
                    try:
                        self.llm = ChatOllama(
                            model=self.model_name,
                            base_url=self.base_url,
                            temperature=0.0,
                            num_ctx=2048,
                        )
                    except Exception as retry_e:
                        logger.warning(f"Could not initialize Ollama LLM after download: {retry_e}")
                        logger.warning("Falling back to pattern-based extraction.")
                        self.llm = None
                else:
                    logger.warning(f"Could not download model '{self.model_name}'")
                    logger.warning("Falling back to pattern-based extraction.")
                    self.llm = None
            else:
                logger.warning(f"Could not initialize Ollama LLM: {e}")
                logger.warning("Falling back to pattern-based extraction.")
                self.llm = None
    
    def _ensure_model_available(self, model_name: str) -> bool:
        """
        Check if model is available, and download it if not.
        
        Args:
            model_name: Name of the model to check/download
            
        Returns:
            True if model is available, False otherwise
        """
        try:
            # Check if model exists by listing available models
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Check if model is in the list
                model_available = model_name in result.stdout or f"{model_name}:" in result.stdout
                
                if not model_available:
                    logger.info(f"Model '{model_name}' not found. Downloading...")
                    logger.info(f"This may take a few minutes depending on model size...")
                    
                    # Download the model
                    download_result = subprocess.run(
                        ['ollama', 'pull', model_name],
                        capture_output=True,
                        text=True
                    )
                    
                    if download_result.returncode == 0:
                        logger.info(f"Successfully downloaded model '{model_name}'")
                        return True
                    else:
                        error_msg = download_result.stderr or download_result.stdout
                        logger.error(f"Failed to download model '{model_name}': {error_msg}")
                        
                        # If model name has a tag (e.g., "llama3.2:1b"), try without tag
                        if ':' in model_name:
                            base_model = model_name.split(':')[0]
                            logger.info(f"Trying base model '{base_model}' instead...")
                            self.model_name = base_model
                            return self._ensure_model_available(base_model)
                        
                        # Try to use default model
                        if model_name != "llama3.2":
                            logger.warning(f"Falling back to default model 'llama3.2'")
                            self.model_name = "llama3.2"
                            return self._ensure_model_available("llama3.2")
                        return False
                else:
                    return True
            else:
                logger.warning(f"Could not check Ollama models: {result.stderr}")
                return False
                
        except FileNotFoundError:
            logger.warning("'ollama' command not found. Please ensure Ollama is installed.")
            return False
        except subprocess.TimeoutExpired:
            logger.warning("Timeout checking Ollama models.")
            return False
        except Exception as e:
            logger.warning(f"Error checking model availability: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if AI extraction is available."""
        return self.llm is not None
    
    def _extract_relevant_sections(self, content: str, max_length: int = 5000) -> str:
        """
        Extract only relevant sections that likely contain person-company relationships.
        This significantly reduces the content sent to LLM.
        """
        import re
        
        # Keywords that indicate sections with person information
        relevant_keywords = [
            r'(?i)(signature|signed|by\s*/\s*s\s*/)',
            r'(?i)(director|officer|executive|chief|president|ceo|cfo|coo)',
            r'(?i)(contact\s*(?:person|information)?|investor\s*relations)',
            r'(?i)(board\s*of\s*directors|management|leadership)',
        ]
        
        # Split content into lines
        lines = content.split('\n')
        relevant_lines = []
        seen_positions = set()
        
        # Find lines containing relevant keywords
        for i, line in enumerate(lines):
            for pattern in relevant_keywords:
                if re.search(pattern, line):
                    # Include this line and surrounding context (2 lines before/after)
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    for j in range(start, end):
                        if j not in seen_positions:
                            relevant_lines.append((j, lines[j]))
                            seen_positions.add(j)
                    break
        
        # Also include the first 50 lines (header usually has key info)
        for i in range(min(50, len(lines))):
            if i not in seen_positions:
                relevant_lines.append((i, lines[i]))
                seen_positions.add(i)
        
        # Sort by line number and reconstruct
        relevant_lines.sort(key=lambda x: x[0])
        extracted = '\n'.join([line for _, line in relevant_lines])
        
        # Truncate if still too long
        if len(extracted) > max_length:
            extracted = extracted[:max_length] + "\n\n[... content truncated ...]"
        
        return extracted if extracted else content[:max_length]
    
    def extract_relationships(
        self, 
        filing_data: Dict, 
        company_name: str, 
        company_cik: str,
        max_content_length: int = 5000
    ) -> List[Dict]:
        """
        Extract person-company relationships from filing using AI.
        
        Args:
            filing_data: Filing data dictionary with 'raw_text' and/or 'html_content'
            company_name: Name of the filing company
            company_cik: CIK of the filing company
            max_content_length: Maximum length of content to send to LLM (reduced for speed)
            
        Returns:
            List of dictionaries with person-company relationship data
        """
        if not self.is_available():
            return []
        
        # Combine content sources
        content = filing_data.get('raw_text', '') + filing_data.get('html_content', '')
        
        if not content:
            return []
        
        # Extract only relevant sections instead of full content
        content = self._extract_relevant_sections(content, max_content_length)
        
        try:
            # Create the prompt
            prompt = self.prompt_template.format_messages(
                company_name=company_name or "Unknown Company",
                cik=company_cik,
                content=content
            )
            
            # Get response from LLM
            try:
                response = self.llm.invoke(prompt)
            except Exception as llm_error:
                error_msg = str(llm_error)
                # If model not found, try to download it
                if "404" in error_msg or "not found" in error_msg.lower():
                    logger.warning(f"Model '{self.model_name}' not found during extraction. Attempting download...")
                    if self._ensure_model_available(self.model_name):
                        # Retry the call
                        response = self.llm.invoke(prompt)
                    else:
                        raise llm_error
                else:
                    raise llm_error
            
            # Parse JSON response
            response_text = response.content.strip()
            
            # Try to extract JSON from markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON with multiple fallback strategies
            relationships = None
            try:
                relationships = json.loads(response_text)
            except json.JSONDecodeError:
                # Strategy 1: Try to find JSON array in the response
                import re
                json_match = re.search(r'\[[\s\S]*?\]', response_text, re.DOTALL)
                if json_match:
                    try:
                        relationships = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        pass
                
                # Strategy 2: Try to fix common JSON issues
                if relationships is None:
                    # Remove any text before first [
                    cleaned = re.sub(r'^[^[]*', '', response_text)
                    # Remove any text after last ]
                    cleaned = re.sub(r'[^\]]*$', '', cleaned)
                    # Try to close any unclosed brackets
                    open_brackets = cleaned.count('[') - cleaned.count(']')
                    if open_brackets > 0:
                        cleaned += ']' * open_brackets
                    elif open_brackets < 0:
                        cleaned = '[' * abs(open_brackets) + cleaned
                    
                    try:
                        relationships = json.loads(cleaned)
                    except json.JSONDecodeError:
                        pass
                
                # Strategy 3: Try to extract individual JSON objects and wrap in array
                if relationships is None:
                    objects = re.findall(r'\{[^{}]*"name"[^{}]*\}', response_text, re.DOTALL)
                    if objects:
                        try:
                            parsed_objects = [json.loads(obj) for obj in objects]
                            relationships = parsed_objects
                        except json.JSONDecodeError:
                            pass
                
                # If all strategies fail, log and return empty
                if relationships is None:
                    # Only show first 300 chars to avoid cluttering output
                    preview = response_text[:300].replace('\n', ' ')
                    if len(response_text) > 300:
                        preview += "..."
                    logger.warning(f"Could not parse JSON from LLM response (showing first 300 chars): {preview}")
                    return []
            
            # Validate and normalize the response
            if not isinstance(relationships, list):
                return []
            
            # Normalize relationships
            normalized = []
            for rel in relationships:
                if not isinstance(rel, dict):
                    continue
                
                name = rel.get('name', '').strip()
                title = rel.get('title', '').strip()
                company = rel.get('company', company_name).strip()
                role_type = rel.get('role_type', 'Other').strip()
                
                if name and len(name) > 2:
                    normalized.append({
                        'name': name,
                        'title': title or 'Unknown Title',
                        'company': company or company_name,
                        'role_type': role_type or 'Other'
                    })
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error in AI extraction: {e}")
            return []


def create_ai_extractor(model_name: Optional[str] = None, base_url: Optional[str] = None) -> AIRelationshipExtractor:
    """
    Factory function to create an AI extractor.
    
    Args:
        model_name: Ollama model name (default from env or "llama3.2")
        base_url: Ollama base URL (default from env or "http://localhost:11434")
        
    Returns:
        AIRelationshipExtractor instance
    """
    model = model_name or os.getenv("OLLAMA_MODEL", "llama3.2")
    url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    return AIRelationshipExtractor(model_name=model, base_url=url)

