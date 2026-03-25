"use client";

import { cn } from "@/lib/utils";
import Link from "next/link";
import React from "react";

import Image from "next/image";

export const Sidebar = ({
  className,
  links,
}: {
  className?: string;
  links: { href: string; icon: React.ReactNode; active?: boolean }[];
}) => {
  return (
    <div
      className={cn(
        "h-full w-[110px] xl:w-[120px] bg-[#111315]/80 backdrop-blur-2xl rounded-[2.5rem] flex flex-col items-center py-10 justify-between shrink-0",
        "border border-white/[0.08] shadow-[0_20px_40px_rgba(0,0,0,0.4)] relative overflow-hidden group/sidebar",
        className
      )}
    >
      {/* Decorative Sidebar Glow */}
      <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-emerald-500/5 rounded-full blur-[80px] pointer-events-none" />
      {/* Logo Area */}
      <Link href="/" className="flex items-center justify-center w-full px-4 xl:px-6 mt-2">
        <Image
          src="https://res.cloudinary.com/ddvzn2n7i/image/upload/v1774183125/unnamed-removebg-preview_hvqlqb.png"
          alt="EquiVision"
          width={180}
          height={60}
          className="w-full h-auto brightness-0 invert opacity-90 object-contain drop-shadow-md transition-transform hover:scale-105"
        />
      </Link>

      {/* Navigation Links */}
      <div className="flex flex-col gap-8 items-center justify-center flex-1">
        {links.map((link, idx) => (
          <Link
            key={idx}
            href={link.href}
            className={cn(
              "flex items-center justify-center h-12 w-12 rounded-2xl transition-all duration-300 group",
              link.active
                ? "bg-white text-black shadow-[0_0_20px_rgba(255,255,255,0.1)]"
                : "text-white/40 hover:text-white hover:bg-white/10"
            )}
          >
            <div className={cn("transition-transform duration-300 group-hover:scale-110", link.active && "scale-110")}>
              {link.icon}
            </div>
          </Link>
        ))}
      </div>

      {/* Bottom Action Area (Empty or for future use) */}
      <div className="h-12 w-12" />
    </div>
  );
};
