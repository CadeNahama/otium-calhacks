#!/usr/bin/env python3
"""
FastAPI Server for Ping AI Agent
Integrates SSH manager, command executor, and agent for remote server management
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import our existing modules
from agent import Agent
from ssh_manager import SSHManager
from command_executor import CommandExecutor

# Configuration constants
DEFAULT_PORT = 8000
DEFAULT_HOST = "0.0.0.0"
DEFAULT_SSH_PORT = 22
DEFAULT_TIMEOUT = 10
DEFAULT_COMMAND_TIMEOUT = 300
DEFAULT_MAX_COMMANDS = 100
DEFAULT_MAX_PRIORITY_LENGTH = 500

# Environment variables
ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
ENV_DOTENV_PATH = ".env"

# Status codes
STATUS_CONNECTED = "connected"
STATUS_DISCONNECTED = "disconnected"
STATUS_PENDING_APPROVAL = "pending_approval"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_COMPLETED = "completed"

# Priority levels
VALID_PRIORITIES = ['low', 'normal', 'high', 'urgent']

# Error codes
ERROR_CODES = {
    'CONNECTION_NOT_FOUND': 'Connection not found',
    'INTERNAL_ERROR': 'Internal server error',
    'INVALID_PRIORITY': 'Invalid priority level',
    'NO_CONNECTION': 'No active server connection',
    'GENERATOR_NOT_READY': 'Command generator not ready',
    'GENERATION_ERROR': 'Command generation failed',
    'COMMAND_GENERATION_FAILED': 'Failed to generate command plan',
    'COMMAND_NOT_FOUND': 'Command not found',
    'INVALID_STATUS': 'Invalid command status'
}

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(ENV_DOTENV_PATH)
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="Ping AI Agent API",
    description="AI-powered Linux system administration backend with SSH support",
    version="1.0.0"
)

# CORS disabled for testing - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class SSHConnectionRequest(BaseModel):
    hostname: str = Field(..., description="Server hostname or IP address")
    username: str = Field(..., description="SSH username")
    password: str = Field(..., description="SSH password")
    port: int = Field(DEFAULT_SSH_PORT, description="SSH port", ge=1, le=65535)

class SSHConnectionResponse(BaseModel):
    success: bool
    connection_id: Optional[str] = None
    message: str
    hostname: str
    username: str
    port: int

class TaskRequest(BaseModel):
    connection_id: str = Field(..., description="Active SSH connection ID")
    request: str = Field(..., description="Natural language task description", max_length=DEFAULT_MAX_PRIORITY_LENGTH)
    priority: str = Field("normal", description="Task priority level")

class CommandStep(BaseModel):
    step: int
    command: str
    explanation: str
    risk_level: str
    estimated_time: Optional[str] = None

class TaskResponse(BaseModel):
    command_id: str
    status: str
    generated_commands: List[CommandStep]
    intent: str
    action: str
    risk_level: str
    explanation: str
    risk_assessment: Optional[Dict[str, Any]] = None
    created_at: str
    approval_required: bool

class CommandApproval(BaseModel):
    command_id: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    ssh_connections: int
    pending_commands: int
    active_executions: int

# User-scoped storage for multi-user support
user_agents: Dict[str, Dict[str, Agent]] = {}  # user_id -> {connection_id -> Agent}
user_connections: Dict[str, Dict[str, Any]] = {}  # user_id -> {connection_id -> connection_data}
user_commands: Dict[str, Dict[str, Any]] = {}  # user_id -> {command_id -> command_data}
user_ssh_managers: Dict[str, SSHManager] = {}  # user_id -> SSHManager


def get_environment_info() -> Dict[str, Any]:
    """Get environment information for debugging"""
    return {
        'openai_api_key_set': bool(os.getenv(ENV_OPENAI_API_KEY)),
        'openai_api_key_value': os.getenv(ENV_OPENAI_API_KEY, 'NOT_SET')[:20] if os.getenv(ENV_OPENAI_API_KEY) else 'NOT_SET',
        'current_working_directory': os.getcwd(),
        'env_file_exists': os.path.exists(ENV_DOTENV_PATH)
    }


def validate_priority(priority: str) -> None:
    """Validate task priority level"""
    if priority not in VALID_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid priority. Must be one of: {', '.join(VALID_PRIORITIES)}",
                "error_code": "INVALID_PRIORITY"
            }
        )


def validate_connection_exists(user_id: str, connection_id: str) -> None:
    """Validate that a connection exists for this user"""
    if user_id not in user_connections or connection_id not in user_connections[user_id]:
        raise HTTPException(
            status_code=404,
            detail={
                "error": ERROR_CODES['CONNECTION_NOT_FOUND'],
                "error_code": "CONNECTION_NOT_FOUND"
            }
        )


def validate_agent_initialized(user_id: str, connection_id: str) -> None:
    """Validate that the agent is initialized for this user and connection"""
    if user_id not in user_agents or connection_id not in user_agents[user_id]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": ERROR_CODES['NO_CONNECTION'],
                "error_code": "NO_CONNECTION"
            }
        )


def create_connection_info(user_id: str, hostname: str, username: str, port: int) -> Dict[str, Any]:
    """Create standardized connection info"""
    return {
        "user_id": user_id,
        "hostname": hostname,
        "username": username,
        "port": port,
        "connected_at": datetime.now().isoformat(),
        "status": STATUS_CONNECTED
    }


def create_command_data(user_id: str, task_request: TaskRequest, command_plan: Dict[str, Any], command_id: str) -> Dict[str, Any]:
    """Create standardized command data"""
    return {
        "id": command_id,
        "user_id": user_id,
        "connection_id": task_request.connection_id,
        "request": task_request.request,
        "priority": task_request.priority,
        "generated_commands": command_plan['steps'],
        "intent": command_plan.get('intent', 'Unknown'),
        "action": command_plan.get('action', 'Unknown'),
        "risk_level": command_plan.get('risk_level', 'Unknown'),
        "explanation": command_plan.get('explanation', 'No explanation'),
        "status": STATUS_PENDING_APPROVAL,
        "created_at": datetime.now().isoformat(),
        "approved_at": None,
        "executed_at": None,
        "completed_at": None
    }


def convert_command_steps(command_plan: Dict[str, Any]) -> List[CommandStep]:
    """Convert command plan steps to Pydantic models"""
    command_steps = []
    for i, step in enumerate(command_plan['steps']):
        command_steps.append(CommandStep(
            step=i + 1,
            command=step.get('command', ''),
            explanation=step.get('explanation', ''),
            risk_level=step.get('risk_level', 'Unknown'),
            estimated_time=step.get('estimated_time')
        ))
    return command_steps


def cleanup_dead_connections() -> None:
    """Remove dead connections from all users"""
    for user_id in list(user_connections.keys()):
        dead_connections = []
        ssh_manager = user_ssh_managers.get(user_id)
        
        if not ssh_manager:
            continue
            
        for conn_id in list(user_connections[user_id].keys()):
            if not ssh_manager.is_connection_alive(conn_id):
                dead_connections.append(conn_id)
        
        for conn_id in dead_connections:
            user_connections[user_id].pop(conn_id, None)
            if user_id in user_agents and conn_id in user_agents[user_id]:
                user_agents[user_id].pop(conn_id, None)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    total_connections = sum(len(connections) for connections in user_connections.values())
    total_pending = sum(len(commands) for commands in user_commands.values())
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        ssh_connections=total_connections,
        pending_commands=total_pending,
        active_executions=0  # Will implement later
    )


@app.post("/api/connect", response_model=SSHConnectionResponse)
async def connect_to_server(request: SSHConnectionRequest, user_id: str = Header("X-User-ID")):
    """Connect to a server via SSH and store the connection"""
    try:
        # Validate user_id
        if not user_id:
            return SSHConnectionResponse(
                success=False,
                message="User ID required",
                hostname=request.hostname,
                username=request.username,
                port=request.port
            )
        
        # Initialize user storage if needed
        if user_id not in user_ssh_managers:
            user_ssh_managers[user_id] = SSHManager()
        if user_id not in user_connections:
            user_connections[user_id] = {}
        if user_id not in user_agents:
            user_agents[user_id] = {}
        
        # Get user's SSH manager
        ssh_manager = user_ssh_managers[user_id]
        
        # Attempt SSH connection and storage
        connection_result = ssh_manager.connect_and_store(
            hostname=request.hostname,
            username=request.username,
            password=request.password,
            port=request.port
        )
        
        if not connection_result['success']:
            return SSHConnectionResponse(
                success=False,
                message=connection_result['error'],
                hostname=request.hostname,
                username=request.username,
                port=request.port
            )
        
        # Store connection info
        connection_id = connection_result['connection_id']
        user_connections[user_id][connection_id] = create_connection_info(
            user_id, request.hostname, request.username, request.port
        )
        
        # Initialize agent for this specific connection
        agent = await initialize_agent(user_id, connection_id)
        if not agent:
            return SSHConnectionResponse(
                success=False,
                message="Failed to initialize AI agent",
                hostname=request.hostname,
                username=request.username,
                port=request.port
            )
        
        return SSHConnectionResponse(
            success=True,
            connection_id=connection_id,
            message="SSH connection established successfully",
            hostname=request.hostname,
            username=request.username,
            port=request.port
        )
        
    except Exception as e:
        return SSHConnectionResponse(
            success=False,
            message=f"Connection failed: {str(e)}",
            hostname=request.hostname,
            username=request.username,
            port=request.port
        )


async def initialize_agent(user_id: str, connection_id: str) -> Optional[Agent]:
    """Initialize a new agent for a specific user and connection"""
    try:
        print(f"🔧 Initializing new agent for user {user_id}, connection {connection_id}...")
        env_info = get_environment_info()
        print(f"🔍 Debug: Agent creation parameters:")
        print(f"   - user_id: {user_id}")
        print(f"   - api_key: {'SET' if env_info['openai_api_key_set'] else 'NOT_SET'}")
        print(f"   - ssh_manager: {'SET' if user_ssh_managers.get(user_id) else 'NOT_SET'}")
        print(f"   - connection_id: {connection_id}")
        
        # Get user's SSH manager
        ssh_manager = user_ssh_managers[user_id]
        
        agent = Agent(
            api_key=os.getenv(ENV_OPENAI_API_KEY),
            ssh_manager=ssh_manager,
            connection_id=connection_id
        )
        print("Agent created successfully")
        
        # Start the agent in SSH mode
        print("Starting agent...")
        if not agent.start():
            print("Failed to start agent in SSH mode")
            return None
        print("Agent started successfully")
        
        # Store agent for this user and connection
        user_agents[user_id][connection_id] = agent
        
        return agent
        
    except Exception as e:
        print(f"Error creating agent: {e}")
        return None





@app.post("/api/disconnect")
async def disconnect_from_server(disconnect_request: CommandApproval, user_id: str = Header("X-User-ID")):
    """Disconnect from a server"""
    try:
        connection_id = disconnect_request.command_id
        validate_connection_exists(user_id, connection_id)
        
        # Get user's SSH manager
        ssh_manager = user_ssh_managers[user_id]
        
        # Close SSH connection
        ssh_manager.disconnect(connection_id)
        
        # Remove from user's connections
        connection_info = user_connections[user_id].pop(connection_id)
        
        # Remove agent for this connection
        if user_id in user_agents and connection_id in user_agents[user_id]:
            user_agents[user_id].pop(connection_id, None)
        
        return {
            "connection_id": connection_id,
            "status": STATUS_DISCONNECTED,
            "hostname": connection_info["hostname"],
            "disconnected_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": ERROR_CODES['INTERNAL_ERROR'],
                "error_code": "INTERNAL_ERROR",
                "details": str(e)
            }
        )


@app.get("/api/status")
async def get_connection_status(user_id: str = Header("X-User-ID")):
    """Get status of all connections for this user"""
    try:
        # Clean up dead connections first
        cleanup_dead_connections()
        
        # Only return connections for this user
        if user_id not in user_connections:
            return {
                "connections": {},
                "total_connections": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get connection statuses for this user
        connection_statuses = {}
        ssh_manager = user_ssh_managers.get(user_id)
        
        for conn_id, conn_info in user_connections[user_id].items():
            # Check if SSH connection is still alive
            is_alive = ssh_manager.is_connection_alive(conn_id) if ssh_manager else False
            conn_info_copy = conn_info.copy()
            conn_info_copy['alive'] = is_alive
            
            if not is_alive:
                conn_info_copy['status'] = STATUS_DISCONNECTED
                # Remove dead connections
                user_connections[user_id].pop(conn_id, None)
                if user_id in user_agents and conn_id in user_agents[user_id]:
                    user_agents[user_id].pop(conn_id, None)
            else:
                connection_statuses[conn_id] = conn_info_copy
        
        return {
            "connections": connection_statuses,
            "total_connections": len(connection_statuses),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": ERROR_CODES['INTERNAL_ERROR'],
                "error_code": "INTERNAL_ERROR",
                "details": str(e)
            }
        )


@app.get("/api/ssh/status")
async def get_ssh_status(user_id: str = Header("X-User-ID")):
    """Alias for /api/status to match frontend expectations"""
    return await get_connection_status(user_id)


@app.post("/api/commands", response_model=TaskResponse)
async def submit_task(task_request: TaskRequest, user_id: str = Header("X-User-ID")):
    """Submit a natural language task for execution"""
    try:
        # Validate user_id
        if not user_id:
            raise HTTPException(status_code=400, detail={"error": "User ID required"})
        
        # Validate connection exists for this user
        validate_connection_exists(user_id, task_request.connection_id)
        
        # Validate priority
        validate_priority(task_request.priority)
        
        # Check if agent is initialized for this user and connection
        validate_agent_initialized(user_id, task_request.connection_id)
        
        # Check agent status
        await check_agent_status(user_id, task_request.connection_id)
        
        # Generate command plan using the agent
        command_plan = await generate_command_plan(user_id, task_request.connection_id, task_request.request)
        
        # Create command data
        command_id = str(uuid.uuid4())
        command_data = create_command_data(user_id, task_request, command_plan, command_id)
        
        # Initialize user command storage if needed
        if user_id not in user_commands:
            user_commands[user_id] = {}
        
        # Store in user's commands
        user_commands[user_id][command_id] = command_data
        
        # Convert command steps to Pydantic models
        command_steps = convert_command_steps(command_plan)
        
        return TaskResponse(
            command_id=command_id,
            status=STATUS_PENDING_APPROVAL,
            generated_commands=command_steps,
            intent=command_plan.get('intent', 'Unknown'),
            action=command_plan.get('action', 'Unknown'),
            risk_level=command_plan.get('risk_level', 'Unknown'),
            explanation=command_plan.get('explanation', 'No explanation'),
            risk_assessment=None,  # Not implemented in Phase 1
            created_at=command_data["created_at"],
            approval_required=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": ERROR_CODES['INTERNAL_ERROR'],
                "error_code": "INTERNAL_ERROR",
                "details": str(e)
            }
        )


async def check_agent_status(user_id: str, connection_id: str) -> None:
    """Check agent status and components for specific user and connection"""
    print(f"🔍 Agent status check for user {user_id}, connection {connection_id}:")
    
    if user_id not in user_agents or connection_id not in user_agents[user_id]:
        print("❌ Agent not found for this user and connection")
        return
    
    agent = user_agents[user_id][connection_id]
    print(f"   - Agent exists: {agent is not None}")
    print(f"   - Command generator: {hasattr(agent, 'command_generator')}")
    print(f"   - Command generator initialized: {agent.command_generator is not None if hasattr(agent, 'command_generator') else False}")
    print(f"   - System context: {len(agent.system_context) if hasattr(agent, 'command_generator') else 0} items")


async def generate_command_plan(user_id: str, connection_id: str, request: str) -> Dict[str, Any]:
    """Generate command plan using the agent for specific user and connection"""
    print(f"🤖 Generating commands for user {user_id}, connection {connection_id}, request: {request}")
    
    # Get agent for this user and connection
    if user_id not in user_agents or connection_id not in user_agents[user_id]:
        print("❌ Agent not found for this user and connection")
        raise HTTPException(
            status_code=500,
            detail={
                "error": ERROR_CODES['GENERATOR_NOT_READY'],
                "error_code": "GENERATOR_NOT_READY",
                "details": "Agent not found for this user and connection"
            }
        )
    
    agent = user_agents[user_id][connection_id]
    
    # Check if command generator is available
    if not hasattr(agent, 'command_generator') or agent.command_generator is None:
        print("❌ Command generator not initialized")
        raise HTTPException(
            status_code=500,
            detail={
                "error": ERROR_CODES['GENERATOR_NOT_READY'],
                "error_code": "GENERATOR_NOT_READY",
                "details": "Agent command generator is not properly initialized"
            }
        )
    
    try:
        command_plan = agent.command_generator.generate_commands(request)
    except Exception as e:
        print(f"❌ Command generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": ERROR_CODES['GENERATION_ERROR'],
                "error_code": "GENERATION_ERROR",
                "details": f"Error generating commands: {str(e)}"
            }
        )
    
    if not command_plan or 'steps' not in command_plan:
        raise HTTPException(
            status_code=422,
            detail={
                "error": ERROR_CODES['COMMAND_GENERATION_FAILED'],
                "error_code": "COMMAND_GENERATION_FAILED",
                "details": "AI could not generate appropriate commands for this request"
            }
        )
    
    return command_plan


# Safety assessment removed in Phase 1 - handled by basic agent checks


@app.get("/api/commands/{command_id}")
async def get_command_status(command_id: str, user_id: str = Header("X-User-ID")):
    """Get status and details of a specific command"""
    try:
        # Validate user_id
        if not user_id:
            raise HTTPException(status_code=400, detail={"error": "User ID required"})
        
        # Check if user has this command
        if user_id not in user_commands or command_id not in user_commands[user_id]:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": ERROR_CODES['COMMAND_NOT_FOUND'],
                    "error_code": "COMMAND_NOT_FOUND"
                }
            )
        
        return user_commands[user_id][command_id]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": ERROR_CODES['INTERNAL_ERROR'],
                "error_code": "INTERNAL_ERROR",
                "details": str(e)
            }
        )


@app.post("/api/commands/{command_id}/approve")
async def approve_command(command_id: str, user_id: str = Header("X-User-ID")):
    """Approve a command for execution"""
    try:
        # Validate user_id
        if not user_id:
            raise HTTPException(status_code=400, detail={"error": "User ID required"})
        
        # Check if user has this command
        if user_id not in user_commands or command_id not in user_commands[user_id]:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": ERROR_CODES['COMMAND_NOT_FOUND'],
                    "error_code": "COMMAND_NOT_FOUND"
                }
            )
        
        command_data = user_commands[user_id][command_id]
        
        if command_data['status'] != STATUS_PENDING_APPROVAL:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": f"Command cannot be approved in status: {command_data['status']}",
                    "error_code": "INVALID_STATUS"
                }
            )
        
        # Update command status
        command_data['status'] = STATUS_APPROVED
        command_data['approved_at'] = datetime.now().isoformat()
        
        # Execute the command using the agent's command executor
        connection_id = command_data['connection_id']
        if user_id in user_agents and connection_id in user_agents[user_id]:
            agent = user_agents[user_id][connection_id]
            if hasattr(agent, 'command_executor'):
                # Set the connection ID for this execution
                agent.command_executor.set_connection_id(connection_id)
                execution_result = agent.command_executor.execute_steps(
                    command_data['generated_commands']
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Agent command executor not available",
                        "error_code": "EXECUTOR_NOT_AVAILABLE"
                    }
                )
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Agent not found for this connection",
                    "error_code": "AGENT_NOT_FOUND"
                }
            )
        
        # Update command with execution results
        command_data['status'] = STATUS_COMPLETED
        command_data['executed_at'] = datetime.now().isoformat()
        command_data['completed_at'] = datetime.now().isoformat()
        command_data['execution_results'] = execution_result
        
        return {
            "command_id": command_id,
            "status": STATUS_COMPLETED,
            "execution_results": execution_result,
            "message": "Command executed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": ERROR_CODES['INTERNAL_ERROR'],
                "error_code": "INTERNAL_ERROR",
                "details": str(e)
            }
        )


@app.post("/api/commands/{command_id}/reject")
async def reject_command(command_id: str, user_id: str = Header("X-User-ID")):
    """Reject a command"""
    try:
        # Validate user_id
        if not user_id:
            raise HTTPException(status_code=400, detail={"error": "User ID required"})
        
        # Check if user has this command
        if user_id not in user_commands or command_id not in user_commands[user_id]:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": ERROR_CODES['COMMAND_NOT_FOUND'],
                    "error_code": "COMMAND_NOT_FOUND"
                }
            )
        
        command_data = user_commands[user_id][command_id]
        
        if command_data['status'] != STATUS_PENDING_APPROVAL:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": f"Command cannot be rejected in status: {command_id}",
                    "error_code": "INVALID_STATUS"
                }
            )
        
        # Update command status
        command_data['status'] = STATUS_REJECTED
        command_data['rejected_at'] = datetime.now().isoformat()
        
        return {
            "command_id": command_id,
            "status": STATUS_REJECTED,
            "message": "Command rejected successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": ERROR_CODES['INTERNAL_ERROR'],
                "error_code": "INTERNAL_ERROR",
                "details": str(e)
            }
        )


@app.get("/api/commands")
async def list_commands(
    user_id: str = Header("X-User-ID"),
    status: Optional[str] = None,
    connection_id: Optional[str] = None,
    limit: int = 50
):
    """List all commands with optional filtering"""
    try:
        # Validate user_id
        if not user_id:
            raise HTTPException(status_code=400, detail={"error": "User ID required"})
        
        # Validate limit
        limit = min(limit, DEFAULT_MAX_COMMANDS)
        
        # Only return commands for this user
        if user_id not in user_commands:
            return {
                "commands": [],
                "total": 0,
                "filters": {
                    "status": status,
                    "connection_id": connection_id,
                    "limit": limit
                }
            }
        
        # Filter commands for this user
        filtered_commands = []
        for cmd_id, cmd_data in user_commands[user_id].items():
            # Apply status filter
            if status and cmd_data['status'] != status:
                continue
            
            # Apply connection filter
            if connection_id and cmd_data['connection_id'] != connection_id:
                continue
            
            filtered_commands.append(cmd_data)
        
        # Sort by creation date (newest first)
        filtered_commands.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Apply limit
        filtered_commands = filtered_commands[:limit]
        
        return {
            "commands": filtered_commands,
            "total": len(filtered_commands),
            "filters": {
                "status": status,
                "connection_id": connection_id,
                "limit": limit
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": ERROR_CODES['INTERNAL_ERROR'],
                "error_code": "INTERNAL_ERROR",
                "details": str(e)
            }
        )


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Ping AI Agent API",
        "version": "1.0.0",
        "description": "AI-powered Linux system administration backend with SSH support",
        "endpoints": {
            "POST /api/connect": "Connect to SSH server",
            "POST /api/disconnect": "Disconnect from server",
            "GET /api/status": "Get connection status",
            "POST /api/commands": "Submit natural language task",
            "GET /api/commands": "List commands",
            "GET /api/commands/{id}": "Get command details",
            "POST /api/commands/{id}/approve": "Approve command execution",
            "POST /api/commands/{id}/reject": "Reject command",
            "GET /api/health": "Health check"
        },
        "usage": {
            "1. Connect": "POST /api/connect with SSH credentials",
            "2. Submit Task": "POST /api/commands with natural language request",
            "3. Approve": "POST /api/commands/{id}/approve to execute",
            "4. Monitor": "GET /api/commands/{id} for status and results"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Ping AI Agent API Server...")
    print("📡 API endpoints available at http://localhost:8000")
    print("🔗 Health check: GET /api/health")
    print("🔌 Connect to server: POST /api/connect")
    print("📝 Submit task: POST /api/commands")
    print("📚 API documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        "api_server:app",
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        reload=True,
        log_level="info"
    )
