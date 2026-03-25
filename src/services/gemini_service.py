"""Gemini LLM integration service"""
import os
import logging
from typing import Optional
import google.generativeai as genai
from src.config import Config

# Configure logging
logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini API"""
    
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model_name = Config.GEMINI_MODEL
        self.model = None
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                logger.info("✅ Gemini API initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Gemini API: {e}")
                self.model = None
        else:
            logger.warning("⚠️ GEMINI_API_KEY not set. Using fallback responses.")
    
    def generate_remediation(self, issue_description: str, standard: str) -> str:
        """
        Generate remediation guidance for an accessibility issue
        
        Args:
            issue_description: Description of the accessibility issue
            standard: The standard being violated
            
        Returns:
            Remediation guidance text
        """
        if not self.model:
            return self._fallback_remediation(issue_description, standard)
        
        prompt = f"""You are an accessibility expert specializing in PDF document compliance.

Given the following PDF accessibility issue:

Issue: {issue_description}
Standard: {standard}

Provide a specific, actionable remediation step that a document author can follow to fix this issue. 
Be concise (2-3 sentences) but detailed enough to be useful. Focus on practical steps.

Do not include introductory phrases like "To fix this issue" - start directly with the action."""

        try:
            logger.info("🤖 Calling Gemini API for remediation...")
            logger.info(f"📝 Issue: {issue_description[:100]}...")
            logger.info(f"📋 Standard: {standard}")
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': Config.GEMINI_TEMPERATURE,
                    'max_output_tokens': Config.GEMINI_MAX_TOKENS,
                }
            )
            
            if response and response.text:
                logger.info(f"✅ Gemini response: {response.text[:100]}...")
                return response.text.strip()
            else:
                logger.warning("⚠️ No response text, using fallback")
                return self._fallback_remediation(issue_description, standard)
                
        except Exception as e:
            logger.error(f"❌ Gemini API error: {e}")
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
        if not self.model:
            return raw_finding
        
        prompt = f"""Convert this technical PDF accessibility finding into a clear, user-friendly description:

Finding: {raw_finding}
Standard: {standard}

Provide a single clear sentence that explains what the issue is and why it matters for accessibility.
Do not include the standard reference in the description."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.5,
                    'max_output_tokens': 200,
                }
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                return raw_finding
                
        except Exception as e:
            logger.error(f"❌ Gemini API error in enhance: {e}")
            return raw_finding
    
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

