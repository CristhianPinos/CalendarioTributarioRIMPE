/**
 * Componente: Barra de Navegación Principal del Sistema
 * Asignatura: Ingeniería de Software con IA Generativa
 * Caso N.º 11 – Grupo 11
 */

import React from "react";
import { Calendar, Calculator } from "lucide-react";

export default function Navbar({ onAbrirSimulador }) {
  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-40 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logotipo y Título */}
          <div className="flex min-w-0 items-center gap-2 sm:gap-3">
            <div className="w-10 h-10 shrink-0 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-xs">
              <Calendar className="w-5 h-5 text-white" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center space-x-2">
                <span className="sm:hidden whitespace-nowrap font-extrabold text-sm tracking-tight text-white">
                  Calendario RIMPE
                </span>
                <span className="hidden sm:inline font-extrabold text-base tracking-tight text-white">
                  Calendario Tributario
                </span>
                <span className="hidden sm:inline px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-blue-500/20 text-blue-300 border border-blue-400/30">
                  RIMPE Ecuador
                </span>
              </div>
              <p className="hidden sm:block text-[11px] text-slate-400">
                Calendario RIMPE • Explicaciones asistidas por IA cuando está disponible
              </p>
            </div>
          </div>

          {/* Acciones */}
          <div className="flex shrink-0 items-center space-x-3">
            {/* Botón Acceso Rápido Simulador */}
            <button
              onClick={onAbrirSimulador}
              aria-label="Simular Renta"
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold transition-all shadow-xs hover:shadow active:scale-95 cursor-pointer"
            >
              <Calculator className="w-4 h-4 text-blue-200" />
              <span className="sm:hidden">Renta</span>
              <span className="hidden sm:inline">Simular Renta</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
