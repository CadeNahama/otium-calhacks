import type { Metadata } from "next";
import "./globals.css";
import {
  AuthKitProvider
} from "@workos-inc/authkit-nextjs/components";
import { UserProvider } from "./contexts/UserContext";
import { ConnectionProvider } from "./contexts/ConnectionContext";
import Script from "next/script";
import { Analytics } from "@vercel/analytics/next";

export const metadata: Metadata = {
  title: "Otium - Review, approve, and execute",
  description: "Review, approve, and execute AI-generated commands securely with Otium's AI-powered server management platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <Script
          src="https://cdn.amplitude.com/libs/analytics-browser-2.11.1-min.js.gz"
          strategy="beforeInteractive"
        />
        <Script
          src="https://cdn.amplitude.com/libs/plugin-session-replay-browser-1.8.0-min.js.gz"
          strategy="beforeInteractive"
        />
        <Script
          id="amplitude-init"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              if (window.amplitude && window.sessionReplay) {
                window.amplitude.add(window.sessionReplay.plugin({sampleRate: 1}));
                window.amplitude.init('4ab769d77e744c4215941ff88384d66b', {"autocapture":{"elementInteractions":true}});
              }
            `,
          }}
        />
      </head>
      <body className="antialiased">
        <AuthKitProvider>
          <UserProvider>
            <ConnectionProvider>
              {children}
            </ConnectionProvider>
          </UserProvider>
        </AuthKitProvider>
        <Analytics />
      </body>
    </html>
  );
}
