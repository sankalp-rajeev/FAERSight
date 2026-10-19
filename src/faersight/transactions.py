"""Build a shared report universe; therapeutic-class selection limits items only."""

from collections import Counter, defaultdict
from dataclasses import dataclass

from faersight.deduplicate import latest_cases
from faersight.normalize import normalized_name


@dataclass(frozen=True)
class Transaction:
    case_id: str
    primary_id: str
    quarter: str
    drugs: frozenset[str]
    reactions: frozenset[str]


def build_transactions(
    demo: list[dict],
    drugs: list[dict],
    reactions: list[dict],
    mapping: dict[str, str],
    *,
    roles: tuple[str, ...] = ("PS",),
    min_target_cases: int = 1,
) -> tuple[list[Transaction], dict]:
    if type(min_target_cases) is not int or min_target_cases < 1:
        raise ValueError("min_target_cases must be a positive integer")
    if roles not in (("PS",), ("PS", "SS")):
        raise ValueError("roles must be PS or PS+SS")
    retained = latest_cases(demo)
    drug_rows, reaction_rows = defaultdict(list), defaultdict(set)
    demo_ids = {row["primaryid"] for row in demo}
    unknown = Counter()
    role_counts = Counter()
    for row in drugs:
        drug_rows[row["primaryid"]].append(row)
    for row in reactions:
        reaction_rows[row["primaryid"]].add(" ".join(row["pt"].upper().split()))
    transactions = []
    excluded = 0
    for case in retained:
        primary_id = case["primaryid"]
        if not drug_rows[primary_id] or not reaction_rows[primary_id]:
            excluded += 1
            continue
        present = set()
        for row in drug_rows[primary_id]:
            role_counts[row["role_cod"]] += 1
            if row["role_cod"] not in roles:
                continue
            raw = normalized_name(row["drugname"])
            if raw in mapping:
                present.add(mapping[raw])
            else:
                unknown[raw] += 1
        transactions.append(
            Transaction(
                case["caseid"],
                primary_id,
                case["quarter"],
                frozenset(present),
                frozenset(reaction_rows[primary_id]),
            )
        )
    counts = Counter(reaction for txn in transactions if txn.drugs for reaction in txn.reactions)
    vocabulary = {reaction for reaction, count in counts.items() if count >= min_target_cases}
    # Keep empty baskets and reports with no target drug in the same N.
    selected = [
        Transaction(t.case_id, t.primary_id, t.quarter, t.drugs, t.reactions & vocabulary)
        for t in transactions
    ]
    audit = {
        "source_demo_rows": len(demo),
        "source_drug_rows": len(drugs),
        "source_reac_rows": len(reactions),
        "unique_case_ids_before_dedup": len({row["caseid"] for row in demo}),
        "case_versions_removed": len(demo) - len(retained),
        "excluded_latest_cases_missing_drug_or_reaction": excluded,
        "orphan_drug_rows": sum(row["primaryid"] not in demo_ids for row in drugs),
        "orphan_reaction_rows": sum(row["primaryid"] not in demo_ids for row in reactions),
        "eligible_cases_after_dedup": len(selected),
        "final_transaction_count": len(selected),
        "target_exposed_cases": sum(bool(t.drugs) for t in selected),
        "candidate_reaction_count": len(vocabulary),
        "roles": list(roles),
        "retained_eligible_drug_rows_by_role": dict(sorted(role_counts.items())),
        "unmapped_eligible_role_names": dict(sorted(unknown.items())),
        "reaction_min_target_cases": min_target_cases,
    }
    return selected, audit
