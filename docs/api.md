# Opportunity Analysis API Contract

The service contract is represented by `OpportunityAnalysis`. A sufficient result contains an `Opportunity` with evidence and transparency metadata. An insufficient result contains no opportunity and returns:

```text
Insufficient evidence to identify a reliable opportunity from the available public data.
```

The API layer must orchestrate services only. It must not calculate scores, infer demand, or convert missing dataset records into claims of real-world absence.