#!/usr/bin/env python3
"""
Load SWE-bench Lite dataset into SQLite database with completion status.
"""

import json
import sqlite3
import os
from pathlib import Path
from typing import Dict, Any, Optional


def get_completion_status(instance_id: str, results_dir: str) -> tuple[str, Optional[str]]:
    """
    Determine completion status for a task by checking result files.
    
    Returns:
        tuple: (status, details) where status is 'completed', 'failed', 'partial', or 'not_started'
    """
    task_results_dir = Path(results_dir) / instance_id
    
    if not task_results_dir.exists():
        return 'not_started', None
    
    # Check if final result file exists
    final_result_file = task_results_dir / 'swe_result_final.json'
    if final_result_file.exists():
        try:
            with open(final_result_file, 'r') as f:
                final_result = json.load(f)
                status = final_result.get('task_summary', {}).get('status', 'unknown')
                phases_executed = final_result.get('task_summary', {}).get('phases_executed', [])
                total_phases = final_result.get('task_summary', {}).get('total_phases', 0)
                
                if status == 'completed':
                    return 'completed', f"All {len(phases_executed)} phases completed"
                elif status == 'failed':
                    error = final_result.get('task_summary', {}).get('error', 'Unknown error')
                    return 'failed', f"Failed: {error}"
                else:
                    return 'partial', f"Status: {status}, {len(phases_executed)}/{total_phases} phases"
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    
    # Check for individual phase results if no final result
    phase_files = list(task_results_dir.glob('*_result.json'))
    if phase_files:
        return 'partial', f"Has {len(phase_files)} phase results"
    
    # Check for any result files
    any_files = list(task_results_dir.glob('*.json'))
    if any_files:
        return 'partial', f"Has {len(any_files)} result files"
    
    return 'not_started', None


def create_database(db_path: str, json_path: str, results_dir: str) -> None:
    """
    Create SQLite database from SWE-bench Lite JSON file.
    """
    # Load JSON data
    print(f"Loading data from {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} tasks")
    
    # Create database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create main table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS swe_bench_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instance_id TEXT UNIQUE NOT NULL,
            repo TEXT NOT NULL,
            base_commit TEXT NOT NULL,
            problem_statement TEXT NOT NULL,
            hints_text TEXT,
            created_at TEXT,
            version TEXT,
            patch TEXT,
            test_patch TEXT,
            fail_to_pass TEXT,
            pass_to_pass TEXT,
            environment_setup_commit TEXT,
            completion_status TEXT,
            completion_details TEXT,
            created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for better query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_instance_id ON swe_bench_tasks(instance_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_repo ON swe_bench_tasks(repo)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_completion_status ON swe_bench_tasks(completion_status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_version ON swe_bench_tasks(version)')
    
    # Insert data
    print("Inserting data into database...")
    completed_count = 0
    failed_count = 0
    partial_count = 0
    not_started_count = 0
    
    for i, task in enumerate(data):
        if i % 100 == 0:
            print(f"Processing task {i+1}/{len(data)}")
        
        # Get completion status
        status, details = get_completion_status(task['instance_id'], results_dir)
        
        if status == 'completed':
            completed_count += 1
        elif status == 'failed':
            failed_count += 1
        elif status == 'partial':
            partial_count += 1
        else:
            not_started_count += 1
        
        # Extract fields that might be named differently
        fail_to_pass = task.get('FAIL_TO_PASS', task.get('fail_to_pass', ''))
        pass_to_pass = task.get('PASS_TO_PASS', task.get('pass_to_pass', ''))
        
        cursor.execute('''
            INSERT OR REPLACE INTO swe_bench_tasks (
                instance_id, repo, base_commit, problem_statement, hints_text,
                created_at, version, patch, test_patch, fail_to_pass, pass_to_pass,
                environment_setup_commit, completion_status, completion_details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task['instance_id'],
            task['repo'],
            task['base_commit'],
            task['problem_statement'],
            task.get('hints_text', ''),
            task.get('created_at', ''),
            task.get('version', ''),
            task.get('patch', ''),
            task.get('test_patch', ''),
            str(fail_to_pass) if fail_to_pass else '',
            str(pass_to_pass) if pass_to_pass else '',
            task.get('environment_setup_commit', ''),
            status,
            details
        ))
    
    # Create summary table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS completion_summary (
            status TEXT PRIMARY KEY,
            count INTEGER,
            percentage REAL,
            updated_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    total_tasks = len(data)
    summary_data = [
        ('completed', completed_count, (completed_count / total_tasks) * 100),
        ('failed', failed_count, (failed_count / total_tasks) * 100),
        ('partial', partial_count, (partial_count / total_tasks) * 100),
        ('not_started', not_started_count, (not_started_count / total_tasks) * 100)
    ]
    
    cursor.execute('DELETE FROM completion_summary')
    cursor.executemany('''
        INSERT INTO completion_summary (status, count, percentage)
        VALUES (?, ?, ?)
    ''', summary_data)
    
    # Commit changes
    conn.commit()
    
    # Print summary
    print(f"\nDatabase created successfully at: {db_path}")
    print(f"Total tasks: {total_tasks}")
    print(f"Completed: {completed_count} ({(completed_count/total_tasks)*100:.1f}%)")
    print(f"Failed: {failed_count} ({(failed_count/total_tasks)*100:.1f}%)")
    print(f"Partial: {partial_count} ({(partial_count/total_tasks)*100:.1f}%)")
    print(f"Not started: {not_started_count} ({(not_started_count/total_tasks)*100:.1f}%)")
    
    # Show some sample queries
    print("\nSample queries you can run:")
    print("1. SELECT COUNT(*) FROM swe_bench_tasks WHERE completion_status = 'completed';")
    print("2. SELECT repo, COUNT(*) as task_count FROM swe_bench_tasks GROUP BY repo ORDER BY task_count DESC;")
    print("3. SELECT completion_status, COUNT(*) FROM swe_bench_tasks GROUP BY completion_status;")
    print("4. SELECT * FROM completion_summary;")
    print("5. SELECT instance_id, repo, completion_status FROM swe_bench_tasks WHERE completion_status = 'failed' LIMIT 10;")
    
    conn.close()


def main():
    """Main function to run the script."""
    # Define paths
    json_path = "../swe-bench-workspace/datasets/swe_bench_lite.json"
    results_dir = "../swe-bench-workspace/results"
    db_path = "../databases/swe_bench_lite.db"
    
    # Check if input files exist
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found at {json_path}")
        return
    
    if not os.path.exists(results_dir):
        print(f"Warning: Results directory not found at {results_dir}")
        print("Will create database without completion status information")
        results_dir = ""
    
    # Create database
    create_database(db_path, json_path, results_dir)


if __name__ == "__main__":
    main()