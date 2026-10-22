# WEKA Showcase: isolated Step 2A checkpoint

Plan authority: `69d27d7`. This directory contains the separate configuration,
Java exporter, Python runner and tiny semantic fixture. It does not modify the
frozen scientific implementation. Read [SEMANTICS.md](SEMANTICS.md) for verified
binary behavior, cap ambiguity and the long-itemset caveat.

The configuration locks the existing primary PS ARFF, 2025 Q4 only, 385,288
reports / 366 attributes. Lift >=1.2, supports 0.001/0.0005/0.0002/0.0001,
100,000 returned-rule cap, 4 GiB heap and 30-minute timeout remain as planned.
The two-processor JVM hint is verified; an Apriori parallelism option is not
applicable. There is no pair-only export filter, co-drug expansion or classifier.

Inspection and fixture commands, using unused output directories:

```powershell
.venv/Scripts/python -m showcase.inspect artifacts/generated/weka-showcase/new-inspection
.venv/Scripts/python -m showcase.runner fixture --output artifacts/generated/weka-showcase/new-fixture
```

The fixture command starts small, sequential JVMs only. It checks all 50
qualifying rule partitions and all four metrics independently, repeats the
export, and tests cap, integer-rounding, upper-support, decrement and zero-value
behavior. The test suite adds malformed-input and execution-authorization gates.
Tests go under `tests/showcase/`; all original tests still apply.

After the implementation/configuration is committed and tests pass, the `lock`
command records that code commit, complete runtime/options, fixture hashes,
core byte-preservation checks and the unstarted full-data boundary. It hashes
the primary ARFF without handing it to WEKA. Its evidence bundle omits compiled
class files and contains no full-data showcase results.

**Do not execute the following command during Step 2A.** After separate explicit
user authorization, the first full-data invocation would be:

```powershell
.venv/Scripts/python -m showcase.runner run --execution-manifest artifacts/manifests/weka-showcase-step2a/locked/execution_manifest.json --support 0.001 --output artifacts/generated/weka-showcase/full/0.001 --authorize-full-data
```

The command runs only that support level; it does not automatically descend.
The authorization switch is required and is absent from fixture/lock commands.
Later ladder levels require successful, nontruncated predecessors in the fixed
output locations. A cap/numeric-ambiguity return exits nonzero; a timeout or
resource/semantic failure leaves its logs and blocks descent. Do not remove the
stop history or tune around it without a separately registered plan amendment.

All outputs remain factual engineering evidence with
`scientific_findings_validated: false`. Presentation prose and interpretation
remain student-owned.
