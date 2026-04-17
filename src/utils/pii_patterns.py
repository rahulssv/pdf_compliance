"""
PII Pattern Library
Comprehensive patterns for detecting 15+ types of Personally Identifiable Information
"""
import re
from typing import Dict, List, Pattern
from dataclasses import dataclass


@dataclass
class PIIPattern:
    """PII pattern definition"""
    name: str
    pattern: Pattern
    category: str
    severity: str  # 'high', 'medium', 'low'
    description: str
    mask_format: str  # Format for masking (e.g., '***-**-{last4}')


class PIIPatterns:
    """Centralized PII pattern definitions"""
    
    # Financial PII Patterns
    SSN = PIIPattern(
        name='SSN',
        pattern=re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        category='financial',
        severity='high',
        description='Social Security Number',
        mask_format='***-**-{last4}'
    )
    
    CREDIT_CARD = PIIPattern(
        name='CREDIT_CARD',
        pattern=re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
        category='financial',
        severity='high',
        description='Credit Card Number',
        mask_format='****-****-****-{last4}'
    )
    
    BANK_ACCOUNT = PIIPattern(
        name='BANK_ACCOUNT',
        pattern=re.compile(r'\b\d{8,17}\b'),
        category='financial',
        severity='high',
        description='Bank Account Number',
        mask_format='****{last4}'
    )
    
    TAX_ID = PIIPattern(
        name='TAX_ID',
        pattern=re.compile(r'\b\d{2}-\d{7}\b'),
        category='financial',
        severity='high',
        description='Tax Identification Number',
        mask_format='**-****{last3}'
    )
    
    # Personal PII Patterns
    EMAIL = PIIPattern(
        name='EMAIL',
        pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        category='personal',
        severity='medium',
        description='Email Address',
        mask_format='{first}***@{domain}'
    )
    
    PHONE_US = PIIPattern(
        name='PHONE',
        pattern=re.compile(r'\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
        category='personal',
        severity='medium',
        description='US Phone Number',
        mask_format='***-***-{last4}'
    )
    
    DOB = PIIPattern(
        name='DOB',
        pattern=re.compile(r'\b(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/\d{4}\b'),
        category='personal',
        severity='high',
        description='Date of Birth',
        mask_format='**/**/{year}'
    )
    
    ZIP_CODE = PIIPattern(
        name='ZIP_CODE',
        pattern=re.compile(r'\b\d{5}(?:-\d{4})?\b'),
        category='personal',
        severity='low',
        description='ZIP Code',
        mask_format='{first3}**'
    )
    
    # Medical PII Patterns
    MEDICAL_RECORD = PIIPattern(
        name='MEDICAL_RECORD',
        pattern=re.compile(r'\b(MRN|MR#|Medical Record)[:\s#]*\d{6,10}\b', re.IGNORECASE),
        category='medical',
        severity='high',
        description='Medical Record Number',
        mask_format='MRN: ****{last4}'
    )
    
    INSURANCE_NUMBER = PIIPattern(
        name='INSURANCE_NUMBER',
        pattern=re.compile(r'\b[A-Z]{3}\d{9}\b'),
        category='medical',
        severity='high',
        description='Insurance Policy Number',
        mask_format='***{last4}'
    )
    
    # Government ID Patterns
    PASSPORT = PIIPattern(
        name='PASSPORT',
        pattern=re.compile(r'\b[A-Z]{1,2}\d{6,9}\b'),
        category='government',
        severity='high',
        description='Passport Number',
        mask_format='**{last4}'
    )
    
    DRIVERS_LICENSE = PIIPattern(
        name='DRIVERS_LICENSE',
        pattern=re.compile(r'\b[A-Z]\d{7,8}\b'),
        category='government',
        severity='high',
        description='Driver\'s License Number',
        mask_format='*{last4}'
    )
    
    # IP Address (lower severity but still PII)
    IP_ADDRESS = PIIPattern(
        name='IP_ADDRESS',
        pattern=re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
        category='technical',
        severity='low',
        description='IP Address',
        mask_format='{first}.***.***.{last}'
    )
    
    # Name patterns (basic - can be enhanced with NER)
    FULL_NAME = PIIPattern(
        name='FULL_NAME',
        pattern=re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'),
        category='personal',
        severity='medium',
        description='Full Name (basic pattern)',
        mask_format='{first} {last_initial}.'
    )
    
    # Address pattern (basic)
    STREET_ADDRESS = PIIPattern(
        name='STREET_ADDRESS',
        pattern=re.compile(r'\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b', re.IGNORECASE),
        category='personal',
        severity='medium',
        description='Street Address',
        mask_format='*** {street_type}'
    )
    
    @classmethod
    def get_all_patterns(cls) -> List[PIIPattern]:
        """Get all PII patterns"""
        return [
            cls.SSN,
            cls.CREDIT_CARD,
            cls.BANK_ACCOUNT,
            cls.TAX_ID,
            cls.EMAIL,
            cls.PHONE_US,
            cls.DOB,
            cls.ZIP_CODE,
            cls.MEDICAL_RECORD,
            cls.INSURANCE_NUMBER,
            cls.PASSPORT,
            cls.DRIVERS_LICENSE,
            cls.IP_ADDRESS,
            cls.FULL_NAME,
            cls.STREET_ADDRESS
        ]
    
    @classmethod
    def get_patterns_by_category(cls, category: str) -> List[PIIPattern]:
        """Get patterns by category"""
        return [p for p in cls.get_all_patterns() if p.category == category]
    
    @classmethod
    def get_patterns_by_severity(cls, severity: str) -> List[PIIPattern]:
        """Get patterns by severity"""
        return [p for p in cls.get_all_patterns() if p.severity == severity]
    
    @classmethod
    def get_high_severity_patterns(cls) -> List[PIIPattern]:
        """Get high severity patterns only"""
        return cls.get_patterns_by_severity('high')


def mask_pii(text: str, pattern: PIIPattern) -> str:
    """
    Mask PII in text according to pattern's mask format
    
    Args:
        text: Original text containing PII
        pattern: PIIPattern to use for masking
    
    Returns:
        Masked version of the text
    """
    if '{last4}' in pattern.mask_format:
        # Keep last 4 characters
        if len(text) > 4:
            return pattern.mask_format.replace('{last4}', text[-4:])
    
    if '{first}' in pattern.mask_format and '@' in text:
        # Email masking
        parts = text.split('@')
        return pattern.mask_format.replace('{first}', parts[0][0]).replace('{domain}', parts[1])
    
    # Default masking
    return '***' + text[-4:] if len(text) > 4 else '***'

# Made with Bob
