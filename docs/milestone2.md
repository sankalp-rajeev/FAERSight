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
