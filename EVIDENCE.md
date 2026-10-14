# Evidence and review gate

This OSS workflow follows the file-based entry point, saved acceptance criteria,
independent review roles and mechanical reporting gate of
[V3R1T4S's run protocol](https://github.com/elder-plinius/V3R1T4S/blob/9b1d444eb864a1475e092047d49612a7410a7c5a/kit/RUN.md).
Its scientific target bank and statistical rules are replaced by software
regressions, benchmarks and feature checks. The operator has authorized publication
to their public forks and results repository. No upstream submission is authorized.

Each run has `runs/DATE.md` and `runs/DATE/result.json`. A candidate also has
`claim.md`, selected `evidence/` files and three `reviews/ROLE.json` files.
Write the claim before implementation; keep revised criteria in a new file and
explain the change. Save failures, not only successful commands.

The result record uses this shape (values here are descriptive placeholders):

```json
{
  "status": "verified",
  "summary": "One narrowly supported improvement",
  "kind": "bug",
  "upstream": "owner/repository",
  "baseline_commit": "40 lowercase hexadecimal characters",
  "candidate_commit": "40 lowercase hexadecimal characters",
  "candidate_source_sha256": "source fingerprint from the committed check",
  "claim": "claim.md",
  "checks": {
    "before": {"record": "evidence/before.json", "output": "evidence/before.log", "output_sha256": "sha256 of that log"},
    "after": {"record": "evidence/after.json", "output": "evidence/after.log", "output_sha256": "sha256 of that log"},
    "acceptance": [{"record": "evidence/suite.json", "output": "evidence/suite.log", "output_sha256": "sha256 of that log"}]
  },
  "publication": null
}
```

Copy the helper's actual `result.json` as each check record, plus its actual
`output.log`, after checking they are public-safe. The before/after commands and
image ID must match. The before check uses baseline production code with the same
regression test added; the after check names the candidate commit. Acceptance
checks may precede committing, but their source fingerprint must match the
committed after check. At least one relevant existing acceptance check is required.
For a bug or missing feature, the before check must fail because of the claimed
behavior and the after check must pass. For performance both commands pass;
reviewers must verify the repeated raw measurements, variability and equivalence.

Each reviewer writes its own JSON, with `ROLE` one of `reproduce`, `novelty`,
`criterion`:

```json
{
  "role": "reproduce",
  "context": "fresh agent",
  "candidate_commit": "the exact reviewed commit",
  "pass": true,
  "summary": "What this reviewer actually established",
  "evidence": ["Exact commands, observations and public sources"],
  "confirmed_scope": "Required only for criterion: the narrow supported claim"
}
```

The main agent reads every verdict and the complete diff. A repair changes the
candidate commit: obtain fresh verdicts for that revision, or carry it forward.
Do not write a review on a reviewer's behalf or infer approval from silence.

```sh
python3 check_run.py runs/DATE --publish  # required before publishing project code
python3 check_run.py runs/DATE            # required before finishing any run
```

`verified` requires all proof and all three passing reviews. Other statuses are
`promising`, `no_improvement`, and `blocked`; these require a summary and a dated
report, and cannot pass `--publish`. Their reports can still be published.
After a successful code push, set `publication` to an object with `repository`
(`Someblueman/NAME`), `parent` (the exact upstream), `commit`, `remote_commit`,
and `branch`, copied from Git/GitHub observations. Failed pushes leave publication
null and are explained in the report. The gate checks recorded equality, not GitHub.

The gate detects missing or inconsistent records, changed logs, wrong source
fingerprints, failed checks and missing/rejecting reviews. It does not establish
correctness, prove a reviewer was independent, or query the remote. Those remain
the reviewers' and operator agent's responsibilities. A reported PASS is a
record check, not an additional independent test of the software.
