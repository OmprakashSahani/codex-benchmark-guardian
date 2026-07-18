import type { Metadata } from "next";
import { ThemeProvider } from "@/components/theme-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Codex Benchmark Guardian",
  description: "Catch performance regressions before they merge with deterministic benchmark analysis.",
  openGraph: {
    title: "Codex Benchmark Guardian",
    description: "Deterministic performance regression analysis and Codex-ready handoff.",
    type: "website",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
