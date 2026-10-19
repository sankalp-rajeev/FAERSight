# Course compliance engineering checklist

This is an implementation checklist, not a graded submission.

## Course-mandatory work

- [x] Official real-world FDA DEMO, DRUG and REAC data with frozen provenance.
- [x] One therapeutic class and one quarter frozen: statins / 2025 Q4.
- [x] WEKA Apriori executed on a synthetic fixture; raw logs and version retained locally.
- [x] WEKA Apriori executed on the actual frozen FDA experiment; 1,077 searches.
- [x] Fixture tests for preprocessing, binary transactions and independent PRR/ROR calculations.
- [x] Real-data analytical integration and OLAP summaries; evidence in Milestone 2 records.
- [x] Real-data computational evaluation; scientific interpretation remains provisional.
- [ ] Course milestone and final submission requirements verified in Canvas by student.
- [ ] All graded prose authored by the student, with required references/disclosures.

## Methodologically recommended work

- [x] Same background population retained for WEKA input and PRR/ROR fixture calculations.
- [x] Latest-version selection tested before drug/reaction eligibility filtering.
- [x] Presence-only WEKA rule confirmed; absence rules trigger failures.
- [x] Raw counts accompany scores; zero-cell scores explicitly flagged.
- [x] Deterministic ARFF, audit, case index and statistics regression checks.
- [x] Independent automated source checks on 15 retained real-data reports.
- [ ] Student manual source spot checks on 10–15 retained cases (automated checks pass).
- [ ] Prespecified threshold sweep and PS versus PS+SS sensitivity experiment.
- [x] Eight positive reference pairs frozen before mining and evaluated without dropping misses.
- [x] Matched finite-pair rank correlation, top-K overlap and supporting counts exported.

## Portfolio targets

- [x] Reproducible technical README and synthetic end-to-end command.
- [x] Dependency lock and CI workflow; pushed integration checkpoint passes remote CI.
- [ ] Fresh-clone reproduction with frozen real inputs.
- [x] Measured real-data scale, rule count, computational agreement and benchmark evidence.
- [ ] Resume claims traced to actual final artifacts.

Local evidence is under `artifacts/generated/fixture/`; it is ignored by Git.
Real-data aggregate evidence is tracked under `artifacts/manifests/2025Q4-statins/`;
the full mart and detailed sample case records stay local in `data/processed/`.
The project is now versioned at `github.com/sankalp-rajeev/FAERSight`, with the
synthetic baseline pushed. See `docs/milestone2.md` for the real-data scope freeze.
Do not mark the PRD complete based on synthetic evidence.
Primary real-data WEKA evidence is under `artifacts/manifests/2025Q4-statins-mining/`.
Manual review, PS versus PS+SS sensitivity, final interpretation and fresh-clone
reproduction remain open; generated outputs are not validated drug-safety findings.
