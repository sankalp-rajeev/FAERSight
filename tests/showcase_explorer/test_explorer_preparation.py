import pytest

from showcase_explorer.prepare import (
    frozen_selection,
    native_preflight,
    project_arff,
    select_pair,
)
from tests.showcase.test_runner import require_pinned_runtime


def test_selection_is_canonical_and_accepted_at_exact_registered_support():
    benchmark = {
        "pairs": [
            {"drug": "atorvastatin", "reaction": "MYOPATHY"},
            {"drug": "rosuvastatin", "reaction": "MYOPATHY"},
        ]
    }
    rows = [
        {"drug": "rosuvastatin", "reaction": "MYOPATHY", "support_requested": "1.0E-5"},
        {"drug": "atorvastatin", "reaction": "MYOPATHY", "support_requested": ".00005"},
        {"drug": "atorvastatin", "reaction": "MYOPATHY", "support_requested": ".00001"},
    ]
    result = select_pair(benchmark, rows)
    assert result["rule"] == rows[2]
    assert result["candidate_order"][0] == ("atorvastatin", "MYOPATHY")
    assert select_pair(benchmark, list(reversed(rows))) == result


@pytest.mark.parametrize("duplicate", [False, True])
def test_missing_or_ambiguous_representative_is_rejected(duplicate):
    benchmark = {"pairs": [{"drug": "a", "reaction": "R"}]}
    rule = {"drug": "a", "reaction": "R", "support_requested": "0.00001"}
    with pytest.raises(ValueError, match="duplicate|No accepted"):
        select_pair(benchmark, [rule, rule] if duplicate else [])


def test_actual_frozen_selection_and_counts():
    result = frozen_selection()
    r = result["rule"]
    assert (r["drug"], r["reaction"], r["projection"]) == ("atorvastatin", "MYOPATHY", "r0239")
    assert (int(r["n"]), int(r["drug_count"]), int(r["reaction_count"]), int(r["joint_count"])) == (
        385288,
        1157,
        168,
        19,
    )
    assert float(r["weka_confidence"]) == 19 / 1157


@pytest.fixture
def small_source(tmp_path):
    names = ["DRUG_A", "DRUG_B", "REAC_IGNORE", "REAC_MYOPATHY"]
    source = tmp_path / "source.arff"
    source.write_text(
        "@relation fixture\n"
        + "\n".join(f"@attribute '{n}' {{0,1}}" for n in names)
        + "\n@data\n{}\n{0 1,2 1}\n{1 1,3 1}\n{2 1}\n",
        encoding="utf-8",
    )
    return source, names


def test_projection_preserves_all_rows_order_empty_rows_and_statins(small_source, tmp_path):
    source, names = small_source
    out = tmp_path / "projected.arff"
    result = project_arff(source, out, names, "MYOPATHY")
    assert result["rows"] == 4 and result["attributes"] == 3 and result["empty_reports"] == 2
    assert result["attribute_names"] == ["DRUG_A", "DRUG_B", "REAC_MYOPATHY"]
    assert result["source_column_indexes_zero_based"] == [0, 1, 3]
    assert out.read_text().split("@data\n")[1].splitlines() == ["{}", "{0 1}", "{1 1,2 1}", "{}"]
    assert result["drug_reaction_joint_counts"] == {"DRUG_B": 1}


def test_projection_rejects_nonpresence_values(small_source, tmp_path):
    source, names = small_source
    source.write_text(source.read_text().replace("{0 1,2 1}", "{0 0,2 1}"))
    with pytest.raises(ValueError, match="Nonbinary"):
        project_arff(source, tmp_path / "invalid.arff", names, "MYOPATHY")


def test_projection_bytes_are_deterministic(small_source, tmp_path):
    source, names = small_source
    a, b = tmp_path / "one.arff", tmp_path / "two.arff"
    first = project_arff(source, a, names, "MYOPATHY")
    second = project_arff(source, b, names, "MYOPATHY")
    assert a.read_bytes() == b.read_bytes() and first == second


@pytest.mark.weka
def test_native_parser_and_bean_options_are_preflight_not_GUI_or_mining(small_source, tmp_path):
    require_pinned_runtime()
    source, names = small_source
    arff = tmp_path / "projected.arff"
    project_arff(source, arff, names, "MYOPATHY")
    result = native_preflight(arff, tmp_path / "preflight")
    assert (result["rows"], result["attributes"], result["empty_reports"]) == (4, 3, 2)
    assert result["association_builds"] == 0 and result["GUI_observed"] is False
    fields = {r["property"]: r for r in result["unrestricted_fpgrowth"]["bean_properties"]}
    assert fields["positiveIndex"]["value"] == 2
    assert fields["maxNumberOfItems"]["value"] == -1
    assert fields["metricType"]["tag_id"] == 1
    assert fields["minMetric"]["value"] == 1.2
    assert fields["findAllRulesForSupportLevel"]["value"] is True
    assert fields["lowerBoundMinSupport"]["value"] == 0.004
    assert result["max_heap_bytes"] == 4294967296


def test_projection_never_overwrites_existing_artifact(small_source, tmp_path):
    source, names = small_source
    out = tmp_path / "existing.arff"
    out.write_bytes(b"preserved")
    with pytest.raises(FileExistsError):
        project_arff(source, out, names, "MYOPATHY")
    assert out.read_bytes() == b"preserved"
