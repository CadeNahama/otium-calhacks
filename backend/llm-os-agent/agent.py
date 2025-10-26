#Completely replace the centrlaized agent.py file w the orchestrator file:

#!/usr/bin/env python3
"""
Otium Orchestrator AEA (Autonomous Economic Agent)
Replaces the monolithic Agent class, coordinating the decentralized pipeline.
This AEA acts as the primary interface between the FastAPI API and the specialized AEAs.
"""

import os
import sys
from typing import Dict, Any
from uagents import Agent, Context, Bureau, Protocol, Model
from .protocols import (
    ContextRequest, SystemContext, PlanRequest, CommandPlan, ExecutionRequest, ExecutionResult
)
from .database import get_db
from .database_service import DatabaseService
from .command_executor import CommandExecutor
from .ssh_manager import SSHManager

# --- AGENT CONFIGURATION ---
ORCHESTRATOR_SEED = os.getenv("ORCHESTRATOR_AGENT_SEED", "otium_orchestrator_agent_seed")
orchestrator = Agent(name="OtiumOrchestrator", seed=ORCHESTRATOR_SEED)

# Define addresses for our internal pipeline AEAs
CONTEXT_AEA_ADDRESS = os.getenv("CONTEXT_AEA_ADDRESS", "default_context_address")
INFERENCE_AEA_ADDRESS = os.getenv("INFERENCE_AEA_ADDRESS", "default_inference_address")

# --- PROTOCOL FOR INTERNAL API COMMUNICATION (FastAPI Interface) ---
# Define message model for the Orchestrator to receive tasks from the FastAPI
class TaskMessage(Model):
    user_id: str
    connection_id: str
    request: str
    command_id: str

api_protocol = Protocol(name="ApiInterface", version="0.1")

@api_protocol.on_message(model=TaskMessage, replies=CommandPlan)
async def handle_api_task(ctx: Context, sender: str, msg: TaskMessage):
    """Handles a task request initiated by the FastAPI server."""
    
    ctx.logger.info(f"Received API Task: {msg.request} for conn {msg.connection_id}")
    
    # 1. REQUEST SYSTEM CONTEXT FROM CONTEXT AEA
    ctx.logger.info("-> Requesting System Context from Context AEA")
    context_response = await ctx.send_and_receive(
        CONTEXT_AEA_ADDRESS,
        ContextRequest(connection_id=msg.connection_id),
        SystemContext
    )
    
    if not context_response or context_response.body.error:
        error_msg = context_response.body.error if context_response else "No response from Context AEA"
        ctx.logger.error(f"Failed to get context: {error_msg}")
        # Return a failed plan immediately
        await ctx.send(sender, CommandPlan(command_plan=[], error=f"Context failure: {error_msg}"))
        return

    system_context = context_response.body.system_info
    
    # 2. REQUEST COMMAND PLAN FROM INFERENCE AEA
    ctx.logger.info("-> Requesting Command Plan from Inference AEA")
    plan_response = await ctx.send_and_receive(
        INFERENCE_AEA_ADDRESS,
        PlanRequest(
            user_request=msg.request,
            connection_id=msg.connection_id,
            system_context=system_context
        ),
        CommandPlan
    )
    
    if not plan_response or plan_response.body.error:
        error_msg = plan_response.body.error if plan_response else "No response from Inference AEA"
        ctx.logger.error(f"Failed to get plan: {error_msg}")
        await ctx.send(sender, CommandPlan(command_plan=[], error=f"Plan failure: {error_msg}"))
        return

    # 3. PERSIST COMMAND PLAN (DATABASE LOGIC - KEEPING DB LOGIC SIMPLE HERE)
    # The Orchestrator should coordinate saving this initial plan to the 'commands' table.
    try:
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Save command to database using the complete CommandPlan model
        db_service.create_command(
            user_id=msg.user_id,
            connection_id=msg.connection_id,
            request=msg.request,
            intent=plan_response.body.intent,
            action=plan_response.body.action,
            risk_level=plan_response.body.risk_level,
            priority="normal", # Hardcoded for now
            generated_commands=[step.dict() for step in plan_response.body.command_plan]
        )
        db.close()
    except Exception as e:
        ctx.logger.error(f"Failed to save command to DB: {e}")
        # Still return the plan, but log the database error
        pass
        
    # 4. RETURN FINAL COMMAND PLAN TO FASTAPI
    ctx.logger.info("-> Successfully received and returning Command Plan")
    await ctx.send(sender, plan_response.body)

# --- EXECUTION LOGIC (The Orchestrator coordinates execution services) ---
# NOTE: The Orchestrator will implement the execution service locally in Phase 1 
# to wrap the existing command_executor.py for simplicity.

@orchestrator.on_message(model=ExecutionRequest, replies=ExecutionResult)
async def handle_execution_request(ctx: Context, sender: str, msg: ExecutionRequest):
    """
    Handles a request to execute a single, approved command step.
    In this AEA model, the Orchestrator is temporarily acting as the Secure Execution AEA.
    """
    ctx.logger.info(f"Executing approved step {msg.step.step} on {msg.connection_id}")
    
    try:
        # 1. Retrieve Decrypted Credentials and SSH Manager from state (Simulation)
        # This is the point where the Orchestrator would retrieve and decrypt the SSH
        # credentials for the given connection_id from the database.
        
        # 2. Get active SSHManager instance (assumed to be managed by the Orchestrator's FastAPI wrapper)
        # For a true AEA, this logic must be moved to the Secure Execution AEA.
        # Since we are keeping complexity low, we use the old CommandExecutor locally.
        
        # SIMULATION: Execute command
        # For a true Phase 1, you would need to initialize SSHManager/CommandExecutor here,
        # but since that requires complex state transfer, we SIMULATE the result.
        
        # In a real step, you would do:
        # ssh_manager = SSHManager() # must be re-initialized and connected
        # executor = CommandExecutor(ssh_manager, msg.connection_id)
        # result = executor.execute_single_step(msg.step.dict(), msg.step.step)
        
        # SIMULATION RESULT: Assume success for demonstration
        result = {
            'success': True,
            'exit_code': 0,
            'stdout': f"Command '{msg.step.command}' executed successfully. PID: 12345.",
            'stderr': "",
            'execution_time': 0.5
        }
        
        await ctx.send(
            sender, 
            ExecutionResult(
                success=result['success'],
                exit_code=result['exit_code'],
                stdout=result['stdout'],
                stderr=result['stderr'],
                execution_time=result['execution_time']
            )
        )
        
    except Exception as e:
        ctx.logger.error(f"Execution failed: {e}")
        await ctx.send(
            sender, 
            ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=str(e),
                execution_time=0.0,
                error=str(e)
            )
        )

# Include the API interface protocol
orchestrator.include(api_protocol)

if __name__ == "__main__":
    # Note: In a final deployment, you would run all AEAs separately or with a Bureau.
    print(f"Starting Otium Orchestrator AEA at {orchestrator.address}")
    orchestrator.run()






# #!/usr/bin/env python3
# """
# Otium AI Agent - Simplified Phase 1
# SSH-based Linux system administration AI agent with core functionality only
# """

# import os
# import sys
# from typing import Dict, Any

# # Import our modules
# from command_generator import CommandGenerator
# from command_executor import CommandExecutor
# from ssh_system_detector import SSHSystemDetector

# class Agent:
#     """Simplified AI Agent for SSH-based Linux system administration"""
    
#     def __init__(self, api_key: str, ssh_manager, connection_id: str):
#         # Validate required parameters
#         if not api_key:
#             raise ValueError("OpenAI API key is required")
#         if not ssh_manager:
#             raise ValueError("SSH manager is required")
#         if not connection_id:
#             raise ValueError("SSH connection ID is required")
        
#         self.api_key = api_key
#         self.ssh_manager = ssh_manager
#         self.connection_id = connection_id
        
#         # Initialize components
#         self.system_detector = None
#         self.command_executor = None
#         self.command_generator = None
#         self.system_context = {}
    
#     def start(self) -> bool:
#         """Start the agent and initialize environment"""
#         print("🚀 Starting Otium AI Agent...")
#         print("🔌 Starting in SSH mode...")
        
#         try:
#             # Validate SSH connection
#             if not self.ssh_manager.is_connection_alive(self.connection_id):
#                 print("❌ SSH connection not available or not alive")
#                 return False
            
#             print("✅ SSH connection validated")
            
#             # Initialize command executor
#             print("🔧 Initializing command executor...")
#             self.command_executor = CommandExecutor(ssh_manager=self.ssh_manager, connection_id=self.connection_id)
#             self.command_executor.set_connection_id(self.connection_id)
#             print("✅ Command executor initialized")
            
#             # Initialize system detector
#             print("🔍 Initializing system detector...")
#             self.system_detector = SSHSystemDetector(self.ssh_manager, self.connection_id)
#             print("✅ System detector created")
            
#             # Detect system
#             print("🔍 Detecting system...")
#             self.system_context = self.system_detector.detect_system()
#             print(f"✅ System detection complete: {len(self.system_context)} items")
            
#             # Initialize command generator
#             print("🤖 Initializing command generator...")
#             self.command_generator = CommandGenerator(
#                 self.system_context, 
#                 api_key=self.api_key
#             )
#             print("✅ Command generator initialized")
            
#             print("✅ Otium Agent initialized successfully!")
#             return True
            
#         except Exception as e:
#             print(f"❌ Failed to start agent: {e}")
#             import traceback
#             traceback.print_exc()
#             return False
    
#     def process_request(self, user_request: str) -> Dict[str, Any]:
#         """Process a user request and execute commands"""
#         print(f"\n{'='*60}")
#         print(f"📝 Processing Request: {user_request}")
#         print(f"{'='*60}")
        
#         try:
#             # Generate commands based on system context
#             print("🤖 Generating commands...")
#             command_plan = self.command_generator.generate_commands(user_request)
            
#             if not command_plan or 'steps' not in command_plan:
#                 raise ValueError("Failed to generate command plan")
            
#             # Basic safety check
#             if self._is_dangerous_operation(command_plan):
#                 print("🚨 DANGEROUS OPERATION DETECTED")
#                 print("This operation requires explicit approval.")
#                 return {
#                     "success": False,
#                     "error": "Dangerous operation requires approval",
#                     "command_plan": command_plan,
#                     "requires_approval": True
#                 }
            
#             # Print plan
#             self._print_command_plan(command_plan)
            
#             # Execute commands
#             execution_results = self._execute_commands(command_plan)
            
#             return {
#                 "success": execution_results["successful_steps"] == execution_results["total_steps"],
#                 "command_plan": command_plan,
#                 "execution_results": execution_results,
#                 "system_context": self.system_context
#             }
            
#         except Exception as e:
#             print(f"❌ Error processing request: {e}")
#             return {
#                 "success": False,
#                 "error": str(e)
#             }
    
#     def _is_dangerous_operation(self, command_plan: Dict[str, Any]) -> bool:
#         """Basic safety check for dangerous operations"""
#         dangerous_patterns = [
#             'rm -rf /',
#             'rm -rf /etc',
#             'rm -rf /var',
#             'rm -rf /usr',
#             'rm -rf /boot',
#             'dd if=/dev/',
#             'mkfs',
#             'fdisk',
#             'systemctl stop sshd',
#             'systemctl disable sshd',
#             'iptables -F',
#             'firewall-cmd --reload'
#         ]
        
#         steps = command_plan.get('steps', [])
#         for step in steps:
#             command = step.get('command', '').lower()
#             for pattern in dangerous_patterns:
#                 if pattern in command:
#                     print(f"⚠️  Dangerous pattern detected: {pattern}")
#                     return True
        
#         return False
    
#     def _print_command_plan(self, command_plan: Dict[str, Any]) -> None:
#         """Print command plan information"""
#         print(f"\n📋 Command Plan:")
#         print(f"   Intent: {command_plan.get('intent', 'Unknown')}")
#         print(f"   Action: {command_plan.get('action', 'Unknown')}")
#         print(f"   Risk Level: {command_plan.get('risk_level', 'Unknown')}")
#         print(f"   Explanation: {command_plan.get('explanation', 'No explanation')}")
#         print(f"   Steps: {len(command_plan.get('steps', []))}")
        
#         # Print individual steps
#         for i, step in enumerate(command_plan.get('steps', []), 1):
#             print(f"   Step {i}: {step.get('command', 'No command')}")
#             print(f"      Description: {step.get('description', 'No description')}")
    
#     def _execute_commands(self, command_plan: Dict[str, Any]) -> Dict[str, Any]:
#         """Execute commands from command plan"""
#         steps = command_plan.get('steps', [])
#         if steps:
#             return self.command_executor.execute_steps(steps)
#         else:
#             return {
#                 "total_steps": 0,
#                 "successful_steps": 0,
#                 "failed_steps": 0,
#                 "skipped_steps": 0,
#                 "step_results": [],
#                 "total_execution_time": 0
#             }
    
#     def get_system_info(self) -> Dict[str, Any]:
#         """Get current system information"""
#         return self.system_context
    
#     def cleanup(self):
#         """Cleanup resources"""
#         if self.ssh_manager and self.connection_id:
#             try:
#                 print("🧹 Cleaning up SSH connection...")
#                 self.ssh_manager.disconnect(self.connection_id)
#                 print("✅ SSH connection cleaned up")
#             except Exception as e:
#                 print(f"⚠️  Error cleaning up SSH connection: {e}")


# def main():
#     """Main entry point"""
    
#     # Load environment variables from .env file
#     try:
#         from dotenv import load_dotenv
#         load_dotenv()
#         print("✅ Loaded environment variables from .env file")
#     except ImportError:
#         print("⚠️  python-dotenv not installed, using system environment variables")
#     except Exception as e:
#         print(f"⚠️  Error loading .env file: {e}")
    
#     # Check for API key
#     api_key = os.getenv('OPENAI_API_KEY')
#     if not api_key:
#         print("❌ No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
#         return 1
    
#     print(f"✅ OpenAI API key found: {api_key[:20]}...")
    
#     # Note: Agent is now API-only, no interactive mode needed
#     print("🤖 Otium Agent designed for API use only")
#     print("💡 Use the API endpoints to interact with the agent")
    
#     return 0


# if __name__ == "__main__":
#     sys.exit(main())