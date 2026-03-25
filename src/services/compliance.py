"""Main compliance service orchestrating all operations"""
from typing import List, Dict, Any
from collections import Counter
from src.services.file_handler import FileHandler
from src.services.pdf_analyzer import PDFAnalyzer
from src.services.gemini_service import GeminiService


class ComplianceService:
    """Main service for PDF accessibility compliance operations"""
    
    def __init__(self):
        self.file_handler = FileHandler()
        self.pdf_analyzer = PDFAnalyzer()
        self.gemini_service = GeminiService()
    
    def scan_files(self, file_urls: List[str]) -> Dict[str, Any]:
        """
        Scan PDF files for accessibility issues
        
        Args:
            file_urls: List of file locators
            
        Returns:
            Scan results with files and worst file information
        """
        files_results = []
        
        for file_url in file_urls:
            try:
                # Get the file
                file_path, filename = self.file_handler.get_file_path(file_url)
                
                # Analyze the PDF
                analysis = self.pdf_analyzer.analyze_pdf(file_path, filename)
                
                files_results.append(analysis)
                
            except Exception as e:
                print(f"Error processing {file_url}: {str(e)}")
                # Add error result
                files_results.append({
                    'fileName': file_url.split('/')[-1],
                    'nonCompliancePercent': 100,
                    'complianceStatus': 'non-compliant',
                    'issues': [{
                        'description': f'Failed to process file: {str(e)}',
                        'standard': 'N/A',
                        'category': 'Error'
                    }]
                })
        
        # Find worst file
        worst_file = self._find_worst_file(files_results)
        
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
        files_results = []
        
        for file_url in file_urls:
            try:
                # Get the file
                file_path, filename = self.file_handler.get_file_path(file_url)
                
                # Analyze the PDF
                analysis = self.pdf_analyzer.analyze_pdf(file_path, filename)
                
                # Add remediation guidance to each issue
                issues_with_fixes = []
                for issue in analysis['issues']:
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
                
            except Exception as e:
                print(f"Error processing {file_url}: {str(e)}")
                # Add error result
                files_results.append({
                    'fileName': file_url.split('/')[-1],
                    'issues': [{
                        'description': f'Failed to process file: {str(e)}',
                        'standard': 'N/A',
                        'fix': 'Please check the file path and ensure the file is accessible.'
                    }]
                })
        
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
        # First, scan all files
        scan_results = self.scan_files(file_urls)
        files = scan_results['files']
        
        # Calculate totals
        total_scanned = len(files)
        total_issues = sum(len(f['issues']) for f in files)
        
        # For simplicity, assume all issues are fixable
        # In a real implementation, you might categorize some as non-fixable
        total_fixable = total_issues
        
        # Compliance breakdown
        compliance_breakdown = self._calculate_compliance_breakdown(files)
        
        # Top issue types
        top_issue_types = self._calculate_top_issue_types(files)
        
        # Standard violation frequency
        standard_violation_frequency = self._calculate_standard_violations(files)
        
        return {
            'totalScanned': total_scanned,
            'totalIssues': total_issues,
            'totalFixable': total_fixable,
            'complianceBreakdown': compliance_breakdown,
            'topIssueTypes': top_issue_types,
            'standardViolationFrequency': standard_violation_frequency
        }
    
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
        """Calculate compliance status breakdown"""
        status_counts = Counter(f['complianceStatus'] for f in files)
        
        breakdown = []
        for status in ['compliant', 'partially-compliant', 'non-compliant']:
            count = status_counts.get(status, 0)
            if count > 0:
                breakdown.append({
                    'status': status,
                    'count': count
                })
        
        return breakdown
    
    def _calculate_top_issue_types(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate top issue types across all files"""
        issue_types = []
        
        for file in files:
            for issue in file['issues']:
                # Extract issue type from description
                issue_type = self._extract_issue_type(issue['description'])
                issue_types.append(issue_type)
        
        if not issue_types:
            return []
        
        # Count and sort
        type_counts = Counter(issue_types)
        top_types = type_counts.most_common(5)  # Top 5
        
        return [
            {'type': issue_type, 'count': count}
            for issue_type, count in top_types
        ]
    
    def _calculate_standard_violations(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate standard violation frequency"""
        standards = []
        
        for file in files:
            for issue in file['issues']:
                # Extract standard family (e.g., "WCAG 2.1" from "WCAG 2.1 SC 1.1.1")
                standard = self._extract_standard_family(issue['standard'])
                standards.append(standard)
        
        if not standards:
            return []
        
        # Count and sort
        standard_counts = Counter(standards)
        top_standards = standard_counts.most_common(5)  # Top 5
        
        return [
            {'standard': standard, 'count': count}
            for standard, count in top_standards
        ]
    
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

# Made with Bob
