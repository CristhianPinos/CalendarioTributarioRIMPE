/**
 * Componente: Barra de Navegación Principal del Sistema
 * Asignatura: Ingeniería de Software con IA Generativa
 * Caso N.º 11 – Grupo 11
 */

import React, { useState, useEffect } from "react";
import {
  Calendar,
  Calculator,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Scale,
} from "lucide-react";
import { verificarSaludBackend } from "../services/apiClient";

export default function Navbar({ onAbrirSimulador }) {
  const [backendStatus, setBackendStatus] = useState({
    checking: true,
    online: false,
    version: null,
  });

  useEffect(() => {
    chequearSalud();
    const interval = setInterval(chequearSalud, 15000); // Polling suave cada 15s
    return () => clearInterval(interval);
  }, []);

  const chequearSalud = async () => {
    try {
      const res = await verificarSaludBackend();
      if (res.online) {
        setBackendStatus({
          checking: false,
          online: true,
          version: res.data?.version || "2.0.0",
        });
      } else {
        setBackendStatus({
          checking: false,
          online: false,
          version: null,
        });
      }
    } catch {
      setBackendStatus({
        checking: false,
        online: false,
        version: null,
      });
    }
  };

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-40 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logotipo y Título */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-xs">
              <Calendar className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-base tracking-tight text-white">
                  Calendario Tributario
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-blue-500/20 text-blue-300 border border-blue-400/30">
                  RIMPE Ecuador
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Normativa SRI 2026 • Asistido por Google Gemini Flash
              </p>
            </div>
          </div>

          {/* Acciones y Estado del Sistema */}
          <div className="flex items-center space-x-3">
            {/* Estado del Backend */}
            <div className="hidden md:flex items-center">
              {backendStatus.checking ? (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-medium bg-slate-800 text-slate-400">
                  <div className="w-2 h-2 rounded-full bg-slate-400 animate-ping mr-1.5" />
                  Conectando API...
                </span>
              ) : backendStatus.online ? (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-500/30">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 mr-1.5 animate-pulse" />
                  API Activa (v{backendStatus.version})
                </span>
              ) : (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-medium bg-amber-950/80 text-amber-300 border border-amber-500/30">
                  <AlertCircle className="w-3 h-3 mr-1 text-amber-400" />
                  Modo Local
                </span>
              )}
            </div>

            {/* Insignia IA */}
            <div className="hidden lg:flex items-center px-2.5 py-1 rounded-full text-[11px] font-medium bg-indigo-950/80 text-indigo-300 border border-indigo-500/30">
              <Sparkles className="w-3.5 h-3.5 mr-1 text-amber-400" />
              <span>Gemini Flash 3.8</span>
            </div>

            {/* Botón Acceso Rápido Simulador */}
            <button
              onClick={onAbrirSimulador}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold transition-all shadow-xs hover:shadow active:scale-95 cursor-pointer"
            >
              <Calculator className="w-4 h-4 text-blue-200" />
              <span>Simular Renta</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
