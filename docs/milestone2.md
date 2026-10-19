# Milestone 2: acquisition and integration decision

Engineering record, frozen October 18, 2026 (America/New_York). This is not
course-submission prose or a drug-safety result.

## Scope and feasibility

Use **statins** and **2025 Q4**. FDA's
[official extract index](https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html)
links directly to
[faers_ascii_2025Q4.zip](https://fis.fda.gov/content/Exports/faers_ascii_2025Q4.zip).
The successful HTTPS download contained 67,144,585 bytes, with 372,995,167 bytes
uncompressed across all members. Its SHA-256 is
`1a31e6fdedd7442ffb0cd9d0dc8d2d27ee738e5ee2da34e629d82e47f8d418b6`.
This is a locally computed content pin, not an FDA-published checksum/signature.

The required relations are `ASCII/DEMO25Q4.txt` (58,610,237 bytes),
`ASCII/DRUG25Q4.txt` (181,992,344 bytes), and `ASCII/REAC25Q4.txt`
(51,214,752 bytes). Source documentation includes `Readme.pdf`, `FAQs.pdf`,
`ASCII/ASC_NTS.pdf`, and relation summary PDFs. `Deleted/DELETE25Q4.txt` is also
retained and applied. Only the required relations, deleted-case list and
documentation are extracted; the original ZIP is preserved intact.

A complete strict source scan found 385,288 DEMO, 1,815,349 DRUG and 1,349,105
REAC records, with respectively 25, 20 and 4 fields on every record. All bytes
in these relations were ASCII; `encoding: ascii` is frozen for this source,
with decoding errors rejected. Available disk space exceeded 150 GB at probing.
The raw size and bounded-memory staging/native DuckDB loading are feasible.

The index's displayed January posting year appears inconsistent with its Q4
heading. The HTTP Last-Modified header was January 27, 2026; the actual archive
contents and checksum determine identity. No posting-date inference is used
to select records.

The seven ingredients are atorvastatin, fluvastatin, lovastatin, pitavastatin,
pravastatin, rosuvastatin and simvastatin, from the
[FDA class list](https://www.fda.gov/safety/medical-product-safety-information/statins-drug-safety-communication-fda-requests-removal-strongest-warning-against-using-cholesterol).
FDA's [medicine guide](https://www.fda.gov/consumers/womens-health-topics/cholesterol-medicines-guide)
and [approved statin list](https://www.fda.gov/drugs/drug-safety-and-availability/fda-requests-removal-strongest-warning-against-using-cholesterol-lowering-statins-during-pregnancy)
support brand and combination identities. Ingredient salts use explicit reviewed
aliases; label examples include
[atorvastatin calcium](https://www.accessdata.fda.gov/drugsatfda_docs/label/2019/020702s073lbl.pdf),
[atorvastatin calcium trihydrate](https://www.accessdata.fda.gov/drugsatfda_docs/label/2023/213260s000lbl.pdf),
[pitavastatin salts](https://nctr-crs.fda.gov/fdalabel/ui/spl-summaries/criteria/113760),
and [Liptruzet](https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/200153s009s013s014lbl.pdf).

## Frozen integration rules

- Configuration: `config/experiment.yaml`, `config/therapeutic_class.yaml`,
  and `mappings/drug_mapping.csv`; source archive bytes and SHA-256 are pinned.
- The eligibility universe is all latest case versions in the selected extracts,
  excluding FDA-listed deleted cases and latest reports missing a DRUG record
  or any nonblank REAC term. No exposure, role, country, demographic, reaction
  vocabulary or score filter narrows this denominator.
- Choose highest numeric case version, then numeric report ID, then quarter.
  Deduplicate before eligibility; never substitute an older complete report.
- Join on report ID, case ID and source quarter. Reject contradictory case/report
  identities; audit unmatched relation rows separately from stale-version rows.
- Preserve all retained drug records, including repeated drug sequence numbers.
  FDA's included FAQs (question 52) explicitly permit repeated dosing/route rows.
- Normalize case-level drug/reaction presence separately from retained source rows.
- Map exact reviewed drug-name aliases and exact backslash-separated `PROD_AI`
  ingredient tokens. Tokenization is confined to that structured ingredient field;
  no fuzzy matching or substring-based exposure assignment is allowed.
- Include a known statin component of a combination product, retaining the whole
  original product record and its nonstatin components in the source fields.
- Mapping disagreement or multiple target ingredients in one record is flagged
  as a conflict and prevents the integration quality gate from passing.
- Primary exposure requires literal PS. PS+SS is a later sensitivity analysis.
  Do not relabel the first listed drug as PS when no PS was supplied, despite
  the source FAQ's legacy recommendation; record missing-PS counts instead.
- FDA deleted-case lists from all selected quarters are unioned and applied to
  the case universe. The list's blank first line is not a case ID.
- A candidate reaction must occur in at least five distinct target-exposed cases.
  All candidate reactions are encoded across all eligible cases, preserving
  background reports and empty mining baskets.
- For later actual WEKA mining, prespecify support grid `0.00001, 0.00005, 0.0001`,
  minimum lift `1.2`, and maximum requested rules `10000`. These settings have
  not been tuned to reaction rankings or real mining outputs. Runtime feasibility,
  benchmark freeze and threshold sensitivity remain later quality gates.

The included FDA documentation establishes that report versions, not presumed
patient identities, are the deduplication key. This does not eliminate duplicate
clinical events submitted under different case IDs.

## Validation boundary

This milestone validates acquisition, integration and denominators. Real-data
mining, external benchmark recovery, ranking agreement, full sensitivity runs,
and student interpretation remain pending. Automated ingestion success is not
validation of a clinical drug-safety finding. Existing Java 21 and WEKA 3.8.6
are reused; no additional JDK is required.

## Executed integration evidence

Two complete successful integrations produced identical hashes for seven sorted
logical CSV outputs: contingency counts, the three analytical summary slices,
unmapped drug names, target-like unmapped names and mapping conflicts. A clean
CLI reproduction used code commit `1de7eb39c893a83fc31c837bcc8d4426d8fc4378`
with a clean tracked worktree and completed in about 69 seconds on this machine.
Physical DuckDB file layout is not required to be byte-identical between builds.

- Raw source rows: DEMO **385,288**; DRUG **1,815,349**; REAC **1,349,105**.
  These match the included FDA relation summary PDFs; selected missing-field and
  complete drug-role frequency counts also reconcile with those documents.
- Eligible reporting universe: **385,288** unique case IDs. This particular
  extract already contained one version per case; synthetic tests exercise
  highest-version selection, incomplete latest reports and cross-quarter overlap.
- PS statin-exposed cases: **2,298**. Preserved background cases: **382,990**.
  Exposure counts describe mapping and cohort construction, not safety findings.
- All **1,815,349** retained source drug rows are preserved, including **62,384**
  groups with repeated drug sequence numbers.
- Reaction presence rows after within-case term deduplication: **1,332,786**.
  The later mining vocabulary contains **359** terms, producing **2,513**
  drug/reaction contingency rows, each with the same eligible denominator.
- The deleted-case source contains **4,497** case IDs and one blank line; none
  overlap the current-quarter DEMO population. No source rows are orphaned, no
  case/report identity contradictions or mapping conflicts were found, and no
  eligible cases were removed for missing drug/reaction relations.
- **10** cases lack a literal PS drug row; they remain in the population without
  an imputed role. All source role codes, including **DN**, are preserved.
- **274** target-like unmapped drug rows remain flagged: **272 C**, **2 SS**,
  **0 PS**. They are not silently normalized. Review is needed before extending
  the alias map or interpreting the planned PS+SS sensitivity analysis. This
  audit does not prove that every unrecognized spelling has been detected.
- All **21** integration invariants passed, plus subsequent database SHA-256
  validation. Independent source rescans passed five membership/identity checks
  on each of **15** deterministic reports (five in each exposure/background stratum).
  This is automated verification; student manual review is still pending.
- **67** local tests passed with zero skips, including the existing Java 21 /
  actual WEKA 3.8.6 Apriori integration. GitHub Actions passed on the same code
  checkpoint. Real-data WEKA mining has not yet been executed.

The initial local build stalled at its first native load and was terminated;
its incomplete database was preserved under
`data/processed/2025Q4-statins-aborted-run1/`. A clean retry and the final normal
CLI reproduction both succeeded. No JDK installation, FDA input change, scientific
policy waiver or user intervention was needed to complete ingestion.

The validated mart is `data/processed/2025Q4-statins/analytical.duckdb`.
The source ZIP, extracted documentation, staging files, database and detailed
sample case IDs remain local and ignored. Lightweight aggregate evidence is
tracked in [the evidence directory](../artifacts/manifests/2025Q4-statins/),
including source/archive hashes, the complete preprocessing audit, gate results,
independent source checks, PDF count reconciliation and reproduction hashes.
