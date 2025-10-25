"use client";

import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface CodeBlockProps {
  command: string;
  language?: string;
  className?: string;
}

export function CodeBlock({ command, language = 'bash', className = '' }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy command:', err);
    }
  };

  return (
    <div className={`relative group ${className}`}>
      <div className="flex items-center justify-between p-3 bg-muted/30 border border-border rounded-t-md">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {language}
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={copyToClipboard}
          className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-muted"
        >
          {copied ? (
            <Check className="h-3 w-3 text-foreground" />
          ) : (
            <Copy className="h-3 w-3 text-muted-foreground" />
          )}
        </Button>
      </div>
      <div className="p-4 bg-muted/20 border-x border-b border-border rounded-b-md">
        <code className="font-mono text-sm font-bold text-foreground break-all leading-relaxed">
          {command}
        </code>
      </div>
    </div>
  );
}
