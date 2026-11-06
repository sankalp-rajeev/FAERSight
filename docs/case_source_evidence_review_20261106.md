# Independent FAERS case evidence review — 2025 Q4

November 6, 2026. Agent-generated engineering evidence for the student's independent signoff.

## Scope and outcome

Reviewed all **15 checklist cases** by separately scanning the original DEMO, DRUG and REAC text files and opening both DuckDB snapshots read-only. **15 PASS / 0 FAIL** for source-to-packet/mart reconciliation under the frozen contract. **UNCERTAIN** applies to earlier/later-quarter version history and independent regulatory/clinical interpretation, not to the observed within-quarter equality checks.

PASS is an automated evidence verdict, not student manual approval. All checklist reviewer/date/verification fields remain blank; `cases.json` student verdicts remain `pending`. No checklist, packet, database, mapping, configuration, frozen result or scientific-validation flag was edited.

Coverage: **15 DEMO rows, 679 DRUG rows and 131 REAC rows** for these cases, including all original drug columns. Each case has only one DEMO row in the frozen quarter: the observed maximum and retained version agree, but these cases cannot independently test selection between competing versions or establish latest status across other quarters. That missing history is an explicit UNCERTAIN boundary for every case below.

## Method and references

The independent checker used standard-library physical-line parsing and independently recomputed numeric max `(caseversion, primaryid, quarter)` selection, exact alias/ingredient matching, role filters, reaction normalization, and distinct presences. It did not call the project's deduplication, normalization, spot-check or review-package functions, and did not accept the packet's existing `automated_checks` flags as evidence. All columns of retained DEMO/DRUG and raw DEMO/DRUG/REAC rows, physical source references, packet embedded source rows and packet processed drug/reaction lists were compared. Blank source fields correspond to SQL/JSON nulls; nonblank text had to match exactly.

References use physical text lines, header = line 1: **D** = `data/raw/2025Q4/extracted/ASCII/DEMO25Q4.txt`; **G** = `.../DRUG25Q4.txt`; **R** = `.../REAC25Q4.txt`. Ranges are inclusive. **P** = `data/processed/2025Q4-statins/analytical.duckdb`; **S** = `artifacts/generated/2025Q4-statins-sensitivity/mart/analytical.duckdb`. **J[i]** = zero-based element of `artifacts/generated/2025Q4-statins-sensitivity/manual_review/cases.json`; **K:n** = physical line in the adjacent `case_checklist.csv`.

For each case, database references select `cases`, `latest_cases`, `case_eligibility`, `case_drugs`, `case_drug_presence`, `case_reactions`, `case_items`, and `raw_*` by `case_id`; `case_drugs._source_row` points to G. DEMO source equality also checks all 25 original fields; every DRUG row checks all 20 original fields. Non-target drug rows are summarized rather than reproduced, but all their roles, names, ingredients, dosing fields and physical identities were compared.

Exact mappings use `mappings/drug_mapping.csv` (**M**, header line 1). The only sensitivity overlay uses `mappings/sensitivity_ss_aliases.csv:2` and `mappings/sensitivity_ss_review.yaml` (**O**, exact SS name + ingredient string only). PS includes only mapped PS rows; PS+SS includes mapped PS or SS rows; C and I never contribute exposure. Multiple rows for the same ingredient yield one case-level presence. Reaction output is uppercase with whitespace collapsed; all nonblank distinct reactions are retained in `case_reactions`, while only the frozen vocabulary enters mining baskets.

## Case-by-case evidence

### 1. Case 4202111 — PASS

References: K:2; J[0]; P/S `case_id='4202111'`.

- **Latest/identity — PASS:** D385219 source `primaryid=42021115`, `caseversion=5`, `fda_dt=20251112` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G1814582-1814603: 22 source rows -> 22 P / 22 S / 22 J records; all original fields agree. Source -> processed role counts: C 14->14, PS 1->1, SS 7->7.
- **Statin mapping — PASS:** no source name/ingredient matches a reviewed statin alias; every P/S canonical ingredient is NULL and J agrees. No fuzzy matching was applied.
- **Exposure — PASS:** independently expected PS {} (background) -> P/J {} (background); expected PS+SS {} (background) -> S/J {} (background). C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 2 source rows -> 2 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R1348408 `Toxic epidermal necrolysis` -> `TOXIC EPIDERMAL NECROLYSIS`; R1348409 `Septic shock` -> `SEPTIC SHOCK`.
- **Cautions:** G1814587 `NYSTATIN` is not an exact reviewed statin alias; a `STATIN` substring is insufficient. Empty mining basket is consistent with no mapped exposure and no reactions in the frozen mining vocabulary. S mining basket has 0 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

### 2. Case 7032761 — PASS

References: K:3; J[1]; P/S `case_id='7032761'`.

- **Latest/identity — PASS:** D385225 source `primaryid=70327613`, `caseversion=3`, `fda_dt=20251202` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G1814642-1814645: 4 source rows -> 4 P / 4 S / 4 J records; all original fields agree. Source -> processed role counts: C 3->3, PS 1->1.
- **Statin mapping — PASS:** no source name/ingredient matches a reviewed statin alias; every P/S canonical ingredient is NULL and J agrees. No fuzzy matching was applied.
- **Exposure — PASS:** independently expected PS {} (background) -> P/J {} (background); expected PS+SS {} (background) -> S/J {} (background). C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 1 source rows -> 1 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R1348459 `Henoch-Schonlein purpura` -> `HENOCH-SCHONLEIN PURPURA`.
- **Cautions:** Empty mining basket is not a missing source report: one reaction is retained, but lies outside the frozen mining vocabulary. S mining basket has 0 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

### 3. Case 9028913 — PASS

References: K:4; J[2]; P/S `case_id='9028913'`.

- **Latest/identity — PASS:** D385260 source `primaryid=90289133`, `caseversion=3`, `fda_dt=20251218` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G1814938-1814944: 7 source rows -> 7 P / 7 S / 7 J records; all original fields agree. Source -> processed role counts: C 5->5, PS 1->1, SS 1->1.
- **Mapping — PASS:** G1814942, DRUG_SEQ `5`: source `CADUET` / PROD_AI `AMLODIPINE BESYLATE\ATORVASTATIN CALCIUM` / role `C` -> P canonical `atorvastatin` (both), exposure `false`; S/J canonical `atorvastatin` (both), exposure `false`. Exact references: M:3, M:6.
- **Exposure — PASS:** independently expected PS {} (background) -> P/J {} (background); expected PS+SS {} (background) -> S/J {} (background). C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 2 source rows -> 2 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R1348803 `Meniscus injury` -> `MENISCUS INJURY`; R1348804 `Osteoarthritis` -> `OSTEOARTHRITIS`.
- **Cautions:** Mapped atorvastatin has role C only and correctly leaves this report in background. Other drug names do not gain statin mappings from substring resemblance. S mining basket has 1 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

### 4. Case 9219983 — PASS

References: K:5; J[3]; P/S `case_id='9219983'`.

- **Latest/identity — PASS:** D385270 source `primaryid=92199839`, `caseversion=9`, `fda_dt=20251107` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G1815079-1815133: 55 source rows -> 55 P / 55 S / 55 J records; all original fields agree. Source -> processed role counts: C 44->44, PS 1->1, SS 10->10.
- **Mapping — PASS:** G1815079, DRUG_SEQ `1`: source `SIMVASTATIN` / PROD_AI `SIMVASTATIN` / role `PS` -> P canonical `simvastatin` (both), exposure `true`; S/J canonical `simvastatin` (both), exposure `true`. Exact references: M:28.
- **Mapping — PASS:** G1815080-1815082, DRUG_SEQ `2,3,4`: source `SIMVASTATIN` / PROD_AI `SIMVASTATIN` / role `SS` -> P canonical `simvastatin` (both), exposure `false`; S/J canonical `simvastatin` (both), exposure `true`. Exact references: M:28.
- **Exposure — PASS:** independently expected PS {simvastatin} -> P/J {simvastatin}; expected PS+SS {simvastatin} -> S/J {simvastatin}. C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 8 source rows -> 8 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R1348895 `Product use in unapproved indication` -> `PRODUCT USE IN UNAPPROVED INDICATION`; R1348896 `Infection` -> `INFECTION`; R1348897 `Tachycardia` -> `TACHYCARDIA`; R1348898 `Heart rate irregular` -> `HEART RATE IRREGULAR`; R1348899 `Atrial fibrillation` -> `ATRIAL FIBRILLATION`; R1348900 `Off label use` -> `OFF LABEL USE`; R1348901 `Disease progression` -> `DISEASE PROGRESSION`; R1348902 `Blood creatine phosphokinase increased` -> `BLOOD CREATINE PHOSPHOKINASE INCREASED`.
- **Cautions:** S mining basket has 9 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

### 5. Case 9703375 — PASS

References: K:6; J[4]; P/S `case_id='9703375'`.

- **Latest/identity — PASS:** D385278 source `primaryid=970337561`, `caseversion=61`, `fda_dt=20251113` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G1815195-1815210: 16 source rows -> 16 P / 16 S / 16 J records; all original fields agree. Source -> processed role counts: C 5->5, PS 1->1, SS 10->10.
- **Mapping — PASS:** G1815206, DRUG_SEQ `12`: source `ATORVASTATIN` / PROD_AI `ATORVASTATIN` / role `C` -> P canonical `atorvastatin` (both), exposure `false`; S/J canonical `atorvastatin` (both), exposure `false`. Exact references: M:2.
- **Exposure — PASS:** independently expected PS {} (background) -> P/J {} (background); expected PS+SS {} (background) -> S/J {} (background). C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 25 source rows -> 25 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R1348963 `Hepatic lesion` -> `HEPATIC LESION`; R1348964 `Blood pressure systolic increased` -> `BLOOD PRESSURE SYSTOLIC INCREASED`; R1348965 `Chest pain` -> `CHEST PAIN`; R1348966 `Injection site pain` -> `INJECTION SITE PAIN`; R1348967 `Skin lesion` -> `SKIN LESION`; R1348968 `Drug ineffective` -> `DRUG INEFFECTIVE`; R1348969 `Post procedural infection` -> `POST PROCEDURAL INFECTION`; R1348970 `Injection site mass` -> `INJECTION SITE MASS`; R1348971 `Cardiac disorder` -> `CARDIAC DISORDER`; R1348972 `Neoplasm progression` -> `NEOPLASM PROGRESSION`; R1348973 `Asthenia` -> `ASTHENIA`; R1348974 `Gait disturbance` -> `GAIT DISTURBANCE`; R1348975 `Body temperature increased` -> `BODY TEMPERATURE INCREASED`; R1348976 `Syringe issue` -> `SYRINGE ISSUE`; R1348977 `Blood glucose increased` -> `BLOOD GLUCOSE INCREASED`; R1348978 `Fatigue` -> `FATIGUE`; R1348979 `Needle issue` -> `NEEDLE ISSUE`; R1348980 `Weight decreased` -> `WEIGHT DECREASED`; R1348981 `Injection site haemorrhage` -> `INJECTION SITE HAEMORRHAGE`; R1348982 `Tachycardia` -> `TACHYCARDIA`; R1348983 `Lethargy` -> `LETHARGY`; R1348984 `Underdose` -> `UNDERDOSE`; R1348985 `Inappropriate schedule of product administration` -> `INAPPROPRIATE SCHEDULE OF PRODUCT ADMINISTRATION`; R1348986 `Blood pressure increased` -> `BLOOD PRESSURE INCREASED`; R1348987 `Depression` -> `DEPRESSION`.
- **Cautions:** Mapped atorvastatin has role C only and correctly leaves this report in background. Other drug names do not gain statin mappings from substring resemblance. S mining basket has 12 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

### 6. Case 10423086 — PASS

References: K:7; J[5]; P/S `case_id='10423086'`.

- **Latest/identity — PASS:** D14 source `primaryid=104230869`, `caseversion=9`, `fda_dt=20251018` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G192-209: 18 source rows -> 18 P / 18 S / 18 J records; all original fields agree. Source -> processed role counts: C 5->5, I 11->11, PS 1->1, SS 1->1.
- **Mapping — PASS:** G192, DRUG_SEQ `1`: source `SIMVASTATIN` / PROD_AI `SIMVASTATIN` / role `PS` -> P canonical `simvastatin` (both), exposure `true`; S/J canonical `simvastatin` (both), exposure `true`. Exact references: M:28.
- **Mapping — PASS:** G193-194, DRUG_SEQ `2,3`: source `SIMVASTATIN` / PROD_AI `SIMVASTATIN` / role `I` -> P canonical `simvastatin` (both), exposure `false`; S/J canonical `simvastatin` (both), exposure `false`. Exact references: M:28.
- **Exposure — PASS:** independently expected PS {simvastatin} -> P/J {simvastatin}; expected PS+SS {simvastatin} -> S/J {simvastatin}. C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 19 source rows -> 19 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R157 `Alanine aminotransferase increased` -> `ALANINE AMINOTRANSFERASE INCREASED`; R158 `Asthenia` -> `ASTHENIA`; R159 `Hepatocellular injury` -> `HEPATOCELLULAR INJURY`; R160 `C-reactive protein increased` -> `C-REACTIVE PROTEIN INCREASED`; R161 `Blood creatine phosphokinase increased` -> `BLOOD CREATINE PHOSPHOKINASE INCREASED`; R162 `Dysstasia` -> `DYSSTASIA`; R163 `Disability` -> `DISABILITY`; R164 `Hepatic enzyme increased` -> `HEPATIC ENZYME INCREASED`; R165 `Rhabdomyolysis` -> `RHABDOMYOLYSIS`; R166 `Muscular weakness` -> `MUSCULAR WEAKNESS`; R167 `Non-small cell lung cancer` -> `NON-SMALL CELL LUNG CANCER`; R168 `Drug interaction` -> `DRUG INTERACTION`; R169 `Inflammatory marker increased` -> `INFLAMMATORY MARKER INCREASED`; R170 `General physical health deterioration` -> `GENERAL PHYSICAL HEALTH DETERIORATION`; R171 `Aspartate aminotransferase increased` -> `ASPARTATE AMINOTRANSFERASE INCREASED`; R172 `Respiratory failure` -> `RESPIRATORY FAILURE`; R173 `Muscle enzyme increased` -> `MUSCLE ENZYME INCREASED`; R174 `Loss of personal independence in daily activities` -> `LOSS OF PERSONAL INDEPENDENCE IN DAILY ACTIVITIES`; R175 `Diarrhoea` -> `DIARRHOEA`.
- **Cautions:** G193-194 retain simvastatin I-role rows but do not count them as PS/SS exposure; the mapped PS row supplies the sole simvastatin presence. S mining basket has 15 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

### 7. Case 10496244 — PASS

References: K:8; J[6]; P/S `case_id='10496244'`.

- **Latest/identity — PASS:** D22 source `primaryid=1049624418`, `caseversion=18`, `fda_dt=20251218` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G310-408: 99 source rows -> 99 P / 99 S / 99 J records; all original fields agree. Source -> processed role counts: C 46->46, PS 1->1, SS 52->52.
- **Mapping — PASS:** G312-313, DRUG_SEQ `3,4`: source `ZOCOR` / PROD_AI `SIMVASTATIN` / role `SS` -> P canonical `simvastatin` (both), exposure `false`; S/J canonical `simvastatin` (both), exposure `true`. Exact references: M:28, M:29.
- **Mapping — PASS:** G363, DRUG_SEQ `54`: source `SIMVASTATIN` / PROD_AI `SIMVASTATIN` / role `C` -> P canonical `simvastatin` (both), exposure `false`; S/J canonical `simvastatin` (both), exposure `false`. Exact references: M:28.
- **Exposure — PASS:** independently expected PS {} (background) -> P/J {} (background); expected PS+SS {simvastatin} -> S/J {simvastatin}. C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 20 source rows -> 18 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R283 `Diabetes mellitus inadequate control` -> `DIABETES MELLITUS INADEQUATE CONTROL`; R284 `Depressed mood` -> `DEPRESSED MOOD`; R285 `Peripheral swelling` -> `PERIPHERAL SWELLING`; R286-287 `Treatment noncompliance` -> `TREATMENT NONCOMPLIANCE`; R288 `Multiple drug therapy` -> `MULTIPLE DRUG THERAPY`; R289 `Medication error` -> `MEDICATION ERROR`; R290 `Cognitive disorder` -> `COGNITIVE DISORDER`; R291 `Blood pressure inadequately controlled` -> `BLOOD PRESSURE INADEQUATELY CONTROLLED`; R292 `Drug ineffective` -> `DRUG INEFFECTIVE`; R293 `Product use issue` -> `PRODUCT USE ISSUE`; R294 `Off label use` -> `OFF LABEL USE`; R295 `Abdominal discomfort` -> `ABDOMINAL DISCOMFORT`; R296,302 `Hypertension` -> `HYPERTENSION`; R297 `Amnesia` -> `AMNESIA`; R298 `Mobility decreased` -> `MOBILITY DECREASED`; R299 `Exercise tolerance decreased` -> `EXERCISE TOLERANCE DECREASED`; R300 `Contusion` -> `CONTUSION`; R301 `Oedema peripheral` -> `OEDEMA PERIPHERAL`.
- **Cautions:** R286-287 `Treatment noncompliance` and R296/R302 `Hypertension` are repeated source terms, correctly deduplicated to one presence each. SS ZOCOR contributes exposure; C simvastatin does not. S mining basket has 17 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

### 8. Case 10513265 — PASS

References: K:9; J[7]; P/S `case_id='10513265'`.

- **Latest/identity — PASS:** D24 source `primaryid=105132655`, `caseversion=5`, `fda_dt=20251127` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G412-459: 48 source rows -> 48 P / 48 S / 48 J records; all original fields agree. Source -> processed role counts: C 8->8, PS 1->1, SS 39->39.
- **Mapping — PASS:** G416, DRUG_SEQ `5`: source `SIMVASTATIN` / PROD_AI `SIMVASTATIN` / role `SS` -> P canonical `simvastatin` (both), exposure `false`; S/J canonical `simvastatin` (both), exposure `true`. Exact references: M:28.
- **Mapping — PASS:** G451, DRUG_SEQ `40`: source `ZOCOR` / PROD_AI `SIMVASTATIN` / role `SS` -> P canonical `simvastatin` (both), exposure `false`; S/J canonical `simvastatin` (both), exposure `true`. Exact references: M:28, M:29.
- **Exposure — PASS:** independently expected PS {} (background) -> P/J {} (background); expected PS+SS {simvastatin} -> S/J {simvastatin}. C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 18 source rows -> 18 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R309 `Product use issue` -> `PRODUCT USE ISSUE`; R310 `Peripheral swelling` -> `PERIPHERAL SWELLING`; R311 `Blood pressure inadequately controlled` -> `BLOOD PRESSURE INADEQUATELY CONTROLLED`; R312 `Exercise tolerance decreased` -> `EXERCISE TOLERANCE DECREASED`; R313 `Off label use` -> `OFF LABEL USE`; R314 `Oedema peripheral` -> `OEDEMA PERIPHERAL`; R315 `Depressed mood` -> `DEPRESSED MOOD`; R316 `Drug ineffective` -> `DRUG INEFFECTIVE`; R317 `Diabetes mellitus inadequate control` -> `DIABETES MELLITUS INADEQUATE CONTROL`; R318 `Medication error` -> `MEDICATION ERROR`; R319 `Mobility decreased` -> `MOBILITY DECREASED`; R320 `Hypertension` -> `HYPERTENSION`; R321 `Treatment noncompliance` -> `TREATMENT NONCOMPLIANCE`; R322 `Contusion` -> `CONTUSION`; R323 `Multiple drug therapy` -> `MULTIPLE DRUG THERAPY`; R324 `Cognitive disorder` -> `COGNITIVE DISORDER`; R325 `Abdominal discomfort` -> `ABDOMINAL DISCOMFORT`; R326 `Amnesia` -> `AMNESIA`.
- **Cautions:** S mining basket has 17 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

### 9. Case 11638624 — PASS

References: K:10; J[8]; P/S `case_id='11638624'`.

- **Latest/identity — PASS:** D96 source `primaryid=116386246`, `caseversion=6`, `fda_dt=20251222` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G2006-2045: 40 source rows -> 40 P / 40 S / 40 J records; all original fields agree. Source -> processed role counts: C 35->35, PS 2->2, SS 3->3.
- **Mapping — PASS:** G2010, DRUG_SEQ `4`: source `ROSUVASTATIN` / PROD_AI `ROSUVASTATIN` / role `SS` -> P canonical `rosuvastatin` (both), exposure `false`; S/J canonical `rosuvastatin` (both), exposure `true`. Exact references: M:23.
- **Mapping — PASS:** G2011, DRUG_SEQ `5`: source `PRAVASTATIN SODIUM` / PROD_AI `PRAVASTATIN SODIUM` / role `C` -> P canonical `pravastatin` (both), exposure `false`; S/J canonical `pravastatin` (both), exposure `false`. Exact references: M:21.
- **Mapping — PASS:** G2022, DRUG_SEQ `16`: source `LIVALO` / PROD_AI `PITAVASTATIN CALCIUM` / role `C` -> P canonical `pitavastatin` (both), exposure `false`; S/J canonical `pitavastatin` (both), exposure `false`. Exact references: M:16, M:18.
- **Exposure — PASS:** independently expected PS {} (background) -> P/J {} (background); expected PS+SS {rosuvastatin} -> S/J {rosuvastatin}. C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 9 source rows -> 9 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R1378 `Hypertension` -> `HYPERTENSION`; R1379 `Sleep disorder` -> `SLEEP DISORDER`; R1380 `Obstructive sleep apnoea syndrome` -> `OBSTRUCTIVE SLEEP APNOEA SYNDROME`; R1381 `Cardiomyopathy` -> `CARDIOMYOPATHY`; R1382 `Cardiac failure congestive` -> `CARDIAC FAILURE CONGESTIVE`; R1383 `Pulmonary embolism` -> `PULMONARY EMBOLISM`; R1384 `Asthma` -> `ASTHMA`; R1385 `Oedema peripheral` -> `OEDEMA PERIPHERAL`; R1386 `Restless legs syndrome` -> `RESTLESS LEGS SYNDROME`.
- **Cautions:** C-role pravastatin/pitavastatin are preserved and excluded; only SS rosuvastatin enters sensitivity exposure. S mining basket has 7 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

### 10. Case 11704993 — PASS

References: K:11; J[9]; P/S `case_id='11704993'`.

- **Latest/identity — PASS:** D102 source `primaryid=1170499329`, `caseversion=29`, `fda_dt=20251014` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G2091-2407: 317 source rows -> 317 P / 317 S / 317 J records; all original fields agree. Source -> processed role counts: C 8->8, PS 1->1, SS 308->308.
- **Mapping — PASS:** G2149, DRUG_SEQ `59`: source `ZOCOR` / PROD_AI `SIMVASTATIN` / role `SS` -> P canonical `simvastatin` (both), exposure `false`; S/J canonical `simvastatin` (both), exposure `true`. Exact references: M:28, M:29.
- **Mapping — PASS:** G2332-2339, DRUG_SEQ `242,243,244,245,246,247,248,249`: source `SIMVASTATIN` / PROD_AI `SIMVASTATIN` / role `SS` -> P canonical `simvastatin` (both), exposure `false`; S/J canonical `simvastatin` (both), exposure `true`. Exact references: M:28.
- **Exposure — PASS:** independently expected PS {} (background) -> P/J {} (background); expected PS+SS {simvastatin} -> S/J {simvastatin}. C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 13 source rows -> 13 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R1450 `Areflexia` -> `AREFLEXIA`; R1451 `Cerebrovascular accident` -> `CEREBROVASCULAR ACCIDENT`; R1452 `Nausea` -> `NAUSEA`; R1453 `Respiratory distress` -> `RESPIRATORY DISTRESS`; R1454 `Cerebral artery thrombosis` -> `CEREBRAL ARTERY THROMBOSIS`; R1455 `Facial paralysis` -> `FACIAL PARALYSIS`; R1456 `Hemiplegia` -> `HEMIPLEGIA`; R1457 `Respiratory failure` -> `RESPIRATORY FAILURE`; R1458 `Product use issue` -> `PRODUCT USE ISSUE`; R1459 `Ischaemic stroke` -> `ISCHAEMIC STROKE`; R1460 `Disease recurrence` -> `DISEASE RECURRENCE`; R1461 `Off label use` -> `OFF LABEL USE`; R1462 `Brain scan abnormal` -> `BRAIN SCAN ABNORMAL`.
- **Cautions:** 317 drug rows are present in the original source, not introduced by the join. Repeated SS simvastatin records collapse to one ingredient presence without deleting source rows. S mining basket has 8 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

### 11. Case 12625445 — PASS

References: K:12; J[10]; P/S `case_id='12625445'`.

- **Latest/identity — PASS:** D200 source `primaryid=126254458`, `caseversion=8`, `fda_dt=20251029` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G4238-4275: 38 source rows -> 38 P / 38 S / 38 J records; all original fields agree. Source -> processed role counts: PS 2->2, SS 36->36.
- **Mapping — PASS:** G4238-4239, DRUG_SEQ `1`: source `TAHOR` / PROD_AI `ATORVASTATIN CALCIUM` / role `PS` -> P canonical `atorvastatin` (prod_ai), exposure `true`; S/J canonical `atorvastatin` (prod_ai), exposure `true`. Exact references: M:3.
- **Exposure — PASS:** independently expected PS {atorvastatin} -> P/J {atorvastatin}; expected PS+SS {atorvastatin} -> S/J {atorvastatin}. C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 6 source rows -> 6 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R2460 `Hyponatraemia` -> `HYPONATRAEMIA`; R2461 `Dry mouth` -> `DRY MOUTH`; R2462 `Inappropriate antidiuretic hormone secretion` -> `INAPPROPRIATE ANTIDIURETIC HORMONE SECRETION`; R2463 `Chest pain` -> `CHEST PAIN`; R2464 `Paraneoplastic syndrome` -> `PARANEOPLASTIC SYNDROME`; R2465 `Pulmonary mass` -> `PULMONARY MASS`.
- **Cautions:** G4238-4239 both use DRUG_SEQ=1 and are preserved as separate physical records. TAHOR itself is not in M; the exact ATORVASTATIN CALCIUM ingredient token supplies the mapping. Exposure is counted once. S mining basket has 4 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

### 12. Case 12754107 — PASS

References: K:13; J[11]; P/S `case_id='12754107'`.

- **Latest/identity — PASS:** D228 source `primaryid=127541072`, `caseversion=2`, `fda_dt=20251226` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G4770-4775: 6 source rows -> 6 P / 6 S / 6 J records; all original fields agree. Source -> processed role counts: C 1->1, PS 1->1, SS 4->4.
- **Mapping — PASS:** G4770, DRUG_SEQ `1`: source `ATORVASTATIN` / PROD_AI `ATORVASTATIN` / role `PS` -> P canonical `atorvastatin` (both), exposure `true`; S/J canonical `atorvastatin` (both), exposure `true`. Exact references: M:2.
- **Mapping — PASS:** G4771, DRUG_SEQ `2`: source `PRAVASTATIN` / PROD_AI `PRAVASTATIN` / role `SS` -> P canonical `pravastatin` (both), exposure `false`; S/J canonical `pravastatin` (both), exposure `true`. Exact references: M:20.
- **Mapping — PASS:** G4772, DRUG_SEQ `3`: source `ROSUVASTATIN` / PROD_AI `ROSUVASTATIN` / role `SS` -> P canonical `rosuvastatin` (both), exposure `false`; S/J canonical `rosuvastatin` (both), exposure `true`. Exact references: M:23.
- **Exposure — PASS:** independently expected PS {atorvastatin} -> P/J {atorvastatin}; expected PS+SS {atorvastatin, pravastatin, rosuvastatin} -> S/J {atorvastatin, pravastatin, rosuvastatin}. C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 2 source rows -> 2 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R2719 `Pain` -> `PAIN`; R2720 `Arthropathy` -> `ARTHROPATHY`.
- **Cautions:** Multiple suspected statins remain distinct ingredient presences; PS exposure is a subset of the PS+SS exposure. S mining basket has 5 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

### 13. Case 14662881 — PASS

References: K:14; J[12]; P/S `case_id='14662881'`.

- **Latest/identity — PASS:** D681 source `primaryid=146628812`, `caseversion=2`, `fda_dt=20251230` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G11284-11287: 4 source rows -> 4 P / 4 S / 4 J records; all original fields agree. Source -> processed role counts: PS 1->1, SS 3->3.
- **Mapping — PASS:** G11284, DRUG_SEQ `1`: source `SIMVASTATIN` / PROD_AI `SIMVASTATIN` / role `PS` -> P canonical `simvastatin` (both), exposure `true`; S/J canonical `simvastatin` (both), exposure `true`. Exact references: M:28.
- **Mapping — PASS:** G11285, DRUG_SEQ `2`: source `PRAVASTATIN` / PROD_AI `PRAVASTATIN` / role `SS` -> P canonical `pravastatin` (both), exposure `false`; S/J canonical `pravastatin` (both), exposure `true`. Exact references: M:20.
- **Mapping — PASS:** G11286, DRUG_SEQ `3`: source `ATORVASTATIN` / PROD_AI `ATORVASTATIN` / role `SS` -> P canonical `atorvastatin` (both), exposure `false`; S/J canonical `atorvastatin` (both), exposure `true`. Exact references: M:2.
- **Mapping — PASS:** G11287, DRUG_SEQ `4`: source `FLUVASTATIN SODIUM` / PROD_AI `FLUVASTATIN SODIUM` / role `SS` -> P canonical `fluvastatin` (both), exposure `false`; S/J canonical `fluvastatin` (both), exposure `true`. Exact references: M:9.
- **Exposure — PASS:** independently expected PS {simvastatin} -> P/J {simvastatin}; expected PS+SS {atorvastatin, fluvastatin, pravastatin, simvastatin} -> S/J {atorvastatin, fluvastatin, pravastatin, simvastatin}. C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 3 source rows -> 3 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R6733 `Blood creatine phosphokinase increased` -> `BLOOD CREATINE PHOSPHOKINASE INCREASED`; R6734 `Muscle rupture` -> `MUSCLE RUPTURE`; R6735 `Myopathy` -> `MYOPATHY`.
- **Cautions:** Multiple suspected statins remain distinct ingredient presences; PS exposure is a subset of the PS+SS exposure. S mining basket has 7 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

### 14. Case 26202743 — PASS

References: K:15; J[13]; P/S `case_id='26202743'`.

- **Latest/identity — PASS:** D371480 source `primaryid=262027431`, `caseversion=1`, `fda_dt=20251226` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G1761822-1761823: 2 source rows -> 2 P / 2 S / 2 J records; all original fields agree. Source -> processed role counts: PS 1->1, SS 1->1.
- **Mapping — PASS:** G1761822, DRUG_SEQ `1`: source `LIPTRUZET` / PROD_AI `ATORVASTATIN CALCIUM\EZETIMIBE` / role `PS` -> P canonical `atorvastatin` (both), exposure `true`; S/J canonical `atorvastatin` (both), exposure `true`. Exact references: M:3, M:7.
- **Mapping — PASS:** G1761823, DRUG_SEQ `2`: source `EZETIMIBE\ROSUVASTATIN ZINC` / PROD_AI `EZETIMIBE\ROSUVASTATIN ZINC` / role `SS` -> P canonical `NULL` (unmapped), exposure `false`; S/J canonical `rosuvastatin` (prod_ai_sensitivity_review), exposure `true`. Exact references: O.
- **Exposure — PASS:** independently expected PS {atorvastatin} -> P/J {atorvastatin}; expected PS+SS {atorvastatin, rosuvastatin} -> S/J {atorvastatin, rosuvastatin}. C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 2 source rows -> 2 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R1309969 `Myalgia` -> `MYALGIA`; R1309970 `Gait disturbance` -> `GAIT DISTURBANCE`.
- **Cautions:** SS-only overlay adds the exact ROSUVASTATIN ZINC token; the complete ezetimibe combination row remains intact and the primary mapping remains NULL for that row. UNCERTAIN: external regulatory salt/alias appropriateness still requires the student's independent signoff; this check establishes exact policy application only. S mining basket has 4 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

### 15. Case 26212238 — PASS

References: K:16; J[14]; P/S `case_id='26212238'`.

- **Latest/identity — PASS:** D379636 source `primaryid=262122381`, `caseversion=1`, `fda_dt=20251230` -> identical retained P/S identity/version and J fields. 1 DEMO row(s) found for this case in the entire quarter; selected numeric maximum agrees. Not on the original quarter deletion list.
- **Complete drug rows/roles — PASS:** G1794031-1794033: 3 source rows -> 3 P / 3 S / 3 J records; all original fields agree. Source -> processed role counts: PS 1->1, SS 2->2.
- **Mapping — PASS:** G1794032, DRUG_SEQ `2`: source `EZETIMIBE\ROSUVASTATIN ZINC` / PROD_AI `EZETIMIBE\ROSUVASTATIN ZINC` / role `SS` -> P canonical `NULL` (unmapped), exposure `false`; S/J canonical `rosuvastatin` (prod_ai_sensitivity_review), exposure `true`. Exact references: O.
- **Exposure — PASS:** independently expected PS {} (background) -> P/J {} (background); expected PS+SS {rosuvastatin} -> S/J {rosuvastatin}. C/I rows are excluded even when their ingredient is mapped.
- **Reactions — PASS:** 1 source rows -> 1 distinct P/S/J reactions; each source -> processed value below agrees in both marts and J: R1333280 `Hepatic cytolysis` -> `HEPATIC CYTOLYSIS`.
- **Cautions:** SS-only overlay adds the exact ROSUVASTATIN ZINC token; the complete ezetimibe combination row remains intact and the primary mapping remains NULL for that row. UNCERTAIN: external regulatory salt/alias appropriateness still requires the student's independent signoff; this check establishes exact policy application only. S mining basket has 2 items and matches the independently reconstructed frozen-vocabulary basket.
- **UNCERTAIN boundary:** no other-quarter DEMO history was inspected; this PASS establishes latest selection within frozen 2025 Q4 only, not the globally latest FAERS report or clinical causality.

## Discrepancies, missing evidence and integrity

No source-to-packet or source-to-mart discrepancies were found in the inspected scope. The duplicate reaction rows, repeated dosing/DRUG_SEQ records, I-role exclusions, C-only background classifications and SS-only mapping overlays above are supported transformations, not corrections to frozen results.

Missing/uncertain evidence: other-quarter version history, independent external regulatory verification of the zinc-salt overlay, and clinical interpretation are outside this local reconciliation. Original reports supply co-reported roles and reactions, not causality, chronology or verified patient-level treatment histories. The deterministic sample is not a random audit of the complete dataset.

Relevant tests: **39 passed**, no failures/errors/skips. Commands: `python -m pytest -q tests/unit/test_preprocessing.py tests/unit/test_frozen_scope.py tests/integration/test_full_mart.py tests/integration/test_sensitivity.py` (WEKA fixture enabled); `ruff check .`; `ruff format --check src tests`; independent original-ZIP/extracted-source SHA-256 and all-column comparisons; frozen `verify_core()`; manifest checks for **1,096 primary / 1,106 sensitivity generated artifacts**. No real-data mining was rerun.

Baseline commit: `b4fa3c1ce8405a221aa5385efc776d262c3292f4`. All pre-existing tracked files were checked against their committed blob bytes, and all consumed source/packet/database/mapping inputs were hash-checked before and after. Only this new evidence report is intended for commit. The case checklist SHA-256 remains `9c5a16ceb73e99adcb795899d0b84f6a9dc04a16e537dd630ad8a5600ca17758`; `cases.json` remains `f0a220b363acc21d75077c3967a783a2be214dc59be1b86ff87eaa9678a919a9`. Student verification stays pending and `scientific_findings_validated` stays false.

Input SHA-256 values (full files, not selected-row hashes):

- `data/raw/2025Q4/extracted/ASCII/DEMO25Q4.txt`: `7f575aefc901aa380122bb5f35de98f2fc2f33dcaf050cf30426e10f3daa1ae2`.
- `data/raw/2025Q4/extracted/ASCII/DRUG25Q4.txt`: `886ef135263a63ee950be16bf4da1db04f856518b6072111822f1bc7e1112a0f`.
- `data/raw/2025Q4/extracted/ASCII/REAC25Q4.txt`: `1d98d0aa6b187edffb9f6dcffbd1569c16367740a7a126d306483e1888ef9de8`.
- `data/raw/2025Q4/extracted/Deleted/DELETE25Q4.txt`: `c24e98bef43cc601600de55d1978f434dd0f74c8c681b3aeff0108fd01438599`.
- `data/processed/2025Q4-statins/analytical.duckdb`: `2255f30a4b903d9b4ab09c258491e9f1ecc67e2edacf40fee8c1d51f7489a2ce`.
- `artifacts/generated/2025Q4-statins-sensitivity/mart/analytical.duckdb`: `4486d94cc9822962ef1127e7e01f9957f50c7d591806f3924e712fc6b8add803`.
- `mappings/drug_mapping.csv`: `9c26e3bf61608bba873b8475924b694ac7928d951012253b87af623d1f87e1c5`.
- `mappings/sensitivity_ss_aliases.csv`: `23fb8e380d5c171e0007349258e15c0d7f68f031bd102e26176a41a712798292`.
- `mappings/sensitivity_ss_review.yaml`: `54f4bd028568a77cd288f78e6fcf61b4f7eaa59eb6cd23928a94b0a2fffa066c`.

This report is supporting engineering evidence only. Reviewer fields and final manual conclusions are reserved for the student.
