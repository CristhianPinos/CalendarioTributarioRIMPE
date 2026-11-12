/**
 * Componente: Pie de Página Institucional y Avisos Legales
 * Asignatura: Ingeniería de Software con IA Generativa
 * Caso N.º 11 – Grupo 11
 */

import React from "react";
import { ShieldCheck, BookOpen, Scale } from "lucide-react";

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
              Ingeniería de Software con IA Generativa. Calendario tributario personalizado con explicaciones asistidas por IA cuando está disponible y motor determinista de fechas.
            </p>
            <p className="text-[11px] leading-relaxed text-slate-300 mt-2">
              Esta aplicación fue desarrollada con el apoyo de herramientas de inteligencia artificial. Sus resultados deben verificarse con las fuentes oficiales.
            </p>
          </div>

          {/* Columna 2: Fuentes Jurídicas */}
          <div>
            <h4 className="text-white font-bold text-xs uppercase tracking-wider mb-2 flex items-center">
              <BookOpen className="w-4 h-4 mr-1.5 text-indigo-400" />
              Cuerpos Normativos Oficiales
            </h4>
            <ul className="space-y-1 text-[11px] text-slate-400">
              <li>• <a className="hover:text-white underline-offset-2 hover:underline" href="https://www.sri.gob.ec/normativa-tributaria-legislacion-nacional" target="_blank" rel="noreferrer">Ley de Régimen Tributario Interno (LRTI)</a></li>
              <li>• <a className="hover:text-white underline-offset-2 hover:underline" href="https://www.sri.gob.ec/normativa-tributaria-legislacion-nacional" target="_blank" rel="noreferrer">Reglamento para la aplicación de la LRTI</a></li>
              <li>• <a className="hover:text-white underline-offset-2 hover:underline" href="https://www.registroficial.gob.ec/suplemento-al-registro-oficial-no-461/" target="_blank" rel="noreferrer">Ley Orgánica de Eficiencia Económica y Generación de Empleo (R.O. 461)</a></li>
              <li>• <a className="hover:text-white underline-offset-2 hover:underline" href="https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar?id=7c3fb8dc-31a6-4fe3-a6c0-abe1def2c78a&amp;nombre=NAC-DGERCGC24-00000027.pdf" target="_blank" rel="noreferrer">Resolución NAC-DGERCGC24-00000027 (normas de aplicación del RIMPE)</a></li>
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
            Calendario Tributario RIMPE • Proyecto académico independiente; no afiliado al SRI.
          </span>
          <span className="font-mono text-slate-500">
            Fechas calculadas por Python • Explicaciones asistidas por IA cuando está disponible
          </span>
        </div>
      </div>
    </footer>
  );
}
