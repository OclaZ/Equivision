"use client";

import React from "react";
import { Sidebar } from "@/components/ui/sidebar";
import {
  Bell,
  Search,
  ChevronRight,
  Crosshair,
} from "lucide-react";
import { Button } from "@/components/ui/button";

import { getNavLinks } from "@/lib/constants";
import { motion } from "framer-motion";

import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [stats, setStats] = React.useState({ totalScans: 0 });
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    } else if (user) {
      fetchStats();
    }
  }, [user, authLoading, router]);

  const fetchStats = async () => {
    try {
      const predictions = await apiFetch("/predictions/");
      setStats({
        totalScans: predictions.length
      });
    } catch (error) {
      console.error("Failed to fetch dashboard stats:", error);
    } finally {
      setLoading(false);
    }
  };

  if (authLoading || !user) {
    return <div className="min-h-screen bg-black flex items-center justify-center text-white">Authentification...</div>;
  }

  const links = getNavLinks(pathname);

  return (
    <div className="flex w-full h-screen bg-[#050505] text-white font-geist overflow-hidden p-6 lg:px-12 lg:py-10 gap-10 relative">
      
      {/* ── Background Noise Texture ── */}
      <div 
        className="absolute inset-0 z-0 opacity-[0.03] pointer-events-none mix-blend-overlay"
        style={{ backgroundImage: "url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.85%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E')" }}
      />

      <Sidebar links={links} />

      {/* ── Main content wrapper ── */}
      <main className="flex-1 relative overflow-y-auto custom-scrollbar flex flex-col items-center justify-center z-10">
        <div className="max-w-[1600px] w-full mx-auto px-12 pt-20 pb-24 min-h-full flex flex-col justify-center">
          
          {/* Main Layout Gap Increased to gap-16 */}
           <motion.div 
             initial="hidden"
             animate="visible"
             variants={{
               hidden: { opacity: 0 },
               visible: {
                 opacity: 1,
                 transition: {
                   staggerChildren: 0.1,
                   delayChildren: 0.2
                 }
               }
             }}
             className="w-full flex flex-col xl:flex-row gap-16"
           >
           
            {/* ═══ LEFT MAIN COLUMN ═══ */}
            <div className="flex-1 flex flex-col gap-12 w-full">
              
              {/* Header */}
              <motion.header 
                 variants={{
                   hidden: { opacity: 0, y: 20 },
                   visible: { opacity: 1, y: 0 }
                 }}
                 className="flex flex-col gap-4"
               >
                <div className="flex items-center gap-3">
                  <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_10px_#10B981] animate-pulse" />
                  <span className="text-[10px] font-bold tracking-[0.35em] text-white/30 uppercase">Système de Bord Alpha-V7</span>
                </div>
                <h1 className="text-[48px] lg:text-[64px] font-extrabold text-white tracking-[-0.04em] leading-none font-heading italic">
                  Bonjour {user.username}.
                </h1>
                <p className="text-[14px] text-white/40 tracking-wide font-medium max-w-lg">
                  Statut des systèmes biométriques et flux de marché synchronisés. <br />
                  Dernier rafraîchissement à l&apos;instant.
                </p>
              </motion.header>

              {/* ── Visual Anchor: The Biometric Terminal ── */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                <div 
                  className="card-premium rounded-[2.5rem] relative overflow-hidden group cursor-pointer" 
                  onClick={() => router.push('/image-analysis')}
                >
                  <div className="flex gap-6 items-center">
                    <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center text-3xl shadow-inner border border-white/5">🖼️</div>
                    <div>
                      <h4 className="text-[10px] font-bold tracking-[0.25em] text-emerald-400 uppercase mb-1">Module Vision</h4>
                      <h3 className="text-xl font-bold text-white font-heading">Analyse Image</h3>
                      <p className="text-[13px] text-white/30 mt-1">Identification par morphologie IA</p>
                    </div>
                  </div>
                </div>
                
                <div 
                  className="card-premium rounded-[2.5rem] relative overflow-hidden group cursor-pointer" 
                  onClick={() => router.push('/marche')}
                >
                  <div className="flex gap-6 items-center">
                    <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center text-3xl shadow-inner border border-white/5">💰</div>
                    <div>
                      <h4 className="text-[10px] font-bold tracking-[0.25em] text-emerald-400 uppercase mb-1">Module Marché</h4>
                      <h3 className="text-xl font-bold text-white font-heading">Analyse Prix</h3>
                      <p className="text-[13px] text-white/30 mt-1">Estimation de valeur vénale</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Main Analysis Banner */}
              <div className="card-premium rounded-[2.5rem] relative overflow-hidden group mt-16">
                <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                
                <div className="flex flex-col md:flex-row gap-10 items-start md:items-center justify-between">
                  <div className="flex gap-8 items-center">
                    {/* Scanner Element */}
                    <div 
                      className="relative w-[120px] h-[120px] shrink-0 flex items-center justify-center bg-black/40 rounded-xl border border-white/5 overflow-hidden shadow-inner cursor-pointer" 
                      onClick={() => router.push('/prediction')}
                    >
                      <div className="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-transparent to-[#10B981]/20 border-b border-[#10B981]/50 origin-top animate-[ping_4s_linear_infinite]" />
                      <Crosshair className="text-white/10 absolute z-0" size={80} strokeWidth={0.5} />
                      <span className="absolute z-10 text-5xl opacity-80 mix-blend-screen grayscale contrast-125">🐴</span>
                    </div>
                    
                    <div className="flex flex-col gap-1.5">
                      <h4 className="text-[11px] font-medium tracking-[0.18em] text-white/25 uppercase flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] shadow-[0_0_10px_#10B981] animate-pulse" />
                        Système Intégré
                      </h4>
                      <h2 className="text-[28px] font-bold tracking-[-0.02em] text-white leading-tight">Analyse Complète</h2>
                      <p className="text-[14px] text-white/40 tracking-wide font-normal">Identité + Valeur en une capture</p>
                    </div>
                  </div>
                  
                  <div className="flex md:flex-col gap-6 md:gap-8 items-center md:items-end w-full md:w-auto shrink-0">
                    <Button 
                      onClick={() => router.push('/prediction')}
                      variant="premium"
                      className="w-full md:w-[240px] !h-14"
                    >
                      Nouvelle Analyse
                    </Button>
                  </div>
                </div>
              </div>

              {/* ── Recent Activity ── */}
              <div className="card-premium rounded-[2.5rem] flex flex-col gap-10 mt-16">
                <div className="flex items-center justify-between border-b border-white/5 pb-8">
                  <h2 className="text-[17px] font-bold text-white tracking-[0.05em] font-heading uppercase">Log d&apos;Activités</h2>
                </div>

                <div className="flex flex-col">
                  <div className="flex items-center justify-center py-12 text-white/20 font-bold uppercase tracking-widest text-[10px]">
                    {loading ? 'Synchronisation des flux...' : 'Aucune activité récente détectée'}
                  </div>
                </div>
              </div>

            </div>

            {/* ═══ RIGHT METRICS COLUMN ═══ */}
            <div className="w-full xl:w-[420px] shrink-0 flex flex-col gap-10">
              
              {/* Top Minimal Search/Nav */}
              <div className="h-20 flex items-center justify-between px-8 card-premium !rounded-full !p-0 px-8">
                <div className="flex gap-4 items-center text-white/40 group w-full max-w-[240px]">
                  <Search size={18} className="group-focus-within:text-emerald-400 transition-colors" />
                  <input 
                    type="text" 
                    placeholder="Recherche..." 
                    className="bg-transparent border-none text-[14px] outline-none text-white placeholder:text-white/20 w-full font-medium focus:ring-0"
                  />
                </div>
                <div className="flex gap-6 items-center shrink-0">
                  <div className="relative cursor-pointer group/bell">
                    <Bell size={20} className="text-white/40 group-hover/bell:text-white transition-colors" />
                    <div className="absolute top-0 right-0 w-2 h-2 rounded-full bg-[#EF4444] border-2 border-black" />
                  </div>
                  <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-[12px] font-bold text-emerald-400 tracking-wider hover:bg-emerald-500/20 transition-all cursor-pointer border border-emerald-500/20 shadow-lg active:scale-95">
                    {user.username.slice(0, 2).toUpperCase()}
                  </div>
                </div>
              </div>

              {/* Stat Grid */}
              <div className="grid grid-cols-2 gap-8">
                <div 
                  className="stat-card-premium !p-12 flex flex-col justify-center gap-6 cursor-pointer" 
                  onClick={() => router.push('/historique')}
                >
                  <h4 className="text-[11px] font-bold tracking-[0.25em] text-emerald-400/50 uppercase">Total Scans</h4>
                  <div>
                    <span className="text-[48px] font-extrabold text-white tracking-tighter leading-none block font-heading italic">
                      {loading ? '...' : stats.totalScans}
                    </span>
                  </div>
                </div>
                
                <div className="stat-card-premium !p-12 flex flex-col justify-center gap-6">
                  <h4 className="text-[11px] font-bold tracking-[0.25em] text-emerald-400/50 uppercase">Précision</h4>
                  <div className="flex items-baseline gap-2">
                    <span className="text-[48px] font-extrabold text-white tracking-tighter leading-none font-heading italic">94.8</span>
                    <span className="text-[20px] text-emerald-400/50 font-bold">%</span>
                  </div>
                </div>
              </div>

              {/* Technical Chart */}
              <div className="card-premium !p-8 flex flex-col flex-1 min-h-[380px]">
                <div className="flex items-center justify-between mb-8">
                  <h3 className="text-[15px] font-semibold text-white tracking-[-0.01em]">Volumes du Marché</h3>
                  <div 
                    className="flex items-center gap-1 text-[11px] font-medium tracking-[0.18em] text-white/40 hover:text-white uppercase cursor-pointer transition-colors" 
                    onClick={() => router.push('/marche')}
                  >
                    Actualiser
                    <ChevronRight size={14} />
                  </div>
                </div>

                <div className="relative w-full h-[180px] mt-auto">
                  <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
                    {[...Array(4)].map((_, i) => (
                      <div key={i} className="w-full flex items-center gap-4">
                        <span className="text-[10px] text-white/20 font-mono w-4">{(3 - i) * 3}k</span>
                        <div className="flex-1 border-t border-white/[0.03]" />
                      </div>
                    ))}
                  </div>

                  <svg className="absolute inset-0 w-full h-full pt-2 object-visible overflow-visible" viewBox="0 0 300 150" preserveAspectRatio="none">
                    <path 
                      d="M 28 120 C 60 120, 100 80, 150 110 C 200 130, 240 40, 298 60" 
                      fill="none" 
                      stroke="rgba(255,255,255,0.05)" 
                      strokeWidth="2" 
                      strokeLinecap="round" 
                    />
                    <path 
                      d="M 28 120 C 60 120, 100 80, 150 110 C 200 130, 240 40, 298 60" 
                      fill="none" 
                      stroke="white" 
                      strokeWidth="2" 
                      strokeLinecap="round" 
                      style={{ filter: "drop-shadow(0px 4px 6px rgba(255,255,255,0.2))" }}
                      className="opacity-80 group-hover:opacity-100 transition-opacity"
                    />
                    <circle cx="150" cy="110" r="3" fill="#000" stroke="white" strokeWidth="2" />
                    <circle cx="298" cy="60" r="3" fill="#000" stroke="white" strokeWidth="2" />
                  </svg>
                </div>

                <div className="flex justify-between items-center mt-8 pt-6 border-t border-white/[0.05]">
                  <div className="text-[10px] font-mono text-white/30 uppercase tracking-widest">Sys_Status: NominaL</div>
                  <div className="w-1.5 h-1.5 rounded-full bg-[#10B981] shadow-[0_0_8px_#10B981]" />
                </div>
              </div>

            </div>
          </motion.div>
        </div>
      </main>

    </div>
  );
}