/**
 * Aplicación Principal - Calendario Tributario RIMPE
 * Asignatura: Ingeniería de Software con IA Generativa
 * Caso N.º 11 – Grupo 11
 */

import React, { useState } from "react";
import Navbar from "./components/Navbar";
import ProfileForm from "./components/ProfileForm";
import CalendarView from "./components/CalendarView";
import ExplanationModal from "./components/ExplanationModal";
import TaxSimulatorModal from "./components/TaxSimulatorModal";
import Footer from "./components/Footer";
import { calcularCalendario } from "./services/apiClient";
import { CheckCircle2, Sparkles, Shield } from "lucide-react";

export default function App() {
  const [calendario, setCalendario] = useState(null);
  const [perfilActivo, setPerfilActivo] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [errorBackend, setErrorBackend] = useState(null);

  // Estados de Modales
  const [obligacionSeleccionada, setObligacionSeleccionada] = useState(null);
  const [modalExplicacionAbierto, setModalExplicacionAbierto] = useState(false);
  const [modalSimuladorAbierto, setModalSimuladorAbierto] = useState(false);

  const handleGenerarCalendario = async (perfilData) => {
    setCargando(true);
    setErrorBackend(null);
    setCalendario(null);
    setPerfilActivo(null);
    setObligacionSeleccionada(null);
    setModalExplicacionAbierto(false);

    try {
      const res = await calcularCalendario(perfilData);
      setCalendario(res.data);
      setPerfilActivo(perfilData);
    } catch (err) {
      console.error("Error al calcular calendario:", err);
      setErrorBackend(
        err.message || "Error al conectar con el servidor backend de FastAPI."
      );
    } finally {
      setCargando(false);
    }
  };

  const handleSeleccionarObligacion = (evento) => {
    setObligacionSeleccionada(evento);
    setModalExplicacionAbierto(true);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-800">
      {/* Barra de Navegación Superior */}
      <Navbar onAbrirSimulador={() => setModalSimuladorAbierto(true)} />

      {/* Banner de Transparencia de IA y Determinismo Legal */}
      <div className="bg-gradient-to-r from-blue-950 via-slate-900 to-indigo-950 text-white border-b border-blue-900/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between text-xs gap-2">
            <div className="flex items-center space-x-2">
              <span className="p-1 rounded bg-blue-500/20 text-blue-300">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              </span>
              <span className="text-slate-200">
                <strong>Arquitectura Híbrida:</strong> Fechas calculadas por Python. Explicaciones generadas con Gemini cuando está disponible; en caso contrario, se muestra el catálogo de contingencia.
              </span>
            </div>
            <div className="flex items-center space-x-2 flex-shrink-0 text-slate-400">
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              <span>Fuentes: LRTI, Reglamento y normativa RIMPE publicada por el SRI</span>
            </div>
          </div>
        </div>
      </div>

      {/* Contenido Principal */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Panel Izquierdo: Formulario de Perfil del Contribuyente (4 de 12 col) */}
          <div className="lg:col-span-4 space-y-6">
            <ProfileForm
              onGenerarCalendario={handleGenerarCalendario}
              cargando={cargando}
              errorBackend={errorBackend}
            />
            {perfilActivo && calendario && (
              <section aria-label="Resumen del perfil del calendario generado" className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
                <div className="flex items-center gap-2 text-emerald-700 mb-4">
                  <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                  <h3 className="font-bold text-sm">Perfil del calendario generado</h3>
                </div>
                <dl className="text-xs divide-y divide-slate-100">
                  <div className="flex justify-between gap-3 py-2">
                    <dt className="text-slate-500">Contribuyente</dt>
                    <dd className="font-semibold text-slate-800 text-right break-words min-w-0">{perfilActivo.razon_social}</dd>
                  </div>
                  <div className="flex justify-between gap-3 py-2">
                    <dt className="text-slate-500">RUC</dt>
                    <dd className="font-mono font-semibold text-slate-800">{perfilActivo.ruc}</dd>
                  </div>
                  <div className="flex justify-between gap-3 py-2">
                    <dt className="text-slate-500">Noveno dígito</dt>
                    <dd className="font-semibold text-slate-800">{calendario.noveno_digito}</dd>
                  </div>
                  <div className="flex justify-between gap-3 py-2">
                    <dt className="text-slate-500">Régimen</dt>
                    <dd className="font-semibold text-slate-800 text-right">
                      {perfilActivo.tipo_regimen === "RIMPE_EMPRENDEDOR" ? "RIMPE Emprendedor" : "RIMPE Negocio Popular"}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-3 py-2">
                    <dt className="text-slate-500">Año fiscal</dt>
                    <dd className="font-semibold text-slate-800">{calendario.anio_fiscal}</dd>
                  </div>
                  <div className="flex justify-between gap-3 py-2">
                    <dt className="text-slate-500">Actividades excluidas</dt>
                    <dd className="font-semibold text-slate-800">{perfilActivo.tiene_actividades_excluidas ? "Sí" : "No"}</dd>
                  </div>
                  <div className="flex justify-between gap-3 py-2">
                    <dt className="text-slate-500">Obligaciones</dt>
                    <dd className="font-semibold text-slate-800">{calendario.total_obligaciones}</dd>
                  </div>
                </dl>
                <p className="text-[11px] text-slate-500 mt-3">Este perfil solo se usa durante la sesión. El correo se solicita al abrir un vencimiento.</p>
              </section>
            )}
          </div>

          {/* Panel Derecho: Vista del Calendario Interactivo FullCalendar (8 de 12 col) */}
          <div className="lg:col-span-8">
            <CalendarView
              calendarioData={calendario}
              onSelectObligacion={handleSeleccionarObligacion}
              cargando={cargando}
            />
          </div>
        </div>
      </main>

      {/* Modal Didáctico de Explicación con IA y Compuerta HITL */}
      {modalExplicacionAbierto && <ExplanationModal
        isOpen={modalExplicacionAbierto}
        onClose={() => setModalExplicacionAbierto(false)}
        obligacion={obligacionSeleccionada}
        perfil={perfilActivo || calendario}
      />}

      {/* Modal Simulador de Impuesto a la Renta */}
      {modalSimuladorAbierto && (
        <TaxSimulatorModal
          isOpen
          onClose={() => setModalSimuladorAbierto(false)}
          regimenInicial={calendario?.tipo_regimen || "RIMPE_EMPRENDEDOR"}
        />
      )}

      {/* Pie de Página */}
      <Footer />
    </div>
  );
}
