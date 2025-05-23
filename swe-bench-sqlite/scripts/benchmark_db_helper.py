#!/usr/bin/env python3
"""
Benchmark Orchestrator Database Helper

Provides secure database operations for SWE-bench task management.
Ensures solutions are never exposed during active problem solving.
"""

import sqlite3
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class BenchmarkDBHelper:
    """Helper class for benchmark orchestrator database operations."""
    
    def __init__(self, db_path: str = "../databases/swe_bench_full.db"):
        """Initialize with database path."""
        self.db_path = db_path
        if not Path(db_path).exists():
            # Fallback to lite database
            self.db_path = "../databases/swe_bench_lite.db"
            if not Path(self.db_path).exists():
                raise FileNotFoundError(f"No SWE-bench database found at {db_path} or fallback path")
    
    def get_available_task(self, exclude_repos: List[str] = None) -> Optional[Dict]:
        """
        Get a random available task without revealing the solution.
        
        Args:
            exclude_repos: List of repository names to exclude
            
        Returns:
            Dict with task details (NO solution fields) or None if no tasks available
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query with optional repository exclusions
        where_clause = "completion_status = 'not_started'"
        params = []
        
        if exclude_repos:
            placeholders = ','.join(['?' for _ in exclude_repos])
            where_clause += f" AND repo NOT IN ({placeholders})"
            params.extend(exclude_repos)
        
        query = f"""
        SELECT instance_id, repo, problem_statement, hints_text, 
               fail_to_pass, pass_to_pass, base_commit, version
        FROM swe_bench_tasks 
        WHERE {where_clause}
        ORDER BY RANDOM() LIMIT 1;
        """
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        return {
            'instance_id': result[0],
            'repo': result[1],
            'problem_statement': result[2],
            'hints_text': result[3] or '',
            'fail_to_pass': result[4] or '',
            'pass_to_pass': result[5] or '',
            'base_commit': result[6] or '',
            'version': result[7] or ''
        }
    
    def get_tasks_by_repo(self, repo: str, limit: int = 5) -> List[Dict]:
        """Get available tasks for a specific repository."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT instance_id, repo, problem_statement, hints_text, 
               fail_to_pass, pass_to_pass, base_commit, version
        FROM swe_bench_tasks 
        WHERE completion_status = 'not_started' AND repo = ?
        ORDER BY RANDOM() LIMIT ?;
        """
        
        cursor.execute(query, (repo, limit))
        results = cursor.fetchall()
        conn.close()
        
        tasks = []
        for result in results:
            tasks.append({
                'instance_id': result[0],
                'repo': result[1],
                'problem_statement': result[2],
                'hints_text': result[3] or '',
                'fail_to_pass': result[4] or '',
                'pass_to_pass': result[5] or '',
                'base_commit': result[6] or '',
                'version': result[7] or ''
            })
        
        return tasks
    
    def start_task(self, instance_id: str) -> bool:
        """
        Mark task as started and record start time.
        
        Args:
            instance_id: Task identifier
            
        Returns:
            True if update successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE swe_bench_tasks
                SET completion_status = 'in_progress',
                    started_at = CURRENT_TIMESTAMP,
                    steps_taken = 0,
                    step_log = ''
                WHERE instance_id = ?
            """, (instance_id,))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            return success
            
        except Exception as e:
            conn.close()
            raise Exception(f"Failed to start task: {e}")
    
    def log_step(self, instance_id: str, step_description: str) -> bool:
        """
        Log a step taken during task execution.
        
        Args:
            instance_id: Task identifier
            step_description: Description of the step taken
            
        Returns:
            True if update successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get current step count and log
            cursor.execute("""
                SELECT steps_taken, step_log FROM swe_bench_tasks
                WHERE instance_id = ?
            """, (instance_id,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False
            
            current_steps, current_log = result
            new_steps = (current_steps or 0) + 1
            
            # Create step entry with timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            step_entry = f"[{timestamp}] Step {new_steps}: {step_description}"
            
            # Append to existing log
            new_log = current_log + "\n" + step_entry if current_log else step_entry
            
            cursor.execute("""
                UPDATE swe_bench_tasks
                SET steps_taken = ?, step_log = ?
                WHERE instance_id = ?
            """, (new_steps, new_log, instance_id))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            return success
            
        except Exception as e:
            conn.close()
            raise Exception(f"Failed to log step: {e}")

    def update_task_status(self, instance_id: str, status: str, details: str = '') -> bool:
        """
        Update task completion status.
        
        Args:
            instance_id: Task identifier
            status: 'completed', 'failed', 'partial'
            details: Additional details about completion
            
        Returns:
            True if update successful, False otherwise
        """
        valid_statuses = ['completed', 'failed', 'partial', 'not_started', 'in_progress']
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Set completed_at timestamp for completed/failed status
            if status in ['completed', 'failed']:
                cursor.execute("""
                    UPDATE swe_bench_tasks
                    SET completion_status = ?, completion_details = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE instance_id = ?
                """, (status, details, instance_id))
            else:
                cursor.execute("""
                    UPDATE swe_bench_tasks
                    SET completion_status = ?, completion_details = ?
                    WHERE instance_id = ?
                """, (status, details, instance_id))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            return success
            
        except Exception as e:
            conn.close()
            raise Exception(f"Failed to update task status: {e}")
    
    def get_solution_after_completion(self, instance_id: str) -> Optional[Dict]:
        """
        Get solution details ONLY for completed tasks.
        
        Args:
            instance_id: Task identifier
            
        Returns:
            Dict with solution details or None if task not completed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT instance_id, patch, test_patch, completion_status
        FROM swe_bench_tasks 
        WHERE instance_id = ? AND completion_status = 'completed';
        """
        
        cursor.execute(query, (instance_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        return {
            'instance_id': result[0],
            'patch': result[1],
            'test_patch': result[2],
            'completion_status': result[3]
        }
    
    def get_completion_summary(self) -> Dict:
        """Get overall completion statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT completion_status, COUNT(*) as count
            FROM swe_bench_tasks
            GROUP BY completion_status
        """)
        
        results = cursor.fetchall()
        total = sum(count for _, count in results)
        
        summary = {'total_tasks': total}
        for status, count in results:
            percentage = (count / total * 100) if total > 0 else 0
            summary[status] = {'count': count, 'percentage': round(percentage, 2)}
        
        conn.close()
        return summary
    
    def get_repo_statistics(self) -> List[Dict]:
        """Get completion statistics by repository."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT repo,
               COUNT(*) as total,
               SUM(CASE WHEN completion_status = 'completed' THEN 1 ELSE 0 END) as completed,
               SUM(CASE WHEN completion_status = 'failed' THEN 1 ELSE 0 END) as failed,
               SUM(CASE WHEN completion_status = 'partial' THEN 1 ELSE 0 END) as partial,
               SUM(CASE WHEN completion_status = 'not_started' THEN 1 ELSE 0 END) as not_started,
               SUM(CASE WHEN completion_status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
               AVG(CASE WHEN steps_taken > 0 THEN steps_taken ELSE NULL END) as avg_steps,
               AVG(CASE WHEN started_at IS NOT NULL AND completed_at IS NOT NULL
                        THEN (julianday(completed_at) - julianday(started_at)) * 24 * 60
                        ELSE NULL END) as avg_minutes
        FROM swe_bench_tasks
        GROUP BY repo
        ORDER BY total DESC;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        stats = []
        for result in results:
            repo, total, completed, failed, partial, not_started, in_progress, avg_steps, avg_minutes = result
            completion_rate = (completed / total * 100) if total > 0 else 0
            
            stats.append({
                'repo': repo,
                'total': total,
                'completed': completed,
                'failed': failed,
                'partial': partial,
                'not_started': not_started,
                'in_progress': in_progress,
                'completion_rate': round(completion_rate, 2),
                'avg_steps': round(avg_steps, 1) if avg_steps else None,
                'avg_minutes': round(avg_minutes, 1) if avg_minutes else None
            })
        
        return stats
    
    def get_step_analytics(self) -> Dict:
        """Get step-based analytics for completed tasks."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT
            COUNT(*) as total_completed,
            AVG(steps_taken) as avg_steps,
            MIN(steps_taken) as min_steps,
            MAX(steps_taken) as max_steps,
            AVG(CASE WHEN started_at IS NOT NULL AND completed_at IS NOT NULL
                     THEN (julianday(completed_at) - julianday(started_at)) * 24 * 60
                     ELSE NULL END) as avg_duration_minutes,
            COUNT(CASE WHEN steps_taken <= 5 THEN 1 END) as simple_tasks,
            COUNT(CASE WHEN steps_taken BETWEEN 6 AND 15 THEN 1 END) as medium_tasks,
            COUNT(CASE WHEN steps_taken > 15 THEN 1 END) as complex_tasks
        FROM swe_bench_tasks
        WHERE completion_status = 'completed' AND steps_taken > 0;
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return {"message": "No completed tasks with step data found"}
        
        total_completed, avg_steps, min_steps, max_steps, avg_duration, simple, medium, complex = result
        
        return {
            'total_completed': total_completed,
            'avg_steps': round(avg_steps, 2) if avg_steps else 0,
            'min_steps': min_steps or 0,
            'max_steps': max_steps or 0,
            'avg_duration_minutes': round(avg_duration, 2) if avg_duration else None,
            'task_complexity': {
                'simple_tasks_1_5_steps': simple,
                'medium_tasks_6_15_steps': medium,
                'complex_tasks_16_plus_steps': complex
            }
        }
    
    def get_task_details(self, instance_id: str) -> Optional[Dict]:
        """Get detailed task information including step log."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT instance_id, repo, completion_status, steps_taken,
               started_at, completed_at, step_log, completion_details
        FROM swe_bench_tasks
        WHERE instance_id = ?;
        """
        
        cursor.execute(query, (instance_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        instance_id, repo, status, steps, started_at, completed_at, step_log, details = result
        
        # Calculate duration if both timestamps exist
        duration_minutes = None
        if started_at and completed_at:
            try:
                from datetime import datetime
                start = datetime.fromisoformat(started_at.replace('Z', '+00:00') if 'Z' in started_at else started_at)
                end = datetime.fromisoformat(completed_at.replace('Z', '+00:00') if 'Z' in completed_at else completed_at)
                duration_minutes = round((end - start).total_seconds() / 60, 2)
            except:
                pass
        
        return {
            'instance_id': instance_id,
            'repo': repo,
            'completion_status': status,
            'steps_taken': steps or 0,
            'started_at': started_at,
            'completed_at': completed_at,
            'duration_minutes': duration_minutes,
            'step_log': step_log.split('\n') if step_log else [],
            'completion_details': details
        }


def main():
    """Command line interface for benchmark database operations."""
    if len(sys.argv) < 2:
        print("Usage: python benchmark_db_helper.py <command> [args...]")
        print("\nTask Management:")
        print("  get_task                    - Get random available task")
        print("  get_task_repo <repo>        - Get task from specific repository")
        print("  start_task <id>             - Mark task as started")
        print("  log_step <id> <description> - Log a step taken during task execution")
        print("  update_status <id> <status> [details] - Update task completion status")
        print("  get_solution <id>           - Get solution for completed task")
        print("  task_details <id>           - Get detailed task info including step log")
        print("\nAnalytics:")
        print("  summary                     - Get completion summary")
        print("  repo_stats                  - Get repository statistics")
        print("  step_analytics              - Get step-based analytics")
        print("\nStatus values: not_started, in_progress, completed, failed, partial")
        return
    
    helper = BenchmarkDBHelper()
    command = sys.argv[1]
    
    try:
        if command == "get_task":
            task = helper.get_available_task()
            if task:
                print(json.dumps(task, indent=2))
            else:
                print("No available tasks found")
        
        elif command == "get_task_repo":
            if len(sys.argv) < 3:
                print("Usage: get_task_repo <repository>")
                return
            repo = sys.argv[2]
            tasks = helper.get_tasks_by_repo(repo, 1)
            if tasks:
                print(json.dumps(tasks[0], indent=2))
            else:
                print(f"No available tasks found for repository: {repo}")
        
        elif command == "start_task":
            if len(sys.argv) < 3:
                print("Usage: start_task <instance_id>")
                return
            instance_id = sys.argv[2]
            success = helper.start_task(instance_id)
            if success:
                print(f"✅ Started task {instance_id}")
            else:
                print(f"❌ Failed to start task {instance_id}")
        
        elif command == "log_step":
            if len(sys.argv) < 4:
                print("Usage: log_step <instance_id> <step_description>")
                return
            instance_id = sys.argv[2]
            step_description = ' '.join(sys.argv[3:])  # Join all remaining args as description
            success = helper.log_step(instance_id, step_description)
            if success:
                print(f"✅ Logged step for {instance_id}: {step_description}")
            else:
                print(f"❌ Failed to log step for {instance_id}")
        
        elif command == "update_status":
            if len(sys.argv) < 4:
                print("Usage: update_status <instance_id> <status> [details]")
                return
            instance_id = sys.argv[2]
            status = sys.argv[3]
            details = sys.argv[4] if len(sys.argv) > 4 else ''
            
            success = helper.update_task_status(instance_id, status, details)
            if success:
                print(f"✅ Updated {instance_id} to {status}")
            else:
                print(f"❌ Failed to update {instance_id}")
        
        elif command == "get_solution":
            if len(sys.argv) < 3:
                print("Usage: get_solution <instance_id>")
                return
            instance_id = sys.argv[2]
            solution = helper.get_solution_after_completion(instance_id)
            if solution:
                print(json.dumps(solution, indent=2))
            else:
                print(f"No solution available for {instance_id} (task may not be completed)")
        
        elif command == "task_details":
            if len(sys.argv) < 3:
                print("Usage: task_details <instance_id>")
                return
            instance_id = sys.argv[2]
            details = helper.get_task_details(instance_id)
            if details:
                print(json.dumps(details, indent=2))
            else:
                print(f"Task not found: {instance_id}")
        
        elif command == "summary":
            summary = helper.get_completion_summary()
            print(json.dumps(summary, indent=2))
        
        elif command == "repo_stats":
            stats = helper.get_repo_statistics()
            print(json.dumps(stats, indent=2))
        
        elif command == "step_analytics":
            analytics = helper.get_step_analytics()
            print(json.dumps(analytics, indent=2))
        
        else:
            print(f"Unknown command: {command}")
    
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()