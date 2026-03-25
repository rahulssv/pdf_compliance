"""Main compliance service orchestrating all operations with enhanced error handling"""
import logging
from typing import List, Dict, Any
from collections import Counter
from src.services.file_handler import FileHandler
from src.services.pdf_analyzer import PDFAnalyzer
from src.services.gemini_service import GeminiService

# Configure logging
logger = logging.getLogger(__name__)


class ComplianceService:
    """Main service for PDF accessibility compliance operations"""
    
    def __init__(self):
        self.file_handler = FileHandler()
        self.pdf_analyzer = PDFAnalyzer()
        self.gemini_service = GeminiService()
        logger.info(f"🚀 ComplianceService initialized (Gemini: {'✅' if self.gemini_service.is_initialized else '❌'})")
    
    def scan_files(self, file_urls: List[str]) -> Dict[str, Any]:
        """
        Scan PDF files for accessibility issues
        
        Args:
            file_urls: List of file locators
            
        Returns:
            Scan results with files and worst file information
        """
        logger.info(f"📊 Starting scan of {len(file_urls)} file(s)")
        files_results = []
        
        for idx, file_url in enumerate(file_urls, 1):
            try:
                logger.info(f"[{idx}/{len(file_urls)}] Processing: {file_url}")
                
                # Get the file
                file_path, filename = self.file_handler.get_file_path(file_url)
                logger.info(f"  📄 File loaded: {filename}")
                
                # Analyze the PDF
                analysis = self.pdf_analyzer.analyze_pdf(file_path, filename)
                
                files_results.append(analysis)
                
            except FileNotFoundError as e:
                logger.error(f"  ❌ File not found: {file_url}")
                # Add error result with appropriate status
                files_results.append({
                    'fileName': self._extract_filename(file_url),
                    'nonCompliancePercent': 100,
                    'complianceStatus': 'non-compliant',
                    'issues': [{
                        'description': f'File could not be accessed or does not exist.',
                        'standard': 'N/A',
                        'category': 'Error'
                    }]
                })
            except Exception as e:
                logger.error(f"  ❌ Error processing {file_url}: {str(e)}")
                # Add error result
                files_results.append({
                    'fileName': self._extract_filename(file_url),
                    'nonCompliancePercent': 100,
                    'complianceStatus': 'non-compliant',
                    'issues': [{
                        'description': f'Failed to process file: {str(e)[:100]}',
                        'standard': 'N/A',
                        'category': 'Error'
                    }]
                })
        
        # Find worst file
        worst_file = self._find_worst_file(files_results)
        
        logger.info(f"✅ Scan complete. Worst file: {worst_file['fileName']} ({worst_file['nonCompliancePercent']}%)")
        
        return {
            'files': files_results,
            'worstFile': worst_file
        }
    
    def remediate_files(self, file_urls: List[str]) -> Dict[str, Any]:
        """
        Provide remediation guidance for accessibility issues
        
        Args:
            file_urls: List of file locators
            
        Returns:
            Remediation results with fix suggestions
        """
        logger.info(f"🔧 Starting remediation for {len(file_urls)} file(s)")
        files_results = []
        
        for idx, file_url in enumerate(file_urls, 1):
            try:
                logger.info(f"[{idx}/{len(file_urls)}] Processing: {file_url}")
                
                # Get the file
                file_path, filename = self.file_handler.get_file_path(file_url)
                
                # Analyze the PDF
                analysis = self.pdf_analyzer.analyze_pdf(file_path, filename)
                
                # Add remediation guidance to each issue using Gemini
                issues_with_fixes = []
                for issue_idx, issue in enumerate(analysis['issues'], 1):
                    logger.info(f"  🤖 Generating fix {issue_idx}/{len(analysis['issues'])}")
                    
                    fix = self.gemini_service.generate_remediation(
                        issue['description'],
                        issue['standard']
                    )
                    
                    issues_with_fixes.append({
                        'description': issue['description'],
                        'standard': issue['standard'],
                        'fix': fix
                    })
                
                files_results.append({
                    'fileName': filename,
                    'issues': issues_with_fixes
                })
                
                logger.info(f"  ✅ Generated {len(issues_with_fixes)} remediation(s)")
                
            except Exception as e:
                logger.error(f"  ❌ Error processing {file_url}: {str(e)}")
                # Add error result
                files_results.append({
                    'fileName': self._extract_filename(file_url),
                    'issues': [{
                        'description': f'Failed to process file: {str(e)[:100]}',
                        'standard': 'N/A',
                        'fix': 'Please check the file path and ensure the file is accessible and not corrupted.'
                    }]
                })
        
        logger.info(f"✅ Remediation complete for {len(files_results)} file(s)")
        
        return {
            'files': files_results
        }
    
    def generate_dashboard(self, file_urls: List[str]) -> Dict[str, Any]:
        """
        Generate compliance dashboard for batch of files
        
        Args:
            file_urls: List of file locators
            
        Returns:
            Dashboard with aggregated compliance metrics
        """
        logger.info(f"📈 Generating dashboard for {len(file_urls)} file(s)")
        
        # First, scan all files
        scan_results = self.scan_files(file_urls)
        files = scan_results['files']
        
        # Calculate totals
        total_scanned = len(files)
        total_issues = sum(len(f['issues']) for f in files)
        
        # Calculate fixable issues (exclude error category)
        total_fixable = sum(
            len([i for i in f['issues'] if i.get('category') != 'Error']) 
            for f in files
        )
        
        # Compliance breakdown
        compliance_breakdown = self._calculate_compliance_breakdown(files)
        
        # Top issue types
        top_issue_types = self._calculate_top_issue_types(files)
        
        # Standard violation frequency
        standard_violation_frequency = self._calculate_standard_violations(files)
        
        dashboard = {
            'totalScanned': total_scanned,
            'totalIssues': total_issues,
            'totalFixable': total_fixable,
            'complianceBreakdown': compliance_breakdown,
            'topIssueTypes': top_issue_types,
            'standardViolationFrequency': standard_violation_frequency
        }
        
        logger.info(f"✅ Dashboard generated: {total_scanned} scanned, {total_issues} issues, {total_fixable} fixable")
        
        return dashboard
    
    def _extract_filename(self, file_url: str) -> str:
        """Extract filename from URL or path"""
        # Handle Windows and Unix paths
        if '\\' in file_url:
            return file_url.split('\\')[-1]
        return file_url.split('/')[-1]
    
    def _find_worst_file(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find the file with highest non-compliance percentage"""
        if not files:
            return {'fileName': '', 'nonCompliancePercent': 0}
        
        worst = max(files, key=lambda f: f['nonCompliancePercent'])
        return {
            'fileName': worst['fileName'],
            'nonCompliancePercent': worst['nonCompliancePercent']
        }
    
    def _calculate_compliance_breakdown(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate compliance status breakdown ensuring all files are counted"""
        status_counts = Counter(f['complianceStatus'] for f in files)
        
        # Build breakdown in consistent order
        breakdown = []
        for status in ['compliant', 'partially-compliant', 'non-compliant']:
            count = status_counts.get(status, 0)
            if count > 0:
                breakdown.append({
                    'status': status,
                    'count': count
                })
        
        # Verify arithmetic: sum should equal total files
        total_in_breakdown = sum(item['count'] for item in breakdown)
        if total_in_breakdown != len(files):
            logger.warning(f"⚠️ Breakdown sum ({total_in_breakdown}) != total files ({len(files)})")
        
        return breakdown
    
    def _calculate_top_issue_types(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate top issue types across all files (excluding errors)"""
        issue_types = []
        
        for file in files:
            for issue in file['issues']:
                # Skip error category issues
                if issue.get('category') == 'Error':
                    continue
                # Extract issue type from description
                issue_type = self._extract_issue_type(issue['description'])
                issue_types.append(issue_type)
        
        if not issue_types:
            return []
        
        # Count and sort
        type_counts = Counter(issue_types)
        top_types = type_counts.most_common(10)  # Top 10
        
        result = [
            {'type': issue_type, 'count': count}
            for issue_type, count in top_types
        ]
        
        logger.info(f"  📊 Top issue types: {len(result)} unique types")
        return result
    
    def _calculate_standard_violations(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate standard violation frequency (excluding errors)"""
        standards = []
        
        for file in files:
            for issue in file['issues']:
                # Skip error category issues
                if issue.get('category') == 'Error' or issue.get('standard') == 'N/A':
                    continue
                # Extract standard family (e.g., "WCAG 2.1" from "WCAG 2.1 SC 1.1.1")
                standard = self._extract_standard_family(issue['standard'])
                standards.append(standard)
        
        if not standards:
            return []
        
        # Count and sort
        standard_counts = Counter(standards)
        top_standards = standard_counts.most_common(10)  # Top 10
        
        result = [
            {'standard': standard, 'count': count}
            for standard, count in top_standards
        ]
        
        logger.info(f"  📊 Standard violations: {len(result)} unique standards")
        return result
    
    def _extract_issue_type(self, description: str) -> str:
        """Extract a readable issue type from description"""
        description_lower = description.lower()
        
        if 'tag tree' in description_lower:
            return 'No Tag Tree'
        elif 'language' in description_lower:
            return 'Missing Document Language'
        elif 'alternative text' in description_lower or 'alt text' in description_lower:
            return 'Missing Alt Text'
        elif 'form field' in description_lower:
            return 'Unlabeled Form Fields'
        elif 'scanned' in description_lower:
            return 'Scanned Document'
        elif 'metadata' in description_lower:
            return 'Missing Metadata'
        elif 'structure' in description_lower:
            return 'Poor Document Structure'
        else:
            return 'Other Accessibility Issue'
    
    def _extract_standard_family(self, standard: str) -> str:
        """Extract standard family from full standard reference"""
        if 'WCAG' in standard:
            return 'WCAG 2.1'
        elif 'PDF/UA' in standard:
            return 'PDF/UA-1'
        elif 'Section 508' in standard:
            return 'Section 508'
        elif 'ADA' in standard:
            return 'ADA'
        elif 'EAA' in standard:
            return 'EAA'
        else:
            return standard

