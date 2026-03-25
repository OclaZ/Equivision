"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/ui/sidebar";
import {
  Upload,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";

import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";
import { getNavLinks } from "@/lib/constants";
import Image from "next/image";

interface ImageAnalysisResult {
  id: number;
  breed: string;
  confidence: number;
  all_probabilities?: Record<string, number>;
  detection?: {
    bbox: number[];
    label: string;
    confidence: number;
  };
  image_url: string;
  created_at: string;
  error?: string;
}

export default function ImageAnalysisPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  
  const [mounted, setMounted] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [result, setResult] = useState<ImageAnalysisResult | null>(null);
  const [step, setStep] = useState(1);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router, mounted]);

  const handleFile = (file: File) => {
    if (file && file.type.startsWith("image/")) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setStep(1);
      setResult(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setStep(2);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const data = await apiFetch("/predict/breed", {
        method: "POST",
        data: formData,
      });

      setResult(data);
      setStep(3);
    } catch (error) {
      console.error("Image analysis failed:", error);
      alert("L'analyse d'image a échoué.");
      setStep(1);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Prevent hydration mismatch by returning a consistent loading state on first render
  if (!mounted || authLoading || !user) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center text-white">
        <div className="flex flex-col items-center gap-6">
          <div className="h-1 lg:h-2 w-48 bg-white/5 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-500 w-1/3 animate-[loading_2s_ease-in-out_infinite]" />
          </div>
          <span className="text-[10px] font-bold tracking-[0.4em] text-white/20 uppercase">Initialisation du Système...</span>
        </div>
      </div>
    );
  }

  const links = getNavLinks(pathname);
  const hasHorseError = result?.error && result.error.includes("No horse detected");

  return (
    <div className="flex w-full h-screen bg-[#050505] text-white font-geist overflow-hidden p-6 lg:px-12 lg:py-10 gap-10">
      <div 
        className="absolute inset-0 z-0 opacity-[0.03] pointer-events-none mix-blend-overlay"
        style={{ backgroundImage: "url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.85%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E')" }}
      />
      
      <Sidebar links={links} />

      <main className="flex-1 relative overflow-y-auto custom-scrollbar flex flex-col items-center justify-center z-10 animate-in fade-in slide-in-from-bottom-2 duration-700">
        <div className="max-w-[1600px] w-full mx-auto px-12 pt-20 pb-32 min-h-full flex flex-col justify-center">
          
          <div className="w-full flex flex-col gap-16">
            <header className="flex flex-col gap-12 text-center lg:text-left">
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-center lg:justify-start gap-3">
                  <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_10px_#10B981] animate-pulse" />
                  <span className="text-[11px] font-bold tracking-[0.35em] text-white/30 uppercase">Scan-Node 01 — Vision Terminal</span>
                </div>
                <h1 className="text-[48px] lg:text-[72px] font-extrabold text-white tracking-[-0.04em] leading-tight font-heading italic">
                  Analyse <span className="text-white/20 not-italic font-bold">Morphologique</span>
                </h1>
                <p className="text-[14px] text-white/40 tracking-wide font-medium max-w-2xl mx-auto lg:mx-0 leading-relaxed opacity-60">Identification de race et détection de spécimens par vision EquiVision-Alpha. Algorithmes de segmentation en temps-réel activés.</p>
              </div>

               <div className="flex items-center justify-center lg:justify-start gap-8 mt-2 card-premium !p-6 !px-10 !rounded-full w-fit mx-auto lg:mx-0">
                 {[
                   { id: 1, label: "DONNÉES" },
                   { id: 2, label: "ANALYSE" },
                   { id: 3, label: "RÉSULTATS" }
                 ].map((s, idx) => (
                   <React.Fragment key={s.id}>
                      <div className="flex items-center gap-3">
                         <div className={`h-8 w-8 rounded-full flex items-center justify-center text-[12px] font-bold transition-all ${step >= s.id ? "bg-emerald-500 text-black shadow-[0_0_15px_rgba(16,185,129,0.5)]" : "border border-white/10 text-white/20"}`}>
                            {step > s.id ? <CheckCircle2 size={16} /> : s.id}
                         </div>
                         <span className={`text-[10px] font-bold tracking-[0.2em] transition-colors hidden sm:inline ${step >= s.id ? "text-white" : "text-white/20"}`}>{s.label}</span>
                      </div>
                      {idx < 2 && <div className="h-[1px] w-12 bg-white/5" />}
                   </React.Fragment>
                 ))}
              </div>
            </header>

            <div className="flex flex-col gap-16 w-full">
              {step < 3 ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 w-full">
                   {/* Upload Area */}
                   <div 
                      className={`relative card-premium !p-0 border-2 border-dashed flex flex-col items-center justify-center min-h-[500px] cursor-pointer overflow-hidden transition-all duration-500 ${dragActive ? "border-emerald-500/50 bg-emerald-500/[0.08] shadow-emerald-500/20" : "border-white/10 hover:border-white/30"}`}
                      onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                      onDragLeave={() => setDragActive(false)}
                      onDrop={(e) => { e.preventDefault(); setDragActive(false); if(e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]) }}
                      onClick={() => document.getElementById('file-upload')?.click()}
                    >
                      {previewUrl ? (
                         <div className="absolute inset-0 w-full h-full p-2">
                            <div className="relative w-full h-full rounded-[2.2rem] overflow-hidden border border-white/10 shadow-2xl">
                               <Image src={previewUrl} alt="Preview" fill className="object-cover" />
                               <div className="absolute top-6 right-6 z-10">
                                  <Button 
                                   onClick={(e) => { e.stopPropagation(); setSelectedFile(null); setPreviewUrl(null); }}
                                   variant="premium-ghost"
                                   className="px-8 py-4 bg-black/70 backdrop-blur-xl border border-white/15 text-white text-[10px] font-bold uppercase rounded-full hover:bg-red-500 hover:border-red-500 transition-all shadow-2xl tracking-widest h-auto">
                                   Supprimer
                                  </Button>
                               </div>
                            </div>
                         </div>
                      ) : (
                        <div className="flex flex-col items-center gap-10">
                          <div className="h-28 w-28 rounded-full bg-white/5 flex items-center justify-center border border-white/10 shadow-inner">
                            <Upload className="text-white/20" size={40} />
                          </div>
                          <div className="flex flex-col items-center gap-3">
                            <span className="text-white font-bold text-lg tracking-[0.05em] uppercase text-center font-heading">Capture Vision</span>
                            <span className="text-white/20 text-[11px] font-bold tracking-[0.3em] uppercase">PNG, JPG, WEBP — MAX 10MB</span>
                          </div>
                           <Button variant="premium-outline" className="!h-14 !px-10 rounded-xl">
                             Parcourir
                           </Button>
                        </div>
                      )}
                      <input id="file-upload" type="file" className="hidden" accept="image/*" onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
                   </div>

                   {/* Info/Action Card */}
                   <div className="card-premium !p-16 flex flex-col justify-between">
                      <div className="flex flex-col gap-10">
                        <div className="flex items-center gap-4 border-b border-white/5 pb-8 mb-4">
                           <div className="h-12 w-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                             <ChevronRight size={24} />
                           </div>
                           <div className="flex flex-col">
                             <span className="text-[10px] font-bold tracking-[0.3em] text-white/30 uppercase">Protocole d&apos;analyse</span>
                             <span className="text-white font-bold text-lg">Identification Automatisée</span>
                           </div>
                        </div>
                        
                        <div className="space-y-6">
                           <p className="text-white/40 text-sm leading-relaxed">
                             Le système utilise des modèles de deep learning pour segmenter le sujet et identifier les caractéristiques morphologiques clés. 
                             <br/><br/>
                             Assurez-vous que le sujet est entièrement visible sur un fond contrasté pour une précision optimale dépassant 98%.
                           </p>
                        </div>
                      </div>

                      <Button 
                        onClick={handleAnalyze}
                        disabled={!selectedFile || isAnalyzing}
                        variant="premium"
                        className="w-full mt-16 !h-16 text-lg"
                      >
                        {isAnalyzing ? "CHARGEMENT DES RÉSEAUX..." : "LANCER L'IDENTIFICATION"} <ChevronRight size={20} className="ml-2" />
                      </Button>
                   </div>
                </div>
              ) : (
                <div className="animate-in fade-in zoom-in duration-500">
                  <div className="card-premium !p-20 relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-8">
                         <div className="flex items-center gap-2">
                             <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                             <span className="text-[10px] font-bold tracking-[0.3em] text-white/40 uppercase">Statut: Analyse Complétée</span>
                         </div>
                      </div>

                      <div className="grid grid-cols-1 xl:grid-cols-2 gap-16 mt-4">
                        {/* Image Visualization */}
                        <div className="relative h-full min-h-[500px] rounded-[32px] overflow-hidden border border-white/10 bg-black/40 shadow-2xl">
                           {previewUrl && <Image src={previewUrl} alt="Analyzed specimen" fill className={`object-cover ${hasHorseError ? 'grayscale contrast-125' : ''}`} unoptimized={true} />}
                           <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent" />
                           
                           {/* BBox visualization removed as per user request */}

                           {hasHorseError && (
                            <div className="absolute inset-0 flex items-center justify-center bg-red-900/40 backdrop-blur-sm z-30">
                               <div className="bg-red-600 text-white px-8 py-4 rounded-2xl flex items-center gap-3 shadow-2xl animate-pulse">
                                  <AlertCircle size={24} />
                                  <span className="font-bold tracking-widest uppercase text-xs">Alerte: Aucun sujet détecté</span>
                               </div>
                            </div>
                           )}

                           <div className="absolute bottom-10 left-10 flex flex-col gap-1">
                              <span className="text-[10px] font-bold tracking-[0.3em] text-white/40 uppercase">Specimen Trace</span>
                              <span className="text-white font-mono text-lg tracking-wider">#EV-{result?.id || 'ALPHA-01'}</span>
                           </div>
                        </div>

                        {/* Results Summary */}
                        <div className="flex flex-col justify-between h-full">
                           <div className="flex flex-col gap-8">
                              
                               {/* Result Card */}
                               <div className="stat-card-premium !p-12 !border-none !bg-white/[0.02]">
                                  <label className="text-[10px] font-bold tracking-[0.3em] text-white/30 uppercase mb-5 block flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-emerald-500" />
                                    Identification
                                  </label>
                                  <div className="flex flex-col gap-2">
                                     <h2 className={`text-4xl lg:text-7xl font-extrabold tracking-tighter font-heading ${hasHorseError ? 'text-red-500' : 'text-emerald-400'}`}>
                                       {hasHorseError ? "INDÉTERMINÉ" : result?.breed || "INCONNU"}
                                     </h2>
                                     <span className="text-white/40 text-[12px] font-bold tracking-[0.1em] mt-2 bg-white/5 px-4 py-1.5 rounded-full w-fit">
                                       {hasHorseError ? "0.0%" : (result?.confidence ? result.confidence * 100 : 0).toFixed(1)}% DE CONFIANCE
                                     </span>
                                  </div>
                               </div>

                                {!hasHorseError && (
                                  <div className="flex flex-col gap-6">
                                     <h3 className="text-[10px] font-bold tracking-[0.3em] text-white/20 uppercase pl-2">Analyse Probabiliste</h3>
                                      <div className="grid grid-cols-1 gap-3">
                                         {Object.entries(result?.all_probabilities || {})
                                           .sort(([,a], [,b]) => (b as number) - (a as number))
                                           .slice(1, 4)
                                           .map(([key, value]) => (
                                             <div key={key} className="flex items-center justify-between p-8 rounded-[1.25rem] bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-colors">
                                                <span className="text-white/60 text-xs font-bold tracking-widest uppercase">{key.replace('_', ' ')}</span>
                                                <div className="flex items-center gap-4">
                                                  <div className="h-1 w-24 bg-white/5 rounded-full overflow-hidden hidden sm:block">
                                                    <div className="h-full bg-emerald-500/50" style={{ width: `${(value as number) * 100}%` }} />
                                                  </div>
                                                  <span className="text-white/30 text-[11px] font-mono">{(value as number * 100).toFixed(1)}%</span>
                                                </div>
                                             </div>
                                           ))}
                                      </div>
                                  </div>
                                )}
                           </div>

                            <div className="flex gap-4 mt-24 pt-10 border-t border-white/5">
                               <Button 
                                 onClick={() => { setStep(1); setResult(null); }}
                                 variant="premium-outline"
                                 className="!flex-1 h-14"
                                >
                                 Nouvelle Analyse
                               </Button>
                               <Button 
                                 onClick={() => router.push("/historique")}
                                 variant="premium"
                                 className="!flex-1 h-14"
                               >
                                 Vers Historique
                               </Button>
                            </div>
                        </div>
                      </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
      
      <style jsx global>{`
        @keyframes loading {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(300%); }
        }
      `}</style>
    </div>
  );
}
