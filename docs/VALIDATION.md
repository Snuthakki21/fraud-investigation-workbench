# Standalone verification evidence

Checked at 2026-09-17T05:02:00.286923+00:00. These results come from commands executed inside this repository after export.

Runtime versions: Python 3.14.7; Node.js v25.9.0.

Standalone release verification: **PASS**. All recorded commands passed.

| Check | Observed result |
|---|---|
| Python unit and integration tests | 86 discovered; 84 executed; 2 skipped |
| Statement coverage | 611/616 (99.19%) |
| Branch coverage | 284/290 (97.93%) |
| Frontend tests | 31 discovered; 27 executed; 4 skipped |
| Built application discovery | fraud_investigation_workbench |
| Installed project directories | fraud_investigation_workbench |
| Installed UI templates | fraud_investigation_workbench |
| Missing README targets | [] |
| Default input | Executed through the repository CLI; saved in `examples/report.json` |

Reproduce from the repository root:

```sh
python -m pip install -r requirements-dev.txt
python -m coverage run -m unittest discover -s tests -v
python -m coverage report --fail-under=90
python -m portfolio build --output dist
node --test tests/frontend.test.mjs
```

Application source SHA-256: `c1833450f17ca6456aa3f4fab680e175e92d392a91f89e977197060a8b914715`.

Coverage includes this application and its shared Python runtime. Skipped tests exercise capabilities belonging to applications absent from this standalone repository. Provider transport tests use controlled doubles; these counts are not live-model accuracy measurements. The frontend suite exercises rendering, escaping, input binding and asynchronous state with controlled DOM/worker harnesses; it is not an exhaustive visual, accessibility or browser compatibility audit. Coverage measures executed code paths and does not establish semantic correctness.

See the solution-specific independent review linked in the README and the [shared runtime review](INDEPENDENT_RUNTIME_REVIEW.md) for review findings, repairs and limits.
