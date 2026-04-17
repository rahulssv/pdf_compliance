"""PDF accessibility analysis service with enhanced detection algorithms"""
import os
import logging
from typing import Dict, List, Any, Optional
from io import BytesIO
import pypdf
import pdfplumber
from src.utils.standards import map_issue_to_standard

# Configure logging
logger = logging.getLogger(__name__)


class PDFAnalyzer:
    """Analyzes PDF files for accessibility compliance with comprehensive checks"""
    
    def __init__(self):
        self._analysis_cache = {}
    
    def analyze_pdf(self, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Analyze a PDF file for accessibility issues
        
        Args:
            file_path: Path to the PDF file
            filename: Original filename
            
        Returns:
            Dictionary with analysis results
        """
        cache_key = f"{file_path}:{os.path.getmtime(file_path)}"
        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()
        return self._analyze_pdf_bytes(pdf_bytes, filename, cache_key)
    
    def analyze_pdf_buffer(self, file_buffer: BytesIO, filename: str) -> Dict[str, Any]:
        """
        Analyze a PDF directly from memory without touching disk.
        
        Args:
            file_buffer: PDF bytes in memory
            filename: Original filename
        
        Returns:
            Dictionary with analysis results
        """
        file_buffer.seek(0)
        pdf_bytes = file_buffer.read()
        cache_key = f"buffer:{hash(pdf_bytes)}"
        return self._analyze_pdf_bytes(pdf_bytes, filename, cache_key)
    
    def _analyze_pdf_bytes(self, pdf_bytes: bytes, filename: str, cache_key: str) -> Dict[str, Any]:
        """Analyze raw PDF bytes with shared logic for file and in-memory paths."""
        # Check cache
        if cache_key in self._analysis_cache:
            logger.info(f"📦 Using cached analysis for {filename}")
            cached = self._analysis_cache[cache_key].copy()
            cached['fileName'] = filename
            return cached
        
        issues = []
        has_tag_tree = False
        figures_with_alt = 0
        figures_without_alt = 0
        
        try:
            logger.info(f"🔍 Analyzing {filename}...")
            
            # Analyze with pypdf for structure
            pdf_reader = pypdf.PdfReader(BytesIO(pdf_bytes))
            
            # Check for tag tree (PDF/UA requirement)
            has_tag_tree = self._has_tag_tree(pdf_reader)
            if not has_tag_tree:
                issues.append(self._create_issue(
                    'no_tag_tree',
                    'Document does not contain a tag tree, so screen readers cannot interpret structural semantics.'
                ))
                logger.info("  ❌ No tag tree found")
            else:
                logger.info("  ✅ Tag tree present")
                # Check for Figure elements with/without alt text
                figures_with_alt, figures_without_alt = self._check_figure_alt_text(pdf_reader)
                logger.info(f"  📊 Figures with alt: {figures_with_alt}, without alt: {figures_without_alt}")
            
            # Check for document language
            if not self._has_language(pdf_reader):
                issues.append(self._create_issue(
                    'missing_language',
                    'Document language is not declared at the document level.'
                ))
                logger.info("  ❌ No language declaration")
            else:
                logger.info("  ✅ Language declaration present")
            
            # Check metadata
            metadata = pdf_reader.metadata
            if not self._has_complete_metadata(metadata):
                issues.append(self._create_issue(
                    'poor_structure',
                    'Document metadata is missing or incomplete, affecting discoverability.'
                ))
                logger.info("  ❌ Incomplete metadata")
            else:
                logger.info("  ✅ Metadata complete")
            
            # Analyze with pdfplumber for content
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                # Check for images - but only flag if structure tree shows missing alt text
                has_images, image_count = self._check_images(pdf)
                
                # Only report missing alt text if we found figures without alt in structure tree,
                # or if there's no tag tree but images exist
                if figures_without_alt > 0:
                    issues.append(self._create_issue(
                        'missing_alt_text',
                        f'Figure elements are present but missing alternative text.'
                    ))
                    logger.info(f"  ❌ {figures_without_alt} figure(s) missing alt text")
                elif has_images and not has_tag_tree:
                    # Images exist but no tag tree - they can't have proper alt text
                    issues.append(self._create_issue(
                        'missing_alt_text',
                        f'Document contains {image_count} image(s) that may be missing alternative text.'
                    ))
                    logger.info(f"  ⚠️ {image_count} images detected without tag tree")
                elif has_images:
                    logger.info(f"  ✅ {image_count} image(s) with proper alt text")
                
                # Check for form fields
                has_forms, form_count = self._check_form_fields(pdf)
                if has_forms:
                    issues.append(self._create_issue(
                        'form_field_unlabeled',
                        f'Document contains {form_count} form field(s) that may not expose labels to assistive technology.'
                    ))
                    logger.info(f"  ⚠️ {form_count} form fields detected")
                
                # Check if document is scanned (image-only)
                if self._is_scanned_document(pdf):
                    issues.append(self._create_issue(
                        'scanned_document',
                        'Document appears to be scanned images without OCR text layer.'
                    ))
                    logger.info("  ❌ Scanned document detected")
        
        except Exception as e:
            logger.error(f"❌ Error analyzing {filename}: {str(e)}")
            # Return minimal analysis on error
            issues.append(self._create_issue(
                'poor_structure',
                f'Unable to fully analyze document structure. File may be corrupted or use unsupported features.'
            ))
        
        # Calculate non-compliance percentage
        non_compliance_percent = self._calculate_non_compliance(issues)
        
        # Determine compliance status
        compliance_status = self._determine_compliance_status(non_compliance_percent)
        
        result = {
            'fileName': filename,
            'nonCompliancePercent': non_compliance_percent,
            'complianceStatus': compliance_status,
            'issues': issues
        }
        
        # Cache the result
        self._analysis_cache[cache_key] = result.copy()
        
        logger.info(f"✅ Analysis complete: {compliance_status} ({non_compliance_percent}% non-compliant, {len(issues)} issues)")
        
        return result
    
    def _has_tag_tree(self, pdf_reader: pypdf.PdfReader) -> bool:
        """Check if PDF has a tag tree structure (improved detection)"""
        try:
            catalog = pdf_reader.trailer.get('/Root')
            if not catalog:
                return False
                
            if isinstance(catalog, pypdf.generic.IndirectObject):
                catalog = catalog.get_object()
            
            # Primary check: StructTreeRoot
            if '/StructTreeRoot' in catalog:
                struct_tree = catalog['/StructTreeRoot']
                if isinstance(struct_tree, pypdf.generic.IndirectObject):
                    struct_tree = struct_tree.get_object()
                # Verify it's not just an empty object
                if struct_tree and len(struct_tree) > 0:
                    return True
            
            # Secondary check: MarkInfo with Marked flag
            mark_info = catalog.get('/MarkInfo')
            if mark_info:
                if isinstance(mark_info, pypdf.generic.IndirectObject):
                    mark_info = mark_info.get_object()
                
                if mark_info and mark_info.get('/Marked') is True:
                    return True
            
            return False
        except Exception as e:
            logger.warning(f"Error checking tag tree: {e}")
            return False
    
    def _check_figure_alt_text(self, pdf_reader: pypdf.PdfReader) -> tuple[int, int]:
        """
        Check Figure elements in structure tree for alt text
        
        Returns:
            Tuple of (figures_with_alt, figures_without_alt)
        """
        figures_with_alt = 0
        figures_without_alt = 0
        
        try:
            catalog = pdf_reader.trailer.get('/Root')
            if not catalog:
                return 0, 0
            
            if isinstance(catalog, pypdf.generic.IndirectObject):
                catalog = catalog.get_object()
            
            if '/StructTreeRoot' not in catalog:
                return 0, 0
            
            struct_tree = catalog['/StructTreeRoot']
            if isinstance(struct_tree, pypdf.generic.IndirectObject):
                struct_tree = struct_tree.get_object()
            
            k = struct_tree.get('/K')
            if not k:
                return 0, 0
            
            def find_figures(obj, depth=0):
                nonlocal figures_with_alt, figures_without_alt
                
                if depth > 15:  # Prevent infinite recursion
                    return
                
                if isinstance(obj, pypdf.generic.IndirectObject):
                    try:
                        obj = obj.get_object()
                    except Exception:
                        return
                
                if isinstance(obj, pypdf.generic.DictionaryObject):
                    s_type = obj.get('/S')
                    if s_type:
                        if isinstance(s_type, pypdf.generic.IndirectObject):
                            s_type = s_type.get_object()
                        s_type_str = str(s_type)
                        
                        # Check if this is a Figure element
                        if 'Figure' in s_type_str:
                            alt = obj.get('/Alt')
                            if alt and str(alt).strip():
                                figures_with_alt += 1
                            else:
                                figures_without_alt += 1
                    
                    # Check children
                    k_child = obj.get('/K')
                    if k_child:
                        find_figures(k_child, depth + 1)
                
                elif isinstance(obj, pypdf.generic.ArrayObject):
                    for item in obj:
                        find_figures(item, depth + 1)
            
            find_figures(k)
            
        except Exception as e:
            logger.warning(f"Error checking figure alt text: {e}")
        
        return figures_with_alt, figures_without_alt
    
    def _has_language(self, pdf_reader: pypdf.PdfReader) -> bool:
        """Check if PDF has language declaration"""
        try:
            catalog = pdf_reader.trailer.get('/Root')
            if not catalog:
                return False
                
            if isinstance(catalog, pypdf.generic.IndirectObject):
                catalog = catalog.get_object()
            
            lang = catalog.get('/Lang')
            return bool(lang) and len(str(lang)) > 0
        except Exception as e:
            logger.warning(f"Error checking language: {e}")
            return False
    
    def _has_complete_metadata(self, metadata: Optional[pypdf.generic.PdfObject]) -> bool:
        """Check if PDF has complete metadata"""
        if not metadata:
            return False
        
        # Check for important metadata fields
        required_fields = ['/Title']
        optional_fields = ['/Author', '/Subject']
        
        has_required = all(metadata.get(field) for field in required_fields)
        has_some_optional = any(metadata.get(field) for field in optional_fields)
        
        return has_required or has_some_optional
    
    def _check_images(self, pdf: pdfplumber.PDF) -> tuple[bool, int]:
        """Check if PDF has images (returns has_images, count)"""
        try:
            total_images = 0
            for page in pdf.pages:
                if page.images:
                    total_images += len(page.images)
            
            return total_images > 0, total_images
        except Exception as e:
            logger.warning(f"Error checking images: {e}")
            return False, 0
    
    def _check_form_fields(self, pdf: pdfplumber.PDF) -> tuple[bool, int]:
        """Check if PDF has form fields (returns has_forms, count)"""
        try:
            total_fields = 0
            for page in pdf.pages:
                if hasattr(page, 'annots') and page.annots:
                    # Count form field annotations
                    total_fields += len([a for a in page.annots if a.get('Subtype') in ['/Widget', 'Widget']])
            
            return total_fields > 0, total_fields
        except Exception as e:
            logger.warning(f"Error checking form fields: {e}")
            return False, 0
    
    def _is_scanned_document(self, pdf: pdfplumber.PDF) -> bool:
        """Check if PDF is a scanned document without text layer (improved algorithm)"""
        try:
            total_text_length = 0
            total_images = 0
            total_pages = len(pdf.pages)
            
            # Sample pages (check all pages for small docs, sample for large ones)
            pages_to_check = pdf.pages if total_pages <= 10 else [
                pdf.pages[0],  # First page
                pdf.pages[total_pages // 2],  # Middle page
                pdf.pages[-1]  # Last page
            ]
            
            for page in pages_to_check:
                text = page.extract_text()
                if text:
                    # Count actual characters (not whitespace)
                    text_stripped = ''.join(text.split())
                    total_text_length += len(text_stripped)
                
                if page.images:
                    total_images += len(page.images)
            
            # Heuristic: If we have images but very little text, likely scanned
            # Average less than 50 characters per page checked
            avg_text_per_page = total_text_length / len(pages_to_check) if pages_to_check else 0
            
            if total_images > 0 and avg_text_per_page < 50:
                return True
            
            return False
        except Exception as e:
            logger.warning(f"Error checking scanned document: {e}")
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
