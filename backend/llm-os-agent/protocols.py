#!/usr/bin/env python3

from uagents import Model
from typing import Dict, Any, List

# --- 1. System Context Protocol (Context AEA <-> Orchestrator) ---
class ContextRequest(Model):
    """Message sent by Orchestrator requesting system context."""
    connection_id: str

class SystemContext(Model):
    """Message returned by Context AEA with system details."""
    os_name: str
    package_manager: str
    service_manager: str
    system_info: Dict[str, Any]
    error: str = None

# --- 2. Inference Protocol (Orchestrator <-> Inference AEA) ---
class PlanRequest(Model):
    """Message sent by Orchestrator requesting command plan generation."""
    user_request: str
    connection_id: str
    system_context: Dict[str, Any]

class CommandStepModel(Model):
    """Model for a single command step."""
    step: int
    command: str
    explanation: str
    risk_level: str

class CommandPlan(Model):
    """Message returned by Inference AEA with the final command plan."""
    command_plan: List[CommandStepModel]
    intent: str
    action: str
    risk_level: str
    explanation: str
    error: str = None

# --- 3. Execution Protocol (Orchestrator <-> Execution Service) ---
class ExecutionRequest(Model):
    """Message sent by Orchestrator to execute a single step."""
    connection_id: str
    step: CommandStepModel

class ExecutionResult(Model):
    """Message returned by the Execution Service with results."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    error: str = None