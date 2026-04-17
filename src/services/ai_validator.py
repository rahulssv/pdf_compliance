"""
AI Output Validation Framework
Multi-layer validation system for Gemini AI outputs with confidence scoring
"""
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result from a single validation method"""
    score: float  # 0-100
    method: str
    details: List[str]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConfidenceScore:
    """Final confidence score with breakdown"""
    overall_score: float  # 0-100
    confidence_level: str  # very_high, high, medium, low, very_low
    breakdown: Dict[str, Dict[str, Any]]
    recommendation: str
    fallback_recommended: bool


class RuleBasedValidator:
    """Validate AI output against accessibility standards database"""
    
    def __init__(self):
        self.standards_db = {
            'WCAG 2.1 SC 1.1.1': {
                'keywords': ['alternative text', 'alt text', 'image description', 'figure'],
                'required_actions': ['add', 'provide', 'include', 'create'],
                'tools': ['Adobe Acrobat', 'PDF editor', 'Acrobat Pro']
            },
            'WCAG 2.1 SC 3.1.1': {
                'keywords': ['language', 'lang attribute', 'document language', 'metadata'],
                'required_actions': ['set', 'declare', 'specify', 'add'],
                'tools': ['document properties', 'metadata', 'Acrobat']
            },
            'PDF/UA-1 §7.1': {
                'keywords': ['tag tree', 'structure', 'tagged PDF', 'tags'],
                'required_actions': ['create', 'add', 'enable', 'generate'],
                'tools': ['Adobe Acrobat Pro', 'PDF authoring', 'Acrobat']
            },
            'WCAG 2.1 SC 1.3.1': {
                'keywords': ['form field', 'label', 'tooltip', 'accessible name'],
                'required_actions': ['add', 'provide', 'associate', 'link'],
                'tools': ['Forms', 'Acrobat', 'PDF editor']
            }
        }
    
    def validate(self, ai_output: str, issue_context: Dict) -> ValidationResult:
        """Validate AI output against standard requirements"""
        standard = issue_context.get('standard', '')
        score = 0
        details = []
        
        # Find matching standard
        standard_key = self._find_standard_key(standard)
        
        if standard_key and standard_key in self.standards_db:
            requirements = self.standards_db[standard_key]
            
            # Check for required keywords (40 points)
            keyword_score = self._check_keywords(ai_output, requirements['keywords'])
            score += keyword_score * 0.4
            details.append(f"Keyword check: {keyword_score:.1f}/100")
            
            # Check for actionable verbs (30 points)
            action_score = self._check_actions(ai_output, requirements['required_actions'])
            score += action_score * 0.3
            details.append(f"Action verbs: {action_score:.1f}/100")
            
            # Check for tool mentions (30 points)
            tool_score = self._check_tools(ai_output, requirements['tools'])
            score += tool_score * 0.3
            details.append(f"Tool mentions: {tool_score:.1f}/100")
        else:
            # Unknown standard - moderate confidence
            score = 50
            details.append("Standard not in validation database")
        
        return ValidationResult(
            score=score,
            method='rule_based',
            details=details
        )
    
    def _find_standard_key(self, standard: str) -> Optional[str]:
        """Find matching standard key"""
        for key in self.standards_db.keys():
            if key in standard or standard in key:
                return key
        return None
    
    def _check_keywords(self, text: str, keywords: List[str]) -> float:
        """Check for presence of required keywords"""
        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        return (matches / len(keywords)) * 100 if keywords else 0
    
    def _check_actions(self, text: str, actions: List[str]) -> float:
        """Check for actionable verbs"""
        text_lower = text.lower()
        matches = sum(1 for action in actions if action.lower() in text_lower)
        return (matches / len(actions)) * 100 if actions else 0
    
    def _check_tools(self, text: str, tools: List[str]) -> float:
        """Check for tool mentions"""
        text_lower = text.lower()
        matches = sum(1 for tool in tools if tool.lower() in text_lower)
        return min(100, (matches / max(1, len(tools) - 1)) * 100)


class PatternValidator:
    """Validate output structure and format"""
    
    def __init__(self):
        self.quality_patterns = {
            'length': {'min': 50, 'max': 500, 'optimal': (100, 300)},
            'avoid_phrases': [
                'fix this issue',
                'resolve the problem',
                'address this',
                'handle this matter',
                'deal with this'
            ]
        }
    
    def validate(self, ai_output: str) -> ValidationResult:
        """Validate output patterns and structure"""
        score = 0
        details = []
        
        # Length validation (25 points)
        length_score = self._validate_length(ai_output)
        score += length_score * 0.25
        details.append(f"Length check: {length_score:.1f}/100")
        
        # Structure validation (25 points)
        structure_score = self._validate_structure(ai_output)
        score += structure_score * 0.25
        details.append(f"Structure check: {structure_score:.1f}/100")
        
        # Content quality (50 points)
        content_score = self._validate_content_quality(ai_output)
        score += content_score * 0.50
        details.append(f"Content quality: {content_score:.1f}/100")
        
        return ValidationResult(
            score=score,
            method='pattern_matching',
            details=details
        )
    
    def _validate_length(self, text: str) -> float:
        """Validate text length"""
        length = len(text.strip())
        
        if length < self.quality_patterns['length']['min']:
            return 30.0  # Too short
        elif length > self.quality_patterns['length']['max']:
            return 70.0  # Too long
        
        optimal_min, optimal_max = self.quality_patterns['length']['optimal']
        if optimal_min <= length <= optimal_max:
            return 100.0  # Perfect length
        
        return 85.0  # Acceptable length
    
    def _validate_structure(self, text: str) -> float:
        """Validate text structure"""
        score = 100.0
        
        # Check for complete sentences
        if not any(text.endswith(p) for p in ['.', '!', '?']):
            score -= 30
        
        # Check for proper capitalization
        if text and not text[0].isupper():
            score -= 20
        
        # Check for punctuation variety
        if text.count('.') < 2:
            score -= 20
        
        return max(0, score)
    
    def _validate_content_quality(self, text: str) -> float:
        """Validate content is specific and actionable"""
        score = 100.0
        text_lower = text.lower()
        
        # Penalize generic phrases
        for phrase in self.quality_patterns['avoid_phrases']:
            if phrase in text_lower:
                score -= 25
        
        # Reward specific tool mentions
        tools = ['acrobat', 'pdf', 'editor', 'reader', 'software']
        if any(tool in text_lower for tool in tools):
            score += 10
        
        # Reward step-by-step instructions
        if any(marker in text_lower for marker in ['1.', '2.', 'first', 'then', 'next']):
            score += 15
        
        return min(100, max(0, score))


class ConsistencyValidator:
    """Validate consistency with known good responses"""
    
    def __init__(self):
        self.historical_responses = []
    
    def validate(
        self,
        ai_output: str,
        issue_context: Dict,
        fallback_response: str
    ) -> ValidationResult:
        """Compare AI output with fallback and historical responses"""
        score = 0
        details = []
        
        # Compare with fallback (50 points)
        fallback_similarity = self._calculate_similarity(ai_output, fallback_response)
        fallback_score = self._score_similarity(fallback_similarity)
        score += fallback_score * 0.5
        details.append(f"Fallback similarity: {fallback_similarity:.2f} ({fallback_score:.1f}/100)")
        
        # Compare with historical responses (30 points)
        if self.historical_responses:
            historical_score = self._compare_with_history(ai_output, issue_context)
            score += historical_score * 0.3
            details.append(f"Historical consistency: {historical_score:.1f}/100")
        else:
            score += 75 * 0.3  # Default score if no history
            details.append("No historical data available")
        
        # Check for contradictions (20 points)
        contradiction_score = self._check_contradictions(ai_output, fallback_response)
        score += contradiction_score * 0.2
        details.append(f"No contradictions: {contradiction_score:.1f}/100")
        
        return ValidationResult(
            score=score,
            method='consistency',
            details=details
        )
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two texts"""
        tokens1 = set(self._tokenize(text1.lower()))
        tokens2 = set(self._tokenize(text2.lower()))
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        return re.findall(r'\w+', text)
    
    def _score_similarity(self, similarity: float) -> float:
        """Convert similarity score to validation score"""
        if similarity < 0.2:
            return 40.0  # Too different
        elif 0.2 <= similarity < 0.4:
            return 70.0  # Somewhat similar
        elif 0.4 <= similarity < 0.7:
            return 100.0  # Good similarity
        elif 0.7 <= similarity < 0.9:
            return 90.0  # Very similar
        else:
            return 60.0  # Too similar (possible copy)
    
    def _compare_with_history(self, ai_output: str, issue_context: Dict) -> float:
        """Compare with historical responses"""
        # Simplified - would use more sophisticated matching in production
        return 75.0
    
    def _check_contradictions(self, ai_output: str, fallback: str) -> float:
        """Check for contradictory statements"""
        negation_words = ['not', 'never', 'avoid', "don't", 'cannot', "can't"]
        
        ai_negations = sum(1 for word in negation_words if word in ai_output.lower())
        fallback_negations = sum(1 for word in negation_words if word in fallback.lower())
        
        # If one has many negations and other doesn't, potential contradiction
        if abs(ai_negations - fallback_negations) > 2:
            return 60.0
        
        return 100.0


class KnowledgeBaseValidator:
    """Validate against curated knowledge base"""
    
    def __init__(self):
        self.knowledge_base = {
            'tag_tree': {
                'common_solutions': ['enable tagged pdf', 'add structure tags', 'use acrobat pro', 'create tag tree'],
                'expected_tools': ['Adobe Acrobat Pro', 'PDF editor'],
                'typical_steps': (3, 5),
                'difficulty': 'medium'
            },
            'alt_text': {
                'common_solutions': ['add alternative text', 'describe image', 'right-click figure', 'edit alternate text'],
                'expected_tools': ['Adobe Acrobat', 'PDF editor'],
                'typical_steps': (2, 4),
                'difficulty': 'easy'
            },
            'language': {
                'common_solutions': ['set document language', 'document properties', 'lang attribute', 'metadata'],
                'expected_tools': ['Adobe Acrobat', 'PDF properties'],
                'typical_steps': (2, 3),
                'difficulty': 'easy'
            }
        }
    
    def validate(self, ai_output: str, issue_type: str) -> ValidationResult:
        """Validate against known solutions for issue type"""
        score = 0
        details = []
        
        # Normalize issue type
        issue_key = self._normalize_issue_type(issue_type)
        
        if issue_key in self.knowledge_base:
            kb_entry = self.knowledge_base[issue_key]
            
            # Check for common solution keywords (40 points)
            solution_score = self._check_solutions(ai_output, kb_entry['common_solutions'])
            score += solution_score * 0.4
            details.append(f"Solution keywords: {solution_score:.1f}/100")
            
            # Check for expected tools (30 points)
            tool_score = self._check_tools(ai_output, kb_entry['expected_tools'])
            score += tool_score * 0.3
            details.append(f"Tool mentions: {tool_score:.1f}/100")
            
            # Validate step count (30 points)
            step_score = self._validate_steps(ai_output, kb_entry['typical_steps'])
            score += step_score * 0.3
            details.append(f"Step count: {step_score:.1f}/100")
        else:
            score = 70
            details.append("Issue type not in knowledge base")
        
        return ValidationResult(
            score=score,
            method='knowledge_base',
            details=details
        )
    
    def _normalize_issue_type(self, issue_type: str) -> str:
        """Normalize issue type to knowledge base key"""
        issue_lower = issue_type.lower()
        
        if 'tag' in issue_lower or 'structure' in issue_lower:
            return 'tag_tree'
        elif 'alt' in issue_lower or 'image' in issue_lower:
            return 'alt_text'
        elif 'language' in issue_lower or 'lang' in issue_lower:
            return 'language'
        
        return issue_type
    
    def _check_solutions(self, text: str, solutions: List[str]) -> float:
        """Check for common solution keywords"""
        text_lower = text.lower()
        matches = sum(1 for sol in solutions if any(word in text_lower for word in sol.split()))
        return (matches / len(solutions)) * 100 if solutions else 0
    
    def _check_tools(self, text: str, tools: List[str]) -> float:
        """Check for tool mentions"""
        text_lower = text.lower()
        matches = sum(1 for tool in tools if tool.lower() in text_lower)
        return (matches / len(tools)) * 100 if tools else 0
    
    def _validate_steps(self, text: str, typical_steps: tuple) -> float:
        """Validate step count is reasonable"""
        # Count numbered steps or sequential markers
        step_markers = len(re.findall(r'\d+\.|\bfirst\b|\bthen\b|\bnext\b|\bfinally\b', text.lower()))
        
        min_steps, max_steps = typical_steps
        
        if min_steps <= step_markers <= max_steps:
            return 100.0
        elif step_markers < min_steps:
            return 70.0  # Too few steps
        else:
            return 80.0  # More steps than typical


class AIValidator:
    """
    Main AI validation framework
    Coordinates multiple validation strategies
    """
    
    def __init__(self):
        self.rule_based = RuleBasedValidator()
        self.pattern_matcher = PatternValidator()
        self.consistency_checker = ConsistencyValidator()
        self.knowledge_base = KnowledgeBaseValidator()
        
        # Validation weights (sum to 1.0)
        self.weights = {
            'rule_based': 0.25,
            'pattern_matching': 0.20,
            'consistency': 0.25,
            'knowledge_base': 0.15,
            'ensemble': 0.15  # Reserved for future ensemble validation
        }
        
        logger.info("✅ AIValidator initialized with 4 validation layers")
    
    def validate_output(
        self,
        ai_output: str,
        issue_context: Dict[str, Any],
        fallback_response: str
    ) -> ConfidenceScore:
        """
        Validate AI output using all validation strategies
        
        Args:
            ai_output: The AI-generated text to validate
            issue_context: Context about the issue (standard, description, etc.)
            fallback_response: Fallback response for comparison
        
        Returns:
            ConfidenceScore with overall score and breakdown
        """
        validation_results = []
        
        # 1. Rule-based validation
        rule_result = self.rule_based.validate(ai_output, issue_context)
        validation_results.append(rule_result)
        
        # 2. Pattern validation
        pattern_result = self.pattern_matcher.validate(ai_output)
        validation_results.append(pattern_result)
        
        # 3. Consistency validation
        consistency_result = self.consistency_checker.validate(
            ai_output, issue_context, fallback_response
        )
        validation_results.append(consistency_result)
        
        # 4. Knowledge base validation
        issue_type = self._extract_issue_type(issue_context.get('description', ''))
        kb_result = self.knowledge_base.validate(ai_output, issue_type)
        validation_results.append(kb_result)
        
        # 5. Ensemble validation
        ensemble_result = self._ensemble_validate(ai_output, issue_context, fallback_response)
        validation_results.append(ensemble_result)
        
        # Calculate final confidence score
        confidence_score = self._calculate_confidence(validation_results)
        
        logger.info(
            f"🎯 Validation complete: {confidence_score.overall_score:.1f}/100 "
            f"({confidence_score.confidence_level})"
        )
        
        return confidence_score

    def _ensemble_validate(
        self,
        ai_output: str,
        issue_context: Dict[str, Any],
        fallback_response: str
    ) -> ValidationResult:
        """
        Lightweight ensemble validation.
        
        Uses multiple deterministic heuristics and normalizations as independent
        "voters" to estimate output reliability without making additional model calls.
        """
        details: List[str] = []

        raw = ai_output.strip()
        normalized = re.sub(r'\s+', ' ', raw)
        lowercase = normalized.lower()
        flattened = raw.replace('\n', ' ')

        # Voter 1: structural stability under normalization.
        length_delta = abs(len(normalized) - len(flattened))
        stability_score = 100.0 if length_delta == 0 else max(60.0, 100.0 - (length_delta / max(1, len(normalized))) * 100)
        details.append(f"Normalization stability: {stability_score:.1f}/100")

        # Voter 2: context keyword retention.
        context_words = [
            w for w in re.findall(r'[a-zA-Z]{4,}', issue_context.get('description', '').lower())
            if w not in {'document', 'issue', 'missing', 'contains'}
        ]
        context_words = list(dict.fromkeys(context_words))[:8]
        if context_words:
            matched = sum(1 for word in context_words if word in lowercase)
            context_score = (matched / len(context_words)) * 100
        else:
            context_score = 75.0
        details.append(f"Context retention: {context_score:.1f}/100")

        # Voter 3: fallback semantic alignment.
        similarity = self.consistency_checker._calculate_similarity(normalized, fallback_response)
        alignment_score = self.consistency_checker._score_similarity(similarity)
        details.append(f"Fallback alignment: {alignment_score:.1f}/100")

        # Voter 4: actionability markers.
        action_markers = ['add', 'set', 'open', 'use', 'verify', 'check', 'update', 'create']
        action_hits = sum(1 for marker in action_markers if marker in lowercase)
        actionability_score = min(100.0, 40.0 + action_hits * 10.0)
        details.append(f"Actionability markers: {actionability_score:.1f}/100")

        score = (
            stability_score * 0.2
            + context_score * 0.3
            + alignment_score * 0.3
            + actionability_score * 0.2
        )

        return ValidationResult(
            score=round(min(100.0, max(0.0, score)), 1),
            method='ensemble',
            details=details,
            metadata={
                'normalized_length': len(normalized),
                'flattened_length': len(flattened),
                'context_terms': context_words,
                'similarity': round(similarity, 3),
            }
        )
    
    def _calculate_confidence(self, validation_results: List[ValidationResult]) -> ConfidenceScore:
        """Calculate weighted confidence score"""
        total_score = 0
        breakdown = {}
        
        for result in validation_results:
            weight = self.weights.get(result.method, 0)
            weighted_score = result.score * weight
            total_score += weighted_score
            
            breakdown[result.method] = {
                'score': result.score,
                'weight': weight,
                'contribution': weighted_score,
                'details': result.details
            }
        
        # Determine confidence level
        confidence_level = self._determine_level(total_score)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(total_score)
        
        # Determine if fallback is recommended
        fallback_recommended = total_score < 60
        
        return ConfidenceScore(
            overall_score=round(total_score, 1),
            confidence_level=confidence_level,
            breakdown=breakdown,
            recommendation=recommendation,
            fallback_recommended=fallback_recommended
        )
    
    def _determine_level(self, score: float) -> str:
        """Determine confidence level from score"""
        if score >= 90:
            return 'very_high'
        elif score >= 75:
            return 'high'
        elif score >= 60:
            return 'medium'
        elif score >= 45:
            return 'low'
        else:
            return 'very_low'
    
    def _generate_recommendation(self, score: float) -> str:
        """Generate actionable recommendation"""
        if score >= 90:
            return "AI output is highly reliable. Safe to use as-is."
        elif score >= 75:
            return "AI output is reliable. Minor review recommended."
        elif score >= 60:
            return "AI output is acceptable. Review and verify before use."
        elif score >= 45:
            return "AI output has concerns. Thorough review required."
        else:
            return "AI output is unreliable. Use fallback response instead."
    
    def _extract_issue_type(self, description: str) -> str:
        """Extract issue type from description"""
        description_lower = description.lower()
        
        if 'tag' in description_lower or 'structure' in description_lower:
            return 'tag_tree'
        elif 'alt' in description_lower or 'image' in description_lower:
            return 'alt_text'
        elif 'language' in description_lower:
            return 'language'
        elif 'form' in description_lower:
            return 'form_field'
        elif 'scanned' in description_lower:
            return 'scanned'
        
        return 'unknown'
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get validator statistics"""
        return {
            'validation_layers': len(self.weights),
            'weights': self.weights,
            'standards_count': len(self.rule_based.standards_db),
            'knowledge_base_entries': len(self.knowledge_base.knowledge_base)
        }

