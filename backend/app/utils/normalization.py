from datetime import date


def normalize_indicator_name(value: str) -> str:
    return "_".join(value.strip().lower().split())


def parse_dataset_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"dataset date must use YYYY-MM-DD: {value}") from exc