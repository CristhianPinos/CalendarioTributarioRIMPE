/** Simulador referencial de renta RIMPE. El cálculo se realiza en Python. */
import React, { useEffect, useRef, useState } from "react";
import { AlertTriangle, Calculator, CheckCircle2, DollarSign, Scale, X } from "lucide-react";
import { simularCuotaRenta } from "../services/apiClient";
import { validarMonto } from "../utils/simuladorValidation";

const EJEMPLOS = [
  { etiqueta: "Negocio Popular · $1.500", valor: "1500", regimen: "RIMPE_NEGOCIO_POPULAR" },
  { etiqueta: "Negocio Popular · $15.000", valor: "15000", regimen: "RIMPE_NEGOCIO_POPULAR" },
  { etiqueta: "Emprendedor · $35.000", valor: "35000", regimen: "RIMPE_EMPRENDEDOR" },
  { etiqueta: "Emprendedor · $85.000", valor: "85000", regimen: "RIMPE_EMPRENDEDOR" },
];

const formatoDinero = new Intl.NumberFormat("es-EC", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function nombreRegimen(regimen) {
  return regimen === "RIMPE_NEGOCIO_POPULAR" ? "RIMPE Negocio Popular" : "RIMPE Emprendedor";
}

export default function TaxSimulatorModal({ isOpen, onClose, regimenInicial = "RIMPE_EMPRENDEDOR" }) {
  const [tipoRegimen, setTipoRegimen] = useState(regimenInicial);
  const [ingresosBrutos, setIngresosBrutos] = useState("");
  const [cargando, setCargando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState("");
  const solicitudActual = useRef(0);

  useEffect(() => {
    if (!isOpen) return undefined;
    const cerrarConEscape = (evento) => {
      if (evento.key === "Escape") onClose();
    };
    window.addEventListener("keydown", cerrarConEscape);
    return () => window.removeEventListener("keydown", cerrarConEscape);
  }, [isOpen, onClose]);

  const limpiarResultado = () => {
    solicitudActual.current += 1;
    setCargando(false);
    setResultado(null);
    setError("");
  };

  const cambiarRegimen = (regimen) => {
    setTipoRegimen(regimen);
    limpiarResultado();
  };

  const cambiarIngresos = (valor) => {
    setIngresosBrutos(valor);
    limpiarResultado();
  };

  const ejecutarSimulacion = async (entrada, regimen) => {
    const idSolicitud = ++solicitudActual.current;
    setResultado(null);
    const validacion = validarMonto(entrada);
    if (validacion.error) {
      setCargando(false);
      setError(validacion.error);
      return;
    }

    setError("");
    setCargando(true);
    try {
      const respuesta = await simularCuotaRenta({
        ingresos_brutos: validacion.monto,
        tipo_regimen: regimen,
      });
      if (idSolicitud === solicitudActual.current) setResultado(respuesta.data);
    } catch (fallo) {
      if (idSolicitud === solicitudActual.current) {
        setError(fallo.message || "No se pudo calcular la simulación. Inténtalo de nuevo.");
      }
    } finally {
      if (idSolicitud === solicitudActual.current) setCargando(false);
    }
  };

  const seleccionarEjemplo = (ejemplo) => {
    setTipoRegimen(ejemplo.regimen);
    setIngresosBrutos(ejemplo.valor);
    ejecutarSimulacion(ejemplo.valor, ejemplo.regimen);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6">
      <div role="dialog" aria-modal="true" aria-labelledby="titulo-simulador" className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        <div className="bg-gradient-to-r from-slate-900 via-blue-950 to-indigo-950 p-6 text-white relative flex-shrink-0">
          <button type="button" onClick={onClose} aria-label="Cerrar simulador" className="absolute top-5 right-5 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white">
            <X className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2 text-amber-300 text-xs font-bold uppercase tracking-wider mb-1">
            <Calculator className="w-4 h-4" /> Simulador determinista
          </div>
          <h2 id="titulo-simulador" className="text-xl font-bold pr-10">Impuesto a la Renta RIMPE</h2>
          <p className="text-xs text-slate-300 mt-1">Estimación con la tabla RIMPE configurada para 2026. El cálculo lo realiza Python.</p>
        </div>

        <div className="p-5 sm:p-6 overflow-y-auto space-y-5 flex-1">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">1. Selecciona el régimen registrado en tu RUC</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {["RIMPE_NEGOCIO_POPULAR", "RIMPE_EMPRENDEDOR"].map((regimen) => (
                <button key={regimen} type="button" aria-pressed={tipoRegimen === regimen} onClick={() => cambiarRegimen(regimen)} className={`rounded-xl border px-3 py-3 text-sm font-semibold text-left transition-colors ${tipoRegimen === regimen ? "border-blue-600 bg-blue-50 text-blue-900 ring-2 ring-blue-500/20" : "border-slate-200 text-slate-600 hover:bg-slate-50"}`}>
                  {nombreRegimen(regimen)}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={(evento) => { evento.preventDefault(); ejecutarSimulacion(ingresosBrutos, tipoRegimen); }} className="space-y-3">
            <label htmlFor="ingresos-simulador" className="block text-xs font-bold uppercase tracking-wider text-slate-700">2. Introduce los ingresos brutos anuales gravados</label>
            <div className="relative">
              <DollarSign className="w-5 h-5 text-slate-400 absolute left-3 top-3" />
              <input id="ingresos-simulador" type="text" inputMode="decimal" autoComplete="off" value={ingresosBrutos} onChange={(evento) => cambiarIngresos(evento.target.value)} placeholder="Ej.: 35000,00" aria-describedby="ayuda-ingresos" className="w-full pl-10 pr-4 py-2.5 text-base font-semibold font-mono rounded-xl border border-slate-300 focus:border-blue-600 focus:ring-2 focus:ring-blue-100 outline-none" />
            </div>
            <p id="ayuda-ingresos" className="text-xs text-slate-500">Usa punto o coma decimal, sin separadores de miles. Máximo dos decimales.</p>
            <button type="submit" disabled={cargando} className="w-full py-2.5 px-4 rounded-xl text-sm font-bold text-white bg-blue-700 hover:bg-blue-800 disabled:bg-slate-400">
              {cargando ? "Calculando..." : "Calcular impuesto estimado"}
            </button>
          </form>

          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">O prueba un monto de ejemplo</p>
            <div className="flex flex-wrap gap-2">
              {EJEMPLOS.map((ejemplo) => (
                <button key={ejemplo.etiqueta} type="button" onClick={() => seleccionarEjemplo(ejemplo)} className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-xs text-slate-700 border border-slate-200">
                  {ejemplo.etiqueta}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div role="alert" className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-800 flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" /> <span>{error}</span>
            </div>
          )}

          {resultado && !error && (
            <section aria-live="polite" className="space-y-4">
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-5 text-center">
                <div className="flex items-center justify-center gap-1.5 text-blue-900 text-xs font-bold uppercase tracking-wider">
                  <CheckCircle2 className="w-4 h-4" /> Impuesto estimado
                </div>
                <p className="text-3xl sm:text-4xl font-extrabold text-blue-900 mt-2">${formatoDinero.format(resultado.impuesto_causado)} <span className="text-base">USD</span></p>
                <p className="text-xs text-slate-600 mt-2">Sobre ingresos de ${formatoDinero.format(resultado.ingresos_brutos)} USD</p>
              </div>

              <dl className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-xs divide-y divide-slate-200">
                <div className="flex justify-between gap-3 py-2"><dt className="text-slate-500">Régimen seleccionado</dt><dd className="font-semibold text-right">{nombreRegimen(resultado.tipo_regimen)}</dd></div>
                {resultado.alerta_transicion && <div className="flex justify-between gap-3 py-2"><dt className="text-slate-500">Tarifa aplicada</dt><dd className="font-semibold text-right">RIMPE Emprendedor</dd></div>}
                {resultado.cuota_fija_usd != null && <div className="flex justify-between gap-3 py-2"><dt className="text-slate-500">Cuota del tramo</dt><dd className="font-semibold">${formatoDinero.format(resultado.cuota_fija_usd)}</dd></div>}
                {resultado.fraccion_basica != null && <div className="flex justify-between gap-3 py-2"><dt className="text-slate-500">Impuesto a la fracción básica</dt><dd className="font-semibold">${formatoDinero.format(resultado.fraccion_basica)}</dd></div>}
                {resultado.tipo_marginal && <div className="flex justify-between gap-3 py-2"><dt className="text-slate-500">Tasa marginal excedente</dt><dd className="font-semibold">{resultado.tipo_marginal}</dd></div>}
                {resultado.tramo_aplicado && <div className="flex justify-between gap-3 py-2"><dt className="text-slate-500">Tramo aplicado</dt><dd className="font-semibold text-right">{resultado.tramo_aplicado}</dd></div>}
              </dl>

              {resultado.alerta_transicion && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-900 flex items-start gap-2">
                  <AlertTriangle className="w-5 h-5 flex-shrink-0" /> <span>{resultado.alerta_transicion}</span>
                </div>
              )}
              <p className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 flex gap-2">
                <Scale className="w-4 h-4 flex-shrink-0" /> Estimación referencial según el art. 97.6 de la LRTI. No incluye retenciones ni beneficios individuales; consulta tu declaración en el SRI.
              </p>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
