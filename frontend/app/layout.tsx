import type { Metadata } from "next";
import "./globals.css";
import { UserProvider } from "./contexts/UserContext";
import { ConnectionProvider } from "./contexts/ConnectionContext";

export const metadata: Metadata = {
  title: "Ping - Review, approve, and execute",
  description: "Review, approve, and execute AI-generated commands securely with Ping's AI-powered server management platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
          <UserProvider>
            <ConnectionProvider>
              {children}
            </ConnectionProvider>
          </UserProvider>
      </body>
    </html>
  );
}
