import React from "react";
import { cn } from "@/lib/utils";

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  variant?: "light" | "dark" | "strong";
  hoverable?: boolean;
}

export const GlassCard = ({ 
  children, 
  className, 
  variant = "dark", 
  hoverable = true,
  ...props 
}: GlassCardProps) => {
  const variants = {
    light: "glass",
    dark: "glass-dark",
    strong: "glass-strong",
  };

  return (
    <div
      className={cn(
        variants[variant],
        "rounded-[2.5rem] border border-white/10 transition-all duration-700",
        "shadow-[0_20px_50px_rgba(0,0,0,0.5)]",
        // Enforce p-12 as default if not overridden
        !className?.includes('p-') && "p-12",
        hoverable && "hover:bg-white/[0.05] hover:border-white/20 hover:shadow-emerald-500/10",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
