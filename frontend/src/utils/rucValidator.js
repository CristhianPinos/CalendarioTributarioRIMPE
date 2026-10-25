/**
 * Validador de RUC de Persona Natural para Ecuador (Algoritmo Módulo 10 del SRI)
 * Asignatura: Ingeniería de Software con IA Generativa
 * Caso N.º 11 – Grupo 11
 */

/**
 * Valida si un RUC corresponde a una persona natural válida en Ecuador.
 * @param {string} ruc - Cadena de 13 dígitos numéricos.
 * @returns {{ valido: boolean, novenoDigito: number | null, provincia: string | null, error: string | null }}
 */
export function validarRucPersonaNatural(ruc) {
  if (!ruc) {
    return { valido: false, novenoDigito: null, provincia: null, error: "El RUC es requerido." };
  }

  const limpio = String(ruc).trim();

  // 1. Debe tener exactamente 13 caracteres numéricos
  if (!/^\d{13}$/.test(limpio)) {
    return {
      valido: false,
      novenoDigito: null,
      provincia: null,
      error: "El RUC debe tener exactamente 13 dígitos numéricos sin letras ni símbolos.",
    };
  }

  // 2. Validación de código de provincia (primeros dos dígitos: 01 a 24, o 30)
  const provincia = parseInt(limpio.slice(0, 2), 10);
  if ((provincia < 1 || provincia > 24) && provincia !== 30) {
    return {
      valido: false,
      novenoDigito: null,
      provincia: null,
      error: `El código de provincia '${limpio.slice(0, 2)}' no es válido en el Ecuador (01 a 24).`,
    };
  }

  // 3. Validación de tercer dígito para personas naturales: debe ser menor a 6
  const tercerDigito = parseInt(limpio[2], 10);
  if (tercerDigito >= 6) {
    return {
      valido: false,
      novenoDigito: null,
      provincia: null,
      error: "El tercer dígito debe ser menor a 6 para personas naturales (RIMPE).",
    };
  }

  // 4. Validación de establecimiento: debe terminar en 001
  const establecimiento = limpio.slice(10, 13);
  if (establecimiento !== "001") {
    return {
      valido: false,
      novenoDigito: null,
      provincia: null,
      error: "El RUC de persona natural debe registrar el establecimiento principal terminado en '001'.",
    };
  }

  // 5. Algoritmo Módulo 10 sobre los primeros 9 dígitos
  const coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2];
  let suma = 0;

  for (let i = 0; i < 9; i++) {
    let valor = parseInt(limpio[i], 10) * coeficientes[i];
    if (valor >= 10) {
      valor -= 9;
    }
    suma += valor;
  }

  const residuo = suma % 10;
  const digitoVerificadorEsperado = residuo === 0 ? 0 : 10 - residuo;
  const digitoVerificadorReal = parseInt(limpio[9], 10);

  if (digitoVerificadorEsperado !== digitoVerificadorReal) {
    return {
      valido: false,
      novenoDigito: null,
      provincia: null,
      error: `Dígito verificador inválido (${digitoVerificadorReal} no coincide con el algoritmo Módulo 10 del SRI).`,
    };
  }

  const novenoDigito = parseInt(limpio[8], 10);

  return {
    valido: true,
    novenoDigito,
    provincia: limpio.slice(0, 2),
    error: null,
  };
}
