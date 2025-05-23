#!/usr/bin/env python3
"""
Load the full SWE-bench dataset from Hugging Face and convert to SQLite database.

This script downloads and processes the complete SWE-bench dataset (not just lite version)
and stores it in a SQLite database with completion status tracking.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

try:
    from datasets import load_dataset
    HF_DATASETS_AVAILABLE = True
except ImportError:
    HF_DATASETS_AVAILABLE = False
    print("Warning: datasets library not available. Install with: pip install datasets")


def create_database_schema(conn: sqlite3.Connection) -> None:
    """Create the database schema with indexes."""
    cursor = conn.cursor()
    
    # Main tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS swe_bench_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instance_id TEXT UNIQUE NOT NULL,
            repo TEXT NOT NULL,
            base_commit TEXT,
            problem_statement TEXT,
            hints_text TEXT,
            created_at TEXT,
            version TEXT,
            patch TEXT,
            test_patch TEXT,
            fail_to_pass TEXT,
            pass_to_pass TEXT,
            environment_setup_commit TEXT,
            completion_status TEXT DEFAULT 'not_started',
            completion_details TEXT DEFAULT '',
            created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Additional fields from full dataset
            pull_number INTEGER,
            issue_numbers TEXT
        )
    ''')
    
    # Completion summary table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS completion_summary (
            status TEXT PRIMARY KEY,
            count INTEGER,
            percentage REAL,
            updated_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_instance_id ON swe_bench_tasks(instance_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_repo ON swe_bench_tasks(repo)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_completion_status ON swe_bench_tasks(completion_status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_version ON swe_bench_tasks(version)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pull_number ON swe_bench_tasks(pull_number)')
    
    conn.commit()


def determine_completion_status(instance_id: str, results_dir: str = "swe-bench-workspace/results") -> tuple[str, str]:
    """
    Determine the completion status of a task by checking result files.
    
    Returns:
        tuple: (status, details) where status is one of:
            - 'completed': Task fully completed
            - 'failed': Task attempted but failed  
            - 'partial': Task partially completed
            - 'not_started': No results found
    """
    task_dir = Path(results_dir) / instance_id
    
    if not task_dir.exists():
        return 'not_started', 'No result directory found'
    
    # Check for final result file
    final_result_file = task_dir / 'swe_result_final.json'
    if final_result_file.exists():
        try:
            with open(final_result_file, 'r') as f:
                final_data = json.load(f)
                if final_data.get('status') == 'completed':
                    return 'completed', 'All phases completed successfully'
                else:
                    return 'failed', f"Final status: {final_data.get('status', 'unknown')}"
        except Exception as e:
            return 'failed', f'Error reading final result: {str(e)}'
    
    # Check for individual phase results
    phase_files = [
        'spec-pseudocode_result.json',
        'architect_result.json', 
        'code_result.json',
        'tdd_result.json',
        'debug_result.json',
        'security-review_result.json',
        'docs-writer_result.json',
        'integration_result.json'
    ]
    
    completed_phases = 0
    last_error = None
    
    for phase_file in phase_files:
        phase_path = task_dir / phase_file
        if phase_path.exists():
            try:
                with open(phase_path, 'r') as f:
                    phase_data = json.load(f)
                    if phase_data.get('status') == 'completed':
                        completed_phases += 1
                    elif 'error' in phase_data or 'failed' in str(phase_data.get('status', '')):
                        last_error = phase_data.get('error', phase_data.get('status', 'Unknown error'))
            except Exception as e:
                last_error = f'Error reading {phase_file}: {str(e)}'
    
    if completed_phases == len(phase_files):
        return 'completed', 'All 8 phases completed'
    elif completed_phases > 0:
        return 'partial', f'Completed {completed_phases}/{len(phase_files)} phases'
    elif last_error:
        return 'failed', f'Failed: {last_error}'
    else:
        return 'not_started', 'No valid phase results found'


def load_from_huggingface(dataset_name: str = "princeton-nlp/SWE-bench") -> List[Dict[str, Any]]:
    """Load SWE-bench dataset from Hugging Face."""
    if not HF_DATASETS_AVAILABLE:
        raise ImportError("datasets library is required. Install with: pip install datasets")
    
    print(f"Loading {dataset_name} from Hugging Face...")
    dataset = load_dataset(dataset_name)
    
    # Get the test split (main dataset)
    if 'test' in dataset:
        data = dataset['test']
    elif 'train' in dataset:
        data = dataset['train']
    else:
        # Use the first available split
        split_name = list(dataset.keys())[0]
        data = dataset[split_name]
        print(f"Using split: {split_name}")
    
    print(f"Loaded {len(data)} tasks from {dataset_name}")
    return list(data)


def load_from_local_json(json_path: str) -> List[Dict[str, Any]]:
    """Load dataset from local JSON file."""
    print(f"Loading dataset from {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} tasks from local file")
    return data


def insert_task_data(conn: sqlite3.Connection, tasks: List[Dict[str, Any]], results_dir: str) -> None:
    """Insert task data into the database."""
    cursor = conn.cursor()
    
    for i, task in enumerate(tasks):
        if i % 100 == 0:
            print(f"Processing task {i+1}/{len(tasks)}")
        
        instance_id = task.get('instance_id', '')
        completion_status, completion_details = determine_completion_status(instance_id, results_dir)
        
        # Handle both string and list formats for test cases
        fail_to_pass = task.get('fail_to_pass', task.get('FAIL_TO_PASS', ''))
        pass_to_pass = task.get('pass_to_pass', task.get('PASS_TO_PASS', ''))
        
        if isinstance(fail_to_pass, list):
            fail_to_pass = json.dumps(fail_to_pass)
        if isinstance(pass_to_pass, list):
            pass_to_pass = json.dumps(pass_to_pass)
        
        # Handle issue_numbers (can be list or string)
        issue_numbers = task.get('issue_numbers', '')
        if isinstance(issue_numbers, list):
            issue_numbers = json.dumps(issue_numbers)
        
        cursor.execute('''
            INSERT OR REPLACE INTO swe_bench_tasks (
                instance_id, repo, base_commit, problem_statement, hints_text,
                created_at, version, patch, test_patch, fail_to_pass, pass_to_pass,
                environment_setup_commit, completion_status, completion_details,
                pull_number, issue_numbers
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            instance_id,
            task.get('repo', ''),
            task.get('base_commit', ''),
            task.get('problem_statement', ''),
            task.get('hints_text', ''),
            task.get('created_at', ''),
            task.get('version', ''),
            task.get('patch', ''),
            task.get('test_patch', ''),
            fail_to_pass,
            pass_to_pass,
            task.get('environment_setup_commit', ''),
            completion_status,
            completion_details,
            task.get('pull_number', None),
            issue_numbers
        ))
    
    conn.commit()
    print(f"Inserted {len(tasks)} tasks into database")


def update_completion_summary(conn: sqlite3.Connection) -> None:
    """Update the completion summary table."""
    cursor = conn.cursor()
    
    # Get completion statistics
    cursor.execute('''
        SELECT completion_status, COUNT(*) as count
        FROM swe_bench_tasks
        GROUP BY completion_status
    ''')
    
    status_counts = dict(cursor.fetchall())
    total_tasks = sum(status_counts.values())
    
    # Clear existing summary
    cursor.execute('DELETE FROM completion_summary')
    
    # Insert updated summary
    current_time = datetime.now().isoformat()
    for status, count in status_counts.items():
        percentage = (count / total_tasks) * 100 if total_tasks > 0 else 0
        cursor.execute('''
            INSERT INTO completion_summary (status, count, percentage, updated_timestamp)
            VALUES (?, ?, ?, ?)
        ''', (status, count, percentage, current_time))
    
    conn.commit()
    
    print("\nCompletion Summary:")
    for status, count in status_counts.items():
        percentage = (count / total_tasks) * 100 if total_tasks > 0 else 0
        print(f"  {status}: {count} ({percentage:.1f}%)")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Load SWE-bench dataset to SQLite")
    parser.add_argument(
        '--dataset', 
        default='princeton-nlp/SWE-bench',
        help='Hugging Face dataset name or local JSON file path'
    )
    parser.add_argument(
        '--output',
        default='../databases/swe_bench_full.db',
        help='Output SQLite database file'
    )
    parser.add_argument(
        '--results-dir',
        default='../swe-bench-workspace/results',
        help='Directory containing task results'
    )
    parser.add_argument(
        '--local',
        action='store_true',
        help='Load from local JSON file instead of Hugging Face'
    )
    
    args = parser.parse_args()
    
    # Load the dataset
    try:
        if args.local or args.dataset.endswith('.json'):
            tasks = load_from_local_json(args.dataset)
        else:
            tasks = load_from_huggingface(args.dataset)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        print("Available datasets:")
        print("  - princeton-nlp/SWE-bench (full dataset)")
        print("  - princeton-nlp/SWE-bench_lite (lite version)")
        print("  - Local JSON file path")
        return
    
    # Create database
    print(f"\nCreating SQLite database: {args.output}")
    conn = sqlite3.connect(args.output)
    
    try:
        create_database_schema(conn)
        insert_task_data(conn, tasks, args.results_dir)
        update_completion_summary(conn)
        
        print(f"\nDatabase created successfully: {args.output}")
        print(f"Total tasks: {len(tasks)}")
        
    except Exception as e:
        print(f"Error creating database: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()