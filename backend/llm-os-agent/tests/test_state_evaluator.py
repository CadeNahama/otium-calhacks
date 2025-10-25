#!/usr/bin/env python3
"""
Unit tests for State Evaluator
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state_evaluator import StateEvaluator, StateChangeType, EvaluationResult, StateChange, StepEvaluation

@pytest.fixture
def mock_ssh_manager():
    """Create mock SSH manager"""
    manager = Mock()
    return manager

@pytest.fixture
def mock_system_detector():
    """Create mock system detector"""
    detector = Mock()
    detector.detect_system.return_value = {
        'os_name': 'Ubuntu',
        'os_family': 'debian',
        'package_manager': 'apt',
        'service_manager': 'systemctl',
        'memory_available': '8G',
        'disk_available': '50G',
        'cpu_cores': '4',
        'running_services': ['ssh', 'nginx'],
        'installed_packages': ['nginx', 'apache2']
    }
    return detector

@pytest.fixture
def state_evaluator(mock_ssh_manager, mock_system_detector):
    """Create StateEvaluator instance"""
    evaluator = StateEvaluator(mock_ssh_manager, "test-connection")
    evaluator.system_detector = mock_system_detector
    return evaluator

def test_capture_system_state(state_evaluator):
    """Test system state capture"""
    state = state_evaluator.capture_system_state()
    
    assert 'captured_at' in state
    assert 'connection_id' in state
    assert 'state_version' in state
    assert state['os_name'] == 'Ubuntu'
    assert state['package_manager'] == 'apt'

def test_compare_states_no_changes(state_evaluator):
    """Test state comparison with no changes"""
    before = {
        'memory_available': '8G',
        'disk_available': '50G',
        'running_services': ['ssh', 'nginx'],
        'installed_packages': ['nginx']
    }
    after = {
        'memory_available': '8G',
        'disk_available': '50G',
        'running_services': ['ssh', 'nginx'],
        'installed_packages': ['nginx']
    }
    
    changes = state_evaluator.compare_states(before, after)
    assert len(changes) == 0

def test_compare_states_with_changes(state_evaluator):
    """Test state comparison with changes"""
    before = {
        'memory_available': '8G',
        'disk_available': '50G',
        'running_services': ['ssh'],
        'installed_packages': ['nginx']
    }
    after = {
        'memory_available': '7G',
        'disk_available': '45G',
        'running_services': ['ssh', 'nginx'],
        'installed_packages': ['nginx', 'apache2']
    }
    
    changes = state_evaluator.compare_states(before, after)
    assert len(changes) > 0
    
    # Check for service change
    service_changes = [c for c in changes if c.change_type == StateChangeType.SERVICE_CHANGE]
    assert len(service_changes) > 0
    
    # Check for package change
    package_changes = [c for c in changes if c.change_type == StateChangeType.PACKAGE_CHANGE]
    assert len(package_changes) > 0

def test_evaluate_step_success(state_evaluator):
    """Test step success evaluation"""
    step_result = {
        'step_id': 'test-step-1',
        'success': True,
        'exit_code': 0,
        'stdout': 'nginx installed successfully',
        'stderr': ''
    }
    
    expected_outcome = 'nginx installed'
    state_changes = [
        StateChange(
            change_type=StateChangeType.PACKAGE_CHANGE,
            key='package_installed_nginx',
            before='not_installed',
            after='installed',
            significance=1.0,
            description='Package nginx installed'
        )
    ]
    
    evaluation = state_evaluator.evaluate_step_success(step_result, expected_outcome, state_changes)
    
    assert evaluation.step_id == 'test-step-1'
    assert evaluation.evaluation_result == EvaluationResult.SUCCESS
    assert len(evaluation.success_indicators) > 0
    assert evaluation.confidence_score > 0.0

def test_evaluate_step_failure(state_evaluator):
    """Test step failure evaluation"""
    step_result = {
        'step_id': 'test-step-2',
        'success': False,
        'exit_code': 1,
        'stdout': '',
        'stderr': 'Permission denied'
    }
    
    expected_outcome = 'nginx installed'
    state_changes = []
    
    evaluation = state_evaluator.evaluate_step_success(step_result, expected_outcome, state_changes)
    
    assert evaluation.evaluation_result == EvaluationResult.FAILURE
    assert len(evaluation.failure_indicators) > 0
    assert any('permission denied' in indicator.lower() for indicator in evaluation.failure_indicators)

def test_calculate_significance(state_evaluator):
    """Test significance calculation"""
    # Test numeric change
    significance = state_evaluator._calculate_significance('memory_available', '8G', '7G')
    assert 0.0 <= significance <= 1.0
    
    # Test string change
    significance = state_evaluator._calculate_significance('os_name', 'Ubuntu', 'CentOS')
    assert significance == 1.0
    
    # Test no change
    significance = state_evaluator._calculate_significance('os_name', 'Ubuntu', 'Ubuntu')
    assert significance == 0.0

def test_extract_success_indicators(state_evaluator):
    """Test success indicator extraction"""
    step_result = {
        'success': True,
        'exit_code': 0,
        'stdout': 'nginx installed successfully',
        'stderr': ''
    }
    
    indicators = state_evaluator._extract_success_indicators(step_result, 'nginx installed')
    
    assert 'Command executed successfully' in indicators
    assert 'Command returned exit code 0' in indicators
    assert any('nginx installed' in indicator for indicator in indicators)

def test_extract_failure_indicators(state_evaluator):
    """Test failure indicator extraction"""
    step_result = {
        'success': False,
        'exit_code': 1,
        'stdout': '',
        'stderr': 'Permission denied: cannot install package'
    }
    
    indicators = state_evaluator._extract_failure_indicators(step_result)
    
    assert 'Command execution failed' in indicators
    assert 'Command returned non-zero exit code: 1' in indicators
    assert any('permission denied' in indicator.lower() for indicator in indicators)

def test_determine_evaluation_result(state_evaluator):
    """Test evaluation result determination"""
    # Success case
    result = state_evaluator._determine_evaluation_result(
        ['success'], [], []
    )
    assert result == EvaluationResult.SUCCESS
    
    # Failure case
    result = state_evaluator._determine_evaluation_result(
        [], ['failed'], []
    )
    assert result == EvaluationResult.FAILURE
    
    # Partial case
    result = state_evaluator._determine_evaluation_result(
        ['success'], ['warning'], []
    )
    assert result == EvaluationResult.PARTIAL

def test_generate_recommendations(state_evaluator):
    """Test recommendation generation"""
    # Success recommendations
    recommendations = state_evaluator._generate_recommendations(
        EvaluationResult.SUCCESS, ['success'], [], []
    )
    assert 'Step completed successfully' in recommendations
    
    # Failure recommendations
    recommendations = state_evaluator._generate_recommendations(
        EvaluationResult.FAILURE, [], ['failed'], []
    )
    assert 'Step failed - review error messages' in recommendations

if __name__ == "__main__":
    pytest.main([__file__])
