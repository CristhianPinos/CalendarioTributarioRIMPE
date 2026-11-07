/**
 * Componente: Formulario de Perfil del Contribuyente RIMPE (Wizard Paso a Paso)
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
  ShieldCheck,
  Zap,
  ArrowRight,
  ArrowLeft,
  Check,
  User,
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

const PASOS = [
  { id: 1, titulo: "RUC", subtitulo: "Módulo 10" },
  { id: 2, titulo: "Régimen", subtitulo: "Tipo RIMPE" },
  { id: 3, titulo: "Contacto", subtitulo: "Correo y Año" },
  { id: 4, titulo: "Resumen", subtitulo: "Generar" },
];

export default function ProfileForm({ onGenerarCalendario, cargando, errorBackend }) {
  const [pasoActual, setPasoActual] = useState(1);
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

  const puedeAvanzarPaso1 = estadoRuc.valido;
  const puedeAvanzarPaso2 = Boolean(tipoRegimen);
  const puedeAvanzarPaso3 = email.trim().length > 3 && razonSocial.trim().length > 0;

  const handleSiguiente = () => {
    if (pasoActual === 1 && !puedeAvanzarPaso1) return;
    if (pasoActual === 2 && !puedeAvanzarPaso2) return;
    if (pasoActual === 3 && !puedeAvanzarPaso3) return;
    setPasoActual((prev) => Math.min(prev + 1, 4));
  };

  const handleAnterior = () => {
    setPasoActual((prev) => Math.max(prev - 1, 1));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!estadoRuc.valido) return;

    // Se despacha el perfil íntegro a App.jsx para coordinar calendario y notificaciones del agente
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
      {/* Encabezado del Formulario (idéntico al estilo actual) */}
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

        {/* Stepper Superior Integrado */}
        <div className="mt-4 pt-3 border-t border-blue-700/40 grid grid-cols-4 gap-1 sm:gap-2">
          {PASOS.map((paso) => {
            const completado = pasoActual > paso.id;
            const activo = pasoActual === paso.id;
            return (
              <button
                key={paso.id}
                type="button"
                onClick={() => {
                  if (paso.id < pasoActual) setPasoActual(paso.id);
                }}
                disabled={paso.id > pasoActual}
                className={`text-left p-1.5 rounded-lg transition-all ${
                  activo
                    ? "bg-white/20 text-white"
                    : completado
                    ? "text-blue-200 hover:bg-white/10 cursor-pointer"
                    : "text-blue-300/40 cursor-not-allowed"
                }`}
              >
                <div className="flex items-center space-x-1.5">
                  <div
                    className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                      completado
                        ? "bg-emerald-400 text-slate-900"
                        : activo
                        ? "bg-white text-blue-900"
                        : "bg-blue-800 text-blue-300"
                    }`}
                  >
                    {completado ? <Check className="w-3 h-3 stroke-[3]" /> : paso.id}
                  </div>
                  <div className="hidden sm:block">
                    <p className="text-[11px] font-bold leading-none">{paso.titulo}</p>
                    <p className="text-[9px] opacity-75 leading-tight">{paso.subtitulo}</p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-5">
        {/* Presets Rápidos de Demostración (diseño idéntico original) */}
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
                className="text-left p-2 rounded-lg border border-slate-200 bg-white hover:border-blue-300 hover:bg-blue-50/50 transition-all text-xs"
              >
                <p className="font-semibold text-slate-800 truncate">{preset.etiqueta}</p>
                <p className="text-[11px] text-slate-500 font-mono mt-0.5">{preset.ruc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* ============================================================ */}
        {/* PASO 1: RUC Y VALIDACIÓN MÓDULO 10                          */}
        {/* ============================================================ */}
        {pasoActual === 1 && (
          <div className="space-y-4 animate-in fade-in duration-150">
            <div>
              <label htmlFor="ruc-input-field" className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Número de RUC (13 dígitos)
              </label>
              <div className="relative">
                <input
                  id="ruc-input-field"
                  type="text"
                  maxLength={13}
                  value={ruc}
                  onChange={(e) => setRuc(e.target.value.replace(/\D/g, ""))}
                  placeholder="Ej: 0923456784001"
                  className={`w-full px-3.5 py-2.5 text-sm font-mono tracking-wider rounded-xl border transition-all outline-none ${
                    estadoRuc.valido
                      ? "border-emerald-300 bg-emerald-50/20 text-emerald-950 focus:ring-2 focus:ring-emerald-100"
                      : ruc.length === 13
                      ? "border-rose-300 bg-rose-50/20 text-rose-950 focus:ring-2 focus:ring-rose-100"
                      : "border-slate-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  }`}
                />
                <div className="absolute right-3 top-3">
                  {estadoRuc.valido ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  ) : ruc.length > 0 ? (
                    <AlertCircle className="w-5 h-5 text-rose-500" />
                  ) : null}
                </div>
              </div>

              {ruc.length > 0 && !estadoRuc.valido && (
                <p className="mt-1.5 text-xs text-rose-600 flex items-center">
                  <AlertCircle className="w-3.5 h-3.5 mr-1 flex-shrink-0" />
                  {estadoRuc.error || "RUC inválido según Módulo 10 del SRI."}
                </p>
              )}

              {estadoRuc.valido && (
                <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs space-y-1">
                  <div className="flex items-center justify-between text-emerald-900 font-bold">
                    <span>RUC Válido (Persona Natural)</span>
                    <span className="font-mono">Provincia: {estadoRuc.provincia}</span>
                  </div>
                  <p className="text-emerald-700 text-[11px]">
                    Noveno dígito: <strong className="font-mono text-sm">{estadoRuc.novenoDigito}</strong>
                    {" — "}Día nominal de vencimiento en el calendario:{" "}
                    <strong>{DIAS_POR_NOVENO_DIGITO[estadoRuc.novenoDigito]} de cada mes</strong>.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* PASO 2: SELECCIÓN DE RÉGIMEN RIMPE                          */}
        {/* ============================================================ */}
        {pasoActual === 2 && (
          <div className="space-y-4 animate-in fade-in duration-150">
            <div className="space-y-2">
              <label className="block text-xs font-bold text-slate-700 uppercase">
                Tipo de Régimen RIMPE
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setTipoRegimen("RIMPE_EMPRENDEDOR")}
                  className={`p-3.5 rounded-xl border text-left transition-all ${
                    tipoRegimen === "RIMPE_EMPRENDEDOR"
                      ? "border-blue-600 bg-blue-50/70 ring-2 ring-blue-500/20 shadow-xs"
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  }`}
                >
                  <p className="text-xs font-bold text-slate-900">RIMPE Emprendedor</p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Ingresos de $20.000,01 a $300.000 USD. Declaración semestral de IVA y Renta anual.
                  </p>
                </button>

                <button
                  type="button"
                  onClick={() => setTipoRegimen("RIMPE_NEGOCIO_POPULAR")}
                  className={`p-3.5 rounded-xl border text-left transition-all ${
                    tipoRegimen === "RIMPE_NEGOCIO_POPULAR"
                      ? "border-emerald-600 bg-emerald-50/70 ring-2 ring-emerald-500/20 shadow-xs"
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  }`}
                >
                  <p className="text-xs font-bold text-slate-900">RIMPE Negocio Popular</p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Ingresos hasta $20.000 USD. Cuota progresiva única en mayo ($0 a $60 USD).
                  </p>
                </button>
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
              <label className="flex items-start space-x-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={tieneActividadesExcluidas}
                  onChange={(e) => setTieneActividadesExcluidas(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500 mt-0.5"
                />
                <div className="text-xs">
                  <span className="font-bold text-slate-800">
                    ¿Realiza actividades excluidas de RIMPE?
                  </span>
                  <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">
                    Servicios profesionales, comisiones o arriendos. Activa una obligación complementaria obligatoria de IVA bajo Régimen General.
                  </p>
                </div>
              </label>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* PASO 3: CONTACTO (CORREO, RAZÓN SOCIAL Y AÑO)                */}
        {/* ============================================================ */}
        {pasoActual === 3 && (
          <div className="space-y-4 animate-in fade-in duration-150">
            <div>
              <label htmlFor="razon-social-field" className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Razón Social / Nombre Comercial
              </label>
              <div className="relative">
                <input
                  id="razon-social-field"
                  type="text"
                  required
                  value={razonSocial}
                  onChange={(e) => setRazonSocial(e.target.value)}
                  placeholder="Ej: Comercial Andina S.A."
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none"
                />
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
            </div>

            <div>
              <label htmlFor="email-notificacion-field" className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Correo Electrónico de Notificación (HITL)
              </label>
              <div className="relative">
                <input
                  id="email-notificacion-field"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="contribuyente@empresa.ec"
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none"
                />
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
            </div>

            <div>
              <label htmlFor="select-anio-fiscal" className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Año Fiscal
              </label>
              <div className="relative">
                <select
                  id="select-anio-fiscal"
                  value={anio}
                  onChange={(e) => setAnio(parseInt(e.target.value, 10))}
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-300 bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none"
                >
                  <option value={2026}>2026 (Ejercicio Fiscal Vigente)</option>
                  <option value={2025}>2025</option>
                  <option value={2024}>2024</option>
                </select>
                <Calendar className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* PASO 4: RESUMEN ANTES DE GENERAR EL CALENDARIO               */}
        {/* ============================================================ */}
        {pasoActual === 4 && (
          <div className="space-y-4 animate-in fade-in duration-150">
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs space-y-2">
              <div className="flex justify-between py-1 border-b border-slate-200/70">
                <span className="text-slate-500">RUC Persona Natural:</span>
                <span className="font-mono font-bold text-slate-800">{ruc}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/70">
                <span className="text-slate-500">Contribuyente:</span>
                <span className="font-bold text-slate-800">{razonSocial}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/70">
                <span className="text-slate-500">Noveno Dígito / Día:</span>
                <span className="font-bold text-blue-700">
                  Dígito {estadoRuc.novenoDigito} (Día {DIAS_POR_NOVENO_DIGITO[estadoRuc.novenoDigito]})
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/70">
                <span className="text-slate-500">Régimen:</span>
                <span className="font-bold text-slate-800">
                  {tipoRegimen === "RIMPE_EMPRENDEDOR" ? "RIMPE Emprendedor" : "RIMPE Negocio Popular"}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/70">
                <span className="text-slate-500">Actividades Excluidas:</span>
                <span className="font-bold text-slate-800">
                  {tieneActividadesExcluidas ? "Sí (Incluye IVA General)" : "No"}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Correo para HITL:</span>
                <span className="font-bold text-slate-800">{email}</span>
              </div>
            </div>
          </div>
        )}

        {/* Error del Backend si ocurriera */}
        {errorBackend && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 mt-0.5 flex-shrink-0" />
            <span>{errorBackend}</span>
          </div>
        )}

        {/* Botones de Navegación del Asistente */}
        <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-3">
          {pasoActual > 1 ? (
            <button
              type="button"
              onClick={handleAnterior}
              className="py-2.5 px-4 rounded-xl text-xs font-bold border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition-all flex items-center space-x-1.5 cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Anterior</span>
            </button>
          ) : (
            <div />
          )}

          {pasoActual < 4 ? (
            <button
              type="button"
              onClick={handleSiguiente}
              disabled={
                (pasoActual === 1 && !puedeAvanzarPaso1) ||
                (pasoActual === 2 && !puedeAvanzarPaso2) ||
                (pasoActual === 3 && !puedeAvanzarPaso3)
              }
              className={`py-2.5 px-5 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 ${
                (pasoActual === 1 && puedeAvanzarPaso1) ||
                (pasoActual === 2 && puedeAvanzarPaso2) ||
                (pasoActual === 3 && puedeAvanzarPaso3)
                  ? "bg-blue-700 hover:bg-blue-800 text-white shadow-sm cursor-pointer"
                  : "bg-slate-200 text-slate-400 cursor-not-allowed"
              }`}
            >
              <span>Siguiente</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={cargando || !estadoRuc.valido}
              className={`py-2.5 px-5 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
                cargando || !estadoRuc.valido
                  ? "bg-slate-300 text-slate-500 cursor-not-allowed"
                  : "bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm hover:shadow cursor-pointer"
              }`}
            >
              {cargando ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Calculando Vencimientos...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-emerald-200" />
                  <span>Generar Calendario Oficial</span>
                </>
              )}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}