#!/usr/bin/env python3
"""
Query script for SWE-bench Lite SQLite database.
"""

import sqlite3
import sys
from typing import List, Tuple


def execute_query(db_path: str, query: str) -> List[Tuple]:
    """Execute a query and return results."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


def print_results(results: List[Tuple], headers: List[str] = None):
    """Print query results in a formatted table."""
    if not results:
        print("No results found.")
        return
    
    if headers:
        print(" | ".join(f"{h:20}" for h in headers))
        print("-" * (len(headers) * 23))
    
    for row in results:
        print(" | ".join(f"{str(item)[:20]:20}" for item in row))


def main():
    """Main function with predefined queries."""
    db_path = "../databases/swe_bench_lite.db"
    
    queries = {
        "1": {
            "name": "Overall completion summary",
            "query": "SELECT * FROM completion_summary ORDER BY count DESC;",
            "headers": ["Status", "Count", "Percentage", "Updated"]
        },
        "2": {
            "name": "Tasks by repository",
            "query": "SELECT repo, COUNT(*) as task_count FROM swe_bench_tasks GROUP BY repo ORDER BY task_count DESC;",
            "headers": ["Repository", "Task Count"]
        },
        "3": {
            "name": "Completed tasks",
            "query": "SELECT instance_id, repo FROM swe_bench_tasks WHERE completion_status = 'completed';",
            "headers": ["Instance ID", "Repository"]
        },
        "4": {
            "name": "Failed tasks with details",
            "query": "SELECT instance_id, repo, completion_details FROM swe_bench_tasks WHERE completion_status = 'failed';",
            "headers": ["Instance ID", "Repository", "Error Details"]
        },
        "5": {
            "name": "Tasks by version",
            "query": "SELECT version, COUNT(*) as count FROM swe_bench_tasks GROUP BY version ORDER BY count DESC;",
            "headers": ["Version", "Count"]
        },
        "6": {
            "name": "Recent tasks (by created_at)",
            "query": "SELECT instance_id, repo, created_at, completion_status FROM swe_bench_tasks WHERE created_at != '' ORDER BY created_at DESC LIMIT 10;",
            "headers": ["Instance ID", "Repository", "Created At", "Status"]
        },
        "7": {
            "name": "Tasks with test patches",
            "query": "SELECT instance_id, repo, CASE WHEN test_patch != '' THEN 'Yes' ELSE 'No' END as has_test_patch FROM swe_bench_tasks LIMIT 10;",
            "headers": ["Instance ID", "Repository", "Has Test Patch"]
        }
    }
    
    if len(sys.argv) > 1:
        # Execute custom query from command line
        custom_query = " ".join(sys.argv[1:])
        print(f"Executing custom query: {custom_query}")
        try:
            results = execute_query(db_path, custom_query)
            print_results(results)
        except Exception as e:
            print(f"Error executing query: {e}")
        return
    
    # Interactive mode
    print("SWE-bench Lite Database Query Tool")
    print("=" * 40)
    print("\nAvailable queries:")
    for key, query_info in queries.items():
        print(f"{key}. {query_info['name']}")
    print("\nOr enter 'custom' to write your own SQL query")
    print("Enter 'quit' to exit")
    
    while True:
        choice = input("\nEnter your choice: ").strip()
        
        if choice.lower() in ['quit', 'exit', 'q']:
            break
        
        if choice.lower() == 'custom':
            custom_query = input("Enter your SQL query: ").strip()
            if custom_query:
                try:
                    results = execute_query(db_path, custom_query)
                    print_results(results)
                except Exception as e:
                    print(f"Error executing query: {e}")
            continue
        
        if choice in queries:
            query_info = queries[choice]
            print(f"\n{query_info['name']}:")
            print("-" * len(query_info['name']))
            try:
                results = execute_query(db_path, query_info['query'])
                print_results(results, query_info.get('headers'))
            except Exception as e:
                print(f"Error executing query: {e}")
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()