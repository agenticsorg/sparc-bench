# Benchmark Orchestrator Tool Usage Guidelines

## Primary Tool: new_task

The `new_task` tool is the cornerstone of benchmark orchestration. It delegates SWE-bench problems to appropriate roocode SPARC modes.

### Usage Pattern
```xml
<new_task>
<mode>target_mode</mode>
<message>formatted_problem_statement</message>
</new_task>
```

### Mode Selection Guidelines

| Problem Type        | Target Mode       | Criteria                                                     |
| ------------------- | ----------------- | ------------------------------------------------------------ |
| Code Implementation | `code`            | General feature implementation, algorithm fixes              |
| Test Issues         | `tdd`             | Test failures, coverage problems, testing frameworks         |
| Bug Analysis        | `debug`           | Runtime errors, logic bugs, performance issues               |
| Security Problems   | `security-review` | Auth issues, input validation, security vulnerabilities      |
| Integration Issues  | `integration`     | API integration, service communication, dependency conflicts |

### Message Formatting Template

```markdown
# SWE-bench Task: {instance_id}

## Repository: {repo}

## Problem Statement
{detailed_problem_description}

## Implementation Hints
{hints_and_guidance}

## Your Task
You are the {mode} mode in the roocode SPARC system. Please solve this software engineering issue by:

1. **Analysis**: Understand the problem and identify the root cause
2. **Investigation**: Locate the relevant files and problematic code  
3. **Solution**: Implement a proper fix for the issue
4. **Verification**: Ensure your solution works and doesn't break existing functionality

## Requirements
- Provide working code that fixes the described issue
- Follow the repository's coding standards and patterns
- Include appropriate error handling
- Ensure backward compatibility
- Write clear, maintainable code

Begin your implementation now.
```

## Secondary Tools

### execute_command
Use for environment validation, dataset operations, and system checks.
CRITICAL: All commands must be executed from the current workspace root, which VSCode calls `${workspaceFolder}`.
ALWAYS set the cwd for `execute_command` to the workspace root.

```xml
<execute_command>
<command>python3 validate-swe-setup.py --check-all</command>
</execute_command>
```

**Common Commands:**
- Environment validation: `python3 validate-setup.py`
- Dataset loading: `python3 load-swe-dataset.py --lite`
- Result validation: `python3 validate-results.py --summary`
- System health: `python3 check-system-health.py`

### apply_diff
Use for result processing, report generation, and configuration updates.

```xml
<apply_diff>
<path>benchmark-results/summary.json</path>
<diff>
  "total_tasks": 100,
  "completed": 95,
  "success_rate": "95%"
</diff>
</apply_diff>
```

**Use Cases:**
- Update benchmark summaries
- Modify configuration files
- Process result aggregations
- Generate report sections

### read_file
Use to examine existing results, configurations, and task data.

```xml
<read_file>
<path>swe-bench-workspace/results/task_summary.json</path>
</read_file>
```

**Common File Types:**
- Task results: `results/{task_id}/results.json`
- Configuration files: `config/benchmark-config.yaml`
- Dataset files: `datasets/swe-bench-lite.json`
- Log files: `logs/orchestration.log`

### write_to_file
Use for creating new reports, summaries, and documentation.

```xml
<write_to_file>
<path>benchmark-results/final-report.md</path>
<content>
# SWE-bench Benchmark Report
## Executive Summary
...