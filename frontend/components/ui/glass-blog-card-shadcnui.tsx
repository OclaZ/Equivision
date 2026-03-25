"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { Clock } from "lucide-react";
import Image from "next/image";

interface GlassBlogCardProps {
  title?: string;
  excerpt?: string;
  image?: string;
  author?: {
    name: string;
    avatar: string;
  };
  date?: string;
  readTime?: string;
  tags?: string[];
  className?: string;
  onClick?: () => void;
}

const defaultPost = {
  title: "The Future of UI Design",
  excerpt:
    "Exploring the latest trends in glassmorphism, 3D elements, and micro-interactions.",
  image:
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&q=80",
  author: {
    name: "EquiVision AI",
    avatar: "https://github.com/shadcn.png",
  },
  date: "Dec 2, 2025",
  readTime: "5 min read",
  tags: ["Horse", "AI Analysis"],
};

export function GlassBlogCard({
  title = defaultPost.title,
  excerpt = defaultPost.excerpt,
  image = defaultPost.image,
  date = defaultPost.date,
  readTime = defaultPost.readTime,
  tags = defaultPost.tags,
  className,
  onClick,
}: GlassBlogCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className={cn("w-full max-w-[420px]", className)}
      onClick={onClick}
    >
      <Card className="group relative flex flex-col overflow-hidden rounded-2xl border border-white/[0.06] bg-[#0a0a0a] cursor-pointer transition-all duration-500 hover:border-emerald-500/20 hover:shadow-[0_0_60px_-10px_rgba(52,211,153,0.15)]">
        
        {/* ── Image ── */}
        <div className="relative overflow-hidden rounded-t-2xl aspect-[16/9]">
          <motion.img
            src={image}
            alt={title}
            className="h-full w-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.04]"
          />
          {/* Scrim */}
          <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0a] via-[#0a0a0a]/10 to-transparent" />

          {/* Tags — bottom left */}
          <div className="absolute bottom-4 left-4 flex gap-2">
            {tags?.map((tag, i) => (
              <Badge
                key={i}
                className="rounded-full bg-emerald-500/10 border border-emerald-500/25 text-[10px] font-bold tracking-[0.1em] uppercase text-emerald-400 px-4 py-1.5 backdrop-blur-md shadow-lg shadow-black/20"
              >
                {tag}
              </Badge>
            ))}
          </div>

          {/* Read time — top right */}
          <div className="absolute top-4 right-4 flex items-center gap-2 rounded-full bg-black/60 border border-white/10 backdrop-blur-md px-4 py-1.5">
            <Clock className="h-3.5 w-3.5 text-white/30" />
            <span className="text-[10px] font-bold text-white/50 tracking-widest">{readTime}</span>
          </div>
        </div>

        {/* ── Body ── */}
        <div className="flex flex-col items-center text-center gap-6 px-10 pt-7 pb-10">

          {/* Eyebrow */}
          <div className="flex items-center justify-center gap-2 mb-1">
             <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse" />
             <p className="text-[10px] font-black tracking-[0.6em] uppercase text-emerald-400">
               Identifiant Certifi&eacute;
             </p>
          </div>

          {/* Title + arrow integrated */}
          <div className="flex flex-col items-center gap-3">
            <h3 className="text-[24px] font-bold leading-tight tracking-tight text-white capitalize transition-colors duration-300 group-hover:text-emerald-300">
              {title}
            </h3>
            <div className="h-0.5 w-12 bg-emerald-500/30 rounded-full transition-all duration-300 group-hover:w-24 group-hover:bg-emerald-500 shadow-[0_0_10px_rgba(52,211,153,0.3)]" />
          </div>

          {/* Excerpt */}
          <p className="line-clamp-2 text-[14px] leading-relaxed text-white/50 font-medium max-w-[320px]">
            {excerpt}
          </p>

          {/* Footer - Stacked & Centered */}
          <div className="flex flex-col items-center gap-10 w-full pt-4">
            <div className="flex items-center justify-center gap-6">
              <div className="h-10 w-24 relative brightness-0 invert opacity-80 group-hover:opacity-100 transition-opacity">
                 <Image
                  src="https://res.cloudinary.com/ddvzn2n7i/image/upload/v1774183125/unnamed-removebg-preview_hvqlqb.png"
                  alt="EquiVision Logo"
                  fill
                  className="object-contain"
                />
              </div>
              <div className="h-4 w-px bg-white/10" />
              <span className="text-[11px] font-bold text-white/30 tracking-[0.2em] uppercase">
                {date}
              </span>
            </div>

            {/* CTA chip */}
            <motion.button
              whileHover={{ scale: 1.02, backgroundColor: "rgba(52, 211, 153, 0.15)" }}
              whileTap={{ scale: 0.98 }}
              className="w-full text-[11px] font-black tracking-[0.3em] uppercase text-emerald-400 border border-emerald-500/20 rounded-2xl py-5 px-6 bg-emerald-500/5 transition-all duration-500 shadow-2xl shadow-emerald-500/5 group-hover:border-emerald-500/40"
            >
              RAPPORT D&Eacute;TAILL&Eacute;
            </motion.button>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}