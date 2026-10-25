/**
 * Aplicación Principal - Calendario Tributario RIMPE
 * Asignatura: Ingeniería de Software con IA Generativa
 * Caso N.º 11 – Grupo 11
 */

import React, { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import ProfileForm from "./components/ProfileForm";
import CalendarView from "./components/CalendarView";
import ExplanationModal from "./components/ExplanationModal";
import TaxSimulatorModal from "./components/TaxSimulatorModal";
import Footer from "./components/Footer";
import { calcularCalendario } from "./services/apiClient";
import { Sparkles, Shield, AlertCircle, Info } from "lucide-react";

export default function App() {
  const [calendario, setCalendario] = useState(null);
  const [perfilActivo, setPerfilActivo] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [errorBackend, setErrorBackend] = useState(null);

  // Estados de Modales
  const [obligacionSeleccionada, setObligacionSeleccionada] = useState(null);
  const [modalExplicacionAbierto, setModalExplicacionAbierto] = useState(false);
  const [modalSimuladorAbierto, setModalSimuladorAbierto] = useState(false);

  // Cargar calendario inicial de demostración al iniciar para que la interfaz sea inmediatamente visible
  useEffect(() => {
    const perfilInicial = {
      ruc: "0923456784001",
      razon_social: "Comercial Pinos & Asociados",
      tipo_regimen: "RIMPE_EMPRENDEDOR",
      tiene_actividades_excluidas: false,
      anio: 2026,
      email: "cristhian.pinos@empresa.ec",
    };
    handleGenerarCalendario(perfilInicial);
  }, []);

  const handleGenerarCalendario = async (perfilData) => {
    setCargando(true);
    setErrorBackend(null);

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
                <strong>Arquitectura Híbrida:</strong> Fechas calculadas de forma matemática por Python (Zero Hallucination). Explicaciones generadas con Google Gemini Flash fundamentadas en los 7 PDFs oficiales del SRI.
              </span>
            </div>
            <div className="flex items-center space-x-2 flex-shrink-0 text-slate-400">
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              <span>Resoluciones SRI NAC-24-0027 y NAC-23-0034</span>
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
      <ExplanationModal
        isOpen={modalExplicacionAbierto}
        onClose={() => setModalExplicacionAbierto(false)}
        obligacion={obligacionSeleccionada}
        perfil={perfilActivo || calendario}
      />

      {/* Modal Simulador de Impuesto a la Renta */}
      <TaxSimulatorModal
        isOpen={modalSimuladorAbierto}
        onClose={() => setModalSimuladorAbierto(false)}
        regimenInicial={calendario?.tipo_regimen || "RIMPE_EMPRENDEDOR"}
      />

      {/* Pie de Página */}
      <Footer />
    </div>
  );
}
