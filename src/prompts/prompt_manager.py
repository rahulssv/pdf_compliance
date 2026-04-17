"""
Prompt Manager - Version Control and Performance Tracking

This module provides comprehensive prompt management including:
- Version control for prompt templates
- A/B testing capabilities
- Performance tracking and analytics
- Prompt optimization recommendations
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from enum import Enum

from .templates import PromptTemplates, PromptTemplate

logger = logging.getLogger(__name__)


class PromptStatus(Enum):
    """Status of a prompt version"""
    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class PromptPerformance:
    """Performance metrics for a prompt version"""
    prompt_name: str
    version: str
    total_uses: int = 0
    successful_uses: int = 0
    failed_uses: int = 0
    avg_response_time: float = 0.0
    avg_confidence_score: float = 0.0
    avg_validation_score: float = 0.0
    user_satisfaction: float = 0.0
    last_used: Optional[datetime] = None
    performance_trend: str = "stable"  # improving, stable, declining
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_uses == 0:
            return 0.0
        return (self.successful_uses / self.total_uses) * 100
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage"""
        if self.total_uses == 0:
            return 0.0
        return (self.failed_uses / self.total_uses) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        if self.last_used:
            data['last_used'] = self.last_used.isoformat()
        return data


@dataclass
class PromptVersion:
    """Represents a versioned prompt with metadata"""
    template: PromptTemplate
    status: PromptStatus
    created_by: str
    created_at: datetime
    modified_at: datetime
    change_log: List[str] = field(default_factory=list)
    performance: Optional[PromptPerformance] = None
    ab_test_group: Optional[str] = None  # A, B, C, etc.
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'template': {
                'name': self.template.name,
                'version': self.template.version,
                'description': self.template.description,
                'template': self.template.template,
                'parameters': self.template.parameters,
                'expected_output_format': self.template.expected_output_format,
                'performance_notes': self.template.performance_notes,
                'created_at': self.template.created_at.isoformat()
            },
            'status': self.status.value,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'change_log': self.change_log,
            'performance': self.performance.to_dict() if self.performance else None,
            'ab_test_group': self.ab_test_group,
            'tags': self.tags
        }


class PromptManager:
    """
    Manages prompt templates with version control and performance tracking.
    
    Features:
    - Version control for all prompts
    - A/B testing support
    - Performance analytics
    - Automatic optimization recommendations
    - Prompt history and rollback
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the prompt manager.
        
        Args:
            storage_path: Path to store prompt versions and metrics (optional)
        """
        self.storage_path = Path(storage_path) if storage_path else Path("data/prompts")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.versions: Dict[str, List[PromptVersion]] = {}
        self.active_versions: Dict[str, PromptVersion] = {}
        self.ab_tests: Dict[str, Dict[str, PromptVersion]] = {}
        
        self._load_versions()
        self._initialize_default_prompts()
        
        logger.info(f"PromptManager initialized with {len(self.active_versions)} active prompts")
    
    def _initialize_default_prompts(self) -> None:
        """Initialize default prompt templates if not already loaded"""
        templates = PromptTemplates.get_all_templates()
        
        for name, template in templates.items():
            if name not in self.active_versions:
                version = PromptVersion(
                    template=template,
                    status=PromptStatus.ACTIVE,
                    created_by="system",
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    change_log=["Initial version"],
                    performance=PromptPerformance(
                        prompt_name=name,
                        version=template.version
                    ),
                    tags=["default", "production"]
                )
                self.register_version(version)
                self.set_active_version(name, template.version)
    
    def _load_versions(self) -> None:
        """Load prompt versions from storage"""
        versions_file = self.storage_path / "versions.json"
        if versions_file.exists():
            try:
                with open(versions_file, 'r') as f:
                    data = json.load(f)
                    self.versions = {}
                    self.active_versions = {}

                    for prompt_name, serialized_versions in data.items():
                        loaded_versions: List[PromptVersion] = []
                        for raw in serialized_versions:
                            version = self._deserialize_version(raw)
                            loaded_versions.append(version)
                            if version.status == PromptStatus.ACTIVE:
                                self.active_versions[prompt_name] = version

                        if loaded_versions:
                            self.versions[prompt_name] = loaded_versions
                            if prompt_name not in self.active_versions:
                                # Fallback to latest version if none is marked active.
                                latest = max(loaded_versions, key=lambda v: v.modified_at)
                                latest.status = PromptStatus.ACTIVE
                                self.active_versions[prompt_name] = latest

                    logger.info(f"Loaded {sum(len(v) for v in self.versions.values())} prompt versions from storage")
            except Exception as e:
                logger.error(f"Error loading prompt versions: {e}")

    def _deserialize_performance(self, prompt_name: str, template_version: str, data: Dict[str, Any]) -> PromptPerformance:
        """Deserialize performance metrics from dict."""
        last_used = data.get('last_used')
        return PromptPerformance(
            prompt_name=data.get('prompt_name', prompt_name),
            version=data.get('version', template_version),
            total_uses=data.get('total_uses', 0),
            successful_uses=data.get('successful_uses', 0),
            failed_uses=data.get('failed_uses', 0),
            avg_response_time=data.get('avg_response_time', 0.0),
            avg_confidence_score=data.get('avg_confidence_score', 0.0),
            avg_validation_score=data.get('avg_validation_score', 0.0),
            user_satisfaction=data.get('user_satisfaction', 0.0),
            last_used=datetime.fromisoformat(last_used) if last_used else None,
            performance_trend=data.get('performance_trend', 'stable'),
        )

    def _deserialize_version(self, data: Dict[str, Any]) -> PromptVersion:
        """Deserialize prompt version payload."""
        template_data = data['template']
        template = PromptTemplate(
            name=template_data['name'],
            version=template_data['version'],
            template=template_data['template'],
            description=template_data.get('description', ''),
            created_at=datetime.fromisoformat(template_data['created_at']),
            parameters=template_data.get('parameters', {}),
            expected_output_format=template_data.get('expected_output_format', ''),
            performance_notes=template_data.get('performance_notes', ''),
        )

        performance_data = data.get('performance')
        performance = None
        if performance_data:
            performance = self._deserialize_performance(
                prompt_name=template.name,
                template_version=template.version,
                data=performance_data,
            )

        status_raw = data.get('status', PromptStatus.DRAFT.value)
        status = PromptStatus(status_raw) if status_raw in {s.value for s in PromptStatus} else PromptStatus.DRAFT

        return PromptVersion(
            template=template,
            status=status,
            created_by=data.get('created_by', 'unknown'),
            created_at=datetime.fromisoformat(data['created_at']),
            modified_at=datetime.fromisoformat(data['modified_at']),
            change_log=data.get('change_log', []),
            performance=performance,
            ab_test_group=data.get('ab_test_group'),
            tags=data.get('tags', []),
        )
    
    def _save_versions(self) -> None:
        """Save prompt versions to storage"""
        versions_file = self.storage_path / "versions.json"
        try:
            data = {}
            for name, versions in self.versions.items():
                data[name] = [v.to_dict() for v in versions]
            
            with open(versions_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(self.versions)} prompt versions to storage")
        except Exception as e:
            logger.error(f"Error saving prompt versions: {e}")
    
    def register_version(self, version: PromptVersion) -> None:
        """
        Register a new prompt version.
        
        Args:
            version: The prompt version to register
        """
        name = version.template.name
        
        if name not in self.versions:
            self.versions[name] = []
        
        self.versions[name].append(version)
        self._save_versions()
        
        logger.info(f"Registered new version {version.template.version} for prompt '{name}'")
    
    def set_active_version(self, prompt_name: str, version: str) -> None:
        """
        Set the active version for a prompt.
        
        Args:
            prompt_name: Name of the prompt
            version: Version to activate
            
        Raises:
            ValueError: If prompt or version not found
        """
        if prompt_name not in self.versions:
            raise ValueError(f"Prompt '{prompt_name}' not found")
        
        version_obj = None
        for v in self.versions[prompt_name]:
            if v.template.version == version:
                version_obj = v
                break
        
        if not version_obj:
            raise ValueError(f"Version '{version}' not found for prompt '{prompt_name}'")
        
        # Deactivate current active version
        if prompt_name in self.active_versions:
            old_version = self.active_versions[prompt_name]
            old_version.status = PromptStatus.DEPRECATED
        
        # Activate new version
        version_obj.status = PromptStatus.ACTIVE
        self.active_versions[prompt_name] = version_obj
        self._save_versions()
        
        logger.info(f"Activated version {version} for prompt '{prompt_name}'")
    
    def get_active_prompt(self, prompt_name: str) -> PromptTemplate:
        """
        Get the active prompt template.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            PromptTemplate: The active prompt template
            
        Raises:
            ValueError: If prompt not found
        """
        if prompt_name not in self.active_versions:
            raise ValueError(f"No active version for prompt '{prompt_name}'")
        
        return self.active_versions[prompt_name].template
    
    def format_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Format an active prompt with parameters.
        
        Args:
            prompt_name: Name of the prompt
            **kwargs: Parameters to substitute
            
        Returns:
            str: Formatted prompt
        """
        template = self.get_active_prompt(prompt_name)
        return PromptTemplates.format_template(template, **kwargs)
    
    def record_usage(
        self,
        prompt_name: str,
        success: bool,
        response_time: float,
        confidence_score: Optional[float] = None,
        validation_score: Optional[float] = None
    ) -> None:
        """
        Record usage metrics for a prompt.
        
        Args:
            prompt_name: Name of the prompt
            success: Whether the prompt use was successful
            response_time: Response time in seconds
            confidence_score: AI confidence score (0-100)
            validation_score: Validation score (0-100)
        """
        if prompt_name not in self.active_versions:
            logger.warning(f"Cannot record usage for unknown prompt '{prompt_name}'")
            return
        
        version = self.active_versions[prompt_name]
        if not version.performance:
            version.performance = PromptPerformance(
                prompt_name=prompt_name,
                version=version.template.version
            )
        
        perf = version.performance
        perf.total_uses += 1
        
        if success:
            perf.successful_uses += 1
        else:
            perf.failed_uses += 1
        
        # Update running averages
        perf.avg_response_time = (
            (perf.avg_response_time * (perf.total_uses - 1) + response_time) / perf.total_uses
        )
        
        if confidence_score is not None:
            perf.avg_confidence_score = (
                (perf.avg_confidence_score * (perf.total_uses - 1) + confidence_score) / perf.total_uses
            )
        
        if validation_score is not None:
            perf.avg_validation_score = (
                (perf.avg_validation_score * (perf.total_uses - 1) + validation_score) / perf.total_uses
            )
        
        perf.last_used = datetime.now()
        
        # Analyze performance trend
        if perf.total_uses >= 10:
            if perf.success_rate >= 95 and perf.avg_confidence_score >= 85:
                perf.performance_trend = "improving"
            elif perf.success_rate < 80 or perf.avg_confidence_score < 70:
                perf.performance_trend = "declining"
            else:
                perf.performance_trend = "stable"
        
        self._save_versions()
        
        logger.debug(
            f"Recorded usage for '{prompt_name}': "
            f"success={success}, response_time={response_time:.2f}s"
        )
    
    def get_performance_report(self, prompt_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance report for prompts.
        
        Args:
            prompt_name: Specific prompt name, or None for all prompts
            
        Returns:
            Dict containing performance metrics
        """
        if prompt_name:
            if prompt_name not in self.active_versions:
                raise ValueError(f"Prompt '{prompt_name}' not found")
            
            version = self.active_versions[prompt_name]
            if not version.performance:
                return {"prompt_name": prompt_name, "status": "no_data"}
            
            return {
                "prompt_name": prompt_name,
                "version": version.template.version,
                "status": version.status.value,
                "metrics": version.performance.to_dict(),
                "recommendations": self._get_optimization_recommendations(version)
            }
        else:
            # Report for all prompts
            report = {
                "total_prompts": len(self.active_versions),
                "report_generated": datetime.now().isoformat(),
                "prompts": {}
            }
            
            for name, version in self.active_versions.items():
                if version.performance:
                    report["prompts"][name] = {
                        "version": version.template.version,
                        "metrics": version.performance.to_dict(),
                        "status": version.status.value
                    }
            
            return report
    
    def _get_optimization_recommendations(self, version: PromptVersion) -> List[str]:
        """
        Generate optimization recommendations based on performance.
        
        Args:
            version: The prompt version to analyze
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if not version.performance:
            return ["Insufficient data for recommendations"]
        
        perf = version.performance
        
        # Success rate recommendations
        if perf.success_rate < 80:
            recommendations.append(
                f"Low success rate ({perf.success_rate:.1f}%). "
                "Consider revising prompt clarity and specificity."
            )
        
        # Confidence score recommendations
        if perf.avg_confidence_score < 70:
            recommendations.append(
                f"Low confidence scores ({perf.avg_confidence_score:.1f}). "
                "Add more context or examples to the prompt."
            )
        
        # Response time recommendations
        if perf.avg_response_time > 5.0:
            recommendations.append(
                f"High response time ({perf.avg_response_time:.1f}s). "
                "Consider simplifying the prompt or reducing output requirements."
            )
        
        # Validation score recommendations
        if perf.avg_validation_score < 75:
            recommendations.append(
                f"Low validation scores ({perf.avg_validation_score:.1f}). "
                "Improve output format specifications and validation criteria."
            )
        
        # Performance trend recommendations
        if perf.performance_trend == "declining":
            recommendations.append(
                "Performance is declining. Review recent changes and consider A/B testing."
            )
        
        if not recommendations:
            recommendations.append("Performance is good. Continue monitoring.")
        
        return recommendations
    
    def create_ab_test(
        self,
        prompt_name: str,
        variant_a_version: str,
        variant_b_version: str,
        test_name: Optional[str] = None
    ) -> str:
        """
        Create an A/B test between two prompt versions.
        
        Args:
            prompt_name: Name of the prompt
            variant_a_version: Version for variant A
            variant_b_version: Version for variant B
            test_name: Optional name for the test
            
        Returns:
            str: Test ID
            
        Raises:
            ValueError: If prompt or versions not found
        """
        if prompt_name not in self.versions:
            raise ValueError(f"Prompt '{prompt_name}' not found")
        
        # Find versions
        variant_a = None
        variant_b = None
        
        for v in self.versions[prompt_name]:
            if v.template.version == variant_a_version:
                variant_a = v
            if v.template.version == variant_b_version:
                variant_b = v
        
        if not variant_a or not variant_b:
            raise ValueError("One or both versions not found")
        
        # Create test
        test_id = test_name or f"{prompt_name}_ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        variant_a.ab_test_group = "A"
        variant_a.status = PromptStatus.TESTING
        
        variant_b.ab_test_group = "B"
        variant_b.status = PromptStatus.TESTING
        
        self.ab_tests[test_id] = {
            "A": variant_a,
            "B": variant_b
        }
        
        self._save_versions()
        
        logger.info(f"Created A/B test '{test_id}' for prompt '{prompt_name}'")
        return test_id
    
    def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """
        Get results of an A/B test.
        
        Args:
            test_id: ID of the test
            
        Returns:
            Dict containing test results
            
        Raises:
            ValueError: If test not found
        """
        if test_id not in self.ab_tests:
            raise ValueError(f"A/B test '{test_id}' not found")
        
        variants = self.ab_tests[test_id]
        
        results = {
            "test_id": test_id,
            "variants": {}
        }
        
        for group, version in variants.items():
            if version.performance:
                results["variants"][group] = {
                    "version": version.template.version,
                    "metrics": version.performance.to_dict()
                }
        
        # Determine winner
        if all(v.performance for v in variants.values()):
            perf_a = variants["A"].performance
            perf_b = variants["B"].performance
            
            # Type guard - we know performance is not None due to the check above
            if perf_a is None or perf_b is None:
                results["winner"] = "insufficient_data"
                results["recommendation"] = "Continue testing to gather more data"
                return results
            
            # Compare based on success rate and confidence
            score_a = (perf_a.success_rate + perf_a.avg_confidence_score) / 2
            score_b = (perf_b.success_rate + perf_b.avg_confidence_score) / 2
            
            if abs(score_a - score_b) < 5:
                results["winner"] = "inconclusive"
                results["recommendation"] = "Continue testing - results too close"
            elif score_a > score_b:
                results["winner"] = "A"
                results["recommendation"] = f"Activate variant A (score: {score_a:.1f} vs {score_b:.1f})"
            else:
                results["winner"] = "B"
                results["recommendation"] = f"Activate variant B (score: {score_b:.1f} vs {score_a:.1f})"
        else:
            results["winner"] = "insufficient_data"
            results["recommendation"] = "Continue testing to gather more data"
        
        return results
    
    def list_versions(self, prompt_name: str) -> List[Dict[str, Any]]:
        """
        List all versions of a prompt.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            List of version information
        """
        if prompt_name not in self.versions:
            return []
        
        return [
            {
                "version": v.template.version,
                "status": v.status.value,
                "created_at": v.created_at.isoformat(),
                "modified_at": v.modified_at.isoformat(),
                "performance": v.performance.to_dict() if v.performance else None
            }
            for v in self.versions[prompt_name]
        ]
    
    def export_prompt_library(self, output_path: str) -> None:
        """
        Export the entire prompt library to a file.
        
        Args:
            output_path: Path to export the library
        """
        export_data = {
            "export_date": datetime.now().isoformat(),
            "version": PromptTemplates.CURRENT_VERSION,
            "prompts": {}
        }
        
        for name, versions in self.versions.items():
            export_data["prompts"][name] = [v.to_dict() for v in versions]
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported prompt library to {output_path}")

# Made with Bob
