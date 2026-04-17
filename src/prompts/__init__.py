"""
Prompt Library Module

This module provides a centralized, version-controlled prompt management system
for the PDF Accessibility Compliance Engine. It includes:

- Versioned prompt templates
- A/B testing capabilities
- Performance tracking
- Prompt optimization tools
"""

from .prompt_manager import PromptManager, PromptVersion
from .templates import PromptTemplates

__all__ = ['PromptManager', 'PromptVersion', 'PromptTemplates']

# Made with Bob
