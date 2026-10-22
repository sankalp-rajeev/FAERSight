# Student inspection packet (2025 Q4 only)

This is a deterministic engineering sample, not a representative random sample or course-report prose. All student verdicts remain pending. Detailed public report records stay local.

1. Open cases.json alongside case_checklist.csv. Verify latest retained report, complete source DRUG rows, PS/SS/C roles, distinct ingredient presence, combination handling and exact reaction memberships. Source rows are physical text lines including the header. Automated source checks do not sign off this review.
2. Inspect both exact SS zinc-salt cases against mappings/sensitivity_ss_review.yaml and the regulatory sources. Confirm that C remains background and the primary mapping is unchanged.
3. Use rules.csv to compare raw a,b,c,d,N, lift/PRR/ROR, ROR intervals, sparse counts and screening flips. Explain a stable benchmark, a role-sensitive association and a sparse extreme. Co-listed drugs/reactions do not establish a causal link.
4. Check all eight benchmark labels using benchmark_checklist.csv. Positive-only references cannot estimate specificity.
5. Record reviewer/date/verdict/notes yourself. Draft submission interpretation in your own words. The PRR flag (a>=3, PRR>=2, Yates chi-square>=4) and unadjusted log-Wald ROR intervals are descriptive screening conventions, not clinical truth. Zero-cell ROR intervals are unavailable; no pseudocount is added.
