"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Upload, ChevronRight, Info, CheckCircle2, AlertCircle } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";
import { Sidebar } from "@/components/ui/sidebar";
import { getNavLinks } from "@/lib/constants";
import { Button } from "@/components/ui/button";

interface PredictionResult {
  id: number | null;
  predicted_breed: string;
  breed_confidence: number;
  estimated_price: number;
  price_min: number;
  price_max: number;
  age: number | null;
  gender: string | null;
  height: number | null;
  created_at: string | null;
  warning?: string;
}

export default function PredictionPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  
  const [step, setStep] = useState(1);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  
  const [metadata, setMetadata] = useState<{ genders?: string[] } | null>(null);
  const [age, setAge] = useState<string>("");
  const [gender, setGender] = useState<string>("Mare");
  const [height, setHeight] = useState<string>("");

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const data = await apiFetch("/metadata");
        setMetadata(data);
      } catch (error) {
        console.error("Failed to fetch metadata:", error);
      }
    };
    fetchMetadata();
  }, []);

  const handleFile = (file: File) => {
    if (file && file.type.startsWith("image/")) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setStep(1);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setIsAnalyzing(true);
    setStep(2);
    
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      
      if (age) {
        const parsedAge = parseInt(age);
        if (!isNaN(parsedAge)) formData.append("age", parsedAge.toString());
      }
      
      if (gender) {
        formData.append("gender", gender);
      }
      
      if (height) {
        const parsedHeight = parseFloat(height.toString().replace(',', '.'));
        if (!isNaN(parsedHeight)) formData.append("height", parsedHeight.toString());
      }
      
      const data = await apiFetch("/predict/complete", {
        method: "POST",
        data: formData,
      });

      setResult(data);
      setStep(3);
    } catch (error: unknown) {
      console.error("Analysis failed:", error);
      const errorMessage = error instanceof Error ? error.message : "L'analyse a échoué. Veuillez vérifier les données biométriques.";
      alert(errorMessage);
      setStep(1);
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (authLoading || !user) {
    return <div className="min-h-screen bg-black flex items-center justify-center text-white font-medium tracking-widest uppercase text-xs">Initialisation du terminal...</div>;
  }

  const links = getNavLinks("/prediction");

  return (
    <div className="flex w-full h-screen bg-[#050505] text-white font-geist overflow-hidden p-6 lg:px-12 lg:py-10 gap-10">
      <div 
        className="absolute inset-0 z-0 opacity-[0.03] pointer-events-none mix-blend-overlay"
        style={{ backgroundImage: "url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.85%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E')" }}
      />

      <Sidebar links={links} />

      <main className="flex-1 relative overflow-y-auto custom-scrollbar flex flex-col items-center justify-center z-10 animate-in fade-in slide-in-from-bottom-2 duration-700">
        <div className="max-w-[1600px] w-full mx-auto px-12 pt-20 pb-24 min-h-full flex flex-col justify-center">
          
          <div className="w-full flex flex-col gap-16">
            <header className="flex flex-col gap-12">
               <div className="flex flex-col gap-4">
                <h1 className="text-[48px] lg:text-[72px] font-extrabold text-white tracking-[-0.04em] leading-tight text-center lg:text-left font-heading italic">
                  Terminal <span className="text-white/20">de Prédiction</span>
                </h1>
                <p className="text-[14px] text-white/40 tracking-wide font-medium text-center lg:text-left opacity-60">Analyse avancée par vision artificielle EquiVision-Alpha.</p>
              </div>

              <div className="flex items-center justify-center lg:justify-start gap-8 mt-2 card-premium !p-6 !px-10 !rounded-full w-fit">
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
                <>
                   <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 w-full">
                     {/* Upload Card */}
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
                        <div className="flex flex-col items-center gap-6 text-center px-6">
                          <div className="h-20 w-20 rounded-full bg-white/[0.03] border border-white/5 flex items-center justify-center text-white/20">
                            <Upload size={32} strokeWidth={1.5} />
                          </div>
                           <div className="flex flex-col gap-4">
                              <h3 className="text-2xl font-extrabold text-white tracking-tight font-heading">CAPTURE VISION</h3>
                              <p className="text-[12px] text-white/20 uppercase tracking-[0.2em] font-bold">PNG, JPG jusqu&apos;à 10MB</p>
                           </div>
                          <input type="file" id="file-upload" className="hidden" accept="image/*" onChange={(e) => e.target.files && handleFile(e.target.files[0])} />
                           <Button variant="premium-outline" className="h-14 px-10 rounded-xl">
                             Parcourir
                           </Button>
                         </div>
                       )}
                       <input type="file" id="file-upload" className="hidden" accept="image/*" onChange={(e) => e.target.files && handleFile(e.target.files[0])} />
                     </div>

                     {/* Biometric Data Card */}
                     <div className="card-premium !p-16 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center gap-3 mb-10 border-b border-white/5 pb-6">
                            <Info size={16} className="text-emerald-400" />
                            <span className="text-[10px] font-bold tracking-[0.2em] text-white/40 uppercase">Données Biométriques</span>
                        </div>

                         <div className="flex flex-col gap-12">
                             <div className="flex flex-col gap-4">
                               <label className="text-[11px] font-bold tracking-[0.25em] text-white/40 uppercase pl-1">Âge (Années)</label>
                                <input 
                                  type="number" value={age} onChange={(e) => setAge(e.target.value)}
                                  placeholder="Ex: 5" className="input-premium" 
                                />
                             </div>
                              <div className="flex flex-col gap-4">
                                <label className="text-[11px] font-bold tracking-[0.25em] text-white/40 uppercase pl-1">Sexe du Spécimen</label>
                                <select 
                                  value={gender} onChange={(e) => setGender(e.target.value)}
                                   className="input-premium appearance-none cursor-pointer">
                                    {metadata?.genders ? metadata.genders.map((g: string) => (
                                      <option key={g} value={g} className="bg-zinc-900">{g}</option>
                                    )) : (
                                      <>
                                        <option value="Mare" className="bg-zinc-900">Femelle (Mare)</option>
                                        <option value="Stallion" className="bg-zinc-900">Mâle (Stallion)</option>
                                        <option value="Gelding" className="bg-zinc-900">Hongre (Gelding)</option>
                                      </>
                                    )}
                                </select>
                             </div>
                             <div className="flex flex-col gap-4">
                               <label className="text-[11px] font-bold tracking-[0.25em] text-white/40 uppercase pl-1">Taille (m)</label>
                                <input 
                                  type="text" value={height} onChange={(e) => setHeight(e.target.value)}
                                  placeholder="Ex: 1.65" className="input-premium" 
                                />
                             </div>
                         </div>
                       </div>
                       
                       <Button 
                          onClick={handleAnalyze}
                          disabled={!selectedFile || isAnalyzing}
                          variant="premium"
                          className="w-full mt-16 !h-16 text-lg"
                        >
                          {isAnalyzing ? "ANALYSE EN COURS..." : "LANCER L'ANALYSE"} <ChevronRight size={18} className="ml-2" />
                        </Button>
                     </div>
                  </div>
                </>
              ) : (
                <div className="animate-in fade-in zoom-in duration-500">
                  <div className="card-premium !p-20 relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-8">
                         <div className="flex items-center gap-2">
                             <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                             <span className="text-[10px] font-bold tracking-[0.3em] text-white/40 uppercase">Statut: Finalisé</span>
                         </div>
                      </div>

                      <div className="grid grid-cols-1 xl:grid-cols-2 gap-16 mt-4">
                        {/* Image Visualization */}
                        <div className="relative h-full min-h-[500px] rounded-[32px] overflow-hidden border border-white/10 bg-black/40 shadow-2xl">
                           {previewUrl && <Image src={previewUrl} alt="Analyzed specimen" fill className={`object-cover ${result?.warning === "NOT_A_HORSE" ? 'grayscale contrast-125' : ''}`} />}
                           <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent" />
                           
                           {result?.warning === "NOT_A_HORSE" && (
                            <div className="absolute inset-0 flex items-center justify-center bg-red-900/40 backdrop-blur-sm">
                               <div className="bg-red-600 text-white px-6 py-3 rounded-2xl flex items-center gap-3 shadow-2xl animate-pulse">
                                  <AlertCircle size={24} />
                                  <span className="font-bold tracking-widest uppercase text-sm">Aucun cheval détecté</span>
                               </div>
                            </div>
                           )}

                           <div className="absolute bottom-10 left-10 flex flex-col gap-1">
                              <span className="text-[10px] font-bold tracking-[0.3em] text-white/40 uppercase">Specimen ID</span>
                              <span className="text-white font-mono text-lg tracking-wider">#EV-{result?.id || 'ALPHA'}</span>
                           </div>
                        </div>

                        {/* Results Summary */}
                        <div className="flex flex-col justify-between h-full">
                           <div className="flex flex-col gap-8">
                              
                               {/* Breed Identification */}
                               <div className="stat-card-premium !p-12 !border-none !bg-white/[0.02]">
                                  <label className="text-[10px] font-bold tracking-[0.3em] text-white/30 uppercase mb-5 block flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-emerald-500" />
                                    Résultat Identification
                                  </label>
                                  <div className="flex flex-col gap-2">
                                     <h2 className={`text-4xl lg:text-5xl font-bold tracking-tight font-heading ${result?.warning === "NOT_A_HORSE" ? "text-red-500" : "text-white"}`}>
                                       {result?.warning === "NOT_A_HORSE" ? "Pas un cheval" : (result?.predicted_breed || "Inconnu")}
                                     </h2>
                                     {result?.warning !== "NOT_A_HORSE" && (
                                       <span className="text-emerald-400 text-[12px] font-bold tracking-[0.1em] mt-2 bg-emerald-500/10 px-4 py-1.5 rounded-full w-fit">
                                         {(result?.breed_confidence ? result.breed_confidence * 100 : 0).toFixed(1)}% DE CONFIANCE
                                       </span>
                                     )}
                                  </div>
                               </div>

                               {/* Price Estimation */}
                               <div className="stat-card-premium !p-12 !border-none !bg-white/[0.02]">
                                  <label className="text-[10px] font-bold tracking-[0.3em] text-white/30 uppercase mb-5 block flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-white/40" />
                                    Estimation de Valeur
                                  </label>
                                  {result?.warning === "NOT_A_HORSE" ? (
                                     <div className="flex flex-col gap-3">
                                       <h2 className="text-3xl font-bold text-red-500/50 tracking-tight font-heading">Analyse Impossible</h2>
                                       <p className="text-white/20 text-[11px] tracking-widest uppercase italic leading-relaxed mt-2 max-w-sm">
                                         Le système a détecté un sujet non-équin. La prédiction de prix est désactivée par mesure de sécurité.
                                       </p>
                                     </div>
                                  ) : (
                                     <div className="flex flex-col gap-3">
                                       <h2 className="text-4xl lg:text-5xl font-bold text-white tracking-tight font-heading">
                                          {result?.estimated_price ? `${(result.estimated_price * 10.5).toLocaleString()} MAD` : "Non estimé"}
                                        </h2>
                                       <div className="flex items-center gap-2 mt-2">
                                         <p className="text-white/30 text-[11px] tracking-[0.1em] uppercase font-medium">
                                           Fourchette estimée:
                                         </p>
                                         <span className="text-white/90 text-[12px] font-bold">
                                           {(result?.price_min ?? 0) * 10.5 < 1 ? "—" : ((result?.price_min ?? 0) * 10.5).toLocaleString()} — {((result?.price_max ?? 0) * 10.5).toLocaleString()} MAD
                                         </span>
                                       </div>
                                     </div>
                                  )}
                               </div>

                           </div>

                            <div className="flex gap-4 mt-12">
                               <Button 
                                 onClick={() => { setStep(1); setResult(null); }}
                                 variant="premium-outline"
                                 className="!flex-1 h-14"
                               >
                                 Retour
                               </Button>
                               <Button 
                                 onClick={() => { setStep(1); setResult(null); }}
                                 variant="premium"
                                 className="!flex-1 h-14"
                               >
                                   {result?.warning === "NOT_A_HORSE" ? "Quitter" : "Enregistrer & Fermer"}
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
    </div>
  );
}