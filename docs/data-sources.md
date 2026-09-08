# Data Sources

Every integrated dataset must be registered in `backend/data/data_sources.json` with its provider, public URL, access method, publication date, geographic coverage, limitations, and verification date.

The MVP treats mapped business and facility data as identified records, not a complete census. If a query returns zero providers, the system reports that no provider was identified in the available dataset. It does not claim that no provider exists.

The source registry is checked with:

```text
python backend/scripts/verify_data.py
```