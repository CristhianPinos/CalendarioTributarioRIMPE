/**
 * Componente: Pie de Página Institucional y Avisos Legales
 * Asignatura: Ingeniería de Software con IA Generativa
 * Caso N.º 11 – Grupo 11
 */

import React from "react";
import { ShieldCheck, BookOpen, ExternalLink, Scale } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-slate-900 border-t border-slate-800 text-slate-400 text-xs py-8 mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Columna 1: Fundamento Académico */}
          <div>
            <h4 className="text-white font-bold text-xs uppercase tracking-wider mb-2 flex items-center">
              <Scale className="w-4 h-4 mr-1.5 text-blue-400" />
              Caso N.º 11 – Grupo 11
            </h4>
            <p className="text-[11px] leading-relaxed text-slate-400">
              Ingeniería de Software con IA Generativa. Calendario tributario personalizado con explicaciones asistidas por Google Gemini Flash y motor determinista de fechas.
            </p>
          </div>

          {/* Columna 2: Fuentes Jurídicas */}
          <div>
            <h4 className="text-white font-bold text-xs uppercase tracking-wider mb-2 flex items-center">
              <BookOpen className="w-4 h-4 mr-1.5 text-indigo-400" />
              Cuerpos Normativos Oficiales
            </h4>
            <ul className="space-y-1 text-[11px] text-slate-400">
              <li>• Ley de Régimen Tributario Interno (LRTI codificada)</li>
              <li>• Ley de Eficiencia Económica (R.O. Suplemento 461)</li>
              <li>• Resolución SRI NAC-DGERCGC23-00000034 (Calendario)</li>
              <li>• Resolución SRI NAC-DGERCGC24-00000027 (Retenciones)</li>
            </ul>
          </div>

          {/* Columna 3: Privacidad y LOPDP */}
          <div>
            <h4 className="text-white font-bold text-xs uppercase tracking-wider mb-2 flex items-center">
              <ShieldCheck className="w-4 h-4 mr-1.5 text-emerald-400" />
              Privacidad y Cumplimiento LOPDP
            </h4>
            <p className="text-[11px] leading-relaxed text-slate-400">
              Conforme a la Ley Orgánica de Protección de Datos Personales de Ecuador: Los RUCs y correos ingresados se procesan en memoria con anonimización en logs (PII masking).
            </p>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-500 gap-2">
          <span>
            © {new Date().getFullYear()} Calendario Tributario RIMPE • Servicio de Rentas Internas (SRI Ecuador).
          </span>
          <span className="font-mono text-slate-500">
            Algoritmo Módulo 10 • Zero Date Hallucination • Gemini Flash 3.8
          </span>
        </div>
      </div>
    </footer>
  );
}
