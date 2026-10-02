# generar-csv-ofertas

Comando para [opencode](https://opencode.ai) que convierte las ofertas de empleo que
guardas como `.txt` (copias de portales como InfoJobs, WhatJobs o LinkedIn) en un
único CSV limpio y listo para Excel.

```text
Fecha,Portal de empleo,Descripción de la oferta,Ubicación,Estado de la oferta
2026-09-29,InfoJobs,Desarrollador Full Stack Remoto,20001 Donostia San Sebastián / Remoto,Vigente
```

- Sin dependencias de Python: solo `python3` de la máquina.
- Salida en **UTF-8 con BOM**, así que Excel en español la abre sin tocar nada.
- No inventa datos: si un campo no está en el `.txt`, queda vacío o `No identificado`.

---

## Contenido

- [Qué hace](#qué-hace)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Parámetros](#parámetros)
- [El CSV generado](#el-csv-generado)
- [El manifiesto](#el-manifiesto)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Ejemplo completo](#ejemplo-completo)
- [Actualizar y desinstalar](#actualizar-y-desinstalar)
- [Problemas frecuentes](#problemas-frecuentes)

---

## Qué hace

El comando recorre **todos los `.txt`** de la carpeta en la que ejecutas opencode
(archivos tipo `lista trabajos 23-09-2026.txt`), extrae una fila por oferta y escribe
el CSV en esa misma carpeta.

Por cada oferta determina:

| Campo | De dónde sale |
| --- | --- |
| `Descripción de la oferta` | La primera línea del bloque (el puesto). |
| `Ubicación` | La línea siguiente (`20001 Donostia San Sebastián / Remoto`, `Alicante, Alicante provincia – Trabajo híbrido`…). |
| `Portal de empleo` | Las marcas del portal en el texto; si se deduce por el formato, se marca `(inferido)`. Si no hay pistas: `No identificado`. |
| `Fecha` | El texto literal de publicación (`Hoy`, `Ayer`, `Publicado Hace 4 Días`, `23/09/2026 Actualizada`) restado de la fecha del nombre del archivo. |
| `Estado de la oferta` | `Vigente` o `Caducada` según el umbral de días que le pases. |

Los `.txt` se leen en **Latin-1 / Windows-1252**, que es como los guardan estos
portales; leerlos como UTF-8 rompe los acentos.

---

## Requisitos

| Herramienta | Para qué |
| --- | --- |
| [opencode](https://opencode.ai) — `npm i -g opencode-ai` | Ejecutar el comando. |
| `python3` 3.9+ | Generar y validar el CSV. |
| Node.js + npm | Solo si instalas con `npx`. |

---

## Instalación

### Opción 1 — con `npx` (recomendada)

[`tiged`](https://github.com/tiged/tiged) descarga el repositorio y lo desempaqueta
donde quieras, así que no necesitas clonar ni buscar la ruta del archivo a mano.

**Por proyecto** (el comando queda disponible en la carpeta donde tienes los `.txt`):

```bash
npx --yes tiged javierjuanJJ/generar-csv-ofertas /tmp/generar-csv-ofertas --force --disable-cache \
  && mkdir -p .opencode/commands .opencode/scripts \
  && cp /tmp/generar-csv-ofertas/.opencode/commands/generar-csv-ofertas.md .opencode/commands/ \
  && cp /tmp/generar-csv-ofertas/.opencode/scripts/ofertas_csv.py .opencode/scripts/
```

> El script se copia siempre al proyecto porque el CSV se genera sobre los `.txt` de
> esa misma carpeta. Si lo dejas solo en la carpeta global, el comando no lo
> encontrará.

**Global** (el comando `/generar-csv-ofertas` aparece en todos tus proyectos):

```bash
npx --yes tiged javierjuanJJ/generar-csv-ofertas /tmp/generar-csv-ofertas --force --disable-cache \
  && mkdir -p ~/.config/opencode/commands \
  && cp /tmp/generar-csv-ofertas/.opencode/commands/generar-csv-ofertas.md ~/.config/opencode/commands/ \
  && rm -rf /tmp/generar-csv-ofertas
```

Con la instalación global solo falta copiar el script al proyecto la primera vez
que lo uses:

```bash
mkdir -p .opencode/scripts \
  && curl -fsSL https://raw.githubusercontent.com/javierjuanJJ/generar-csv-ofertas/main/.opencode/scripts/ofertas_csv.py \
     -o .opencode/scripts/ofertas_csv.py
```

### Opción 2 — con `curl`

Sin Node.js. Instala el comando y el script en el proyecto actual:

```bash
mkdir -p .opencode/commands .opencode/scripts \
  && curl -fsSL https://raw.githubusercontent.com/javierjuanJJ/generar-csv-ofertas/main/.opencode/commands/generar-csv-ofertas.md \
       -o .opencode/commands/generar-csv-ofertas.md \
  && curl -fsSL https://raw.githubusercontent.com/javierjuanJJ/generar-csv-ofertas/main/.opencode/scripts/ofertas_csv.py \
       -o .opencode/scripts/ofertas_csv.py
```

### Opción 3 — clonando el repositorio

```bash
git clone https://github.com/javierjuanJJ/generar-csv-ofertas.git
cd generar-csv-ofertas
opencode
```

El repositorio ya es un proyecto de opencode funcional: ejecuta `/generar-csv-ofertas`
sobre los `.txt` que dejes en la carpeta.

---

## Uso

Coloca los archivos `.txt` de las ofertas en la carpeta del proyecto y lanza opencode
desde ahí.

### En la TUI

```bash
cd ~/ofertas && opencode
```

Y dentro de opencode:

```text
/generar-csv-ofertas
/generar-csv-ofertas 45
/generar-csv-ofertas 45 ofertas-septiembre.csv
```

### Sin interfaz (scripts, cron, CI)

```bash
opencode run --command generar-csv-ofertas "45 ofertas.csv"
opencode run --command generar-csv-ofertas "30 ofertas.csv" --agent build
```

`--command` carga el comando y el resto del mensaje son sus argumentos. Añade
`--auto` si quieres que no te pregunte permisos en una ejecución desatendida.

### El script por separado

Si ya tienes el `.opencode/manifiesto.json` hecho y solo quieres el CSV:

```bash
python3 .opencode/scripts/ofertas_csv.py \
  --base . \
  --manifest .opencode/manifiesto.json \
  --out ofertas.csv \
  --dias 30
```

---

## Parámetros

Son **posicionales**: el primero son los días, el segundo el nombre del CSV.

| Posición | Parámetro | Por defecto | Significado |
| --- | --- | --- | --- |
| `$1` | Días máximos | `30` | Antigüedad a partir de la cual una oferta pasa a `Caducada`. |
| `$2` | Archivo de salida | `ofertas.csv` | Nombre del CSV, relativo a la carpeta actual. |

Opciones del script (`ofertas_csv.py`), por si lo ejecutas a mano:

| Opción | Por defecto | Significado |
| --- | --- | --- |
| `--base` | `.` | Carpeta con los `.txt` de origen. |
| `--manifest` | `.opencode/manifiesto.json` | Ruta del manifiesto. |
| `--out` | `ofertas.csv` | Ruta del CSV de salida. |
| `--dias` | `30` | Umbral para `Vigente` / `Caducada`. |
| `--hoy` | hoy | Fecha de referencia `YYYY-MM-DD`, útil para reproducir resultados. |

---

## El CSV generado

### Columnas

| # | Columna | Notas |
| --- | --- | --- |
| 1 | `Fecha` | `DD/MM/YYYY`, calculada a partir del texto de publicación. |
| 2 | `Portal de empleo` | `WhatJobs`, `InfoJobs`, `LinkedIn (inferido)` o `No identificado`. |
| 3 | `Descripción de la oferta` | Puesto, con las erratas del original si las hubiera. |
| 4 | `Ubicación` | Tal cual aparece en el `.txt`. |
| 5 | `Estado de la oferta` | `Vigente` o `Caducada`. |

- **Orden:** de la fecha más reciente a la más antigua.
- **Separador:** coma, con comillas solo donde hace falta (`Madrid, Madrid`).
- **Codificación:** UTF-8 con BOM (la que espera Excel en español).
- **Duplicados:** si un puesto aparece dos veces dentro del mismo archivo **no se
  borra**: la segunda fila se etiqueta como `(duplicado en el archivo)`.

### Cómo se calcula la `Fecha`

Los `.txt` no llevan la fecha de publicación, solo el texto. El script la obtiene
restando ese texto a la fecha del nombre del archivo (`23-09-2026`):

| Texto en el `.txt` | Fecha resultante |
| --- | --- |
| `Hoy` | La del archivo. |
| `Ayer` | La del archivo − 1 día. |
| `Publicado Hace 4 Días` | La del archivo − 4 días. |
| `Publicada Hace 2h` | La del archivo − 2 horas. |
| `23/09/2026 Actualizada` | La fecha literal del texto. |
| *(sin texto)* | La del archivo, marcada como **aproximada**. |

### `Estado de la oferta`

```text
Vigente  =  (hoy − Fecha) <= --dias
Caducada =  (hoy − Fecha) >  --dias
```

Si al terminar todas las filas tienen el mismo estado, el script te avisa para que
ajustes el umbral (por ejemplo, con ofertas de hace dos meses necesitarías
`/generar-csv-ofertas 60`).

---

## El manifiesto

Entre pasos, el comando escribe `.opencode/manifiesto.json` con una entrada por
oferta detectada. Es la fuente de la que se genera el CSV y sirve de revisión
manual antes de dar el resultado por bueno:

```json
[
  {
    "archivo": "lista trabajos 23-09-2026.txt",
    "titulo": "Desarrollador Full Stack Remoto",
    "ubicacion": "Alicante, Alicante provincia – Trabajo híbrido",
    "portal": "WhatJobs",
    "publicacion": "Publicado Hace 2 Días"
  }
]
```

| Clave | Significado |
| --- | --- |
| `archivo` | Nombre del `.txt` de origen (relativo a `--base`). |
| `titulo` | Puesto. Debe aparecer **literalmente** en el archivo. |
| `ubicacion` | Línea de ubicación. |
| `portal` | Portal detectado o inferido. |
| `publicacion` | Texto literal de publicación; vacío si no hay ninguno. |

**El script valida el manifiesto y se niega a generar el CSV si un título no aparece
literalmente en su archivo.** Si falla, corrige el manifiesto; nunca edites el CSV a
mano, porque en la siguiente ejecución se pierde.

---

## Estructura del repositorio

```text
.
├── .opencode/
│   ├── commands/
│   │   └── generar-csv-ofertas.md   # el comando: /generar-csv-ofertas
│   └── scripts/
│       └── ofertas_csv.py            # validación + generación del CSV
└── README.md
```

---

## Ejemplo completo

```console
$ cd ~/ofertas && ls
lista trabajos 23-09-2026.txt  lista trabajos 29-09-2026.txt  notas.txt

$ opencode run --command generar-csv-ofertas "30 ofertas.csv"
CSV generado en /home/jj/ofertas/ofertas.csv (5 ofertas).
2 fila(s) con fecha aproximada (tomada del nombre del archivo): lista trabajos 23-09-2026.txt
1 .txt sin ofertas en el manifiesto (pueden no contener ofertas): notas.txt
Todas las filas quedan como 'Caducada' con --dias 30; prueba con un umbral mayor.

$ cat ofertas.csv
Fecha,Portal de empleo,Descripción de la oferta,Ubicación,Estado de la oferta
29/09/2026,LinkedIn (inferido),Data Engineer,"Madrid, Madrid",Caducada
25/09/2026,WhatJobs,Desarrollador Full Stack Remoto,20001 Donostia San Sebastián / Remoto,Caducada
23/09/2026,InfoJobs,Desarrollador Full Stack Remoto,"Alicante, Alicante - Trabajo híbrido",Caducada
```

---

## Actualizar y desinstalar

Actualizar es volver a copiar los dos archivos (o reinstalar con `npx tiged`).
Desinstalar es borrar:

```bash
rm -f ~/.config/opencode/commands/generar-csv-ofertas.md   # instalación global
rm -f .opencode/commands/generar-csv-ofertas.md             # instalación por proyecto
```

El `.opencode/manifiesto.json` y los CSV que ya hayas generado son tuyos: el comando
no los borra.

---

## Problemas frecuentes

**El comando no aparece en la lista de opencode.**
El archivo debe llamarse como el comando y vivir en `.opencode/commands/` (proyecto)
o `~/.config/opencode/commands/` (global). Comprueba la ruta; reinicia la TUI.

**`error: No existe el manifiesto .opencode/manifiesto.json`.**
Se ejecutó el script suelto sin el manifiesto. Pásalo con `--manifest`, o deja que
sea el comando quien lo genere.

**`error: El manifiesto no cuadra con los archivos de origen`.**
Algún `titulo` del manifiesto no aparece tal cual en su `.txt` (normalmente por un
tildón, una mayúscula o un espacio). Corrige el `titulo` para que coincida
exactamente con el archivo.

**Acentos rotos en el CSV.**
El `.txt` está en UTF-8 y no en Latin-1. El comando fuerza `latin-1` porque es el
formato habitual de estos portales; si tu copia vino en UTF-8, conviértela con
`iconv -f UTF-8 -t ISO-8859-1 entrada.txt > salida.txt`.

**Todas las ofertas salen como `Caducada`.**
Esperado si los `.txt` son antiguos: el estado se compara contra hoy. Sube el umbral
(`/generar-csv-ofertas 90`) o prueba con `--hoy` para ver el resultado en otra fecha.

**El comando no hace lo que le pido un `.txt`.**
Los portales a veces incluyen texto de instrucciones dentro del archivo. Se trata
como **dato**, nunca como orden: el comando solo lo menciona como aviso.