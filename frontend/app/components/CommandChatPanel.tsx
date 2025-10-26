"use client";

import { useState, useEffect, useRef } from 'react';
import { API_CONFIG, apiCall } from '@/app/config/api';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, MessageSquare, Loader2 } from 'lucide-react';
import { useToast } from '../hooks/useToast';

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  message: string;
  message_type: string;
  created_at: string;
  metadata?: any;
}

interface CommandChatPanelProps {
  commandId: string;
  userId: string;
  commands?: Array<{
    step: number;
    command: string;
    explanation: string;
  }>;
}

export function CommandChatPanel({ commandId, userId, commands = [] }: CommandChatPanelProps) {
  const { error: showError } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch existing messages on mount
  useEffect(() => {
    const fetchMessages = async () => {
      try {
        setIsLoading(true);
        const response = await apiCall<{ messages: ChatMessage[] }>(
          `${API_CONFIG.ENDPOINTS.COMMANDS.BASE}/${commandId}/chat`,
          { method: 'GET' },
          userId
        );
        setMessages(response.messages || []);
      } catch (error) {
        console.error('Failed to fetch chat messages:', error);
        // Don't show error toast on initial load - just start with empty chat
      } finally {
        setIsLoading(false);
      }
    };

    if (commandId) {
      fetchMessages();
    }
  }, [commandId, userId]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || isSending) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsSending(true);

    try {
      const response = await apiCall<{
        user_message: ChatMessage;
        ai_message: ChatMessage;
      }>(
        `${API_CONFIG.ENDPOINTS.COMMANDS.BASE}/${commandId}/chat`,
        {
          method: 'POST',
          body: JSON.stringify({ message: userMessage }),
        },
        userId
      );

      // Add both user and AI messages to the chat
      setMessages(prev => [
        ...prev,
        response.user_message,
        response.ai_message
      ]);
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Failed to send message');
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  return (
    <div className="mt-6 border-t border-border/20 pt-6">
      <div className="space-y-4">
        {/* Chat Header */}
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-primary" />
          <h4 className="text-lg font-semibold text-foreground">
            Ask questions about these commands
          </h4>
        </div>

        {/* Chat Messages */}
        <div className="bg-muted/10 rounded-xl border border-border/20 p-4 min-h-[200px] max-h-[400px] overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center h-[200px]">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[200px] text-center">
              <MessageSquare className="w-12 h-12 text-muted-foreground/30 mb-3" />
              <p className="text-sm text-muted-foreground">
                No messages yet. Ask me anything about these commands!
              </p>
              <div className="mt-4 space-y-2">
                <p className="text-xs text-muted-foreground/70">Try asking:</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  <button
                    onClick={() => setInputMessage("What will these commands do?")}
                    className="text-xs px-3 py-1 bg-muted/30 hover:bg-muted/50 rounded-full transition-colors"
                  >
                    What will these commands do?
                  </button>
                  <button
                    onClick={() => setInputMessage("Is this safe to run?")}
                    className="text-xs px-3 py-1 bg-muted/30 hover:bg-muted/50 rounded-full transition-colors"
                  >
                    Is this safe to run?
                  </button>
                  <button
                    onClick={() => setInputMessage("Explain step by step")}
                    className="text-xs px-3 py-1 bg-muted/30 hover:bg-muted/50 rounded-full transition-colors"
                  >
                    Explain step by step
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      msg.sender === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted/50 text-foreground'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <span className="text-xs font-semibold opacity-70">
                        {msg.sender === 'user' ? '👤 You' : '🤖 AI'}
                      </span>
                    </div>
                    <p className="text-sm mt-1 whitespace-pre-wrap break-words">
                      {msg.message}
                    </p>
                    <p className="text-xs opacity-50 mt-2">
                      {new Date(msg.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Chat Input */}
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <Textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about these commands..."
            className="flex-1 min-h-[60px] max-h-[120px] resize-none"
            disabled={isSending}
          />
          <Button
            type="submit"
            disabled={!inputMessage.trim() || isSending}
            className="self-end"
          >
            {isSending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </form>

        {/* Helper Text */}
        <p className="text-xs text-muted-foreground">
          💡 Ask questions to understand the commands better. I'll explain without changing them unless you explicitly ask me to.
        </p>
      </div>
    </div>
  );
}

