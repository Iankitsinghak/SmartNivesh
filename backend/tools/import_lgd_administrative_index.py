"""Convert an official LGD ZIP export into VyaparSathi's offline lookup index.

LGD exports legacy Excel-XML files with an ``.xls`` extension.  This importer
uses only the standard library so a release build can be reproduced without an
office suite or third-party spreadsheet dependency.
"""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path

NS = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}
INDEX = "{urn:schemas-microsoft-com:office:spreadsheet}Index"


def rows_from_excel_xml(content: bytes) -> list[list[str]]:
    root = ET.fromstring(content)
    rows: list[list[str]] = []
    for row in root.findall(".//ss:Worksheet/ss:Table/ss:Row", NS):
        values: list[str] = []
        column = 1
        for cell in row.findall("ss:Cell", NS):
            column_index = int(cell.attrib.get(INDEX, column))
            values.extend([""] * (column_index - column))
            column = column_index
            data = cell.find("ss:Data", NS)
            values.append((data.text or "").strip() if data is not None else "")
            column += 1
        rows.append(values)
    return rows


def data_rows(rows: list[list[str]]) -> list[list[str]]:
    return [row for row in rows[5:] if len(row) >= 2 and re.fullmatch(r"\d+(?:\.0)?", row[0])]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with zipfile.ZipFile(args.archive) as archive:
        sheets = {name.casefold(): rows_from_excel_xml(archive.read(name)) for name in archive.namelist() if name.casefold().endswith(".xls")}
    districts_sheet = next(rows for name, rows in sheets.items() if "district" in name and "subdistrict" not in name)
    blocks_sheet = next(rows for name, rows in sheets.items() if "block" in name)
    state_match = re.search(r"All Districts of (.+?)\(State Code:(\d+)\)", districts_sheet[1][0])
    if not state_match:
        raise ValueError("Could not identify State name and LGD code from the district sheet.")
    state_name, state_code = state_match.groups()
    state_slug = re.sub(r"[^a-z0-9]+", "-", state_name.casefold()).strip("-")
    state_id = f"state:{state_slug}"
    districts = [
        {"id": f"lgd-district:{row[1]}", "state_id": state_id, "name": row[3], "lgd_code": row[1]}
        for row in data_rows(districts_sheet)
        if len(row) >= 4 and row[1] and row[3]
    ]
    district_ids = {district["lgd_code"] for district in districts}
    blocks = [
        {"id": f"lgd-block:{row[3]}", "district_id": f"lgd-district:{row[1]}", "name": row[5], "lgd_code": row[3]}
        for row in data_rows(blocks_sheet)
        if len(row) >= 6 and row[1] in district_ids and row[3] and row[5]
    ]
    index = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "name": "Local Government Directory (LGD), Ministry of Panchayati Raj",
            "url": "https://lgdirectory.gov.in/demo/downloadDirectory.do",
            "archive_name": args.archive.name,
            "state_name": state_name,
            "state_lgd_code": state_code,
            "classification": "VERIFIED",
        },
        "states": [{"id": state_id, "name": state_name, "lgd_code": state_code}],
        "districts": districts,
        "blocks": blocks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {args.output}: {len(districts)} districts, {len(blocks)} development blocks.")


if __name__ == "__main__":
    main()
