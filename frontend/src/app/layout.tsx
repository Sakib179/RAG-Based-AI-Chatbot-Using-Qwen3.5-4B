import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AuthProvider } from "@/hooks/useAuth";
import { QueryProvider } from "@/providers/QueryProvider";
import { ThemeProvider } from "@/providers/ThemeProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Knowledge Chatbot",
  description: "Ask questions grounded in your private knowledge base.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="en" suppressHydrationWarning><body><ThemeProvider><QueryProvider><AuthProvider>{children}</AuthProvider></QueryProvider></ThemeProvider></body></html>;
}
