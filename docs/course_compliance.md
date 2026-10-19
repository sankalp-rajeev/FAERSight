# Course compliance engineering checklist

This is an implementation checklist, not a graded submission.

## Course-mandatory work

- [x] Official real-world FDA DEMO, DRUG and REAC data with frozen provenance.
- [x] One therapeutic class and one quarter frozen: statins / 2025 Q4.
- [x] WEKA Apriori executed on a synthetic fixture; raw logs and version retained locally.
- [ ] WEKA Apriori executed on the actual frozen FDA experiment.
- [x] Fixture tests for preprocessing, binary transactions and independent PRR/ROR calculations.
- [x] Real-data analytical integration and OLAP summaries; evidence in Milestone 2 records.
- [ ] Real-data association evaluation.
- [ ] Course milestone and final submission requirements verified in Canvas by student.
- [ ] All graded prose authored by the student, with required references/disclosures.

## Methodologically recommended work

- [x] Same background population retained for WEKA input and PRR/ROR fixture calculations.
- [x] Latest-version selection tested before drug/reaction eligibility filtering.
- [x] Presence-only WEKA rule confirmed; absence rules trigger failures.
- [x] Raw counts accompany scores; zero-cell scores explicitly flagged.
- [x] Deterministic ARFF, audit, case index and statistics regression checks.
- [ ] Real-quarter source spot checks on 10–15 retained cases.
- [ ] Prespecified threshold sweep and PS versus PS+SS sensitivity experiment.
- [ ] Known-signal benchmark frozen before final ranking and evaluated.
- [ ] Rank correlation, top-K overlap and count diagnostics for method disagreements.

## Portfolio targets

- [x] Reproducible technical README and synthetic end-to-end command.
- [x] Dependency lock and CI workflow; pushed integration checkpoint passes remote CI.
- [ ] Fresh-clone reproduction with frozen real inputs.
- [ ] Measured real-data scale, rule count, agreement and benchmark evidence.
- [ ] Resume claims traced to actual final artifacts.

Local evidence is under `artifacts/generated/fixture/`; it is ignored by Git.
The project is now versioned at `github.com/sankalp-rajeev/FAERSight`, with the
synthetic baseline pushed. See `docs/milestone2.md` for the real-data scope freeze.
Do not mark the PRD complete based on synthetic evidence.
