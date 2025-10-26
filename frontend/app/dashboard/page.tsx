"use client";

import { useState } from 'react';
import { SSHCard } from '../components/SSHCard';
import { CommandPreviewCard } from '../components/CommandPreviewCard';
import { TaskSubmissionCardEnhanced } from '../components/TaskSubmissionCardEnhanced';
import { Footer } from '../components/Footer';
import { useUser } from '../contexts/UserContext';
import { Zap, Shield, Bot } from 'lucide-react';
import { ToastContainer } from '../components/Toast';
import { useToast } from '../hooks/useToast';

export default function Dashboard() {
  const { userId, isAuthenticated, isLoading } = useUser();
  const { toasts, removeToast } = useToast();
  const [commandRefreshTrigger, setCommandRefreshTrigger] = useState(0);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-6" />
            <p className="text-body-regular text-muted-foreground">Loading authentication...</p>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <div className="flex-1">
          <main className="px-8 py-16">
            <div className="max-w-4xl mx-auto">
              <div className="text-center py-24">
                <h1 className="mb-8 leading-tight">
                  Welcome to Ping
                </h1>
                <p className="text-body-large text-muted-foreground mb-12 max-w-2xl mx-auto leading-relaxed">
                  Review, approve, and execute AI-generated commands securely.
                </p>
                <div className="flex items-center justify-center gap-12 mb-12">
                  <div className="flex items-center gap-3 text-muted-foreground">
                    <Shield className="w-5 h-5" />
                    <span className="text-body-regular">Secure SSH</span>
                  </div>
                  <div className="flex items-center gap-3 text-muted-foreground">
                    <Bot className="w-5 h-5" />
                    <span className="text-body-regular">AI Commands</span>
                  </div>
                  <div className="flex items-center gap-3 text-muted-foreground">
                    <Zap className="w-5 h-5" />
                    <span className="text-body-regular">Fast Execution</span>
                  </div>
                </div>
                <a 
                  href="/login" 
                  className="inline-flex items-center gap-2 px-8 py-3 bg-primary hover:bg-primary/90 text-primary-foreground font-medium rounded-xl shadow-sm transition-colors"
                >
                  Sign In
                </a>
              </div>
            </div>
          </main>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <div className="flex-1">
        <main className="px-8 py-16">
          <div className="max-w-7xl mx-auto">
            <div className="mb-16 text-center">
              <h1 className="text-4xl font-bold text-foreground leading-tight">
                Welcome to Ping.
              </h1>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-10">
              <SSHCard userId={userId} />
              <TaskSubmissionCardEnhanced 
                userId={userId} 
                onCommandStatusChange={() => {
                  // Refresh command list when status changes
                  setCommandRefreshTrigger(prev => prev + 1);
                }}
              />
              <CommandPreviewCard userId={userId} refreshTrigger={commandRefreshTrigger} />
            </div>
          </div>
        </main>

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
      <Footer />
    </div>
  );
}