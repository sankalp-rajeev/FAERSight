# Pinned WEKA 3.8.6 Apriori semantics

Step 2A engineering record. Authority: roadmap commit `69d27d7`; primary and
sensitivity code, configurations and evidence remain unchanged. No full-data
showcase association search has run.

Evidence is the **actual pinned binary**, its `-h` help, `javap -c -p` output,
runtime introspection and a 20-report semantic fixture. Retained inspection files
are under `artifacts/manifests/weka-showcase-step2a/semantics/`; locked fixture
evidence and the execution manifest are under the sibling `locked/` directory.
The runner is separate from `src/faersight/java/WekaExperiment.java`.

## Binary/runtime identity

WEKA jar SHA-256:
`932ea2f342b58fe45736389e9c426d5b5955e610d1f5f6485117f532068915e9`.
Existing Android Studio Java executable SHA-256:
`7f7bc646f8697255fc98a950412c741a453360586e1208ce683212f638444d85`.
The runtime identifies itself as OpenJDK `21.0.10+-14961533-b1163.108`.
The existing Bounce 0.18 jar is included explicitly, not an unbounded classpath
wildcard. No replacement WEKA version or new JDK is installed.

## Support and cycle behavior

- `-M` sets the lower support bound. Internally it is raised to `1/N` if the
  requested minimum would be below one report.
- The first support is `max(1 - delta, effective_lower)`, not simply `-U`.
  The ordinary default `-D 0.05` therefore starts at 0.95 and descends until
  enough rules have been obtained or the lower/count stopping condition applies.
- The locked command uses **`-D 1.0 -U 1.0 -M <support>`**. The first cycle starts
  at the requested lower bound; the next decrement drops below it, so there is
  exactly one cycle. The fixture proves one cycle versus 18 with the default
  decrement on the same data and requested cap. The exporter checks `m_cycles`.
- `-U` also prunes rules whose joint count exceeds `int(U*N + 0.5)` in
  `pruneRulesForUpperBoundSupport`. Setting `U=M` is not an equivalent fixed
  support command: the fixture returns zero rules instead of 50. Keep `U=1`.
- `findLargeItemSets` computes the integer minimum as
  **`int(max(requested_support, 1/N) * N + 0.5)`**, rounding positive counts to
  the nearest integer, with half rounded up. It does not take the ceiling.
  Java introspection of the pinned setup gives, at `N=385288`:
  `0.001 -> 385`, `0.0005 -> 193`, `0.0002 -> 77`, `0.0001 -> 39`.
  The fixture additionally verifies `.12*20=2.4 -> 2`, not 3.
- WEKA subtracts/re-adds delta in its final bookkeeping. The reported support
  double can differ from the requested value by floating rounding (for example
  0.1 becomes 0.09999999999999998). Requested options and actual state are both
  retained; integer counts, cycles and metrics are verified independently.

## Binary presence and population

`-Z` treats the **first nominal value** as missing for association counting.
With declared order `{0,1}`, implicit sparse zeros and explicit zero entries
cannot form mined items. It does not drop empty observations from `N`.
The fixture contains eight empty baskets among 20 reports; all metrics use 20.
Without `-Z`, the same fixture emits 120 rules and includes zero-valued items.
With it, all 50 qualifying exported rules use `=1` only. The exporter rejects
every non-presence item, missing/nonbinary input, non-unit case weight, duplicate
attribute name, wrong nominal order or changed input dimensions.

## Metrics and thresholds

The pinned `Apriori.TAGS_SELECTION` exposes:

- `-T 0`: confidence (ordinary default).
- `-T 1`: lift (locked showcase choice).
- `-T 2`: leverage.
- `-T 3`: conviction.

`-C` is the **minimum selected metric**, despite help text calling it minimum
confidence. The brute-force implementation accepts a metric **greater than or
equal to** the cutoff; its tip text's "higher" wording is less precise than the
comparison bytecode. Higher scores rank first. The locked lift cutoff is 1.2.
Changing the metric through `setMetricType` resets the default minimum to 0.9
for confidence, 1.1 for lift/conviction, or 0.1 for leverage. Explicit `-C 1.2`
overrides that for this lift study. No same-threshold metric comparison is run
in Step 2A; the four values below are exported for verification only.

For joint count `j`, antecedent count `l`, consequent count `r`, and `N`:

- Support: `j/N`; confidence: `j/l`.
- Lift: `(j/l)/(r/N)`.
- Leverage: `j/N - (l/N)*(r/N)`.
- **WEKA conviction: `(l*(N-r)/N)/(l-j+1)`**. The `+1` in the denominator is
  implemented both by `AprioriItemSet.convictionForRule` and by the public
  `DefaultAssociationRule` API. It is not the unsmoothed textbook formula.
  Perfect confidence therefore need not yield infinite conviction in this jar.

The exporter obtains all four values from WEKA's rule API, retaining the primary
metric name/value and native WEKA rank. Independent Python calculations use the
verified WEKA formula, with absolute and relative tolerance `1e-12` for every
fixture rule. Native ranking is preserved separately from canonical CSV order.

## Rule cap, direction and length

`-N` requests the maximum number of retained ranked rules. Rule generation occurs
before sorting and clipping the result lists; the cap **does not bound itemset
enumeration, candidate-rule work or memory**. `getAllTheRules` and
`getAssociationRules` expose the already clipped lists, not a pre-cap total.

A returned count **equal to 100000 is detectable but ambiguous**: exactly that
many rules and a larger clipped universe cannot be distinguished from the count
alone. The runner marks `stop_cap_ambiguity`, retains raw output, and prevents
descent. A fixture cap of one returns one where exhaustive independent counting
finds 50. A below-cap count establishes no cap clipping only conditional on the
other semantic/completeness checks; no cap increase or tuning is authorized.

With lift selected and class rules disabled, Apriori uses
`findRulesBruteForce`. It enumerates nonempty proper partitions of frequent
itemsets, allowing multiple items on either side and any attribute direction.
There is no configured maximum itemset length or single-consequent restriction
on this path. Frequent itemsets grow until no candidates survive. The fixture
recovers all four requested structures plus multi-item consequents (22 rules).
No namespace/direction/length filter is applied to the export.

There is an **implementation-level completeness caveat**: the brute-force
partition bound uses `(int)Math.pow(2, itemset_size)`. At sizes >=31 this saturates
the signed Java integer range and cannot represent all proper partitions.
Even smaller large sets can be prohibitively expensive. The exporter records
maximum frequent-itemset length and flags a completed run containing size >=31
as `stop_integer_partition_limit`; no exhaustive-rule claim is then permitted.
This is a factual binary limitation, not a silently imposed maximum length.
The search can hit its registered resource limit before it can return this audit;
such a failure is preserved and stops the ladder. No workaround is registered.

## Other defaults and resource semantics

- `-S` is the significance-test level; **`-S -1.0` disables testing**. It is
  unrelated to fixed support or the decrement. A nonnegative setting can filter
  rules by significance; the production showcase runner rejects that change.
- `-A` is off: no class-association restriction. `-c -1` is retained in resolved
  options but is irrelevant with `-A` off; the input has no designated class.
- `-R` is off: all-missing columns are not removed. The frozen vocabulary,
  including a statin with no PS exposure, remains intact.
- `-I` is off: full frequent-itemset text is not printed; it does not restrict
  mining. Counts and maximum size are audited through the subclass.
- `-V` is off. Traditional `toString` delimiters are left unchanged (`-B` absent);
  the canonical exporter uses item objects, not parsed rounded display strings.
- Apriori exposes **no processor/thread option** and these search methods use
  ordinary serial loops. The JVM honors `-XX:ActiveProcessorCount=2`, verified by
  `availableProcessors()==2` and VM flags. This is a JVM availability hint, not
  an Apriori two-thread setting, hard CPU quota or count of all JVM threads.
  `apriori_processor_option` is therefore explicitly not applicable/null.
- `-Xmx4g` is observed as 4,294,967,296 maximum heap bytes. Each invocation has
  a 1,800-second process timeout covering load, association search and export;
  compilation is separate with its own 120-second bound. Whole-process elapsed
  time and WEKA-build time are retained separately; no unmeasured peak memory
  claim is made. A shared lock prevents simultaneous showcase JVM invocations.
- One registered support level is invoked at a time. Failed/partial outputs
  cannot be overwritten, lower supports require successful predecessor records,
  and cap/numeric completeness stops are distinct from successful completion.

## Fixture evidence and next boundary

The deterministic input is `showcase/fixtures/semantic.arff` (20 rows, four
attributes). It was designed before the fixture run and has not been tuned to
hide an associator limitation. Two independent JVM runs return the same 50 rules;
every ordered disjoint nonempty itemset pair is independently enumerated to prove
coverage on this small fixture. Counts, direction, both side lengths and all four
metrics reconcile. Canonical export and raw output are byte-identical.

Step 2A only locks prerequisites. The 385,288-report ARFF is hash-verified, not
loaded into WEKA or mined. Full-data execution, later metric-ranking studies,
FPGrowth and Explorer remain unstarted and require the user's continuation.
