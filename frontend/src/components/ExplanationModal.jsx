/**
 * Componente: Modal de Explicación Didáctica GenAI y Compuerta HITL
 * Asignatura: Ingeniería de Software con IA Generativa
 * Caso N.º 11 – Grupo 11
 */

import React, { useState, useEffect } from "react";
import {
  X,
  Sparkles,
  BookOpen,
  FileText,
  Receipt,
  AlertTriangle,
  Scale,
  Lightbulb,
  CheckCircle,
  CheckCircle2,
  Mail,
  ShieldCheck,
  RefreshCw,
  ExternalLink,
  Lock,
} from "lucide-react";
import { obtenerExplicacion } from "../services/apiClient";

export default function ExplanationModal({
  isOpen,
  onClose,
  obligacion,
  perfil,
}) {
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [explicacionData, setExplicacionData] = useState(null);
  const [esDeclaracionEnCero, setEsDeclaracionEnCero] = useState(false);

  // Estados de la Compuerta HITL (Human-in-the-Loop)
  const [confirmadoPorUsuario, setConfirmadoPorUsuario] = useState(false);
  const [emailDestino, setEmailDestino] = useState(perfil?.email || "");
  const [recordatorioProgramado, setRecordatorioProgramado] = useState(false);
  const [enviandoHitl, setEnviandoHitl] = useState(false);

  // Cargar explicación cada vez que se abre el modal con una nueva obligación
  useEffect(() => {
    if (!isOpen || !obligacion) {
      setExplicacionData(null);
      setError(null);
      setRecordatorioProgramado(false);
      setConfirmadoPorUsuario(false);
      return;
    }

    cargarExplicacion(esDeclaracionEnCero);
  }, [isOpen, obligacion, esDeclaracionEnCero]);

  useEffect(() => {
    if (perfil?.email) {
      setEmailDestino(perfil.email);
    }
  }, [perfil]);

  // Cerrar con tecla Escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const cargarExplicacion = async (enCero) => {
    setCargando(true);
    setError(null);

    try {
      const payload = {
        codigo_obligacion: obligacion.codigo_obligacion,
        tipo_regimen: perfil.tipo_regimen,
        fecha_vencimiento: obligacion.fecha_vencimiento,
        noveno_digito: perfil.noveno_digito,
        ruc: perfil.ruc,
        es_declaracion_en_cero: enCero,
      };

      const res = await obtenerExplicacion(payload);
      setExplicacionData(res.data);
    } catch (err) {
      setError(
        err.message ||
          "No se pudo cargar la explicación con IA. Por favor, reintente en unos momentos."
      );
    } finally {
      setCargando(false);
    }
  };

  const handleProgramarRecordatorio = (e) => {
    e.preventDefault();
    if (!confirmadoPorUsuario) return;

    setEnviandoHitl(true);
    // Simulación de envío a través de la compuerta HITL
    setTimeout(() => {
      setEnviandoHitl(false);
      setRecordatorioProgramado(true);
    }, 700);
  };

  if (!isOpen || !obligacion) return null;

  const recordatorio = explicacionData?.obligacion || explicacionData?.recordatorio;
  const esFallback =
    explicacionData?.fuente === "CATALOGO_DETERMINISTA_FALLBACK" ||
    explicacionData?.modelo_utilizado === "fallback-determinista-sri";
  const modeloTexto =
    explicacionData?.modelo || explicacionData?.modelo_utilizado || "gemini-3.8-flash";
  const tiempoTexto =
    explicacionData?.tiempo_generacion_ms !== undefined && explicacionData?.tiempo_generacion_ms !== null
      ? (explicacionData.tiempo_generacion_ms / 1000).toFixed(2)
      : explicacionData?.tiempo_generacion_segundos
      ? Number(explicacionData.tiempo_generacion_segundos).toFixed(2)
      : null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        {/* Cabecera del Modal */}
        <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 p-6 text-white relative flex-shrink-0">
          <button
            onClick={onClose}
            className="absolute top-5 right-5 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
            title="Cerrar modal (Esc)"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center space-x-2 mb-2">
            <span
              className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full text-white"
              style={{ backgroundColor: obligacion.color_identificador }}
            >
              {obligacion.categoria}
            </span>
            <span className="text-xs text-blue-200">
              Formulario: <strong>{obligacion.formulario_sri}</strong>
            </span>
          </div>

          <h3 className="text-lg sm:text-xl font-bold pr-10 leading-snug">
            {recordatorio?.titulo_pedagogico || obligacion.titulo}
          </h3>

          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
            <span className="bg-white/15 px-3 py-1 rounded-lg font-mono font-bold text-white">
              Límite: {obligacion.fecha_vencimiento}
            </span>
            {obligacion.fue_trasladada && (
              <span className="bg-amber-400 text-slate-950 px-2.5 py-1 rounded-lg font-bold flex items-center text-[11px]">
                <AlertTriangle className="w-3.5 h-3.5 mr-1" />
                {obligacion.motivo_traslado}
              </span>
            )}
          </div>
        </div>

        {/* Cuerpo del Modal con Scroll */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {/* Banner de Declaración en Cero Toggle */}
          <div
            className={`border rounded-2xl p-4 transition-all duration-200 ${
              esDeclaracionEnCero
                ? "bg-emerald-50/90 border-emerald-300 ring-2 ring-emerald-500/20 shadow-xs"
                : "bg-slate-50 border-slate-200"
            }`}
          >
            <div className="flex items-center justify-between">
              <label className="flex items-center space-x-2.5 text-xs text-slate-700 font-semibold cursor-pointer">
                <input
                  type="checkbox"
                  checked={esDeclaracionEnCero}
                  onChange={(e) => setEsDeclaracionEnCero(e.target.checked)}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500 cursor-pointer"
                />
                <span>
                  ¿No tuviste ventas ni compras en este período?{" "}
                  <strong className={esDeclaracionEnCero ? "text-emerald-900" : "text-slate-900"}>
                    (Activar Modo Declaración en Cero)
                  </strong>
                </span>
              </label>
              {esDeclaracionEnCero ? (
                <span className="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-emerald-600 text-white shadow-2xs">
                  Modo en Cero Activo
                </span>
              ) : (
                <span className="text-[11px] text-slate-400 hidden sm:inline">
                  Art. 97.6 LRTI
                </span>
              )}
            </div>

            {/* Guía Visual Específica cuando está activado */}
            {esDeclaracionEnCero && (
              <div className="mt-3 pt-3 border-t border-emerald-200 text-xs space-y-2 animate-in fade-in duration-150">
                <div className="flex items-start space-x-2 text-emerald-900 font-bold">
                  <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>¿Es obligatorio declarar si no vendí nada? SÍ, 100% OBLIGATORIO.</span>
                </div>
                <p className="text-emerald-800 text-[11px] leading-relaxed pl-6">
                  Muchos emprendedores creen erróneamente que sin ventas no deben ingresar al sistema. 
                  En Ecuador, no declarar a tiempo genera una <strong>multa automática del SRI de $30 a $60 USD</strong> (Art. 100 LRTI), 
                  aunque el valor final a pagar de impuesto sea $0.00.
                </p>
                <div className="bg-white/80 rounded-xl p-2.5 border border-emerald-200/80 text-[11px] text-slate-700 space-y-1">
                  <span className="font-bold text-slate-900 block">
                    Pasos rápidos para tu declaración en cero en sri.gob.ec:
                  </span>
                  <ol className="list-decimal list-inside space-y-0.5 text-slate-600 pl-1">
                    <li>Ingresa con RUC y clave a <em>Declaraciones &gt; Declaración de Impuestos</em>.</li>
                    <li>Selecciona el formulario correspondiente (<strong>{obligacion.formulario_sri}</strong>).</li>
                    <li>En la pregunta <em>"¿Requiere registrar información para este período?"</em>, marca <strong>NO</strong>.</li>
                    <li>El portal completará los casilleros en <strong>$0.00</strong>. Haz clic en <strong>Firmar y Enviar</strong>.</li>
                  </ol>
                </div>
              </div>
            )}
          </div>

          {/* Estado de Carga con IA */}
          {cargando && (
            <div className="py-12 flex flex-col items-center justify-center space-y-3">
              <div className="relative">
                <div className="w-12 h-12 rounded-full border-4 border-blue-200 border-t-blue-700 animate-spin" />
                <Sparkles className="w-5 h-5 text-amber-500 absolute inset-0 m-auto animate-pulse" />
              </div>
              <p className="text-sm font-semibold text-slate-700">
                Consultando normativa oficial del SRI con Google Gemini Flash...
              </p>
              <p className="text-xs text-slate-400">
                Generando explicación didáctica estructurada y citas jurídicas
              </p>
            </div>
          )}

          {/* Estado de Error */}
          {!cargando && error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-700 space-y-2">
              <div className="flex items-center space-x-2 font-bold">
                <AlertTriangle className="w-4 h-4 text-red-600" />
                <span>Error al obtener la explicación generativa</span>
              </div>
              <p>{error}</p>
              <button
                onClick={() => cargarExplicacion(esDeclaracionEnCero)}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-red-600 text-white rounded-lg font-bold hover:bg-red-700 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Reintentar Consulta</span>
              </button>
            </div>
          )}

          {/* Contenido Explicativo Estructurado */}
          {!cargando && recordatorio && (
            <div className="space-y-4">
              {/* Badge del Modelo / Fuente */}
              <div className="flex items-center justify-between text-xs pb-2 border-b border-slate-100">
                <span className="inline-flex items-center text-indigo-700 font-semibold bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-100">
                  <Sparkles className="w-3.5 h-3.5 mr-1 text-indigo-600" />
                  {esFallback
                    ? "Catálogo Oficial SRI (Contingencia)"
                    : `Google Gemini Flash (${modeloTexto})`}
                </span>
                {tiempoTexto && (
                  <span className="text-slate-400 text-[11px]">
                    Latencia: {tiempoTexto}s
                  </span>
                )}
              </div>

              {/* 1. Resumen Didáctico */}
              <div className="bg-blue-50/60 border border-blue-100 rounded-2xl p-4">
                <h4 className="text-xs font-bold text-blue-900 uppercase tracking-wider mb-1.5 flex items-center">
                  <BookOpen className="w-4 h-4 mr-1.5 text-blue-700" />
                  ¿En qué consiste esta obligación?
                </h4>
                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                  {recordatorio.explicacion_sencilla || recordatorio.resumen_didactico}
                </p>
              </div>

              {/* 2. Grid de Formulario / Canal y Comprobantes / Sugerencia */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-3.5">
                  <h5 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-1 flex items-center">
                    <FileText className="w-3.5 h-3.5 mr-1.5 text-blue-700" />
                    Canal y Formulario Oficial
                  </h5>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {recordatorio.canal_recomendado || recordatorio.formulario_sri || obligacion.formulario_sri}
                  </p>
                </div>

                <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-3.5">
                  <h5 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-1 flex items-center">
                    <Receipt className="w-3.5 h-3.5 mr-1.5 text-emerald-700" />
                    Paso a Paso Recomendado
                  </h5>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {recordatorio.sugerencia_accion || recordatorio.comprobantes_validos || "Cumplir dentro del plazo establecido en el portal SRI en Línea."}
                  </p>
                </div>
              </div>

              {/* 3. Consecuencias por Incumplimiento o Multas */}
              <div className="bg-amber-50/70 border border-amber-200 rounded-2xl p-3.5">
                <h5 className="text-xs font-bold text-amber-900 uppercase tracking-wider mb-1 flex items-center">
                  <AlertTriangle className="w-3.5 h-3.5 mr-1.5 text-amber-700" />
                  Consecuencias por Incumplimiento o Declaración Tardía
                </h5>
                <p className="text-xs text-amber-900/90 leading-relaxed">
                  {recordatorio.consecuencia_incumplimiento || recordatorio.advertencia_en_cero}
                </p>
              </div>

              {/* 4. Base Legal y Consejo Práctico */}
              <div className="space-y-2">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/70 text-xs text-slate-600 flex items-start space-x-2">
                  <Scale className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-slate-800 block">Base Legal Oficial:</strong>
                    <span>{recordatorio.base_legal_oficial}</span>
                  </div>
                </div>

                {recordatorio.consejo_practico && (
                  <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200/70 text-xs text-emerald-800 flex items-start space-x-2">
                    <Lightbulb className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <strong className="block text-emerald-950">Consejo Práctico:</strong>
                      <span>{recordatorio.consejo_practico}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* 5. Compuerta Human-in-the-Loop (HITL) */}
              <div className="mt-6 pt-5 border-t border-slate-200 bg-slate-50/50 -mx-6 -mb-6 p-6 rounded-b-3xl">
                <div className="flex items-center space-x-2 mb-3">
                  <ShieldCheck className="w-5 h-5 text-blue-700" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    Compuerta de Envío Seguro (Human-in-the-Loop)
                  </h4>
                </div>

                {recordatorioProgramado ? (
                  <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-xs text-emerald-900 flex items-center space-x-3">
                    <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
                    <div>
                      <strong className="block font-bold text-sm">
                        ¡Recordatorio Programado con Éxito!
                      </strong>
                      <span>
                        Se ha registrado el recordatorio verificado para{" "}
                        <strong>{emailDestino}</strong> 5 días antes del vencimiento.
                      </span>
                    </div>
                  </div>
                ) : (
                  <form onSubmit={handleProgramarRecordatorio} className="space-y-3">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                        Correo de Notificación
                      </label>
                      <div className="relative">
                        <input
                          type="email"
                          required
                          value={emailDestino}
                          onChange={(e) => setEmailDestino(e.target.value)}
                          placeholder="tu-correo@empresa.ec"
                          className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-300 bg-white focus:ring-2 focus:ring-blue-100 outline-none"
                        />
                        <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                      </div>
                    </div>

                    <label className="flex items-start space-x-2.5 cursor-pointer p-2.5 bg-white rounded-xl border border-slate-200 hover:border-slate-300 transition-colors">
                      <input
                        type="checkbox"
                        checked={confirmadoPorUsuario}
                        onChange={(e) => setConfirmadoPorUsuario(e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500 mt-0.5"
                      />
                      <span className="text-xs text-slate-700 leading-snug">
                        <strong>Confirmo expresamente</strong> que he revisado las fechas y condiciones de esta
                        obligación tributaria y autorizo la programación del recordatorio a mi correo.
                      </span>
                    </label>

                    <button
                      type="submit"
                      disabled={!confirmadoPorUsuario || enviandoHitl}
                      className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-center space-x-2 ${
                        confirmadoPorUsuario && !enviandoHitl
                          ? "bg-blue-700 hover:bg-blue-800 text-white shadow-sm hover:shadow"
                          : "bg-slate-300 text-slate-500 cursor-not-allowed"
                      }`}
                    >
                      {enviandoHitl ? (
                        <>
                          <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>Autorizando con Compuerta HITL...</span>
                        </>
                      ) : (
                        <>
                          <Lock className="w-3.5 h-3.5 text-blue-200" />
                          <span>Autorizar y Programar Recordatorio por Correo</span>
                        </>
                      )}
                    </button>
                  </form>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
