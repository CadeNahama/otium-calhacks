"use client";

import { useState, useEffect } from 'react';
import { API_CONFIG, apiCall } from '@/app/config/api';
import { useConnection } from '@/app/contexts/ConnectionContext';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Drawer, DrawerContent, DrawerDescription, DrawerHeader, DrawerTitle, DrawerTrigger } from '@/components/ui/drawer';
import { Wifi, User, Lock, Globe, Zap, Server, RotateCcw } from 'lucide-react';
import { useToast } from '../hooks/useToast';

interface SSHCardProps {
  userId: string;
}

export function SSHCard({ userId }: SSHCardProps) {
  const { activeConnection, refreshConnection } = useConnection();
  const { success: showSuccess, error: showError } = useToast();
  const [isConnecting, setIsConnecting] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);
  const [credentialError, setCredentialError] = useState(false);
  const [isTestServerDrawerOpen, setIsTestServerDrawerOpen] = useState(false);
  const [lastConnection, setLastConnection] = useState<{ hostname: string; username: string; port: string } | null>(null);
  
  const [formData, setFormData] = useState({
    hostname: '',
    username: '',
    password: '',
    port: '22'
  });

  // SESSION-BASED: Load last connection details from localStorage
  useEffect(() => {
    const saved = localStorage.getItem(`ping_last_connection_${userId}`);
    if (saved) {
      try {
        const lastConn = JSON.parse(saved);
        setLastConnection(lastConn);
      } catch (error) {
        console.error('Failed to parse saved connection:', error);
        localStorage.removeItem(`ping_last_connection_${userId}`);
      }
    }
  }, [userId]);

  // SESSION-BASED: Save successful connection details (without password)
  const saveLastConnection = (connectionData: typeof formData) => {
    const toSave = {
      hostname: connectionData.hostname,
      username: connectionData.username,
      port: connectionData.port
    };
    localStorage.setItem(`ping_last_connection_${userId}`, JSON.stringify(toSave));
    setLastConnection(toSave);
  };

  // SESSION-BASED: Use last connection details
  const useLastConnection = () => {
    if (lastConnection) {
      setFormData(prev => ({
        ...prev,
        hostname: lastConnection.hostname,
        username: lastConnection.username,
        port: lastConnection.port,
        password: '' // User must enter password again for security
      }));
      setCredentialError(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear credential error when user starts typing
    if (credentialError) {
      setCredentialError(false);
    }
  };

  const useTestServer = () => {
    setFormData({
      hostname: '143.198.64.140',
      username: 'root',
      password: '7^e+unJ%Dk%KMbS',
      port: '22'
    });
    setCredentialError(false);
    setIsTestServerDrawerOpen(false);
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsConnecting(true);

    try {
      const response = await apiCall(API_CONFIG.ENDPOINTS.SSH.CONNECT, {
        method: 'POST',
        body: JSON.stringify(formData),
      }, userId);

      // Check if the response indicates failure
      if (response && typeof response === 'object' && 'success' in response && response.success === false) {
        setCredentialError(true);
        showError('Error: Check credentials');
        return;
      }

      // Clear any previous credential errors on success
      setCredentialError(false);
      
      // SESSION-BASED: Save connection details for quick reconnect
      saveLastConnection(formData);
      
      showSuccess(`Successfully connected to ${formData.hostname}`);
      setFormData({ hostname: '', username: '', password: '', port: '22' });
      await refreshConnection();
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Failed to connect');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!activeConnection?.connection_id) {
      showError('No active connection or connection ID missing');
      return;
    }
    
    const connectionId = activeConnection.connection_id;
    const hostname = activeConnection.hostname;
    
    setIsDisconnecting(true);

    try {
      await apiCall(API_CONFIG.ENDPOINTS.SSH.DISCONNECT, {
        method: 'POST',
        body: JSON.stringify({ connection_id: connectionId }),
      }, userId);

      // SESSION-BASED: Clear saved connection on manual disconnect
      localStorage.removeItem(`ping_last_connection_${userId}`);
      setLastConnection(null);
      
      showSuccess(`Disconnected from ${hostname}`);
      await refreshConnection();
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Failed to disconnect');
    } finally {
      setIsDisconnecting(false);
    }
  };

  const getStatusColor = (status: string, alive: boolean) => {
    if (status === 'connected' && alive) return 'bg-emerald-400';
    if (status === 'connected' && !alive) return 'bg-amber-400';
    return 'bg-red-400';
  };

  const getStatusText = (status: string, alive: boolean) => {
    if (status === 'connected' && alive) return 'Connected';
    if (status === 'connected' && !alive) return 'Unstable';
    return 'Disconnected';
  };

  return (
    <Card className="h-fit border border-border/20 shadow-sm bg-card">
      <CardHeader className="pb-4 pt-5 px-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base leading-tight">SSH</h3>
            <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">Secure server access</p>
          </div>
          
          {activeConnection && (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${getStatusColor(activeConnection.status, activeConnection.alive)} animate-pulse`} />
                <Badge variant="secondary" className="text-body-small font-medium px-2 py-1">
                  {getStatusText(activeConnection.status, activeConnection.alive)}
                </Badge>
              </div>
              <Button
                onClick={handleDisconnect}
                disabled={isDisconnecting}
                variant="outline"
                size="sm"
                className="border-border/30 text-foreground hover:bg-red-50 hover:border-red-200 hover:text-red-700 text-body-small px-3 py-1 h-8 rounded-lg transition-colors"
              >
                {isDisconnecting ? 'Disconnecting...' : 'Disconnect'}
              </Button>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4 px-6 pb-5">
        {activeConnection && (
          <div className="p-4 bg-muted/20 rounded-xl border border-border/30">
            <div className="flex-1">
              <h4 className="text-sm leading-tight mb-2">Connection Details</h4>
              <div className="space-y-2 text-xs text-muted-foreground">
                <p className="flex items-center gap-2">
                  <Globe className="w-4 h-4" />
                  <span className="font-medium text-foreground">{activeConnection.hostname}:{activeConnection.port}</span>
                </p>
                <p className="flex items-center gap-2">
                  <User className="w-4 h-4" />
                  Connected as <span className="font-medium text-foreground">{activeConnection.username}</span>
                </p>
                <p className="flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  {activeConnection.connected_at ? new Date(activeConnection.connected_at).toLocaleString() : 'Unknown time'}
                </p>
              </div>
            </div>
          </div>
        )}

        {!activeConnection && (
          <div className="space-y-3">
            {/* SESSION-BASED: Quick Reconnect Button */}
            {lastConnection && (
              <div className="p-4 bg-blue-50/50 border border-blue-200 rounded-xl">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-blue-900 mb-1">Quick Reconnect</h4>
                    <p className="text-xs text-blue-700">
                      {lastConnection.username}@{lastConnection.hostname}:{lastConnection.port}
                    </p>
                  </div>
                  <Button
                    onClick={useLastConnection}
                    variant="outline"
                    size="sm"
                    className="border-blue-200 text-blue-700 hover:bg-blue-100 hover:border-blue-300 text-xs px-3 py-1 h-8"
                  >
                    <RotateCcw className="w-3 h-3 mr-1" />
                    Use
                  </Button>
                </div>
              </div>
            )}

            <form onSubmit={handleConnect} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="hostname" className="text-body-small font-medium text-foreground">Hostname/IP</Label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input 
                      id="hostname"
                      type="text" 
                      name="hostname"
                      value={formData.hostname}
                      onChange={handleInputChange}
                      placeholder="192.168.1.100"
                      required
                      className="pl-10 h-10 border-border/30 bg-input text-foreground focus:border-primary/50 focus:ring-primary/20 text-body-regular"
                    />
                  </div>
                </div>
                
                <div className="space-y-1.5">
                  <Label htmlFor="port" className="text-body-small font-medium text-foreground">Port</Label>
                  <Input 
                    id="port"
                    type="number" 
                    name="port"
                    value={formData.port}
                    onChange={handleInputChange}
                    placeholder="22"
                    min="1"
                    max="65535"
                    required
                    className="h-10 border-border/30 bg-input text-foreground focus:border-primary/50 focus:ring-primary/20 text-body-regular"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="username" className="text-body-small font-medium text-foreground">Username</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input 
                      id="username"
                      type="text" 
                      name="username"
                      value={formData.username}
                      onChange={handleInputChange}
                      placeholder="admin"
                      required
                      className="pl-10 h-10 border-border/30 bg-input text-foreground focus:border-primary/50 focus:ring-primary/20 text-body-regular"
                    />
                  </div>
                </div>
                
                <div className="space-y-1.5">
                  <Label htmlFor="password" className="text-body-small font-medium text-foreground">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input 
                      id="password"
                      type="password" 
                      name="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      placeholder="••••••••"
                      required
                      className="pl-10 h-10 border-border/30 bg-input text-foreground focus:border-primary/50 focus:ring-primary/20 text-body-regular"
                    />
                  </div>
                </div>
              </div>
              {/* Test Server Button */}
              <div className="text-center">
                <Drawer open={isTestServerDrawerOpen} onOpenChange={setIsTestServerDrawerOpen}>
                  <DrawerTrigger asChild>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="border-border/30 text-muted-foreground hover:bg-muted/30 hover:text-foreground transition-colors"
                    >
                      <Server className="w-4 h-4 mr-2" />
                      Use test server
                    </Button>
                  </DrawerTrigger>
                  <DrawerContent>
                    <div className="mx-auto w-full max-w-sm">
                      <DrawerHeader>
                        <DrawerTitle>Test Server Credentials</DrawerTitle>
                        <DrawerDescription>
                          Use these credentials to test Ping.
                        </DrawerDescription>
                      </DrawerHeader>
                      <div className="p-4 space-y-4">
                        <div className="space-y-2">
                          <Label className="text-sm font-medium">Hostname</Label>
                          <div className="p-3 bg-muted/30 rounded-lg border border-border/20">
                            <code className="text-sm">143.198.64.140</code>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label className="text-sm font-medium">Username</Label>
                          <div className="p-3 bg-muted/30 rounded-lg border border-border/20">
                            <code className="text-sm">root</code>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label className="text-sm font-medium">Password</Label>
                          <div className="p-3 bg-muted/30 rounded-lg border border-border/20">
                            <code className="text-sm">7^e+unJ%Dk%KMbS</code>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label className="text-sm font-medium">Port</Label>
                          <div className="p-3 bg-muted/30 rounded-lg border border-border/20">
                            <code className="text-sm">22</code>
                          </div>
                        </div>
                        <Button 
                          onClick={useTestServer}
                          className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
                        >
                          Use These Credentials
                        </Button>
                      </div>
                    </div>
                  </DrawerContent>
                </Drawer>
              </div>
              <Button 
                type="submit"
                disabled={isConnecting || !formData.hostname || !formData.username || !formData.password}
                className="w-full h-11 bg-primary hover:bg-primary/90 text-primary-foreground font-medium shadow-sm rounded-xl transition-all duration-200"
              >
                {isConnecting ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    <span className="text-body-regular">Connecting...</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Wifi className="w-4 h-4" />
                    <span className="text-body-regular">Connect to Server</span>
                  </div>
                )}
              </Button>

              {/* Credential Error Alert */}
              {credentialError && (
                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-xs font-bold">!</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-red-700">Authentication Failed</p>
                      <p className="text-xs text-red-600">Please check your username, password, and server details</p>
                    </div>
                  </div>
                </div>
              )}
            </form>
          </div>
        )}
      </CardContent>
    </Card>
  );
}