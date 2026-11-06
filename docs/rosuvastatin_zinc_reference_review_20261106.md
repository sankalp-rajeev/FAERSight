# Rosuvastatin-zinc SS mapping: independent reference review

Reviewed November 6, 2026. Technical source-validation note, not clinical advice,
student signoff, or submission prose. No frozen mapping or result was modified.

## Conclusion

**Scientifically justified for ingredient-level binary presence:** the exact
`ROSUVASTATIN ZINC` token can be normalized to `rosuvastatin` in the two existing
SS combination-product rows. This is an inference from the regulatory composition
evidence below and the frozen ingredient-level estimand. It does not identify a
particular brand/strength in FAERS, establish dose equivalence for these reports,
or attribute their reactions to rosuvastatin.

## Authoritative references inspected

- **HPRA, Lipocomb 40 mg/10 mg SmPC, January 22, 2024, section 2, page 1.**
  Lists the combination's two active components and explicitly expresses the
  rosuvastatin amount using the zinc salt. This predates the frozen 2025 Q4
  reports and supports the ingredient interpretation of the exact salt token.
  [Regulator-hosted SmPC](https://www.hpra.ie/img/uploaded/swedocuments/Licence_PA1470-004-003_22012024105413.pdf#page=1).
- **MHRA, Rosuvastatin tablets PAR, UK/H/6263/001-4/DC, October 2016 summary,
  quality section II.1-II.2, printed page 6.** Identifies rosuvastatin zinc as the
  drug substance and states rosuvastatin amounts corresponding to zinc-salt
  amounts. Independent corroboration comes from a different regulator and a
  single-ingredient product, rather than assuming every statin salt is identical.
  [Regulator-hosted assessment](https://mhraproducts4853.blob.core.windows.net/docs/704ac196122f3954aaf0295a67fdd22f011126d4#page=6).
- **HPRA, Lipocomb 10/10 mg SmPC, June 10, 2026, section 2, page 1.** The current
  linked document specifies the tetrahydrate form alongside ezetimibe. This
  corroborates active-moiety normalization; it was not available during 2025 Q4
  and is not substituted for the earlier evidence.
  [Current regulator-hosted SmPC](https://assets.hpra.ie/products/Human/28356/Licence_PA1470-004-001_10062026093800.pdf#page=1).

The [HPRA product record](https://www.hpra.ie/find-a-medicine/for-human-use/authorised-medicines/details/28356)
now lists the licence as withdrawn September 30, 2026. That current status does
not establish why it was withdrawn and does not invalidate the historical
ingredient-composition evidence. No reason for withdrawal or current marketing
claim is inferred here.

## Application to the two source rows

Physical source lines include the header as line 1, in
`data/raw/2025Q4/extracted/ASCII/DRUG25Q4.txt`. Both source fields `drugname` and
`prod_ai` contain exactly `EZETIMIBE\ROSUVASTATIN ZINC`, and `role_cod=SS`.

- **Case 26202743 / primary 262027431 / G1761823 / DRUG_SEQ 2:** primary canonical
  ingredient remains NULL; sensitivity canonical is `rosuvastatin`, method
  `prod_ai_sensitivity_review`, exposure true. The existing PS atorvastatin row
  still supplies the primary exposure. Sensitivity presence is
  `{atorvastatin, rosuvastatin}`.
- **Case 26212238 / primary 262122381 / G1794032 / DRUG_SEQ 2:** primary canonical
  ingredient remains NULL and primary statin exposure is empty; sensitivity
  canonical is `rosuvastatin`, method `prod_ai_sensitivity_review`, exposure true.
  Sensitivity presence is `{rosuvastatin}`.

The original combination product and ezetimibe text are preserved. Only the
exact rosuvastatin ingredient token contributes a target-class presence; the
SS-only scope excludes C/I rows and leaves the primary map unchanged. The
15-case independent audit was rerun without discrepancies; see the
[case evidence report](case_source_evidence_review_20261106.md#case-by-case-evidence).

Frozen policy references: [overlay CSV](../mappings/sensitivity_ss_aliases.csv),
[review decision](../mappings/sensitivity_ss_review.yaml),
[sensitivity configuration](../config/sensitivity.yaml), and
[Milestone 4 evidence](milestone4.md). Their original bytes remain unchanged.

## Remaining uncertainty and approval boundary

The earlier case report accurately recorded external verification as unresolved
at that checkpoint. This note supplies the subsequent independent regulatory
support; it does not rewrite that historical report or its evidence. Exact brand,
formulation, strength, adherence, causality and worldwide report-version history
remain unestablished by these rows. No dose conversion or broader salt mapping
is proposed. The student's alias/benchmark/source-review fields remain pending;
`scientific_findings_validated` remains false.

**No mapping change is needed to support the current ingredient-presence policy.**
Any proposal to broaden aliases, change role scope, replace frozen results, or
add quarters requires a separate explicit approval and new versioned experiment
plan before execution. This checkpoint authorizes documentation only.
