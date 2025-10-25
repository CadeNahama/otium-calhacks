"use client";

export function LoginButton() {
  return (
    <a 
      href="/login" 
      className="inline-flex items-center gap-2 px-6 py-2.5 border border-border text-foreground hover:bg-muted hover:text-foreground font-medium rounded-lg transition-colors"
    >
      Sign In
    </a>
  );
}
