#!/usr/bin/env python3
"""
SWE-bench Task List JSON to SQLite Converter

This script converts the SWE-bench lite task list JSON file to a SQLite database
for easier querying and analysis of benchmark tasks.
"""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Any, List
import argparse
from datetime import datetime


class TaskListConverter:
    """Converts SWE-bench task list from JSON to SQLite format."""
    
    def __init__(self, json_file: str, sqlite_file: str):
        self.json_file = Path(json_file)
        self.sqlite_file = Path(sqlite_file)
        self.conn = None
        
    def create_schema(self):
        """Create the SQLite database schema for SWE-bench tasks."""
        schema_sql = """
        -- Main tasks table
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instance_id TEXT UNIQUE NOT NULL,
            repository TEXT NOT NULL,
            problem_statement TEXT NOT NULL,
            hints TEXT,
            base_commit TEXT NOT NULL,
            patch TEXT NOT NULL,
            test_patch TEXT NOT NULL,
            fail_to_pass TEXT,
            pass_to_pass TEXT,
            environment_setup_commit TEXT NOT NULL,
            created_at TEXT NOT NULL,
            version TEXT NOT NULL,
            complexity_score INTEGER,
            estimated_time_minutes INTEGER,
            created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Delegation plan table (normalized)
        CREATE TABLE IF NOT EXISTS delegation_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            specification TEXT,
            architecture TEXT,
            implementation TEXT,
            testing TEXT,
            debugging TEXT,
            security_review TEXT,
            documentation TEXT,
            integration TEXT,
            orchestration TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        );
        
        -- Metadata table for dataset information
        CREATE TABLE IF NOT EXISTS dataset_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_type TEXT NOT NULL,
            total_tasks INTEGER NOT NULL,
            generated_at TEXT NOT NULL,
            conversion_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Repository statistics view
        CREATE VIEW IF NOT EXISTS repository_stats AS
        SELECT 
            repository,
            COUNT(*) as task_count,
            AVG(complexity_score) as avg_complexity,
            AVG(estimated_time_minutes) as avg_time_minutes,
            MIN(created_at) as earliest_task,
            MAX(created_at) as latest_task
        FROM tasks 
        GROUP BY repository 
        ORDER BY task_count DESC;
        
        -- Complexity distribution view
        CREATE VIEW IF NOT EXISTS complexity_distribution AS
        SELECT 
            complexity_score,
            COUNT(*) as task_count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tasks), 2) as percentage
        FROM tasks 
        WHERE complexity_score IS NOT NULL
        GROUP BY complexity_score 
        ORDER BY complexity_score;
        
        -- Task summary view
        CREATE VIEW IF NOT EXISTS task_summary AS
        SELECT 
            t.instance_id,
            t.repository,
            t.complexity_score,
            t.estimated_time_minutes,
            t.version,
            t.created_at,
            dp.specification,
            dp.implementation,
            dp.testing
        FROM tasks t
        LEFT JOIN delegation_plans dp ON t.id = dp.task_id;
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_tasks_repository ON tasks(repository);
        CREATE INDEX IF NOT EXISTS idx_tasks_complexity ON tasks(complexity_score);
        CREATE INDEX IF NOT EXISTS idx_tasks_instance_id ON tasks(instance_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_version ON tasks(version);
        CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
        """
        
        self.conn.executescript(schema_sql)
        self.conn.commit()
        print("✅ Database schema created successfully")
    
    def load_json_data(self) -> Dict[str, Any]:
        """Load and parse the JSON file."""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Loaded JSON data: {data.get('total_tasks', 0)} tasks")
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {self.json_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def insert_metadata(self, data: Dict[str, Any]):
        """Insert dataset metadata into the database."""
        metadata_sql = """
        INSERT INTO dataset_metadata (dataset_type, total_tasks, generated_at)
        VALUES (?, ?, ?)
        """
        
        self.conn.execute(metadata_sql, (
            data.get('dataset_type', 'unknown'),
            data.get('total_tasks', 0),
            data.get('generated_at', '')
        ))
        print("✅ Dataset metadata inserted")
    
    def insert_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Insert tasks into the database and return mapping of instance_id to task_id."""
        task_sql = """
        INSERT INTO tasks (
            instance_id, repository, problem_statement, hints, base_commit,
            patch, test_patch, fail_to_pass, pass_to_pass, environment_setup_commit,
            created_at, version, complexity_score, estimated_time_minutes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        instance_id_to_task_id = {}
        
        for task in tasks:
            cursor = self.conn.execute(task_sql, (
                task.get('instance_id', ''),
                task.get('repository', ''),
                task.get('problem_statement', ''),
                task.get('hints', ''),
                task.get('base_commit', ''),
                task.get('patch', ''),
                task.get('test_patch', ''),
                json.dumps(task.get('fail_to_pass', [])) if task.get('fail_to_pass') else None,
                json.dumps(task.get('pass_to_pass', [])) if task.get('pass_to_pass') else None,
                task.get('environment_setup_commit', ''),
                task.get('created_at', ''),
                task.get('version', ''),
                task.get('complexity_score'),
                task.get('estimated_time_minutes')
            ))
            
            task_id = cursor.lastrowid
            instance_id_to_task_id[task.get('instance_id', '')] = task_id
        
        print(f"✅ Inserted {len(tasks)} tasks")
        return instance_id_to_task_id
    
    def insert_delegation_plans(self, tasks: List[Dict[str, Any]], task_id_map: Dict[str, int]):
        """Insert delegation plans into the database."""
        delegation_sql = """
        INSERT INTO delegation_plans (
            task_id, specification, architecture, implementation, testing,
            debugging, security_review, documentation, integration, orchestration
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        delegation_count = 0
        for task in tasks:
            instance_id = task.get('instance_id', '')
            task_id = task_id_map.get(instance_id)
            
            if task_id and 'delegation_plan' in task:
                plan = task['delegation_plan']
                self.conn.execute(delegation_sql, (
                    task_id,
                    plan.get('specification', ''),
                    plan.get('architecture', ''),
                    plan.get('implementation', ''),
                    plan.get('testing', ''),
                    plan.get('debugging', ''),
                    plan.get('security_review', ''),
                    plan.get('documentation', ''),
                    plan.get('integration', ''),
                    plan.get('orchestration', '')
                ))
                delegation_count += 1
        
        print(f"✅ Inserted {delegation_count} delegation plans")
    
    def generate_summary_report(self):
        """Generate a summary report of the converted data."""
        print("\n" + "="*60)
        print("📊 CONVERSION SUMMARY REPORT")
        print("="*60)
        
        # Total tasks
        total_tasks = self.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        print(f"Total tasks: {total_tasks}")
        
        # Repository distribution
        print(f"\n📦 Repository Distribution:")
        repo_stats = self.conn.execute("""
            SELECT repository, COUNT(*) as count, 
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tasks), 1) as percentage
            FROM tasks 
            GROUP BY repository 
            ORDER BY count DESC 
            LIMIT 10
        """).fetchall()
        
        for repo, count, percentage in repo_stats:
            print(f"  {repo}: {count} tasks ({percentage}%)")
        
        # Complexity distribution
        print(f"\n🎯 Complexity Distribution:")
        complexity_stats = self.conn.execute("""
            SELECT complexity_score, COUNT(*) as count
            FROM tasks 
            WHERE complexity_score IS NOT NULL
            GROUP BY complexity_score 
            ORDER BY complexity_score
        """).fetchall()
        
        for complexity, count in complexity_stats:
            print(f"  Level {complexity}: {count} tasks")
        
        # Version distribution
        print(f"\n📋 Version Distribution:")
        version_stats = self.conn.execute("""
            SELECT version, COUNT(*) as count
            FROM tasks 
            GROUP BY version 
            ORDER BY count DESC
        """).fetchall()
        
        for version, count in version_stats:
            print(f"  Version {version}: {count} tasks")
        
        # Average metrics
        avg_stats = self.conn.execute("""
            SELECT AVG(complexity_score) as avg_complexity,
                   AVG(estimated_time_minutes) as avg_time
            FROM tasks 
            WHERE complexity_score IS NOT NULL AND estimated_time_minutes IS NOT NULL
        """).fetchone()
        
        if avg_stats:
            print(f"\n📈 Average Metrics:")
            print(f"  Average complexity: {avg_stats[0]:.1f}")
            print(f"  Average estimated time: {avg_stats[1]:.0f} minutes")
        
        print(f"\n💾 Database file: {self.sqlite_file}")
        print(f"Database size: {self.sqlite_file.stat().st_size / 1024:.1f} KB")
        print("="*60)
    
    def convert(self):
        """Main conversion process."""
        try:
            print(f"🔄 Converting {self.json_file} to {self.sqlite_file}")
            
            # Load JSON data
            data = self.load_json_data()
            
            # Create SQLite database
            self.conn = sqlite3.connect(self.sqlite_file)
            self.conn.execute("PRAGMA foreign_keys = ON")
            
            # Create schema
            self.create_schema()
            
            # Insert data
            self.insert_metadata(data)
            
            tasks = data.get('tasks', [])
            task_id_map = self.insert_tasks(tasks)
            self.insert_delegation_plans(tasks, task_id_map)
            
            # Commit all changes
            self.conn.commit()
            
            # Generate summary
            self.generate_summary_report()
            
            print(f"\n🎉 Conversion completed successfully!")
            print(f"📁 SQLite database created: {self.sqlite_file}")
            
        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            if self.conn:
                self.conn.close()


def main():
    """Main entry point for the converter."""
    parser = argparse.ArgumentParser(
        description="Convert SWE-bench task list JSON to SQLite database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python json_to_sqlite_converter.py
  python json_to_sqlite_converter.py --input custom_tasks.json --output custom_db.sqlite
  python json_to_sqlite_converter.py --input datasets/task_list_lite.json --output databases/swe_bench_lite.db
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        default='datasets/task_list_lite.json',
        help='Input JSON file path (default: datasets/task_list_lite.json)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='swe_bench_lite_tasks.sqlite',
        help='Output SQLite file path (default: swe_bench_lite_tasks.sqlite)'
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Overwrite output file if it exists'
    )
    
    args = parser.parse_args()
    
    # Check input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        sys.exit(1)
    
    # Check output file
    output_path = Path(args.output)
    if output_path.exists() and not args.force:
        print(f"❌ Output file already exists: {output_path}")
        print("Use --force to overwrite")
        sys.exit(1)
    
    # Perform conversion
    converter = TaskListConverter(str(input_path), str(output_path))
    converter.convert()


if __name__ == '__main__':
    main()