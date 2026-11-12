/** Valida un monto monetario antes de solicitar el cálculo a Python. */
export function validarMonto(entrada) {
  const texto = entrada.trim();
  if (!texto) return { error: "Introduce los ingresos brutos anuales para calcular." };
  if (texto.startsWith("-")) return { error: "Los ingresos no pueden ser negativos." };
  if (!/^\d+(?:[.,]\d{1,2})?$/.test(texto)) {
    return { error: "Introduce un número sin separadores de miles y con máximo dos decimales (por ejemplo, 35000,50)." };
  }
  const monto = Number(texto.replace(",", "."));
  if (!Number.isFinite(monto)) return { error: "Introduce un monto válido." };
  if (monto > 300000) {
    return { error: "Los ingresos superan USD 300.000. Esta simulación RIMPE no calcula el Régimen General." };
  }
  return { monto };
}
