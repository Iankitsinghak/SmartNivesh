import json
from datetime import date
from pathlib import Path

from app.schemas.common import DataSource


REQUIRED_FIELDS = (
    "source_id",
    "provider_name",
    "dataset_name",
    "source_url",
    "access_method",
    "publication_date",
    "geographic_coverage",
    "limitations",
)


def verify_source_registry(path: Path) -> list[str]:
    records = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for index, record in enumerate(records):
        prefix = f"record {index}"
        errors.extend(f"{prefix}: missing {field}" for field in REQUIRED_FIELDS if not record.get(field))
        for field in ("publication_date", "last_verified"):
            if record.get(field):
                try:
                    date.fromisoformat(record[field])
                except ValueError:
                    errors.append(f"{prefix}: invalid {field}")
        if record.get("source_url") and not record["source_url"].startswith(("http://", "https://")):
            errors.append(f"{prefix}: source_url must be public http(s)")
    return errors


def load_source_registry(path: Path) -> list[DataSource]:
    errors = verify_source_registry(path)
    if errors:
        raise ValueError("\n".join(errors))
    records = json.loads(path.read_text(encoding="utf-8"))
    return [
        DataSource(
            source_id=record["source_id"],
            provider_name=record["provider_name"],
            dataset_name=record["dataset_name"],
            source_url=record["source_url"],
            access_method=record["access_method"],
            publication_date=date.fromisoformat(record["publication_date"]),
            geographic_coverage=record["geographic_coverage"],
            limitations=tuple(record["limitations"]),
            update_frequency=record.get("update_frequency"),
            last_verified=(
                date.fromisoformat(record["last_verified"])
                if record.get("last_verified")
                else None
            ),
        )
        for record in records
    ]


if __name__ == "__main__":
    registry = Path(__file__).parents[1] / "data" / "data_sources.json"
    errors = verify_source_registry(registry)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Verified {len(json.loads(registry.read_text(encoding='utf-8')))} data source(s).")