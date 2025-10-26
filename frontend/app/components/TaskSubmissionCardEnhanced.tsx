"use client";

import { useState, useEffect, useCallback } from 'react';
import { API_CONFIG, apiCall } from '@/app/config/api';
import { useConnection } from '@/app/contexts/ConnectionContext';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Send, CheckCircle, XCircle, Clock, Zap, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { CodeBlock } from './CodeBlock';
import { useToast } from '../hooks/useToast';

interface GeneratedCommand {
  step: number;
  command: string;
  explanation: string;
  risk_level: string;
  estimated_time: string;
  status?: string;
  approved_by?: string;
  approved_at?: string;
  reason?: string;
}


interface CommandResponse {
  command_id: string;
  status: string;
  generated_commands: GeneratedCommand[];
  intent: string;
  action: string;
  risk_level: string;
  explanation: string;
  created_at: string;
  approval_required: boolean;
  approval_status?: {
    command_id: string;
    total_steps: number;
    approved_steps: number;
    rejected_steps: number;
    pending_steps: number;
    can_execute: boolean;
    steps: Array<{
      step_index: number;
      command: string;
      explanation: string;
      risk_level: string;
      estimated_time: string;
      status: string;
      approved: boolean | null;
      approved_by: string | null;
      reason: string | null;
      approved_at: string | null;
    }>;
  };
}

interface TaskSubmissionCardProps {
  userId: string;
  onCommandStatusChange?: () => void;
}

export function TaskSubmissionCardEnhanced({ userId, onCommandStatusChange }: TaskSubmissionCardProps) {
  const { activeConnection } = useConnection();
  const { success: showSuccess, error: showError } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generatedCommand, setGeneratedCommand] = useState<CommandResponse | null>(null);
  const [approvalStatus, setApprovalStatus] = useState<CommandResponse['approval_status'] | null>(null);
  const [showRejectedSteps, setShowRejectedSteps] = useState(false);
  const [rejectionReasons, setRejectionReasons] = useState<{[key: number]: string}>({});
  const [executionResults, setExecutionResults] = useState<{[key: number]: any}>({});
  
  const [formData, setFormData] = useState({
    taskRequest: ''
  });

  const fetchApprovalStatus = useCallback(async () => {
    if (!generatedCommand?.command_id) return;

    try {
      const status = await apiCall<CommandResponse['approval_status']>(
        `${API_CONFIG.ENDPOINTS.COMMANDS.BASE}/${generatedCommand.command_id}/approval-status`,
        { method: 'GET' },
        userId
      );
      setApprovalStatus(status);
    } catch (error) {
      console.error('Failed to fetch approval status:', error);
    }
  }, [generatedCommand?.command_id, userId]);

  // Fetch approval status when command is generated
  useEffect(() => {
    if (generatedCommand?.command_id && generatedCommand.approval_required) {
      fetchApprovalStatus();
    }
  }, [generatedCommand, fetchApprovalStatus]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setGeneratedCommand(null);
    setApprovalStatus(null);
    setExecutionResults({});
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!activeConnection) {
      showError('No active SSH connection. Please connect to a server first.');
      return;
    }

    if (!activeConnection.connection_id) {
      showError('Connection ID is missing. Please reconnect to the server.');
      return;
    }

    if (!formData.taskRequest.trim()) {
      showError('Please enter a task description.');
      return;
    }

    setIsSubmitting(true);

    try {
      const requestBody = {
        connection_id: activeConnection.connection_id,
        request: formData.taskRequest.trim(),
        priority: 'normal',
      };
      
      const data = await apiCall<CommandResponse>(API_CONFIG.ENDPOINTS.COMMANDS.SUBMIT, {
        method: 'POST',
        body: JSON.stringify(requestBody),
      }, userId);

      console.log('[TaskSubmissionCard] Task submission response:', data);
      console.log('[TaskSubmissionCard] approval_required:', data.approval_required);
      console.log('[TaskSubmissionCard] generated_commands:', data.generated_commands);
      
      setGeneratedCommand(data);
      
      if (data.approval_required) {
        showSuccess('Task submitted! Please review and approve each command step individually.');
      } else {
        showSuccess('Task submitted and auto-approved! Commands are ready to execute.');
      }
      
      setFormData({ taskRequest: '' });
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Failed to submit task');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStepApproval = async (stepIndex: number, approved: boolean, reason?: string) => {
    console.log('[TaskSubmissionCard] handleStepApproval called:', { stepIndex, approved, reason, commandId: generatedCommand?.command_id });
    
    if (!generatedCommand?.command_id) {
      console.error('[TaskSubmissionCard] No command_id found for approval');
      return;
    }

    try {
      console.log('[TaskSubmissionCard] Making API call to approve-step...');
      const response = await apiCall<{ 
        success: boolean; 
        message: string; 
        approval_status?: CommandResponse['approval_status'];
        execution_result?: {
          success: boolean;
          error?: string;
          output?: string;
        };
        all_responded?: boolean;
      }>(
        `${API_CONFIG.ENDPOINTS.COMMANDS.BASE}/${generatedCommand.command_id}/approve-step`,
        {
          method: 'POST',
          body: JSON.stringify({
            step_index: stepIndex,
            approved,
            reason
          }),
        },
        userId
      );

      console.log('[TaskSubmissionCard] API response received:', response);

      if (response.approval_status) {
        console.log('[TaskSubmissionCard] Updating approval status:', response.approval_status);
        setApprovalStatus(response.approval_status);
      }
      
      // Store execution result
      if (response.execution_result) {
        setExecutionResults(prev => ({
          ...prev,
          [stepIndex]: response.execution_result
        }));
      }
      
      if (approved) {
        if (response.execution_result?.success) {
          showSuccess(`Step ${stepIndex + 1} approved and executed successfully!`);
        } else if (response.execution_result) {
          showError(`Step ${stepIndex + 1} approved but execution failed: ${response.execution_result.error || 'Unknown error'}`);
        } else {
          showSuccess(`Step ${stepIndex + 1} approved!`);
        }
      } else {
        showSuccess(`Step ${stepIndex + 1} rejected.`);
      }

      // Clear rejection reason after submitting
      setRejectionReasons(prev => {
        const newReasons = {...prev};
        delete newReasons[stepIndex];
        return newReasons;
      });

      // If all steps have been responded to, clear the task from UI and refresh command history
      if (response.all_responded) {
        console.log('[TaskSubmissionCard] All steps responded - clearing task from UI');
        console.log('[TaskSubmissionCard] all_responded value:', response.all_responded);
        
        // Show success message first
        showSuccess('All steps processed! Task will move to command history.');
        
        // Clear the task and refresh command history
        setTimeout(() => {
          console.log('[TaskSubmissionCard] Clearing task now...');
          setGeneratedCommand(null);
          setApprovalStatus(null);
          setFormData({ taskRequest: '' });
          onCommandStatusChange?.();
        }, 2000); // 2 second delay so user can see the final status
      } else {
        // Just refresh the command list for partial updates
        console.log('[TaskSubmissionCard] Not all responded yet, refreshing...');
        onCommandStatusChange?.();
      }
    } catch (error) {
      console.error('[TaskSubmissionCard] Error in handleStepApproval:', error);
      showError(error instanceof Error ? error.message : `Failed to ${approved ? 'approve' : 'reject'} step`);
    }
  };


  const getStepStatus = (stepIndex: number) => {
    if (!approvalStatus?.steps) {
      console.log(`[getStepStatus] No approval status, returning 'pending' for step ${stepIndex}`);
      return 'pending';
    }
    const step = approvalStatus.steps.find((s) => s.step_index === stepIndex);
    const status = step?.status || 'pending';
    console.log(`[getStepStatus] Step ${stepIndex} status:`, status, 'approvalStatus:', approvalStatus);
    return status;
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'low': return 'bg-green-500/20 text-green-600 border-green-500/30';
      case 'medium': return 'bg-yellow-500/20 text-yellow-600 border-yellow-500/30';
      case 'high': return 'bg-orange-500/20 text-orange-600 border-orange-500/30';
      case 'critical': return 'bg-red-500/20 text-red-600 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-600 border-gray-500/30';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'rejected': return <XCircle className="w-4 h-4 text-red-600" />;
      case 'pending': return <Clock className="w-4 h-4 text-yellow-600" />;
      default: return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  const hasRejectedSteps = approvalStatus?.rejected_steps ? approvalStatus.rejected_steps > 0 : false;
  
  // Sequential approval logic - find first pending step
  const getFirstPendingStepIndex = () => {
    if (!generatedCommand?.generated_commands) return -1;
    // If no approval status yet, Step 0 is first pending
    if (!approvalStatus?.steps) return 0;
    return generatedCommand.generated_commands.findIndex((_, index) => getStepStatus(index) === 'pending');
  };
  
  const firstPendingStepIndex = getFirstPendingStepIndex();
  const hasPendingSteps = firstPendingStepIndex >= 0;
  
  // Approve All functionality
  const handleApproveAll = async () => {
    if (!generatedCommand?.command_id || !hasPendingSteps) return;
    
    try {
      // Get all pending step indices
      const pendingSteps = generatedCommand.generated_commands
        .map((_, index) => ({ index, status: getStepStatus(index) }))
        .filter(step => step.status === 'pending')
        .map(step => step.index);
      
      // Approve each step sequentially (each will execute immediately)
      for (const stepIndex of pendingSteps) {
        await handleStepApproval(stepIndex, true);
        // Small delay to ensure proper sequencing
        await new Promise(resolve => setTimeout(resolve, 200));
      }
      
      showSuccess(`Approved and executed all ${pendingSteps.length} steps!`);
    } catch {
      showError('Failed to approve all steps');
    }
  };

  // Reject All functionality
  const handleRejectAll = async () => {
    if (!generatedCommand?.command_id || !hasPendingSteps) return;
    
    try {
      // Get all pending step indices
      const pendingSteps = generatedCommand.generated_commands
        .map((_, index) => ({ index, status: getStepStatus(index) }))
        .filter(step => step.status === 'pending')
        .map(step => step.index);
      
      // Reject each step sequentially
      for (const stepIndex of pendingSteps) {
        await handleStepApproval(stepIndex, false);
        // Small delay to ensure proper sequencing
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      showSuccess(`Rejected all ${pendingSteps.length} steps!`);
    } catch {
      showError('Failed to reject all steps');
    }
  };

  return (
    <Card className="h-full border border-border/20 shadow-sm bg-card flex flex-col">
      <CardHeader className="pb-8 pt-8 px-8">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="leading-tight">Task Submission</h3>
            <p className="text-body-small text-muted-foreground mt-1 leading-relaxed">
              Natural language task submission with step-by-step approval
            </p>
          </div>
          
          {activeConnection && (
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              <span className="text-body-small text-muted-foreground font-medium">
                Connected to {activeConnection.hostname}
              </span>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-8 px-8 pb-8 flex-1 flex flex-col">
        {!activeConnection && (
          <div className="p-8 bg-muted/30 border border-border/30 rounded-2xl text-center">
            <div className="text-3xl mb-4">🔌</div>
            <p className="text-body-small text-muted-foreground font-medium">Connect to a server to submit tasks</p>
          </div>
        )}

        {activeConnection && (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-3">
              <Label htmlFor="taskRequest" className="text-body-small font-medium text-foreground">
                Task Description
              </Label>
              <Textarea 
                id="taskRequest"
                name="taskRequest"
                value={formData.taskRequest}
                onChange={handleInputChange}
                placeholder="e.g., Check system memory usage and disk space, or Install and start nginx web server"
                rows={3}
                required
                className="resize-none border-border/30 bg-input text-foreground placeholder:text-muted-foreground/60 focus:border-primary/50 focus:ring-primary/20 text-body-regular"
              />
              {!formData.taskRequest.trim() && (
                <p className="text-body-small text-muted-foreground/80">
                  Enter a task description to enable submission
                </p>
              )}
            </div>

            <Button 
              type="submit"
              disabled={isSubmitting || !formData.taskRequest.trim()}
              className="w-full h-11 bg-primary hover:bg-primary/90 text-primary-foreground font-medium shadow-sm rounded-xl transition-all duration-200"
            >
              {isSubmitting ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  <span className="text-body-regular">Generating Commands...</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Send className="w-4 h-4" />
                  <span className="text-body-regular">Submit Task</span>
                </div>
              )}
            </Button>
          </form>
        )}

        {generatedCommand && (
          <div className="space-y-6">
            {/* Command Overview */}
            <div className="p-6 bg-muted/20 rounded-2xl border border-border/30">
              <div className="flex items-center justify-between mb-5">
                <h4 className="leading-tight">AI-Generated Commands</h4>
                <Badge variant="outline" className={getRiskLevelColor(generatedCommand.risk_level)}>
                  {generatedCommand.risk_level} Risk
                </Badge>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-muted/30 rounded-xl border border-border/20">
                    <p className="text-body-small text-muted-foreground mb-2 font-medium uppercase tracking-wide">Intent</p>
                    <p className="text-body-regular font-medium text-foreground truncate" title={generatedCommand.intent}>
                      {generatedCommand.intent}
                    </p>
                  </div>
                  
                  <div className="p-4 bg-muted/30 rounded-xl border border-border/20">
                    <p className="text-body-small text-muted-foreground mb-2 font-medium uppercase tracking-wide">Action</p>
                    <p className="text-body-regular font-medium text-foreground truncate" title={generatedCommand.action}>
                      {generatedCommand.action}
                    </p>
                  </div>
                </div>

                {generatedCommand.approval_required && approvalStatus && (
                  <div className="p-4 bg-muted/30 rounded-xl border border-border/20">
                    <p className="text-body-small text-muted-foreground mb-3 font-medium uppercase tracking-wide">
                      Approval Status
                    </p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="text-center">
                        <div className="text-lg font-bold text-foreground">{approvalStatus?.total_steps || 0}</div>
                        <div className="text-xs text-muted-foreground">Total Steps</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-green-600">{approvalStatus?.approved_steps || 0}</div>
                        <div className="text-xs text-muted-foreground">Approved</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-red-600">{approvalStatus?.rejected_steps || 0}</div>
                        <div className="text-xs text-muted-foreground">Rejected</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-yellow-600">{approvalStatus?.pending_steps || 0}</div>
                        <div className="text-xs text-muted-foreground">Pending</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Step-by-Step Commands */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="leading-tight flex items-center gap-2 text-foreground">
                  <Zap className="w-4 h-4 text-primary" />
                  Command Steps
                  {generatedCommand.approval_required && (
                    <Badge variant="outline" className="ml-2">
                      Step-by-Step Approval Required
                    </Badge>
                  )}
                </h4>
                
                {hasRejectedSteps && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowRejectedSteps(!showRejectedSteps)}
                    className="flex items-center gap-2"
                  >
                    {showRejectedSteps ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    {showRejectedSteps ? 'Hide' : 'Show'} Rejected
                  </Button>
                )}
              </div>

              {generatedCommand.generated_commands.map((cmd, index) => {
                const stepStatus = getStepStatus(index);
                const isRejected = stepStatus === 'rejected';
                const isApproved = stepStatus === 'approved';
                const isPending = stepStatus === 'pending';
                const isCurrentStep = index === firstPendingStepIndex; // First pending step gets highlighted
                
                console.log(`[TaskSubmissionCard] Step ${index}:`, { 
                  stepStatus, 
                  isPending, 
                  isCurrentStep, 
                  approvalRequired: generatedCommand.approval_required 
                });

                // Hide rejected steps if toggle is off
                if (isRejected && !showRejectedSteps) return null;

                return (
                  <div 
                    key={index} 
                    className={`p-5 border rounded-xl space-y-4 ${
                      isApproved ? 'bg-green-50/50 border-green-200' :
                      isRejected ? 'bg-red-50/50 border-red-200' :
                      isCurrentStep ? 'bg-blue-50/50 border-blue-200 ring-2 ring-blue-100' : // Highlight current step
                      'bg-muted/20 border-border/20'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className={`text-body-small font-semibold ${
                          isCurrentStep ? 'text-blue-600' : 'text-muted-foreground'
                        }`}>
                          Step {cmd.step}
                          {isCurrentStep && <span className="ml-1 text-xs">(Current)</span>}
                        </span>
                        {getStatusIcon(stepStatus)}
                        <Badge variant="outline" className={`text-xs ${getRiskLevelColor(cmd.risk_level)}`}>
                          {cmd.risk_level} Risk
                        </Badge>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="gap-1 text-body-small px-2 py-1 border-border/30">
                          <Clock className="w-3 h-3" />
                          {cmd.estimated_time}
                        </Badge>
                      </div>
                    </div>
                    
                    <CodeBlock command={cmd.command} language="bash" />
                    
                    <p className="text-body-regular text-muted-foreground leading-relaxed">
                      {cmd.explanation}
                    </p>

                    {/* Step Approval/Rejection Buttons - Only show for pending steps */}
                    {generatedCommand.approval_required && isPending && (
                      <div className="space-y-3 pt-2">
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => handleStepApproval(index, true)}
                            className="bg-green-600 hover:bg-green-700 text-white"
                          >
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Approve & Execute
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleStepApproval(index, false, rejectionReasons[index] || '')}
                            variant="outline"
                            className="border-red-300 text-red-600 hover:bg-red-50"
                          >
                            <XCircle className="w-3 h-3 mr-1" />
                            Reject
                          </Button>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor={`rejection-reason-${index}`} className="text-xs text-muted-foreground">
                            Rejection reason (optional):
                          </Label>
                          <Textarea
                            id={`rejection-reason-${index}`}
                            value={rejectionReasons[index] || ''}
                            onChange={(e) => setRejectionReasons(prev => ({...prev, [index]: e.target.value}))}
                            placeholder="Enter reason for rejection..."
                            rows={2}
                            className="text-xs resize-none"
                          />
                        </div>
                      </div>
                    )}

                    {/* Step Status */}
                    {generatedCommand.approval_required && !isPending && (
                      <div className={`p-3 rounded-lg text-sm ${
                        isApproved ? 'bg-green-100 text-green-800' :
                        isRejected ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(stepStatus)}
                          <span className="font-medium">
                            Step {isApproved ? 'approved' : 'rejected'}
                          </span>
                          {cmd.reason && (
                            <span className="text-xs opacity-75">- {cmd.reason}</span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Execution Results */}
                    {executionResults[index] && (
                      <div className="mt-3 p-4 bg-gray-900 rounded-lg border border-gray-700">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold text-gray-300">Execution Output</span>
                          <div className="flex items-center gap-3 text-xs">
                            <span className={`font-medium ${
                              executionResults[index].success ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {executionResults[index].success ? '✓ Success' : '✗ Failed'}
                            </span>
                            {executionResults[index].exit_code !== undefined && (
                              <span className="text-gray-400">
                                Exit Code: {executionResults[index].exit_code}
                              </span>
                            )}
                            {executionResults[index].execution_time && (
                              <span className="text-gray-400">
                                {executionResults[index].execution_time.toFixed(3)}s
                              </span>
                            )}
                          </div>
                        </div>
                        {executionResults[index].output && (
                          <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap overflow-x-auto max-h-48 overflow-y-auto">
                            {executionResults[index].output}
                          </pre>
                        )}
                        {executionResults[index].stderr && (
                          <div className="mt-2">
                            <span className="text-xs font-semibold text-red-400">Error Output:</span>
                            <pre className="text-xs text-red-300 font-mono whitespace-pre-wrap overflow-x-auto mt-1">
                              {executionResults[index].stderr}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Bulk Action Buttons */}
            {generatedCommand.approval_required && hasPendingSteps && (
              <div className="pt-4 border-t space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <Button 
                    onClick={handleApproveAll}
                    variant="outline"
                    className="h-11 border-green-200 text-green-700 hover:bg-green-50 font-medium text-body-regular rounded-xl shadow-sm transition-all duration-200"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Approve & Execute All
                  </Button>
                  <Button 
                    onClick={handleRejectAll}
                    variant="outline"
                    className="h-11 border-red-200 text-red-700 hover:bg-red-50 font-medium text-body-regular rounded-xl shadow-sm transition-all duration-200"
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Reject All
                  </Button>
                </div>
                <p className="text-center text-sm text-muted-foreground">
                  {(approvalStatus?.pending_steps || 0)} steps pending • Each approved step executes immediately
                </p>
              </div>
            )}

            {/* Status Messages */}
            {generatedCommand.approval_required && (
              <div className="p-4 rounded-xl border bg-muted/20">
                {(approvalStatus?.pending_steps && approvalStatus.pending_steps > 0) && (
                  <div className="flex items-center gap-2 text-yellow-600">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="text-sm">
                      {approvalStatus.pending_steps} step(s) pending • Each approved step executes immediately
                    </span>
                  </div>
                )}
                
                {hasRejectedSteps && (
                  <div className="flex items-center gap-2 text-red-600 mt-2">
                    <XCircle className="w-4 h-4" />
                    <span className="text-sm">
                      {approvalStatus?.rejected_steps || 0} step(s) rejected (not executed)
                    </span>
                  </div>
                )}
                
                {approvalStatus?.approved_steps && approvalStatus.approved_steps > 0 && (
                  <div className="flex items-center gap-2 text-green-600 mt-2">
                    <CheckCircle className="w-4 h-4" />
                    <span className="text-sm">
                      {approvalStatus.approved_steps} step(s) approved and executed
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
