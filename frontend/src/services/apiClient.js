/**
 * Cliente HTTP y Capa de Servicios para la API del Calendario Tributario RIMPE
 * Asignatura: Ingeniería de Software con IA Generativa
 * Caso N.º 11 – Grupo 11
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Bandera para pruebas offline (por defecto en false para conectar con la API real en vivo)
export const USE_MOCKS = false;

/**
 * Catálogo mock determinista para pruebas offline de emergencia.
 */
const MOCK_CALENDARIO_EMPRENDEDOR = {
  ruc: "0923456784001",
  noveno_digito: 8,
  tipo_regimen: "RIMPE_EMPRENDEDOR",
  anio_fiscal: 2026,
  tiene_actividades_excluidas: false,
  total_obligaciones: 3,
  eventos: [
    {
      id: "evt-iva-sem1-2026",
      codigo_obligacion: "IVA_SEMESTRAL_1",
      titulo: "Declaración Semestral de IVA (Semestre 1: Ene - Jun)",
      fecha_vencimiento: "2026-07-24",
      fecha_nominal: "2026-07-24",
      fue_trasladada: false,
      motivo_traslado: "Día hábil regular",
      categoria: "RIMPE",
      color_identificador: "#2563eb",
      formulario_sri: "Formulario 104",
      descripcion: "Declaración del primer semestre de IVA ante el SRI para RIMPE Emprendedor.",
    },
    {
      id: "evt-iva-sem2-2026",
      codigo_obligacion: "IVA_SEMESTRAL_2",
      titulo: "Declaración Semestral de IVA (Semestre 2: Jul - Dic)",
      fecha_vencimiento: "2027-01-25",
      fecha_nominal: "2027-01-24",
      fue_trasladada: true,
      motivo_traslado: "Domingo trasladado al lunes hábil siguiente",
      categoria: "RIMPE",
      color_identificador: "#2563eb",
      formulario_sri: "Formulario 104",
      descripcion: "Declaración del segundo semestre de IVA ante el SRI para RIMPE Emprendedor.",
    },
    {
      id: "evt-renta-emp-2026",
      codigo_obligacion: "RENTA_ANUAL_EMPRENDEDOR",
      titulo: "Declaración Anual de Impuesto a la Renta (Ejercicio Fiscal 2026)",
      fecha_vencimiento: "2027-03-24",
      fecha_nominal: "2027-03-24",
      fue_trasladada: false,
      motivo_traslado: "Día hábil regular",
      categoria: "RIMPE",
      color_identificador: "#1d4ed8",
      formulario_sri: "Formulario Renta Personas Naturales",
      descripcion: "Declaración anual y liquidación sobre la base de ingresos brutos gravados aplicando tabla progresiva.",
    },
  ],
};

/**
 * Función genérica de petición con captura de errores del backend FastAPI y LOPDP.
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    const latencyHeader = response.headers.get("x-process-time-ms");

    let data;
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      let mensajeError = "Error en el servidor backend";
      if (typeof data === "object" && data !== null) {
        if (typeof data.detail === "string") {
          mensajeError = data.detail;
        } else if (Array.isArray(data.detail)) {
          // Errores de validación Pydantic HTTP 422
          mensajeError = data.detail.map((err) => `${err.loc?.slice(-1)[0] || "campo"}: ${err.msg}`).join(" | ");
        }
      }

      const errorObj = new Error(mensajeError);
      errorObj.status = response.status;
      errorObj.data = data;
      errorObj.latencyMs = latencyHeader;
      throw errorObj;
    }

    return { data, latencyMs: latencyHeader };
  } catch (err) {
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      const connError = new Error(
        `No se pudo conectar con el servidor backend en ${API_BASE_URL}. Asegúrate de que FastAPI esté ejecutándose con 'uvicorn backend.main:app'.`
      );
      connError.status = 0;
      throw connError;
    }
    throw err;
  }
}

/**
 * Calcula el calendario personalizado de obligaciones tributarias para el contribuyente.
 * @param {Object} perfilData - { ruc, tipo_regimen, anio, tiene_actividades_excluidas }
 */
export async function calcularCalendario(perfilData) {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 400));
    return { data: MOCK_CALENDARIO_EMPRENDEDOR, latencyMs: "12.5" };
  }

  const payload = {
    ruc: perfilData.ruc.trim(),
    tipo_regimen: perfilData.tipo_regimen,
    anio: perfilData.anio || 2026,
    tiene_actividades_excluidas: Boolean(perfilData.tiene_actividades_excluidas),
  };

  return await apiRequest("/api/perfil/calcular-vencimientos", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Obtiene la explicación pedagógica generada con IA (Google Gemini Flash) o catálogo de contingencia.
 * @param {Object} payload - { codigo_obligacion, tipo_regimen, fecha_vencimiento, noveno_digito, ruc, es_declaracion_en_cero }
 */
export async function obtenerExplicacion(payload) {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 600));
    const enCero = Boolean(payload.es_declaracion_en_cero);
    return {
      data: {
        recordatorio: {
          codigo_obligacion: payload.codigo_obligacion,
          titulo_pedagogico: enCero
            ? `[DECLARACIÓN EN CEROS] ${payload.codigo_obligacion}`
            : "Tu Declaración Tributaria RIMPE",
          resumen_didactico: enCero
            ? "ATENCIÓN - DECLARACIÓN EN CERO: Aunque no registraste ventas ni compras durante este período, el SRI exige presentar de forma 100% obligatoria la declaración informativa con valores en cero ($0.00). Omitir esta declaración genera multas automáticas inmediatas."
            : "Como contribuyente del régimen RIMPE debes presentar la declaración del período acumulado conforme a la normativa oficial.",
          formulario_sri: "Formulario en línea (portal del SRI)",
          comprobantes_validos: enCero
            ? "No se requieren facturas de ventas. En el formulario marca 'NO' a registrar información."
            : "Facturas electrónicas autorizadas y comprobantes de retención recibidos.",
          advertencia_en_cero:
            "La presentación en ceros es obligatoria. No presentarla dentro del plazo genera una sanción pecuniaria de $30 a $60 USD según el Art. 100 de la LRTI.",
          base_legal_oficial: "LRTI Art. 97.6, 97.8 y Resoluciones SRI NAC-DGERCGC24-00000027 / NAC-23-0034.",
          sugerencia_accion: enCero
            ? "1. Accede a SRI en Línea > Declaraciones. 2. En la pregunta inicial selecciona 'NO'. 3. Confirma que los casilleros queden en $0.00 y pulsa 'Firmar y Enviar'."
            : "Revisa tus facturas emitidas y recibidas al menos 5 días antes de la fecha límite.",
          canal_recomendado: "Portal SRI en Línea (www.sri.gob.ec) > Declaraciones.",
        },
        fuente: "GEMINI_FLASH",
        modelo: "gemini-3.8-flash",
        tiempo_generacion_segundos: 0.85,
      },
    };
  }

  return await apiRequest("/api/obligaciones/explicar", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Simula la cuota o impuesto causado de Impuesto a la Renta según la Ley de Eficiencia Económica.
 * @param {Object} payload - { ingresos_brutos_anuales, tipo_regimen }
 */
export async function simularCuotaRenta(payload) {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 200));
    const ingresos = parseFloat(payload.ingresos_brutos_anuales) || 0;
    return {
      data: {
        ingresos_brutos_anuales: ingresos,
        tipo_regimen: payload.tipo_regimen,
        cuota_estimada_usd: ingresos <= 20000 ? 60.0 : 60.0 + (ingresos - 20000) * 0.01,
        detalle_calculo: "Cálculo simulado basado en el Art. 23 de la Ley de Eficiencia Económica.",
        alerta_transicion: ingresos > 20000 && payload.tipo_regimen === "RIMPE_NEGOCIO_POPULAR"
          ? "Tus ingresos superan el límite de $20,000 USD de Negocio Popular."
          : null,
      },
    };
  }

  return await apiRequest("/api/simulador/renta", {
    method: "POST",
    body: JSON.stringify({
      ingresos_brutos: parseFloat(payload.ingresos_brutos ?? payload.ingresos_brutos_anuales) || 0.0,
      tipo_regimen: payload.tipo_regimen,
    }),
  });
}

/**
 * Valida un RUC de persona natural en el backend.
 * @param {string} ruc
 */
export async function validarRucEnBackend(ruc) {
  return await apiRequest("/api/perfil/validar-ruc", {
    method: "POST",
    body: JSON.stringify({ ruc }),
  });
}

/**
 * Obtiene la lista oficial de feriados nacionales del ejercicio fiscal.
 */
export async function obtenerFeriados() {
  return await apiRequest("/api/calendario/feriados", {
    method: "GET",
  });
}

/**
 * Verifica el estado operativo de salud del backend FastAPI.
 */
export async function verificarSaludBackend() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (res.ok) {
      const data = await res.json();
      return { online: true, data };
    }
    return { online: false, error: `HTTP ${res.status}` };
  } catch (err) {
    return { online: false, error: err.message };
  }
}
