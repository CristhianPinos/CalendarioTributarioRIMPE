/**
 * Componente: Formulario de Perfil del Contribuyente RIMPE
 * Asignatura: Ingeniería de Software con IA Generativa
 * Caso N.º 11 – Grupo 11
 */

import React, { useState, useEffect } from "react";
import {
  CheckCircle2,
  AlertCircle,
  Building2,
  Calendar,
  Mail,
  Sparkles,
  HelpCircle,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { validarRucPersonaNatural } from "../utils/rucValidator";

// Mapeo oficial del SRI de noveno dígito a día de vencimiento nominal
const DIAS_POR_NOVENO_DIGITO = {
  1: 10,
  2: 12,
  3: 14,
  4: 16,
  5: 18,
  6: 20,
  7: 22,
  8: 24,
  9: 26,
  0: 28,
};

// Contribuyentes reales de prueba para testing inmediato (Guayas, Pichincha, Azuay)
const PRESETS_PRUEBA = [
  {
    etiqueta: "Emprendedor (Guayas - Dígito 8)",
    ruc: "0923456784001",
    razonSocial: "Comercial Pinos & Asociados",
    regimen: "RIMPE_EMPRENDEDOR",
    excluidas: false,
    email: "cristhian.pinos@empresa.ec",
  },
  {
    etiqueta: "Negocio Popular (Pichincha - Dígito 6)",
    ruc: "1710034065001",
    razonSocial: "Bazar y Papelería San Francisco",
    regimen: "RIMPE_NEGOCIO_POPULAR",
    excluidas: false,
    email: "bazar.sf@negocio.ec",
  },
  {
    etiqueta: "Mixto con Act. Excluida (Dígito 0)",
    ruc: "0910000009001",
    razonSocial: "Servicios Contables y Tienda",
    regimen: "RIMPE_EMPRENDEDOR",
    excluidas: true,
    email: "contacto@mixto.ec",
  },
];

export default function ProfileForm({ onGenerarCalendario, cargando, errorBackend }) {
  const [ruc, setRuc] = useState("0923456784001");
  const [razonSocial, setRazonSocial] = useState("Comercial Pinos & Asociados");
  const [tipoRegimen, setTipoRegimen] = useState("RIMPE_EMPRENDEDOR");
  const [tieneActividadesExcluidas, setTieneActividadesExcluidas] = useState(false);
  const [anio, setAnio] = useState(2026);
  const [email, setEmail] = useState("contacto@empresa.ec");

  const [estadoRuc, setEstadoRuc] = useState({
    valido: true,
    novenoDigito: 8,
    provincia: "09",
    error: null,
  });

  // Validar RUC en tiempo real mientras el usuario escribe
  useEffect(() => {
    if (!ruc) {
      setEstadoRuc({ valido: false, novenoDigito: null, provincia: null, error: null });
      return;
    }
    const resultado = validarRucPersonaNatural(ruc);
    setEstadoRuc(resultado);
  }, [ruc]);

  const aplicarPreset = (preset) => {
    setRuc(preset.ruc);
    setRazonSocial(preset.razonSocial);
    setTipoRegimen(preset.regimen);
    setTieneActividadesExcluidas(preset.excluidas);
    setEmail(preset.email);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!estadoRuc.valido) return;

    onGenerarCalendario({
      ruc,
      razon_social: razonSocial,
      tipo_regimen: tipoRegimen,
      tiene_actividades_excluidas: tieneActividadesExcluidas,
      anio: parseInt(anio, 10),
      email,
    });
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Encabezado del Formulario */}
      <div className="bg-gradient-to-r from-blue-900 via-blue-800 to-indigo-900 p-5 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-700/50 rounded-lg backdrop-blur-sm">
              <Building2 className="w-5 h-5 text-blue-200" />
            </div>
            <div>
              <h2 className="text-lg font-bold leading-tight">Perfil del Contribuyente</h2>
              <p className="text-xs text-blue-200">Parámetros tributarios oficiales SRI 2026</p>
            </div>
          </div>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-200 border border-emerald-400/30">
            <ShieldCheck className="w-3.5 h-3.5 mr-1" />
            Módulo 10 Activo
          </span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-5">
        {/* Presets Rápidos de Demostración */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center">
              <Zap className="w-3.5 h-3.5 mr-1 text-amber-500" />
              Cargar Perfil de Prueba Rápido
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {PRESETS_PRUEBA.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => aplicarPreset(preset)}
                className="text-left px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-blue-50 hover:border-blue-300 text-xs text-slate-700 font-medium transition-colors shadow-2xs"
              >
                {preset.etiqueta}
              </button>
            ))}
          </div>
        </div>

        {/* Campo: RUC */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
            RUC de Persona Natural (13 dígitos) <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <input
              type="text"
              maxLength={13}
              value={ruc}
              onChange={(e) => setRuc(e.target.value.replace(/\D/g, ""))}
              placeholder="Ej: 0923456784001"
              className={`w-full px-3.5 py-2.5 text-sm rounded-xl font-mono tracking-wider transition-all outline-none border ${
                !ruc
                  ? "border-slate-300 focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
                  : estadoRuc.valido
                  ? "border-emerald-500 bg-emerald-50/20 text-slate-900 focus:ring-2 focus:ring-emerald-100"
                  : "border-red-400 bg-red-50/20 text-red-900 focus:ring-2 focus:ring-red-100"
              }`}
            />
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              {estadoRuc.valido ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              ) : ruc.length === 13 ? (
                <AlertCircle className="w-5 h-5 text-red-500" />
              ) : null}
            </div>
          </div>

          {/* Feedback de Validación de RUC */}
          {estadoRuc.valido && estadoRuc.novenoDigito !== null && (
            <div className="mt-2 p-2.5 bg-emerald-50 border border-emerald-200/70 rounded-lg text-xs text-emerald-800 flex items-center justify-between">
              <span className="font-medium">
                Provincia {estadoRuc.provincia} • <strong>9.º Dígito: {estadoRuc.novenoDigito}</strong>
              </span>
              <span className="bg-emerald-600 text-white px-2 py-0.5 rounded text-[11px] font-semibold">
                Vence día {DIAS_POR_NOVENO_DIGITO[estadoRuc.novenoDigito]}
              </span>
            </div>
          )}

          {!estadoRuc.valido && ruc && estadoRuc.error && (
            <p className="mt-1.5 text-xs text-red-600 flex items-start">
              <AlertCircle className="w-3.5 h-3.5 mr-1 flex-shrink-0 mt-0.5" />
              <span>{estadoRuc.error}</span>
            </p>
          )}
        </div>

        {/* Campo: Razón Social / Nombre Comercial */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
            Razón Social / Nombre Comercial
          </label>
          <input
            type="text"
            value={razonSocial}
            onChange={(e) => setRazonSocial(e.target.value)}
            placeholder="Ej: Comercial Don Juan"
            className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-300 focus:border-blue-600 focus:ring-2 focus:ring-blue-100 transition-all outline-none"
          />
        </div>

        {/* Selector de Régimen RIMPE */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
            Tipo de Régimen RIMPE <span className="text-red-500">*</span>
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Opción 1: RIMPE Emprendedor */}
            <div
              onClick={() => setTipoRegimen("RIMPE_EMPRENDEDOR")}
              className={`cursor-pointer rounded-xl p-3.5 border transition-all ${
                tipoRegimen === "RIMPE_EMPRENDEDOR"
                  ? "border-blue-600 bg-blue-50/50 shadow-xs ring-2 ring-blue-500/20"
                  : "border-slate-200 hover:border-slate-300 hover:bg-slate-50/50"
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-bold text-sm text-blue-900">RIMPE Emprendedor</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">
                  $20k - $300k
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                3 obligaciones anuales (IVA Semestral en Julio y Enero + Renta en Marzo). Emite facturas electrónicas.
              </p>
            </div>

            {/* Opción 2: RIMPE Negocio Popular */}
            <div
              onClick={() => setTipoRegimen("RIMPE_NEGOCIO_POPULAR")}
              className={`cursor-pointer rounded-xl p-3.5 border transition-all ${
                tipoRegimen === "RIMPE_NEGOCIO_POPULAR"
                  ? "border-emerald-600 bg-emerald-50/50 shadow-xs ring-2 ring-emerald-500/20"
                  : "border-slate-200 hover:border-slate-300 hover:bg-slate-50/50"
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-bold text-sm text-emerald-900">Negocio Popular</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                  Hasta $20k
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                1 sola obligación de Renta en Mayo ($0 a $60 USD). Sin IVA periódico. Emite notas de venta físicas.
              </p>
            </div>
          </div>
        </div>

        {/* Checkbox: Actividades Excluidas (Condición Mixta) */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5">
          <label className="flex items-start space-x-3 cursor-pointer">
            <input
              type="checkbox"
              checked={tieneActividadesExcluidas}
              onChange={(e) => setTieneActividadesExcluidas(e.target.checked)}
              className="w-4 h-4 mt-0.5 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
            />
            <div>
              <span className="text-xs font-bold text-slate-800 block">
                Percibo ingresos por actividades excluidas del RIMPE
              </span>
              <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
                Servicios profesionales con título, arriendos, transporte o comisiones. Se añadirá la declaración de IVA
                bajo Régimen General.
              </p>
            </div>
          </label>
        </div>

        {/* Fila: Año Fiscal y Correo */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5 flex items-center">
              <Calendar className="w-3.5 h-3.5 mr-1 text-slate-500" />
              Ejercicio Fiscal
            </label>
            <select
              value={anio}
              onChange={(e) => setAnio(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-100 outline-none"
            >
              <option value={2026}>2026 (Oficial)</option>
              <option value={2025}>2025</option>
              <option value={2027}>2027</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5 flex items-center">
              <Mail className="w-3.5 h-3.5 mr-1 text-slate-500" />
              Correo Electrónico
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="correo@ejemplo.com"
              className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:border-blue-600 focus:ring-2 focus:ring-blue-100 outline-none"
            />
          </div>
        </div>

        {/* Mensaje de Error del Backend si existe */}
        {errorBackend && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
            <span className="leading-relaxed">{errorBackend}</span>
          </div>
        )}

        {/* Botón Principal de Envío */}
        <button
          type="submit"
          disabled={!estadoRuc.valido || cargando}
          className={`w-full py-3 px-4 rounded-xl font-bold text-sm text-white shadow-md transition-all flex items-center justify-center space-x-2 ${
            !estadoRuc.valido || cargando
              ? "bg-slate-400 cursor-not-allowed opacity-80"
              : "bg-gradient-to-r from-blue-700 to-indigo-700 hover:from-blue-800 hover:to-indigo-800 active:scale-[0.99] hover:shadow-lg"
          }`}
        >
          {cargando ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Calculando Vencimientos...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 text-amber-300" />
              <span>Generar Mi Calendario Tributario</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
