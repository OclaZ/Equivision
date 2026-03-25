'use client'

import * as React from 'react'
import { useState, MouseEvent } from 'react'
import Image from 'next/image';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { BASE_URL } from '@/lib/api';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  icon?: React.ReactNode;
}

const AppInput = (props: InputProps) => {
  const { label, className, icon, ...rest } = props;
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);

  const handleMouseMove = (e: MouseEvent<HTMLInputElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    });
  };

  return (
    <div className="w-full min-w-[200px] relative font-sans">
      { label && 
        <label className='block mb-2 text-sm'>
          {label}
        </label>
      }
      <div className="relative w-full">
        <input
          className={`peer relative z-10 border-2 border-white/5 h-14 w-full rounded-xl bg-white/[0.03] px-8 text-base text-center font-normal outline-none drop-shadow-sm transition-all duration-200 ease-in-out focus:bg-white/[0.05] focus:border-white/20 placeholder:font-medium font-sans text-white ${className || ''}`}
          onMouseMove={handleMouseMove}
          onMouseEnter={() => setIsHovering(true)}
          onMouseLeave={() => setIsHovering(false)}
          {...rest}
        />
        {isHovering && (
          <>
            <div
              className="absolute pointer-events-none top-0 left-0 right-0 h-[2px] z-20 rounded-t-md overflow-hidden"
              style={{
                background: `radial-gradient(30px circle at ${mousePosition.x}px 0px, rgba(255,255,255,0.4) 0%, transparent 70%)`,
              }}
            />
            <div
              className="absolute pointer-events-none bottom-0 left-0 right-0 h-[2px] z-20 rounded-b-md overflow-hidden"
              style={{
                background: `radial-gradient(30px circle at ${mousePosition.x}px 2px, rgba(255,255,255,0.4) 0%, transparent 70%)`,
              }}
            />
          </>
        )}
        {icon && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 z-20">
            {icon}
          </div>
        )}
      </div>
    </div>
  )
}

interface AuthFormProps {
  mode: "login" | "register";
}

export function AuthForm({ mode }: AuthFormProps) {
  const { login: authLogin } = useAuth();
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [mousePosition, setMousePosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    });
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    const formData = new FormData(e.currentTarget);
    const username = formData.get("username") as string;
    const password = formData.get("password") as string;
    const email = formData.get("email") as string;

    try {
      if (mode === "login") {
        const loginData = new FormData();
        loginData.append("username", username);
        loginData.append("password", password);

        const response = await fetch(`${BASE_URL}/auth/login`, {
          method: "POST",
          body: loginData,
        });

        if (response.ok) {
          const { access_token } = await response.json();
          await authLogin(access_token);
        } else {
          const err = await response.json();
          throw new Error(err.detail || "Identifiants incorrects");
        }
      } else {
        const response = await fetch(`${BASE_URL}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, username, password }),
        });

        if (response.ok) {
          const loginData = new FormData();
          loginData.append("username", username);
          loginData.append("password", password);
          
          const loginRes = await fetch(`${BASE_URL}/auth/login`, {
            method: "POST",
            body: loginData,
          });
          const { access_token } = await loginRes.json();
          await authLogin(access_token);
        } else {
          const err = await response.json();
          throw new Error(err.detail || "Erreur lors de l'inscription");
        }
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const isLogin = mode === 'login';

  return (
    <div className="min-h-screen w-full bg-black flex items-center justify-center p-4 font-sans text-white">
       {/* Background Noise Texture */}
       <div 
        className="absolute inset-0 z-0 opacity-[0.03] pointer-events-none mix-blend-overlay"
        style={{ backgroundImage: "url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.85%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E')" }}
      />

      <div className='w-full max-w-[1100px] flex flex-col lg:flex-row justify-between h-auto lg:h-[700px] bg-white/[0.02] border border-white/5 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-3xl relative z-10'>
        <div
          className='flex-1 flex flex-col justify-center items-center p-8 md:p-12 relative overflow-hidden'
          onMouseMove={handleMouseMove}
          onMouseEnter={() => setIsHovering(true)}
          onMouseLeave={() => setIsHovering(false)}>
          
          <div
            className={`absolute pointer-events-none w-[500px] h-[500px] bg-gradient-to-r from-purple-500/10 via-blue-500/10 to-emerald-500/10 rounded-full blur-[100px] transition-opacity duration-500 ease-in-out ${
              isHovering ? 'opacity-100' : 'opacity-0'
            }`}
            style={{
              left: mousePosition.x - 250,
              top: mousePosition.y - 250,
              zIndex: 0
            }}
          />

          <div className="w-full max-w-[320px] z-10 relative flex flex-col items-center">
            <div className="mb-10 mt-4 w-[160px] relative">
               <Image
                 src="https://res.cloudinary.com/ddvzn2n7i/image/upload/v1774183125/unnamed-removebg-preview_hvqlqb.png"
                 alt="EquiVision"
                 width={180}
                 height={60}
                 className="w-full h-auto brightness-0 invert opacity-90 object-contain drop-shadow-md transition-transform hover:scale-105"
               />
            </div>

            <form className='text-center flex flex-col gap-6 w-full pb-12' onSubmit={handleSubmit}>
              <div className='flex flex-col items-center w-full'>
                <h1 className='text-4xl font-bold tracking-tight text-white uppercase'>{isLogin ? 'Connexion' : 'Inscription'}</h1>
                <span className='text-[10px] font-bold tracking-[0.2em] text-white/30 uppercase mt-3'>
                  {isLogin ? 'Terminal d\'accès sécurisé' : 'Création de profil terminal'}
                </span>
              </div>
              
              <div className='flex flex-col gap-4 items-center w-full'>
                {!isLogin && (
                    <AppInput placeholder="ADRESSE EMAIL" type="email" name="email" required />
                )}
                <AppInput placeholder="NOM D'UTILISATEUR" type="text" name="username" required />
                <AppInput placeholder="MOT DE PASSE" type="password" name="password" required />
              </div>

              {error && (
                <p className="text-red-400 text-[10px] font-bold tracking-wider uppercase bg-red-400/10 py-2 w-full rounded-lg px-4 border border-red-400/20">{error}</p>
              )}
              
              {isLogin && (
                <div className='w-full flex justify-end -mt-7'>
                  <a href="#" className='text-[10px] font-bold tracking-widest text-white/30 hover:text-white transition-colors uppercase'>Oublié ?</a>
                </div>
              )}
              
              <div className='w-full flex flex-col items-center gap-6'>
                 <button 
                  disabled={isLoading}
                  type="submit"
                  className="w-full relative h-12 rounded-xl bg-white text-black text-[12px] font-bold tracking-[0.2em] uppercase hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_0_20px_rgba(255,255,255,0.1)] disabled:opacity-50"
                >
                  {isLoading ? 'TRAITEMENT...' : (isLogin ? 'AUTHENTIFIER' : 'ENREGISTRER')}
                </button>

                <div className='text-[10px] font-bold tracking-widest text-white/20 uppercase'>
                  {isLogin ? (
                    <>
                      Pas de compte ?{' '}
                      <Link href="/register" className='text-white hover:underline transition-all underline-offset-4 cursor-pointer'>
                        S&apos;inscrire
                      </Link>
                    </>
                  ) : (
                    <>
                      Déjà un compte ?{' '}
                      <Link href="/login" className='text-white hover:underline transition-all underline-offset-4 cursor-pointer'>
                        Se connecter
                      </Link>
                    </>
                  )}
                </div>
              </div>
            </form>
          </div>
        </div>

        <div className='hidden lg:block w-1/2 h-full overflow-hidden relative'>
             <div className="absolute inset-0 bg-black/40 z-10" />
             <div className="absolute inset-0 bg-gradient-to-r from-black/80 to-transparent z-20" />
             <Image
              src='https://res.cloudinary.com/ddvzn2n7i/image/upload/v1774189552/2c281d28f7e3b8c26c6bfe1edb91b397_a0flqn.jpg'
              width={800}
              height={800}
              priority
              alt="Equine image"
              className="absolute inset-0 w-full h-full object-cover grayscale brightness-50"
            />
            <div className="absolute bottom-12 left-12 z-30 flex flex-col gap-4">
               <div className="h-[2px] w-12 bg-white" />
               <p className="text-[24px] font-bold text-white uppercase tracking-tighter leading-none max-w-[200px]">Intelligence Équestre de Pointe.</p>
            </div>
        </div>
      </div>
    </div>
  )
}
