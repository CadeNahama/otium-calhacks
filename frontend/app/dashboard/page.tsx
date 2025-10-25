"use client";

import { useState } from 'react';
import { SSHCard } from '../components/SSHCard';
import { CommandPreviewCard } from '../components/CommandPreviewCard';
import { TaskSubmissionCardEnhanced } from '../components/TaskSubmissionCardEnhanced';
import { Footer } from '../components/Footer';
import { useUser } from '../contexts/UserContext';
import { Zap, Shield, Bot, LogOut } from 'lucide-react';
import { ToastContainer } from '../components/Toast';
import { useToast } from '../hooks/useToast';
import { handleSignOutAction } from '../actions/signOut';

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
                  Welcome to Otium
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
        <div className="absolute top-6 right-8 z-50 group">
          <div className="relative">
            {/* Hamburger Icon */}
            <button className="flex items-center justify-center w-8 h-8 bg-card hover:bg-card/80 text-foreground rounded-lg border border-border/20 shadow-sm transition-colors">
              <div className="flex flex-col gap-0.5">
                <div className="w-4 h-0.5 bg-foreground rounded-full transition-all group-hover:rotate-45 group-hover:translate-y-1"></div>
                <div className="w-4 h-0.5 bg-foreground rounded-full transition-all group-hover:opacity-0"></div>
                <div className="w-4 h-0.5 bg-foreground rounded-full transition-all group-hover:-rotate-45 group-hover:-translate-y-1"></div>
              </div>
            </button>
            
            {/* Sliding Menu */}
            <div className="absolute right-0 top-10 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 transform translate-y-2 group-hover:translate-y-0">
              <div className="bg-card border border-border/20 rounded-lg shadow-lg p-1.5 min-w-40">
                <button
                  onClick={() => handleSignOutAction()}
                  className="w-full flex items-center gap-2 px-3 py-2 text-left text-foreground hover:bg-muted/30 rounded-md transition-colors text-sm"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <main className="px-8 py-16">
          <div className="max-w-7xl mx-auto">
            <div className="mb-16 text-center">
              <h1 className="text-4xl font-bold text-foreground leading-tight">
                Welcome to Otium.
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