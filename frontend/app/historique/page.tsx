"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/ui/sidebar";
import {
  Search,
  Grid,
  List as ListIcon,
  Filter,
  ArrowUpDown,
  BarChart3
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { getNavLinks } from "@/lib/constants";
import { GlassBlogCard } from "@/components/ui/glass-blog-card-shadcnui";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { apiFetch, BASE_URL } from "@/lib/api";
import { motion } from "framer-motion";

interface Prediction {
  id: number;
  predicted_breed: string;
  breed_confidence: number;
  estimated_price: number;
  image_url: string;
  input_breed: string;
  input_age: number;
  input_gender: string;
  input_height: number;
  created_at: string;
}

export default function HistoriquePage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [view, setView] = useState<"grid" | "list">("grid");
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    } else if (user) {
      fetchPredictions();
    }
  }, [user, authLoading, router]);

  const fetchPredictions = async () => {
    try {
      const data = await apiFetch("/predictions/");
      setPredictions(data);
    } catch (error) {
      console.error("Error fetching predictions:", error);
    } finally {
      setLoading(false);
    }
  };

  if (authLoading || !user) {
    return <div className="min-h-screen bg-black flex items-center justify-center text-white">Initialisation du terminal...</div>;
  }

  const links = getNavLinks("/historique");

  const filteredPredictions = predictions.filter(p => 
    p.predicted_breed?.toLowerCase().includes(searchQuery.toLowerCase()) || 
    p.input_breed?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.input_gender?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex w-full h-screen bg-[#050505] text-white font-geist overflow-hidden p-6 lg:px-12 lg:py-10 gap-10">
      
      {/* ── Background Noise Texture ── */}
      <div 
        className="absolute inset-0 z-0 opacity-[0.03] pointer-events-none mix-blend-overlay"
        style={{ backgroundImage: "url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.85%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E')" }}
      />

      <Sidebar links={links} />

      {/* ── Main Content ── */}
      <main className="flex-1 relative overflow-y-auto custom-scrollbar flex flex-col items-center z-10 animate-in fade-in slide-in-from-bottom-2 duration-700">
        <div className="max-w-[1600px] w-full mx-auto px-12 pt-20 pb-32 min-h-full flex flex-col">
          
          {/* ═══ Header Section ═══ */}
          <header className="flex flex-col gap-6 mb-16 mt-8 font-heading">
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-3">
                 <div className="h-6 w-6 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
                    <BarChart3 size={14} className="text-emerald-400" />
                 </div>
                 <span className="text-[10px] font-bold tracking-[0.35em] text-emerald-400 uppercase">Archive Alpha-Data</span>
              </div>
              <h1 className="text-[48px] lg:text-[72px] font-extrabold text-white tracking-[-0.04em] leading-tight">
                Historique <span className="text-white/20 italic">des Analyses</span>
              </h1>
              <p className="text-[14px] text-white/40 tracking-wide font-normal max-w-2xl mt-2">
                Consultez le registre complet des spécimens analysés par le terminal EquiVision-Alpha. 
                Toutes les données sont synchronisées en temps réel avec le serveur central.
              </p>
            </div>
          </header>

          {/* ═══ Page Management Hub ═══ */}
          <div className="flex flex-col gap-10">
            
             {/* Stats Bar */}
             <div className="grid grid-cols-1 md:grid-cols-3 gap-10 mb-12">
                <div className="stat-card-premium">
                   <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500/10 group-hover:bg-emerald-500/20 transition-colors" />
                   <span className="text-[11px] font-bold tracking-[0.4em] text-white/40 uppercase pl-2">Analyses Totales</span>
                   <div className="flex items-baseline gap-2 pl-2">
                     <span className="text-6xl font-extrabold text-white tracking-tighter font-heading">{predictions.length}</span>
                     <span className="text-emerald-400 text-[12px] font-bold font-mono tracking-widest pl-2">+12.4%</span>
                   </div>
                </div>
                <div className="stat-card-premium">
                   <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500/10 group-hover:bg-emerald-500/20 transition-colors" />
                   <span className="text-[11px] font-bold tracking-[0.4em] text-white/40 uppercase pl-2">Confiance Moyenne</span>
                   <div className="flex items-baseline gap-2 pl-2">
                     <span className="text-6xl font-extrabold text-white tracking-tighter font-heading">
                       {predictions.length > 0 
                         ? (predictions.reduce((acc, p) => acc + p.breed_confidence, 0) / predictions.length * 100).toFixed(1) 
                         : "0.0"}
                     </span>
                     <span className="text-emerald-400 text-2xl font-bold font-mono tracking-tighter">%</span>
                   </div>
                </div>
                <div className="stat-card-premium">
                   <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500/10 group-hover:bg-emerald-500/20 transition-colors" />
                   <span className="text-[11px] font-bold tracking-[0.4em] text-white/40 uppercase pl-2">Valorisation Alpha</span>
                   <div className="flex items-baseline gap-3 pl-2">
                     <span className="text-5xl font-extrabold text-white tracking-tighter font-heading">
                       {predictions.reduce((acc, p) => acc + (p.estimated_price * 10.5 || 0), 0).toLocaleString()} 
                     </span>
                     <span className="text-[12px] text-white/30 font-bold tracking-widest uppercase mb-1">MAD</span>
                   </div>
                </div>
             </div>

            {/* Management Controls */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-10 card-premium !p-10 !px-16 mb-12">
              <div className="flex-1 max-w-xl relative group">
                <Search size={18} className="absolute left-6 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-emerald-400 transition-colors z-10" />
                <input 
                  type="text" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Rechercher par race, sexe ou ID..." 
                  className="input-premium !pl-16 !h-14"
                />
              </div>

              <div className="flex items-center gap-4">
                <Button variant="outline" size="icon" className="h-12 w-12 rounded-xl border border-white/5 flex items-center justify-center text-white/40 hover:text-white hover:bg-white/5 transition-all">
                   <Filter size={18} />
                </Button>
                <Button variant="outline" size="icon" className="h-12 w-12 rounded-xl border border-white/5 flex items-center justify-center text-white/40 hover:text-white hover:bg-white/5 transition-all">
                   <ArrowUpDown size={18} />
                </Button>
                <div className="h-8 w-px bg-white/5 mx-2" />
                <div className="flex gap-2 bg-black/40 p-1.5 rounded-xl border border-white/5">
                  <Button 
                    onClick={() => setView("grid")} 
                    variant={view === 'grid' ? 'default' : 'premium-ghost'}
                    className={cn(
                      "h-10 px-6 rounded-lg flex items-center gap-2 text-[10px] font-bold tracking-[0.1em] transition-all",
                      view === 'grid' ? "bg-white text-black hover:bg-white/90" : ""
                    )}
                  >
                    <Grid size={14} /> GRILLE
                  </Button>
                  <Button 
                    onClick={() => setView("list")} 
                    variant={view === 'list' ? 'default' : 'premium-ghost'}
                    className={cn(
                      "h-10 px-6 rounded-lg flex items-center gap-2 text-[10px] font-bold tracking-[0.1em] transition-all",
                      view === 'list' ? "bg-white text-black hover:bg-white/90" : ""
                    )}
                  >
                    <ListIcon size={14} /> LISTE
                  </Button>
                </div>
              </div>
            </div>

            {/* List Results */}
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="h-80 rounded-[2rem] bg-white/[0.02] border border-white/5 animate-pulse" />
                ))}
              </div>
            ) : filteredPredictions.length === 0 ? (
              <div className="py-32 flex flex-col items-center justify-center text-center gap-4">
                 <div className="w-16 h-16 rounded-full bg-white/[0.02] border border-white/5 flex items-center justify-center text-white/10">
                    <Search size={32} />
                 </div>
                 <div className="space-y-1">
                    <p className="text-white font-bold tracking-tight">Aucun résultat trouvé</p>
                    <p className="text-white/30 text-[12px]">Essayez de modifier vos critères de recherche.</p>
                 </div>
              </div>
            ) : (
              <motion.div 
                layout
                className={view === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10" : "flex flex-col gap-10"}
              >
                {filteredPredictions.map((scan, index) => (
                  <motion.div
                    key={scan.id}
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                  >
                    <GlassBlogCard 
                      title={scan.predicted_breed || scan.input_breed || "Inconnu"}
                      excerpt={`Spécimen EQ-${scan.id.toString().padStart(4, '0')} • Estimé à ${(scan.estimated_price * 10.5).toLocaleString()} MAD`}
                      image={scan.image_url ? (scan.image_url.startsWith("http") ? scan.image_url : `${BASE_URL}${scan.image_url}`) : "https://images.unsplash.com/photo-1553284965-83fd3e82fa5a?w=800&q=80"}
                      author={{
                        name: "Alpha-Core",
                        avatar: "https://ui-avatars.com/api/?name=EV&background=0D8ABC&color=fff"
                      }}
                      date={new Date(scan.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
                      readTime={`${scan.input_age || '?'} ans • ${scan.input_height || '?'} m`}
                      tags={[scan.input_gender || "N/A", `${(scan.breed_confidence * 100).toFixed(0)}%`]}
                      className="max-w-none transition-all duration-500 hover:scale-[1.03] hover:shadow-[0_40px_80px_rgba(0,0,0,0.4)]"
                    />
                  </motion.div>
                ))}
              </motion.div>
            )}
          </div>

        </div>
      </main>

    </div>
  );
}