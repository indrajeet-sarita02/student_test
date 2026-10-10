"""Dependency-free XLSX reader/writer.

A ``.xlsx`` file is a ZIP archive of Office Open XML parts. The project ships
without third-party spreadsheet libraries, so this module implements just the
subset needed to:

* **read** a workbook into ``{sheet_name: [[cell, ...], ...]}`` where every cell
  is returned as a string (the import service coerces the values); and
* **write** a workbook from ``[(sheet_name, rows), ...]`` so the downloadable
  sample/template can be generated on the fly.

Only value round-tripping is supported - no formulas, charts or real styling.
A minimal ``styles.xml`` is emitted so Excel/LibreOffice open the generated file
without complaints, and date-formatted numeric cells are converted to ISO text
while reading so a user may type either text or a real Excel date cell.
"""

from __future__ import annotations

import zipfile
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

# Relationships namespace used on the ``r:id`` attribute of a ``<sheet>``.
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

# Builtin ``numFmtId`` values that represent dates/times (ECMA-376 §18.8.30).
_BUILTIN_DATE_IDS = frozenset(
    list(range(14, 23)) + list(range(45, 48)) + [27, 28, 29, 30, 31, 32, 33, 34, 35, 36]
)


# --------------------------------------------------------------------------- #
# Reading
# --------------------------------------------------------------------------- #
def _tag(element: ET.Element) -> str:
    """Local (namespace-free) tag name of an element."""
    return element.tag.rsplit("}", 1)[-1]


def _col_index(ref: str) -> int:
    """0-based column index for an ``A1`` style reference (``A`` -> 0)."""
    index = 0
    for char in ref:
        if char.isalpha():
            index = index * 26 + (ord(char.upper()) - ord("A") + 1)
    return max(index - 1, 0)


def _serial_to_text(serial: float) -> str:
    """Convert an Excel date serial to an ISO-ish text value."""
    # Excel's day 0 is 1899-12-30 (accounting for the fictitious 1900-02-29).
    moment = datetime(1899, 12, 30) + timedelta(days=serial)
    if moment.hour or moment.minute or moment.second:
        return moment.strftime("%Y-%m-%d %H:%M:%S")
    return moment.strftime("%Y-%m-%d")


def _is_date_numfmt(numfmt_id: int, custom: Dict[int, str]) -> bool:
    if numfmt_id in _BUILTIN_DATE_IDS:
        return True
    code = custom.get(numfmt_id)
    if not code:
        return False
    lowered = code.lower()
    if "general" in lowered:
        return False
    return any(token in lowered for token in ("yy", "dd", "hh", "ss", "m/", "/m", "h:", ":m"))


def _read_styles(zf: zipfile.ZipFile) -> Dict[str, Any]:
    try:
        root = ET.fromstring(zf.read("xl/styles.xml"))
    except KeyError:
        return {"xf_numfmt": [], "numfmts": {}}

    custom: Dict[int, str] = {}
    for node in root.iter():
        if _tag(node) == "numFmt":
            try:
                custom[int(node.get("numFmtId", "0"))] = node.get("formatCode", "")
            except ValueError:  # pragma: no cover - malformed package
                continue

    xf_numfmt: List[int] = []
    for node in root.iter():
        if _tag(node) == "cellXfs":
            for xf in node:
                if _tag(xf) == "xf":
                    xf_numfmt.append(int(xf.get("numFmtId", "0")))
    return {"xf_numfmt": xf_numfmt, "numfmts": custom}


def _read_shared_strings(zf: zipfile.ZipFile) -> List[str]:
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return []

    values: List[str] = []
    for si in root:
        if _tag(si) != "si":
            continue
        values.append("".join(node.text or "" for node in si.iter() if _tag(node) == "t"))
    return values


def _sheet_parts(zf: zipfile.ZipFile) -> List[Tuple[str, str]]:
    """Return ``(sheet_name, archive_path)`` pairs in workbook order."""
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels: Dict[str, str] = {}
    rel_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    for rel in rel_root:
        if _tag(rel) == "Relationship":
            rels[rel.get("Id", "")] = rel.get("Target", "")

    parts: List[Tuple[str, str]] = []
    for node in workbook.iter():
        if _tag(node) != "sheet":
            continue
        name = node.get("name") or "Sheet"
        target = rels.get(node.get(f"{{{_REL_NS}}}id", ""), "")
        if not target:
            continue
        if target.startswith("/"):
            path = target.lstrip("/")
        else:
            path = f"xl/{target}"
        parts.append((name, path))
    return parts


def _cell_value(
    cell: ET.Element, shared: List[str], styles: Dict[str, Any]
) -> str:
    cell_type = cell.get("t")
    if cell_type == "inlineStr":
        inner = next((n for n in cell if _tag(n) == "is"), None)
        if inner is None:
            return ""
        return "".join(n.text or "" for n in inner.iter() if _tag(n) == "t")

    value_node = next((n for n in cell if _tag(n) == "v"), None)
    if value_node is None or value_node.text is None:
        return ""
    raw = value_node.text

    if cell_type == "s":
        try:
            return shared[int(raw)]
        except (ValueError, IndexError):
            return ""
    if cell_type in ("str", "e"):
        return raw
    if cell_type == "b":
        return "TRUE" if raw.strip() in ("1", "true", "TRUE") else "FALSE"

    style_index = cell.get("s")
    if style_index is not None:
        try:
            xf = int(style_index)
        except ValueError:
            xf = -1
        xfs = styles.get("xf_numfmt") or []
        if 0 <= xf < len(xfs) and _is_date_numfmt(xfs[xf], styles.get("numfmts", {})):
            try:
                return _serial_to_text(float(raw))
            except ValueError:
                return raw
    return raw


def _read_sheet(
    zf: zipfile.ZipFile, path: str, shared: List[str], styles: Dict[str, Any]
) -> List[List[str]]:
    root = ET.fromstring(zf.read(path))
    rows: List[List[str]] = []
    for row in root.iter():
        if _tag(row) != "row":
            continue
        cells: Dict[int, str] = {}
        last_col = -1
        for cell in row:
            if _tag(cell) != "c":
                continue
            ref = cell.get("r")
            col = _col_index(ref) if ref else last_col + 1
            cells[col] = _cell_value(cell, shared, styles)
            last_col = max(last_col, col)
        rows.append([cells.get(index, "") for index in range(last_col + 1)])
    return rows


def read_xlsx(data: bytes) -> Dict[str, List[List[str]]]:
    """Parse an ``.xlsx`` payload into ``{sheet_name: rows}``.

    Raises ``zipfile.BadZipFile`` when the payload is not a valid archive; the
    caller is expected to translate that into a user-facing validation error.
    """
    with zipfile.ZipFile(BytesIO(data)) as zf:
        shared = _read_shared_strings(zf)
        styles = _read_styles(zf)
        return {
            name: _read_sheet(zf, path, shared, styles)
            for name, path in _sheet_parts(zf)
        }


# --------------------------------------------------------------------------- #
# Writing
# --------------------------------------------------------------------------- #
def _col_letter(index: int) -> str:
    """0-based column index to its spreadsheet letter (``0`` -> ``A``)."""
    letters = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def _escape_text(value: str) -> str:
    """Escape text for an XML text node and drop XML-illegal control chars."""
    cleaned = "".join(
        char
        for char in value
        if char in ("\t", "\n", "\r") or ord(char) >= 0x20
    )
    return escape(cleaned)


def _cell_xml(column: int, row: int, value: Any) -> str:
    if value is None:
        return ""
    ref = f"{_col_letter(column)}{row}"
    if isinstance(value, bool):
        return f'<c r="{ref}" t="b"><v>{1 if value else 0}</v></c>'
    if isinstance(value, (int, float)):
        return f'<c r="{ref}"><v>{value}</v></c>'
    return (
        f'<c r="{ref}" t="inlineStr"><is>'
        f'<t xml:space="preserve">{_escape_text(str(value))}</t>'
        f"</is></c>"
    )


def _sheet_xml(rows: Sequence[Sequence[Any]]) -> str:
    body: List[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells = "".join(
            _cell_xml(col_index, row_index, value)
            for col_index, value in enumerate(row)
        )
        body.append(f'<row r="{row_index}">{cells}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(body)}</sheetData>"
        "</worksheet>"
    )


def _workbook_xml(sheets: Sequence[Tuple[str, Sequence[Sequence[Any]]]]) -> str:
    entries = "".join(
        f"<sheet name={quoteattr(name)} sheetId=\"{index}\" r:id=\"rId{index}\"/>"
        for index, (name, _rows) in enumerate(sheets, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'xmlns:r="{_REL_NS}">'
        f"<sheets>{entries}</sheets>"
        "</workbook>"
    )


def _workbook_rels(count: int) -> str:
    rels = "".join(
        f'<Relationship Id="rId{index}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{index}.xml"/>'
        for index in range(1, count + 1)
    )
    rels += (
        f'<Relationship Id="rIdStyles" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{rels}</Relationships>"
    )


def _content_types(count: int) -> str:
    overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for index in range(1, count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        f"{overrides}"
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        "</Types>"
    )


def _root_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def _styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="2"><fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill></fills>'
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
        '<cellXfs count="1"><xf/></cellXfs>'
        "</styleSheet>"
    )


def write_xlsx(sheets: Sequence[Tuple[str, Sequence[Sequence[Any]]]]) -> bytes:
    """Serialise ``sheets`` to an ``.xlsx`` payload.

    ``sheets`` is an ordered sequence of ``(name, rows)`` pairs; every value may
    be ``str``, ``int``, ``float``, ``bool`` or ``None`` (``None`` writes an
    empty cell).
    """
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _content_types(len(sheets)))
        zf.writestr("_rels/.rels", _root_rels())
        zf.writestr("xl/workbook.xml", _workbook_xml(sheets))
        zf.writestr("xl/_rels/workbook.xml.rels", _workbook_rels(len(sheets)))
        zf.writestr("xl/styles.xml", _styles_xml())
        for index, (_name, rows) in enumerate(sheets, start=1):
            zf.writestr(f"xl/worksheets/sheet{index}.xml", _sheet_xml(rows))
    return buffer.getvalue()
