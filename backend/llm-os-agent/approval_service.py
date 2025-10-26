#!/usr/bin/env python3
"""
Step-by-step command approval service for Ping AI Agent
Implements Cursor-style approval workflow where each command step must be individually approved
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from database_service import DatabaseService
from auth_service import AuthService, UserRole
from security import SecurityLevel

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"

class StepApprovalResult:
    def __init__(self, step_index: int, status: ApprovalStatus, approved_by: str = None, 
                 reason: str = None, approved_at: datetime = None):
        self.step_index = step_index
        self.status = status
        self.approved_by = approved_by
        self.reason = reason
        self.approved_at = approved_at

class CommandApprovalService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    def requires_approval(self, command_data: Dict[str, Any], user_role: str) -> bool:
        """Determine if command requires approval based on risk level and user role"""
        risk_level = command_data.get('risk_level', 'medium')
        
        # High and critical risk commands always require approval
        if risk_level in ['high', 'critical']:
            return True
        
        # Commands that affect multiple systems require approval
        if self._affects_multiple_systems(command_data):
            return True
        
        # Commands during maintenance windows require approval
        if self._is_maintenance_window():
            return True
        
        # Viewer role always requires approval
        if user_role == 'viewer':
            return True
        
        return False
    
    def get_approval_requirements(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get approval requirements for a command"""
        risk_level = command_data.get('risk_level', 'medium')
        generated_commands = command_data.get('generated_commands', [])
        
        requirements = {
            'requires_approval': self.requires_approval(command_data, 'operator'),
            'risk_level': risk_level,
            'total_steps': len(generated_commands),
            'required_approver_role': self._get_required_approver_role(risk_level),
            'approval_timeout': self._get_approval_timeout(risk_level),
            'can_auto_approve': self._can_auto_approve(risk_level, generated_commands),
        }
        
        return requirements
    
    def create_step_approvals(self, command_id: str, generated_commands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create individual step approval records for each command step"""
        step_approvals = []
        
        for i, step in enumerate(generated_commands):
            # Determine if this step can be auto-approved
            can_auto_approve = self._can_auto_approve_step(step)
            
            if can_auto_approve:
                # Auto-approve safe steps
                approval = self.db_service.create_step_approval(
                    command_id=command_id,
                    user_id="system",  # System auto-approval
                    step_index=i,
                    approved=True,
                    reason="Auto-approved safe command"
                )
                step_approvals.append({
                    'step_index': i,
                    'status': 'approved',
                    'auto_approved': True,
                    'approved_by': 'system',
                    'approved_at': approval.approved_at.isoformat(),
                    'reason': 'Auto-approved safe command'
                })
            else:
                # Mark step as pending approval
                step_approvals.append({
                    'step_index': i,
                    'status': 'pending',
                    'auto_approved': False,
                    'approved_by': None,
                    'approved_at': None,
                    'reason': None
                })
        
        return step_approvals
    
    def approve_step(self, command_id: str, step_index: int, user_id: str, 
                    approved: bool, reason: str = None) -> StepApprovalResult:
        """Approve or reject a specific command step"""
        # Validate command exists
        command = self.db_service.get_command(command_id, user_id)
        if not command:
            raise Exception("Command not found")
        
        # Validate step index
        if not command.generated_commands or step_index >= len(command.generated_commands):
            raise Exception("Invalid step index")
        
        # Check if user can approve this step
        if not self._can_user_approve_step(command, step_index, user_id):
            raise Exception("User cannot approve this step")
        
        # Check if step is already approved/rejected
        existing_approvals = self.db_service.get_command_approvals(command_id)
        for approval in existing_approvals:
            if approval.step_index == step_index:
                raise Exception("Step already approved/rejected")
        
        # Create approval record
        approval = self.db_service.create_step_approval(
            command_id=command_id,
            user_id=user_id,
            step_index=step_index,
            approved=approved,
            reason=reason
        )
        
        # Log the approval action
        self.db_service.log_action(
            user_id=user_id,
            action="step_approval",
            details={
                "command_id": command_id,
                "step_index": step_index,
                "approved": approved,
                "reason": reason
            },
            command_id=command_id,
            success=True
        )
        
        return StepApprovalResult(
            step_index=step_index,
            status=ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED,
            approved_by=user_id,
            reason=reason,
            approved_at=approval.approved_at
        )
    
    def get_step_approval_status(self, command_id: str) -> Dict[str, Any]:
        """Get detailed approval status for all steps of a command"""
        step_status = self.db_service.get_step_approval_status(command_id)
        command = self.db_service.db.query(self.db_service.db.query(Command).filter(Command.id == command_id).first())
        
        if not command or not command.generated_commands:
            return {}
        
        # Build comprehensive status
        status = {
            'command_id': command_id,
            'total_steps': len(command.generated_commands),
            'approved_steps': 0,
            'rejected_steps': 0,
            'pending_steps': 0,
            'can_execute': False,
            'steps': []
        }
        
        for i, step in enumerate(command.generated_commands):
            step_info = {
                'step_index': i,
                'command': step.get('command', ''),
                'explanation': step.get('explanation', ''),
                'risk_level': step.get('risk_level', 'medium'),
                'estimated_time': step.get('estimated_time', 'Unknown'),
            }
            
            if i in step_status:
                approval_info = step_status[i]
                step_info.update({
                    'status': approval_info['status'],
                    'approved': approval_info['approved'],
                    'approved_by': approval_info['approved_by'],
                    'reason': approval_info['reason'],
                    'approved_at': approval_info['approved_at']
                })
                
                # Count statuses
                if approval_info['status'] == 'approved':
                    status['approved_steps'] += 1
                elif approval_info['status'] == 'rejected':
                    status['rejected_steps'] += 1
                else:
                    status['pending_steps'] += 1
            else:
                step_info.update({
                    'status': 'pending',
                    'approved': None,
                    'approved_by': None,
                    'reason': None,
                    'approved_at': None
                })
                status['pending_steps'] += 1
            
            status['steps'].append(step_info)
        
        # Determine if command can be executed
        status['can_execute'] = (
            status['pending_steps'] == 0 and 
            status['rejected_steps'] == 0 and 
            status['approved_steps'] > 0
        )
        
        return status
    
    def get_pending_approvals(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get all pending approvals for a user or all users"""
        # This would need to be implemented with proper queries
        # For now, return empty list
        return []
    
    def batch_approve_steps(self, command_id: str, step_indices: List[int], 
                           user_id: str, approved: bool, reason: str = None) -> List[StepApprovalResult]:
        """Approve or reject multiple steps at once"""
        results = []
        
        for step_index in step_indices:
            try:
                result = self.approve_step(command_id, step_index, user_id, approved, reason)
                results.append(result)
            except Exception as e:
                results.append(StepApprovalResult(
                    step_index=step_index,
                    status=ApprovalStatus.REJECTED,
                    reason=f"Error: {str(e)}"
                ))
        
        return results
    
    def _can_user_approve_step(self, command: Any, step_index: int, user_id: str) -> bool:
        """Check if user can approve a specific step"""
        # Get user info
        user = self.db_service.get_user(user_id)
        if not user:
            return False
        
        # Get step info
        if not command.generated_commands or step_index >= len(command.generated_commands):
            return False
        
        step = command.generated_commands[step_index]
        step_risk = step.get('risk_level', 'medium')
        
        # Check if user role can approve this risk level
        return AuthService.can_user_approve_command(user.role, step_risk)
    
    def _can_auto_approve_step(self, step: Dict[str, Any]) -> bool:
        """Determine if a step can be auto-approved"""
        command = step.get('command', '').lower()
        risk_level = step.get('risk_level', 'medium')
        
        # Never auto-approve high or critical risk commands
        if risk_level in ['high', 'critical']:
            return False
        
        # Auto-approve safe read-only commands
        safe_patterns = [
            'ls', 'pwd', 'whoami', 'date', 'uptime', 'uname',
            'df', 'free', 'ps', 'top', 'htop', 'netstat',
            'cat', 'head', 'tail', 'grep', 'find', 'locate',
            'stat', 'file', 'which', 'whereis', 'history'
        ]
        
        for pattern in safe_patterns:
            if command.startswith(pattern):
                return True
        
        return False
    
    def _affects_multiple_systems(self, command_data: Dict[str, Any]) -> bool:
        """Check if command affects multiple systems"""
        request = command_data.get('request', '').lower()
        
        multi_system_patterns = [
            'restart', 'stop', 'start', 'reload', 'reconfigure',
            'cluster', 'distributed', 'all nodes', 'all servers',
            'network', 'firewall', 'load balancer'
        ]
        
        for pattern in multi_system_patterns:
            if pattern in request:
                return True
        
        return False
    
    def _is_maintenance_window(self) -> bool:
        """Check if current time is within maintenance window"""
        # This is a placeholder - implement based on your maintenance schedule
        current_hour = datetime.utcnow().hour
        # Example: maintenance window is 2 AM - 4 AM UTC
        return 2 <= current_hour <= 4
    
    def _get_required_approver_role(self, risk_level: str) -> str:
        """Get required approver role for risk level"""
        if risk_level in ['high', 'critical']:
            return 'admin'
        return 'operator'
    
    def _get_approval_timeout(self, risk_level: str) -> int:
        """Get approval timeout in minutes"""
        timeouts = {
            'low': 60,      # 1 hour
            'medium': 30,   # 30 minutes
            'high': 15,     # 15 minutes
            'critical': 5   # 5 minutes
        }
        return timeouts.get(risk_level, 30)
    
    def _can_auto_approve(self, risk_level: str, generated_commands: List[Dict[str, Any]]) -> bool:
        """Check if entire command can be auto-approved"""
        if risk_level in ['high', 'critical']:
            return False
        
        # Check if all steps can be auto-approved
        for step in generated_commands:
            if not self._can_auto_approve_step(step):
                return False
        
        return True
