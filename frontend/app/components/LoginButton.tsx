"use client";

export function LoginButton() {
  return (
    <a 
      href="/login" 
      className="inline-flex items-center gap-2 px-8 py-3 bg-foreground hover:bg-foreground/90 text-background font-medium rounded-xl shadow-sm transition-colors"
    >
      Sign In
    </a>
  );
}
