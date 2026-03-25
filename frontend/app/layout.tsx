import type { Metadata } from "next";
import { Bricolage_Grotesque, Geist } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

const geist = Geist({ subsets: ['latin'], variable: '--font-sans' });
const bricolage = Bricolage_Grotesque({ subsets: ['latin'], variable: '--font-heading' });

export const metadata: Metadata = {
  title: "EquiVision — Intelligent Equine Platform",
  description:
    "The intelligent system combining computer vision and machine learning to secure transactions and identify equine market value with 95% confidence.",
  keywords: [
    "equine",
    "horse",
    "AI",
    "breed identification",
    "market valuation",
    "computer vision",
    "machine learning",
  ],
  openGraph: {
    title: "EquiVision — Where Innovation Meets Execution",
    description:
      "AI-powered equine breed analysis, market valuation, and health insights.",
    type: "website",
  },
};

import { AuthProvider } from "@/context/AuthContext";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn("font-sans", geist.variable, bricolage.variable)} suppressHydrationWarning>
      <body className={cn("antialiased", "font-sans")} suppressHydrationWarning>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
