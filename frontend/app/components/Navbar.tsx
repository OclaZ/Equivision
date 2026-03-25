"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import Image from "next/image";
import { ButtonBorder } from "@/components/ui/button-border";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      <motion.nav
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-700 ${
          scrolled || mobileOpen ? "glass-dark" : "bg-transparent"
        }`}
      >
        <div className="max-w-[1920px] mx-auto px-4 sm:px-8 md:px-12 lg:px-16 grid grid-cols-[1fr_auto_1fr] items-center h-[72px] sm:h-[84px] md:h-[96px] xl:h-[110px]">
          {/* Left — Empty spacer (desktop) / Hamburger (mobile) */}
          <div className="flex items-center">
            <button
              className="md:hidden flex flex-col gap-[5px] p-2"
              aria-label="Menu"
              onClick={() => setMobileOpen(!mobileOpen)}
            >
              <span
                className={`w-5 h-[1.5px] bg-white/70 transition-all duration-300 ${
                  mobileOpen ? "rotate-45 translate-y-[3.25px]" : ""
                }`}
              />
              <span
                className={`w-3.5 h-[1.5px] bg-white/40 transition-all duration-300 ${
                  mobileOpen ? "opacity-0" : ""
                }`}
              />
              <span
                className={`w-5 h-[1.5px] bg-white/70 transition-all duration-300 ${
                  mobileOpen ? "-rotate-45 -translate-y-[3.25px]" : ""
                }`}
              />
            </button>
          </div>

          {/* Center — Logo */}
          <div className="flex justify-center">
            <a href="/" className="flex items-center">
              <Image
                src="https://res.cloudinary.com/ddvzn2n7i/image/upload/v1774183125/unnamed-removebg-preview_hvqlqb.png"
                alt="EquiVision"
                width={220}
                height={60}
                className="h-[50px] sm:h-[65px] md:h-[80px] xl:h-[95px] w-auto brightness-0 invert transition-all duration-300"
                priority
              />
            </a>
          </div>

          <div className="flex items-center justify-end gap-2 sm:gap-3">
            <a href="/login" className="hidden md:block">
              <ButtonBorder className="w-[110px]">
                Connexion
              </ButtonBorder>
            </a>
            <a href="/register" className="hidden md:block">
              <ButtonBorder className="w-[110px]">
                S&apos;inscrire
              </ButtonBorder>
            </a>
          </div>
        </div>
      </motion.nav>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-x-0 top-[64px] sm:top-[72px] z-40 glass-dark md:hidden"
          >
            <div className="flex flex-col items-center gap-3 py-6 px-6">
              <a href="/login" className="w-full">
                <ButtonBorder className="w-full">
                  Connexion
                </ButtonBorder>
              </a>
              <a href="/register" className="w-full">
                <ButtonBorder className="w-full">
                  S&apos;inscrire
                </ButtonBorder>
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
