# SWE-bench Lite SQLite Database

This directory contains scripts and tools for working with the SWE-bench Lite dataset in SQLite format.

## Files

- `load_swe_bench_to_sqlite.py` - Script to load the JSON dataset into SQLite
- `query_swe_bench_db.py` - Interactive query tool for exploring the database
- `swe_bench_lite.db` - The SQLite database file (created after running the loader)

## Database Schema

### Main Table: `swe_bench_tasks`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| instance_id | TEXT | Unique task identifier |
| repo | TEXT | Repository name (e.g., "django/django") |
| base_commit | TEXT | Base commit hash |
| problem_statement | TEXT | Description of the issue to fix |
| hints_text | TEXT | Additional hints or context |
| created_at | TEXT | Task creation timestamp |
| version | TEXT | Software version |
| patch | TEXT | The solution patch |
| test_patch | TEXT | Test cases for the solution |
| fail_to_pass | TEXT | Tests that should pass after fix |
| pass_to_pass | TEXT | Tests that should continue to pass |
| environment_setup_commit | TEXT | Commit for environment setup |
| **completion_status** | TEXT | Task completion status |
| **completion_details** | TEXT | Additional completion information |
| created_timestamp | DATETIME | When record was added to DB |

### Completion Status Values

- `completed` - Task fully completed through all phases
- `failed` - Task attempted but failed with error
- `partial` - Task partially completed (some phases done)
- `not_started` - No results found for this task

### Summary Table: `completion_summary`

| Column | Type | Description |
|--------|------|-------------|
| status | TEXT | Completion status |
| count | INTEGER | Number of tasks with this status |
| percentage | REAL | Percentage of total tasks |
| updated_timestamp | DATETIME | When summary was last updated |

## Usage Examples

### Using the Query Tool

```bash
# Interactive mode
python query_swe_bench_db.py

# Direct SQL query
python query_swe_bench_db.py "SELECT repo, COUNT(*) FROM swe_bench_tasks GROUP BY repo;"
```

### Using SQLite CLI

```bash
# Open database
sqlite3 swe_bench_lite.db

# Basic queries
sqlite3 swe_bench_lite.db "SELECT * FROM completion_summary;"
sqlite3 swe_bench_lite.db "SELECT COUNT(*) FROM swe_bench_tasks WHERE completion_status = 'completed';"
```

## Useful Queries

### 1. Completion Overview
```sql
SELECT * FROM completion_summary;
```

### 2. Tasks by Repository
```sql
SELECT repo, COUNT(*) as task_count, 
       SUM(CASE WHEN completion_status = 'completed' THEN 1 ELSE 0 END) as completed,
       SUM(CASE WHEN completion_status = 'failed' THEN 1 ELSE 0 END) as failed
FROM swe_bench_tasks 
GROUP BY repo 
ORDER BY task_count DESC;
```

### 3. Completed Tasks Details
```sql
SELECT instance_id, repo, completion_details 
FROM swe_bench_tasks 
WHERE completion_status = 'completed';
```

### 4. Failed Tasks with Error Details
```sql
SELECT instance_id, repo, completion_details 
FROM swe_bench_tasks 
WHERE completion_status = 'failed';
```

### 5. Tasks by Software Version
```sql
SELECT version, COUNT(*) as count,
       AVG(CASE WHEN completion_status = 'completed' THEN 1.0 ELSE 0.0 END) as success_rate
FROM swe_bench_tasks 
WHERE version != ''
GROUP BY version 
ORDER BY count DESC;
```

### 6. Search Problem Statements
```sql
SELECT instance_id, repo, substr(problem_statement, 1, 100) as problem_preview
FROM swe_bench_tasks 
WHERE problem_statement LIKE '%authentication%' 
LIMIT 10;
```

### 7. Tasks with Test Patches
```sql
SELECT COUNT(*) as total,
       SUM(CASE WHEN test_patch != '' THEN 1 ELSE 0 END) as with_tests,
       ROUND(100.0 * SUM(CASE WHEN test_patch != '' THEN 1 ELSE 0 END) / COUNT(*), 2) as test_coverage_pct
FROM swe_bench_tasks;
```

## Current Status

As of the last update:
- **Total tasks**: 300
- **Completed**: 2 (0.7%)
- **Failed**: 8 (2.7%) 
- **Not started**: 290 (96.7%)

## Regenerating the Database

To update the database with new results:

```bash
python load_swe_bench_to_sqlite.py
```

This will:
1. Load the JSON dataset
2. Check for result files in `swe-bench-workspace/results/`
3. Determine completion status for each task
4. Create/update the SQLite database
5. Generate completion statistics

## Database Indexes

The following indexes are created for optimal query performance:
- `idx_instance_id` on `instance_id`
- `idx_repo` on `repo` 
- `idx_completion_status` on `completion_status`
- `idx_version` on `version`