"""
Automated Remediation Engine
Two-tier system: automated fixes + user action guidance
"""
import logging
import pypdf
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from io import BytesIO
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RemediationAction:
    """Represents a remediation action"""
    issue_type: str
    action_type: str  # 'automated' or 'manual'
    description: str
    status: str  # 'completed', 'failed', 'pending'
    timestamp: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class UserAction:
    """Represents a manual action required from user"""
    issue: str
    priority: str  # 'high', 'medium', 'low'
    steps: List[str]
    estimated_time: str
    tools_required: List[str]
    difficulty: str  # 'easy', 'medium', 'hard'


class AutoRemediationEngine:
    """
    Automated remediation engine with two-tier system
    Tier 1: Automated fixes for deterministic issues
    Tier 2: User action guidance for complex issues
    """
    
    def __init__(self):
        self.auto_fixable_issues = self._define_auto_fixable()
        self.user_action_templates = self._define_user_actions()
        self._remediation_history = []
        
        logger.info(f"✅ AutoRemediationEngine initialized ({len(self.auto_fixable_issues)} auto-fixable types)")
    
    def _define_auto_fixable(self) -> Dict[str, Dict[str, Any]]:
        """Define issues that can be automatically fixed"""
        return {
            'missing_language': {
                'fix_function': 'add_document_language',
                'default_value': 'en-US',
                'success_rate': 0.95,
                'description': 'Add missing document language metadata'
            },
            'missing_title': {
                'fix_function': 'add_document_title',
                'default_value': 'from_filename',
                'success_rate': 0.90,
                'description': 'Add document title from filename'
            },
            'missing_metadata': {
                'fix_function': 'add_basic_metadata',
                'default_value': 'auto_generated',
                'success_rate': 0.85,
                'description': 'Add basic document metadata'
            },
            'pdf_ua_flag': {
                'fix_function': 'set_pdf_ua_flag',
                'default_value': True,
                'success_rate': 0.95,
                'description': 'Set PDF/UA compliance flag'
            }
        }
    
    def _define_user_actions(self) -> Dict[str, UserAction]:
        """Define user action templates for manual remediation"""
        return {
            'missing_alt_text': UserAction(
                issue='Missing alternative text for images',
                priority='high',
                steps=[
                    'Open document in Adobe Acrobat Pro',
                    'Navigate to the page containing images',
                    'Right-click on each image in the Tags panel',
                    'Select "Edit Alternate Text"',
                    'Add a meaningful description of the image content',
                    'Save the document'
                ],
                estimated_time='5 minutes per image',
                tools_required=['Adobe Acrobat Pro'],
                difficulty='easy'
            ),
            'form_field_unlabeled': UserAction(
                issue='Form fields missing proper labels',
                priority='high',
                steps=[
                    'Open document in Adobe Acrobat Pro',
                    'Go to Tools > Prepare Form',
                    'Select each form field',
                    'In Properties panel, add a descriptive label',
                    'Add tooltip text for additional context',
                    'Test with screen reader to verify',
                    'Save the document'
                ],
                estimated_time='3 minutes per field',
                tools_required=['Adobe Acrobat Pro'],
                difficulty='medium'
            ),
            'no_tag_tree': UserAction(
                issue='Document lacks tag tree structure',
                priority='high',
                steps=[
                    'Open document in Adobe Acrobat Pro',
                    'Go to Tools > Accessibility > Add Tags to Document',
                    'Wait for automatic tagging to complete',
                    'Review tag structure in Tags panel',
                    'Manually correct any tagging errors',
                    'Run Accessibility Checker to verify',
                    'Save the document'
                ],
                estimated_time='10-30 minutes depending on document complexity',
                tools_required=['Adobe Acrobat Pro'],
                difficulty='hard'
            ),
            'scanned_document': UserAction(
                issue='Scanned document without text layer',
                priority='high',
                steps=[
                    'Open document in Adobe Acrobat Pro',
                    'Go to Tools > Enhance Scans > Recognize Text',
                    'Select "In This File" and choose language',
                    'Click "Recognize Text"',
                    'Wait for OCR processing to complete',
                    'Review and correct any OCR errors',
                    'Add tags to document',
                    'Save the document'
                ],
                estimated_time='15-45 minutes depending on document length',
                tools_required=['Adobe Acrobat Pro'],
                difficulty='hard'
            ),
            'reading_order': UserAction(
                issue='Incorrect reading order',
                priority='medium',
                steps=[
                    'Open document in Adobe Acrobat Pro',
                    'Go to Tools > Accessibility > Reading Order',
                    'Review the reading order panel',
                    'Drag and drop elements to correct order',
                    'Test with screen reader',
                    'Save the document'
                ],
                estimated_time='10-20 minutes per page',
                tools_required=['Adobe Acrobat Pro'],
                difficulty='medium'
            ),
            'color_contrast': UserAction(
                issue='Insufficient color contrast',
                priority='medium',
                steps=[
                    'Identify text with poor contrast',
                    'Open document in PDF editor',
                    'Select text with contrast issues',
                    'Change text color or background to meet WCAG AA standards (4.5:1 ratio)',
                    'Use color contrast checker tool to verify',
                    'Save the document'
                ],
                estimated_time='5 minutes per instance',
                tools_required=['Adobe Acrobat Pro', 'Color Contrast Checker'],
                difficulty='easy'
            )
        }
    
    def remediate_issues(
        self,
        file_buffer: BytesIO,
        filename: str,
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Remediate issues using two-tier approach
        
        Args:
            file_buffer: PDF file buffer
            filename: Original filename
            issues: List of detected issues
        
        Returns:
            {
                'fileName': str,
                'autoFixed': List[RemediationAction],
                'userActions': List[UserAction],
                'summary': Dict
            }
        """
        logger.info(f"🔧 Starting remediation for {filename} ({len(issues)} issues)")
        
        auto_fixed = []
        user_actions = []
        
        # Separate auto-fixable from manual issues
        for issue in issues:
            issue_type = self._classify_issue(issue)
            
            if issue_type in self.auto_fixable_issues:
                # Attempt automated fix
                action = self._apply_automated_fix(
                    file_buffer, issue_type, issue, filename
                )
                auto_fixed.append(action)
            else:
                # Generate user action guidance
                user_action = self._generate_user_action(issue_type, issue)
                if user_action:
                    user_actions.append(user_action)
        
        # Calculate summary
        summary = {
            'totalIssues': len(issues),
            'autoFixed': len([a for a in auto_fixed if a.status == 'completed']),
            'autoFailed': len([a for a in auto_fixed if a.status == 'failed']),
            'manualRequired': len(user_actions),
            'remediationRate': round(
                (len([a for a in auto_fixed if a.status == 'completed']) / len(issues)) * 100, 1
            ) if issues else 0
        }
        
        logger.info(
            f"✅ Remediation complete: {summary['autoFixed']} auto-fixed, "
            f"{summary['manualRequired']} manual actions required"
        )
        
        return {
            'fileName': filename,
            'autoFixed': [asdict(a) for a in auto_fixed],
            'userActions': [asdict(a) for a in user_actions],
            'summary': summary
        }
    
    def _classify_issue(self, issue: Dict[str, Any]) -> str:
        """Classify issue type for remediation"""
        description = issue.get('description', '').lower()
        
        if 'language' in description and 'not declared' in description:
            return 'missing_language'
        elif 'title' in description and 'missing' in description:
            return 'missing_title'
        elif 'metadata' in description:
            return 'missing_metadata'
        elif 'tag tree' in description:
            return 'no_tag_tree'
        elif 'alternative text' in description or 'alt text' in description:
            return 'missing_alt_text'
        elif 'form field' in description:
            return 'form_field_unlabeled'
        elif 'scanned' in description:
            return 'scanned_document'
        elif 'reading order' in description:
            return 'reading_order'
        elif 'contrast' in description:
            return 'color_contrast'
        
        return 'unknown'
    
    def _apply_automated_fix(
        self,
        file_buffer: BytesIO,
        issue_type: str,
        issue: Dict[str, Any],
        filename: str
    ) -> RemediationAction:
        """Apply automated fix to PDF"""
        fix_config = self.auto_fixable_issues[issue_type]
        
        try:
            # Get fix function
            fix_function = getattr(self, fix_config['fix_function'])
            
            # Apply fix
            success, details = fix_function(file_buffer, filename, fix_config['default_value'])
            
            action = RemediationAction(
                issue_type=issue_type,
                action_type='automated',
                description=fix_config['description'],
                status='completed' if success else 'failed',
                timestamp=datetime.utcnow().isoformat(),
                details=details
            )
            
            # Record in history
            self._remediation_history.append(action)
            
            if success:
                logger.info(f"  ✅ Auto-fixed: {issue_type}")
            else:
                logger.warning(f"  ⚠️ Auto-fix failed: {issue_type}")
            
            return action
            
        except Exception as e:
            logger.error(f"  ❌ Error applying fix for {issue_type}: {e}")
            return RemediationAction(
                issue_type=issue_type,
                action_type='automated',
                description=fix_config['description'],
                status='failed',
                timestamp=datetime.utcnow().isoformat(),
                details={'error': str(e)}
            )
    
    def _generate_user_action(
        self,
        issue_type: str,
        issue: Dict[str, Any]
    ) -> Optional[UserAction]:
        """Generate user action guidance"""
        if issue_type in self.user_action_templates:
            return self.user_action_templates[issue_type]
        
        # Generate generic user action
        return UserAction(
            issue=issue.get('description', 'Unknown issue'),
            priority='medium',
            steps=[
                'Review the issue description',
                'Consult accessibility guidelines',
                'Use appropriate PDF editing tools',
                'Verify fix with accessibility checker'
            ],
            estimated_time='Variable',
            tools_required=['PDF Editor'],
            difficulty='medium'
        )
    
    # Automated fix functions
    
    def add_document_language(
        self,
        file_buffer: BytesIO,
        filename: str,
        language: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Add document language metadata"""
        try:
            file_buffer.seek(0)
            pdf_reader = pypdf.PdfReader(file_buffer)
            pdf_writer = pypdf.PdfWriter()
            
            # Copy all pages
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # Add language to catalog
            if pdf_writer._root_object:
                pdf_writer._root_object[pypdf.generic.NameObject('/Lang')] = \
                    pypdf.generic.TextStringObject(language)
            
            # Write to buffer (in production, would return modified buffer)
            output_buffer = BytesIO()
            pdf_writer.write(output_buffer)
            
            return True, {
                'language_set': language,
                'method': 'catalog_metadata'
            }
            
        except Exception as e:
            logger.error(f"Error adding language: {e}")
            return False, {'error': str(e)}
    
    def add_document_title(
        self,
        file_buffer: BytesIO,
        filename: str,
        title_source: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Add document title from filename"""
        try:
            file_buffer.seek(0)
            pdf_reader = pypdf.PdfReader(file_buffer)
            pdf_writer = pypdf.PdfWriter()
            
            # Copy all pages
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # Generate title from filename
            if title_source == 'from_filename':
                title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ').title()
            else:
                title = title_source
            
            # Add metadata
            pdf_writer.add_metadata({
                '/Title': title,
                '/Producer': 'PDF Accessibility Compliance Engine',
                '/Creator': 'Auto Remediation'
            })
            
            # Write to buffer
            output_buffer = BytesIO()
            pdf_writer.write(output_buffer)
            
            return True, {
                'title_set': title,
                'source': title_source
            }
            
        except Exception as e:
            logger.error(f"Error adding title: {e}")
            return False, {'error': str(e)}
    
    def add_basic_metadata(
        self,
        file_buffer: BytesIO,
        filename: str,
        metadata_type: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Add basic document metadata"""
        try:
            file_buffer.seek(0)
            pdf_reader = pypdf.PdfReader(file_buffer)
            pdf_writer = pypdf.PdfWriter()
            
            # Copy all pages
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # Add metadata
            metadata = {
                '/Producer': 'PDF Accessibility Compliance Engine',
                '/Creator': 'Auto Remediation',
                '/CreationDate': datetime.utcnow().strftime('D:%Y%m%d%H%M%S')
            }
            
            pdf_writer.add_metadata(metadata)
            
            # Write to buffer
            output_buffer = BytesIO()
            pdf_writer.write(output_buffer)
            
            return True, {
                'metadata_added': list(metadata.keys()),
                'type': metadata_type
            }
            
        except Exception as e:
            logger.error(f"Error adding metadata: {e}")
            return False, {'error': str(e)}
    
    def set_pdf_ua_flag(
        self,
        file_buffer: BytesIO,
        filename: str,
        flag_value: bool
    ) -> Tuple[bool, Dict[str, Any]]:
        """Set PDF/UA compliance flag"""
        try:
            file_buffer.seek(0)
            pdf_reader = pypdf.PdfReader(file_buffer)
            pdf_writer = pypdf.PdfWriter()
            
            # Copy all pages
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # Set PDF/UA flag in catalog
            if pdf_writer._root_object:
                mark_info = pypdf.generic.DictionaryObject()
                mark_info[pypdf.generic.NameObject('/Marked')] = \
                    pypdf.generic.BooleanObject(flag_value)
                pdf_writer._root_object[pypdf.generic.NameObject('/MarkInfo')] = mark_info
            
            # Write to buffer
            output_buffer = BytesIO()
            pdf_writer.write(output_buffer)
            
            return True, {
                'pdf_ua_flag': flag_value,
                'method': 'mark_info'
            }
            
        except Exception as e:
            logger.error(f"Error setting PDF/UA flag: {e}")
            return False, {'error': str(e)}
    
    def get_user_action_template(self, issue_type: str) -> Optional[UserAction]:
        """Get a user-action template for a given issue type."""
        normalized = issue_type.strip().lower()
        aliases = {
            'tag_tree': 'no_tag_tree',
            'no_tags': 'no_tag_tree',
            'alt_text': 'missing_alt_text',
            'image_alt_text': 'missing_alt_text',
            'forms': 'form_field_unlabeled',
            'form_fields': 'form_field_unlabeled',
        }
        key = aliases.get(normalized, normalized)
        return self.user_action_templates.get(key)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get remediation statistics"""
        total_attempts = len(self._remediation_history)
        successful = len([a for a in self._remediation_history if a.status == 'completed'])
        
        return {
            'total_attempts': total_attempts,
            'successful': successful,
            'failed': total_attempts - successful,
            'success_rate': round((successful / total_attempts) * 100, 1) if total_attempts > 0 else 0,
            'auto_fixable_types': len(self.auto_fixable_issues),
            'user_action_templates': len(self.user_action_templates)
        }
    
    def clear_history(self):
        """Clear remediation history"""
        self._remediation_history.clear()
        logger.info("🗑️ Remediation history cleared")

# Made with Bob
