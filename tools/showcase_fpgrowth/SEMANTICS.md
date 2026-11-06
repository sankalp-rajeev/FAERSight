# Pinned FPGrowth 3.8.6 semantics and pre-run mode decision

Evidence: `artifacts/manifests/weka-showcase-fpgrowth/semantics/`, exact binary
hashes inherited unchanged from Step 2A. The `javap -c -p` output is implementation
evidence, not an assumption from another WEKA release. An exploratory lookup of
the nonexistent nested `FPGrowth$AssociationRule` is retained with exit 1;
actual rules use `DefaultAssociationRule`. Inspection did not mine full data.

- `-S` is a **flag**, not Apriori's significance option. It starts at lower
  support and exits after that cycle, disabling iterative support reduction.
- `-N` defaults to 10. Without `-S`, it is the desired rule count for support
  descent and clips both `getAssociationRules()` and textual display after
  internal generation. Internal `m_rules` can exceed N. With `-S`, N is ignored
  for both descent and API/display clipping; it does not bound generation.
- Without `-S`, execution starts at support 1.0, not at `-U`. `-D` subtracts
  support after each build; it clamps to lower support for the final pass if
  needed. `-U` is an inclusive maximum **joint rule support** filter, not the
  initial mining support. `-U 1 -D 1 -M .1` takes **two** tree-build passes on the
  fixture (20 then 2 minimum count). It does not meet a single-cycle contract.
- Fractional lower/upper support converts using `ceil(fraction*N)`; values >1
  are absolute counts cast to int. Delta >1 is divided by N, otherwise it is a
  fraction. This runner permits registered fractional support only. At .001
  and N=385288 the cutoff is **386**, versus Apriori's rounded **385**. At .12
  on 20 rows FPGrowth resolves 3 versus Apriori 2. No count matching is substituted.
- `-T`: confidence=0, lift=1, leverage=2, conviction=3; `-C` is the inclusive
  minimum selected metric (default .9). Lock lift `-T 1 -C 1.2`. All four metrics
  are available through the rule API. `DefaultAssociationRule` conviction is
  `(lhs*(N-rhs)/N)/(lhs-joint+1)`; document this WEKA convention.
- `-P` uses a **one-based nominal-value index**, default 2. For sparse instances
  singleton counting/tree insertion uses stored nonzero indexes, independent of
  P. However binary item labels are constructed with P-1: the fixture with P=1
  still counts the stored presences but labels rules `=0`. Therefore explicitly
  lock **P=2**, verify `{0,1}` and reject every exported non-`=1` item. Help's
  statement that sparse instances always use index 2 does not justify P=1.
  Empty sparse rows remain in N; no transaction filter is enabled.
- `-I` limits total frequent-itemset size (hence total rule length), default -1
  unbounded. Lock -1. Rule generation enumerates all nonempty proper partitions
  of frequent binary itemsets, including multi-item consequents and both
  directions. It uses a boolean-array subset counter, not Apriori's saturated
  int/Math.pow partition loop; Apriori's >=31-itemset caveat is not transferred
  to this algorithm. Exponential enumeration/resource limits still apply.
- `-transactions`/`-rules` default empty, `-use-or` false. No presence/direction
  filter, class assignment, maximum length or `-disk` mode is added. In-memory
  Instances uses the same full input population and empty rows as Apriori.
- No associator thread/processor option or parallel executor occurs in the
  inspected implementation. `-XX:ActiveProcessorCount=2` is a JVM hint observed
  as availableProcessors=2, not parallel mining or a CPU quota. Heap is exactly
  4294967296 bytes. The single shared JVM lock also covers compilation.

## Selected mode and honest completion gate

Choose **Mode 1 (`-S`) before any full-data result**. It implements exactly one
fixed-support pass, whereas the proposed Mode 2 does not. Retain `-N 100000`
as a recorded requested count, explicitly **not an enforceable generation or
export cap**. Reliable completion signal: build returns normally, all rules are
exported with a completion marker, and API count equals the protected internal
`m_rules.size()`. At or above 100000 internal rules, preserve output and stop for
review even if enumeration completed; never call this clipping detection in -S.
Below 100000, this count equality plus normal unrestricted completion establishes
absence of N truncation. Heap/time remain the effective resource bounds.

The exporter does not override mining or rule generation. The protected
`buildFPTree` signature refers to a private nested type, so it cannot be
overridden for cycle observation. Instead a read-only `Instances.instance(i)`
counter is reset immediately after `getSingletons(Object)`; the inspected
in-memory tree builder reads exactly N rows per cycle thereafter. Report the
observed scan count and tree passes, and separately the resolved lower count
computed from the verified expression; do not label it a native WEKA printed
support. The fixture verifies one pass under -S and two without it, and checks
every count/rule independently. Input values and algorithm behavior are unchanged.

Fixture: 20 rows, 4 attributes, 8 empty baskets; exhaustive 50-rule family,
22 multi-item consequents, all five planned forms, all counts/four metrics within
1e-12, repeated canonical CSV and raw model byte-identical. Probes cover N=1 in
both modes, rounding, sparse P=1 mislabeling and I=2. No full ARFF is used in fixtures.

## Locked command

`-P 2 -I -1 -N 100000 -T 1 -C 1.2 -U 1.0 -M 0.001 -D 1.0 -S`

Run exactly one separate full-data invocation after committed manifest/fixture
validation; stop on error, timeout, resource failure, incomplete export or policy
limit. No fallback, retry, support descent, metric experiment or GUI is implicit.
Compare nominal supports with the 386/385 limitation disclosed. With Apriori's
unfinished model there is no rule overlap or completed-runtime ratio to compute.
