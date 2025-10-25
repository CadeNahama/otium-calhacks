"use client";

import { useState, useEffect, useCallback } from 'react';
import { API_CONFIG, apiCall } from '@/app/config/api';
import { useConnection } from '@/app/contexts/ConnectionContext';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, Clock, Hourglass, ChevronRight, X } from 'lucide-react';
import { CodeBlock } from './CodeBlock';
import { useToast } from '../hooks/useToast';

interface GeneratedCommand {
  step: number;
  command: string;
  explanation: string;
  risk_level: string;
  estimated_time: string;
}

interface Command {
  id: string;
  connection_id: string;
  request: string;
  priority: string;
  status: string;
  intent: string;
  action: string;
  risk_level: string;
  explanation: string;
  created_at: string;
  approved_at: string | null;
  executed_at: string | null;
  completed_at: string | null;
  generated_commands?: GeneratedCommand[];
  execution_results?: ExecutionResult;
}

interface ExecutionResult {
  success: boolean;
  total_steps: number;
  successful_steps: number;
  failed_steps: number;
  skipped_steps: number;
  step_results: Array<{
    step: number;
    command: string;
    status: string;
    reason?: string;
    execution_time: number;
    output?: string;
    stdout?: string;
    exit_code?: number;
  }>;
  total_execution_time: number;
}

interface CommandPreviewCardProps {
  userId: string;
  refreshTrigger?: number; // Add refresh trigger prop
}

export function CommandPreviewCard({ userId, refreshTrigger }: CommandPreviewCardProps) {
  const { activeConnection } = useConnection();
  const { error: showError } = useToast();
  const [isLoading] = useState(false);
  const [commands, setCommands] = useState<Command[]>([]);
  const [selectedCommand, setSelectedCommand] = useState<Command | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  const fetchCommands = useCallback(async (connectionId?: string) => {
    console.log('[CommandPreviewCard] fetchCommands called with connectionId:', connectionId);
    
    try {
      // Show commands from all connections for this user (not filtered by connection_id)
      const url = `${API_CONFIG.ENDPOINTS.COMMANDS.LIST}?limit=10`;
      console.log('[CommandPreviewCard] Making API call to:', url);
      console.log('[CommandPreviewCard] NOTE: Fetching ALL commands for user (not filtered by connection)');
      
      const data = await apiCall<{ commands: Command[] }>(url, { method: 'GET' }, userId);
      console.log('[CommandPreviewCard] API response:', data);
      
      setCommands(data.commands || []);
      console.log('[CommandPreviewCard] Commands set:', data.commands || []);
    } catch (error) {
      console.error('[CommandPreviewCard] Failed to fetch commands:', error);
      showError('Failed to fetch command history');
    }
  }, [userId, showError]);

  useEffect(() => {
    console.log('[CommandPreviewCard] useEffect triggered:', { activeConnection });
    // Always fetch commands for this user (show command history from all connections)
    console.log('[CommandPreviewCard] Fetching all commands for user');
    fetchCommands(activeConnection?.connection_id);
  }, [activeConnection, fetchCommands]);

  // Add effect to refresh when refreshTrigger changes
  useEffect(() => {
    if (refreshTrigger && refreshTrigger > 0) {
      console.log('[CommandPreviewCard] Refresh trigger activated:', refreshTrigger);
      fetchCommands(activeConnection?.connection_id);
    }
  }, [refreshTrigger, fetchCommands, activeConnection]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending_approval': return <Hourglass className="w-3 h-3" />;
      case 'approved': return <CheckCircle className="w-3 h-3" />;
      case 'completed': return <CheckCircle className="w-3 h-3" />;
      case 'rejected': return <XCircle className="w-3 h-3" />;
      default: return <Clock className="w-3 h-3" />;
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'pending_approval': return 'destructive';
      case 'approved': return 'default';
      case 'completed': return 'secondary';
      case 'rejected': return 'destructive';
      default: return 'secondary';
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending_approval': return 'text-amber-300';
      case 'approved': return 'text-blue-300';
      case 'completed': return 'text-emerald-300';
      case 'rejected': return 'text-red-300';
      default: return 'text-muted-foreground';
    }
  };

  const openDetailsModal = (command: Command) => {
    setSelectedCommand(command);
    setShowDetailsModal(true);
  };

  const closeDetailsModal = () => {
    setShowDetailsModal(false);
    setSelectedCommand(null);
  };

  return (
    <Card className="h-fit border border-border/20 shadow-sm bg-card">
      <CardHeader className="pb-8 pt-8 px-8">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="leading-tight">Command History</h3>
            <p className="text-body-small text-muted-foreground mt-1 leading-relaxed">Track execution status</p>
          </div>
          
          {activeConnection && commands.length > 0 && (
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              <span className="text-body-small text-muted-foreground font-medium">{commands.length} commands</span>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-8 px-8 pb-8">
        {!activeConnection && (
          <div className="p-8 bg-muted/30 border border-border/30 rounded-2xl text-center">
            <div className="text-3xl mb-4">🔌</div>
            <p className="text-body-small text-muted-foreground font-medium">Connect to a server to view command history</p>
          </div>
        )}

        {activeConnection && commands.length > 0 && (
          <div className="space-y-4 overflow-y-auto max-h-[230px] pr-2 scrollbar-thin scrollbar-thumb-muted-foreground/20 scrollbar-track-transparent hover:scrollbar-thumb-muted-foreground/40">
            {commands.map((command) => (
              <Card 
                key={command.id}
                className="hover:bg-muted/20 transition-all cursor-pointer border-l-4 border-l-transparent border border-border/20 shadow-sm bg-card"
                onClick={() => openDetailsModal(command)}
              >
                <CardContent className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-body-regular font-semibold line-clamp-2 mb-3 leading-relaxed text-foreground">{command.request}</p>
                      <div className="flex items-center gap-3 text-body-small text-muted-foreground">
                        <span className="flex-shrink-0">{formatDate(command.created_at)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-3">
                      <Badge variant={getStatusVariant(command.status)} className="gap-1 font-medium text-body-small px-2 py-1">
                        {getStatusIcon(command.status)}
                        {command.status.replace('_', ' ')}
                      </Badge>
                    </div>
                  </div>



                  <div className="flex items-center justify-center mt-3">
                    <div className={`text-body-small font-medium ${getStatusColor(command.status)} flex items-center gap-1 cursor-pointer hover:text-primary transition-colors`}>
                      <ChevronRight className="w-3 h-3" />
                      View details
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {activeConnection && commands.length === 0 && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📋</div>
            <p className="text-body-regular text-muted-foreground font-medium mb-2">No commands yet</p>
            <p className="text-body-small text-muted-foreground">Submit a task to see AI-generated commands here</p>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Command Details Modal */}
        {showDetailsModal && selectedCommand && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div className="bg-card border border-border/20 rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden">
          {/* Modal Header */}
          <div className="flex items-center justify-between p-6 border-b border-border/20 bg-muted/10">
            <div>
              <h2 className="text-xl font-semibold text-foreground">Command Details</h2>
              <p className="text-sm text-muted-foreground mt-1">{selectedCommand.request}</p>
            </div>
            <button
              onClick={closeDetailsModal}
              className="p-2 hover:bg-muted/30 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Modal Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
            <div className="space-y-6">
              {/* Basic Info Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-muted/20 rounded-xl border border-border/20">
                  <span className="text-sm text-muted-foreground font-medium uppercase tracking-wide">Status</span>
                  <div className="mt-2">
                    <Badge variant={getStatusVariant(selectedCommand.status)} className="gap-1 font-medium">
                      {getStatusIcon(selectedCommand.status)}
                      {selectedCommand.status.replace('_', ' ')}
                    </Badge>
                  </div>
                </div>
                
                <div className="p-4 bg-muted/20 rounded-xl border border-border/20">
                  <span className="text-sm text-muted-foreground font-medium uppercase tracking-wide">Risk Level</span>
                  <p className="font-medium mt-2 text-foreground">{selectedCommand.risk_level}</p>
                </div>
                
                <div className="p-4 bg-muted/20 rounded-xl border border-border/20">
                  <span className="text-sm text-muted-foreground font-medium uppercase tracking-wide">Created</span>
                  <p className="font-medium mt-2 text-foreground">{formatDate(selectedCommand.created_at)}</p>
                </div>
              </div>

              {/* Intent & Action */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-muted/20 rounded-xl border border-border/20">
                  <span className="text-sm text-muted-foreground font-medium uppercase tracking-wide">Intent</span>
                  <p className="font-medium mt-2 text-foreground">{selectedCommand.intent}</p>
                </div>
                
                <div className="p-4 bg-muted/20 rounded-xl border border-border/20">
                  <span className="text-sm text-muted-foreground font-medium uppercase tracking-wide">Action</span>
                  <p className="font-medium mt-2 text-foreground">{selectedCommand.action}</p>
                </div>
              </div>

              {/* Explanation */}
              <div className="p-4 bg-muted/20 rounded-xl border border-border/20">
                <span className="text-sm text-muted-foreground font-medium uppercase tracking-wide mb-2 block">Explanation</span>
                <p className="text-foreground leading-relaxed">{selectedCommand.explanation}</p>
              </div>

              {/* Generated Commands */}
              {selectedCommand.generated_commands && selectedCommand.generated_commands.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-foreground">Generated Commands</h3>
                  <div className="space-y-4">
                    {selectedCommand.generated_commands.map((cmd, index) => (
                      <div key={index} className="p-4 bg-muted/20 rounded-xl border border-border/20 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-muted-foreground">Step {cmd.step}</span>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs border-border/30">
                              {cmd.risk_level} Risk
                            </Badge>
                            <Badge variant="outline" className="text-xs border-border/30">
                              {cmd.estimated_time}
                            </Badge>
                          </div>
                        </div>
                        
                        <CodeBlock command={cmd.command} language="bash" />
                        
                        <p className="text-sm text-muted-foreground leading-relaxed">{cmd.explanation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

                                {/* Execution Results */}
                  {selectedCommand.execution_results && (
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold text-foreground">Execution Results</h3>
                      
                      {/* Raw JSON Response */}
                      <div className="p-4 bg-muted/20 border border-border/20 rounded-lg">
                        <h4 className="text-sm font-semibold text-foreground mb-2">Raw JSON Response</h4>
                        <pre className="text-xs text-muted-foreground overflow-auto">
                          {JSON.stringify(selectedCommand.execution_results, null, 2)}
                        </pre>
                      </div>
                      
                      <div className="p-4 bg-muted/20 rounded-xl border border-border/20">

                    {/* Execution Summary */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="text-center p-4 bg-muted/30 rounded-lg">
                        <div className="text-2xl font-bold text-foreground">{selectedCommand.execution_results.total_steps}</div>
                        <div className="text-sm text-muted-foreground">Total Steps</div>
                      </div>
                      <div className="text-center p-4 bg-emerald-500/20 rounded-lg">
                        <div className="text-2xl font-bold text-emerald-600">{selectedCommand.execution_results.successful_steps}</div>
                        <div className="text-sm text-emerald-600">Successful</div>
                      </div>
                      <div className="text-center p-4 bg-red-500/20 rounded-lg">
                        <div className="text-2xl font-bold text-red-600">{selectedCommand.execution_results.failed_steps}</div>
                        <div className="text-sm text-red-600">Failed</div>
                      </div>
                      <div className="text-center p-4 bg-amber-500/20 rounded-lg">
                        <div className="text-2xl font-bold text-amber-600">{selectedCommand.execution_results.skipped_steps}</div>
                        <div className="text-sm text-amber-600">Skipped</div>
                      </div>
                    </div>

                    {/* Overall Status & Time */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                      <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
                        <span className="text-sm font-medium">Overall Status:</span>
                        <Badge 
                          variant={selectedCommand.execution_results.success ? "secondary" : "destructive"}
                          className="font-medium"
                        >
                          {selectedCommand.execution_results.success ? "Success" : "Failed"}
                        </Badge>
                      </div>
                      
                      <div className="text-center p-4 bg-muted/30 rounded-lg">
                        <div className="text-sm font-medium text-muted-foreground">Total Execution Time</div>
                        <div className="text-xl font-bold text-foreground">
                          {selectedCommand.execution_results.total_execution_time.toFixed(4)}s
                        </div>
                      </div>
                    </div>

                    {/* Step Results */}
                    <div className="space-y-4">
                      <h4 className="text-md font-semibold text-foreground">Step Results:</h4>
                      {selectedCommand.execution_results.step_results.map((step, index) => (
                        <div key={index} className="p-4 bg-muted/30 rounded-lg border border-border/20 space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Step {step.step}</span>
                            <Badge 
                              variant={
                                step.status === 'success' ? "secondary" :
                                step.status === 'failed' ? "destructive" :
                                step.status === 'skipped' ? "outline" : "default"
                              }
                              className="text-xs"
                            >
                              {step.status}
                            </Badge>
                          </div>
                          
                          <CodeBlock command={step.command} language="bash" />
                          
                          {step.reason && (
                            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded text-sm text-amber-700">
                              <strong>Reason:</strong> {step.reason}
                            </div>
                          )}
                          
                          {step.stdout && (
                            <div className="space-y-2">
                              <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Terminal Output:</div>
                              <div className="p-3 bg-black/90 rounded text-sm font-mono text-green-100 whitespace-pre-wrap border border-border/20">
                                {step.stdout}
                              </div>
                            </div>
                          )}
                          
                          <div className="flex items-center justify-between text-sm text-muted-foreground">
                            <span>Execution Time: {step.execution_time.toFixed(4)}s</span>
                            {step.exit_code !== undefined && (
                              <span>Exit Code: {step.exit_code}</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Timestamps */}
              <div className="p-4 bg-muted/20 rounded-xl border border-border/20">
                <span className="text-sm text-muted-foreground font-medium uppercase tracking-wide mb-3 block">Timeline</span>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Created:</span>
                    <p className="font-medium text-foreground">{formatDate(selectedCommand.created_at)}</p>
                  </div>
                  {selectedCommand.approved_at && (
                    <div>
                      <span className="text-muted-foreground">Approved:</span>
                      <p className="font-medium text-foreground">{formatDate(selectedCommand.approved_at)}</p>
                    </div>
                  )}
                  {selectedCommand.executed_at && (
                    <div>
                      <span className="text-muted-foreground">Executed:</span>
                      <p className="font-medium text-foreground">{formatDate(selectedCommand.executed_at)}</p>
                    </div>
                  )}
                  {selectedCommand.completed_at && (
                    <div>
                      <span className="text-muted-foreground">Completed:</span>
                      <p className="font-medium text-foreground">{formatDate(selectedCommand.completed_at)}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
        )}
      </CardContent>
    </Card>
  );
}