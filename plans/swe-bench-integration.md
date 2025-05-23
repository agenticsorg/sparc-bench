# SWE-bench Integration & Benchmarking Plan for roocode SPARC (Native Implementation)

## 1. Overview

This plan details the native (non-Docker) installation, configuration, and automation of SWE-bench (lite and full) to benchmark the roocode SPARC system. All SWE tasks will be completed by the roocode agentic system rather than direct LLM calls. Includes requirements, setup, orchestration via `new_task`, and .roomodes updates.

---

## 2. Requirements

- **Hardware:** 16GB RAM, 8 CPUs, 60GB disk space (reduced without Docker)
- **Software:** Python 3.8+, Git, native SWE-bench tools, Make
- **API Keys:** GitHub token (required), roocode API access
- **Network:** Internet access for SWE-bench datasets and repositories
- **Environment:** Native Python environment (no containerization)

---

## 3. Installation Steps (Native)

### 3.1 Native SWE-bench Setup

- Clone SWE-bench repository: `git clone https://github.com/SWE-bench/SWE-bench`
- Install dependencies: `pip install -e .` (in SWE-bench directory)
- Install evaluation harness natively without Docker dependencies

### 3.2 SWE-bench CLI (Native)

- Install sb-cli without Docker requirements:
  ```bash
  pip install swebench --no-deps
  pip install -r requirements-native.txt  # custom requirements without Docker
  ```
- Configure for native execution mode
- Authenticate with SWE-bench API key

### 3.3 roocode Integration Config

- Create `roocode-config.yaml` in the project root:
  ```yaml
  github_token: 'your_github_token'
  roocode_api_endpoint: 'your_roocode_endpoint'
  benchmark_mode: 'native'
  docker_enabled: false
  agent_system: 'roocode_sparc'
  ```

---

## 4. Configuration (Native Mode)

- Ensure Python environment has all native dependencies
- Place `roocode-config.yaml` in working directory
- Configure SWE-bench for native execution:
  ```bash
  export SWE_BENCH_DOCKER_DISABLED=true
  export SWE_BENCH_NATIVE_MODE=true
  ```
- Validate installation:
  ```bash
  python -m swebench.harness.test_native
  ```

---

## 5. Usage Patterns (roocode Integration)

### 5.1 Running Benchmarks with roocode

- **Lite:** Quick evaluation using roocode SPARC system
- **Full:** Comprehensive benchmarking with roocode completing all SWE tasks

Example commands:
```bash
# Lite benchmark with roocode
python -m swebench.harness.run_evaluation \
  --predictions_path roocode_predictions.jsonl \
  --swe_bench_tasks swe_bench_lite \
  --log_dir ./logs \
  --agent_system roocode_sparc

# Full benchmark with roocode
python -m swebench.harness.run_evaluation \
  --predictions_path roocode_predictions.jsonl \
  --swe_bench_tasks swe_bench_full \
  --log_dir ./logs \
  --agent_system roocode_sparc
```

### 5.2 roocode Task Completion Pipeline

- All patch generation handled by roocode SPARC modes
- Test execution routed through roocode TDD mode
- Code analysis via roocode security and debug modes
- Results aggregation through roocode integration mode

### 5.3 Automation

- Use Makefile or shell scripts for native benchmark orchestration
- Integrate with roocode workflow for task delegation
- Collect logs and metrics through roocode monitoring

---

## 6. Orchestration via SPARC `.roomodes` (Native roocode Integration)

✅ **Updated `.roomodes`** to allow the SPARC orchestrator to:
- Spawn sub-tasks via `new_task` for native SWE-bench workflows:
  - Native SWE-bench install and environment validation
  - sb-cli or equivalent CLI install/config (no Docker)
  - roocode-config.yaml creation/validation
  - Benchmark runs (lite/full) using roocode for all SWE task completions
  - Results collection and reporting through roocode integration mode
- Ensure each sub-task ends with `attempt_completion`
- Enforce modular, <500 line task outputs
- Route all SWE tasks through roocode agentic system (not direct LLM calls)

### 6.1 roocode SPARC Mode Integration

The updated SPARC orchestrator mode now includes:
- **Native execution requirements:** All SWE-bench operations must run natively
- **roocode task routing:** All SWE task completions handled by roocode modes
- **Sub-task delegation patterns:** Clear `new_task` flows for each benchmark phase
- **Validation checkpoints:** Each phase must complete with `attempt_completion`

---

## 7. Best Practices (Native & roocode)

- Keep native Python environment and SWE-bench tools updated
- Never commit API keys or tokens to version control
- Use native execution for better performance and resource efficiency
- Route all SWE tasks through appropriate roocode modes (not direct LLM calls)
- Monitor disk usage for datasets and logs
- Automate benchmark orchestration through roocode SPARC
- Ensure modular task delegation and completion validation

---

## 8. References

- [SWE-bench Main](https://www.swebench.com/SWE-bench/)
- [SWE-bench GitHub](https://github.com/SWE-bench/SWE-bench)
- [sb-cli Docs](https://www.swebench.com/sb-cli/)
- [Native Installation Guide](https://github.com/SWE-bench/SWE-bench#installation)
- [Local Agent Dev Guide](https://website-nine-gules.vercel.app/blog/how-to-setup-swe-agent-local-dev-docker-vscode)

---

## 9. Implementation Phases (roocode SPARC Sub-tasks)

### Phase 1: Environment Setup
- **Sub-task:** `new_task` to `devops` mode for native SWE-bench installation
- **Sub-task:** `new_task` to `code` mode for roocode-config.yaml creation
- **Validation:** Each sub-task ends with `attempt_completion`

### Phase 2: Integration Testing
- **Sub-task:** `new_task` to `tdd` mode for benchmark validation tests
- **Sub-task:** `new_task` to `debug` mode for any installation issues
- **Validation:** Successful native SWE-bench execution without Docker

### Phase 3: Benchmark Orchestration
- **Sub-task:** `new_task` to `sparc` mode for lite benchmark coordination
- **Sub-task:** `new_task` to `sparc` mode for full benchmark coordination
- **Validation:** All SWE tasks completed by roocode, not direct LLM calls

### Phase 4: Results & Documentation
- **Sub-task:** `new_task` to `integration` mode for results aggregation
- **Sub-task:** `new_task` to `docs-writer` mode for benchmark documentation
- **Validation:** Complete benchmarking pipeline with roocode task completion

---

## 10. Success Criteria

✅ SWE-bench installed and running natively (no Docker)
✅ All SWE tasks (patch generation, testing, etc.) completed by roocode modes
✅ SPARC orchestrator can delegate benchmark sub-tasks via `new_task`
✅ Both lite and full benchmarks execute successfully
✅ Results demonstrate roocode SPARC system performance on SWE-bench
✅ All components are modular (<500 lines) and environment-safe
✅ Documentation covers integration points and orchestration patterns