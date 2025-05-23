# SWE-bench SQLite Tools

A comprehensive toolkit for working with SWE-bench datasets in SQLite format, supporting both lite and full versions with completion status tracking.

## 📁 Directory Structure

```
swe-bench-sqlite/
├── scripts/           # Python scripts for database operations
├── databases/         # SQLite database files
├── docs/             # Documentation
└── README.md         # This file
```

## 🚀 Quick Start

### 1. Load Datasets

```bash
cd swe-bench-sqlite/scripts

# Load full SWE-bench dataset (2,294 tasks)
python load_full_swe_bench_to_sqlite.py

# Load lite dataset from local JSON (300 tasks)
python load_swe_bench_to_sqlite.py
```

### 2. Query Databases

```bash
# Interactive query tool (lite dataset)
python query_swe_bench_db.py

# Direct SQL queries
sqlite3 ../databases/swe_bench_full.db "SELECT COUNT(*) FROM swe_bench_tasks;"
sqlite3 ../databases/swe_bench_lite.db "SELECT * FROM completion_summary;"
```

### 3. Compare Datasets

```bash
python compare_datasets.py
```

## 📊 Available Datasets

| Dataset | Tasks | Size | Source |
|---------|-------|------|--------|
| **Lite** | 300 | ~15MB | Local JSON |
| **Full** | 2,294 | ~120MB | Hugging Face |

Both databases include:
- ✅ Complete problem statements and solutions
- ✅ Test cases for verification
- ✅ Completion status tracking
- ✅ Repository and commit information

## 📝 Scripts

### Core Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `load_swe_bench_to_sqlite.py` | Load lite dataset | `python load_swe_bench_to_sqlite.py` |
| `load_full_swe_bench_to_sqlite.py` | Load full dataset | `python load_full_swe_bench_to_sqlite.py` |
| `query_swe_bench_db.py` | Interactive queries | `python query_swe_bench_db.py` |
| `compare_datasets.py` | Dataset comparison | `python compare_datasets.py` |
| `benchmark_db_helper.py` | **Benchmark Orchestrator** | `python benchmark_db_helper.py get_task` |

### Benchmark Orchestrator Integration

The `benchmark_db_helper.py` script provides secure database operations for the **Benchmark Orchestrator** mode:

#### Secure Task Selection (No Solution Exposure)
```bash
# Get random available task
python benchmark_db_helper.py get_task

# Get task from specific repository
python benchmark_db_helper.py get_task_repo django/django

# Get completion summary
python benchmark_db_helper.py summary
```

#### Task Management with Step Tracking
```bash
# Start a task (marks as in_progress, records start time)
python benchmark_db_helper.py start_task <instance_id>

# Log steps during task execution
python benchmark_db_helper.py log_step <instance_id> "Step description"

# Update task status after completion
python benchmark_db_helper.py update_status <instance_id> completed "Success details"

# Get detailed task information including step log
python benchmark_db_helper.py task_details <instance_id>

# Get solution ONLY after task completion
python benchmark_db_helper.py get_solution <instance_id>
```

#### Analytics & Reporting
```bash
# Get completion summary
python benchmark_db_helper.py summary

# Get repository statistics with step data
python benchmark_db_helper.py repo_stats

# Get step-based analytics (complexity analysis)
python benchmark_db_helper.py step_analytics
```

#### Step Tracking Features
- **Automatic timing**: Records start and completion timestamps
- **Step counting**: Tracks number of steps taken per task
- **Step logging**: Detailed log of each step with timestamps
- **Complexity analysis**: Categorizes tasks as simple (1-5 steps), medium (6-15 steps), or complex (16+ steps)
- **Duration tracking**: Calculates time spent on each task
- **Performance metrics**: Average steps per task, completion rates, duration analytics

### Script Options

#### Load Full Dataset
```bash
python load_full_swe_bench_to_sqlite.py --help

Options:
  --dataset         Dataset name or path (default: princeton-nlp/SWE-bench)
  --output          Output database file
  --results-dir     Results directory for completion status
  --local           Load from local JSON instead of Hugging Face
```

#### Examples
```bash
# Load specific dataset
python load_full_swe_bench_to_sqlite.py --dataset princeton-nlp/SWE-bench_lite

# Load from local file
python load_full_swe_bench_to_sqlite.py --local --dataset /path/to/dataset.json

# Custom output location
python load_full_swe_bench_to_sqlite.py --output /path/to/my_database.db
```

## 🗄️ Database Schema

### Main Table: `swe_bench_tasks`

| Column | Type | Description |
|--------|------|-------------|
| instance_id | TEXT | Unique task identifier |
| repo | TEXT | Repository (e.g., "django/django") |
| problem_statement | TEXT | Issue description |
| patch | TEXT | Solution code |
| test_patch | TEXT | Test cases |
| completion_status | TEXT | 'completed', 'failed', 'partial', 'not_started' |
| completion_details | TEXT | Additional status information |

[See full schema in docs/](docs/README_swe_bench_databases.md)

## 🎯 Benchmark Creation

Perfect for creating coding benchmarks:

1. **Extract Problems**: Query database for problem statements
2. **Hide Solutions**: Don't expose the `patch` field
3. **Verify Results**: Compare solutions against stored patches
4. **Run Tests**: Use `test_patch` for verification

### Example Benchmark Query
```sql
SELECT instance_id, repo, problem_statement, base_commit
FROM swe_bench_tasks 
WHERE completion_status = 'not_started'
  AND LENGTH(problem_statement) BETWEEN 200 AND 1000
ORDER BY repo, instance_id
LIMIT 50;
```

## 📚 Documentation

- [Complete Database Documentation](docs/README_swe_bench_databases.md)
- [Original Lite Database Docs](docs/README_database.md)

## 🛠️ Development

### Requirements
- Python 3.8+
- sqlite3
- datasets (for Hugging Face loading)

### Installation
```bash
pip install datasets  # Optional, for loading from Hugging Face
```

### File Paths
All scripts use relative paths from the `scripts/` directory:
- Databases: `../databases/`
- Documentation: `../docs/`
- SWE-bench workspace: `../swe-bench-workspace/`

## 📈 Current Status

### Lite Dataset (300 tasks)
- Completed: 2 (0.7%)
- Failed: 8 (2.7%)
- Not started: 290 (96.7%)

### Full Dataset (2,294 tasks)  
- Completed: 0 (0.0%)
- Failed: 10 (0.4%)
- Not started: 2,284 (99.6%)

## 🔄 Updating Results

To refresh completion status with new results:

```bash
cd scripts/
python load_swe_bench_to_sqlite.py      # Update lite
python load_full_swe_bench_to_sqlite.py  # Update full
```

Both scripts automatically:
- Scan for new result files
- Update completion status  
- Regenerate statistics
- Preserve existing data

---

**Note**: Run all scripts from the `scripts/` directory to ensure correct relative paths.