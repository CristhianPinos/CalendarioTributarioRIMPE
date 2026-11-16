"""Comprueba una respuesta normativa real de la imagen Docker en ejecución.

El flujo de CI invoca este programa antes y después de `docker restart`.
No utiliza perfiles, correo, claves ni el proveedor Gemini.
"""

import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PREGUNTA = "Soy RIMPE negocio popular, ¿tengo que presentar declaraciones de IVA?"
FRASE_DIRECTA = "Los negocios populares no presentarán declaraciones de IVA."


def solicitar_json(url: str, payload: dict | None = None) -> dict:
    datos = json.dumps(payload).encode("utf-8") if payload is not None else None
    solicitud = Request(
        url,
        data=datos,
        headers={"Content-Type": "application/json"} if datos else {},
        method="POST" if datos else "GET",
    )
    with urlopen(solicitud, timeout=30) as respuesta:
        if respuesta.status != 200:
            raise AssertionError(f"HTTP {respuesta.status} en {url}")
        return json.load(respuesta)


def comprobar(base_url: str) -> dict:
    ultimo_error = None
    for intento in range(30):
        try:
            salud = solicitar_json(f"{base_url}/health")
            break
        except (HTTPError, URLError, TimeoutError) as error:
            ultimo_error = error
            time.sleep(2)
    else:
        raise AssertionError(f"El servicio no inició: {ultimo_error}")

    assert salud["status"] == "healthy", salud
    assert salud["checks"]["rag_chunks_available"] is True, salud

    resultado = solicitar_json(
        f"{base_url}/api/rag/consultar",
        {
            "pregunta": PREGUNTA,
            "regimen": "RIMPE_NEGOCIO_POPULAR",
            "top_k": 3,
        },
    )
    citas = resultado["citas"]
    assert resultado["se_abstuvo"] is False, resultado
    assert resultado["fragmentos_recuperados"] >= 1, resultado
    assert FRASE_DIRECTA in resultado["respuesta"], resultado
    assert any(
        "LRTI" in cita["documento"]
        and "Art. 97.9" in cita["articulo_seccion"]
        and (cita.get("url") or "").startswith("https://www.sri.gob.ec/")
        for cita in citas
    ), resultado

    return {
        "salud": salud["status"],
        "fragmentos_disponibles": salud["checks"]["rag_chunks_available"],
        "pregunta": PREGUNTA,
        "regimen": "RIMPE_NEGOCIO_POPULAR",
        "se_abstuvo": resultado["se_abstuvo"],
        "fragmentos_recuperados": resultado["fragmentos_recuperados"],
        "cita_directa": next(
            cita["cita_oficial"]
            for cita in citas
            if "LRTI" in cita["documento"] and "Art. 97.9" in cita["articulo_seccion"]
        ),
        "pasaje_directo_presente": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18080")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()

    evidencia = comprobar(args.base_url.rstrip("/"))
    if args.compare:
        anterior = json.loads(args.compare.read_text(encoding="utf-8"))
        assert evidencia == anterior, (anterior, evidencia)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(evidencia, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(evidencia, ensure_ascii=False))
    print("RAG verificado" + (" después del reinicio" if args.compare else " antes del reinicio"))


if __name__ == "__main__":
    main()
