/**
 * Componente: Vista Principal del Calendario Tributario Interactivo (FullCalendar)
 * Asignatura: Ingeniería de Software con IA Generativa
 * Caso N.º 11 – Grupo 11
 */

import React, { useRef, useState, useMemo } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/react/daygrid";
import interactionPlugin from "@fullcalendar/react/interaction";
import classicTheme from "@fullcalendar/react/themes/classic";
import "@fullcalendar/react/skeleton.css";
import "@fullcalendar/react/themes/classic/theme.css";
import "@fullcalendar/react/themes/classic/palette.css";
import {
  Calendar as CalendarIcon,
  Clock,
  AlertTriangle,
  Info,
  CheckCircle,
  Sparkles,
  ArrowRight,
  Shield,
  Layers,
  ChevronLeft,
  ChevronRight,
  CalendarDays,
  Tag,
  Zap,
} from "lucide-react";

export default function CalendarView({
  calendarioData,
  onSelectObligacion,
  cargando,
}) {
  const calendarRef = useRef(null);
  const [tituloMes, setTituloMes] = useState("Julio de 2026");
  const [mesActualKey, setMesActualKey] = useState("2026-07");

  // Lista de meses que tienen obligaciones tributarias para navegación rápida (chips)
  const mesesConObligaciones = useMemo(() => {
    if (!calendarioData?.eventos) return [];
    const map = new Map();
    calendarioData.eventos.forEach((evt) => {
      const ym = evt.fecha_vencimiento.substring(0, 7); // "YYYY-MM"
      if (!map.has(ym)) {
        const [y, m] = ym.split("-");
        const dateObj = new Date(parseInt(y, 10), parseInt(m, 10) - 1, 1);
        const nombreMes = dateObj.toLocaleDateString("es-EC", {
          month: "short",
          year: "numeric",
        });
        map.set(ym, {
          key: ym,
          dateStr: `${ym}-01`,
          label: nombreMes.charAt(0).toUpperCase() + nombreMes.slice(1),
          eventos: [],
        });
      }
      map.get(ym).eventos.push(evt);
    });
    return Array.from(map.values()).sort((a, b) => a.key.localeCompare(b.key));
  }, [calendarioData?.eventos]);

  // Vencimientos del mes actualmente visible
  const eventosMesActual = useMemo(() => {
    if (!calendarioData?.eventos) return [];
    return calendarioData.eventos.filter((e) =>
      e.fecha_vencimiento.startsWith(mesActualKey)
    );
  }, [calendarioData?.eventos, mesActualKey]);

  // Si no hay datos cargados aún, mostrar estado vacío didáctico
  if (!calendarioData) {
    return (
      <div className="bg-white rounded-2xl shadow-xs border border-slate-200 p-12 text-center flex flex-col items-center justify-center min-h-[550px]">
        <div className="w-16 h-16 bg-blue-50 text-blue-700 rounded-2xl flex items-center justify-center mb-4 shadow-2xs">
          <CalendarIcon className="w-8 h-8" />
        </div>
        <h3 className="text-xl font-bold text-slate-800 mb-2">
          Tu Calendario Tributario Inteligente
        </h3>
        <p className="text-sm text-slate-500 max-w-md mb-6 leading-relaxed">
          Ingresa tu RUC en el panel izquierdo para calcular de forma matemática y determinista
          tus fechas de vencimiento ante el SRI, considerando tu noveno dígito y los feriados de Ecuador.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-lg text-left">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
            <span className="font-bold text-xs text-blue-900 block mb-1">Cero Alucinaciones</span>
            <span className="text-[11px] text-slate-500">Fechas calculadas con Python según normativa del SRI.</span>
          </div>
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
            <span className="font-bold text-xs text-indigo-900 block mb-1">Explicaciones con IA</span>
            <span className="text-[11px] text-slate-500">Google Gemini Flash fundamentado en 7 PDFs oficiales.</span>
          </div>
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
            <span className="font-bold text-xs text-emerald-900 block mb-1">Prórrogas Hábiles</span>
            <span className="text-[11px] text-slate-500">Traslados automáticos por fines de semana y festivos.</span>
          </div>
        </div>
      </div>
    );
  }

  // Mapear eventos deterministas del backend a formato compatible con FullCalendar
  const eventosFullCalendar = (calendarioData.eventos || []).map((evento) => ({
    id: evento.id,
    title: evento.titulo,
    date: evento.fecha_vencimiento,
    backgroundColor: evento.color_identificador,
    borderColor: evento.color_identificador,
    textColor: "#ffffff",
    extendedProps: {
      ...evento,
    },
  }));

  // Ordenar cronológicamente para la lista de resumen lateral
  const eventosOrdenados = [...(calendarioData.eventos || [])].sort(
    (a, b) => new Date(a.fecha_vencimiento) - new Date(b.fecha_vencimiento)
  );

  // Manejadores de navegación del calendario
  const handlePrev = () => {
    calendarRef.current?.getApi()?.prev();
  };

  const handleNext = () => {
    calendarRef.current?.getApi()?.next();
  };

  const handleToday = () => {
    calendarRef.current?.getApi()?.today();
  };

  const handleGoToMonth = (dateStr) => {
    calendarRef.current?.getApi()?.gotoDate(dateStr);
  };

  const handleDatesSet = (dateInfo) => {
    const rawTitle = dateInfo.view.title || "";
    const formatted = rawTitle.charAt(0).toUpperCase() + rawTitle.slice(1);
    setTituloMes(formatted);

    const d = dateInfo.view.currentStart || dateInfo.start;
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    setMesActualKey(`${year}-${month}`);
  };

  // Render personalizado de cada evento en la cuadrícula mensual
  const renderEventContent = (eventInfo) => {
    const props = eventInfo.event.extendedProps;
    return (
      <div
        className="w-full p-1.5 rounded-lg text-left shadow-xs transition-all hover:scale-[1.02] cursor-pointer overflow-hidden border border-white/20 select-none"
        style={{ backgroundColor: props.color_identificador || "#2563eb" }}
      >
        <div className="flex items-center justify-between gap-1 mb-1">
          <span className="text-[9px] font-extrabold tracking-wider bg-white/25 text-white px-1.5 py-0.5 rounded uppercase">
            {props.formulario_sri || "SRI"}
          </span>
          {props.fue_trasladada && (
            <span
              title={`Trasladado: ${props.motivo_traslado}`}
              className="inline-flex items-center text-[9px] bg-amber-400 text-slate-950 font-black px-1.5 py-0.5 rounded shadow-2xs"
            >
              <AlertTriangle className="w-2.5 h-2.5 mr-0.5" />
              PRÓRROGA
            </span>
          )}
        </div>
        <div className="text-[11px] font-bold text-white leading-tight line-clamp-2 drop-shadow-xs">
          {eventInfo.event.title}
        </div>
        <div className="mt-1 flex items-center justify-between text-[10px] text-white/90 pt-1 border-t border-white/20">
          <span className="font-mono font-medium">{props.fecha_vencimiento}</span>
          <span className="text-[9px] font-semibold flex items-center">
            Ver pasos <ArrowRight className="w-2.5 h-2.5 ml-0.5" />
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-5">
      {/* Barra de Resumen de Contribuyente */}
      <div className="bg-white rounded-2xl shadow-xs border border-slate-200 p-5">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-blue-100 text-blue-800 rounded-2xl flex flex-col items-center justify-center font-bold shadow-xs">
              <span className="text-[10px] text-blue-600 uppercase font-semibold leading-none">Dígito</span>
              <span className="text-xl leading-none mt-0.5">{calendarioData.noveno_digito}</span>
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-bold text-slate-900 text-base font-mono">
                  RUC: {calendarioData.ruc}
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  {calendarioData.tipo_regimen === "RIMPE_EMPRENDEDOR"
                    ? "RIMPE Emprendedor"
                    : "RIMPE Negocio Popular"}
                </span>
                {calendarioData.tiene_actividades_excluidas && (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
                    Actividad Excluida (Mixto)
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Ejercicio Fiscal {calendarioData.anio_fiscal} • Vencimientos regidos por el noveno dígito • Total:{" "}
                <strong className="text-slate-700">{calendarioData.total_obligaciones} obligaciones anuales</strong>
              </p>
            </div>
          </div>

          {/* Leyenda de Colores Oficial */}
          <div className="flex flex-wrap items-center gap-3 text-xs bg-slate-50 p-2.5 rounded-xl border border-slate-200/70">
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-[#2563eb]" />
              <span className="text-slate-600 font-medium">IVA Semestral</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-[#1d4ed8]" />
              <span className="text-slate-600 font-medium">Renta Emprendedor</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-[#16a34a]" />
              <span className="text-slate-600 font-medium">Renta Neg. Popular</span>
            </div>
            {calendarioData.tiene_actividades_excluidas && (
              <div className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded-full bg-[#ea580c]" />
                <span className="text-slate-600 font-medium">Régimen General</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Contenedor Principal: Calendario Interactivo + Resumen de Vencimientos */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
        {/* FullCalendar Grid (3 Columnas) */}
        <div className="lg:col-span-3 bg-white rounded-2xl shadow-xs border border-slate-200 p-5 flex flex-col space-y-4">
          
          {/* BARRA SUPERIOR DE NAVEGACIÓN Y CONTROLES PERSONALIZADOS */}
          <div className="bg-gradient-to-r from-slate-50 via-blue-50/40 to-slate-50 p-4 rounded-2xl border border-slate-200">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              {/* Botones Avanzar / Retroceder y Hoy */}
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={handlePrev}
                  className="inline-flex items-center px-3 py-2 bg-white hover:bg-blue-50 border border-slate-200 hover:border-blue-300 text-slate-700 hover:text-blue-700 font-bold text-xs rounded-xl shadow-2xs transition-all active:scale-95"
                  title="Mes anterior"
                >
                  <ChevronLeft className="w-4 h-4 mr-1 text-slate-500 group-hover:text-blue-600" />
                  <span>Anterior</span>
                </button>

                <button
                  type="button"
                  onClick={handleToday}
                  className="inline-flex items-center px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-semibold text-xs rounded-xl shadow-2xs transition-all active:scale-95"
                  title="Ir al mes actual de hoy"
                >
                  <CalendarDays className="w-3.5 h-3.5 mr-1.5 text-blue-600" />
                  <span>Hoy</span>
                </button>

                <button
                  type="button"
                  onClick={handleNext}
                  className="inline-flex items-center px-3 py-2 bg-white hover:bg-blue-50 border border-slate-200 hover:border-blue-300 text-slate-700 hover:text-blue-700 font-bold text-xs rounded-xl shadow-2xs transition-all active:scale-95"
                  title="Mes siguiente"
                >
                  <span>Siguiente</span>
                  <ChevronRight className="w-4 h-4 ml-1 text-slate-500 group-hover:text-blue-600" />
                </button>
              </div>

              {/* Título Central y Badge de Vencimientos del Mes */}
              <div className="flex items-center space-x-3">
                <h4 className="text-lg sm:text-xl font-extrabold text-slate-900 tracking-tight">
                  {tituloMes}
                </h4>

                {eventosMesActual.length > 0 ? (
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200 shadow-2xs">
                    <Sparkles className="w-3 h-3 mr-1 text-blue-600" />
                    {eventosMesActual.length} {eventosMesActual.length === 1 ? "vencimiento" : "vencimientos"}
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-500 border border-slate-200">
                    Sin vencimientos
                  </span>
                )}
              </div>
            </div>

            {/* ACCESOS DIRECTOS: Meses con Obligaciones Tributarias */}
            {mesesConObligaciones.length > 0 && (
              <div className="mt-3 pt-3 border-t border-slate-200/80 flex flex-wrap items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 flex items-center mr-1">
                  <Tag className="w-3 h-3 mr-1 text-blue-600" />
                  Saltar a mes con vencimiento:
                </span>
                {mesesConObligaciones.map((m) => {
                  const isActive = m.key === mesActualKey;
                  const tieneProrroga = m.eventos.some((e) => e.fue_trasladada);
                  return (
                    <button
                      key={m.key}
                      type="button"
                      onClick={() => handleGoToMonth(m.dateStr)}
                      className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                        isActive
                          ? "bg-blue-700 text-white shadow-xs ring-2 ring-blue-500/30"
                          : "bg-white hover:bg-blue-50 text-slate-700 border border-slate-200 hover:border-blue-300"
                      }`}
                    >
                      <span
                        className={`w-2 h-2 rounded-full mr-1.5 ${
                          isActive
                            ? "bg-amber-300"
                            : m.eventos[0]?.color_identificador
                            ? ""
                            : "bg-blue-600"
                        }`}
                        style={{
                          backgroundColor: isActive
                            ? "#fde047"
                            : m.eventos[0]?.color_identificador,
                        }}
                      />
                      <span>{m.label}</span>
                      <span
                        className={`ml-1 text-[10px] font-mono px-1 rounded ${
                          isActive
                            ? "bg-blue-800 text-blue-100"
                            : "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {m.eventos.length}
                      </span>
                      {tieneProrroga && (
                        <span
                          title="Este mes incluye prórroga por feriado o fin de semana"
                          className="ml-1 text-[10px] text-amber-500 font-extrabold"
                        >
                          ⚠️
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* CUADRÍCULA FULLCALENDAR */}
          <div className="calendar-container">
            <FullCalendar
              key={`${calendarioData.ruc || "cal"}-${calendarioData.anio_fiscal || 2026}`}
              ref={calendarRef}
              plugins={[dayGridPlugin, interactionPlugin, classicTheme]}
              initialView="dayGridMonth"
              initialDate={`${calendarioData.anio_fiscal || 2026}-07-01`}
              locale="es"
              firstDay={1}
              fixedWeekCount={false}
              dayHeaderFormat={{ weekday: "short" }}
              dayCellClassNames={(arg) => {
                const dow = arg.date.getDay();
                return dow === 0 || dow === 6 ? "fc-fin-de-semana" : "";
              }}
              dayHeaderClassNames={(arg) => {
                const dow = arg.date.getDay();
                return dow === 0 || dow === 6 ? "fc-fin-de-semana-header" : "";
              }}
              headerToolbar={false}
              datesSet={handleDatesSet}
              events={eventosFullCalendar}
              eventContent={renderEventContent}
              eventClick={(info) => {
                info.jsEvent.preventDefault();
                onSelectObligacion(info.event.extendedProps);
              }}
              height="auto"
              dayMaxEvents={3}
            />
          </div>

          <div className="text-right text-[11px] text-slate-500 italic pt-1">
            💡 Haz clic en cualquier tarjeta de obligación para abrir la guía detallada de IA y requisitos del SRI.
          </div>
        </div>

        {/* Panel Lateral: Lista de Obligaciones Ordenadas (1 Columna) */}
        <div className="lg:col-span-1 space-y-3">
          <div className="bg-white rounded-2xl shadow-xs border border-slate-200 p-4">
            <h4 className="font-bold text-xs uppercase tracking-wider text-slate-700 mb-3 flex items-center">
              <Clock className="w-4 h-4 mr-1.5 text-blue-700" />
              Próximos Vencimientos
            </h4>

            <div className="space-y-2.5">
              {eventosOrdenados.map((evento) => (
                <div
                  key={evento.id}
                  onClick={() => onSelectObligacion(evento)}
                  className="p-3 rounded-xl border border-slate-200 hover:border-blue-300 hover:bg-blue-50/40 transition-all cursor-pointer group shadow-2xs hover:shadow-xs"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span
                      className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded text-white"
                      style={{ backgroundColor: evento.color_identificador }}
                    >
                      {evento.categoria}
                    </span>
                    <span className="text-xs font-bold font-mono text-slate-800">
                      {evento.fecha_vencimiento}
                    </span>
                  </div>

                  <h5 className="font-bold text-xs text-slate-800 group-hover:text-blue-800 transition-colors line-clamp-2">
                    {evento.titulo}
                  </h5>

                  {evento.fue_trasladada && (
                    <div className="mt-1.5 flex items-center text-[10px] text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                      <AlertTriangle className="w-3 h-3 mr-1 flex-shrink-0" />
                      <span className="truncate">{evento.motivo_traslado}</span>
                    </div>
                  )}

                  <div className="mt-2 flex items-center justify-between text-[11px] text-blue-700 font-semibold pt-1 border-t border-slate-100">
                    <span className="flex items-center">
                      <Sparkles className="w-3 h-3 mr-1 text-amber-500" />
                      Ver Explicación SRI
                    </span>
                    <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Tarjeta de Garantía Determinista */}
          <div className="bg-gradient-to-br from-slate-900 to-blue-950 text-white rounded-2xl p-4 shadow-xs">
            <div className="flex items-center space-x-2 mb-2 text-emerald-400 font-bold text-xs uppercase tracking-wider">
              <Shield className="w-4 h-4" />
              <span>Garantía Legal</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Todas las fechas mostradas están estrictamente calculadas mediante el código de rentas internas de Ecuador,
              garantizando <strong>0% de alucinación temporal</strong>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
