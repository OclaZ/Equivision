"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/ui/sidebar";
import { 
  ChevronRight, 
  CheckCircle2,
  BarChart3,
  TrendingUp,
  Scale,
  Calendar,
  ChevronLeft
} from "lucide-react";
import { getNavLinks } from "@/lib/constants";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";

interface MarketResult {
  estimated_price: number;
  currency: string;
  confidence_interval: {
    min: number;
    max: number;
  };
}

const BREEDS = [
  { id: "Akhal-Teke", name: "Akhal-Teke", img: "/breeds_imgs/Akhal-Teke.png" },
  { id: "Arabian", name: "Arabe", img: "/breeds_imgs/arabian.png" },
  { id: "Barb", name: "Barbe", img: "/breeds_imgs/Barb.png" },
  { id: "Friesian", name: "Frison", img: "/breeds_imgs/Friesian.png" },
  { id: "Iberian", name: "Ibérique", img: "/breeds_imgs/Iberian.png" },
  { id: "Orlov Trotter", name: "Orlov Trotter", img: "/breeds_imgs/Orlov Trotter.png" },
  { id: "Paint Horse", name: "Paint Horse", img: "/breeds_imgs/Paint Horse.png" },
  { id: "Pony", name: "Poney", img: "/breeds_imgs/Pony.png" },
  { id: "Quarter Horse", name: "Quarter Horse", img: "/breeds_imgs/Quarter Horse.png" },
  { id: "Selle Français", name: "Selle Français", img: "/breeds_imgs/Selle Français.png" },
  { id: "Sport Horse", name: "Sport Horse", img: "/breeds_imgs/Sport Horse.png" },
  { id: "Trakehner", name: "Trakehner", img: "/breeds_imgs/Trakehner.png" },
  { id: "Welsh", name: "Welsh", img: "/breeds_imgs/Welsh.png" }
];

const GENDERS = [
  { id: "Mare", name: "Jument", img: "/genders_imgs/mare.png" },
  { id: "Stallion", name: "Étalon", img: "/genders_imgs/stallion.png" },
  { id: "Gelding", name: "Hongre", img: "/genders_imgs/Gelding.png" }
];

export default function MarketAnalysisPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Selection state
  const [selectedBreed, setSelectedBreed] = useState<string>("");
  const [selectedGender, setSelectedGender] = useState<string>("");
  const [age, setAge] = useState<string>("");
  const [height, setHeight] = useState<string>("");
  
  // Result state
  const [result, setResult] = useState<MarketResult | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  const handleNext = () => setStep(prev => prev + 1);
  const handleBack = () => setStep(prev => prev - 1);

  const calculateEstimate = async () => {
    setLoading(true);
    try {
      const response = await apiFetch("/predict/price", {
        method: "POST",
        data: {
          breed: selectedBreed,
          gender: selectedGender,
          age: parseInt(age),
          height: parseFloat(height)
        }
      });
      setResult(response);
      setStep(4);
    } catch (error) {
      console.error("Evaluation failed:", error);
      alert("Une erreur est survenue lors de l'estimation.");
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) return null;

  const links = getNavLinks("/marche");

  return (
    <div className="flex h-screen bg-[#050505] text-white font-geist overflow-hidden p-6 lg:px-12 lg:py-10 gap-10">
      <Sidebar links={links} />

      <main className="flex-1 relative overflow-y-auto custom-scrollbar flex flex-col items-center justify-center">
        {/* Background Elements */}
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-white/[0.015] rounded-full blur-[120px] -mr-64 -mt-64 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-emerald-500/[0.015] rounded-full blur-[100px] -ml-48 -mb-48 pointer-events-none" />

        <div className="max-w-[1600px] w-full mx-auto px-12 pt-20 pb-32 min-h-full flex flex-col items-center justify-center">
          <div className="w-full flex items-center justify-between mb-24 max-w-[1400px]">
            <div>
              <h1 className="text-[48px] lg:text-[72px] font-extrabold tracking-tighter mb-4 font-heading italic">Analyse du Marché</h1>
              <p className="text-white/40 text-sm tracking-[0.05em] font-medium pl-1">Évaluation instantanée basée sur les algorithmes FinTech mondiaux</p>
            </div>
            
            {/* Unified Step Indicator */}
            <div className="flex items-center gap-5 card-premium !p-6 !px-10 !rounded-full">
              {[1, 2, 3, 4].map((s) => (
                <div key={s} className="flex items-center gap-5">
                  <div className={`w-3.5 h-3.5 rounded-full transition-all duration-700 ${step >= s ? 'bg-emerald-400 shadow-[0_0_15px_rgba(52,211,153,0.8)] scale-110' : 'bg-white/10'}`} />
                  {s < 4 && (
                    <div className={`w-12 h-[2px] rounded-full transition-all duration-700 ${step > s ? 'bg-emerald-400/60' : 'bg-white/10'}`} />
                  )}
                </div>
              ))}
            </div>
          </div>

          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div 
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="max-w-[1400px] w-full mx-auto space-y-16"
              >
                <div className="flex items-center justify-between border-b border-white/5 pb-12 mb-16">
                  <h2 className="text-4xl font-extrabold tracking-tighter font-heading italic">Sélection de la Lignée</h2>
                  <span className="text-[11px] text-emerald-400 tracking-[0.4em] font-bold uppercase py-3 px-8 bg-emerald-500/10 rounded-full border border-emerald-500/20">Étape 01/04</span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-8">
                  {BREEDS.map((breed) => (
                    <button
                      key={breed.id}
                      onClick={() => setSelectedBreed(breed.id)}
                      className={`group relative card-premium !p-12 !rounded-[2.5rem] transition-all duration-700 ${
                        selectedBreed === breed.id 
                        ? 'bg-emerald-500/10 border-emerald-500/40 shadow-emerald-500/20' 
                        : 'hover:border-white/30'
                      }`}
                    >
                      <div className="aspect-square relative mb-8 overflow-hidden rounded-3xl bg-black/40 shadow-inner">
                        <Image 
                          src={breed.img} 
                          alt={breed.name} 
                          fill 
                          className={`object-contain p-6 transition-all duration-1000 group-hover:scale-110 ${selectedBreed === breed.id ? 'brightness-125' : 'opacity-40 brightness-75 grayscale group-hover:grayscale-0 group-hover:opacity-100'}`}
                        />
                      </div>
                      <span className={`block text-center text-[12px] font-extrabold tracking-[0.2em] uppercase transition-all duration-500 ${selectedBreed === breed.id ? 'text-emerald-400' : 'text-white/30 group-hover:text-white'}`}>
                        {breed.name}
                      </span>
                      {selectedBreed === breed.id && (
                        <div className="absolute top-6 right-6 bg-emerald-500 rounded-full p-1.5 shadow-[0_0_20px_rgba(52,211,153,0.4)]">
                          <CheckCircle2 className="text-black w-4 h-4 stroke-[3]" />
                        </div>
                      )}
                    </button>
                  ))}
                </div>

                <div className="mt-24 pt-12 border-t border-white/5 flex justify-end">
                  <Button
                    disabled={!selectedBreed}
                    onClick={handleNext}
                    variant="premium"
                    className="h-14 px-10 rounded-xl"
                  >
                    Confirmer la race <ChevronRight className="w-5 h-5 transition-transform group-hover:translate-x-1 ml-2" />
                  </Button>
                </div>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div 
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="max-w-[1400px] w-full mx-auto space-y-12"
              >
                <div className="text-center border-b border-white/5 pb-12 mb-16">
                  <h2 className="text-4xl font-extrabold tracking-tighter font-heading italic">Profil Biologique</h2>
                  <p className="text-white/40 text-[11px] font-bold tracking-[0.4em] uppercase mt-4">Étape 02/04</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-12 max-w-6xl mx-auto">
                  {GENDERS.map((g) => (
                    <button
                      key={g.id}
                      onClick={() => setSelectedGender(g.id)}
                      className={`group relative aspect-square card-premium !p-12 !rounded-[2.5rem] transition-all duration-700 overflow-hidden ${
                        selectedGender === g.id 
                        ? 'bg-emerald-500/10 border-emerald-400/60 shadow-emerald-500/25' 
                        : 'hover:border-white/30'
                      }`}
                    >
                       <div className="h-full flex flex-col items-center justify-between">
                          <div className="flex-1 relative w-full mb-10">
                            <Image 
                              src={g.img} 
                              alt={g.name} 
                              fill 
                              className={`object-contain transition-all duration-1000 ${selectedGender === g.id ? 'scale-110 brightness-125' : 'opacity-40 brightness-50 grayscale group-hover:grayscale-0 group-hover:opacity-100'}`}
                            />
                          </div>
                          <span className={`text-[14px] font-black tracking-[0.4em] uppercase transition-all duration-500 ${selectedGender === g.id ? 'text-emerald-400' : 'text-white/30 group-hover:text-white'}`}>
                            {g.name}
                          </span>
                       </div>
                    </button>
                  ))}
                </div>

                <div className="flex justify-between items-center mt-24 pt-12 border-t border-white/5 gap-8">
                  <Button onClick={handleBack} variant="premium-outline" className="h-14 px-10 rounded-xl">
                    <ChevronLeft className="w-5 h-5 mr-2" /> Précédent
                  </Button>
                  <Button
                    disabled={!selectedGender}
                    onClick={handleNext}
                    variant="premium"
                    className="h-14 px-10 rounded-xl"
                  >
                    Valider le profil <ChevronRight className="w-5 h-5 transition-transform group-hover:translate-x-1 ml-2" />
                  </Button>
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div 
                key="step3"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="max-w-[1000px] w-full mx-auto space-y-12"
              >
                <div className="text-center border-b border-white/5 pb-10 mb-12">
                  <h2 className="text-4xl font-extrabold tracking-tight mb-4 font-heading italic">Paramètres Biométriques</h2>
                  <p className="text-[11px] text-white/40 font-bold tracking-[0.4em] uppercase">Étape 03/04 • Facteurs de valorisation</p>
                </div>

                <div className="space-y-10">
                  <div className="space-y-5">
                    <label className="text-[11px] font-bold tracking-[0.3em] text-white/40 uppercase ml-2 flex items-center gap-3">
                      <Calendar className="w-4 h-4 text-emerald-400" />
                      Maturité (Âge en années)
                    </label>
                    <div className="relative group">
                      <input 
                        type="number"
                        value={age}
                        onChange={(e) => setAge(e.target.value)}
                        placeholder="Ex: 5"
                        className="input-premium"
                      />
                    </div>
                  </div>

                  <div className="space-y-5">
                    <label className="text-[11px] font-bold tracking-[0.3em] text-white/40 uppercase ml-2 flex items-center gap-3">
                      <Scale className="w-4 h-4 text-emerald-400" />
                      Gabarit (Taille en mètres)
                    </label>
                    <div className="relative group">
                      <input 
                        type="number"
                        step="0.01"
                        value={height}
                        onChange={(e) => setHeight(e.target.value)}
                        placeholder="Ex: 1.65"
                        className="input-premium"
                      />
                    </div>
                  </div>
                </div>

                <div className="flex justify-between gap-8 items-center mt-24 pt-12 border-t border-white/5">
                  <Button onClick={handleBack} variant="premium-outline" className="h-14 px-10 rounded-xl">
                    <ChevronLeft className="w-5 h-5 mr-2" /> Retour
                  </Button>
                  <Button
                    disabled={!age || !height || loading}
                    onClick={calculateEstimate}
                    variant="premium"
                    className="flex-1 h-14 rounded-xl"
                  >
                    {loading ? (
                      <div className="w-6 h-6 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                    ) : (
                      <>Exécuter l&apos;évaluation <TrendingUp className="w-5 h-5 ml-2" /></>
                    )}
                  </Button>
                </div>
              </motion.div>
            )}

            {step === 4 && result && (
              <motion.div 
                key="step4"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="max-w-[1400px] w-full mx-auto"
              >
                <div className="card-premium !p-12 lg:!p-24 relative overflow-hidden text-center">
                  {/* Decorative Result Glow */}
                  <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-lg h-1 bg-gradient-to-r from-transparent via-emerald-500 to-transparent" />
                  <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-emerald-500/10 rounded-full blur-[100px] pointer-events-none" />
                  
                  <div className="flex flex-col items-center gap-12 relative z-10">
                    <div className="space-y-6">
                      <div className="inline-flex items-center gap-3 bg-emerald-500/10 px-5 py-2.5 rounded-full border border-emerald-500/20">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        <span className="text-emerald-400 text-[11px] font-bold tracking-[0.25em] uppercase">Analyse FinTech Validée</span>
                      </div>
                      <h2 className="text-5xl font-extrabold tracking-tight font-heading">VALEUR ESTIMÉE</h2>
                    </div>

                    <div className="relative w-full py-8">
                      <h3 className="text-[80px] lg:text-[120px] leading-none font-extrabold text-white tracking-tighter drop-shadow-2xl font-heading italic">
                        {Math.round(result.estimated_price * 10.5).toLocaleString()} <span className="text-4xl lg:text-5xl text-white/40 font-medium font-sans not-italic">MAD</span>
                      </h3>
                      
                      <div className="flex items-center justify-center gap-6 mt-10">
                         <div className="px-8 py-4 rounded-2xl border border-white/5 bg-white/[0.02] backdrop-blur-md">
                            <span className="text-[10px] font-bold block uppercase tracking-[0.2em] mb-2 text-white/40">Seuil Minimum</span>
                            <span className="text-xl font-bold text-white/80">{Math.round((result.confidence_interval?.min || 0) * 10.5).toLocaleString()} MAD</span>
                         </div>
                         <div className="px-8 py-4 rounded-2xl border border-white/5 bg-white/[0.02] backdrop-blur-md">
                            <span className="text-[10px] font-bold block uppercase tracking-[0.2em] mb-2 text-white/40">Plafond Maximum</span>
                            <span className="text-xl font-bold text-white/80">{Math.round((result.confidence_interval?.max || 0) * 10.5).toLocaleString()} MAD</span>
                         </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6 w-full p-12 border-y border-white/5 bg-white/[0.01] rounded-3xl">
                      <div className="flex flex-col items-center gap-3">
                        <span className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em]">Lignée</span>
                        <span className="text-base font-semibold tracking-wide text-emerald-400">{BREEDS.find(b => b.id === selectedBreed)?.name}</span>
                      </div>
                      <div className="flex flex-col items-center gap-3 border-l border-white/5">
                        <span className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em]">Profil</span>
                        <span className="text-base font-semibold tracking-wide">{GENDERS.find(g => g.id === selectedGender)?.name}</span>
                      </div>
                      <div className="flex flex-col items-center gap-3 border-l border-white/5">
                        <span className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em]">Maturité</span>
                        <span className="text-base font-semibold tracking-wide">{age} Ans</span>
                      </div>
                      <div className="flex flex-col items-center gap-3 border-l border-white/5">
                        <span className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em]">Gabarit</span>
                        <span className="text-base font-semibold tracking-wide">{height} m</span>
                      </div>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-6 w-full pt-4">
                      <Button 
                         onClick={() => setStep(1)}
                         variant="premium-outline"
                         className="!flex-1 h-16 rounded-2xl"
                      >
                        Nouveau Calcul
                      </Button>
                      <Button 
                        onClick={() => router.push("/prediction")}
                        variant="premium"
                        className="!flex-[2] h-16 rounded-2xl"
                      >
                        <BarChart3 className="w-5 h-5 mr-2" /> Vérification Visuelle Complète
                      </Button>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}