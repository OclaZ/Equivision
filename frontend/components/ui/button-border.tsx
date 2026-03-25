"use client";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { motion } from "motion/react";
import React from "react";

export function ButtonBorder({ children, className, ...props }: React.ComponentProps<typeof Button>) {
  return (
    <Button 
      variant={"outline"} 
      className={cn("relative bg-black/40 backdrop-blur-md border border-white/10 hover:bg-white/10 hover:border-white/20 text-white rounded-full transition-all duration-300", className)} 
      {...props}
    >
      <div
        className={cn(
          "-inset-px pointer-events-none absolute rounded-[inherit] border-2 border-transparent border-inset [mask-clip:padding-box,border-box]",
          "[mask-composite:intersect] [mask-image:linear-gradient(transparent,transparent),linear-gradient(#000,#000)]"
        )}
      >
        <motion.div
          className={cn(
            "absolute aspect-square bg-gradient-to-r from-transparent via-white to-white"
          )}
          animate={{
            offsetDistance: ["0%", "100%"],
          }}
          style={{
            width: 30,
            offsetPath: `rect(0 auto auto 0 round 100px)`,
          }}
          transition={{
            repeat: Number.POSITIVE_INFINITY,
            duration: 4,
            ease: "linear",
          }}
        />
      </div>
      {children}
    </Button>
  );
}
