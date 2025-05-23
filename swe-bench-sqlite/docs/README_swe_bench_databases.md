# SWE-bench SQLite Databases

This directory contains tools and databases for working with SWE-bench datasets in SQLite format, supporting both the lite and full versions.

## Files

### Scripts
- `load_swe_bench_to_sqlite.py` - Load SWE-bench Lite from local JSON
- `load_full_swe_bench_to_sqlite.py` - Load full SWE-bench dataset from Hugging Face
- `query_swe_bench_db.py` - Interactive query tool for exploring databases
- `compare_datasets.py` - Compare lite vs full datasets

### Databases
- `swe_bench_lite.db` - SQLite database with 300 tasks (lite version)
- `swe_bench_full.db` - SQLite database with 2,294 tasks (full version)

## Dataset Comparison

| Dataset | Tasks | Top Repository | Completion Status Available |
|---------|-------|----------------|---------------------------|
| **Lite** | 300 | django/django (114) | ✅ Yes (2 completed, 8 failed) |
| **Full** | 2,294 | django/django (850) | ✅ Yes (0 completed, 10 failed) |

The full dataset is **7.6x larger** than the lite version and includes additional fields like `pull_number` and `issue_numbers`.

## Quick Start

### Load Full SWE-bench Dataset
```bash
# Load from Hugging Face (default: princeton-nlp/SWE-bench)
python load_full_swe_bench_to_sqlite.py

# Load specific dataset
python load_full_swe_bench_to_sqlite.py --dataset princeton-nlp/SWE-bench_lite

# Load from local JSON file
python load_full_swe_bench_to_sqlite.py --local --dataset path/to/dataset.json
```

### Query Databases
```bash
# Interactive query tool (works with lite database)
python query_swe_bench_db.py

# Direct SQL on full database
sqlite3 swe_bench_full.db "SELECT repo, COUNT(*) FROM swe_bench_tasks GROUP BY repo;"

# Compare datasets
python compare_datasets.py
```

## Database Schema

### Main Table: `swe_bench_tasks`

| Column | Type | Description | Lite | Full |
|--------|------|-------------|------|------|
| id | INTEGER | Primary key | ✅ | ✅ |
| instance_id | TEXT | Unique task identifier | ✅ | ✅ |
| repo | TEXT | Repository name | ✅ | ✅ |
| base_commit | TEXT | Base commit hash | ✅ | ✅ |
| problem_statement | TEXT | Issue description | ✅ | ✅ |
| hints_text | TEXT | Additional context | ✅ | ✅ |
| created_at | TEXT | Creation timestamp | ✅ | ✅ |
| version | TEXT | Software version | ✅ | ✅ |
| patch | TEXT | Solution patch | ✅ | ✅ |
| test_patch | TEXT | Test cases | ✅ | ✅ |
| fail_to_pass | TEXT | Tests that should pass | ✅ | ✅ |
| pass_to_pass | TEXT | Tests that should continue passing | ✅ | ✅ |
| environment_setup_commit | TEXT | Environment setup | ✅ | ✅ |
| **completion_status** | TEXT | Task completion status | ✅ | ✅ |
| **completion_details** | TEXT | Completion information | ✅ | ✅ |
| created_timestamp | DATETIME | DB record creation | ✅ | ✅ |
| pull_number | INTEGER | PR number | ❌ | ✅ |
| issue_numbers | TEXT | Related issue numbers | ❌ | ✅ |

### Completion Status Values

- `completed` - Task fully completed through all phases
- `failed` - Task attempted but failed with error
- `partial` - Task partially completed (some phases done)
- `not_started` - No results found for this task

## Using for Benchmarking

Both databases contain everything needed for creating benchmark tasks:

### 1. Problem Definition
```sql
SELECT instance_id, repo, problem_statement, base_commit
FROM swe_bench_tasks 
WHERE completion_status = 'not_started'
LIMIT 10;
```

### 2. Solution Verification
```sql
SELECT instance_id, patch, test_patch, fail_to_pass, pass_to_pass
FROM swe_bench_tasks 
WHERE instance_id = 'django__django-11179';
```

### 3. Repository Analysis
```sql
SELECT repo, 
       COUNT(*) as total_tasks,
       SUM(CASE WHEN completion_status = 'completed' THEN 1 ELSE 0 END) as solved,
       AVG(LENGTH(problem_statement)) as avg_problem_length
FROM swe_bench_tasks 
GROUP BY repo 
ORDER BY total_tasks DESC;
```

## Benchmark Creation Workflow

1. **Select Tasks**: Query database for appropriate difficulty/repositories
2. **Extract Context**: Get problem statement, repository info, base commit
3. **Hide Solutions**: Don't expose the `patch` field to the benchmark solver
4. **Setup Environment**: Use `base_commit` and `environment_setup_commit`
5. **Verify Solutions**: Compare against `patch` or run `test_patch` tests
6. **Evaluate**: Use `fail_to_pass` and `pass_to_pass` test specifications

## Advanced Queries

### Repository Difficulty Analysis
```sql
SELECT repo,
       COUNT(*) as tasks,
       AVG(LENGTH(problem_statement)) as avg_complexity,
       AVG(LENGTH(patch)) as avg_solution_size,
       COUNT(CASE WHEN test_patch != '' THEN 1 END) as tasks_with_tests
FROM swe_bench_tasks 
GROUP BY repo 
HAVING tasks >= 10
ORDER BY avg_complexity DESC;
```

### Find Similar Tasks
```sql
SELECT instance_id, repo, 
       substr(problem_statement, 1, 100) as preview
FROM swe_bench_tasks 
WHERE problem_statement LIKE '%authentication%'
   OR problem_statement LIKE '%security%'
ORDER BY repo, instance_id;
```

### Test Coverage Analysis
```sql
SELECT 
    COUNT(*) as total_tasks,
    SUM(CASE WHEN test_patch != '' THEN 1 ELSE 0 END) as with_tests,
    SUM(CASE WHEN fail_to_pass != '' THEN 1 ELSE 0 END) as with_fail_to_pass,
    ROUND(100.0 * SUM(CASE WHEN test_patch != '' THEN 1 ELSE 0 END) / COUNT(*), 1) as test_coverage_pct
FROM swe_bench_tasks;
```

## Available Datasets

The script can load various SWE-bench datasets:

- `princeton-nlp/SWE-bench` - Full dataset (2,294 tasks)
- `princeton-nlp/SWE-bench_lite` - Lite version (300 tasks)
- Local JSON files

## Performance Notes

- Both databases include optimized indexes for common queries
- Full database (~2,294 tasks) loads in under 30 seconds
- Query performance is excellent for analytical workloads
- Use LIMIT clauses when exploring large result sets

## Current Status

### Lite Dataset (300 tasks)
- Completed: 2 (0.7%)
- Failed: 8 (2.7%)  
- Not started: 290 (96.7%)

### Full Dataset (2,294 tasks)
- Completed: 0 (0.0%)
- Failed: 10 (0.4%)
- Not started: 2,284 (99.6%)

## Regenerating Databases

To update with new completion results:

```bash
# Update lite dataset
python load_swe_bench_to_sqlite.py

# Update full dataset
python load_full_swe_bench_to_sqlite.py
```

Both scripts automatically:
1. Check for result files in `swe-bench-workspace/results/`
2. Determine completion status for each task
3. Update completion statistics
4. Maintain database integrity