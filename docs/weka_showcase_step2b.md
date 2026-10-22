# WEKA Showcase Step 2B: first full-data attempt at support 0.001

Factual engineering record, October 22, 2026. This records one authorized
feasibility attempt, not a scientific interpretation or a completed rule study.

## Registered invocation and outcome

The exact authorized command was invoked once from repository commit `78dd8de`,
using the Step 2A execution manifest and implementation commit `11d81fa`:

```powershell
.venv/Scripts/python -m showcase.runner run --execution-manifest artifacts/manifests/weka-showcase-step2a/locked/execution_manifest.json --support 0.001 --output artifacts/generated/weka-showcase/full/0.001 --authorize-full-data
```

The Java subprocess **timed out at its registered 1,800-second wall-clock limit**.
The runner exited with code **1**. Total command wall time was
**1,804.6805372 seconds** (30 minutes 4.68 seconds), including Python preflight
and compilation. The runner's separately recorded interval including compilation
was 1,800.6743626 seconds. Its timeout exception records the 1,800-second JVM
limit explicitly. No association-build duration was returned. A separate native
Java exit code was not retained by the locked runner on this timeout path.

Capture start: `2026-10-22T21:40:46.492600+00:00`. The runner recorded the timeout
at `2026-10-22T22:10:51.235189+00:00`. There was no retry or tuning.

The input remained the primary PS sparse ARFF: **385,288 reports, 366 attributes**,
SHA-256 `de0f94f545ebae18033195524984fc842d3359154b864cb52bef2372a877dcf1`.
The actual resolved options were:

```text
-N 100000 -T 1 -C 1.2 -D 1.0 -U 1.0 -M 0.001 -S -1.0 -Z -c -1
```

The requested minimum count was **385**, calculated by the verified WEKA rounding
rule. The timeout returned no WEKA run-result metadata, so an observed support
count or completed cycle count is not claimed. The registered fixed-support
configuration, unrestricted exporter, 4 GiB heap, JVM `ActiveProcessorCount=2`,
single-JVM lock and timeout were unchanged. Apriori has no algorithm-level
thread setting, as documented in Step 2A.

## Requested rule statistics

There is no completed `run.json`, `rules.csv`, `apriori_raw.txt` or `complete.txt`.
Consequently all of the following are **unavailable, not zero**:

- Returned rule count and whether exactly 100,000 rules would have been returned.
- Whether the >=31-itemset implementation caveat was encountered.
- Maximum antecedent size, consequent size and total rule item count.
- Counts for single-statin -> single-reaction rules; two-statins -> reaction;
  statin-plus-reaction -> reaction; reaction -> reaction; multi-item consequents;
  or any other structural family.
- Representative multi-item rules with counts, support, confidence and lift.

The user authorized mechanical rule analysis only after a successful below-cap
run. That condition was not met. No partial rules are presented as complete
output, and no examples or structural counts were inferred from the fixture.
No broader scientific interpretation was performed.

## Preserved evidence

Raw local output: `artifacts/generated/weka-showcase/full/0.001/`.
Invocation capture: `artifacts/generated/weka-showcase/step2b-0.001-capture/`.
Tracked snapshot: `artifacts/manifests/weka-showcase-step2b-0.001/`.

The tracked snapshot retains the complete command and JVM arguments, exact
resolved options, original invocation manifest, combined stdout/stderr, current
Java/Javac version output, pinned runtime/input hashes, exit status, timings and
core-preservation checks. `raw_output.zip` contains every emitted raw-output file,
including compiled class bytes and partial evidence. Each archived entry is
verified against its original SHA-256. `evidence_index.json` lists all snapshot
hashes and the uncompressed raw-file hashes. `run_outcome.json` records unavailable
statistics explicitly as null and distinguishes the locked count from an
observed WEKA result. No ARFF rows or report-level identifiers are published.

The capture script records the exact existing runner invocation; the exporter
does not invoke mining. Both live under `scripts/` and do not alter the locked
showcase source/configuration or any scientific-core implementation.

## Validation and decision gate

The pre- and post-attempt byte checks confirm that all **108 frozen core files**
still match roadmap commit `69d27d7`. The Step 2A source hashes/configuration and
execution manifest remain unchanged. Milestone 3/4 evidence indices, input
hashes, source snapshot and original mart also revalidate without changes.
All **113 post-run tests passed**, with zero failures, errors or skips, including
the 100 existing core tests and 13 showcase fixture tests. The result is stored
in the snapshot's `test_results.json`; lint and format checks pass. All scientific
validation flags remain unchanged.

**Do not proceed to 0.0005 under the current registered stop rule.** The first
full-data invocation timed out, which stops ladder descent. A separate review
and plan amendment would be required before any retry or altered execution.
No 0.0005, 0.0002 or 0.0001 full-data showcase invocation, metric-comparison
experiment, FPGrowth run or Explorer demo was performed. Preserve this failed
attempt and stop at the Step 2B evidence checkpoint.
