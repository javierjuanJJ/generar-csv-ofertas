#!/usr/bin/env python3
"""Genera un CSV de ofertas a partir del manifiesto `.opencode/manifiesto.json`.

Valida que cada titulo exista literalmente en su archivo de origen, calcula la
fecha de publicacion a partir del texto literal y del nombre del archivo
(`DD-MM-YYYY`) y escribe un CSV UTF-8 con BOM, separado por comas y ordenado de
fecha mas reciente a mas antigua.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

VIGENTE = "Vigente"
CADUCADA = "Caducada"
SUFIJO_DUPLICADO = "(duplicado en el archivo)"

CAMPOS = [
    "Fecha",
    "Portal de empleo",
    "Descripcion de la oferta",
    "Ubicacion",
    "Estado de la oferta",
]

RE_FECHA_ARCHIVO = re.compile(r"(\d{2})-(\d{2})-(\d{4})")
RE_FECHA_ABSOLUTA = re.compile(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})")
RE_HACE_DIAS = re.compile(r"hace\s+(\d+)\s*d[ií]a", re.IGNORECASE)
RE_HACE_HORAS = re.compile(r"hace\s+(\d+)\s*h", re.IGNORECASE)


class ErrorManifiesto(Exception):
    """Error de uso que se muestra sin traza."""


@dataclass
class Oferta:
    archivo: str
    titulo: str
    ubicacion: str
    portal: str
    publicacion: str
    fecha: date = field(default=None)
    fecha_aproximada: bool = False


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="ofertas_csv.py",
        description="Valida el manifiesto y genera el CSV de ofertas.",
    )
    p.add_argument("--base", default=".", help="Carpeta con los .txt de origen.")
    p.add_argument(
        "--manifest",
        default=".opencode/manifiesto.json",
        help="Ruta del manifiesto JSON.",
    )
    p.add_argument("--out", default="ofertas.csv", help="Ruta del CSV de salida.")
    p.add_argument(
        "--dias",
        type=int,
        default=30,
        help="Dias maximos para marcar una oferta como %s (por defecto 30)." % VIGENTE,
    )
    p.add_argument(
        "--hoy",
        help="Fecha de referencia YYYY-MM-DD para el estado (por defecto, hoy).",
    )
    return p.parse_args(argv)


def fecha_de_referencia(valor: str | None) -> date:
    if not valor:
        return date.today()
    try:
        return datetime.strptime(valor.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ErrorManifiesto(
            "--hoy debe tener el formato YYYY-MM-DD (por ejemplo 2026-10-02)."
        )


def fecha_del_nombre(archivo: str) -> date:
    m = RE_FECHA_ARCHIVO.search(Path(archivo).name)
    if not m:
        raise ErrorManifiesto(
            "El nombre del archivo %r no contiene una fecha DD-MM-YYYY, que es "
            "la base para calcular la fecha de publicacion." % archivo
        )
    dia, mes, anio = (int(g) for g in m.groups())
    try:
        return date(anio, mes, dia)
    except ValueError:
        raise ErrorManifiesto(
            "La fecha %s del nombre del archivo %r no es una fecha valida."
            % (m.group(0), archivo)
        )


def calcula_fecha(oferta: Oferta, hoy: date) -> None:
    """Rellena `fecha` a partir del texto de publicacion y de la fecha del archivo."""
    base = fecha_del_nombre(oferta.archivo)
    texto = (oferta.publicacion or "").strip()
    low = texto.lower()

    if not texto:
        oferta.fecha = base
        oferta.fecha_aproximada = True
        return

    m = RE_FECHA_ABSOLUTA.search(texto)
    if m:
        oferta.fecha = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        return

    if low.startswith("hoy"):
        oferta.fecha = base
        return

    if low.startswith("ayer"):
        oferta.fecha = base - timedelta(days=1)
        return

    m = RE_HACE_DIAS.search(texto)
    if m:
        oferta.fecha = base - timedelta(days=int(m.group(1)))
        return

    m = RE_HACE_HORAS.search(texto)
    if m:
        oferta.fecha = base - timedelta(hours=int(m.group(1)))
        return

    print(
        "aviso: texto de publicacion no reconocido %r en %s; se usa la fecha del "
        "archivo" % (texto, oferta.archivo),
        file=sys.stderr,
    )
    oferta.fecha = base
    oferta.fecha_aproximada = True


def carga_manifiesto(ruta: Path) -> list[dict]:
    if not ruta.is_file():
        raise ErrorManifiesto(
            "No existe el manifiesto %s. El comando debe escribirlo antes de "
            "lanzar este script." % ruta
        )
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ErrorManifiesto("El manifiesto %s no es JSON valido: %s" % (ruta, e))
    if not isinstance(datos, list):
        raise ErrorManifiesto(
            "El manifiesto %s debe contener una lista de ofertas." % ruta
        )

    campos = ("archivo", "titulo", "ubicacion", "portal", "publicacion")
    ofertas = []
    for i, item in enumerate(datos, start=1):
        if not isinstance(item, dict):
            raise ErrorManifiesto(
                "La entrada %d del manifiesto no es un objeto." % i
            )
        faltan = [c for c in campos if c not in item]
        if faltan:
            raise ErrorManifiesto(
                "La entrada %d del manifiesto no tiene %s."
                % (i, ", ".join(faltan))
            )
        ofertas.append(Oferta(**{c: str(item[c]) for c in campos}))
    return ofertas


def valida_titulos(base: Path, ofertas: list[Oferta]) -> dict[str, str]:
    """Comprueba que cada titulo aparezca literalmente en su archivo. Falla si no."""
    cache: dict[str, str] = {}
    fallos: list[str] = []
    for oferta in ofertas:
        ruta = (base / oferta.archivo).resolve()
        if oferta.archivo not in cache:
            if not ruta.is_file():
                fallos.append("  - %s: no existe el archivo %s" % (oferta.titulo, ruta))
                cache[oferta.archivo] = ""
            else:
                try:
                    cache[oferta.archivo] = ruta.read_text(encoding="latin-1")
                except (OSError, UnicodeDecodeError) as e:
                    fallos.append("  - no se pudo leer %s: %s" % (ruta, e))
                    cache[oferta.archivo] = ""
        if cache.get(oferta.archivo) and oferta.titulo not in cache[oferta.archivo]:
            fallos.append(
                "  - %s: el titulo %r no aparece literalmente en %s"
                % (oferta.archivo, oferta.titulo, oferta.archivo)
            )
    if fallos:
        raise ErrorManifiesto(
            "El manifiesto no cuadra con los archivos de origen:\n"
            + "\n".join(fallos)
            + "\nCorrige el manifiesto (no el CSV)."
        )
    return cache


def marca_duplicados(ofertas: list[Oferta]) -> int:
    """Etiqueta como duplicado el segundo y sucesivos del mismo titulo y archivo."""
    vistos: dict[tuple[str, str], int] = {}
    total = 0
    for oferta in ofertas:
        clave = (oferta.archivo, oferta.titulo)
        vistos[clave] = vistos.get(clave, 0) + 1
        if vistos[clave] > 1:
            oferta.titulo = "%s %s" % (oferta.titulo, SUFIJO_DUPLICADO)
            total += 1
    return total


def escribe_csv(ruta: Path, ofertas: list[Oferta], hoy: date, dias: int) -> None:
    ordenadas = sorted(ofertas, key=lambda o: o.fecha, reverse=True)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(CAMPOS)
        for o in ordenadas:
            estado = VIGENTE if (hoy - o.fecha).days <= dias else CADUCADA
            writer.writerow(
                [
                    o.fecha.strftime("%d/%m/%Y"),
                    o.portal or "No identificado",
                    o.titulo,
                    o.ubicacion,
                    estado,
                ]
            )


def archivos_sin_inventariar(base: Path, ofertas: list[Oferta]) -> list[str]:
    inventariados = {o.archivo for o in ofertas}
    return sorted(
        str(p)
        for p in base.glob("*.txt")
        if str(p.relative_to(base)) not in inventariados
    )


def informe(
    ruta_csv: Path,
    ofertas: list[Oferta],
    duplicados: int,
    sin_inventariar: list[str],
    hoy: date,
    dias: int,
) -> None:
    aproximadas = [o for o in ofertas if o.fecha_aproximada]
    inferidos = [o for o in ofertas if "inferido" in o.portal.lower()]
    estados = {
        (VIGENTE if (hoy - o.fecha).days <= dias else CADUCADA) for o in ofertas
    }

    print("CSV generado en %s (%d ofertas)." % (ruta_csv, len(ofertas)))
    if aproximadas:
        print(
            "%d fila(s) con fecha aproximada (tomada del nombre del archivo): %s"
            % (
                len(aproximadas),
                ", ".join(sorted({o.archivo for o in aproximadas})),
            )
        )
    if duplicados:
        print(
            "%d oferta(s) repetidas dentro de su archivo, marcadas como %r."
            % (duplicados, SUFIJO_DUPLICADO)
        )
    if inferidos:
        print("%d oferta(s) con portal %r." % (len(inferidos), "(inferido)"))
    if sin_inventariar:
        print(
            "%d .txt sin ofertas en el manifiesto (pueden no contener ofertas): %s"
            % (len(sin_inventariar), ", ".join(sin_inventariar))
        )
    if len(estados) == 1 and ofertas:
        unico = estados.pop()
        print(
            "Todas las filas quedan como %r con --dias %d; prueba con un umbral "
            "mayor." % (unico, dias)
        )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    base = Path(args.base).resolve()
    hoy = fecha_de_referencia(args.hoy)
    if args.dias < 0:
        raise ErrorManifiesto("--dias no puede ser negativo.")

    ofertas = carga_manifiesto(Path(args.manifest))
    if not ofertas:
        print("El manifiesto no contiene ofertas.", file=sys.stderr)
        return 1
    valida_titulos(base, ofertas)
    for oferta in ofertas:
        calcula_fecha(oferta, hoy)
    duplicados = marca_duplicados(ofertas)

    ruta_csv = Path(args.out)
    if not ruta_csv.is_absolute():
        ruta_csv = base / ruta_csv
    escribe_csv(ruta_csv, ofertas, hoy, args.dias)
    informe(
        ruta_csv, ofertas, duplicados, archivos_sin_inventariar(base, ofertas), hoy, args.dias
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ErrorManifiesto as error:
        print("error: %s" % error, file=sys.stderr)
        sys.exit(1)