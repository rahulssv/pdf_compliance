"""
Enhanced Reporting System

This module provides comprehensive report generation capabilities for
PDF accessibility compliance analysis results. Supports multiple output
formats including PDF, HTML, JSON, and CSV.

Features:
- Multi-format export (PDF, HTML, JSON, CSV)
- Executive summaries
- Detailed issue breakdowns
- Visual charts and graphs
- Customizable templates
- Branding support
"""

import json
import csv
import logging
from typing import Dict, List, Optional, Any, BinaryIO
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from io import BytesIO, StringIO
from enum import Enum

try:
    from reportlab.lib.pagesizes import A4, LETTER, landscape
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Supported report formats"""
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"


class ReportSection(Enum):
    """Report sections"""
    EXECUTIVE_SUMMARY = "executive_summary"
    COMPLIANCE_OVERVIEW = "compliance_overview"
    ISSUE_DETAILS = "issue_details"
    REMEDIATION_PLAN = "remediation_plan"
    PAGE_ANALYSIS = "page_analysis"
    PII_SUMMARY = "pii_summary"
    VALIDATION_METRICS = "validation_metrics"
    RECOMMENDATIONS = "recommendations"


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    format: ReportFormat
    include_sections: List[ReportSection]
    include_charts: bool = True
    include_page_details: bool = True
    include_pii_details: bool = False  # Privacy-sensitive
    branding: Optional[Dict[str, str]] = None
    custom_css: Optional[str] = None
    page_size: str = "A4"  # For PDF reports
    orientation: str = "portrait"  # portrait or landscape
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'format': self.format.value,
            'include_sections': [s.value for s in self.include_sections],
            'include_charts': self.include_charts,
            'include_page_details': self.include_page_details,
            'include_pii_details': self.include_pii_details,
            'branding': self.branding,
            'page_size': self.page_size,
            'orientation': self.orientation
        }


@dataclass
class ComplianceReport:
    """Complete compliance analysis report data"""
    document_name: str
    analysis_date: datetime
    compliance_score: float
    compliance_level: str
    wcag_level: str
    total_pages: int
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    auto_fixable: int
    manual_fixes_required: int
    issues: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    page_analyses: Optional[List[Dict[str, Any]]] = None
    pii_summary: Optional[Dict[str, Any]] = None
    validation_metrics: Optional[Dict[str, Any]] = None
    remediation_summary: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['analysis_date'] = self.analysis_date.isoformat()
        return data


class ReportGenerator:
    """
    Generates comprehensive compliance reports in multiple formats.
    
    Supports:
    - PDF reports with charts and branding
    - HTML reports with interactive elements
    - JSON exports for API integration
    - CSV exports for spreadsheet analysis
    - Markdown reports for documentation
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize the report generator.
        
        Args:
            template_dir: Directory containing custom report templates
        """
        self.template_dir = Path(template_dir) if template_dir else Path("templates/reports")
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("ReportGenerator initialized")
    
    def generate_report(
        self,
        report_data: ComplianceReport,
        config: ReportConfig,
        output_path: Optional[str] = None
    ) -> BytesIO:
        """
        Generate a compliance report in the specified format.
        
        Args:
            report_data: The compliance analysis data
            config: Report configuration
            output_path: Optional path to save the report
            
        Returns:
            BytesIO: The generated report as a byte stream
        """
        logger.info(
            f"Generating {config.format.value} report for '{report_data.document_name}'"
        )
        
        # Generate report based on format
        if config.format == ReportFormat.JSON:
            output = self._generate_json_report(report_data, config)
        elif config.format == ReportFormat.CSV:
            output = self._generate_csv_report(report_data, config)
        elif config.format == ReportFormat.HTML:
            output = self._generate_html_report(report_data, config)
        elif config.format == ReportFormat.MARKDOWN:
            output = self._generate_markdown_report(report_data, config)
        elif config.format == ReportFormat.PDF:
            output = self._generate_pdf_report(report_data, config)
        else:
            raise ValueError(f"Unsupported report format: {config.format}")
        
        # Save to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'wb') as f:
                f.write(output.getvalue())
            
            logger.info(f"Report saved to {output_path}")
        
        # Reset stream position
        output.seek(0)
        return output
    
    def _generate_json_report(
        self,
        report_data: ComplianceReport,
        config: ReportConfig
    ) -> BytesIO:
        """Generate JSON format report"""
        data = report_data.to_dict()
        
        # Filter sections based on config
        filtered_data = self._filter_sections(data, config)
        
        # Convert to JSON
        json_str = json.dumps(filtered_data, indent=2, default=str)
        
        output = BytesIO()
        output.write(json_str.encode('utf-8'))
        
        logger.debug(f"Generated JSON report ({len(json_str)} bytes)")
        return output
    
    def _generate_csv_report(
        self,
        report_data: ComplianceReport,
        config: ReportConfig
    ) -> BytesIO:
        """Generate CSV format report (issues list)"""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Issue ID',
            'Category',
            'Severity',
            'WCAG Criterion',
            'Description',
            'Location',
            'Impact',
            'Complexity',
            'Estimated Time',
            'Auto-Fixable'
        ])
        
        # Write issues
        for idx, issue in enumerate(report_data.issues, 1):
            writer.writerow([
                f"ISSUE-{idx:03d}",
                issue.get('category', 'N/A'),
                issue.get('severity', 'N/A'),
                issue.get('wcag_criterion', 'N/A'),
                issue.get('description', 'N/A'),
                issue.get('location', 'N/A'),
                issue.get('impact', 'N/A'),
                issue.get('remediation_complexity', 'N/A'),
                issue.get('estimated_time', 'N/A'),
                'Yes' if issue.get('auto_fixable', False) else 'No'
            ])
        
        # Convert to bytes
        csv_bytes = output.getvalue().encode('utf-8')
        byte_output = BytesIO(csv_bytes)
        
        logger.debug(f"Generated CSV report ({len(csv_bytes)} bytes)")
        return byte_output
    
    def _generate_html_report(
        self,
        report_data: ComplianceReport,
        config: ReportConfig
    ) -> BytesIO:
        """Generate HTML format report"""
        html_content = self._build_html_report(report_data, config)
        
        output = BytesIO()
        output.write(html_content.encode('utf-8'))
        
        logger.debug(f"Generated HTML report ({len(html_content)} bytes)")
        return output
    
    def _generate_markdown_report(
        self,
        report_data: ComplianceReport,
        config: ReportConfig
    ) -> BytesIO:
        """Generate Markdown format report"""
        md_content = self._build_markdown_report(report_data, config)
        
        output = BytesIO()
        output.write(md_content.encode('utf-8'))
        
        logger.debug(f"Generated Markdown report ({len(md_content)} bytes)")
        return output
    
    def _generate_pdf_report(
        self,
        report_data: ComplianceReport,
        config: ReportConfig
    ) -> BytesIO:
        """Generate PDF format report"""
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("PDF export requires reportlab. Install dependencies from requirements.txt.")

        page_sizes = {
            "A4": A4,
            "LETTER": LETTER,
        }
        base_size = page_sizes.get(config.page_size.upper(), A4)
        page_size = landscape(base_size) if config.orientation.lower() == "landscape" else base_size

        output = BytesIO()
        pdf = canvas.Canvas(output, pagesize=page_size)
        width, height = page_size
        y = height - 40

        def new_page_if_needed(lines: int = 1):
            nonlocal y
            if y < 40 + lines * 14:
                pdf.showPage()
                y = height - 40

        def draw_line(text: str, size: int = 10, bold: bool = False):
            nonlocal y
            new_page_if_needed()
            font = "Helvetica-Bold" if bold else "Helvetica"
            pdf.setFont(font, size)
            pdf.drawString(40, y, text[:140])
            y -= 14 if size <= 10 else 18

        draw_line("PDF Accessibility Compliance Report", size=16, bold=True)
        draw_line(f"Document: {report_data.document_name}", bold=True)
        draw_line(f"Analysis date: {report_data.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}")
        draw_line(f"Compliance score: {report_data.compliance_score:.1f}/100")
        draw_line(f"Compliance level: {report_data.compliance_level} | WCAG: {report_data.wcag_level}")
        y -= 4

        draw_line("Issue Summary", size=12, bold=True)
        draw_line(
            f"Total: {report_data.total_issues} | "
            f"Critical: {report_data.critical_issues} | "
            f"High: {report_data.high_issues} | "
            f"Medium: {report_data.medium_issues} | "
            f"Low: {report_data.low_issues}"
        )
        draw_line(
            f"Auto-fixable: {report_data.auto_fixable} | Manual required: {report_data.manual_fixes_required}"
        )
        y -= 4

        if report_data.issues:
            draw_line("Top Issues", size=12, bold=True)
            for idx, issue in enumerate(report_data.issues[:20], 1):
                new_page_if_needed(lines=2)
                draw_line(
                    f"{idx}. [{issue.get('severity', 'N/A')}] {issue.get('description', 'N/A')}",
                    size=10,
                    bold=False,
                )
                draw_line(f"   Standard: {issue.get('wcag_criterion', issue.get('standard', 'N/A'))}", size=9)

        if report_data.recommendations:
            y -= 4
            draw_line("Recommendations", size=12, bold=True)
            for idx, recommendation in enumerate(report_data.recommendations[:10], 1):
                draw_line(
                    f"{idx}. ({recommendation.get('priority', 'medium')}) {recommendation.get('action', 'N/A')}",
                    size=10,
                )

        pdf.showPage()
        pdf.save()
        output.seek(0)
        logger.debug("Generated PDF report")
        return output
    
    def _build_html_report(
        self,
        report_data: ComplianceReport,
        config: ReportConfig
    ) -> str:
        """Build HTML report content"""
        # Get branding
        branding = config.branding or {}
        company_name = branding.get('company_name', 'PDF Compliance Engine')
        logo_url = branding.get('logo_url', '')
        primary_color = branding.get('primary_color', '#2563eb')
        
        # Build HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Accessibility Compliance Report - {report_data.document_name}</title>
    <style>
        {self._get_default_css(primary_color)}
        {config.custom_css or ''}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="report-header">
            {f'<img src="{logo_url}" alt="Logo" class="logo">' if logo_url else ''}
            <h1>PDF Accessibility Compliance Report</h1>
            <p class="company-name">{company_name}</p>
        </header>
        
        <!-- Document Info -->
        <section class="document-info">
            <h2>Document Information</h2>
            <table>
                <tr><th>Document Name:</th><td>{report_data.document_name}</td></tr>
                <tr><th>Analysis Date:</th><td>{report_data.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                <tr><th>Total Pages:</th><td>{report_data.total_pages}</td></tr>
            </table>
        </section>
"""
        
        # Executive Summary
        if ReportSection.EXECUTIVE_SUMMARY in config.include_sections:
            html += self._build_executive_summary_html(report_data)
        
        # Compliance Overview
        if ReportSection.COMPLIANCE_OVERVIEW in config.include_sections:
            html += self._build_compliance_overview_html(report_data, config)
        
        # Issue Details
        if ReportSection.ISSUE_DETAILS in config.include_sections:
            html += self._build_issue_details_html(report_data)
        
        # Remediation Plan
        if ReportSection.REMEDIATION_PLAN in config.include_sections:
            html += self._build_remediation_plan_html(report_data)
        
        # Page Analysis
        if ReportSection.PAGE_ANALYSIS in config.include_sections and config.include_page_details:
            html += self._build_page_analysis_html(report_data)
        
        # PII Summary
        if ReportSection.PII_SUMMARY in config.include_sections and config.include_pii_details:
            html += self._build_pii_summary_html(report_data)
        
        # Recommendations
        if ReportSection.RECOMMENDATIONS in config.include_sections:
            html += self._build_recommendations_html(report_data)
        
        # Footer
        html += f"""
        <footer class="report-footer">
            <p>Generated by {company_name} PDF Accessibility Compliance Engine</p>
            <p>Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>
</body>
</html>"""
        
        return html
    
    def _build_markdown_report(
        self,
        report_data: ComplianceReport,
        config: ReportConfig
    ) -> str:
        """Build Markdown report content"""
        md = f"""# PDF Accessibility Compliance Report

## Document Information

- **Document Name:** {report_data.document_name}
- **Analysis Date:** {report_data.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}
- **Total Pages:** {report_data.total_pages}

---

"""
        
        # Executive Summary
        if ReportSection.EXECUTIVE_SUMMARY in config.include_sections:
            md += f"""## Executive Summary

- **Compliance Score:** {report_data.compliance_score:.1f}/100
- **Compliance Level:** {report_data.compliance_level}
- **WCAG Level:** {report_data.wcag_level}
- **Total Issues:** {report_data.total_issues}
  - Critical: {report_data.critical_issues}
  - High: {report_data.high_issues}
  - Medium: {report_data.medium_issues}
  - Low: {report_data.low_issues}

---

"""
        
        # Issue Details
        if ReportSection.ISSUE_DETAILS in config.include_sections:
            md += "## Issues Identified\n\n"
            
            for idx, issue in enumerate(report_data.issues, 1):
                md += f"""### Issue {idx}: {issue.get('description', 'N/A')}

- **Category:** {issue.get('category', 'N/A')}
- **Severity:** {issue.get('severity', 'N/A')}
- **WCAG Criterion:** {issue.get('wcag_criterion', 'N/A')}
- **Location:** {issue.get('location', 'N/A')}
- **Impact:** {issue.get('impact', 'N/A')}
- **Complexity:** {issue.get('remediation_complexity', 'N/A')}
- **Estimated Time:** {issue.get('estimated_time', 'N/A')}

"""
        
        # Recommendations
        if ReportSection.RECOMMENDATIONS in config.include_sections:
            md += "## Recommendations\n\n"
            
            for idx, rec in enumerate(report_data.recommendations, 1):
                md += f"""{idx}. **{rec.get('action', 'N/A')}** (Priority: {rec.get('priority', 'N/A')})
   - Benefit: {rec.get('benefit', 'N/A')}

"""
        
        md += f"\n---\n\n*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return md
    
    def _build_executive_summary_html(self, report_data: ComplianceReport) -> str:
        """Build executive summary section"""
        # Determine status color
        if report_data.compliance_score >= 90:
            status_class = "status-excellent"
            status_text = "Excellent"
        elif report_data.compliance_score >= 75:
            status_class = "status-good"
            status_text = "Good"
        elif report_data.compliance_score >= 60:
            status_class = "status-fair"
            status_text = "Fair"
        else:
            status_class = "status-poor"
            status_text = "Poor"
        
        return f"""
        <section class="executive-summary">
            <h2>Executive Summary</h2>
            <div class="score-card">
                <div class="score-circle {status_class}">
                    <span class="score-value">{report_data.compliance_score:.0f}</span>
                    <span class="score-label">Compliance Score</span>
                </div>
                <div class="score-details">
                    <p><strong>Status:</strong> <span class="{status_class}">{status_text}</span></p>
                    <p><strong>WCAG Level:</strong> {report_data.wcag_level}</p>
                    <p><strong>Compliance Level:</strong> {report_data.compliance_level}</p>
                </div>
            </div>
            
            <div class="issue-summary">
                <h3>Issue Summary</h3>
                <div class="issue-grid">
                    <div class="issue-stat critical">
                        <span class="stat-value">{report_data.critical_issues}</span>
                        <span class="stat-label">Critical</span>
                    </div>
                    <div class="issue-stat high">
                        <span class="stat-value">{report_data.high_issues}</span>
                        <span class="stat-label">High</span>
                    </div>
                    <div class="issue-stat medium">
                        <span class="stat-value">{report_data.medium_issues}</span>
                        <span class="stat-label">Medium</span>
                    </div>
                    <div class="issue-stat low">
                        <span class="stat-value">{report_data.low_issues}</span>
                        <span class="stat-label">Low</span>
                    </div>
                </div>
            </div>
            
            <div class="remediation-summary">
                <p><strong>Auto-Fixable Issues:</strong> {report_data.auto_fixable} ({(report_data.auto_fixable/report_data.total_issues*100) if report_data.total_issues > 0 else 0:.1f}%)</p>
                <p><strong>Manual Fixes Required:</strong> {report_data.manual_fixes_required}</p>
            </div>
        </section>
"""
    
    def _build_compliance_overview_html(
        self,
        report_data: ComplianceReport,
        config: ReportConfig
    ) -> str:
        """Build compliance overview section"""
        return f"""
        <section class="compliance-overview">
            <h2>Compliance Overview</h2>
            <p>This document has been analyzed against WCAG 2.1 Level AA standards.</p>
            
            <div class="metrics-grid">
                <div class="metric">
                    <h4>Total Issues</h4>
                    <p class="metric-value">{report_data.total_issues}</p>
                </div>
                <div class="metric">
                    <h4>Pages Analyzed</h4>
                    <p class="metric-value">{report_data.total_pages}</p>
                </div>
                <div class="metric">
                    <h4>Compliance Level</h4>
                    <p class="metric-value">{report_data.compliance_level}</p>
                </div>
                <div class="metric">
                    <h4>WCAG Level</h4>
                    <p class="metric-value">{report_data.wcag_level}</p>
                </div>
            </div>
        </section>
"""
    
    def _build_issue_details_html(self, report_data: ComplianceReport) -> str:
        """Build issue details section"""
        html = """
        <section class="issue-details">
            <h2>Detailed Issues</h2>
            <div class="issues-list">
"""
        
        for idx, issue in enumerate(report_data.issues, 1):
            severity_class = issue.get('severity', 'low').lower()
            html += f"""
                <div class="issue-card {severity_class}">
                    <div class="issue-header">
                        <h3>Issue {idx}: {issue.get('description', 'N/A')}</h3>
                        <span class="severity-badge {severity_class}">{issue.get('severity', 'N/A')}</span>
                    </div>
                    <div class="issue-body">
                        <p><strong>Category:</strong> {issue.get('category', 'N/A')}</p>
                        <p><strong>WCAG Criterion:</strong> {issue.get('wcag_criterion', 'N/A')}</p>
                        <p><strong>Location:</strong> {issue.get('location', 'N/A')}</p>
                        <p><strong>Impact:</strong> {issue.get('impact', 'N/A')}</p>
                        <p><strong>Remediation Complexity:</strong> {issue.get('remediation_complexity', 'N/A')}</p>
                        <p><strong>Estimated Time:</strong> {issue.get('estimated_time', 'N/A')}</p>
                        {f'<p><strong>Auto-Fixable:</strong> Yes</p>' if issue.get('auto_fixable') else ''}
                    </div>
                </div>
"""
        
        html += """
            </div>
        </section>
"""
        return html
    
    def _build_remediation_plan_html(self, report_data: ComplianceReport) -> str:
        """Build remediation plan section"""
        return f"""
        <section class="remediation-plan">
            <h2>Remediation Plan</h2>
            <p>Recommended approach to address identified issues:</p>
            
            <div class="remediation-steps">
                <div class="step">
                    <h4>Step 1: Automated Fixes</h4>
                    <p>{report_data.auto_fixable} issues can be automatically fixed by the system.</p>
                    <p><strong>Action:</strong> Run automated remediation tool</p>
                </div>
                
                <div class="step">
                    <h4>Step 2: Critical Issues</h4>
                    <p>{report_data.critical_issues} critical issues require immediate attention.</p>
                    <p><strong>Priority:</strong> Address within 24 hours</p>
                </div>
                
                <div class="step">
                    <h4>Step 3: High Priority Issues</h4>
                    <p>{report_data.high_issues} high priority issues should be addressed next.</p>
                    <p><strong>Priority:</strong> Address within 1 week</p>
                </div>
                
                <div class="step">
                    <h4>Step 4: Medium & Low Priority</h4>
                    <p>{report_data.medium_issues + report_data.low_issues} remaining issues can be addressed in subsequent iterations.</p>
                    <p><strong>Priority:</strong> Address within 1 month</p>
                </div>
            </div>
        </section>
"""
    
    def _build_page_analysis_html(self, report_data: ComplianceReport) -> str:
        """Build page analysis section"""
        if not report_data.page_analyses:
            return ""
        
        html = """
        <section class="page-analysis">
            <h2>Page-by-Page Analysis</h2>
            <div class="pages-list">
"""
        
        for page in report_data.page_analyses:
            page_num = page.get('page_number', 'N/A')
            page_score = page.get('page_score', 0)
            page_issues = page.get('issues', [])
            
            html += f"""
                <div class="page-card">
                    <h3>Page {page_num}</h3>
                    <p><strong>Score:</strong> {page_score:.1f}/100</p>
                    <p><strong>Issues:</strong> {len(page_issues)}</p>
                </div>
"""
        
        html += """
            </div>
        </section>
"""
        return html
    
    def _build_pii_summary_html(self, report_data: ComplianceReport) -> str:
        """Build PII summary section"""
        if not report_data.pii_summary:
            return ""
        
        pii_data = report_data.pii_summary
        total_pii = pii_data.get('total_detected', 0)
        
        return f"""
        <section class="pii-summary">
            <h2>PII Detection Summary</h2>
            <div class="alert alert-warning">
                <p><strong>⚠️ Privacy Notice:</strong> {total_pii} instances of Personally Identifiable Information detected.</p>
            </div>
            <p>PII types detected: {', '.join(pii_data.get('types', []))}</p>
            <p><strong>Recommendation:</strong> Review and redact sensitive information before sharing this document.</p>
        </section>
"""
    
    def _build_recommendations_html(self, report_data: ComplianceReport) -> str:
        """Build recommendations section"""
        html = """
        <section class="recommendations">
            <h2>Recommendations</h2>
            <div class="recommendations-list">
"""
        
        for idx, rec in enumerate(report_data.recommendations, 1):
            priority_class = rec.get('priority', 'low').lower()
            html += f"""
                <div class="recommendation-card {priority_class}">
                    <h4>{idx}. {rec.get('action', 'N/A')}</h4>
                    <p><strong>Priority:</strong> <span class="priority-badge {priority_class}">{rec.get('priority', 'N/A')}</span></p>
                    <p><strong>Benefit:</strong> {rec.get('benefit', 'N/A')}</p>
                </div>
"""
        
        html += """
            </div>
        </section>
"""
        return html
    
    def _get_default_css(self, primary_color: str) -> str:
        """Get default CSS styles for HTML reports"""
        return f"""
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: white;
        }}
        
        .report-header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 3px solid {primary_color};
            margin-bottom: 30px;
        }}
        
        .report-header h1 {{
            color: {primary_color};
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .logo {{
            max-width: 200px;
            margin-bottom: 20px;
        }}
        
        .company-name {{
            color: #666;
            font-size: 1.2em;
        }}
        
        section {{
            margin-bottom: 40px;
            padding: 20px;
            background: #fafafa;
            border-radius: 8px;
        }}
        
        h2 {{
            color: {primary_color};
            font-size: 1.8em;
            margin-bottom: 20px;
            border-bottom: 2px solid {primary_color};
            padding-bottom: 10px;
        }}
        
        h3 {{
            color: #444;
            font-size: 1.3em;
            margin: 15px 0 10px 0;
        }}
        
        h4 {{
            color: #555;
            font-size: 1.1em;
            margin: 10px 0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            background: {primary_color};
            color: white;
            font-weight: 600;
        }}
        
        .score-card {{
            display: flex;
            align-items: center;
            gap: 40px;
            margin: 20px 0;
        }}
        
        .score-circle {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            border: 8px solid;
        }}
        
        .score-circle.status-excellent {{
            border-color: #10b981;
            background: #d1fae5;
        }}
        
        .score-circle.status-good {{
            border-color: #3b82f6;
            background: #dbeafe;
        }}
        
        .score-circle.status-fair {{
            border-color: #f59e0b;
            background: #fef3c7;
        }}
        
        .score-circle.status-poor {{
            border-color: #ef4444;
            background: #fee2e2;
        }}
        
        .score-value {{
            font-size: 3em;
        }}
        
        .score-label {{
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .issue-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin: 20px 0;
        }}
        
        .issue-stat {{
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            background: white;
        }}
        
        .issue-stat.critical {{
            border-left: 4px solid #ef4444;
        }}
        
        .issue-stat.high {{
            border-left: 4px solid #f59e0b;
        }}
        
        .issue-stat.medium {{
            border-left: 4px solid #3b82f6;
        }}
        
        .issue-stat.low {{
            border-left: 4px solid #10b981;
        }}
        
        .stat-value {{
            display: block;
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }}
        
        .stat-label {{
            display: block;
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin: 20px 0;
        }}
        
        .metric {{
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: {primary_color};
        }}
        
        .issue-card {{
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            border-left: 4px solid;
        }}
        
        .issue-card.critical {{
            border-left-color: #ef4444;
        }}
        
        .issue-card.high {{
            border-left-color: #f59e0b;
        }}
        
        .issue-card.medium {{
            border-left-color: #3b82f6;
        }}
        
        .issue-card.low {{
            border-left-color: #10b981;
        }}
        
        .issue-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .severity-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            color: white;
        }}
        
        .severity-badge.critical {{
            background: #ef4444;
        }}
        
        .severity-badge.high {{
            background: #f59e0b;
        }}
        
        .severity-badge.medium {{
            background: #3b82f6;
        }}
        
        .severity-badge.low {{
            background: #10b981;
        }}
        
        .priority-badge {{
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .priority-badge.high {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .priority-badge.medium {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .priority-badge.low {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .alert {{
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }}
        
        .alert-warning {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            color: #92400e;
        }}
        
        .remediation-steps .step {{
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            border-left: 4px solid {primary_color};
        }}
        
        .report-footer {{
            text-align: center;
            padding: 30px 0;
            border-top: 2px solid #ddd;
            margin-top: 40px;
            color: #666;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            
            .container {{
                max-width: 100%;
            }}
            
            section {{
                page-break-inside: avoid;
            }}
        }}
"""
    
    def _filter_sections(
        self,
        data: Dict[str, Any],
        config: ReportConfig
    ) -> Dict[str, Any]:
        """Filter report data based on included sections"""
        filtered = data.copy()
        
        # Remove sections not included in config
        if ReportSection.PAGE_ANALYSIS not in config.include_sections:
            filtered.pop('page_analyses', None)
        
        if ReportSection.PII_SUMMARY not in config.include_sections or not config.include_pii_details:
            filtered.pop('pii_summary', None)
        
        if ReportSection.VALIDATION_METRICS not in config.include_sections:
            filtered.pop('validation_metrics', None)
        
        if ReportSection.REMEDIATION_PLAN not in config.include_sections:
            filtered.pop('remediation_summary', None)
        
        return filtered
    
    def generate_executive_summary(
        self,
        report_data: ComplianceReport
    ) -> Dict[str, Any]:
        """
        Generate a concise executive summary.
        
        Args:
            report_data: The compliance analysis data
            
        Returns:
            Dict containing executive summary
        """
        return {
            'document_name': report_data.document_name,
            'analysis_date': report_data.analysis_date.isoformat(),
            'compliance_score': report_data.compliance_score,
            'compliance_level': report_data.compliance_level,
            'wcag_level': report_data.wcag_level,
            'total_issues': report_data.total_issues,
            'critical_issues': report_data.critical_issues,
            'auto_fixable': report_data.auto_fixable,
            'manual_fixes_required': report_data.manual_fixes_required,
            'top_recommendations': report_data.recommendations[:3] if report_data.recommendations else []
        }

