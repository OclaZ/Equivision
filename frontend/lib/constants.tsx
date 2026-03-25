import React from 'react';
import { 
  LayoutDashboard, 
  Maximize, 
  ScanEye, 
  TrendingUp, 
  History
} from "lucide-react";

export const getNavLinks = (activePath: string) => [
  { 
    icon: <LayoutDashboard size={20} strokeWidth={1.5} />, 
    label: "Dashboard", 
    href: "/dashboard",
    active: activePath === "/dashboard"
  },
  { 
    icon: <Maximize size={20} strokeWidth={1.5} />, 
    label: "Analyse Image", 
    href: "/image-analysis",
    active: activePath === "/image-analysis"
  },
  { 
    icon: <ScanEye size={20} strokeWidth={1.5} />, 
    label: "Analyse Complète", 
    href: "/prediction",
    active: activePath === "/prediction"
  },
  { 
    icon: <TrendingUp size={20} strokeWidth={1.5} />, 
    label: "Marché", 
    href: "/marche",
    active: activePath === "/marche"
  },
  { 
    icon: <History size={20} strokeWidth={1.5} />, 
    label: "Historique", 
    href: "/historique",
    active: activePath === "/historique"
  },
];
