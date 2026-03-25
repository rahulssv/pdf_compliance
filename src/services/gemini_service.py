"""Gemini LLM integration service with enhanced error handling and validation"""
import os
import logging
import time
from typing import Optional, Dict, Any
import google.generativeai as genai
from src.config import Config

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini API with retry logic and caching"""
    
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model_name = Config.GEMINI_MODEL
        self.model = None
        self.is_initialized = False
        self._cache = {}  # Simple in-memory cache for responses
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(
                    self.model_name,
                    generation_config={
                        'temperature': Config.GEMINI_TEMPERATURE,
                        'max_output_tokens': Config.GEMINI_MAX_TOKENS,
                    }
                )
                
                # Test the connection
                self._validate_connection()
                self.is_initialized = True
                logger.info(f"✅ Gemini API initialized successfully with model: {self.model_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize Gemini API: {e}")
                self.model = None
                self.is_initialized = False
        else:
            logger.warning("⚠️ GEMINI_API_KEY not set. Using fallback responses.")
            self.is_initialized = False
    
    def _validate_connection(self):
        """Validate that the API key and model work"""
        try:
            test_response = self.model.generate_content(
                "Hello",
                generation_config={'max_output_tokens': 10}
            )
            
            # Handle both simple and complex response formats
            response_text = self._extract_response_text(test_response)
            
            if not response_text:
                raise Exception("No response text from Gemini API")
            
            logger.info("✅ Gemini API connection validated")
        except Exception as e:
            logger.error(f"❌ Gemini API validation failed: {e}")
            raise
    
    def generate_remediation(self, issue_description: str, standard: str, max_retries: int = 3) -> str:
        """
        Generate remediation guidance for an accessibility issue with retry logic
        
        Args:
            issue_description: Description of the accessibility issue
            standard: The standard being violated
            max_retries: Maximum number of retry attempts
            
        Returns:
            Remediation guidance text
        """
        if not self.is_initialized or not self.model:
            return self._fallback_remediation(issue_description, standard)
        
        # Check cache first
        cache_key = f"remediation:{issue_description}:{standard}"
        if cache_key in self._cache:
            logger.info("📦 Using cached remediation")
            return self._cache[cache_key]
        
        prompt = f"""You are an accessibility expert specializing in PDF document compliance.

PDF Accessibility Issue:
{issue_description}

Violated Standard: {standard}

Task: Provide specific, actionable remediation steps that a document author can follow to fix this issue.

Requirements:
- Be specific and technical
- Include tool names (e.g., Adobe Acrobat Pro) when relevant
- Focus on practical, implementable steps
- Keep it concise (2-4 sentences)
- Start directly with the action (no preamble like "To fix this...")

Remediation:"""

        for attempt in range(max_retries):
            try:
                logger.info(f"🤖 Calling Gemini API for remediation (attempt {attempt + 1}/{max_retries})...")
                
                response = self.model.generate_content(prompt)
                
                # Extract text from response (handle different formats)
                response_text = self._extract_response_text(response)
                
                if response_text and len(response_text.strip()) > 20:
                    result = response_text.strip()
                    logger.info(f"✅ Gemini response received ({len(result)} chars)")
                    
                    # Cache the result
                    self._cache[cache_key] = result
                    return result
                else:
                    logger.warning(f"⚠️ Empty or too short response (attempt {attempt + 1})")
                    
            except Exception as e:
                logger.error(f"❌ Gemini API error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt)  # Exponential backoff
                    logger.info(f"⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        # All retries failed, use fallback
        logger.warning("⚠️ All Gemini API attempts failed, using fallback")
        return self._fallback_remediation(issue_description, standard)
    
    def enhance_issue_description(self, raw_finding: str, standard: str) -> str:
        """
        Enhance a technical finding into a clear description
        
        Args:
            raw_finding: Raw technical finding
            standard: The relevant standard
            
        Returns:
            Enhanced description
        """
        if not self.is_initialized or not self.model:
            return raw_finding
        
        # Check cache
        cache_key = f"enhance:{raw_finding}:{standard}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        prompt = f"""Convert this technical PDF accessibility finding into a clear, user-friendly description:

Finding: {raw_finding}
Standard: {standard}

Provide a single clear sentence that explains what the issue is and why it matters for accessibility.
Do not include the standard reference in the description.

Description:"""

        try:
            response = self.model.generate_content(prompt)
            response_text = self._extract_response_text(response)
            
            if response_text:
                result = response_text.strip()
                self._cache[cache_key] = result
                return result
            else:
                return raw_finding
                
        except Exception as e:
            logger.error(f"❌ Gemini API error in enhance: {e}")
            return raw_finding
    
    def _extract_response_text(self, response) -> Optional[str]:
        """Extract text from Gemini API response handling different formats"""
        try:
            # Try simple text accessor first
            if hasattr(response, 'text'):
                return response.text
        except Exception as e:
            logger.debug(f"Simple text accessor failed: {e}")
        
        try:
            # Try candidates accessor (protobuf structure)
            if hasattr(response, 'candidates') and response.candidates:
                logger.debug(f"Found {len(response.candidates)} candidates")
                for idx, candidate in enumerate(response.candidates):
                    logger.debug(f"Processing candidate {idx}")
                    if hasattr(candidate, 'content'):
                        content = candidate.content
                        logger.debug(f"Candidate {idx} has content")
                        if hasattr(content, 'parts'):
                            # parts is a proto repeated field, iterate directly
                            text_parts = []
                            part_count = 0
                            for part in content.parts:
                                part_count += 1
                                logger.debug(f"Part {part_count}: {type(part)}")
                                if hasattr(part, 'text'):
                                    logger.debug(f"Part {part_count} has text: {part.text[:50]}")
                                    text_parts.append(part.text)
                            if text_parts:
                                result = ''.join(text_parts)
                                logger.debug(f"Extracted {len(result)} chars from parts")
                                return result
                            else:
                                logger.debug(f"No text parts found (checked {part_count} parts)")
        except Exception as e:
            logger.warning(f"Error extracting text from candidates: {e}")
        
        try:
            # Try parts accessor directly
            if hasattr(response, 'parts'):
                text_parts = []
                for part in response.parts:
                    if hasattr(part, 'text'):
                        text_parts.append(part.text)
                if text_parts:
                    return ''.join(text_parts)
        except Exception as e:
            logger.debug(f"Parts accessor failed: {e}")
        
        logger.warning("Could not extract text from any method")
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the Gemini service"""
        return {
            'initialized': self.is_initialized,
            'model': self.model_name if self.is_initialized else None,
            'cache_size': len(self._cache),
            'api_key_set': bool(self.api_key)
        }
    
    def _fallback_remediation(self, issue_description: str, standard: str) -> str:
        """
        Provide fallback remediation guidance when Gemini is unavailable
        
        Args:
            issue_description: Description of the issue
            standard: The standard being violated
            
        Returns:
            Fallback remediation text
        """
        # Map common issues to remediation guidance
        fallback_map = {
            'tag tree': 'Use Adobe Acrobat Pro or similar PDF authoring tool to add tags to the document structure. Enable the "Tagged PDF" option when creating the PDF from the source document. Verify the tag structure using the Accessibility Checker.',
            
            'language': 'Open the document properties and set the document language in the metadata. In Adobe Acrobat, go to File > Properties > Advanced and set the Language field to the appropriate language code (e.g., "en-US" for English).',
            
            'alternative text': 'Add meaningful Alt Text to each figure tag so a screen reader can announce the image purpose to non-visual users. Right-click on images in the Tags panel and select "Edit Alternate Text" to add descriptions.',
            
            'form field': 'Add a programmatic label or tooltip to each form field and verify the field name is announced correctly through keyboard navigation. Use the Forms editing tools to add proper labels and tooltips to all interactive elements.',
            
            'scanned': 'Run OCR (Optical Character Recognition) on the scanned document to create a searchable text layer. In Adobe Acrobat, use Tools > Enhance Scans > Recognize Text to add a text layer that assistive technology can read.',
            
            'metadata': 'Add complete document metadata including Title, Author, Subject, and Keywords. This information helps users understand the document content and improves discoverability for assistive technology users.',
            
            'structure': 'Review and correct the document structure using proper heading tags (H1-H6), paragraph tags, and list tags. Ensure the reading order matches the visual order and logical flow of content.'
        }
        
        # Find matching fallback based on keywords in description
        description_lower = issue_description.lower()
        for keyword, guidance in fallback_map.items():
            if keyword in description_lower:
                return guidance
        
        # Generic fallback
        return f'Review the document according to {standard} requirements. Use PDF accessibility tools to identify and fix the specific issue. Consider consulting WCAG 2.1 guidelines and PDF/UA standards for detailed remediation steps.'

