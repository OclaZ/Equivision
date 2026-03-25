"use client";

import { motion } from "motion/react";
import dynamic from "next/dynamic";
import { ButtonBorder } from "@/components/ui/button-border";

const VideoPlayer = dynamic(() => import("./VideoPlayer"), { ssr: false });

const VIDEO_SRC =
  "https://res.cloudinary.com/ddvzn2n7i/video/upload/v1773750447/Untitled_design_hko4au.mp4";

const badges = [
  { icon: "◎", label: "Analyse de Race par IA" },
  { icon: "◈", label: "Évaluation du Marché" },
  { icon: "◉", label: "Aperçus de Santé" },
];

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.14, delayChildren: 0.4 },
  },
};

const fadeInUp = {
  hidden: { opacity: 0, y: 40, filter: "blur(12px)" },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 1, ease: [0.16, 1, 0.3, 1] as const },
  },
};

export default function HeroSection() {
  return (
    <section className="relative w-full h-screen overflow-hidden">
      {/* ─── Full-Bleed Video Background ─── */}
      <div className="absolute inset-0 w-full h-full">
        <VideoPlayer src={VIDEO_SRC} />
      </div>

      {/* ─── Subtle Overlay ─── */}
      <div className="absolute inset-0 bg-black/20" />

      {/* ─── Top Vignette ─── */}
      <div className="absolute inset-x-0 top-0 h-32 sm:h-48 bg-gradient-to-b from-black/50 to-transparent pointer-events-none" />

      {/* ─── Bottom Vignette ─── */}
      <div className="absolute inset-x-0 bottom-0 h-32 sm:h-48 bg-gradient-to-t from-black/70 to-transparent pointer-events-none" />

      {/* ─── Hero Content (shifted down slightly) ─── */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative z-10 flex flex-col items-center justify-center h-full px-4 sm:px-6 text-center pt-[15vh] sm:pt-[12vh]"
      >
        {/* Badges */}
        <motion.div
          variants={fadeInUp}
          className="flex flex-wrap items-center justify-center gap-2 sm:gap-3 mb-6 sm:mb-10"
        >
          {badges.map((badge) => (
            <span
              key={badge.label}
              className="glass inline-flex items-center gap-1.5 sm:gap-2.5 px-3 sm:px-5 py-2 sm:py-2.5 rounded-full text-[10px] sm:text-[12px] tracking-[0.1em] uppercase text-white/80 transition-all duration-300 hover:bg-white/10 hover:border-white/20 cursor-default"
            >
              <span className="text-white/50 text-xs sm:text-sm">
                {badge.icon}
              </span>
              {badge.label}
            </span>
          ))}
        </motion.div>

        {/* Headline */}
        <motion.h1
          variants={fadeInUp}
          className="max-w-[880px] text-[36px] sm:text-[52px] md:text-[64px] lg:text-[80px] font-bold leading-[0.95] tracking-[-0.035em] text-white drop-shadow-[0_4px_30px_rgba(0,0,0,0.4)]"
        >
          Où l&apos;Innovation
          <br />
          Rencontre l&apos;Exécution
        </motion.h1>

        {/* Subtext */}
        <motion.div
          variants={fadeInUp}
          className="mt-5 sm:mt-8 max-w-[620px] mx-4"
        >
          <p className="text-[13px] sm:text-[15px] md:text-[16px] leading-[1.65] text-white/80 tracking-[-0.005em]">
            Le système intelligent combinant la vision par ordinateur et l&apos;apprentissage
            automatique pour sécuriser les transactions et identifier la valeur marchande
            équine avec <span className="text-white font-semibold">95% de confiance</span>.
          </p>
        </motion.div>

        {/* Action Buttons */}
        <motion.div
          variants={fadeInUp}
          className="flex flex-col sm:flex-row items-center gap-3 sm:gap-4 mt-12 sm:mt-16 w-full sm:w-auto px-4 sm:px-0"
        >
          <a href="#get-started" className="w-full sm:w-[240px]">
            <ButtonBorder className="w-full h-12 text-[14px]">
              Commencer Gratuitement
            </ButtonBorder>
          </a>
          <a href="#contact" className="w-full sm:w-[240px]">
            <ButtonBorder className="w-full h-12 text-[14px]">
              Entrer en Contact
            </ButtonBorder>
          </a>
        </motion.div>
      </motion.div>

      {/* ─── Logo Marquee ─── */}
      <div className="absolute bottom-0 left-0 right-0 z-20 glass-dark py-3 sm:py-5 overflow-hidden">
        <div className="flex animate-marquee" style={{ width: "200%" }}>
          {[...Array(2)].map((_, setIdx) => (
            <div
              key={setIdx}
              className="flex items-center justify-around flex-1 gap-8 sm:gap-16 px-4 sm:px-10"
            >
              {[
                "Arabian Breeders",
                "EquiTech Labs",
                "Global Stallion",
                "FEI Partners",
                "Thoroughbred Corp",
                "Saddle Analytics",
              ].map((name) => (
                <span
                  key={`${setIdx}-${name}`}
                  className="text-[10px] sm:text-[12px] tracking-[0.18em] uppercase text-white/25 whitespace-nowrap font-medium select-none"
                >
                  {name}
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
