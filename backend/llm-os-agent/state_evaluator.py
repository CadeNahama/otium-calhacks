#!/usr/bin/env python3
"""
State Evaluation Service for Otium AI Agent
Captures, compares, and evaluates system state changes for adaptive step execution
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ssh_system_detector import SSHSystemDetector

# Configure logging
logger = logging.getLogger(__name__)

class StateChangeType(Enum):
    """Types of system state changes"""
    PACKAGE_CHANGE = "package_change"
    SERVICE_CHANGE = "service_change"
    FILE_CHANGE = "file_change"
    NETWORK_CHANGE = "network_change"
    RESOURCE_CHANGE = "resource_change"
    CONFIG_CHANGE = "config_change"
    UNKNOWN = "unknown"

class EvaluationResult(Enum):
    """Step evaluation results"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    UNEXPECTED = "unexpected"

@dataclass
class StateChange:
    """Represents a detected change in system state"""
    change_type: StateChangeType
    key: str
    before: Any
    after: Any
    significance: float  # 0.0 to 1.0
    description: str

@dataclass
class StepEvaluation:
    """Evaluation of a command step's success"""
    step_id: str
    evaluation_result: EvaluationResult
    success_indicators: List[str]
    failure_indicators: List[str]
    state_changes: List[StateChange]
    confidence_score: float
    recommendations: List[str]
    evaluated_at: datetime

class StateEvaluator:
    """Evaluates system state changes and step success"""
    
    def __init__(self, ssh_manager, connection_id: str):
        self.ssh_manager = ssh_manager
        self.connection_id = connection_id
        self.system_detector = SSHSystemDetector(ssh_manager, connection_id)
        
        # State comparison thresholds
        self.significance_thresholds = {
            'memory_available': 0.1,  # 10% change
            'disk_available': 0.05,   # 5% change
            'cpu_cores': 0.0,         # Any change
            'running_services': 0.0,  # Any change
            'installed_packages': 0.0, # Any change
        }
    
    def capture_system_state(self) -> Dict[str, Any]:
        """Capture current system state"""
        try:
            logger.info(f"Capturing system state for connection {self.connection_id}")
            state = self.system_detector.detect_system()
            
            # Add timestamp and metadata
            state.update({
                'captured_at': datetime.now().isoformat(),
                'connection_id': self.connection_id,
                'state_version': '1.0'
            })
            
            logger.info(f"System state captured: {len(state)} items")
            return state
            
        except Exception as e:
            logger.error(f"Failed to capture system state: {e}")
            return self._create_empty_state()
    
    def compare_states(self, before: Dict[str, Any], after: Dict[str, Any]) -> List[StateChange]:
        """Compare two system states and detect changes"""
        changes = []
        
        try:
            # Compare key system metrics
            for key in self.significance_thresholds.keys():
                if key in before and key in after:
                    change = self._detect_change(key, before[key], after[key])
                    if change:
                        changes.append(change)
            
            # Compare services status
            service_changes = self._compare_services(before, after)
            changes.extend(service_changes)
            
            # Compare installed packages
            package_changes = self._compare_packages(before, after)
            changes.extend(package_changes)
            
            logger.info(f"Detected {len(changes)} state changes")
            return changes
            
        except Exception as e:
            logger.error(f"Failed to compare states: {e}")
            return []
    
    def evaluate_step_success(self, step_result: Dict[str, Any], 
                            expected_outcome: str, 
                            state_changes: List[StateChange]) -> StepEvaluation:
        """Evaluate if a step achieved its expected outcome"""
        
        try:
            # Basic success indicators
            success_indicators = self._extract_success_indicators(step_result, expected_outcome)
            failure_indicators = self._extract_failure_indicators(step_result)
            
            # Determine evaluation result
            evaluation_result = self._determine_evaluation_result(
                success_indicators, failure_indicators, state_changes
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                success_indicators, failure_indicators, state_changes
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                evaluation_result, success_indicators, failure_indicators, state_changes
            )
            
            return StepEvaluation(
                step_id=step_result.get('step_id', 'unknown'),
                evaluation_result=evaluation_result,
                success_indicators=success_indicators,
                failure_indicators=failure_indicators,
                state_changes=state_changes,
                confidence_score=confidence_score,
                recommendations=recommendations,
                evaluated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to evaluate step success: {e}")
            return self._create_failed_evaluation(step_result)
    
    def _detect_change(self, key: str, before: Any, after: Any) -> Optional[StateChange]:
        """Detect if a specific system metric changed significantly"""
        try:
            if before == after:
                return None
            
            # Calculate significance based on type
            significance = self._calculate_significance(key, before, after)
            threshold = self.significance_thresholds.get(key, 0.0)
            
            if significance < threshold:
                return None
            
            return StateChange(
                change_type=self._get_change_type(key),
                key=key,
                before=before,
                after=after,
                significance=significance,
                description=f"{key} changed from {before} to {after}"
            )
            
        except Exception as e:
            logger.warning(f"Failed to detect change for {key}: {e}")
            return None
    
    def _calculate_significance(self, key: str, before: Any, after: Any) -> float:
        """Calculate significance of a change (0.0 to 1.0)"""
        try:
            if isinstance(before, (int, float)) and isinstance(after, (int, float)):
                if before == 0:
                    return 1.0 if after != 0 else 0.0
                return abs(after - before) / abs(before)
            
            elif isinstance(before, str) and isinstance(after, str):
                return 1.0 if before != after else 0.0
            
            elif isinstance(before, list) and isinstance(after, list):
                before_set = set(before)
                after_set = set(after)
                if not before_set and not after_set:
                    return 0.0
                if not before_set or not after_set:
                    return 1.0
                return len(before_set.symmetric_difference(after_set)) / len(before_set.union(after_set))
            
            return 1.0 if before != after else 0.0
            
        except Exception:
            return 0.0
    
    def _get_change_type(self, key: str) -> StateChangeType:
        """Map system metric keys to change types"""
        type_mapping = {
            'memory_available': StateChangeType.RESOURCE_CHANGE,
            'disk_available': StateChangeType.RESOURCE_CHANGE,
            'cpu_cores': StateChangeType.RESOURCE_CHANGE,
            'running_services': StateChangeType.SERVICE_CHANGE,
            'installed_packages': StateChangeType.PACKAGE_CHANGE,
            'network_connections': StateChangeType.NETWORK_CHANGE,
        }
        return type_mapping.get(key, StateChangeType.UNKNOWN)
    
    def _compare_services(self, before: Dict, after: Dict) -> List[StateChange]:
        """Compare running services between states"""
        changes = []
        
        try:
            before_services = set(before.get('running_services', []))
            after_services = set(after.get('running_services', []))
            
            # Services that started
            started = after_services - before_services
            for service in started:
                changes.append(StateChange(
                    change_type=StateChangeType.SERVICE_CHANGE,
                    key=f"service_started_{service}",
                    before="stopped",
                    after="running",
                    significance=1.0,
                    description=f"Service {service} started"
                ))
            
            # Services that stopped
            stopped = before_services - after_services
            for service in stopped:
                changes.append(StateChange(
                    change_type=StateChangeType.SERVICE_CHANGE,
                    key=f"service_stopped_{service}",
                    before="running",
                    after="stopped",
                    significance=1.0,
                    description=f"Service {service} stopped"
                ))
            
        except Exception as e:
            logger.warning(f"Failed to compare services: {e}")
        
        return changes
    
    def _compare_packages(self, before: Dict, after: Dict) -> List[StateChange]:
        """Compare installed packages between states"""
        changes = []
        
        try:
            before_packages = set(before.get('installed_packages', []))
            after_packages = set(after.get('installed_packages', []))
            
            # Newly installed packages
            installed = after_packages - before_packages
            for package in installed:
                changes.append(StateChange(
                    change_type=StateChangeType.PACKAGE_CHANGE,
                    key=f"package_installed_{package}",
                    before="not_installed",
                    after="installed",
                    significance=1.0,
                    description=f"Package {package} installed"
                ))
            
            # Removed packages
            removed = before_packages - after_packages
            for package in removed:
                changes.append(StateChange(
                    change_type=StateChangeType.PACKAGE_CHANGE,
                    key=f"package_removed_{package}",
                    before="installed",
                    after="not_installed",
                    significance=1.0,
                    description=f"Package {package} removed"
                ))
            
        except Exception as e:
            logger.warning(f"Failed to compare packages: {e}")
        
        return changes
    
    def _extract_success_indicators(self, step_result: Dict, expected_outcome: str) -> List[str]:
        """Extract indicators that suggest step success"""
        indicators = []
        
        # Basic success indicators
        if step_result.get('success', False):
            indicators.append("Command executed successfully")
        
        if step_result.get('exit_code') == 0:
            indicators.append("Command returned exit code 0")
        
        # Check for expected output
        stdout = step_result.get('stdout', '').lower()
        if expected_outcome.lower() in stdout:
            indicators.append(f"Expected output found: {expected_outcome}")
        
        # Check for success keywords
        success_keywords = ['success', 'completed', 'installed', 'started', 'enabled', 'ok']
        for keyword in success_keywords:
            if keyword in stdout:
                indicators.append(f"Success keyword found: {keyword}")
        
        return indicators
    
    def _extract_failure_indicators(self, step_result: Dict) -> List[str]:
        """Extract indicators that suggest step failure"""
        indicators = []
        
        # Basic failure indicators
        if not step_result.get('success', True):
            indicators.append("Command execution failed")
        
        if step_result.get('exit_code', 0) != 0:
            indicators.append(f"Command returned non-zero exit code: {step_result.get('exit_code')}")
        
        # Check for error keywords
        stderr = step_result.get('stderr', '').lower()
        error_keywords = ['error', 'failed', 'permission denied', 'not found', 'command not found']
        for keyword in error_keywords:
            if keyword in stderr:
                indicators.append(f"Error keyword found: {keyword}")
        
        return indicators
    
    def _determine_evaluation_result(self, success_indicators: List[str], 
                                  failure_indicators: List[str], 
                                  state_changes: List[StateChange]) -> EvaluationResult:
        """Determine overall evaluation result"""
        
        # Strong success: no failures and has success indicators
        if not failure_indicators and success_indicators:
            return EvaluationResult.SUCCESS
        
        # Strong failure: has failures and no success indicators
        if failure_indicators and not success_indicators:
            return EvaluationResult.FAILURE
        
        # Partial: mixed indicators
        if success_indicators and failure_indicators:
            return EvaluationResult.PARTIAL
        
        # Unexpected: no clear indicators but state changed
        if state_changes and not success_indicators and not failure_indicators:
            return EvaluationResult.UNEXPECTED
        
        # Default to failure if no clear success
        return EvaluationResult.FAILURE
    
    def _calculate_confidence_score(self, success_indicators: List[str], 
                                 failure_indicators: List[str], 
                                 state_changes: List[StateChange]) -> float:
        """Calculate confidence score (0.0 to 1.0)"""
        
        # Base score from indicators
        success_score = len(success_indicators) * 0.2
        failure_score = len(failure_indicators) * 0.2
        
        # State change bonus
        state_score = min(len(state_changes) * 0.1, 0.3)
        
        # Calculate final score
        total_score = success_score - failure_score + state_score
        
        # Normalize to 0.0-1.0 range
        return max(0.0, min(1.0, total_score))
    
    def _generate_recommendations(self, evaluation_result: EvaluationResult,
                                success_indicators: List[str],
                                failure_indicators: List[str],
                                state_changes: List[StateChange]) -> List[str]:
        """Generate recommendations based on evaluation"""
        recommendations = []
        
        if evaluation_result == EvaluationResult.SUCCESS:
            recommendations.append("Step completed successfully")
            if state_changes:
                recommendations.append("System state changed as expected")
        
        elif evaluation_result == EvaluationResult.FAILURE:
            recommendations.append("Step failed - review error messages")
            if failure_indicators:
                recommendations.append("Check for permission issues or missing dependencies")
        
        elif evaluation_result == EvaluationResult.PARTIAL:
            recommendations.append("Step partially succeeded - review output carefully")
            recommendations.append("Consider running additional verification commands")
        
        elif evaluation_result == EvaluationResult.UNEXPECTED:
            recommendations.append("Unexpected result - system state changed but success unclear")
            recommendations.append("Verify step outcome manually")
        
        return recommendations
    
    def _create_empty_state(self) -> Dict[str, Any]:
        """Create empty state for error cases"""
        return {
            'captured_at': datetime.now().isoformat(),
            'connection_id': self.connection_id,
            'state_version': '1.0',
            'os_name': 'Unknown',
            'os_family': 'unknown',
            'package_manager': 'unknown',
            'service_manager': 'unknown',
            'available_tools': [],
            'memory_available': 'Unknown',
            'disk_available': 'Unknown',
            'cpu_cores': 'Unknown',
            'running_services': [],
            'installed_packages': []
        }
    
    def _create_failed_evaluation(self, step_result: Dict) -> StepEvaluation:
        """Create evaluation for failed analysis"""
        return StepEvaluation(
            step_id=step_result.get('step_id', 'unknown'),
            evaluation_result=EvaluationResult.FAILURE,
            success_indicators=[],
            failure_indicators=["State evaluation failed"],
            state_changes=[],
            confidence_score=0.0,
            recommendations=["Manual verification required"],
            evaluated_at=datetime.now()
        )
