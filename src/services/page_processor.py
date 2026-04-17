"""
Page Processor Service
Granular page-by-page PDF processing with extraction and analysis capabilities
"""
import logging
import pypdf
import pdfplumber
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.services.pii_detector import PIIDetector
from src.utils.standards import map_issue_to_standard

logger = logging.getLogger(__name__)


class PageProcessor:
    """
    Service for page-level PDF processing
    Enables granular analysis, extraction, and remediation at the page level
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize page processor
        
        Args:
            max_workers: Maximum number of parallel workers for page processing
        """
        self.max_workers = max_workers
        self.pii_detector = PIIDetector(sensitivity='high')
        self._page_cache = {}
        
        logger.info(f"✅ PageProcessor initialized (max workers: {max_workers})")
    
    def analyze_document_by_pages(
        self,
        file_buffer: BytesIO,
        filename: str,
        page_range: Optional[Tuple[int, int]] = None,
        parallel: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze PDF document page by page
        
        Args:
            file_buffer: BytesIO buffer containing PDF
            filename: Original filename
            page_range: Optional (start_page, end_page) tuple (1-indexed)
            parallel: Whether to use parallel processing
        
        Returns:
            {
                'fileName': str,
                'totalPages': int,
                'analyzedPages': int,
                'pageRange': str,
                'documentLevelIssues': List[Dict],
                'pageAnalysis': List[Dict],
                'aggregateMetrics': Dict
            }
        """
        logger.info(f"🔍 Starting page-level analysis for {filename}")
        
        try:
            # Read PDF metadata
            file_buffer.seek(0)
            pdf_reader = pypdf.PdfReader(file_buffer)
            total_pages = len(pdf_reader.pages)
            
            # Determine page range
            start_page, end_page = self._determine_page_range(total_pages, page_range)
            
            logger.info(f"📊 Analyzing pages {start_page}-{end_page} of {total_pages}")
            
            # Document-level analysis
            doc_level_issues = self._analyze_document_structure(pdf_reader)
            
            # Page-by-page analysis
            if parallel and (end_page - start_page + 1) > 3:
                page_analyses = self._analyze_pages_parallel(
                    file_buffer, start_page, end_page, total_pages
                )
            else:
                page_analyses = self._analyze_pages_sequential(
                    file_buffer, start_page, end_page, total_pages
                )
            
            # Aggregate metrics
            aggregate_metrics = self._calculate_aggregate_metrics(
                page_analyses, doc_level_issues
            )
            
            result = {
                'fileName': filename,
                'totalPages': total_pages,
                'analyzedPages': len(page_analyses),
                'pageRange': f"{start_page}-{end_page}",
                'documentLevelIssues': doc_level_issues,
                'pageAnalysis': page_analyses,
                'aggregateMetrics': aggregate_metrics
            }
            
            logger.info(f"✅ Page-level analysis complete: {len(page_analyses)} pages analyzed")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in page-level analysis: {e}")
            raise
    
    def analyze_single_page(
        self,
        file_buffer: BytesIO,
        page_number: int,  # 0-indexed
        total_pages: int
    ) -> Dict[str, Any]:
        """
        Analyze a single page for accessibility issues
        
        Args:
            file_buffer: BytesIO buffer containing PDF
            page_number: Page number (0-indexed)
            total_pages: Total number of pages in document
        
        Returns:
            Page analysis dictionary
        """
        logger.info(f"  📄 Analyzing page {page_number + 1}/{total_pages}")
        
        # Check cache
        cache_key = f"{id(file_buffer)}:{page_number}"
        if cache_key in self._page_cache:
            logger.debug(f"  📦 Using cached analysis for page {page_number + 1}")
            return self._page_cache[cache_key]
        
        issues = []
        pii_detected = False
        pii_details = []
        
        try:
            # Analyze with pypdf
            file_buffer.seek(0)
            pdf_reader = pypdf.PdfReader(file_buffer)
            page = pdf_reader.pages[page_number]
            
            # Analyze page structure
            page_structure = self._analyze_page_structure(page, page_number)
            issues.extend(page_structure['issues'])
            
            # Analyze with pdfplumber
            file_buffer.seek(0)
            with pdfplumber.open(file_buffer) as pdf:
                plumber_page = pdf.pages[page_number]
                
                # Extract text
                text_content = plumber_page.extract_text() or ""
                
                # Content metrics
                content_metrics = {
                    'textLength': len(text_content),
                    'wordCount': len(text_content.split()),
                    'imageCount': len(plumber_page.images) if plumber_page.images else 0,
                    'tableCount': len(plumber_page.extract_tables()),
                    'hasAnnotations': bool(plumber_page.annots)
                }
                
                # PII detection
                if text_content:
                    pii_result = self.pii_detector.detect_pii(text_content, page_number + 1)
                    pii_detected = pii_result['detected']
                    
                    if pii_detected:
                        pii_details = pii_result['details']
                        issues.append({
                            'description': f"Page contains {pii_result['count']} PII instance(s): {', '.join(pii_result['categories'])}",
                            'standard': 'Privacy/GDPR',
                            'category': 'Privacy',
                            'severity': 'high'
                        })
                
                # Check images
                if plumber_page.images:
                    image_issues = self._check_page_images(page, plumber_page)
                    issues.extend(image_issues)
                
                # Check forms
                if plumber_page.annots:
                    form_issues = self._check_page_forms(plumber_page)
                    issues.extend(form_issues)
                
                # Check reading order
                reading_order_issues = self._check_reading_order(page, page_number)
                issues.extend(reading_order_issues)
            
            # Calculate compliance score
            compliance_score = self._calculate_page_compliance(issues, content_metrics)
            
            result = {
                'pageNumber': page_number + 1,  # 1-indexed for display
                'issues': issues,
                'issueCount': len(issues),
                'piiDetected': pii_detected,
                'piiDetails': pii_details,
                'contentMetrics': content_metrics,
                'complianceScore': compliance_score,
                'hasImages': content_metrics['imageCount'] > 0,
                'hasForms': content_metrics.get('hasAnnotations', False),
                'hasText': content_metrics['textLength'] > 0
            }
            
            # Cache result
            self._page_cache[cache_key] = result
            
            logger.info(f"  ✅ Page {page_number + 1}: {len(issues)} issues, score: {compliance_score}")
            
            return result
            
        except Exception as e:
            logger.error(f"  ❌ Error analyzing page {page_number + 1}: {e}")
            return self._error_page_result(page_number + 1, str(e))
    
    def extract_page(
        self,
        file_buffer: BytesIO,
        page_number: int,  # 1-indexed
        output_format: str = 'pdf'
    ) -> BytesIO:
        """
        Extract a single page as a separate document
        
        Args:
            file_buffer: Source PDF buffer
            page_number: Page to extract (1-indexed)
            output_format: 'pdf', 'text', or 'json'
        
        Returns:
            BytesIO buffer containing extracted page
        """
        logger.info(f"📤 Extracting page {page_number} as {output_format}")
        
        if output_format == 'pdf':
            return self._extract_page_as_pdf(file_buffer, page_number)
        elif output_format == 'text':
            return self._extract_page_as_text(file_buffer, page_number)
        elif output_format == 'json':
            return self._extract_page_as_json(file_buffer, page_number)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _analyze_pages_parallel(
        self,
        file_buffer: BytesIO,
        start_page: int,
        end_page: int,
        total_pages: int
    ) -> List[Dict[str, Any]]:
        """Analyze pages in parallel"""
        page_analyses = []
        pdf_bytes = file_buffer.getvalue()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self.analyze_single_page,
                    BytesIO(pdf_bytes),
                    page_num,
                    total_pages
                ): page_num
                for page_num in range(start_page - 1, end_page)
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    page_analyses.append(result)
                except Exception as e:
                    page_num = futures[future]
                    logger.error(f"Error processing page {page_num + 1}: {e}")
                    page_analyses.append(self._error_page_result(page_num + 1, str(e)))
        
        # Sort by page number
        page_analyses.sort(key=lambda p: p['pageNumber'])
        
        return page_analyses
    
    def _analyze_pages_sequential(
        self,
        file_buffer: BytesIO,
        start_page: int,
        end_page: int,
        total_pages: int
    ) -> List[Dict[str, Any]]:
        """Analyze pages sequentially"""
        page_analyses = []
        pdf_bytes = file_buffer.getvalue()
        
        for page_num in range(start_page - 1, end_page):
            result = self.analyze_single_page(BytesIO(pdf_bytes), page_num, total_pages)
            page_analyses.append(result)
        
        return page_analyses
    
    def _analyze_document_structure(self, pdf_reader: pypdf.PdfReader) -> List[Dict]:
        """Analyze document-level structure"""
        issues = []
        
        try:
            catalog = pdf_reader.trailer.get('/Root')
            if catalog and hasattr(catalog, 'get_object'):
                catalog = catalog.get_object()
            
            # Check tag tree
            if catalog and '/StructTreeRoot' not in catalog:
                issues.append({
                    'description': 'Document does not contain a tag tree',
                    'standard': 'PDF/UA-1 §7.1',
                    'category': 'PDF/UA',
                    'scope': 'document',
                    'severity': 'high'
                })
            
            # Check language
            if catalog and '/Lang' not in catalog:
                issues.append({
                    'description': 'Document language is not declared',
                    'standard': 'WCAG 2.1 SC 3.1.1',
                    'category': 'WCAG',
                    'scope': 'document',
                    'severity': 'high'
                })
            
            # Check metadata
            metadata = pdf_reader.metadata
            if not metadata or not metadata.get('/Title'):
                issues.append({
                    'description': 'Document title is missing from metadata',
                    'standard': 'PDF/UA-1 §7.1',
                    'category': 'PDF/UA',
                    'scope': 'document',
                    'severity': 'medium'
                })
        
        except Exception as e:
            logger.warning(f"Error analyzing document structure: {e}")
        
        return issues
    
    def _analyze_page_structure(
        self,
        page: pypdf.PageObject,
        page_num: int
    ) -> Dict:
        """Analyze structural elements on a page"""
        issues = []
        
        try:
            # Check for structure elements
            if '/StructParents' not in page:
                issues.append({
                    'description': f'Page {page_num + 1} is not tagged with structure information',
                    'standard': 'PDF/UA-1 §7.1',
                    'category': 'PDF/UA',
                    'severity': 'high'
                })
        
        except Exception as e:
            logger.warning(f"Error analyzing page structure: {e}")
        
        return {'issues': issues}
    
    def _check_page_images(self, page: pypdf.PageObject, plumber_page) -> List[Dict]:
        """Check images on a specific page"""
        issues = []
        
        if plumber_page.images:
            image_count = len(plumber_page.images)
            issues.append({
                'description': f'Page contains {image_count} image(s) that may be missing alternative text',
                'standard': 'WCAG 2.1 SC 1.1.1',
                'category': 'WCAG',
                'severity': 'high'
            })
        
        return issues
    
    def _check_page_forms(self, plumber_page) -> List[Dict]:
        """Check form fields on a specific page"""
        issues = []
        
        if plumber_page.annots:
            form_fields = [a for a in plumber_page.annots 
                          if a.get('Subtype') in ['/Widget', 'Widget']]
            
            if form_fields:
                issues.append({
                    'description': f'Page contains {len(form_fields)} form field(s) that may lack proper labels',
                    'standard': 'WCAG 2.1 SC 1.3.1',
                    'category': 'WCAG',
                    'severity': 'high'
                })
        
        return issues
    
    def _check_reading_order(self, page: pypdf.PageObject, page_num: int) -> List[Dict]:
        """Check reading order on a page"""
        issues = []
        
        if '/StructParents' not in page:
            issues.append({
                'description': f'Page {page_num + 1} reading order cannot be verified (no structure tags)',
                'standard': 'WCAG 2.1 SC 1.3.2',
                'category': 'WCAG',
                'severity': 'medium'
            })
        
        return issues
    
    def _calculate_page_compliance(
        self,
        issues: List[Dict],
        metrics: Dict
    ) -> int:
        """Calculate compliance score for a single page (0-100)"""
        if not issues:
            return 100
        
        severity_weights = {
            'high': 20,
            'medium': 10,
            'low': 5
        }
        
        total_deduction = sum(
            severity_weights.get(issue.get('severity', 'medium'), 10)
            for issue in issues
        )
        
        score = max(0, 100 - total_deduction)
        return score
    
    def _calculate_aggregate_metrics(
        self,
        page_analyses: List[Dict],
        doc_issues: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate aggregate metrics across all pages"""
        total_issues = sum(p['issueCount'] for p in page_analyses) + len(doc_issues)
        pages_with_pii = sum(1 for p in page_analyses if p['piiDetected'])
        pages_with_images = sum(1 for p in page_analyses if p['hasImages'])
        pages_with_forms = sum(1 for p in page_analyses if p['hasForms'])
        
        avg_compliance = (
            sum(p['complianceScore'] for p in page_analyses) / len(page_analyses)
            if page_analyses else 0
        )
        
        issue_distribution = [
            {
                'pageNumber': p['pageNumber'],
                'issueCount': p['issueCount'],
                'complianceScore': p['complianceScore']
            }
            for p in page_analyses
        ]
        
        return {
            'totalIssues': total_issues,
            'documentLevelIssues': len(doc_issues),
            'pageLevelIssues': total_issues - len(doc_issues),
            'averageComplianceScore': round(avg_compliance, 1),
            'pagesWithPII': pages_with_pii,
            'pagesWithImages': pages_with_images,
            'pagesWithForms': pages_with_forms,
            'issueDistribution': issue_distribution,
            'mostProblematicPages': sorted(
                page_analyses,
                key=lambda p: p['issueCount'],
                reverse=True
            )[:5]
        }
    
    def _determine_page_range(
        self,
        total_pages: int,
        page_range: Optional[Tuple[int, int]]
    ) -> Tuple[int, int]:
        """Determine which pages to analyze"""
        if page_range:
            start, end = page_range
            start = max(1, min(start, total_pages))
            end = max(start, min(end, total_pages))
            return start, end
        
        return 1, total_pages
    
    def _extract_page_as_pdf(self, file_buffer: BytesIO, page_number: int) -> BytesIO:
        """Extract page as PDF"""
        file_buffer.seek(0)
        pdf_reader = pypdf.PdfReader(file_buffer)
        pdf_writer = pypdf.PdfWriter()
        
        pdf_writer.add_page(pdf_reader.pages[page_number - 1])
        
        output_buffer = BytesIO()
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)
        
        return output_buffer
    
    def _extract_page_as_text(self, file_buffer: BytesIO, page_number: int) -> BytesIO:
        """Extract page as plain text"""
        file_buffer.seek(0)
        with pdfplumber.open(file_buffer) as pdf:
            page = pdf.pages[page_number - 1]
            text = page.extract_text() or ""
            
            output_buffer = BytesIO(text.encode('utf-8'))
            output_buffer.seek(0)
            return output_buffer
    
    def _extract_page_as_json(self, file_buffer: BytesIO, page_number: int) -> BytesIO:
        """Extract page with full analysis as JSON"""
        import json
        
        file_buffer.seek(0)
        pdf_reader = pypdf.PdfReader(file_buffer)
        total_pages = len(pdf_reader.pages)
        
        analysis = self.analyze_single_page(file_buffer, page_number - 1, total_pages)
        
        output_buffer = BytesIO(json.dumps(analysis, indent=2).encode('utf-8'))
        output_buffer.seek(0)
        return output_buffer
    
    def _error_page_result(self, page_number: int, error_msg: str) -> Dict[str, Any]:
        """Return error result for a page"""
        return {
            'pageNumber': page_number,
            'issues': [{
                'description': f'Failed to analyze page: {error_msg[:100]}',
                'standard': 'N/A',
                'category': 'Error',
                'severity': 'high'
            }],
            'issueCount': 1,
            'piiDetected': False,
            'piiDetails': [],
            'contentMetrics': {},
            'complianceScore': 0,
            'hasImages': False,
            'hasForms': False,
            'hasText': False
        }
    
    def clear_cache(self):
        """Clear page analysis cache"""
        self._page_cache.clear()
        logger.info("🗑️ Page analysis cache cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            'max_workers': self.max_workers,
            'cache_size': len(self._page_cache),
            'pii_detector_stats': self.pii_detector.get_statistics()
        }

