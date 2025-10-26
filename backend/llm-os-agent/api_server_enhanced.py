#!/usr/bin/env python3
"""
Enhanced FastAPI Server for Otium AI Agent - Version 2
Integrates database persistence, step-by-step approval, audit logging, and security controls
"""

from fastapi import FastAPI, HTTPException, Header, Request, Response, Depends
from fastapi.encoders import jsonable_encoder
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import uuid
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from decimal import Decimal
from uuid import UUID
import base64
import logging
import traceback
import asyncio

# Import existing modules
from agent import Agent
from ssh_manager import SSHManager
from command_executor import CommandExecutor

# Import new database modules  
from database import get_db, init_database
from database_service import DatabaseService
from secrets_manager import SecretsManager

# Configuration constants
DEFAULT_PORT = 8000
DEFAULT_HOST = "0.0.0.0"
DEFAULT_SSH_PORT = 22

# Setup logging
logger = logging.getLogger(__name__)

# Safe serialization helpers
def _default_encoder(obj):
    """Custom encoder for non-JSON-serializable objects"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, (bytes, bytearray)):
        # Avoid dumping raw bytes into JSON
        return {"__type__": "bytes", "base64": base64.b64encode(obj).decode("ascii")}
    if isinstance(obj, set):
        return list(obj)
    # Last resort: stringify
    return str(obj)

def serialize_command(cmd) -> dict:
    """Safely serialize a command object to JSON-compatible dict"""
    try:
        # Build dict with safe field access - let FastAPI handle JSON serialization
        payload = {
            "id": str(cmd.id) if cmd.id else None,
            "connection_id": str(cmd.connection_id) if cmd.connection_id else None,
            "request": getattr(cmd, "request", None) or "",
            "priority": getattr(cmd, "priority", None) or "normal",
            "status": getattr(cmd, "status", None) or "pending",
            "intent": getattr(cmd, "intent", None) or "Unknown",
            "action": getattr(cmd, "action", None) or "Unknown",
            "risk_level": getattr(cmd, "risk_level", None) or "medium",
            "explanation": getattr(cmd, "explanation", None) or "",
            "created_at": cmd.created_at.isoformat() if getattr(cmd, "created_at", None) else None,
            "approved_at": cmd.approved_at.isoformat() if getattr(cmd, "approved_at", None) else None,
            "executed_at": cmd.executed_at.isoformat() if getattr(cmd, "executed_at", None) else None,
            "completed_at": cmd.completed_at.isoformat() if getattr(cmd, "completed_at", None) else None,
            "generated_commands": cmd.generated_commands or [],  # JSONB field
            "execution_results": cmd.execution_results or {}     # JSONB field
        }
        return payload  # Return plain dict, FastAPI handles JSON serialization
    except Exception as e:
        logger.error(f"Failed to serialize command {getattr(cmd, 'id', 'unknown')}: {str(e)}")
        # Return minimal safe representation
        return {
            "id": str(getattr(cmd, "id", "unknown")),
            "error": f"Serialization failed: {str(e)}"
        }

# Status codes
STATUS_CONNECTED = "connected"
STATUS_PENDING_APPROVAL = "pending_approval"
STATUS_APPROVED = "approved"
STATUS_COMPLETED = "completed"

# Initialize database
init_database()

# Initialize FastAPI app
app = FastAPI(
    title="Otium AI Agent API - Enhanced Version",
    description="AI-powered system administration with enterprise security and step-by-step approval",
    version="2.0.0"
)

# SESSION-BASED: Background task for cleaning up inactive users
background_task_running = False

async def inactivity_cleanup_task():
    """Background task to clean up inactive users every 5 minutes"""
    global background_task_running
    background_task_running = True
    
    while background_task_running:
        try:
            print("[DEBUG] Running inactivity cleanup check...")
            cleanup_inactive_users()
            await asyncio.sleep(300)  # 5 minutes
        except Exception as e:
            print(f"[ERROR] Inactivity cleanup task error: {str(e)}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying

@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    print("[DEBUG] Starting inactivity cleanup background task...")
    asyncio.create_task(inactivity_cleanup_task())

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global background_task_running
    background_task_running = False
    print("[DEBUG] Stopped inactivity cleanup background task")

# CORS Configuration - Local development only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",        # Local development
        "http://127.0.0.1:3000",        # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Auth helper that skips OPTIONS requests (handled by CORS middleware)
async def require_auth(request: Request, user_id: str = Header(None, alias="user-id")):
    # Skip auth for OPTIONS requests - let CORS middleware handle them
    if request.method == "OPTIONS":
        return "options_skip"  # Return dummy value for OPTIONS
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
    database_status: str
    features: List[str]

# User storage for backward compatibility
user_agents: Dict[str, Dict[str, Agent]] = {}
user_connections: Dict[str, Dict[str, Any]] = {}
user_ssh_managers: Dict[str, SSHManager] = {}

# SESSION-BASED: Inactivity tracking
INACTIVITY_TIMEOUT_MINUTES = 60  # 60 minutes of inactivity before auto-disconnect (was 20)
user_last_activity: Dict[str, datetime] = {}

# Initialize secrets manager
secrets_manager = SecretsManager()

# SESSION-BASED: Inactivity management functions
def update_user_activity(user_id: str):
    """Update the last activity timestamp for a user"""
    user_last_activity[user_id] = datetime.now()
    print(f"[DEBUG] Updated activity for user {user_id}")

def resolve_active_connection_id(user_id: str, requested_connection_id: str = None) -> str:
    """Resolve the active connection ID for a user - prefer requested if alive, else pick any alive"""
    mem = user_connections.get(user_id, {})
    alive = [cid for cid, info in mem.items() if info.get("alive")]
    
    if requested_connection_id and requested_connection_id in alive:
        return requested_connection_id
    if alive:
        return alive[0]
    raise HTTPException(status_code=409, detail="No active SSH connection. Please reconnect and try again.")

def persist_connection_remap(db_service, command_id: str, resolved_conn_id: str, user_id: str):
    """Update command's connection_id if it was remapped to an active connection"""
    # For now, just log - we can implement DB update later if needed
    print(f"[DEBUG] Connection remapped for command {command_id}: using {resolved_conn_id}")

def cleanup_inactive_users():
    """Disconnect users who have been inactive for too long"""
    if not user_last_activity:
        return
        
    current_time = datetime.now()
    inactive_users = []
    
    for user_id, last_activity in user_last_activity.items():
        time_since_activity = current_time - last_activity
        if time_since_activity.total_seconds() > (INACTIVITY_TIMEOUT_MINUTES * 60):
            inactive_users.append(user_id)
    
    for user_id in inactive_users:
        print(f"[DEBUG] Disconnecting inactive user {user_id} (inactive for {INACTIVITY_TIMEOUT_MINUTES} minutes)")
        
        # Disconnect all SSH connections for this user
        if user_id in user_ssh_managers:
            ssh_manager = user_ssh_managers[user_id]
            if user_id in user_connections:
                for connection_id in list(user_connections[user_id].keys()):
                    try:
                        ssh_manager.disconnect(connection_id)
                        print(f"[DEBUG] Disconnected connection {connection_id} for inactive user {user_id}")
                    except Exception as e:
                        print(f"[ERROR] Failed to disconnect {connection_id}: {str(e)}")
                
                # Clear user's connections
                user_connections[user_id].clear()
            
            # Remove SSH manager
            del user_ssh_managers[user_id]
        
        # Remove user from tracking
        del user_last_activity[user_id]
        if user_id in user_agents:
            del user_agents[user_id]
        if user_id in user_connections:
            del user_connections[user_id]

# Handle OPTIONS requests explicitly for CORS preflight
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    """Handle all OPTIONS requests for CORS preflight"""
    return Response(status_code=200)

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check with database status"""
    try:
        db = next(get_db())
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="2.0.0",
        database_status=db_status,
        features=[
            "Database Persistence",
            "Encrypted Credentials",
            "Step-by-Step Approval",
            "Audit Logging",
            "Role-Based Security"
        ]
    )

@app.post("/api/connect", response_model=SSHConnectionResponse)
async def connect_to_server(
    request: Request,
    ssh_request: SSHConnectionRequest, 
    user_id: str = Depends(require_auth)
):
    """Connect to server with encrypted credential storage"""
    # SESSION-BASED: Update user activity
    update_user_activity(user_id)
    
    print(f"[DEBUG] Connect request from user {user_id} to {ssh_request.hostname}:{ssh_request.port}")
    print(f"[DEBUG] SSH Request details: hostname={ssh_request.hostname}, username={ssh_request.username}, port={ssh_request.port}")
    try:
        # Get database service
        print(f"[DEBUG] Getting database connection...")
        db = next(get_db())
        print(f"[DEBUG] Creating database service...")
        db_service = DatabaseService(db)
        print(f"[DEBUG] Database service created successfully")
        
        # Create or get WorkOS user (not tied to server credentials)
        print(f"[DEBUG] Creating/getting WorkOS user {user_id}...")
        user = db_service.create_or_get_user(user_id, f"{user_id}@otium.app")  # Use WorkOS ID for email
        print(f"[DEBUG] WorkOS user created/retrieved: {user}")
        
        # Initialize user storage
        print(f"[DEBUG] Initializing user storage...")
        if user_id not in user_ssh_managers:
            print(f"[DEBUG] Creating new SSHManager for user {user_id}")
            user_ssh_managers[user_id] = SSHManager()
        if user_id not in user_connections:
            user_connections[user_id] = {}
        if user_id not in user_agents:
            user_agents[user_id] = {}
        print(f"[DEBUG] User storage initialized successfully")
        
        # Check if user already has an active connection
        if user_id in user_connections and user_connections[user_id]:
            # User already has a connection - disconnect old one first
            for conn_id, conn_info in list(user_connections[user_id].items()):
                if conn_info.get('status') == STATUS_CONNECTED:
                    print(f"[DEBUG] User {user_id} already has active connection {conn_id}, disconnecting first")
                    ssh_manager = user_ssh_managers[user_id]
                    ssh_manager.disconnect(conn_id)
                    del user_connections[user_id][conn_id]
        
        # Connect via SSH
        ssh_manager = user_ssh_managers[user_id]
        connection_result = ssh_manager.connect_and_store(
            hostname=ssh_request.hostname,
            username=ssh_request.username,
            password=ssh_request.password,
            port=ssh_request.port
        )
        
        if not connection_result['success']:
            db_service.log_action(
                user_id=user_id,
                action="connect_failed",
                details={"hostname": ssh_request.hostname, "error": connection_result['error']},
                success=False
            )
            db.close()
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
        
        # Store connection in database (any user can connect to any server)
        print(f"[DEBUG] Creating connection record for user {user_id} to {ssh_request.hostname}...")
        db_service.create_connection(
            user_id=user_id,  # Use actual WorkOS user ID
            hostname=ssh_request.hostname,
            username=ssh_request.username,
            encrypted_credentials=encrypted_credentials,
            port=ssh_request.port
        )
        print(f"[DEBUG] Connection record created successfully")
        
        # Store in memory for active use
        connection_info = {
            "user_id": user_id,
            "hostname": ssh_request.hostname,
            "username": ssh_request.username,
            "port": ssh_request.port,
            "connected_at": datetime.now().isoformat(),
            "status": STATUS_CONNECTED,
            "alive": True  # Add alive flag for frontend compatibility
        }
        user_connections[user_id][connection_id] = connection_info
        
        print(f"[DEBUG] Stored connection {connection_id} for user {user_id}: {connection_info}")
        print(f"[DEBUG] Total connections for user: {len(user_connections[user_id])}")
        
        # Initialize agent
        agent = await initialize_agent(user_id, connection_id)
        
        # Log successful connection
        db_service.log_action(
            user_id=user_id,
            action="connect",
            details={
                "hostname": ssh_request.hostname,
                "connection_id": connection_id
            },
            connection_id=connection_id,
            success=True
        )
        
        db_service.update_user_last_login(user_id)
        db.close()
        
        return SSHConnectionResponse(
            success=True,
            connection_id=connection_id,
            message="SSH connection established successfully",
            hostname=ssh_request.hostname,
            username=ssh_request.username,
            port=ssh_request.port
        )
        
    except HTTPException as he:
        print(f"[DEBUG] HTTPException in connect: {he.detail}")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error in connect: {str(e)}")
        import traceback
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")

@app.post("/api/commands", response_model=TaskResponse)
async def submit_task(
    request: Request,
    task_request: TaskRequest,
    user_id: str = Depends(require_auth)
):
    """Submit task with database persistence and step-by-step approval"""
    # SESSION-BASED: Update user activity
    update_user_activity(user_id)
    
    print(f"[DEBUG] Task submission from user {user_id}")
    print(f"[DEBUG] Task request: connection_id={task_request.connection_id}, request='{task_request.request}'")
    try:
        # Get database service
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Smart connection selection - prefer active memory connections over database ones
        print(f"[DEBUG] Validating connection {task_request.connection_id} for user {user_id}")
        
        # Get memory connections (active SSH sessions)
        memory_connection_ids = set()
        if user_id in user_connections:
            memory_connection_ids = set(user_connections[user_id].keys())
        print(f"[DEBUG] Memory/Active connection IDs: {list(memory_connection_ids)}")
        
        # Get database connections
        db_connections = db_service.get_user_active_connections(user_id)
        db_connection_ids = {conn.id for conn in db_connections}
        print(f"[DEBUG] Database connection IDs: {list(db_connection_ids)}")
        
        # Smart connection selection logic - PREFER active memory connections
        actual_connection_id = task_request.connection_id
        
        # If requested connection exists in memory (active), use it as-is
        if task_request.connection_id in memory_connection_ids:
            print(f"[DEBUG] Using requested connection {task_request.connection_id} (found in active memory)")
        # If we have active memory connections but requested connection is stale (database-only), switch to active
        elif memory_connection_ids and task_request.connection_id in db_connection_ids:
            actual_connection_id = list(memory_connection_ids)[0]  # Use first active connection
            print(f"[DEBUG] Requested connection {task_request.connection_id} is stale (database only)")
            print(f"[DEBUG] Switching to active memory connection: {actual_connection_id}")
        # If requested connection exists in database and no memory connections, try to use it
        elif task_request.connection_id in db_connection_ids:
            print(f"[DEBUG] Using requested connection {task_request.connection_id} (found in database, no memory connections)")
        # If connection doesn't exist anywhere, fail
        else:
            all_connection_ids = db_connection_ids.union(memory_connection_ids)
            print(f"[DEBUG] Connection {task_request.connection_id} not found for user {user_id}")
            print(f"[DEBUG] Available connections: {list(all_connection_ids)}")
            raise HTTPException(status_code=404, detail="Connection not found")
        
        print(f"[DEBUG] Connection validation passed, using connection: {actual_connection_id}")
        
        # Update the connection_id to use the active one
        task_request.connection_id = actual_connection_id
        
        # Generate command plan
        print(f"[DEBUG] Initializing agent for user {user_id}, connection {task_request.connection_id}")
        agent = await initialize_agent(user_id, task_request.connection_id)
        if not agent:
            print(f"[DEBUG] Failed to initialize AI agent")
            raise HTTPException(status_code=500, detail="Failed to initialize AI agent")
        print(f"[DEBUG] Agent initialized successfully")
        
        print(f"[DEBUG] Generating command plan...")
        command_plan = await generate_command_plan(user_id, task_request.connection_id, task_request.request)
        print(f"[DEBUG] Command plan generated successfully: {len(command_plan.get('steps', []))} steps")
        
        # Ensure we use a connection_id that exists in database for foreign key constraint
        database_connection_id = None
        if db_connection_ids:
            # Use the first database connection ID to satisfy foreign key constraint
            database_connection_id = list(db_connection_ids)[0]
            print(f"[DEBUG] Using database connection ID for command: {database_connection_id}")
        else:
            # If no database connection, we need to create one for the active connection
            print(f"[DEBUG] No database connection found, creating record for active connection: {actual_connection_id}")
            # This should rarely happen if connection persistence is working correctly
            database_connection_id = actual_connection_id
        
        # Create command in database
        command = db_service.create_command(
            user_id=user_id,
            connection_id=database_connection_id,  # Use database connection ID for foreign key
            request=task_request.request,
            intent=command_plan.get('intent', 'Unknown'),
            action=command_plan.get('action', 'Unknown'),
            risk_level=command_plan.get('risk_level', 'medium'),
            priority=task_request.priority,
            generated_commands=command_plan['steps']
        )
        
        # Log the action
        db_service.log_action(
            user_id=user_id,
            action="submit_command",
            details={
                "command_id": command.id,
                "request": task_request.request,
                "total_steps": len(command_plan['steps'])
            },
            command_id=command.id,
            connection_id=task_request.connection_id,
            success=True
        )
        
        db.close()
        
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
            command_id=command.id,
            status=STATUS_PENDING_APPROVAL,
            generated_commands=command_steps,
            intent=command.intent,
            action=command.action,
            risk_level=command.risk_level,
            explanation=command_plan.get('explanation', 'No explanation'),
            created_at=command.created_at.isoformat(),
            approval_required=True
        )
        
    except HTTPException as he:
        print(f"[DEBUG] HTTPException in submit_task: {he.detail}")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error in submit_task: {str(e)}")
        import traceback
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Command submission failed: {str(e)}")

@app.post("/api/commands/{command_id}/approve-step")
async def approve_command_step(
    command_id: str,
    request: Request,
    approval_request: StepApprovalRequest,
    user_id: str = Depends(require_auth)
):
    """Approve or reject a specific command step - APPROVE = EXECUTE IMMEDIATELY"""
    print(f"[DEBUG] ===== APPROVE COMMAND STEP CALLED =====")
    print(f"[DEBUG] Command ID: {command_id}")
    print(f"[DEBUG] User ID: {user_id}")
    print(f"[DEBUG] Approval Request: {approval_request}")
    
    # SESSION-BASED: Update user activity
    update_user_activity(user_id)
    
    try:
        # Get database service
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Create step approval
        approval = db_service.create_step_approval(
            command_id=command_id,
            user_id=user_id,
            step_index=approval_request.step_index,
            approved=approval_request.approved,
            reason=approval_request.reason
        )
        
        # Log the approval
        db_service.log_action(
            user_id=user_id,
            action="step_approval",
            details={
                "command_id": command_id,
                "step_index": approval_request.step_index,
                "approved": approval_request.approved
            },
            command_id=command_id,
            success=True
        )
        
        # Get command for execution
        command = db_service.get_command(command_id, user_id)
        if not command:
            raise Exception("Command not found")
        
        execution_result = None
        
        # If APPROVED, execute the step immediately
        if approval_request.approved:
            try:
                print(f"[DEBUG] Executing approved step {approval_request.step_index} immediately")
                
                # Resolve active connection
                resolved_conn_id = resolve_active_connection_id(user_id, command.connection_id)
                print(f"[DEBUG] Resolved connection ID: {resolved_conn_id}")
                
                # Get SSH manager
                ssh_manager = user_ssh_managers.get(user_id)
                if not ssh_manager:
                    print(f"[ERROR] SSH manager not found for user {user_id}")
                    raise Exception("SSH session expired. Please reconnect.")
                
                # Create CommandExecutor
                from command_executor import CommandExecutor
                executor = CommandExecutor(ssh_manager, resolved_conn_id)
                
                # Execute only this specific step
                step_command = command.generated_commands[approval_request.step_index]
                print(f"[DEBUG] Executing command: {step_command.get('command')}")
                
                # Execute single step
                result = executor.execute_single_step(step_command, approval_request.step_index)
                execution_result = result
                
                print(f"[DEBUG] Step execution result: {result}")
                
                # Save execution result to database
                # CRITICAL: Refresh command from database to get latest execution_results
                # (another step might have saved results while we were executing)
                db_service.db.refresh(command)
                
                # Get existing execution_results or create new structure
                existing_results = command.execution_results or {
                    "success": None,
                    "total_steps": len(command.generated_commands) if command.generated_commands else 0,
                    "successful_steps": 0,
                    "failed_steps": 0,
                    "skipped_steps": 0,
                    "total_execution_time": 0,
                    "step_results": []
                }
                
                # Initialize step_results if it doesn't exist
                if "step_results" not in existing_results:
                    existing_results["step_results"] = []
                
                # Add this step's result
                step_result = {
                    "step_index": approval_request.step_index,
                    "command": step_command.get('command', ''),
                    "success": result.get('success', False),
                    "status": result.get('status', 'unknown'),
                    "output": result.get('output', ''),
                    "stderr": result.get('stderr', ''),
                    "error": result.get('error', ''),
                    "exit_code": result.get('exit_code', -1),
                    "execution_time": result.get('execution_time', 0)
                }
                existing_results["step_results"].append(step_result)
                
                # Update counters
                if result.get('success', False):
                    existing_results["successful_steps"] = existing_results.get("successful_steps", 0) + 1
                else:
                    existing_results["failed_steps"] = existing_results.get("failed_steps", 0) + 1
                
                existing_results["total_execution_time"] = existing_results.get("total_execution_time", 0) + result.get('execution_time', 0)
                
                # Update overall success status
                total_executed = existing_results.get("successful_steps", 0) + existing_results.get("failed_steps", 0)
                if total_executed == existing_results.get("total_steps", 0):
                    # All steps executed - determine overall success
                    existing_results["success"] = existing_results.get("failed_steps", 0) == 0
                
                # Save to database
                db_service.update_command_execution_results(command_id, existing_results)
                print(f"[DEBUG] Saved execution result to database for step {approval_request.step_index}")
                
                # Log the execution
                db_service.log_action(
                    user_id=user_id,
                    action="step_execution",
                    details={
                        "command_id": command_id,
                        "step_index": approval_request.step_index,
                        "success": result.get('success', False),
                        "output": result.get('output', '')
                    },
                    command_id=command_id,
                    connection_id=resolved_conn_id,
                    success=result.get('success', False)
                )
                
            except Exception as exec_error:
                print(f"[ERROR] Step execution failed: {str(exec_error)}")
                import traceback
                print(f"[ERROR] Execution traceback: {traceback.format_exc()}")
                execution_result = {
                    "success": False,
                    "error": str(exec_error),
                    "output": ""
                }
        else:
            # If REJECTED, just log it (no execution)
            print(f"[DEBUG] Step {approval_request.step_index} rejected - skipping execution")
            print(f"[DEBUG] Rejection reason: {approval_request.reason or 'No reason provided'}")
            db_service.log_action(
                user_id=user_id,
                action="step_rejected",
                details={
                    "command_id": command_id,
                    "step_index": approval_request.step_index,
                    "reason": approval_request.reason or "No reason provided"
                },
                command_id=command_id,
                success=True
            )
        
        # Check if all steps have been responded to (approved or rejected)
        step_approvals = db_service.get_command_approvals(command_id)
        total_steps = len(command.generated_commands) if command.generated_commands else 0
        all_responded = len(step_approvals) == total_steps
        
        print(f"[DEBUG] Step approval check: {len(step_approvals)}/{total_steps} steps have responses")
        print(f"[DEBUG] All responded: {all_responded}")
        
        if all_responded:
            print(f"[DEBUG] All steps have responses - marking command as completed")
            db_service.update_command_status(command_id, "completed", user_id)
            print(f"[DEBUG] Command {command_id} status updated to 'completed'")
        
        # Get updated approval status for frontend
        step_approvals = db_service.get_command_approvals(command_id)
        command = db_service.get_command(command_id, user_id)
        
        # Build approval status response (same format as approval-status endpoint)
        total_steps = len(command.generated_commands) if command.generated_commands else 0
        approved_steps = 0
        rejected_steps = 0
        pending_steps = 0
        
        steps = []
        for i in range(total_steps):
            step_approval = next((approval for approval in step_approvals if approval.step_index == i), None)
            
            if step_approval:
                status = "approved" if step_approval.approved else "rejected"
                if step_approval.approved:
                    approved_steps += 1
                else:
                    rejected_steps += 1
            else:
                status = "pending"
                pending_steps += 1
            
            step_data = {
                "step_index": i,
                "command": command.generated_commands[i].get('command', '') if command.generated_commands else '',
                "explanation": command.generated_commands[i].get('explanation', '') if command.generated_commands else '',
                "risk_level": command.generated_commands[i].get('risk_level', 'medium') if command.generated_commands else 'medium',
                "estimated_time": command.generated_commands[i].get('estimated_time', 'Unknown') if command.generated_commands else 'Unknown',
                "status": status,
                "approved": step_approval.approved if step_approval else None,
                "approved_by": step_approval.user_id if step_approval else None,
                "reason": step_approval.approval_reason if step_approval else None,
                "approved_at": step_approval.approved_at.isoformat() if step_approval and step_approval.approved_at else None
            }
            steps.append(step_data)
        
        can_execute = (rejected_steps == 0 and pending_steps == 0 and approved_steps == total_steps)
        
        approval_status = {
            "command_id": command_id,
            "total_steps": total_steps,
            "approved_steps": approved_steps,
            "rejected_steps": rejected_steps,
            "pending_steps": pending_steps,
            "can_execute": can_execute,
            "steps": steps
        }
        
        db.close()
        
        return {
            "command_id": command_id,
            "step_index": approval_request.step_index,
            "status": "approved" if approval_request.approved else "rejected",
            "message": f"Step {approval_request.step_index} {'approved and executed' if approval_request.approved else 'rejected'} successfully",
            "execution_result": execution_result,
            "all_responded": all_responded,
            "approval_status": approval_status  # Frontend expects this field!
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step approval failed: {str(e)}")

@app.get("/api/commands/{command_id}/approval-status")
async def get_command_approval_status(
    command_id: str,
    request: Request,
    user_id: str = Depends(require_auth)
):
    """Get the approval status of a specific command"""
    try:
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Get command
        command = db_service.get_command(command_id, user_id)
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")
        
        # Get step approvals
        step_approvals = db_service.get_command_approvals(command_id)
        
        # Count approval statuses
        total_steps = len(command.generated_commands) if command.generated_commands else 0
        approved_steps = 0
        rejected_steps = 0
        pending_steps = 0
        
        # Create step status array
        steps = []
        for i in range(total_steps):
            step_approval = next((approval for approval in step_approvals if approval.step_index == i), None)
            
            if step_approval:
                status = "approved" if step_approval.approved else "rejected"
                if step_approval.approved:
                    approved_steps += 1
                else:
                    rejected_steps += 1
            else:
                status = "pending"
                pending_steps += 1
            
            step_data = {
                "step_index": i,
                "command": command.generated_commands[i].get('command', '') if command.generated_commands else '',
                "explanation": command.generated_commands[i].get('explanation', '') if command.generated_commands else '',
                "risk_level": command.generated_commands[i].get('risk_level', 'medium') if command.generated_commands else 'medium',
                "estimated_time": command.generated_commands[i].get('estimated_time', 'Unknown') if command.generated_commands else 'Unknown',
                "status": status,
                "approved": step_approval.approved if step_approval else None,
                "approved_by": step_approval.user_id if step_approval else None,
                "reason": step_approval.approval_reason if step_approval else None,
                "approved_at": step_approval.approved_at.isoformat() if step_approval and step_approval.approved_at else None
            }
            steps.append(step_data)
        
        can_execute = (rejected_steps == 0 and pending_steps == 0 and approved_steps == total_steps)
        
        db.close()
        
        return {
            "command_id": command_id,
            "total_steps": total_steps,
            "approved_steps": approved_steps,
            "rejected_steps": rejected_steps,
            "pending_steps": pending_steps,
            "can_execute": can_execute,
            "steps": steps
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get approval status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get approval status: {str(e)}")

@app.post("/api/commands/{command_id}/execute")
async def execute_command(
    command_id: str,
    request: Request,
    user_id: str = Depends(require_auth)
):
    """Execute all approved steps of a command"""
    try:
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Get command
        command = db_service.get_command(command_id, user_id)
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")
        
        # Check if command is fully approved
        if not db_service.is_command_fully_approved(command_id):
            raise HTTPException(status_code=400, detail="Command is not fully approved")
        
        # Update status to executing
        db_service.update_command_status(command_id, "executing", user_id)
        
        # Get SSH manager and execute commands
        if user_id not in user_ssh_managers:
            raise HTTPException(status_code=500, detail="SSH manager not found")
        
        ssh_manager = user_ssh_managers[user_id]
        
        # Import CommandExecutor
        from command_executor import CommandExecutor
        
        # Find the active connection for this command
        connection_found = False
        active_connection_id = None
        
        # Check if command's connection exists in memory
        if user_id in user_connections:
            for conn_id, conn_info in user_connections[user_id].items():
                if conn_info.get('hostname') == command.connection.hostname:
                    active_connection_id = conn_id
                    connection_found = True
                    break
        
        # If not in memory, try to re-establish connection
        if not connection_found:
            # Get connection details from database
            db_connection = db_service.get_connection(command.connection_id, user_id)
            if not db_connection:
                raise HTTPException(status_code=500, detail="Connection details not found")
            
            # For now, we'll use the command's original connection_id and hope it's still valid
            active_connection_id = command.connection_id
            print(f"[DEBUG] Using database connection ID for execution: {active_connection_id}")
        
        # Create command executor
        executor = CommandExecutor(ssh_manager, active_connection_id)
        
        # Execute the commands
        execution_results = executor.execute_steps(command.generated_commands)
        
        # Update command with results
        db_service.complete_command(command_id, execution_results)
        
        # Log the execution
        db_service.log_action(
            user_id=user_id,
            action="execute_command",
            details={
                "command_id": command_id,
                "total_steps": execution_results.get('total_steps', 0),
                "successful_steps": execution_results.get('successful_steps', 0),
                "failed_steps": execution_results.get('failed_steps', 0)
            },
            command_id=command_id,
            connection_id=active_connection_id,
            success=execution_results.get('overall_success', False)
        )
        
        db.close()
        
        return {
            "command_id": command_id,
            "status": "completed" if execution_results.get('overall_success') else "failed",
            "message": f"Command execution {'completed successfully' if execution_results.get('overall_success') else 'completed with errors'}",
            "execution_results": execution_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Command execution failed: {str(e)}")
        import traceback
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        
        # Update command status to failed
        try:
            db_service.update_command_status(command_id, "failed", user_id)
        except:
            pass
            
        raise HTTPException(status_code=500, detail=f"Command execution failed: {str(e)}")

# Include original endpoints for compatibility
@app.get("/api/status")
async def get_connection_status(request: Request, user_id: str = Depends(require_auth)):
    """Get connection status - check both memory and database"""
    print(f"[DEBUG] Status check for user {user_id}")
    print(f"[DEBUG] Memory connections keys: {list(user_connections.keys())}")
    
    # Get database service to check for persistent connections
    try:
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Get active connections from database
        db_connections = db_service.get_user_active_connections(user_id)
        print(f"[DEBUG] Database shows {len(db_connections)} active connections for user {user_id}")
        
        # Build response format compatible with frontend
        connections = {}
        for db_conn in db_connections:
            connections[db_conn.id] = {
                "user_id": db_conn.user_id,
                "hostname": db_conn.hostname,
                "username": db_conn.username,
                "port": db_conn.port,
                "connected_at": db_conn.connected_at.isoformat(),
                "status": db_conn.status,
                "alive": True if db_conn.status == STATUS_CONNECTED else False
            }
        
        # Also check memory connections and merge
        if user_id in user_connections:
            print(f"[DEBUG] Also found {len(user_connections[user_id])} memory connections")
            for conn_id, conn_info in user_connections[user_id].items():
                if conn_id not in connections:  # Don't overwrite database info
                    connections[conn_id] = conn_info
        
        db.close()
        
        print(f"[DEBUG] Returning {len(connections)} total connections")
        return {
            "connections": connections,
            "total_connections": len(connections),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"[DEBUG] Database error, falling back to memory: {str(e)}")
        # Fallback to memory-only if database fails
    if user_id not in user_connections:
        return {"connections": {}, "total_connections": 0, "timestamp": datetime.now().isoformat()}
    
    return {
        "connections": user_connections[user_id],
        "total_connections": len(user_connections[user_id]),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/ssh/status")
async def get_ssh_status(request: Request, user_id: str = Depends(require_auth)):
    """Get SSH connection status (alias for /api/status for frontend compatibility)"""
    # SESSION-BASED: Update user activity
    update_user_activity(user_id)
    
    result = await get_connection_status(request, user_id)
    print(f"[DEBUG] SSH Status for user {user_id}: {result}")
    return result

@app.post("/api/disconnect")
async def disconnect_ssh(request: Request, user_id: str = Depends(require_auth)):
    """Disconnect SSH connection"""
    try:
        body = await request.json()
        connection_id = body.get("connection_id")
        
        # SESSION-BASED: If no specific connection_id, disconnect ALL user connections
        if not connection_id:
            print(f"[DEBUG] No connection_id provided, disconnecting ALL connections for user {user_id}")
            # Disconnect all connections for this user
            if user_id in user_ssh_managers:
                ssh_manager = user_ssh_managers[user_id]
                if user_id in user_connections:
                    for conn_id in list(user_connections[user_id].keys()):
                        try:
                            ssh_manager.disconnect(conn_id)
                            print(f"[DEBUG] Disconnected connection {conn_id}")
                        except Exception as e:
                            print(f"[ERROR] Failed to disconnect {conn_id}: {str(e)}")
                    user_connections[user_id].clear()
                del user_ssh_managers[user_id]
            
            # Update all database connections for this user to disconnected
            db = next(get_db())
            db_service = DatabaseService(db)
            db_service.disconnect_all_user_connections(user_id)
            db.close()
            
            return {"status": "success", "message": "All connections disconnected"}
        
        # Original logic for specific connection_id
        print(f"[DEBUG] Disconnecting specific connection: {connection_id}")
        
        # Get database service
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Disconnect from SSH manager
        if user_id in user_ssh_managers:
            ssh_manager = user_ssh_managers[user_id]
            ssh_manager.disconnect(connection_id)
        
        # Update database
        db_service.disconnect_connection(connection_id)
        
        # Remove from user connections
        if user_id in user_connections and connection_id in user_connections[user_id]:
            del user_connections[user_id][connection_id]
        
        # Log the action
        db_service.log_action(
            user_id=user_id,
            action="disconnect",
            details={"connection_id": connection_id},
            connection_id=connection_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        db.close()
        
        return {"success": True, "message": "Disconnected successfully"}
        
    except Exception as e:
        print(f"Disconnect error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/commands/{command_id}/chat")
async def send_chat_message(
    command_id: str,
    request: Request,
    chat_request: dict,
    user_id: str = Depends(require_auth)
):
    """Send a chat message about a command"""
    try:
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Get command
        command = db_service.get_command(command_id, user_id)
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")
        
        # Extract message from request
        message = chat_request.get('message', '')
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Save user message
        user_msg = db_service.create_chat_message(
            command_id=command_id,
            sender='user',
            message=message
        )
        
        # TODO: Generate AI response using OpenAI
        # For now, just return a simple acknowledgment
        ai_response = f"I understand you're asking about: {message}. This is the chat feature - AI responses coming soon!"
        
        # Save AI response
        ai_msg = db_service.create_chat_message(
            command_id=command_id,
            sender='ai',
            message=ai_response
        )
        
        db.close()
        
        return {
            "user_message": {
                "id": user_msg.id,
                "message": user_msg.message,
                "created_at": user_msg.created_at.isoformat()
            },
            "ai_message": {
                "id": ai_msg.id,
                "message": ai_msg.message,
                "created_at": ai_msg.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat message failed: {str(e)}")

@app.get("/api/commands/{command_id}/chat")
async def get_chat_messages(
    command_id: str,
    request: Request,
    user_id: str = Depends(require_auth)
):
    """Get chat messages for a command"""
    try:
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Get command
        command = db_service.get_command(command_id, user_id)
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")
        
        # Get chat messages
        messages = db_service.get_chat_messages(command_id)
        
        db.close()
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "sender": msg.sender,
                    "message": msg.message,
                    "message_type": msg.message_type,
                    "created_at": msg.created_at.isoformat(),
                    "metadata": msg.message_metadata or {}
                }
                for msg in messages
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat messages: {str(e)}")

@app.get("/api/commands")
async def list_commands(
    request: Request,
    user_id: str = Depends(require_auth),
    status: Optional[str] = None,
    connection_id: Optional[str] = None,
    limit: int = 50
):
    """List commands with safe serialization and proper error handling"""
    logger.debug(f"list_commands: user_id={user_id}, connection_id={connection_id}, limit={limit}")
    
    try:
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Get commands from database
        commands = db_service.get_user_commands(user_id, limit, status, connection_id)
        logger.debug(f"list_commands: db returned {len(commands)} rows")
        
        # Serialize commands safely - direct field access to avoid SQLAlchemy issues
        command_list = []
        for cmd in commands:
            try:
                # Direct field access with ONLY FIELDS THAT EXIST in Command model
                command_dict = {
                    "id": str(cmd.id) if cmd.id else "",
                    "connection_id": str(cmd.connection_id) if cmd.connection_id else "",
                    "request": cmd.request if cmd.request else "",
                    "priority": cmd.priority if cmd.priority else "normal",
                    "status": cmd.status if cmd.status else "pending",
                    "intent": cmd.intent if cmd.intent else "Unknown",
                    "action": cmd.action if cmd.action else "Unknown", 
                    "risk_level": cmd.risk_level if cmd.risk_level else "medium",
                    "explanation": "",  # Frontend expects this field - provide empty string
                    "created_at": cmd.created_at.isoformat() if cmd.created_at else None,
                    "approved_at": cmd.approved_at.isoformat() if cmd.approved_at else None,
                    "executed_at": cmd.executed_at.isoformat() if cmd.executed_at else None,
                    "completed_at": cmd.completed_at.isoformat() if cmd.completed_at else None,
                    "generated_commands": cmd.generated_commands if cmd.generated_commands else [],
                    "execution_results": cmd.execution_results if cmd.execution_results else {
                        "success": False,
                        "total_steps": 0,
                        "successful_steps": 0, 
                        "failed_steps": 0,
                        "skipped_steps": 0,
                        "total_execution_time": 0.0,
                        "step_results": []
                    }
                }
                command_list.append(command_dict)
                
            except Exception as cmd_error:
                logger.error(f"Failed to serialize command: {str(cmd_error)}")
                command_list.append({
                    "id": "error",
                    "error": f"Serialization failed: {str(cmd_error)}"
                })
        
        # Close session after serialization
        db.close()
        
        return {
            "commands": command_list,
            "total": len(command_list)
        }
        
    except Exception as e:
        logger.error(f"list_commands: exception: {str(e)}\n{traceback.format_exc()}")
        # Return 500 instead of silent empty - this is critical for debugging!
        raise HTTPException(status_code=500, detail=f"Failed to list commands: {str(e)}")

# Helper functions
async def initialize_agent(user_id: str, connection_id: str):
    """Initialize agent for user and connection"""
    try:
        ssh_manager = user_ssh_managers[user_id]
        agent = Agent(
            api_key=os.getenv("OPENAI_API_KEY"),
            ssh_manager=ssh_manager,
            connection_id=connection_id
        )
        
        if agent.start():
            user_agents[user_id][connection_id] = agent
            return agent
        return None
    except Exception as e:
        print(f"Error creating agent: {e}")
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
        "message": "Otium AI Agent API - Enhanced Version",
        "version": "2.0.0",
        "features": [
            "Database Persistence",
            "Encrypted Credential Storage", 
            "Step-by-Step Approval (Cursor-style)",
            "Comprehensive Audit Logging",
            "Role-Based Security"
        ],
        "new_endpoints": {
            "POST /api/commands/{id}/approve-step": "Approve/reject individual command steps",
            "GET /api/health": "Enhanced health check with database status"
        }
    }

@app.post("/api/commands/{command_id}/execute-immediately")
async def execute_command_immediately(
    command_id: str,
    request: Request,
    user_id: str = Depends(require_auth)
):
    """Execute command immediately via SSH - DIRECT EXECUTION (FIXED VERSION)"""
    print(f"[DEBUG] ===== EXECUTE IMMEDIATELY CALLED =====")
    print(f"[DEBUG] Command ID: {command_id}")
    print(f"[DEBUG] User ID: {user_id}")
    
    # SESSION-BASED: Update user activity
    update_user_activity(user_id)
    
    # Get database service
    db = next(get_db())
    db_service = DatabaseService(db)
    
    try:
        # 1) Load command
        command = db_service.get_command(command_id, user_id)
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")
        
        print(f"[DEBUG] Found command: {command.request}")
        print(f"[DEBUG] Generated commands: {command.generated_commands}")
        
        # 2) Resolve active connection (fix connection ID mismatch)
        try:
            resolved_conn_id = resolve_active_connection_id(user_id, command.connection_id)
            print(f"[DEBUG] Resolved connection ID: {resolved_conn_id}")
        except HTTPException as e:
            print(f"[ERROR] Connection resolution failed: {e.detail}")
            db_service.update_command_status(command_id, "failed", user_id)
            raise
        
        # 3) Persist connection remap so DB and memory align
        persist_connection_remap(db_service, command_id, resolved_conn_id, user_id)
        
        # 4) Get SSH manager
        ssh_manager = user_ssh_managers.get(user_id)
        if not ssh_manager:
            print(f"[ERROR] SSH manager not found for user {user_id}")
            db_service.update_command_status(command_id, "failed", user_id)
            raise HTTPException(status_code=440, detail="SSH session expired. Please reconnect.")
        
        # 5) Mark command as running
        print(f"[DEBUG] Marking command as running...")
        db_service.update_command_status(command_id, "running", user_id)
        
        # 6) Create CommandExecutor with BOTH parameters (FIX!)
        print(f"[DEBUG] Creating CommandExecutor with ssh_manager and connection_id: {resolved_conn_id}")
        from command_executor import CommandExecutor
        executor = CommandExecutor(ssh_manager, resolved_conn_id)
        
        # 7) ACTUALLY EXECUTE THE COMMANDS (this was missing!)
        print(f"[DEBUG] Starting command execution...")
        execution_results = executor.execute_steps(command.generated_commands)
        print(f"[DEBUG] ✅ Execution completed! Results: {execution_results}")
        
        # 8) Update command with results and final status
        exit_code = 0 if execution_results.get('success', False) else 1
        final_status = STATUS_COMPLETED if execution_results.get('success', False) else "failed"
        
        db_service.complete_command(command_id, execution_results)
        db_service.update_command_status(command_id, final_status, user_id)
        
        print(f"[DEBUG] Command marked as {final_status}")
        
        # 9) Log the execution
        db_service.log_action(
            user_id=user_id,
            action="execute_command_immediately",
            details={
                "command_id": command_id,
                "total_steps": execution_results.get('total_steps', 0),
                "successful_steps": execution_results.get('successful_steps', 0),
                "failed_steps": execution_results.get('failed_steps', 0),
                "resolved_connection_id": resolved_conn_id
            },
            command_id=command_id,
            connection_id=resolved_conn_id,
            success=execution_results.get('success', False)
        )
        
        return {
            "ok": True,
            "command_id": command_id,
            "status": final_status,
            "exit_code": exit_code,
            "message": f"Command executed {'successfully' if execution_results.get('success') else 'with errors'}",
            "execution_results": execution_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Immediate execution failed: {str(e)}")
        import traceback
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        
        # Update command status to failed
        try:
            db_service.update_command_status(command_id, "failed", user_id)
        except Exception as db_error:
            print(f"[ERROR] Failed to update command status: {db_error}")
            
        raise HTTPException(status_code=500, detail=f"Immediate execution failed: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server_v2:app", host=DEFAULT_HOST, port=DEFAULT_PORT, reload=True)
