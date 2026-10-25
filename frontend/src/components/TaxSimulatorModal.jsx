/**
 * Componente: Modal Simulador de Impuesto a la Renta RIMPE (Ley de Eficiencia Económica)
 * Asignatura: Ingeniería de Software con IA Generativa
 * Caso N.º 11 – Grupo 11
 */

import React, { useState, useEffect } from "react";
import {
  X,
  Calculator,
  DollarSign,
  AlertTriangle,
  Scale,
  Sparkles,
  Info,
  CheckCircle,
  TrendingUp,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import { simularCuotaRenta } from "../services/apiClient";

const PRESETS_SIMULACION = [
  { etiqueta: "$1,500 (NP Cuota $0)", valor: 1500, regimen: "RIMPE_NEGOCIO_POPULAR" },
  { etiqueta: "$15,000 (NP Cuota $60)", valor: 15000, regimen: "RIMPE_NEGOCIO_POPULAR" },
  { etiqueta: "$35,000 (Emprendedor)", valor: 35000, regimen: "RIMPE_EMPRENDEDOR" },
  { etiqueta: "$85,000 (Emprendedor)", valor: 85000, regimen: "RIMPE_EMPRENDEDOR" },
  { etiqueta: "$220,000 (Emprendedor)", valor: 220000, regimen: "RIMPE_EMPRENDEDOR" },
];

export default function TaxSimulatorModal({
  isOpen,
  onClose,
  regimenInicial = "RIMPE_EMPRENDEDOR",
}) {
  const [tipoRegimen, setTipoRegimen] = useState(regimenInicial);
  const [ingresosBrutos, setIngresosBrutos] = useState("35000");
  const [cargando, setCargando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (regimenInicial) {
      setTipoRegimen(regimenInicial);
    }
  }, [regimenInicial]);

  // Ejecutar simulación automática al abrir o al cambiar valores
  useEffect(() => {
    if (!isOpen) return;
    ejecutarSimulacion(ingresosBrutos, tipoRegimen);
  }, [isOpen, tipoRegimen]);

  // Cerrar con Escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const ejecutarSimulacion = async (ingresos, regimen) => {
    const monto = parseFloat(ingresos);
    if (isNaN(monto) || monto < 0) {
      setError("Por favor ingresa un monto válido mayor o igual a 0.");
      setResultado(null);
      return;
    }

    if (monto > 300000 && regimen === "RIMPE_EMPRENDEDOR") {
      setError(
        "Los ingresos superan el límite legal de $300,000.00 USD para RIMPE. A partir de ese umbral corresponde tributar bajo el Régimen General."
      );
      setResultado(null);
      return;
    }

    setCargando(true);
    setError(null);

    try {
      const res = await simularCuotaRenta({
        ingresos_brutos: monto,
        tipo_regimen: regimen,
      });
      setResultado(res.data);
    } catch (err) {
      setError(err.message || "Error al calcular la simulación de renta.");
      setResultado(null);
    } finally {
      setCargando(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    ejecutarSimulacion(ingresosBrutos, tipoRegimen);
  };

  const aplicarPreset = (preset) => {
    setTipoRegimen(preset.regimen);
    setIngresosBrutos(String(preset.valor));
    ejecutarSimulacion(preset.valor, preset.regimen);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        {/* Cabecera */}
        <div className="bg-gradient-to-r from-slate-900 via-blue-950 to-indigo-950 p-6 text-white relative flex-shrink-0">
          <button
            onClick={onClose}
            className="absolute top-5 right-5 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
            title="Cerrar modal (Esc)"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center space-x-2 text-amber-400 text-xs font-bold uppercase tracking-wider mb-1">
            <Calculator className="w-4 h-4" />
            <span>Simulador Determinista Oficial SRI</span>
          </div>
          <h3 className="text-xl font-bold pr-10 leading-snug">
            Simulador de Impuesto a la Renta RIMPE
          </h3>
          <p className="text-xs text-slate-300 mt-1">
            Escala Progresiva según Ley de Eficiencia Económica (Art. 23 - R.O. 461)
          </p>
        </div>

        {/* Cuerpo del Formulario */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {/* Selector de Régimen */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
              Selecciona el Régimen del Contribuyente
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setTipoRegimen("RIMPE_NEGOCIO_POPULAR")}
                className={`py-2.5 px-3 rounded-xl text-xs font-bold border transition-all text-center ${
                  tipoRegimen === "RIMPE_NEGOCIO_POPULAR"
                    ? "border-emerald-600 bg-emerald-50 text-emerald-900 ring-2 ring-emerald-500/20"
                    : "border-slate-200 text-slate-600 hover:bg-slate-50"
                }`}
              >
                Negocio Popular (Hasta $20k)
              </button>
              <button
                type="button"
                onClick={() => setTipoRegimen("RIMPE_EMPRENDEDOR")}
                className={`py-2.5 px-3 rounded-xl text-xs font-bold border transition-all text-center ${
                  tipoRegimen === "RIMPE_EMPRENDEDOR"
                    ? "border-blue-600 bg-blue-50 text-blue-900 ring-2 ring-blue-500/20"
                    : "border-slate-200 text-slate-600 hover:bg-slate-50"
                }`}
              >
                Emprendedor ($20k a $300k)
              </button>
            </div>
          </div>

          {/* Presets Rápidos */}
          <div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">
              Montos de Ejemplo Rápido:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {PRESETS_SIMULACION.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => aplicarPreset(p)}
                  className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-xs text-slate-600 border border-slate-200 transition-colors"
                >
                  {p.etiqueta}
                </button>
              ))}
            </div>
          </div>

          {/* Formulario de Entrada */}
          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Ingresos Brutos Anuales Gravados ($ USD)
              </label>
              <div className="relative">
                <input
                  type="number"
                  step="any"
                  min="0"
                  required
                  value={ingresosBrutos}
                  onChange={(e) => setIngresosBrutos(e.target.value)}
                  placeholder="Ej: 35000"
                  className="w-full pl-9 pr-24 py-2.5 text-base font-bold font-mono rounded-xl border border-slate-300 focus:border-blue-600 focus:ring-2 focus:ring-blue-100 outline-none"
                />
                <DollarSign className="w-5 h-5 text-slate-400 absolute left-2.5 top-3" />
                <button
                  type="submit"
                  disabled={cargando}
                  className="absolute right-1.5 top-1.5 px-3 py-1.5 bg-blue-700 hover:bg-blue-800 text-white rounded-lg text-xs font-bold transition-colors"
                >
                  {cargando ? "Calculando..." : "Calcular"}
                </button>
              </div>
            </div>
          </form>

          {/* Mensaje de Error */}
          {error && (
            <div className="p-3.5 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-700 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Tarjeta de Resultado */}
          {resultado && !error && (
            <div className="space-y-4 animate-in fade-in duration-150">
              {/* Cuota Principal Destacada */}
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200/80 rounded-2xl p-5 text-center">
                <span className="text-xs font-bold text-blue-900 uppercase tracking-wider block mb-1">
                  Impuesto a la Renta Estimado (Ejercicio 2026)
                </span>
                <div className="text-3xl sm:text-4xl font-extrabold text-blue-900 font-mono tracking-tight my-1">
                  ${(resultado.impuesto_causado ?? resultado.cuota_estimada_usd ?? 0).toFixed(2)}{" "}
                  <span className="text-lg font-bold text-blue-700">USD</span>
                </div>
                <p className="text-xs text-slate-500">
                  Calculado sobre ingresos brutos de:{" "}
                  <strong>${parseFloat(ingresosBrutos).toLocaleString("en-US", { minimumFractionDigits: 2 })} USD</strong>
                </p>
              </div>

              {/* Desglose Matemático */}
              <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-4 text-xs space-y-2">
                <div className="flex items-center justify-between pb-1.5 border-b border-slate-200">
                  <span className="text-slate-500 font-medium">Régimen Evaluado:</span>
                  <span className="font-bold text-slate-800">
                    {resultado.tipo_regimen === "RIMPE_EMPRENDEDOR"
                      ? "RIMPE Emprendedor"
                      : "RIMPE Negocio Popular"}
                  </span>
                </div>

                {resultado.cuota_fija_usd != null && (
                  <div className="flex items-center justify-between pb-1.5 border-b border-slate-200">
                    <span className="text-slate-500 font-medium">Cuota Fija Anual:</span>
                    <span className="font-bold text-emerald-700">${Number(resultado.cuota_fija_usd).toFixed(2)} USD</span>
                  </div>
                )}

                {resultado.fraccion_basica != null && (
                  <div className="flex items-center justify-between pb-1.5 border-b border-slate-200">
                    <span className="text-slate-500 font-medium">Impuesto Fracción Básica:</span>
                    <span className="font-bold text-slate-800">${Number(resultado.fraccion_basica).toFixed(2)} USD</span>
                  </div>
                )}

                {resultado.tipo_marginal && (
                  <div className="flex items-center justify-between pb-1.5 border-b border-slate-200">
                    <span className="text-slate-500 font-medium">Tasa Marginal Excedente:</span>
                    <span className="font-bold text-blue-700">{resultado.tipo_marginal}</span>
                  </div>
                )}

                {resultado.tramo_aplicado && (
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">Tramo de Ingresos:</span>
                    <span className="font-bold text-slate-800">{resultado.tramo_aplicado}</span>
                  </div>
                )}
              </div>

              {/* Alerta de Transición si existe */}
              {resultado.alerta_transicion && (
                <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-900 flex items-start space-x-2.5">
                  <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <strong className="block font-bold">Alerta de Transición Obligatoria:</strong>
                    <span className="leading-relaxed">{resultado.alerta_transicion}</span>
                  </div>
                </div>
              )}

              {/* Nota Normativa */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/70 text-[11px] text-slate-500 flex items-start space-x-2">
                <Scale className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Fundamento Normativo:</strong> Art. 23 de la Ley de Eficiencia Económica y Art. 97.6 de la LRTI.
                  Este cálculo es referencial sobre ingresos brutos proyectados y no considera retenciones practicadas.
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
