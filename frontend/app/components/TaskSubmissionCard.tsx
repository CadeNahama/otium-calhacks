"use client";

import { useState } from 'react';
import { API_CONFIG, apiCall } from '@/app/config/api';
import { useConnection } from '@/app/contexts/ConnectionContext';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Send, CheckCircle, XCircle, Clock, Zap } from 'lucide-react';
import { CodeBlock } from './CodeBlock';
import { useToast } from '../hooks/useToast';

interface GeneratedCommand {
  step: number;
  command: string;
  explanation: string;
  risk_level: string;
  estimated_time: string;
}

interface CommandResponse {
  command_id: string;
  status: string;
  generated_commands: GeneratedCommand[];
  intent: string;
  action: string;
  risk_level: string;
  explanation: string;
  risk_assessment: string | null;
  created_at: string;
  approval_required: boolean;
}

interface TaskSubmissionCardProps {
  userId: string;
  onCommandStatusChange?: () => void;
}

export function TaskSubmissionCard({ userId, onCommandStatusChange }: TaskSubmissionCardProps) {
  const { activeConnection } = useConnection();
  const { success: showSuccess, error: showError } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [generatedCommand, setGeneratedCommand] = useState<CommandResponse | null>(null);
  
  const [formData, setFormData] = useState({
    taskRequest: ''
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setGeneratedCommand(null);
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
        priority: 'normal', // Keep default priority for API
      };
      
      const data = await apiCall<CommandResponse>(API_CONFIG.ENDPOINTS.COMMANDS.SUBMIT, {
        method: 'POST',
        body: JSON.stringify(requestBody),
      }, userId);

      setGeneratedCommand(data);
      showSuccess('Task submitted successfully! AI has generated commands for your review.');
      setFormData({ taskRequest: '' });
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Failed to submit task');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApprove = async () => {
    if (!generatedCommand) return;

    setIsApproving(true);
    try {
      await apiCall(API_CONFIG.ENDPOINTS.COMMANDS.APPROVE(generatedCommand.command_id), {
        method: 'POST',
      }, userId);

      showSuccess('Commands approved and executed successfully!');
      setGeneratedCommand(null);
      
      // Refresh command list
      onCommandStatusChange?.();
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Failed to approve commands');
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async () => {
    if (!generatedCommand) return;

    setIsRejecting(true);
    try {
      await apiCall(API_CONFIG.ENDPOINTS.COMMANDS.REJECT(generatedCommand.command_id), {
        method: 'POST',
      }, userId);

      showSuccess('Commands rejected successfully.');
      setGeneratedCommand(null);
      
      // Refresh command list
      onCommandStatusChange?.();
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Failed to reject commands');
    } finally {
      setIsRejecting(false);
    }
  };

  return (
    <Card className="h-fit border border-border/20 shadow-sm bg-card">
      <CardHeader className="pb-8 pt-8 px-8">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="leading-tight">Task Submission</h3>
            <p className="text-body-small text-muted-foreground mt-1 leading-relaxed">Natural language task submission</p>
          </div>
          
          {activeConnection && (
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              <span className="text-body-small text-muted-foreground font-medium">Connected to {activeConnection.hostname}</span>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-8 px-8 pb-8">
        {!activeConnection && (
          <div className="p-8 bg-muted/30 border border-border/30 rounded-2xl text-center">
            <div className="text-3xl mb-4">🔌</div>
            <p className="text-body-small text-muted-foreground font-medium">Connect to a server to submit tasks</p>
          </div>
        )}

        {activeConnection && (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-3">
              <Label htmlFor="taskRequest" className="text-body-small font-medium text-foreground">Task Description</Label>
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
                <p className="text-body-small text-muted-foreground/80">Enter a task description to enable submission</p>
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
            <div className="p-6 bg-muted/20 rounded-2xl border border-border/30">
              <div className="flex items-center justify-between mb-5">
                <h4 className="leading-tight">AI-Generated Commands</h4>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-muted/30 rounded-xl border border-border/20">
                    <p className="text-body-small text-muted-foreground mb-2 font-medium uppercase tracking-wide">Intent</p>
                    <p className="text-body-regular font-medium text-foreground truncate" title={generatedCommand.intent}>{generatedCommand.intent}</p>
                  </div>
                  
                  <div className="p-4 bg-muted/30 rounded-xl border border-border/20">
                    <p className="text-body-small text-muted-foreground mb-2 font-medium uppercase tracking-wide">Action</p>
                    <p className="text-body-regular font-medium text-foreground truncate" title={generatedCommand.action}>{generatedCommand.action}</p>
                  </div>
                </div>
                
                {generatedCommand.risk_assessment && (
                  <div className="p-4 bg-muted/30 rounded-xl border border-border/20">
                    <p className="text-body-small text-muted-foreground mb-2 font-medium uppercase tracking-wide">Risk Assessment</p>
                    <p className="text-body-regular font-medium text-foreground">{generatedCommand.risk_assessment}</p>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="leading-tight flex items-center gap-2 text-foreground">
                <Zap className="w-4 h-4 text-primary" />
                Generated Commands
              </h4>
              {generatedCommand.generated_commands.map((cmd, index) => (
                <div key={index} className="p-5 bg-muted/20 border border-border/20 rounded-xl space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-body-small font-semibold text-muted-foreground">Step {cmd.step}</span>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="gap-1 text-body-small px-2 py-1 border-border/30">
                        <Clock className="w-3 h-3" />
                        {cmd.estimated_time}
                      </Badge>
                    </div>
                  </div>
                  
                  <CodeBlock command={cmd.command} language="bash" />
                  
                  <p className="text-body-regular text-muted-foreground leading-relaxed">{cmd.explanation}</p>
                </div>
              ))}
            </div>

            <div className="flex gap-3 pt-4">
              <Button 
                onClick={handleApprove}
                disabled={isApproving || isRejecting}
                className="flex-1 h-12 bg-primary hover:bg-primary/90 !text-black font-medium text-body-regular rounded-xl shadow-sm transition-all duration-200"
              >
                {isApproving ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    <span>Approving...</span>
                  </div>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Approve & Execute
                  </>
                )}
              </Button>
              <Button 
                onClick={handleReject}
                disabled={isApproving || isRejecting}
                variant="outline" 
                className="flex-1 h-12 border-border/30 text-foreground hover:bg-muted/30 hover:text-foreground font-medium rounded-xl transition-all duration-200"
              >
                {isRejecting ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    <span>Rejecting...</span>
                  </div>
                ) : (
                  <>
                    <XCircle className="w-4 h-4 mr-2" />
                    Reject
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}