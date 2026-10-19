# Milestone 3: real WEKA experiment execution contract

Engineering record frozen October 19, 2026. Not course-submission prose or
validated drug-safety interpretation.

## Pre-experiment decisions

The Milestone 2 source, mappings, PS role definition, reaction floor and support
grid remain frozen. `benchmarks/known_signals.yaml` selects eight positive pairs
from four pre-2025 FDA labels, before any real mining/ranking run. These sources
are referenced for known reported associations, not for present-day clinical advice.
Exact uppercase terms are used; absent or filtered terms are reported rather than
renamed after the results. A positive-only benchmark cannot measure specificity.

The analytical mart has 385,288 eligible cases, seven candidate drugs and 359
candidate reactions. The exporter will write a complete sparse nominal `{0,1}`
ARFF and a case index, retaining empty and non-exposed cases. The source database
and all input/config/benchmark hashes are pinned in the experiment manifest.

## Bounded WEKA search, without changing pair statistics

Use actual `weka.associations.Apriori` through its public Java API. For each
reaction, project the full ARFF onto all seven drug attributes plus that one
reaction. Every projection retains every report, including empty baskets.
Only rules with exactly one present drug antecedent and one present reaction
consequent enter the accepted rule table. Python only verifies counts/statistics
and compares rankings; it does not implement association-rule search.

For a fixed drug/reaction pair, projection changes neither its joint count,
marginals nor N, hence support, confidence and lift remain identical. Every
desired one-to-one rule above the same support/lift thresholds remains available
to WEKA. Reaction-to-reaction and larger-consequent rules are outside the frozen
question. A synthetic test must compare projected results with a full-attribute
WEKA Apriori run, including co-exposures and empty background cases.

The 10,000-rule cap exceeds the maximum number of possible presence-only rules
on eight items: `3^8 - 2*2^8 + 1 = 6050`. Actual output caps are still checked.
This avoids silently losing drug rules behind a global reaction-rule output cap.

For each prespecified support value (`0.00001`, `0.00005`, `0.0001`), set both
WEKA upper and lower support to that value. WEKA's adaptive support descent must
not stop at a different threshold because enough rules were found. Retain its
reported integer support count rather than assume a rounding convention.
Lift threshold remains 1.2. Raw per-projection output, exact options, full API
metrics and version/resource logs are retained. Reuse the existing Java 21 JDK
and WEKA 3.8.6 jars with a 4 GB heap and a 30-minute run timeout.

## Quality gates and interpretation boundary

- Validate source mart hash, full case count and binary attribute semantics.
- Prove projected/full WEKA equivalence on a scientific fixture.
- Check all raw mined items for presence value 1 and validate rule direction.
- Verify WEKA N and integer joint/drug/reaction counts against the mart.
- Independently check support, confidence and lift at full floating precision.
- Detect missing eligible pairs, duplicates and output-cap truncation.
- Retain `a,b,c,d,N` for PRR/ROR and explicitly flag undefined/infinite scores.
- Compute rank correlation with ties and top-K overlap on explicitly shared pair
  sets. Separate pair eligibility and benchmark recovery from top-K appearance.
- Preserve failures and partial logs; never label a timed-out run complete.

Student manual source review, benchmark review, role sensitivity and final
scientific interpretation remain pending. Unmapped C/SS spellings remain unchanged.
All primary experiment outputs must retain `scientific_findings_validated: false`.
