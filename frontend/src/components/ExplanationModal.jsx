/**
 * Componente: Modal de Explicación Didáctica GenAI y Compuerta HITL
 * Asignatura: Ingeniería de Software con IA Generativa
 * Caso N.º 11 – Grupo 11
 */

import React, { useState, useEffect, useRef } from "react";
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
import { obtenerExplicacion, solicitarCodigoCorreo, enviarRecordatorioVerificado } from "../services/apiClient";

// Incluye el posible arranque en frío de Render Free y el límite del backend.
const EXPLANATION_TIMEOUT_MS = 90_000;

export default function ExplanationModal({
  isOpen,
  onClose,
  obligacion,
  perfil,
}) {
  const [cargando, setCargando] = useState(false);
  const [esperaProlongada, setEsperaProlongada] = useState(false);
  const [error, setError] = useState(null);
  const [explicacionData, setExplicacionData] = useState(null);
  const requestControllerRef = useRef(null);
  const requestIdRef = useRef(0);
  const [esDeclaracionEnCero, setEsDeclaracionEnCero] = useState(false);

  // Estados de la Compuerta HITL (Human-in-the-Loop) y Agente Autónomo
  const [confirmadoPorUsuario, setConfirmadoPorUsuario] = useState(false);
  const [emailDestino, setEmailDestino] = useState("");
  const [recordatorioProgramado, setRecordatorioProgramado] = useState(false);
  const [enviandoHitl, setEnviandoHitl] = useState(false);
  const [resultadoAgente, setResultadoAgente] = useState(null);
  const [errorEnvio, setErrorEnvio] = useState(null);
  const [codigo, setCodigo] = useState("");
  const [codigoSolicitado, setCodigoSolicitado] = useState(false);
  const [solicitandoCodigo, setSolicitandoCodigo] = useState(false);

  // Cargar explicación cada vez que se abre el modal con una nueva obligación
  useEffect(() => {
    if (!isOpen || !obligacion) {
      requestControllerRef.current?.abort();
      requestIdRef.current += 1;
      setCargando(false);
      setEsperaProlongada(false);
      setExplicacionData(null);
      setError(null);
      setRecordatorioProgramado(false);
      setConfirmadoPorUsuario(false);
      setResultadoAgente(null);
      setErrorEnvio(null);
      setCodigo("");
      setCodigoSolicitado(false);
      setEmailDestino("");
      return;
    }

    cargarExplicacion(esDeclaracionEnCero);
    return () => {
      requestControllerRef.current?.abort();
      requestIdRef.current += 1;
    };
  }, [isOpen, obligacion, esDeclaracionEnCero]);

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
    requestControllerRef.current?.abort();
    const controller = new AbortController();
    requestControllerRef.current = controller;
    const requestId = ++requestIdRef.current;
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, EXPLANATION_TIMEOUT_MS);
    const progressTimer = setTimeout(() => {
      if (requestId === requestIdRef.current) setEsperaProlongada(true);
    }, 8_000);
    setCargando(true);
    setEsperaProlongada(false);
    setError(null);
    setExplicacionData(null);

    try {
      const payload = {
        codigo_obligacion: obligacion.codigo_obligacion,
        tipo_regimen: perfil.tipo_regimen,
        fecha_vencimiento: obligacion.fecha_vencimiento,
        es_declaracion_en_cero: enCero,
      };

      const res = await obtenerExplicacion(payload, { signal: controller.signal });
      if (requestId === requestIdRef.current) setExplicacionData(res.data);
    } catch (err) {
      if (requestId === requestIdRef.current) {
        setError(timedOut
          ? "La explicación tardó demasiado. Puedes reintentar la consulta."
          : err.status === 429 && err.retryAfterSeconds
            ? `Se alcanzó el límite de consultas. Intenta de nuevo en ${err.retryAfterSeconds} segundos.`
            : err.message || "No se pudo cargar la explicación. Por favor, reintenta en unos momentos.");
      }
    } finally {
      clearTimeout(timeout);
      clearTimeout(progressTimer);
      if (requestId === requestIdRef.current) {
        requestControllerRef.current = null;
        setCargando(false);
        setEsperaProlongada(false);
      }
    }
  };

  const handleSolicitarCodigo = async () => {
    if (!emailDestino.trim()) return;
    setSolicitandoCodigo(true);
    setErrorEnvio(null);
    try {
      const respuesta = await solicitarCodigoCorreo(emailDestino.trim());
      setCodigoSolicitado(true);
      if (respuesta.data.estado === "INCIERTO") setErrorEnvio(respuesta.data.mensaje);
    } catch (err) {
      setErrorEnvio(err.message || "No se pudo enviar el código.");
    } finally {
      setSolicitandoCodigo(false);
    }
  };

  const handleProgramarRecordatorio = async (e) => {
    e.preventDefault();
    if (!confirmadoPorUsuario || !emailDestino.trim() || !/^\d{6}$/.test(codigo)) return;

    setEnviandoHitl(true);
    setErrorEnvio(null);

    try {
      const res = await enviarRecordatorioVerificado({
        email: emailDestino.trim(),
        codigo,
        codigo_obligacion: obligacion.codigo_obligacion,
        perfil: {
          ruc: perfil.ruc,
          razon_social: perfil.razon_social,
          tipo_regimen: perfil.tipo_regimen,
          email: emailDestino.trim(),
          tiene_actividades_excluidas: Boolean(perfil.tiene_actividades_excluidas),
        },
        anio: perfil.anio || 2026,
      });

      if (!res.data.exito) {
        throw new Error(res.data.respuesta_final || "No se pudo completar la operación.");
      }
      setResultadoAgente(res.data);
      setRecordatorioProgramado(true);
      setCodigo("");
    } catch (err) {
      setErrorEnvio(
        err.message || "No se pudo procesar la ejecución del agente tributario."
      );
    } finally {
      setEnviandoHitl(false);
    }
  };

  if (!isOpen || !obligacion) return null;

  const recordatorio = explicacionData?.obligacion || explicacionData?.recordatorio;
  const admiteDeclaracionEnCero = ["IVA_SEMESTRAL_1", "IVA_SEMESTRAL_2"].includes(obligacion.codigo_obligacion);
  const esFallback =
    explicacionData?.fuente === "CATALOGO_DETERMINISTA_FALLBACK" ||
    explicacionData?.modelo_utilizado === "fallback-determinista-sri";
  const modeloTexto = explicacionData?.modelo_utilizado || explicacionData?.modelo || "Origen no informado";
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
            className="absolute top-5 right-5 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors cursor-pointer"
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
          {admiteDeclaracionEnCero && <div
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
                  ¿No tuviste ventas ni compras en este semestre?{" "}
                  <strong className={esDeclaracionEnCero ? "text-emerald-900" : "text-slate-900"}>
                    (Activar Modo Declaración en Cero)
                  </strong>
                </span>
              </label>
              {esDeclaracionEnCero ? (
                <span className="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-emerald-600 text-white shadow-2xs">
                  Modo en Cero Activo
                </span>
              ) : null}
            </div>

            {/* Guía Visual Específica cuando está activado */}
            {esDeclaracionEnCero && (
              <div className="mt-3 pt-3 border-t border-emerald-200 text-xs space-y-2 animate-in fade-in duration-150">
                <div className="flex items-start space-x-2 text-emerald-900 font-bold">
                  <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>Revisa tu situación antes de declarar sin movimiento.</span>
                </div>
                <p className="text-emerald-800 text-[11px] leading-relaxed pl-6">
                  Confirma que no hubo operaciones y consulta las obligaciones activas de tu RUC.
                  No presupongas que el impuesto o una eventual sanción sean siempre de un importe fijo.
                </p>
                <div className="bg-white/80 rounded-xl p-2.5 border border-emerald-200/80 text-[11px] text-slate-700 space-y-1">
                  <span className="font-bold text-slate-900 block">
                    Antes de enviar en SRI en Línea:
                  </span>
                  <ol className="list-decimal list-inside space-y-0.5 text-slate-600 pl-1">
                    <li>Ingresa con RUC y clave a <em>Declaraciones &gt; Declaración de Impuestos</em>.</li>
                    <li>Selecciona el formulario correspondiente (<strong>{obligacion.formulario_sri}</strong>).</li>
                    <li>Contrasta los datos precargados con tus registros del semestre.</li>
                    <li>Si corresponde declarar sin movimiento, verifica el formulario antes de firmar y enviar.</li>
                  </ol>
                </div>
              </div>
            )}
          </div>}

          {cargando ? (
            <div className="py-12 flex flex-col items-center justify-center space-y-3">
              <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs text-slate-500 font-medium">
                Solicitando explicación didáctica...
              </p>
              {esperaProlongada && (
                <p className="text-xs text-slate-500 text-center max-w-sm">
                  La respuesta está tardando. Si Gemini no está disponible, mostraremos la explicación de contingencia.
                </p>
              )}
            </div>
          ) : error ? (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-800 flex items-start space-x-3">
              <AlertTriangle className="w-4 h-4 text-rose-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="font-bold">Error al procesar</p>
                <p className="text-[11px] mt-0.5">{error}</p>
                <button
                  type="button"
                  onClick={() => cargarExplicacion(esDeclaracionEnCero)}
                  className="mt-2 text-rose-700 underline font-semibold flex items-center space-x-1 cursor-pointer"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Reintentar consulta</span>
                </button>
              </div>
            </div>
          ) : recordatorio ? (
            <div className="space-y-4 text-xs">
              {/* 1. Resumen Didáctico */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4">
                <div className="flex items-center space-x-2 text-slate-800 font-bold mb-2">
                  <BookOpen className="w-4 h-4 text-blue-600" />
                  <span className="uppercase text-[11px] tracking-wider">Resumen Explicativo</span>
                </div>
                <p className="text-slate-600 leading-relaxed text-xs">
                  {recordatorio.explicacion_sencilla || "No se recibió una explicación para esta obligación."}
                </p>
              </div>

              {/* 2. Requisitos y Comprobantes Válidos */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4">
                <div className="flex items-center space-x-2 text-slate-800 font-bold mb-2">
                  <Receipt className="w-4 h-4 text-emerald-600" />
                  <span className="uppercase text-[11px] tracking-wider">Comprobantes y Documentos Válidos</span>
                </div>
                <p className="text-slate-600 leading-relaxed text-xs">
                  {recordatorio.comprobantes_validos || "Consulta en el SRI los comprobantes que sustentan esta obligación."}
                </p>
              </div>

              {/* 3. Base Legal Oficial y Citas */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4">
                <div className="flex items-center space-x-2 text-slate-800 font-bold mb-2">
                  <Scale className="w-4 h-4 text-indigo-600" />
                  <span className="uppercase text-[11px] tracking-wider">Base Legal y Fundamentación SRI</span>
                </div>
                <p className="text-slate-600 font-mono text-[11px] bg-white p-2.5 rounded-xl border border-slate-200/80 leading-relaxed">
                  {recordatorio.base_legal_oficial}
                </p>
              </div>

              {/* 4. Sugerencia de Acción y Canal */}
              <div className="bg-blue-50/70 border border-blue-200 rounded-2xl p-4">
                <div className="flex items-center space-x-2 text-blue-900 font-bold mb-2">
                  <Lightbulb className="w-4 h-4 text-amber-500" />
                  <span className="uppercase text-[11px] tracking-wider">Sugerencia de Acción</span>
                </div>
                <p className="text-blue-900 text-xs leading-relaxed mb-2 whitespace-pre-line">
                  {recordatorio.sugerencia_accion}
                </p>
                {recordatorio.canal_recomendado && (
                  <div className="flex items-center space-x-1.5 text-[11px] text-blue-700 font-semibold pt-2 border-t border-blue-100">
                    <ExternalLink className="w-3.5 h-3.5 text-blue-600" />
                    <span>Canal recomendado: {recordatorio.canal_recomendado}</span>
                  </div>
                )}
              </div>

              {/* Metadata de IA Generativa */}
              <div className="flex flex-wrap items-center justify-between gap-2 px-1 text-[11px] text-slate-400">
                <div className="flex items-center space-x-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
                  <span>
                    {esFallback ? "Explicación de contingencia: " : "Generado con "}<strong>{modeloTexto}</strong>
                    {tiempoTexto ? ` en ${tiempoTexto}s` : ""}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => cargarExplicacion(esDeclaracionEnCero)}
                  className="flex items-center space-x-1 hover:text-slate-700 transition-colors cursor-pointer"
                  title="Regenerar explicación con IA"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Regenerar</span>
                </button>
              </div>

              {/* 5. Compuerta Human-in-the-Loop (HITL) */}
              <div className="mt-6 pt-5 border-t border-slate-200 bg-slate-50/50 -mx-6 -mb-6 p-6 rounded-b-3xl">
                <div className="flex items-center space-x-2 mb-3">
                  <ShieldCheck className="w-5 h-5 text-blue-700" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    Compuerta de Envío Seguro (Human-in-the-Loop - Agente ReAct)
                  </h4>
                </div>

                {recordatorioProgramado ? (
                  <div className="space-y-3 animate-in fade-in duration-200">
                    <div className={`p-4 border rounded-2xl text-xs flex items-start space-x-3 ${resultadoAgente?.estado_envio === "ENVIADO" ? "bg-emerald-50 border-emerald-200 text-emerald-900" : "bg-amber-50 border-amber-200 text-amber-900"}`}>
                      <CheckCircle2 className={`w-5 h-5 flex-shrink-0 mt-0.5 ${resultadoAgente?.estado_envio === "ENVIADO" ? "text-emerald-600" : "text-amber-600"}`} />
                      <div className="space-y-1">
                        <p className="font-bold">
                          {resultadoAgente?.estado_envio === "ENVIADO"
                            ? "Recordatorio aceptado por Mailjet para envío"
                            : resultadoAgente?.estado_envio === "SIMULADO"
                            ? "Aprobación registrada en modo simulación; no se envió correo"
                            : resultadoAgente?.estado_envio === "ESTADO_INCIERTO"
                            ? "Resultado de Mailjet incierto; requiere revisión antes de reintentar"
                            : "El correo no se envió; revise la configuración o reintente"}
                        </p>
                        <p className="text-[11px] leading-relaxed">
                          {resultadoAgente?.respuesta_final ||
                            `Se procesó la solicitud para ${emailDestino}.`}
                        </p>
                        {resultadoAgente?.trazas_herramientas && (
                          <p className="text-[10px] font-mono text-emerald-700 pt-1">
                            Ciclo ReAct: {resultadoAgente.num_iteraciones} iteraciones | {resultadoAgente.trazas_herramientas.length} herramientas ejecutadas
                          </p>
                        )}
                      </div>
                    </div>

                    {resultadoAgente?.trazas_herramientas && resultadoAgente.trazas_herramientas.length > 0 && (
                      <div className="bg-white border border-slate-200 rounded-2xl p-3.5 text-[11px] space-y-2">
                        <span className="font-bold text-slate-700 block uppercase text-[10px] tracking-wider">
                          Bitácora de Razonamiento del Agente (ReAct Tools):
                        </span>
                        <div className="space-y-1.5 font-mono text-[10px]">
                          {resultadoAgente.trazas_herramientas.map((t, idx) => (
                            <div
                              key={idx}
                              className="flex items-center justify-between p-1.5 bg-slate-50 rounded-lg border border-slate-100"
                            >
                              <span className="text-blue-700 font-bold">
                                {idx + 1}. {t.herramienta}()
                              </span>
                              <span className="text-slate-400">
                                {new Date(t.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <form onSubmit={handleProgramarRecordatorio} className="space-y-3">
                    <div className="space-y-1">
                      <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                        Correo de Notificación
                      </label>
                      <div className="relative">
                        <input
                          type="email"
                          required
                          value={emailDestino}
                          onChange={(e) => {
                            setEmailDestino(e.target.value);
                            setCodigo("");
                            setCodigoSolicitado(false);
                          }}
                          placeholder="tu-correo@empresa.ec"
                          className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-300 bg-white focus:ring-2 focus:ring-blue-100 outline-none"
                        />
                        <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <button type="button" onClick={handleSolicitarCodigo} disabled={solicitandoCodigo || !emailDestino.trim()}
                        className="rounded-lg border border-blue-300 px-3 py-2 text-xs font-semibold text-blue-800 disabled:opacity-50">
                        {solicitandoCodigo ? "Enviando código..." : codigoSolicitado ? "Solicitar otro código" : "Enviar código de verificación"}
                      </button>
                      {codigoSolicitado && (
                        <label className="block text-[11px] font-bold text-slate-600">
                          Código recibido por correo
                          <input inputMode="numeric" pattern="[0-9]{6}" maxLength={6} value={codigo}
                            onChange={(e) => setCodigo(e.target.value.replace(/\D/g, ""))}
                            className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs" />
                        </label>
                      )}
                    </div>

                    <label className="flex items-start space-x-2.5 cursor-pointer p-2.5 bg-white rounded-xl border border-slate-200 hover:border-slate-300 transition-colors">
                      <input
                        type="checkbox"
                        checked={confirmadoPorUsuario}
                        onChange={(e) => setConfirmadoPorUsuario(e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500 mt-0.5 cursor-pointer"
                      />
                      <span className="text-xs text-slate-700 leading-snug">
                        <strong>Confirmo expresamente</strong> que he revisado las fechas y condiciones de esta
                        obligación tributaria y autorizo la ejecución del agente y despacho a mi correo.
                      </span>
                    </label>

                    <button
                      type="submit"
                      disabled={!confirmadoPorUsuario || !emailDestino.trim() || !/^\d{6}$/.test(codigo) || enviandoHitl}
                      className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-center space-x-2 ${
                        confirmadoPorUsuario && emailDestino.trim() && /^\d{6}$/.test(codigo) && !enviandoHitl
                          ? "bg-blue-700 hover:bg-blue-800 text-white shadow-sm hover:shadow cursor-pointer"
                          : "bg-slate-300 text-slate-500 cursor-not-allowed"
                      }`}
                    >
                      {enviandoHitl ? (
                        <>
                          <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>Ejecutando Agente ReAct con Compuerta HITL...</span>
                        </>
                      ) : (
                        <>
                          <Lock className="w-3.5 h-3.5 text-blue-200" />
                          <span>Autorizar y Ejecutar Agente Autónomo</span>
                        </>
                      )}
                    </button>
                    {errorEnvio && <p role="alert" className="text-xs text-rose-700">{errorEnvio}</p>}
                  </form>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
