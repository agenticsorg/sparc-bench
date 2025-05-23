#!/usr/bin/env python3
"""
Compare SWE-bench Lite vs Full datasets.
"""

import sqlite3
from pathlib import Path


def get_db_stats(db_path: str) -> dict:
    """Get statistics from a SWE-bench database."""
    if not Path(db_path).exists():
        return {"exists": False}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    stats = {"exists": True}
    
    # Total tasks
    cursor.execute("SELECT COUNT(*) FROM swe_bench_tasks")
    stats["total_tasks"] = cursor.fetchone()[0]
    
    # Tasks by status
    cursor.execute("SELECT completion_status, COUNT(*) FROM swe_bench_tasks GROUP BY completion_status")
    stats["by_status"] = dict(cursor.fetchall())
    
    # Top repositories
    cursor.execute("SELECT repo, COUNT(*) FROM swe_bench_tasks GROUP BY repo ORDER BY COUNT(*) DESC LIMIT 5")
    stats["top_repos"] = cursor.fetchall()
    
    # Schema info
    cursor.execute("PRAGMA table_info(swe_bench_tasks)")
    stats["columns"] = [row[1] for row in cursor.fetchall()]
    
    conn.close()
    return stats


def main():
    """Compare the datasets."""
    print("SWE-bench Database Comparison")
    print("=" * 50)
    
    lite_stats = get_db_stats("../databases/swe_bench_lite.db")
    full_stats = get_db_stats("../databases/swe_bench_full.db")
    
    # Lite dataset
    print("\n📋 SWE-bench Lite Dataset:")
    if lite_stats["exists"]:
        print(f"  Total tasks: {lite_stats['total_tasks']}")
        print("  Status breakdown:")
        for status, count in lite_stats["by_status"].items():
            pct = (count / lite_stats['total_tasks']) * 100
            print(f"    {status}: {count} ({pct:.1f}%)")
        print("  Top repositories:")
        for repo, count in lite_stats["top_repos"]:
            print(f"    {repo}: {count}")
    else:
        print("  ❌ Database not found")
    
    # Full dataset
    print("\n📚 SWE-bench Full Dataset:")
    if full_stats["exists"]:
        print(f"  Total tasks: {full_stats['total_tasks']}")
        print("  Status breakdown:")
        for status, count in full_stats["by_status"].items():
            pct = (count / full_stats['total_tasks']) * 100
            print(f"    {status}: {count} ({pct:.1f}%)")
        print("  Top repositories:")
        for repo, count in full_stats["top_repos"]:
            print(f"    {repo}: {count}")
    else:
        print("  ❌ Database not found")
    
    # Comparison
    if lite_stats["exists"] and full_stats["exists"]:
        print(f"\n🔍 Comparison:")
        ratio = full_stats["total_tasks"] / lite_stats["total_tasks"]
        print(f"  Full dataset is {ratio:.1f}x larger than lite")
        print(f"  Full: {full_stats['total_tasks']} tasks")
        print(f"  Lite: {lite_stats['total_tasks']} tasks")
        
        # Schema differences
        lite_cols = set(lite_stats["columns"])
        full_cols = set(full_stats["columns"])
        
        if lite_cols != full_cols:
            print(f"\n  Schema differences:")
            only_in_full = full_cols - lite_cols
            only_in_lite = lite_cols - full_cols
            
            if only_in_full:
                print(f"    Columns only in full: {', '.join(only_in_full)}")
            if only_in_lite:
                print(f"    Columns only in lite: {', '.join(only_in_lite)}")
        else:
            print(f"    ✅ Schemas are identical")
    
    print(f"\n💡 Usage:")
    print(f"  Query lite dataset: python query_swe_bench_db.py")
    print(f"  Query full dataset: sqlite3 swe_bench_full.db")
    print(f"  Load specific dataset: python load_full_swe_bench_to_sqlite.py --dataset <name>")


if __name__ == "__main__":
    main()