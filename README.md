# sparc-bench
**SWE-bench gives us exactly what we need: thousands of real GitHub issues, their ground-truth pull-request patches, and the unit-tests that prove each fix.  By wiring that dataset into Roo Code’s Boomerang workflow we can grade every run on three axes—steps, dollars, and correctness—without writing a single extra test.**

---

### 1 Project scaffold

```
bench-swe/
├─ harness/
│  └─ run_benchmark.py
├─ roomodes.json
├─ rules/
│  ├─ specification.md
│  ├─ pseudocode.md
│  ├─ architecture.md
│  ├─ refinement.md
│  └─ completion.md
└─ requirements.txt
```

*`requirements.txt`*

```txt
datasets==2.*
pytest==8.*
pytest-benchmark==4.*
pyperf==2.*
gitpython==3.*
rich==13.*
```

---

### 2 Pull a working slice of SWE-bench

```python
from datasets import load_dataset
ds = load_dataset("princeton-nlp/SWE-bench", "lite", split="test")  # 235 fast issues
ds = ds.rename_columns({"patch": "gold_patch"})   # clarity
ds.to_json("harness/swe_lite.json", orient="records", lines=True)
```

([GitHub][1], [SWE-bench][2])

---

### 3 Define Roo Code modes

*`roomodes.json`*

```jsonc
{
  "$schema": "https://roo.dev/schemas/roomodes-v1.json",
  "modes": {
    "Specification":  { "rules": "rules/specification.md" },
    "Pseudocode":     { "rules": "rules/pseudocode.md"   },
    "Architecture":   { "rules": "rules/architecture.md" },
    "Refinement":     { "rules": "rules/refinement.md"   },
    "Completion":     { "rules": "rules/completion.md"   }
  },
  "boomerang": {
    "plan": ["Specification", "Pseudocode", "Architecture",
             "Refinement", "Completion"]
  }
}
```

Each referenced **.md** file lists role, allowed actions, and exit criteria.  For example:

*`rules/refinement.md`*

```
### Purpose
Apply TDD and security review until unit-tests pass.

### Guard-rails
* Only edit files inside ./repo/**
* Never touch .git directory
* Run `pytest -q` after every change

### Done-when
All tests green; diff reviewed by CodeCritic mode.
```

---

### 4 Harness script

*`harness/run_benchmark.py`* (abridged)

```python
import json, os, subprocess, time, openai, git, pyperf, rich, statistics
from pathlib import Path
from datasets import load_dataset
from roo import BoomerangClient   # Roo SDK

HF_DATA = "harness/swe_lite.json"
TOKEN_PRICE = 0.00001  # $ per prompt token (example)

def _checkout_issue(issue):
    repo_url = issue["repo"]
    workspace = Path("work")/issue["issue_id"]
    git.Repo.clone_from(repo_url, workspace, depth=1)
    return workspace

def _apply_patch(workspace, patch):
    subprocess.run(["git", "apply", "-"], cwd=workspace, input=patch.encode(), check=True)

def solve(issue):
    ws = _checkout_issue(issue)
    client = BoomerangClient(roomodes="roomodes.json", workspace=ws)
    result = client.run(issue["title"] + "\n\n" + issue["body"])
    _apply_patch(ws, result["patch"])
    completed = subprocess.run(["pytest", "-q"], cwd=ws, capture_output=True)
    ok = completed.returncode == 0
    cost = result["usage"]["total_tokens"] * TOKEN_PRICE
    return {"ok": ok, "steps": result["steps"], "cost": cost}

def main():
    issues = [json.loads(l) for l in open(HF_DATA)]
    bench = pyperf.Runner(values=[])
    metrics = []
    for iss in issues:
        t0 = time.time()
        out = solve(iss)
        out["time"] = time.time() - t0
        metrics.append(out)
        bench.metadata[str(iss["issue_id"])] = out
    # aggregate
    passed = [m for m in metrics if m["ok"]]
    rich.print({
        "accuracy": len(passed)/len(metrics),
        "median_steps": statistics.median(m["steps"] for m in metrics),
        "median_cost": statistics.median(m["cost"] for m in metrics),
        "median_time": statistics.median(m["time"] for m in metrics)
    })

if __name__ == "__main__":
    main()
```

This script:

1. Clones the target repo.
2. Feeds the issue description to Roo Code via Boomerang.
3. Applies the generated patch.
4. Runs the project’s own unit-tests.
5. Logs steps, runtime, token-cost, and pass/fail.

---

### 5 How we score every run

| Metric          | Source                           | Goal                              |
| --------------- | -------------------------------- | --------------------------------- |
| **Steps**       | `result["steps"]` from Boomerang | Fewer mode hops ⇒ better planning |
| **Cost**        | token count × unit price         | Budget impact                     |
| **Performance** | Unit-test pass rate              | Functional correctness            |
| **Time**        | Wall-clock seconds               | Latency awareness                 |

All results are stored in **pyperf**’s JSON so we can diff regressions across model upgrades or temperature tweaks.

---

### 6 Running the benchmark

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python harness/run_benchmark.py
```

The script prints aggregate stats and leaves individual run metadata in `~/.pyperf`.  Feed that to `pyperf compare_to` or ship it to a dashboard of your choice.

---

### 7 Expanding beyond the “lite” split

Replace `"lite"` with `"test"` (full 2 294 issues) or the stricter **SWE-bench Verified** subset for higher-fidelity evaluation.  The harness stays the same.([GitHub][3], [DEV Community][4])

---

**With SWE-bench wired into Roo Code we’re no longer guessing: every agentic edit is judged by the project’s own tests, every token is priced, and every orchestration hop is counted.  That clarity turns iteration into compounding insight.**

[1]: https://github.com/SWE-bench/SWE-bench?utm_source=chatgpt.com "SWE-bench [Multimodal]: Can Language Models Resolve ... - GitHub"
[2]: https://www.swebench.com/SWE-bench/guides/datasets/?utm_source=chatgpt.com "Datasets - SWE-bench documentation"
[3]: https://github.com/swe-bench?utm_source=chatgpt.com "SWE-bench - GitHub"
[4]: https://dev.to/duplys/swe-bench-swe-bench-verified-benchmarks-1cm?utm_source=chatgpt.com "SWE-bench & SWE-bench Verified Benchmarks - DEV Community"
