#!/usr/bin/env python3
"""
In-Memory FastAPI Server for Ping AI Agent
Session-based storage - all data persists only while backend is running
"""

from fastapi import FastAPI, HTTPException, Header, Request, Depends
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import existing modules
from agent import Agent
from ssh_manager import SSHManager
from command_executor import CommandExecutor
from secrets_manager import SecretsManager

# Import in-memory storage
from memory_storage import memory_storage

# Configuration constants
DEFAULT_PORT = 8000
DEFAULT_HOST = "0.0.0.0"
DEFAULT_SSH_PORT = 22

# Status codes
STATUS_CONNECTED = "connected"
STATUS_PENDING_APPROVAL = "pending_approval"
STATUS_APPROVED = "approved"
STATUS_COMPLETED = "completed"

# Initialize FastAPI app
app = FastAPI(
    title="Ping AI Agent API - In-Memory Version",
    description="AI-powered system administration with session-based in-memory storage",
    version="3.0.0"
)

# CORS Configuration - Local development only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Auth helper
def require_auth(request: Request = None, user_id: str = Header(None, alias="user-id")):
    if request and request.method == "OPTIONS":
        return None
    if not user_id:
        raise HTTPException(status_code=401, detail="user-id header required")
    return user_id

# Pydantic models
class SSHConnectionRequest(BaseModel):
    hostname: str
    username: str
    password: str
    port: int = DEFAULT_SSH_PORT

class SSHConnectionResponse(BaseModel):
    success: bool
    connection_id: Optional[str] = None
    message: str
    hostname: str
    username: str
    port: int

class TaskRequest(BaseModel):
    connection_id: str
    request: str
    priority: str = "normal"

class CommandStep(BaseModel):
    step: int
    command: str
    explanation: str
    risk_level: str
    estimated_time: Optional[str] = None
    status: Optional[str] = "pending"
    approved_by: Optional[str] = None

class TaskResponse(BaseModel):
    command_id: str
    status: str
    generated_commands: List[CommandStep]
    intent: str
    action: str
    risk_level: str
    explanation: str
    created_at: str
    approval_required: bool

class StepApprovalRequest(BaseModel):
    step_index: int
    approved: bool
    reason: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    storage_type: str
    features: List[str]
    stats: Dict[str, int]

# In-memory session storage
user_agents: Dict[str, Dict[str, Agent]] = {}
user_ssh_managers: Dict[str, SSHManager] = {}
user_last_activity: Dict[str, datetime] = {}

# Inactivity settings
INACTIVITY_TIMEOUT_MINUTES = 60
background_task_running = False

# Initialize secrets manager
secrets_manager = SecretsManager()

# Helper functions
def update_user_activity(user_id: str):
    """Update the last activity timestamp for a user"""
    user_last_activity[user_id] = datetime.now()

def resolve_active_connection_id(user_id: str, requested_connection_id: str = None) -> str:
    """Resolve the active connection ID for a user"""
    connections = memory_storage.get_user_active_connections(user_id)
    
    if not connections:
        raise HTTPException(status_code=409, detail="No active SSH connection. Please reconnect and try again.")
    
    # If requested connection exists and is active, use it
    if requested_connection_id:
        for conn in connections:
            if conn["id"] == requested_connection_id:
                return requested_connection_id
    
    # Otherwise return first active connection
    return connections[0]["id"]

async def cleanup_inactive_users():
    """Background task to clean up inactive users"""
    global background_task_running
    background_task_running = True
    
    while background_task_running:
        try:
            await asyncio.sleep(300)  # Check every 5 minutes
            
            current_time = datetime.now()
            inactive_users = []
            
            for user_id, last_activity in user_last_activity.items():
                time_since_activity = current_time - last_activity
                if time_since_activity.total_seconds() > (INACTIVITY_TIMEOUT_MINUTES * 60):
                    inactive_users.append(user_id)
            
            for user_id in inactive_users:
                print(f"[MEMORY] Cleaning up inactive user {user_id}")
                
                # Disconnect SSH connections
                if user_id in user_ssh_managers:
                    ssh_manager = user_ssh_managers[user_id]
                    connections = memory_storage.get_user_active_connections(user_id)
                    for conn in connections:
                        try:
                            ssh_manager.disconnect(conn["id"])
                        except Exception as e:
                            print(f"[ERROR] Failed to disconnect {conn['id']}: {e}")
                    
                    del user_ssh_managers[user_id]
                
                # Disconnect all connections in storage
                memory_storage.disconnect_all_user_connections(user_id)
                
                # Remove from tracking
                del user_last_activity[user_id]
                if user_id in user_agents:
                    del user_agents[user_id]
                    
        except Exception as e:
            print(f"[ERROR] Cleanup task error: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    print("[MEMORY] Starting in-memory backend")
    print("[MEMORY] All data will be lost on restart")
    asyncio.create_task(cleanup_inactive_users())

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global background_task_running
    background_task_running = False
    print("[MEMORY] Shutting down - all session data will be lost")

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check with storage statistics"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="3.0.0",
        storage_type="in-memory (session-based)",
        features=[
            "In-Memory Storage",
            "Session-Based Persistence",
            "Encrypted Credentials",
            "Step-by-Step Approval",
            "Audit Logging",
            "Auto-Cleanup on Inactivity"
        ],
        stats=memory_storage.get_stats()
    )

@app.post("/api/connect", response_model=SSHConnectionResponse)
async def connect_to_server(
    request: Request,
    ssh_request: SSHConnectionRequest, 
    user_id: str = Depends(require_auth)
):
    """Connect to server with encrypted credential storage"""
    update_user_activity(user_id)
    
    print(f"[MEMORY] Connect request from user {user_id} to {ssh_request.hostname}:{ssh_request.port}")
    
    try:
        # Create or get user
        memory_storage.create_or_get_user(user_id, f"{user_id}@otium.local")
        
        # Initialize user storage
        if user_id not in user_ssh_managers:
            user_ssh_managers[user_id] = SSHManager()
        if user_id not in user_agents:
            user_agents[user_id] = {}
        
        # Disconnect any existing connections for this user
        active_connections = memory_storage.get_user_active_connections(user_id)
        if active_connections:
            ssh_manager = user_ssh_managers[user_id]
            for conn in active_connections:
                ssh_manager.disconnect(conn["id"])
                memory_storage.disconnect_connection(conn["id"])
        
        # Connect via SSH
        ssh_manager = user_ssh_managers[user_id]
        connection_result = ssh_manager.connect_and_store(
            hostname=ssh_request.hostname,
            username=ssh_request.username,
            password=ssh_request.password,
            port=ssh_request.port
        )
        
        if not connection_result['success']:
            memory_storage.log_action(
                user_id=user_id,
                action="connect_failed",
                details={"hostname": ssh_request.hostname, "error": connection_result['error']},
                success=False
            )
            raise HTTPException(status_code=400, detail=connection_result['error'])
        
        # Encrypt and store credentials
        connection_id = connection_result['connection_id']
        credentials = {
            "hostname": ssh_request.hostname,
            "username": ssh_request.username,
            "password": ssh_request.password,
            "port": ssh_request.port
        }
        encrypted_credentials = secrets_manager.encrypt_credentials(credentials)
        
        # Store connection in memory (use the same connection_id from SSH manager)
        memory_storage.create_connection(
            user_id=user_id,
            hostname=ssh_request.hostname,
            username=ssh_request.username,
            encrypted_credentials=encrypted_credentials,
            port=ssh_request.port,
            connection_id=connection_id
        )
        
        # Initialize agent
        agent = await initialize_agent(user_id, connection_id)
        
        # Log successful connection
        memory_storage.log_action(
            user_id=user_id,
            action="connect",
            details={"hostname": ssh_request.hostname, "connection_id": connection_id},
            connection_id=connection_id,
            success=True
        )
        
        memory_storage.update_user_last_login(user_id)
        
        return SSHConnectionResponse(
            success=True,
            connection_id=connection_id,
            message="SSH connection established successfully",
            hostname=ssh_request.hostname,
            username=ssh_request.username,
            port=ssh_request.port
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")

@app.post("/api/commands", response_model=TaskResponse)
async def submit_task(
    request: Request,
    task_request: TaskRequest,
    user_id: str = Depends(require_auth)
):
    """Submit task with in-memory persistence and step-by-step approval"""
    update_user_activity(user_id)
    
    print(f"[MEMORY] Task submission from user {user_id}: '{task_request.request}'")
    
    try:
        # Validate connection exists
        connections = memory_storage.get_user_active_connections(user_id)
        if not connections:
            raise HTTPException(status_code=404, detail="No active connection. Please connect first.")
        
        # Use the first active connection if requested one doesn't exist
        connection_id = task_request.connection_id
        if not any(conn["id"] == connection_id for conn in connections):
            connection_id = connections[0]["id"]
            print(f"[MEMORY] Using first active connection: {connection_id}")
        
        # Generate command plan
        agent = await initialize_agent(user_id, connection_id)
        if not agent:
            raise HTTPException(status_code=500, detail="Failed to initialize AI agent")
        
        command_plan = await generate_command_plan(user_id, connection_id, task_request.request)
        
        # Create command in memory
        command = memory_storage.create_command(
            user_id=user_id,
            connection_id=connection_id,
            request=task_request.request,
            intent=command_plan.get('intent', 'Unknown'),
            action=command_plan.get('action', 'Unknown'),
            risk_level=command_plan.get('risk_level', 'medium'),
            priority=task_request.priority,
            generated_commands=command_plan['steps']
        )
        
        # Log the action
        memory_storage.log_action(
            user_id=user_id,
            action="submit_command",
            details={
                "command_id": command["id"],
                "request": task_request.request,
                "total_steps": len(command_plan['steps'])
            },
            command_id=command["id"],
            connection_id=connection_id,
            success=True
        )
        
        # Convert to response format
        command_steps = []
        for i, step in enumerate(command_plan['steps']):
            command_steps.append(CommandStep(
                step=i + 1,
                command=step.get('command', ''),
                explanation=step.get('explanation', ''),
                risk_level=step.get('risk_level', 'medium'),
                estimated_time=step.get('estimated_time', 'Unknown'),
                status="pending"
            ))
        
        return TaskResponse(
            command_id=command["id"],
            status=STATUS_PENDING_APPROVAL,
            generated_commands=command_steps,
            intent=command["intent"],
            action=command["action"],
            risk_level=command["risk_level"],
            explanation=command_plan.get('explanation', 'No explanation'),
            created_at=command["created_at"].isoformat(),
            approval_required=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Task submission failed: {e}")
        raise HTTPException(status_code=500, detail=f"Command submission failed: {str(e)}")

@app.post("/api/commands/{command_id}/approve-step")
async def approve_command_step(
    command_id: str,
    request: Request,
    approval_request: StepApprovalRequest,
    user_id: str = Depends(require_auth)
):
    """Approve or reject a specific command step - APPROVE = EXECUTE IMMEDIATELY"""
    update_user_activity(user_id)
    
    print(f"[MEMORY] Step approval: command={command_id}, step={approval_request.step_index}, approved={approval_request.approved}")
    
    try:
        # Create step approval
        memory_storage.create_step_approval(
            command_id=command_id,
            user_id=user_id,
            step_index=approval_request.step_index,
            approved=approval_request.approved,
            reason=approval_request.reason
        )
        
        # Get command
        command = memory_storage.get_command(command_id, user_id)
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")
        
        execution_result = None
        
        # If APPROVED, execute the step immediately
        if approval_request.approved:
            try:
                # Resolve active connection
                resolved_conn_id = resolve_active_connection_id(user_id, command["connection_id"])
                
                # Get SSH manager
                ssh_manager = user_ssh_managers.get(user_id)
                if not ssh_manager:
                    raise Exception("SSH session expired. Please reconnect.")
                
                # Execute the step
                executor = CommandExecutor(ssh_manager, resolved_conn_id)
                step_command = command["generated_commands"][approval_request.step_index]
                result = executor.execute_single_step(step_command, approval_request.step_index)
                execution_result = result
                
                # Update execution results
                existing_results = command.get("execution_results") or {
                    "success": None,
                    "total_steps": len(command["generated_commands"]),
                    "successful_steps": 0,
                    "failed_steps": 0,
                    "step_results": []
                }
                
                step_result = {
                    "step_index": approval_request.step_index,
                    "command": step_command.get('command', ''),
                    "success": result.get('success', False),
                    "output": result.get('output', ''),
                    "exit_code": result.get('exit_code', -1),
                    "execution_time": result.get('execution_time', 0)
                }
                existing_results["step_results"].append(step_result)
                
                if result.get('success', False):
                    existing_results["successful_steps"] += 1
                else:
                    existing_results["failed_steps"] += 1
                
                # Update overall success
                total_executed = existing_results["successful_steps"] + existing_results["failed_steps"]
                if total_executed == existing_results["total_steps"]:
                    existing_results["success"] = existing_results["failed_steps"] == 0
                
                memory_storage.update_command_execution_results(command_id, existing_results)
                
                memory_storage.log_action(
                    user_id=user_id,
                    action="step_execution",
                    details={"command_id": command_id, "step_index": approval_request.step_index, "success": result.get('success', False)},
                    command_id=command_id,
                    connection_id=resolved_conn_id,
                    success=result.get('success', False)
                )
                
            except Exception as exec_error:
                print(f"[ERROR] Step execution failed: {exec_error}")
                execution_result = {"success": False, "error": str(exec_error), "output": ""}
        
        # Check if all steps have been responded to
        step_approvals = memory_storage.get_command_approvals(command_id)
        total_steps = len(command["generated_commands"])
        all_responded = len(step_approvals) == total_steps
        
        if all_responded:
            memory_storage.update_command_status(command_id, "completed", user_id)
        
        # Build approval status
        approved_steps = sum(1 for a in step_approvals if a["approved"])
        rejected_steps = sum(1 for a in step_approvals if not a["approved"])
        pending_steps = total_steps - len(step_approvals)
        
        steps = []
        for i in range(total_steps):
            step_approval = next((a for a in step_approvals if a["step_index"] == i), None)
            
            step_data = {
                "step_index": i,
                "command": command["generated_commands"][i].get('command', ''),
                "explanation": command["generated_commands"][i].get('explanation', ''),
                "risk_level": command["generated_commands"][i].get('risk_level', 'medium'),
                "status": "approved" if (step_approval and step_approval["approved"]) else ("rejected" if step_approval else "pending"),
                "approved": step_approval["approved"] if step_approval else None,
                "approved_at": step_approval["approved_at"].isoformat() if step_approval else None
            }
            steps.append(step_data)
        
        return {
            "command_id": command_id,
            "step_index": approval_request.step_index,
            "status": "approved" if approval_request.approved else "rejected",
            "message": f"Step {approval_request.step_index} {'approved and executed' if approval_request.approved else 'rejected'} successfully",
            "execution_result": execution_result,
            "all_responded": all_responded,
            "approval_status": {
                "command_id": command_id,
                "total_steps": total_steps,
                "approved_steps": approved_steps,
                "rejected_steps": rejected_steps,
                "pending_steps": pending_steps,
                "steps": steps
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Step approval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Step approval failed: {str(e)}")

@app.get("/api/commands/{command_id}/approval-status")
async def get_command_approval_status(
    command_id: str,
    request: Request,
    user_id: str = Depends(require_auth)
):
    """Get the approval status of a specific command"""
    try:
        command = memory_storage.get_command(command_id, user_id)
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")
        
        step_approvals = memory_storage.get_command_approvals(command_id)
        total_steps = len(command["generated_commands"])
        
        approved_steps = sum(1 for a in step_approvals if a["approved"])
        rejected_steps = sum(1 for a in step_approvals if not a["approved"])
        pending_steps = total_steps - len(step_approvals)
        
        steps = []
        for i in range(total_steps):
            step_approval = next((a for a in step_approvals if a["step_index"] == i), None)
            
            step_data = {
                "step_index": i,
                "command": command["generated_commands"][i].get('command', ''),
                "explanation": command["generated_commands"][i].get('explanation', ''),
                "risk_level": command["generated_commands"][i].get('risk_level', 'medium'),
                "status": "approved" if (step_approval and step_approval["approved"]) else ("rejected" if step_approval else "pending"),
                "approved": step_approval["approved"] if step_approval else None
            }
            steps.append(step_data)
        
        return {
            "command_id": command_id,
            "total_steps": total_steps,
            "approved_steps": approved_steps,
            "rejected_steps": rejected_steps,
            "pending_steps": pending_steps,
            "can_execute": (rejected_steps == 0 and pending_steps == 0),
            "steps": steps
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get approval status: {str(e)}")

@app.get("/api/ssh/status")
async def get_ssh_status(request: Request, user_id: str = Depends(require_auth)):
    """Get SSH connection status"""
    update_user_activity(user_id)
    
    connections = memory_storage.get_user_active_connections(user_id)
    
    # Convert to frontend format
    connections_dict = {}
    for conn in connections:
        connections_dict[conn["id"]] = {
            "user_id": conn["user_id"],
            "hostname": conn["hostname"],
            "username": conn["username"],
            "port": conn["port"],
            "connected_at": conn["connected_at"].isoformat(),
            "status": conn["status"],
            "alive": True
        }
    
    return {
        "connections": connections_dict,
        "total_connections": len(connections_dict),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/disconnect")
async def disconnect_ssh(request: Request, user_id: str = Depends(require_auth)):
    """Disconnect SSH connection"""
    try:
        body = await request.json()
        connection_id = body.get("connection_id")
        
        if not connection_id:
            # Disconnect all connections
            if user_id in user_ssh_managers:
                ssh_manager = user_ssh_managers[user_id]
                connections = memory_storage.get_user_active_connections(user_id)
                for conn in connections:
                    ssh_manager.disconnect(conn["id"])
                del user_ssh_managers[user_id]
            
            memory_storage.disconnect_all_user_connections(user_id)
            return {"status": "success", "message": "All connections disconnected"}
        
        # Disconnect specific connection
        if user_id in user_ssh_managers:
            ssh_manager = user_ssh_managers[user_id]
            ssh_manager.disconnect(connection_id)
        
        memory_storage.disconnect_connection(connection_id)
        
        memory_storage.log_action(
            user_id=user_id,
            action="disconnect",
            details={"connection_id": connection_id},
            connection_id=connection_id
        )
        
        return {"success": True, "message": "Disconnected successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/commands")
async def list_commands(
    request: Request,
    user_id: str = Depends(require_auth),
    status: Optional[str] = None,
    connection_id: Optional[str] = None,
    limit: int = 50
):
    """List commands for a user"""
    try:
        commands = memory_storage.get_user_commands(user_id, limit, status, connection_id)
        
        command_list = []
        for cmd in commands:
            command_dict = {
                "id": cmd["id"],
                "connection_id": cmd["connection_id"],
                "request": cmd["request"],
                "priority": cmd["priority"],
                "status": cmd["status"],
                "intent": cmd["intent"],
                "action": cmd["action"],
                "risk_level": cmd["risk_level"],
                "explanation": "",
                "created_at": cmd["created_at"].isoformat(),
                "approved_at": cmd["approved_at"].isoformat() if cmd["approved_at"] else None,
                "executed_at": cmd["executed_at"].isoformat() if cmd["executed_at"] else None,
                "completed_at": cmd["completed_at"].isoformat() if cmd["completed_at"] else None,
                "generated_commands": cmd["generated_commands"],
                "execution_results": cmd["execution_results"] or {}
            }
            command_list.append(command_dict)
        
        return {
            "commands": command_list,
            "total": len(command_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list commands: {str(e)}")

# Helper functions
async def initialize_agent(user_id: str, connection_id: str):
    """Initialize agent for user and connection"""
    try:
        print(f"[DEBUG] Initializing agent for user {user_id}, connection {connection_id}")
        
        # Check if user has SSH manager
        if user_id not in user_ssh_managers:
            print(f"[ERROR] SSH manager not found for user {user_id}")
            return None
            
        ssh_manager = user_ssh_managers[user_id]
        
        # Check Anthropic API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print(f"[ERROR] Anthropic API key not set")
            return None
        print(f"[DEBUG] Anthropic API key found: {api_key[:10]}...")
        
        # Check connection exists
        if not ssh_manager.is_connection_alive(connection_id):
            print(f"[ERROR] SSH connection {connection_id} not alive")
            return None
        print(f"[DEBUG] SSH connection {connection_id} is alive")
        
        agent = Agent(
            api_key=api_key,
            ssh_manager=ssh_manager,
            connection_id=connection_id
        )
        print(f"[DEBUG] Agent object created")
        
        if agent.start():
            user_agents[user_id][connection_id] = agent
            print(f"[DEBUG] Agent started successfully")
            return agent
        else:
            print(f"[ERROR] Agent start() returned False")
            return None
    except Exception as e:
        print(f"[ERROR] Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def generate_command_plan(user_id: str, connection_id: str, request: str):
    """Generate command plan using agent"""
    if user_id not in user_agents or connection_id not in user_agents[user_id]:
        raise HTTPException(status_code=500, detail="Agent not found")
    
    agent = user_agents[user_id][connection_id]
    
    if not hasattr(agent, 'command_generator') or agent.command_generator is None:
        raise HTTPException(status_code=500, detail="Agent command generator not initialized")
    
    try:
        command_plan = agent.command_generator.generate_commands(request)
        if not command_plan or 'steps' not in command_plan:
            raise HTTPException(status_code=422, detail="Could not generate commands")
        return command_plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Command generation failed: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Ping AI Agent API - In-Memory Version",
        "version": "3.0.0",
        "storage": "session-based (in-memory)",
        "features": [
            "In-Memory Storage",
            "Session-Based Persistence",
            "Encrypted Credentials",
            "Step-by-Step Approval",
            "Audit Logging"
        ],
        "note": "All data is lost on backend restart"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server_memory:app", host=DEFAULT_HOST, port=DEFAULT_PORT, reload=True)


