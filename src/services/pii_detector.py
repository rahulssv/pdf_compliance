"""
PII Detection Service
Automatically identifies and flags Personally Identifiable Information in PDF content
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from src.utils.pii_patterns import PIIPatterns, PIIPattern, mask_pii

logger = logging.getLogger(__name__)


@dataclass
class PIIMatch:
    """Represents a detected PII instance"""
    type: str
    category: str
    severity: str
    original: str
    masked: str
    location: str
    confidence: float
    start_pos: int
    end_pos: int


class PIIDetector:
    """
    Service for detecting PII in text content
    Supports 15+ PII types with configurable sensitivity
    """
    
    def __init__(self, sensitivity: str = 'high'):
        """
        Initialize PII detector
        
        Args:
            sensitivity: Detection sensitivity ('high', 'medium', 'low')
                        - high: Detect all patterns including low severity
                        - medium: Detect medium and high severity only
                        - low: Detect high severity only
        """
        self.sensitivity = sensitivity
        self.patterns = self._get_patterns_by_sensitivity()
        self._detection_cache = {}
        
        logger.info(f"✅ PIIDetector initialized with {len(self.patterns)} patterns (sensitivity: {sensitivity})")
    
    def _get_patterns_by_sensitivity(self) -> List[PIIPattern]:
        """Get patterns based on sensitivity level"""
        all_patterns = PIIPatterns.get_all_patterns()
        
        if self.sensitivity == 'low':
            return [p for p in all_patterns if p.severity == 'high']
        elif self.sensitivity == 'medium':
            return [p for p in all_patterns if p.severity in ['high', 'medium']]
        else:  # high sensitivity
            return all_patterns
    
    def detect_pii(self, text: str, page_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Detect PII in text content
        
        Args:
            text: Text content to analyze
            page_number: Optional page number for location tracking
        
        Returns:
            {
                'detected': bool,
                'count': int,
                'categories': List[str],
                'details': List[Dict],
                'summary': Dict
            }
        """
        if not text or not text.strip():
            return self._empty_result()
        
        # Check cache
        cache_key = hash(text)
        if cache_key in self._detection_cache:
            logger.debug("📦 Using cached PII detection result")
            return self._detection_cache[cache_key]
        
        matches: List[PIIMatch] = []
        
        # Scan text with each pattern
        for pattern in self.patterns:
            pattern_matches = self._scan_pattern(text, pattern, page_number)
            matches.extend(pattern_matches)
        
        # Remove duplicates and overlapping matches
        matches = self._deduplicate_matches(matches)
        
        # Build result
        result = self._build_result(matches)
        
        # Cache result
        self._detection_cache[cache_key] = result
        
        if result['detected']:
            logger.info(f"🔍 Detected {result['count']} PII instance(s): {', '.join(result['categories'])}")
        
        return result
    
    def _scan_pattern(
        self, 
        text: str, 
        pattern: PIIPattern, 
        page_number: Optional[int]
    ) -> List[PIIMatch]:
        """Scan text for a specific PII pattern"""
        matches = []
        
        for match in pattern.pattern.finditer(text):
            original_text = match.group(0)
            masked_text = mask_pii(original_text, pattern)
            
            # Determine location
            location = f"page {page_number}" if page_number else "document"
            
            # Calculate confidence (can be enhanced with ML)
            confidence = self._calculate_confidence(original_text, pattern)
            
            pii_match = PIIMatch(
                type=pattern.name,
                category=pattern.category,
                severity=pattern.severity,
                original=original_text,
                masked=masked_text,
                location=location,
                confidence=confidence,
                start_pos=match.start(),
                end_pos=match.end()
            )
            
            matches.append(pii_match)
        
        return matches
    
    def _calculate_confidence(self, text: str, pattern: PIIPattern) -> float:
        """
        Calculate confidence score for PII match
        
        Simple heuristic-based scoring. Can be enhanced with ML models.
        """
        confidence = 0.85  # Base confidence
        
        # Adjust based on pattern type
        if pattern.name in ['SSN', 'CREDIT_CARD']:
            # High confidence for well-defined patterns
            confidence = 0.95
        elif pattern.name in ['FULL_NAME', 'STREET_ADDRESS']:
            # Lower confidence for ambiguous patterns
            confidence = 0.70
        
        # Adjust based on text length
        if len(text) < 5:
            confidence *= 0.8
        
        return min(confidence, 1.0)
    
    def _deduplicate_matches(self, matches: List[PIIMatch]) -> List[PIIMatch]:
        """Remove duplicate and overlapping matches"""
        if not matches:
            return matches
        
        # Sort by start position
        sorted_matches = sorted(matches, key=lambda m: m.start_pos)
        
        deduplicated = []
        last_end = -1
        
        for match in sorted_matches:
            # Skip if overlaps with previous match
            if match.start_pos < last_end:
                # Keep the one with higher confidence
                if deduplicated and match.confidence > deduplicated[-1].confidence:
                    deduplicated[-1] = match
                    last_end = match.end_pos
                continue
            
            deduplicated.append(match)
            last_end = match.end_pos
        
        return deduplicated
    
    def _build_result(self, matches: List[PIIMatch]) -> Dict[str, Any]:
        """Build detection result from matches"""
        if not matches:
            return self._empty_result()
        
        # Extract unique categories
        categories = list(set(m.type for m in matches))
        
        # Group by category
        by_category = {}
        for match in matches:
            if match.category not in by_category:
                by_category[match.category] = 0
            by_category[match.category] += 1
        
        # Group by severity
        by_severity = {}
        for match in matches:
            if match.severity not in by_severity:
                by_severity[match.severity] = 0
            by_severity[match.severity] += 1
        
        return {
            'detected': True,
            'count': len(matches),
            'categories': sorted(categories),
            'details': [asdict(m) for m in matches],
            'summary': {
                'by_category': by_category,
                'by_severity': by_severity,
                'high_severity_count': by_severity.get('high', 0),
                'unique_types': len(categories)
            }
        }
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result when no PII detected"""
        return {
            'detected': False,
            'count': 0,
            'categories': [],
            'details': [],
            'summary': {
                'by_category': {},
                'by_severity': {},
                'high_severity_count': 0,
                'unique_types': 0
            }
        }
    
    def redact_pii(self, text: str) -> str:
        """
        Redact all PII from text
        
        Args:
            text: Original text
        
        Returns:
            Text with PII redacted
        """
        detection_result = self.detect_pii(text)
        
        if not detection_result['detected']:
            return text
        
        # Sort matches by position (reverse order to maintain positions)
        matches = sorted(
            detection_result['details'],
            key=lambda m: m['start_pos'],
            reverse=True
        )
        
        redacted_text = text
        for match in matches:
            start = match['start_pos']
            end = match['end_pos']
            redacted_text = redacted_text[:start] + match['masked'] + redacted_text[end:]
        
        return redacted_text
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics"""
        return {
            'sensitivity': self.sensitivity,
            'active_patterns': len(self.patterns),
            'cache_size': len(self._detection_cache),
            'patterns_by_category': {
                'financial': len([p for p in self.patterns if p.category == 'financial']),
                'personal': len([p for p in self.patterns if p.category == 'personal']),
                'medical': len([p for p in self.patterns if p.category == 'medical']),
                'government': len([p for p in self.patterns if p.category == 'government']),
                'technical': len([p for p in self.patterns if p.category == 'technical'])
            }
        }
    
    def clear_cache(self):
        """Clear detection cache"""
        self._detection_cache.clear()
        logger.info("🗑️ PII detection cache cleared")

