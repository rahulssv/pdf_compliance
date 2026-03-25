"""Accessibility standards mapping and definitions"""

# WCAG 2.1 Success Criteria
WCAG_STANDARDS = {
    'alt_text': {
        'code': 'WCAG 2.1 SC 1.1.1',
        'name': 'Non-text Content',
        'category': 'WCAG',
        'description': 'All non-text content must have text alternatives'
    },
    'language': {
        'code': 'WCAG 2.1 SC 3.1.1',
        'name': 'Language of Page',
        'category': 'WCAG',
        'description': 'The default language must be programmatically determined'
    },
    'structure': {
        'code': 'WCAG 2.1 SC 1.3.1',
        'name': 'Info and Relationships',
        'category': 'WCAG',
        'description': 'Information and relationships must be programmatically determined'
    },
    'headings': {
        'code': 'WCAG 2.1 SC 2.4.6',
        'name': 'Headings and Labels',
        'category': 'WCAG',
        'description': 'Headings and labels must describe topic or purpose'
    },
    'reading_order': {
        'code': 'WCAG 2.1 SC 1.3.2',
        'name': 'Meaningful Sequence',
        'category': 'WCAG',
        'description': 'Content must be presented in a meaningful sequence'
    },
    'color_contrast': {
        'code': 'WCAG 2.1 SC 1.4.3',
        'name': 'Contrast (Minimum)',
        'category': 'WCAG',
        'description': 'Text must have sufficient contrast ratio'
    }
}

# PDF/UA-1 Standards
PDFUA_STANDARDS = {
    'tag_tree': {
        'code': 'PDF/UA-1 §7.1',
        'name': 'Tag Tree',
        'category': 'PDF/UA',
        'description': 'Document must contain a logical structure tree'
    },
    'alt_descriptions': {
        'code': 'PDF/UA-1 §7.3',
        'name': 'Alternative Descriptions',
        'category': 'PDF/UA',
        'description': 'Alternative descriptions must be provided for content'
    },
    'form_fields': {
        'code': 'PDF/UA-1 §7.18',
        'name': 'Form Fields',
        'category': 'PDF/UA',
        'description': 'Form fields must be properly tagged and labeled'
    },
    'metadata': {
        'code': 'PDF/UA-1 §7.1',
        'name': 'Document Metadata',
        'category': 'PDF/UA',
        'description': 'Document must contain proper metadata'
    }
}

# Section 508 Standards
SECTION_508_STANDARDS = {
    'form_labels': {
        'code': 'Section 508 §1194.22(n)',
        'name': 'Form Field Labels',
        'category': 'Section 508',
        'description': 'Forms must allow assistive technology users to access information'
    },
    'text_equivalents': {
        'code': 'Section 508 §1194.22(a)',
        'name': 'Text Equivalents',
        'category': 'Section 508',
        'description': 'Text equivalent must be provided for non-text elements'
    }
}

# ADA Standards
ADA_STANDARDS = {
    'digital_accessibility': {
        'code': 'ADA Title III',
        'name': 'Digital Accessibility',
        'category': 'ADA',
        'description': 'Digital content must be accessible to people with disabilities'
    }
}

# European Accessibility Act
EAA_STANDARDS = {
    'digital_services': {
        'code': 'EAA Article 4',
        'name': 'Digital Services Accessibility',
        'category': 'EAA',
        'description': 'Digital services must meet accessibility requirements'
    }
}


def get_standard_info(issue_type: str, standard_family: str = 'WCAG'):
    """
    Get standard information for a specific issue type
    
    Args:
        issue_type: Type of accessibility issue
        standard_family: Standard family (WCAG, PDF/UA, Section 508, ADA, EAA)
        
    Returns:
        Dictionary with standard information
    """
    standards_map = {
        'WCAG': WCAG_STANDARDS,
        'PDF/UA': PDFUA_STANDARDS,
        'Section 508': SECTION_508_STANDARDS,
        'ADA': ADA_STANDARDS,
        'EAA': EAA_STANDARDS
    }
    
    standards = standards_map.get(standard_family, WCAG_STANDARDS)
    return standards.get(issue_type, {
        'code': f'{standard_family} General',
        'name': 'General Accessibility',
        'category': standard_family,
        'description': 'General accessibility requirement'
    })


# Issue type to standard mapping
ISSUE_TO_STANDARD = {
    'missing_alt_text': ('alt_text', 'WCAG'),
    'no_tag_tree': ('tag_tree', 'PDF/UA'),
    'missing_language': ('language', 'WCAG'),
    'form_field_unlabeled': ('form_labels', 'Section 508'),
    'poor_structure': ('structure', 'WCAG'),
    'missing_headings': ('headings', 'WCAG'),
    'scanned_document': ('text_equivalents', 'Section 508'),
    'reading_order': ('reading_order', 'WCAG'),
}


def map_issue_to_standard(issue_type: str):
    """
    Map an issue type to its corresponding standard
    
    Args:
        issue_type: Type of accessibility issue
        
    Returns:
        Dictionary with standard code, category, and description
    """
    if issue_type in ISSUE_TO_STANDARD:
        std_key, family = ISSUE_TO_STANDARD[issue_type]
        info = get_standard_info(std_key, family)
        return {
            'standard': info['code'],
            'category': info['category']
        }
    
    # Default to WCAG general
    return {
        'standard': 'WCAG 2.1',
        'category': 'WCAG'
    }

# Made with Bob
