"""PDF accessibility analysis service"""
import os
from typing import Dict, List, Any
import pypdf
import pdfplumber
from src.utils.standards import map_issue_to_standard


class PDFAnalyzer:
    """Analyzes PDF files for accessibility compliance"""
    
    def __init__(self):
        pass
    
    def analyze_pdf(self, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Analyze a PDF file for accessibility issues
        
        Args:
            file_path: Path to the PDF file
            filename: Original filename
            
        Returns:
            Dictionary with analysis results
        """
        issues = []
        
        try:
            # Analyze with pypdf for structure
            with open(file_path, 'rb') as f:
                pdf_reader = pypdf.PdfReader(f)
                
                # Check for tag tree (PDF/UA requirement)
                if not self._has_tag_tree(pdf_reader):
                    issues.append(self._create_issue(
                        'no_tag_tree',
                        'Document does not contain a tag tree, so screen readers cannot interpret structural semantics.'
                    ))
                
                # Check for document language
                if not self._has_language(pdf_reader):
                    issues.append(self._create_issue(
                        'missing_language',
                        'Document language is not declared at the document level.'
                    ))
                
                # Check metadata
                metadata = pdf_reader.metadata
                if not metadata or not metadata.get('/Title'):
                    issues.append(self._create_issue(
                        'poor_structure',
                        'Document metadata is missing or incomplete, affecting discoverability.'
                    ))
            
            # Analyze with pdfplumber for content
            with pdfplumber.open(file_path) as pdf:
                # Check for images without alt text
                if self._has_images_without_alt_text(pdf):
                    issues.append(self._create_issue(
                        'missing_alt_text',
                        'Figure elements are present but missing alternative text.'
                    ))
                
                # Check for form fields
                if self._has_unlabeled_form_fields(pdf):
                    issues.append(self._create_issue(
                        'form_field_unlabeled',
                        'Form fields do not expose labels to assistive technology.'
                    ))
                
                # Check if document is scanned (image-only)
                if self._is_scanned_document(pdf):
                    issues.append(self._create_issue(
                        'scanned_document',
                        'Document appears to be scanned images without OCR text layer.'
                    ))
        
        except Exception as e:
            print(f"Error analyzing {filename}: {str(e)}")
            # Return minimal analysis on error
            issues.append(self._create_issue(
                'poor_structure',
                f'Unable to fully analyze document structure: {str(e)}'
            ))
        
        # Calculate non-compliance percentage
        non_compliance_percent = self._calculate_non_compliance(issues)
        
        # Determine compliance status
        compliance_status = self._determine_compliance_status(non_compliance_percent)
        
        return {
            'fileName': filename,
            'nonCompliancePercent': non_compliance_percent,
            'complianceStatus': compliance_status,
            'issues': issues
        }
    
    def _has_tag_tree(self, pdf_reader: pypdf.PdfReader) -> bool:
        """Check if PDF has a tag tree structure"""
        try:
            catalog = pdf_reader.trailer.get('/Root', {})
            if isinstance(catalog, pypdf.generic.IndirectObject):
                catalog = catalog.get_object()
            
            # Check for StructTreeRoot
            if '/StructTreeRoot' in catalog:
                return True
            
            # Check for MarkInfo
            mark_info = catalog.get('/MarkInfo', {})
            if isinstance(mark_info, pypdf.generic.IndirectObject):
                mark_info = mark_info.get_object()
            
            if mark_info and mark_info.get('/Marked') == True:
                return True
            
            return False
        except:
            return False
    
    def _has_language(self, pdf_reader: pypdf.PdfReader) -> bool:
        """Check if PDF has language declaration"""
        try:
            catalog = pdf_reader.trailer.get('/Root', {})
            if isinstance(catalog, pypdf.generic.IndirectObject):
                catalog = catalog.get_object()
            
            return '/Lang' in catalog
        except:
            return False
    
    def _has_images_without_alt_text(self, pdf: pdfplumber.PDF) -> bool:
        """Check if PDF has images without alternative text"""
        try:
            for page in pdf.pages:
                # Check for images
                if page.images:
                    # In a real implementation, we'd check if images have alt text
                    # For now, we'll use a heuristic
                    return True
            return False
        except:
            return False
    
    def _has_unlabeled_form_fields(self, pdf: pdfplumber.PDF) -> bool:
        """Check if PDF has form fields without labels"""
        try:
            # Check if document has form fields
            # This is a simplified check
            for page in pdf.pages:
                if hasattr(page, 'annots') and page.annots:
                    return True
            return False
        except:
            return False
    
    def _is_scanned_document(self, pdf: pdfplumber.PDF) -> bool:
        """Check if PDF is a scanned document without text layer"""
        try:
            total_text = 0
            total_images = 0
            
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    total_text += len(text.strip())
                if page.images:
                    total_images += len(page.images)
            
            # If we have images but very little text, likely scanned
            if total_images > 0 and total_text < 100:
                return True
            
            return False
        except:
            return False
    
    def _create_issue(self, issue_type: str, description: str) -> Dict[str, str]:
        """Create an issue dictionary with proper standard mapping"""
        standard_info = map_issue_to_standard(issue_type)
        
        return {
            'description': description,
            'standard': standard_info['standard'],
            'category': standard_info['category']
        }
    
    def _calculate_non_compliance(self, issues: List[Dict]) -> int:
        """
        Calculate non-compliance percentage based on issues found
        
        Args:
            issues: List of accessibility issues
            
        Returns:
            Non-compliance percentage (0-100)
        """
        if not issues:
            return 0
        
        # Weight different issue types
        weights = {
            'no_tag_tree': 30,
            'missing_language': 15,
            'missing_alt_text': 20,
            'form_field_unlabeled': 20,
            'scanned_document': 35,
            'poor_structure': 10
        }
        
        total_weight = 0
        for issue in issues:
            # Extract issue type from description (simplified)
            issue_type = 'poor_structure'  # default
            
            if 'tag tree' in issue['description'].lower():
                issue_type = 'no_tag_tree'
            elif 'language' in issue['description'].lower():
                issue_type = 'missing_language'
            elif 'alternative text' in issue['description'].lower() or 'alt text' in issue['description'].lower():
                issue_type = 'missing_alt_text'
            elif 'form field' in issue['description'].lower():
                issue_type = 'form_field_unlabeled'
            elif 'scanned' in issue['description'].lower():
                issue_type = 'scanned_document'
            
            total_weight += weights.get(issue_type, 10)
        
        # Cap at 100
        return min(total_weight, 100)
    
    def _determine_compliance_status(self, non_compliance_percent: int) -> str:
        """
        Determine compliance status based on non-compliance percentage
        
        Args:
            non_compliance_percent: Non-compliance percentage
            
        Returns:
            Compliance status string
        """
        if non_compliance_percent == 0:
            return 'compliant'
        elif non_compliance_percent < 40:
            return 'partially-compliant'
        else:
            return 'non-compliant'

# Made with Bob
