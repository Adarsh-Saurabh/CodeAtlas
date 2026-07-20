from pathlib import Path

from analyzer.bottleneck_rules import find_bottlenecks


ROOT = Path(__file__).parents[1]


def test_detects_three_explicit_bottlenecks_without_clean_false_positive():
    repo = ROOT / "fixtures" / "sample_repo_with_bottlenecks"
    findings = find_bottlenecks(repo / "bottlenecks.py", repo)["bottlenecks.slow"]
    assert {item["kind"] for item in findings} == {"nested_loop", "blocking_io", "n_plus_one"}
    assert not find_bottlenecks(repo / "clean.py", repo)
