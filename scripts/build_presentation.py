"""Regenera la presentación PDF de la fase 4 a partir de evidencias verificadas."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "sustentacion-grupo11.pdf"
W, H = 960, 540

NAVY = colors.HexColor("#071b3b")
DEEP = colors.HexColor("#0b2b58")
PANEL = colors.HexColor("#103967")
LINE = colors.HexColor("#31567d")
WHITE = colors.HexColor("#f7f9fd")
MUTED = colors.HexColor("#b8c9dd")
GOLD = colors.HexColor("#ffcb13")
BLUE = colors.HexColor("#79aaff")
TEAL = colors.HexColor("#55dfc8")
RED = colors.HexColor("#ff918f")

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

c = canvas.Canvas(str(OUTPUT), pagesize=(W, H), pageCompression=1)
c.setTitle("Calendario Tributario RIMPE - Presentación Grupo 11")
c.setAuthor("Cristhian Pinos y Juan Lucumi")


def txt(x, y, value, size=16, color=WHITE, bold=False):
    c.setFillColor(color)
    c.setFont("Arial-Bold" if bold else "Arial", size)
    c.drawString(x, y, value)


def wrapped(x, y, value, width, size=15, leading=21, color=WHITE, bold=False):
    font = "Arial-Bold" if bold else "Arial"
    for line in simpleSplit(value, font, size, width):
        txt(x, y, line, size, color, bold)
        y -= leading
    return y


def rect(x, y, w, h, fill=PANEL, radius=14, stroke=None):
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=int(stroke is not None))


def arrow(x1, y1, x2, y2, color=GOLD, width=2.5):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2 - 8, y2)
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(x2 - 10, y2 + 5)
    p.lineTo(x2 - 10, y2 - 5)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def base(number, section, source=None):
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#173e70"))
    for r in (185, 245, 305):
        c.circle(868, 362, r, fill=0, stroke=1)
    c.setFillColor(GOLD)
    c.rect(0, 0, 260, 7, fill=1, stroke=0)
    txt(54, 507, "CASO 11  /  GRUPO 11", 11, GOLD, True)
    txt(740, 507, "UNIANDES  2026", 11, WHITE, True)
    c.setStrokeColor(LINE)
    c.line(54, 491, 906, 491)
    txt(54, 29, section.upper(), 9, MUTED, True)
    txt(854, 29, f"{number:02d} / 11", 10, MUTED, True)
    if source:
        txt(54, 47, source, 8, MUTED)


def heading(title, sub=None):
    txt(54, 441, title, 31, WHITE, True)
    if sub:
        wrapped(54, 409, sub, 835, 15, 20, MUTED)


def finish():
    c.showPage()


# 1. Portada
base(1, "Presentación del proyecto")
txt(54, 385, "Calendario tributario", 42, WHITE, True)
txt(54, 331, "RIMPE", 53, GOLD, True)
wrapped(54, 281, "Fechas calculadas con Python, explicaciones asistidas por Gemini y recordatorios con autorización humana.", 475, 19, 27, WHITE)
txt(54, 135, "Cristhian Pinos  /  Juan Lucumi", 18, WHITE, True)
txt(54, 108, "Ingeniería de Software con IA Generativa", 14, MUTED)
rect(618, 149, 260, 251, DEEP, 22)
txt(645, 359, "PERFIL", 13, BLUE, True)
txt(645, 316, "RUC + régimen", 21, WHITE, True)
c.setStrokeColor(GOLD)
c.setFillColor(GOLD)
c.setLineWidth(2.5)
c.line(713, 291, 713, 266)
p = c.beginPath()
p.moveTo(713, 258)
p.lineTo(708, 268)
p.lineTo(718, 268)
p.close()
c.drawPath(p, fill=1, stroke=0)
txt(645, 229, "CALENDARIO", 13, GOLD, True)
txt(645, 190, "Fecha verificable", 20, WHITE, True)
finish()

# 2. Problema y objetivo
base(2, "Problema y objetivo")
heading("Una fecha depende de varios datos", "Un día de diferencia puede cambiar la oportunidad de una declaración.")
for x, label, detail, accent in [
    (54, "RUC", "Noveno dígito", BLUE),
    (335, "RÉGIMEN", "Obligación aplicable", TEAL),
    (616, "CALENDARIO", "Días inhábiles", GOLD),
]:
    rect(x, 245, 258, 108, DEEP, 14)
    txt(x + 18, 317, label, 13, accent, True)
    txt(x + 18, 279, detail, 19, WHITE, True)
arrow(140, 212, 480, 212, GOLD)
arrow(480, 212, 818, 212, GOLD)
rect(125, 94, 710, 96, PANEL, 12)
txt(149, 157, "OBJETIVO", 13, GOLD, True)
wrapped(149, 131, "Calcular el vencimiento desde reglas versionadas y mostrar qué debe revisar el contribuyente antes de declarar.", 660, 17, 23)
finish()

# 3. Experiencia
base(3, "Recorrido del contribuyente")
heading("Del perfil al recordatorio", "El correo se solicita al abrir un vencimiento; no forma parte del perfil del calendario.")
steps = [
    ("1", "Perfil", "RUC, régimen, nombre y año"),
    ("2", "Calendario", "Fechas y obligaciones"),
    ("3", "Detalle", "Guía y fuente normativa"),
    ("4", "Código", "Verifica el correo elegido"),
    ("5", "Confirmación", "Autoriza el envío puntual"),
]
for i, (n, name, detail) in enumerate(steps):
    x = 54 + i * 174
    c.setFillColor(GOLD if i == 4 else BLUE)
    c.circle(x + 20, 296, 20, fill=1, stroke=0)
    txt(x + 14, 290, n, 17, NAVY, True)
    txt(x, 243, name, 17, WHITE, True)
    wrapped(x, 218, detail, 142, 12, 16, MUTED)
    if i < 4:
        arrow(x + 50, 296, x + 166, 296, LINE, 2)
rect(54, 93, 852, 75, DEEP)
txt(75, 134, "RESULTADO", 12, TEAL, True)
wrapped(75, 110, "El usuario ve su calendario sin guardar un perfil y recibe un correo solo después de verificarlo y confirmar.", 803, 16, 21)
finish()

# 4. Arquitectura
base(4, "Arquitectura implementada", "Fuentes: backend/main.py y README.md")
heading("Una API conecta cálculo, IA y correo")
rect(54, 285, 188, 97, DEEP)
txt(73, 345, "REACT", 14, BLUE, True)
txt(73, 315, "Formulario y vista", 16, WHITE, True)
arrow(247, 334, 320, 334)
rect(322, 285, 192, 97, DEEP)
txt(342, 345, "FASTAPI", 14, GOLD, True)
txt(342, 315, "Rutas y controles", 16, WHITE, True)
arrow(519, 334, 592, 334)
rect(594, 285, 312, 97, DEEP)
txt(614, 345, "PYTHON", 14, TEAL, True)
txt(614, 315, "Obligaciones, fechas y montos", 16, WHITE, True)
for x, name, detail, accent in [
    (54, "RAG", "BM25 y siete PDF", BLUE),
    (344, "GEMINI", "Explica si responde", GOLD),
    (634, "MAILJET", "Correo por HTTPS", TEAL),
]:
    rect(x, 115, 270, 99, PANEL)
    txt(x + 17, 178, name, 14, accent, True)
    txt(x + 17, 145, detail, 15, WHITE)
txt(55, 80, "Las rutas de perfiles persistidos y escaneo periódico no están montadas.", 14, MUTED)
finish()

# 5. Motor determinista
base(5, "Cálculo por dentro", "Ejemplo del perfil de referencia 02 en eval/resultados_etapa6_render.json")
heading("Python fija la fecha del vencimiento", "Ejemplo de IVA semestral para noveno dígito 2, ejercicio 2026.")
rect(58, 221, 268, 130, DEEP)
txt(80, 313, "DÍA NOMINAL", 13, BLUE, True)
txt(80, 263, "12 JUL 2026", 30, WHITE, True)
arrow(340, 286, 478, 286, GOLD, 4)
rect(495, 221, 409, 130, PANEL)
txt(519, 313, "FECHA CALCULADA", 13, TEAL, True)
txt(519, 263, "13 JUL 2026", 31, WHITE, True)
rect(58, 102, 846, 78, DEEP)
txt(80, 149, "POR QUÉ CAMBIA", 12, GOLD, True)
txt(80, 120, "El 12 de julio cae domingo; la regla traslada el vencimiento al lunes 13.", 16, WHITE)
finish()

# 6. Explicación y agente
base(6, "Cómo funciona la IA", "Fuentes: docs/06-rag.md y backend/services/agent_service.py")
heading("Gemini explica; Python conserva el control")
rect(54, 166, 402, 216, DEEP)
txt(76, 345, "EXPLICACIÓN DEL VENCIMIENTO", 14, BLUE, True)
wrapped(76, 308, "El RAG recupera normas con BM25. Gemini redacta el resumen, los documentos y la sugerencia cuando responde.", 350, 16, 23)
rect(76, 193, 358, 48, PANEL, 8)
txt(91, 212, "Si falla: catálogo determinista identificado", 13, GOLD, True)
rect(504, 166, 402, 216, DEEP)
txt(526, 345, "AGENTE CON HERRAMIENTAS", 14, TEAL, True)
wrapped(526, 308, "Gemini puede elegir entre herramientas habilitadas por Python. El backend valida la elección y limita los pasos.", 350, 16, 23)
rect(526, 193, 358, 48, PANEL, 8)
txt(541, 212, "La ruta del agente no envía correos", 13, GOLD, True)
txt(54, 110, "La fecha mostrada se impone desde el cálculo Python incluso si el modelo propone otra.", 15, MUTED)
finish()

# 7. Seguridad
base(7, "Seguridad y privacidad", "Fuentes: backend/routers/correo_router.py, backend/main.py y docs/riesgos.md")
heading("El envío necesita una decisión humana")
checks = [
    ("01", "Destino verificado", "Código de seis dígitos enviado al mismo correo; vence en 10 minutos."),
    ("02", "Confirmación explícita", "El botón de envío requiere autorización y consume el código una sola vez."),
    ("03", "Datos mínimos", "El perfil no se registra. Códigos y límites se mantienen en memoria del proceso."),
    ("04", "Estados reales", "Aceptación de Mailjet, rechazo e incertidumbre se distinguen; los logs reducen identificadores."),
]
for i, (n, title, body) in enumerate(checks):
    y = 340 - i * 75
    rect(54, y - 32, 852, 66, DEEP, 11)
    txt(73, y - 4, n, 18, GOLD, True)
    txt(124, y + 6, title, 16, WHITE, True)
    txt(124, y - 17, body, 13, MUTED)
finish()

# 8. Evidencia pública
base(8, "Pruebas públicas", "Commit 414bc44; docs/07-evaluacion.md y docs/08-pruebas.md")
heading("La versión candidata pasó pruebas en Render", "Estas cifras corresponden al mismo commit identificado por /health y CI.")
metrics = [
    ("18/18", "casos HTTP", BLUE),
    ("10/10", "perfiles de referencia", TEAL),
    ("23/23", "fechas del dataset", GOLD),
    ("235", "pruebas backend en CI", WHITE),
]
for i, (value, label, accent) in enumerate(metrics):
    x = 54 + i * 218
    rect(x, 218, 197, 120, DEEP)
    txt(x + 17, 279, value, 31, accent, True)
    wrapped(x + 17, 248, label, 166, 14, 18, WHITE)
rect(54, 106, 852, 78, PANEL)
txt(75, 150, "RAG EN RENDER", 13, GOLD, True)
txt(75, 120, "15/16 Hit@3 por artículo; 4/5 pares exactos fuente-artículo en muestra curada.", 16, WHITE)
finish()

# 9. Comparación RAG
base(9, "Mejora del RAG", "Render: eval/resultados_etapa6_render.json. Local: eval/resultados_preg02_local.json")
heading("PREG-02 mejoró en local", "La publicación actual todavía corresponde a la medición anterior.")
for y, name, a, b, color in [
    (312, "Hit@3 por artículo", "15/16", "16/16", BLUE),
    (211, "Fuente y artículo exactos", "4/5", "5/5", TEAL),
]:
    txt(54, y + 33, name, 17, WHITE, True)
    rect(334, y, 200, 61, DEEP)
    txt(355, y + 20, a, 24, MUTED, True)
    arrow(546, y + 30, 631, y + 30, GOLD, 3)
    rect(647, y, 216, 61, PANEL)
    txt(670, y + 20, b, 24, color, True)
txt(339, 129, "RENDER", 12, MUTED, True)
txt(651, 129, "LOCAL POSTERIOR", 12, TEAL, True)
txt(54, 89, "Hit@3 es una coincidencia del evaluador; no acredita exactitud jurídica general.", 14, MUTED)
finish()

# 10. Integraciones y límites
base(10, "Integraciones y límites", "Fuentes: docs/08-pruebas.md y docs/09-decisiones.md")
heading("Qué se comprobó y qué queda limitado")
rect(54, 238, 403, 140, DEEP)
txt(75, 343, "GEMINI FLASH LITE", 14, GOLD, True)
wrapped(75, 307, "Produjo una explicación real en Render. Ante 429, 503 o timeout, la app muestra el catálogo de contingencia.", 350, 16, 22)
rect(503, 238, 403, 140, DEEP)
txt(524, 343, "MAILJET", 14, TEAL, True)
wrapped(524, 307, "El usuario recibió el código y el recordatorio en Gmail desde la demo. La respuesta del proveedor solo prueba aceptación.", 350, 16, 22)
rect(54, 102, 852, 100, PANEL)
txt(75, 170, "RENDER FREE", 14, BLUE, True)
wrapped(75, 141, "El almacenamiento es efímero. El registro de perfiles, la cola persistente y el escaneo periódico están desactivados.", 808, 16, 22)
finish()

# 11. Aporte del proyecto
base(11, "Aporte y cierre")
heading("Un calendario verificable y un envío controlado")
for x, title, body, accent in [
    (54, "Claridad", "El usuario ve fecha, obligación, formulario y documentos útiles.", BLUE),
    (344, "Trazabilidad", "Python calcula; las fuentes normativas se identifican y se evalúan.", GOLD),
    (634, "Control", "El correo requiere código y confirmación humana.", TEAL),
]:
    c.setStrokeColor(accent)
    c.setLineWidth(4)
    c.line(x, 333, x + 253, 333)
    txt(x, 291, title, 22, WHITE, True)
    wrapped(x, 259, body, 250, 16, 23, MUTED)
rect(54, 91, 852, 81, DEEP)
txt(75, 140, "Cristhian Pinos y Juan Lucumi", 18, WHITE, True)
txt(75, 111, "Proyecto académico independiente; no afiliado al SRI.", 14, MUTED)
finish()

c.save()
print(OUTPUT)
