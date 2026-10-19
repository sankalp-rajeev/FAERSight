-- Run only after raw source identities and schemas have been validated.
CREATE TABLE latest_cases AS
SELECT trim(caseid) AS case_id, trim(primaryid) AS primary_id,
       CAST(caseversion AS BIGINT) AS case_version, _quarter AS quarter,
       _source_row AS source_row, d.*
FROM raw_demo d
QUALIFY row_number() OVER (
    PARTITION BY trim(caseid)
    ORDER BY CAST(caseversion AS BIGINT) DESC, CAST(primaryid AS BIGINT) DESC,
             _quarter DESC, _source_row ASC
) = 1;

CREATE TABLE case_eligibility AS
SELECT c.case_id, c.primary_id, c.quarter,
       EXISTS (SELECT 1 FROM deleted_cases x WHERE x.case_id = c.case_id) AS is_deleted,
       EXISTS (SELECT 1 FROM raw_drug r WHERE trim(r.primaryid) = c.primary_id
               AND trim(r.caseid) = c.case_id AND r._quarter = c.quarter) AS has_drug,
       EXISTS (SELECT 1 FROM raw_reac r WHERE trim(r.primaryid) = c.primary_id
               AND trim(r.caseid) = c.case_id AND r._quarter = c.quarter
               AND nullif(trim(r.pt), '') IS NOT NULL) AS has_reaction
FROM latest_cases c;

-- Eligibility is independent of therapeutic class, mapping, role and vocabulary.
CREATE TABLE cases AS
SELECT c.* FROM latest_cases c JOIN case_eligibility e
USING (case_id, primary_id, quarter)
WHERE NOT e.is_deleted AND e.has_drug AND e.has_reaction;
CREATE UNIQUE INDEX cases_identity ON cases(case_id);

CREATE TEMP TABLE retained_drug_keys AS
SELECT c.case_id, c.primary_id, c.quarter, r.*,
       upper(trim(regexp_replace(coalesce(r.drugname, ''), '\s+', ' ', 'g'))) AS normalized_name,
       upper(trim(regexp_replace(coalesce(r.prod_ai, ''), '\s+', ' ', 'g'))) AS normalized_prod_ai
FROM cases c JOIN raw_drug r
ON c.primary_id = trim(r.primaryid) AND c.case_id = trim(r.caseid) AND c.quarter = r._quarter;

CREATE TEMP TABLE ingredient_matches AS
SELECT r.quarter, r._source_row, count(DISTINCT m.canonical_ingredient) AS matched_ingredients,
       min(m.canonical_ingredient) AS ai_ingredient
FROM retained_drug_keys r,
     unnest(string_split(r.normalized_prod_ai,
                         (SELECT ingredient_separator FROM analysis_settings))) t(ingredient)
JOIN drug_mapping m ON trim(t.ingredient) = m.raw_name AND m.alias_type = 'ingredient'
GROUP BY r.quarter, r._source_row;

CREATE TABLE case_drugs AS
WITH matched AS (
    SELECT r.*, m.canonical_ingredient AS name_ingredient, ai.ai_ingredient,
           coalesce(ai.matched_ingredients, 0) AS matched_ai_count,
           coalesce(ai.matched_ingredients > 1 OR
                    (m.canonical_ingredient IS NOT NULL AND ai.ai_ingredient IS NOT NULL
                     AND m.canonical_ingredient <> ai.ai_ingredient), false) AS mapping_conflict
    FROM retained_drug_keys r
    LEFT JOIN drug_mapping m ON r.normalized_name = m.raw_name
    LEFT JOIN ingredient_matches ai ON r.quarter = ai.quarter AND r._source_row = ai._source_row
), canonical AS (
    SELECT *, CASE WHEN mapping_conflict THEN NULL
                   ELSE coalesce(ai_ingredient, name_ingredient) END AS canonical_ingredient,
           upper(trim(coalesce(role_cod, ''))) AS role_code
    FROM matched
)
SELECT *, CASE WHEN canonical_ingredient IS NOT NULL
               THEN (SELECT therapeutic_class FROM analysis_settings) END AS target_class,
       CASE WHEN mapping_conflict THEN 'conflict'
            WHEN name_ingredient IS NOT NULL AND ai_ingredient IS NOT NULL THEN 'both'
            WHEN ai_ingredient IS NOT NULL THEN 'prod_ai'
            WHEN name_ingredient IS NOT NULL THEN 'drugname'
            ELSE 'unmapped' END AS mapping_method,
       canonical_ingredient IS NOT NULL AND NOT mapping_conflict
       AND role_code IN (SELECT role_code FROM analysis_roles) AS is_target_exposure,
       canonical_ingredient IS NULL AND NOT mapping_conflict AND
       regexp_matches(normalized_name || ' ' || normalized_prod_ai,
                      (SELECT target_candidate_pattern FROM analysis_settings))
       AS is_unmapped_target_candidate
FROM canonical;
-- DRUG_SEQ is deliberately not unique: FDA permits repeated dosing/route rows.
CREATE UNIQUE INDEX case_drug_source ON case_drugs(quarter, _source_row);

CREATE TABLE case_reactions AS
SELECT DISTINCT c.case_id, c.primary_id, c.quarter,
       upper(trim(regexp_replace(r.pt, '\s+', ' ', 'g'))) AS reaction
FROM cases c JOIN raw_reac r
ON c.primary_id = trim(r.primaryid) AND c.case_id = trim(r.caseid) AND c.quarter = r._quarter
WHERE nullif(trim(r.pt), '') IS NOT NULL;
CREATE UNIQUE INDEX reaction_presence ON case_reactions(case_id, reaction);

CREATE TABLE case_drug_presence AS
SELECT DISTINCT case_id, primary_id, quarter, canonical_ingredient AS drug
FROM case_drugs WHERE is_target_exposure;
CREATE UNIQUE INDEX drug_presence ON case_drug_presence(case_id, drug);

CREATE TABLE candidate_reactions AS
SELECT reaction, count(*) AS target_case_count
FROM case_reactions r
WHERE EXISTS (SELECT 1 FROM case_drug_presence d WHERE d.case_id = r.case_id)
GROUP BY reaction
HAVING count(*) >= (SELECT reaction_min_target_cases FROM analysis_settings);

CREATE TABLE case_items AS
SELECT case_id, 'DRUG' AS item_type, drug AS item_value FROM case_drug_presence
UNION ALL
SELECT r.case_id, 'REAC' AS item_type, r.reaction AS item_value
FROM case_reactions r JOIN candidate_reactions v USING (reaction);

CREATE TABLE signal_counts AS
WITH drug_totals AS (
    SELECT drug, count(*) AS exposed_n FROM case_drug_presence GROUP BY drug
), reaction_totals AS (
    SELECT reaction, count(*) AS reaction_n FROM case_reactions GROUP BY reaction
), pair_totals AS (
    SELECT d.drug, r.reaction, count(*) AS a
    FROM case_drug_presence d JOIN case_reactions r USING (case_id)
    JOIN candidate_reactions v USING (reaction) GROUP BY d.drug, r.reaction
), counts AS (
    SELECT g.drug, v.reaction, coalesce(p.a, 0)::BIGINT AS a,
           coalesce(d.exposed_n, 0)::BIGINT AS exposed_n,
           coalesce(r.reaction_n, 0)::BIGINT AS reaction_n,
           (SELECT count(*) FROM cases)::BIGINT AS n
    FROM class_ingredients g CROSS JOIN candidate_reactions v
    LEFT JOIN drug_totals d ON g.drug = d.drug
    LEFT JOIN reaction_totals r ON v.reaction = r.reaction
    LEFT JOIN pair_totals p ON g.drug = p.drug AND v.reaction = p.reaction
)
SELECT drug, reaction, a, exposed_n - a AS b, reaction_n - a AS c,
       n - exposed_n - reaction_n + a AS d, n
FROM counts;

CREATE VIEW quarter_drug_role AS
SELECT quarter, canonical_ingredient AS drug, role_code,
       count(DISTINCT case_id) AS report_count, count(*) AS source_drug_rows
FROM case_drugs WHERE canonical_ingredient IS NOT NULL GROUP BY ALL;
CREATE VIEW quarter_reaction AS
SELECT quarter, reaction, count(*) AS report_count FROM case_reactions GROUP BY ALL;
CREATE VIEW quarter_population AS
SELECT quarter, count(*) AS eligible_reports,
       count(*) FILTER (WHERE EXISTS (SELECT 1 FROM case_drug_presence d
                                     WHERE d.case_id = c.case_id)) AS target_exposed_reports,
       count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM case_drug_presence d
                                         WHERE d.case_id = c.case_id)) AS background_reports
FROM cases c GROUP BY quarter;
