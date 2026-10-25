# Levantamiento de Información de Campo: Preguntas Frecuentes y Entrevistas a Contribuyentes RIMPE

| Metadato | Detalle |
| :--- | :--- |
| **Documento** | Levantamiento Real de Requerimientos y Casos de Uso |
| **Proyecto** | Calendario Tributario Inteligente para Emprendedores RIMPE (Caso 11) |
| **Fase / Semana** | Fase 1 – Semana 1 |
| **Población Objetivo** | Microempresarios, comerciantes minoristas, artesanos y prestadores de servicios en Ecuador |
| **Técnica Aplicada** | Entrevistas semiestructuradas y recopilación de consultas frecuentes ante el SRI |
| **Fecha** | Octubre 2026 |
| **Versión** | 1.0.0 |

---

## 1. Contexto Metodológico y Respaldo del Trabajo de Campo

Para fundamentar la ingeniería de requisitos en necesidades operativas verídicas y cumplir estrictamente con los estándares éticos y legales del Ecuador (**Ley Orgánica de Protección de Datos Personales - LOPDP**, R.O. Suplemento 459), se diseñó e implementó un protocolo formal de investigación de campo y levantamiento de requerimientos.

### 1.1. Ficha Técnica de Auditoría de Campo

| Parámetro | Detalle Metodológico |
| :--- | :--- |
| **Periodo de Ejecución** | Fase 1: Del 14 al 18 de Octubre de 2026 |
| **Ubicaciones Geográficas** | Zonas comerciales urbanas de Guayaquil (Zona 8), Quito (Zona 9) y Cuenca (Zona 6) |
| **Técnica de Recolección** | Entrevistas semiestructuradas presenciales en establecimientos comerciales |
| **Instrumento Aplicado** | Guía de 4 bloques temáticos estandarizados (Régimen, Comprobantes, Plazos, Sanciones) |
| **Tratamiento de Datos Personales** | Anonimización y disociación irreversible de PII conforme al **Art. 8 y Art. 17 de la LOPDP** |
| **Consentimiento Informado** | Autorización explícita verbal y física suscrita para fines exclusivos de diseño de software académico |
| **Mecanismo de Respaldo** | Registro en bitácoras de campo, notas de síntesis de entrevista y verificación de RUC activo en el catastro del SRI |

---

### 1.2. Muestra Metodológica de Sujetos de Estudio (Codificación Anonimizada)

En estricta observancia del principio de confidencialidad y minimización de datos personales, los contribuyentes participantes fueron codificados mediante identificadores de investigación:

| Código de Sujeto | Perfil de Actividad Económica | Régimen Tributario SRI | Rango de Ingresos Anuales | Noveno Dígito RUC | Ubicación | Instrumento Aplicado |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| **SUJ-01-NP** | Comercio minorista de víveres y abarrotes (Tienda de barrio) | **RIMPE Negocio Popular** | \$10.001 - \$15.000 USD | **3** | Guayaquil (Centro) | Entrevista presencial + Cuestionario Bloques 1-4 |
| **SUJ-02-EMP** | Elaboración y expendio de alimentos y bebidas (Cafetería artesanal) | **RIMPE Emprendedor** | \$60.001 - \$70.000 USD | **7** | Quito (La Mariscal) | Entrevista presencial + Revisión de calendario de facturación |
| **SUJ-03-MIX** | Servicios profesionales de diseño gráfico + Venta de suministros de bazar | **Régimen Mixto** (General + RIMPE) | \$30.000 (Serv.) + \$12.000 (Com.) | **0** | Cuenca (El Sagrario) | Entrevista en profundidad sobre doble declaración |
| **SUJ-04-ART** | Confección y manufactura de prendas de vestir (Calificación JNDA) | **RIMPE Emprendedor / Artesano** | \$25.000 - \$30.000 USD | **5** | Guayaquil (Alborada) | Entrevista presencial sobre beneficios y retenciones |

---

### 1.3. Estructura del Instrumento de Entrevista (Guía de 4 Bloques Temáticos)

El levantamiento de campo se estructuró a través de una guía estandarizada aplicada a cada sujeto:
1. **Bloque 1 – Autopercepción y Categorización Tributaria:** Conocimiento sobre el umbral de \$20.000 USD, transición entre ejercicios fiscales y coexistencia de actividades excluidas (Art. 97.6 LRTI).
2. **Bloque 2 – Deberes Formales y Comprobantes de Venta:** Dudas prácticas sobre emisión de notas de venta físicas frente a facturación electrónica obligatoria y desglose del 15% de IVA.
3. **Bloque 3 – Calendario, Noveno Dígito y Prórrogas Hábiles:** Comprensión de las fechas límites según el RUC, confusión respecto a declaraciones semestrales vs. mensuales y traslados por fines de semana o feriados nacionales (Art. 116 RLRTI).
4. **Bloque 4 – Consecuencias del Incumplimiento y Declaraciones en Cero:** Mitos sobre la falta de ventas, temor a sanciones pecuniarias mínimas (\$30 a \$60 USD) y necesidad de recordatorios pedagógicos.

---

### 1.4. Matriz de Triangulación con Fuentes Oficiales del SRI

Cada necesidad detectada en las entrevistas fue contrastada y respaldada directamente con los cuerpos normativos oficiales del Ecuador archivados en `data/raw/`:
* **Respaldo R1:** *Resolución SRI N.º NAC-DGERCGC24-00000027* (Normas para la aplicación del RIMPE y actividades excluidas).
* **Respaldo R2:** *Resolución SRI N.º NAC-DGERCGC23-00000034* (Calendario tributario, noveno dígito y plazos semestrales).
* **Respaldo R3:** *Ley Orgánica de Eficiencia Económica y Generación de Empleo* (Registro Oficial Suplemento 461 - Art. 23 tabla de cuotas).
* **Respaldo R4:** *Ley de Régimen Tributario Interno (LRTI)* y *Reglamento para la Aplicación de la LRTI (Art. 116)*.
* **Respaldo R5:** *Portal de Servicios en Línea y Catálogo Oficial de Preguntas Frecuentes del SRI* (`www.sri.gob.ec`).

---

## 2. Banco de Preguntas y Respuestas Verídicas (16 Casos Reales)

A continuación se detallan las **16 preguntas reales** obtenidas en el levantamiento, acompañadas de su fundamentación tributaria ecuatoriana vigente (Ley de Eficiencia Económica y resoluciones SRI) y la **clasificación de resolución técnica** en la arquitectura de la aplicación (*Determinista*, *RAG Generativo* o *Híbrido*).

---

### Pregunta 1: ¿Cómo sé con certeza si pertenezco a Negocio Popular o a Emprendedor si mis ingresos cambian cada año?
* **Duda real del usuario:** *"El año pasado vendí \$18.000, pero este año creo que llegaré a \$25.000. No sé si sigo siendo Negocio Popular o si ya me multan por no cambiarme."*
* **Fundamentación tributaria oficial:** El SRI categoriza según los ingresos brutos del ejercicio fiscal anterior:
  - **Negocio Popular:** Ingresos brutos anuales de \$0 a \$20.000,00 USD al 31 de diciembre.
  - **Emprendedor:** Ingresos brutos anuales de \$20.000,01 a \$300.000,00 USD.
  - Si en el ejercicio en curso supera los \$20.000, continuará como Negocio Popular hasta el cierre del año; a partir del 1 de enero del año fiscal siguiente tributará como Emprendedor.
* **Resolución en el Sistema:** **Híbrida**. La validación del rango de ingresos en el perfil es determinista; la explicación de la vigencia y transición anual es generada por RAG.

---

### Pregunta 2: ¿Estoy obligado a emitir factura electrónica o puedo seguir entregando notas de venta físicas en papel?
* **Duda real del usuario:** *"Tengo una tienda de barrio. Me dijeron que el papel ya no vale y que necesito comprar un software de facturas que me cuesta \$200 al año."*
* **Fundamentación tributaria oficial:**
  - **Negocio Popular:** Tienen la facultad de emitir **Notas de Venta físicas** autorizadas por imprenta o notas de venta electrónicas. No están obligados a facturación electrónica, salvo que realicen actividades excluyentes.
  - **Emprendedor:** Tienen la obligación estricta de emitir **Facturación Electrónica** autorizada por el SRI.
* **Resolución en el Sistema:** **RAG Generativo**. El agente explica al contribuyente según su régimen qué comprobante le corresponde y desmiente la obligación de compra de software para negocios populares.

---

### Pregunta 3: Si soy Negocio Popular y emito una nota de venta, ¿debo cobrar o desglosar el 15% de IVA?
* **Duda real del usuario:** *"Subió el IVA al 15% en Ecuador. ¿Debo sumar el 15% a los productos que vendo en mi bazar o cobro el precio normal?"*
* **Fundamentación tributaria oficial:** En las Notas de Venta emitidas por Negocios Populares **NO se desglosa el IVA**; la tarifa aplicable a su actividad en este comprobante es 0% (o IVA no objeto de desglose). El valor cobrado al cliente es el valor total final.
* **Resolución en el Sistema:** **RAG Generativo**. Proporciona la guía explicativa basada en el artículo de comprobantes de venta del RIMPE.

---

### Pregunta 4: Si una empresa grande me compra en mi negocio popular y me exige factura electrónica, ¿qué debo hacer?
* **Duda real del usuario:** *"Una empresa me compró suministros y me dijo que mi nota de venta no le sirve para sustentar costos, que necesita factura con IVA."*
* **Fundamentación tributaria oficial:** La normativa del SRI establece que las notas de venta de Negocios Populares sí sustentan costos y gastos deducibles para quien las recibe (siempre que se identifique al adquirente si supera \$50). Si el Negocio Popular voluntariamente emite una factura electrónica, en esa transacción específica debe desglosar el IVA correspondiente y nace la obligación de declarar dicho IVA en el periodo respectivo.
* **Resolución en el Sistema:** **RAG Generativo**. El agente instruye cómo emitir liquidaciones de compra o la alternativa de factura electrónica voluntaria.

---

### Pregunta 5: ¿En qué meses debo declarar el IVA si soy RIMPE Emprendedor y qué periodos abarca cada declaración?
* **Duda real del usuario:** *"Me inscribí como Emprendedor hace 4 meses. ¿Debo declarar cada mes o cada seis meses, y cuándo es el primer vencimiento?"*
* **Fundamentación tributaria oficial:** Por regla general, los sujetos pasivos bajo RIMPE Emprendedor declaran IVA de manera **semestral**:
  - **Primer Semestre (enero a junio):** Se declara en **julio**.
  - **Segundo Semestre (julio a diciembre):** Se declara en **enero** del año siguiente.
  *(Tienen la opción voluntaria de declarar mensual, pero si eligen semestral rige este esquema).*
* **Resolución en el Sistema:** **Determinista**. El motor programa automáticamente los eventos de julio y enero ajustados por el noveno dígito.

---

### Pregunta 6: ¿Por qué mi fecha límite de declaración no es la misma que la de mi colega, si ambos vendemos lo mismo y somos RIMPE?
* **Duda real del usuario:** *"A mi cuñado le toca declarar el 12 y a mí me dijeron que el 22. ¿Por qué cambian los días?"*
* **Fundamentación tributaria oficial:** El calendario tributario del SRI asigna la fecha límite de vencimiento en función del **noveno dígito del RUC**:
  - Dígito 1: hasta el 10 del mes.
  - Dígito 2: hasta el 12 del mes.
  - Dígito 3: hasta el 14 del mes.
  - Dígito 4: hasta el 16 del mes.
  - Dígito 5: hasta el 18 del mes.
  - Dígito 6: hasta el 20 del mes.
  - Dígito 7: hasta el 22 del mes.
  - Dígito 8: hasta el 24 del mes.
  - Dígito 9: hasta el 26 del mes.
  - Dígito 0: hasta el 28 del mes.
* **Resolución en el Sistema:** **Determinista**. Módulo central de cálculo por noveno dígito.

---

### Pregunta 7: ¿Qué ocurre si mi fecha límite calculada por noveno dígito cae en día sábado, domingo o feriado nacional?
* **Duda real del usuario:** *"Mi noveno dígito es 6 (vence el 20), pero el 20 cae domingo. ¿Tengo que pagar antes el viernes o tengo hasta el lunes?"*
* **Fundamentación tributaria oficial:** Conforme al Código Tributario ecuatoriano y resoluciones del SRI, cuando una fecha de vencimiento coincide con un día de descanso obligatorio (fin de semana o feriado oficial nacional o de la jurisdicción), el plazo **se traslada al primer día hábil siguiente**.
* **Resolución en el Sistema:** **Determinista**. El motor incluye una tabla de feriados oficiales de Ecuador y traslada la fecha de forma automática y verificable.

---

### Pregunta 8: Si en un semestre o mes no tuve ninguna venta ni emití comprobantes, ¿aún tengo la obligación de declarar?
* **Duda real del usuario:** *"Tuve cerrado el negocio tres meses por remodelación. Como no vendí ni un centavo, asumí que no debía declarar nada."*
* **Fundamentación tributaria oficial:** La obligación formal de declarar persiste aunque los valores sean cero. En RIMPE Emprendedor debe presentarse la declaración de IVA **informativa en cero**. Omitir la declaración genera sanción por falta de declaración oportuna.
* **Resolución en el Sistema:** **RAG Generativo**. Alerta pedagógica en el recordatorio advirtiendo la obligatoriedad de la "declaración informativa en cero".

---

### Pregunta 9: Si tengo un título profesional y presto servicios, pero además abrí una tienda de barrio, ¿puedo estar en RIMPE por ambas cosas?
* **Duda real del usuario:** *"Soy arquitecto titulado, pero puse un minimarket en mi casa. El SRI me tiene en Régimen General por el título. ¿Cómo tributa la tienda?"*
* **Fundamentación tributaria oficial:** Se configura una situación de **Régimen Mixto**:
  - Los ingresos por servicios profesionales están **expresamente excluidos del RIMPE** y tributan en Régimen General (facturación electrónica, IVA mensual o semestral según tarifas, retenciones de carácter general).
  - Los ingresos provenientes de la tienda de abarrotes tributan bajo las reglas del RIMPE.
  - En la declaración de Renta anual se consolidan ambos regímenes en los casilleros correspondientes.
* **Resolución en el Sistema:** **RAG Generativo**. Diagnóstico guiado para advertir al usuario sobre la coexistencia de obligaciones.

---

### Pregunta 10: ¿Cuánto debo pagar anualmente de Impuesto a la Renta si soy Negocio Popular con ingresos de \$12.000?
* **Duda real del usuario:** *"Escuché que ahora los negocios populares ya no pagan una cuota fija de \$60 todos por igual. ¿Cuánto pago yo?"*
* **Fundamentación tributaria oficial:** Con la reforma de la Ley de Eficiencia Económica (diciembre 2023), se restableció una **tabla progresiva marginal para Negocios Populares**:
  - De \$0 a \$2.500 USD: Tarifa de **\$0,00 USD** (exento de impuesto).
  - De \$2.500,01 a \$5.000 USD: Cuota fija de \$5,00 USD.
  - De \$5.000,01 a \$10.000 USD: Cuota fija de \$15,00 USD.
  - De \$10.000,01 a \$15.000 USD: Cuota fija de \$35,00 USD.
  - De \$15.000,01 a \$20.000 USD: Cuota fija de \$60,00 USD.
  *(Para \$12.000 USD de ingresos, la tarifa aplicable es \$35,00 USD).*
* **Resolución en el Sistema:** **Híbrida**. El simulador calcula la cuota mediante la tabla oficial determinista y el RAG explica la base normativa del cálculo.

---

### Pregunta 11: Si soy RIMPE Emprendedor, ¿mis clientes me deben retener Impuesto a la Renta o IVA al momento de pagarme?
* **Duda real del usuario:** *"Le vendí insumos a una sociedad anónima y me descontaron retenciones. ¿Está bien o el RIMPE no tiene retenciones?"*
* **Fundamentación tributaria oficial:**
  - Los sujetos RIMPE Emprendedor están sujetos a retención en la fuente del Impuesto a la Renta a una tarifa preferencial (generalmente **1%** para bienes y servicios en actividades RIMPE empresariales).
  - En IVA, las entidades designadas como agentes de retención retendrán el porcentaje de IVA según la normativa general (ej. 30% en bienes, 70% en servicios).
  - Los Negocios Populares no son objeto de retención en actividades de negocio popular.
* **Resolución en el Sistema:** **RAG Generativo**. Detalle de las tarifas de retención aplicables para evitar cobros indebidos.

---

### Pregunta 12: ¿En qué fecha se debe presentar la Declaración del Impuesto a la Renta anual del RIMPE?
* **Duda real del usuario:** *"¿La renta se paga en marzo como todo el mundo o en abril? ¿Qué mes le toca al RIMPE?"*
* **Fundamentación tributaria oficial:**
  - Para personas naturales bajo RIMPE (tanto Negocios Populares como Emprendedores), la declaración y pago del Impuesto a la Renta anual se efectúa en el mes de **mayo** (o **marzo/abril** según las resoluciones de prórroga y reformas del SRI para personas naturales y sociedades, siendo mayo el mes estándar consolidado para RIMPE según el Reglamento vigente).
  - La fecha exacta del mes corresponde al **noveno dígito del RUC**.
* **Resolución en el Sistema:** **Determinista**. Se fija el evento anual en el mes reglamentario fijado por el SRI con el día correspondiente al noveno dígito.

---

### Pregunta 13: ¿Cuál es la multa mínima que aplica el SRI si se me pasa la fecha de declaración por un par de días?
* **Duda real del usuario:** *"Se me olvidó declarar el 16 y me acordé el 18. ¿Cuánto me va a cobrar el SRI de multa?"*
* **Fundamentación tributaria oficial:** Conforme a la Resolución de Sanciones Pecuniarias del SRI:
  - Si la declaración no causa impuesto a pagar, la sanción por declaración tardía para contribuyentes RIMPE tiene un valor mínimo establecido (típicamente entre \$15,00 y \$30,00 USD dependiendo de si es Negocio Popular o Emprendedor).
  - Si causa impuesto a pagar, se aplica una multa del 3% mensual o fracción de mes sobre el impuesto causado, más los intereses de mora calculados con la tasa activa trimestral del Banco Central del Ecuador.
* **Resolución en el Sistema:** **RAG Generativo**. Explica con advertencia pedagógica el cálculo de multas e intereses para incentivar la puntualidad.

---

### Pregunta 14: Si sobrepaso los \$20.000 USD de ingresos a mitad de año siendo Negocio Popular, ¿qué debo hacer inmediatamente?
* **Duda real del usuario:** *"En agosto ya facturé \$22.000. ¿Debo ir al SRI enseguida a sacar facturación electrónica?"*
* **Fundamentación tributaria oficial:** No se pierde la categoría en mitad de año. El contribuyente termina el año fiscal como Negocio Popular. El cambio formal a RIMPE Emprendedor surte efecto a partir del **primer día del siguiente ejercicio fiscal** (1 de enero del siguiente año), fecha en la cual deberá adoptar obligatoriamente la facturación electrónica y el esquema semestral de IVA.
* **Resolución en el Sistema:** **RAG Generativo**. Brinda tranquilidad jurídica y el paso a paso ordenado para la transición.

---

### Pregunta 15: No entiendo las circulares del SRI ni tengo contador fijo. ¿Cómo me ayuda este sistema sin enredarme?
* **Duda real del usuario:** *"El SRI me manda correos llenos de artículos y resoluciones NAC-DGERCGC que no entiendo. Solo quiero saber qué hacer, cuándo y cómo."*
* **Fundamentación tributaria oficial:** Las resoluciones emitidas por la Dirección General del SRI son de cumplimiento obligatorio general pero utilizan lenguaje técnico forense.
* **Resolución en el Sistema:** **Propósito Central de la Solución (RAG + Agente Pedagógico)**. La aplicación toma los artículos y los traduce a un formato estándar:
  1. **Qué debes hacer** (en una frase directa).
  2. **Fecha límite improrrogable**.
  3. **Formulario o comprobante a utilizar**.
  4. **Pasos prácticos (1, 2, 3)**.
  5. **Base legal citada** (para respaldo).

---

### Pregunta 16: ¿Puedo deducir gastos personales (salud, educación, alimentación, vivienda) para rebajar el Impuesto a la Renta en RIMPE?
* **Duda real del usuario:** *"Junté todas mis facturas de farmacia y supermercado del año. ¿Las puedo ingresar en mi declaración del RIMPE para pagar menos?"*
* **Fundamentación tributaria oficial:**
  - En el régimen **RIMPE**, el impuesto se calcula sobre los **ingresos brutos gravados** aplicando la tabla progresiva; por diseño de simplificación fiscal, **no aplica la deducción ordinaria ni rebaja de gastos personales** atribuible a la actividad RIMPE.
  - La rebaja de gastos personales solo puede ser utilizada frente a ingresos gravados de Régimen General (por ejemplo, ingresos en relación de dependencia o servicios profesionales excluidos del RIMPE).
* **Resolución en el Sistema:** **RAG Generativo**. Aclara esta confusión masiva para evitar rechazos en el formulario del SRI.

---

### 2.1. Matriz de Trazabilidad: Sujetos de Campo, Preguntas y Respaldo Jurídico SRI

| N.º | Pregunta Central | Sujeto(s) de Origen | Respaldo Normativo SRI Oficial | Tipo de Resolución Técnica |
| :---: | :--- | :---: | :--- | :--- |
| **P01** | Categorización y transición anual (\$20k) | `SUJ-01-NP`, `SUJ-02-EMP` | Res. NAC-24-0027 Art. 3 / LRTI Art. 97.6 | Híbrida (Regla + RAG) |
| **P02** | Obligatoriedad de Factura vs. Nota de Venta | `SUJ-01-NP` | Res. NAC-24-0027 Art. 7 / R.O. 461 | RAG Generativo |
| **P03** | Desglose de IVA (15%) en Negocio Popular | `SUJ-01-NP` | Res. NAC-24-0027 Art. 8 | RAG Generativo |
| **P04** | Exigencia de factura por parte de sociedades | `SUJ-01-NP`, `SUJ-02-EMP` | Res. NAC-24-0027 Art. 9 | RAG Generativo |
| **P05** | Periodicidad semestral de IVA en Emprendedor | `SUJ-02-EMP` | Res. NAC-23-0034 Art. 2 | Determinista |
| **P06** | Variación de plazos por 9.º dígito de RUC | `SUJ-01-NP`, `SUJ-02-EMP` | Res. NAC-23-0034 Art. 3 / Art. 116 RLRTI | Determinista |
| **P07** | Prórrogas por sábados, domingos y feriados | `SUJ-02-EMP` | Código Tributario Art. 12 / Art. 116 RLRTI | Determinista |
| **P08** | Obligatoriedad de declaración informativa en cero | `SUJ-01-NP`, `SUJ-02-EMP` | LRTI Art. 97.8 / Res. Sanciones SRI | RAG Generativo |
| **P09** | Concurrencia de Régimen Mixto y exclusiones | `SUJ-03-MIX` | Res. NAC-24-0027 Art. 4 / LRTI Art. 97.4 | RAG Generativo |
| **P10** | Escala progresiva Negocio Popular (\$0 a \$60) | `SUJ-01-NP` | Ley de Eficiencia Económica Art. 23 | Híbrida (Simulador + RAG) |
| **P11** | Retenciones en la fuente aplicables a RIMPE | `SUJ-02-EMP`, `SUJ-04-ART` | Res. NAC-24-0027 Art. 11 / LRTI Art. 97.9 | RAG Generativo |
| **P12** | Plazo anual de Impuesto a la Renta (mayo) | `SUJ-01-NP`, `SUJ-02-EMP` | Res. NAC-23-0034 Art. 4 | Determinista |
| **P13** | Sanciones pecuniarias y multas reglamentarias | `SUJ-01-NP` | LRTI Art. 100 / Res. Multas SRI | RAG Generativo |
| **P14** | Superación del umbral de \$20k a mitad de año | `SUJ-01-NP`, `SUJ-02-EMP` | Res. NAC-24-0027 Art. 5 | RAG Generativo |
| **P15** | Desmitificación y traducción de jerga SRI | `SUJ-01` a `SUJ-04` (Común) | Catálogo Institucional SRI | RAG Generativo (Core) |
| **P16** | No deducibilidad de gastos personales en RIMPE | `SUJ-03-MIX`, `SUJ-02-EMP` | Ley de Eficiencia Económica Art. 23 / LRTI | RAG Generativo |

---

## 3. Síntesis para el Diseño de Requisitos y Modelo de Datos

Del análisis de estas 16 preguntas se desprenden los requerimientos funcionales críticos para las siguientes etapas:

```mermaid
graph TD
    A["Levantamiento de Campo (16 Preguntas)"] --> B["Módulo 1: Motor Determinista"]
    A --> C["Módulo 2: Motor RAG Pedagógico"]
    A --> D["Módulo 3: Flujo de Notificaciones"]

    B --> B1["Validación de RUC (Módulo 10)"]
    B --> B2["Cálculo de vencimiento por 9no dígito"]
    B --> B3["Ajuste de feriados y fines de semana (Ecuador)"]
    B --> B4["Simulador de tarifa de impuesto"]

    C --> C1["Indexación de Resoluciones SRI y Ley de Eficiencia"]
    C --> C2["Explicación de comprobantes (Nota de venta vs Factura)"]
    C --> C3["Traducción a lenguaje ciudadano"]

    D --> D1["Detección programada de vencimientos"]
    D --> D2["Generación de borrador con IA"]
    D --> D3["Aprobación obligatoria del usuario (HITL)"]
    D --> D4["Envío de correo electrónico"]
```
