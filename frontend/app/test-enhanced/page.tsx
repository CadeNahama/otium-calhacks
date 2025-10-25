"use client";

import { TaskSubmissionCardEnhanced } from '../components/TaskSubmissionCardEnhanced';
import { useUser } from '../contexts/UserContext';

export default function TestEnhancedPage() {
  const { userId, isAuthenticated, isLoading } = useUser();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Authentication Required</h1>
          <a href="/login" className="text-primary hover:underline">Sign In</a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-foreground mb-4">
            🎯 Enhanced Step-by-Step Approval Test
          </h1>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="text-green-600 font-semibold">✅ Database Persistence</div>
              <div className="text-sm text-green-600">All data stored in PostgreSQL</div>
            </div>
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="text-blue-600 font-semibold">🔐 Encrypted Credentials</div>
              <div className="text-sm text-blue-600">SSH passwords secured</div>
            </div>
            <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <div className="text-purple-600 font-semibold">🎯 Step-by-Step Approval</div>
              <div className="text-sm text-purple-600">Like Cursor workflow</div>
            </div>
          </div>
          <p className="text-muted-foreground">
            Test the new step-by-step approval system. Each command step requires individual approval.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-8">
          <TaskSubmissionCardEnhanced
            userId={userId}
            onCommandStatusChange={() => {
              console.log('Command status changed - refreshing...');
            }}
          />
        </div>

        <div className="mt-8 p-6 bg-muted/20 rounded-lg border border-border/20">
          <h3 className="font-semibold mb-4">🧪 Test Instructions:</h3>
          <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
            <li>Connect to an SSH server using the connection form</li>
            <li>Submit a task like &quot;Check system status&quot; or &quot;List files and check disk space&quot;</li>
            <li>You should see each command step displayed individually</li>
            <li>Approve or reject each step separately</li>
            <li>Safe commands (ls, pwd, df) should be auto-approved</li>
            <li>Risky commands require manual approval</li>
            <li>Only when all steps are approved can you execute</li>
          </ol>
        </div>

        <div className="mt-6 flex items-center justify-center gap-4">
          <a
            href="/dashboard"
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            ← Back to Dashboard
          </a>
          <a
            href="https://otium-backend-production.up.railway.app/api/health"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 border border-border text-foreground rounded-lg hover:bg-muted/20 transition-colors"
          >
            Check API Health →
          </a>
        </div>
      </div>
    </div>
  );
}
