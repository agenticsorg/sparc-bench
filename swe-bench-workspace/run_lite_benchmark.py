#!/usr/bin/env python3
"""
Run SWE-bench Lite Benchmark with roocode SPARC and Completion Tracking

This script demonstrates the full benchmark orchestration workflow using:
1. SQLite database for efficient task storage and querying
2. Completion tracking with real-time status updates
3. Filtering by repository, complexity, and other criteria
4. Comprehensive reporting and analytics
"""

import sys
import argparse
from pathlib import Path
from swe_bench_orchestrator import SWEBenchOrchestrator


def print_completion_report(orchestrator, dataset_type="lite"):
    """Print comprehensive completion report"""
    print("\n" + "="*60)
    print("📊 SWE-bench Completion Report")
    print("="*60)
    
    try:
        # Get completion statistics
        completion_stats = orchestrator.get_completion_statistics(dataset_type)
        
        print("\n📈 Overall Progress:")
        total_tasks = sum(data['count'] for data in completion_stats['overall'].values())
        for status, data in completion_stats['overall'].items():
            bar_length = int((data['count'] / total_tasks) * 40)
            bar = "█" * bar_length + "░" * (40 - bar_length)
            print(f"  {status:10} │{bar}│ {data['count']:3d} ({data['percentage']:5.1f}%)")
            if data['avg_time']:
                print(f"             └─ Avg time: {data['avg_time']}s, Success: {data['avg_success_rate']:.1%}")
        
        print(f"\n🏆 Top Performing Repositories:")
        for repo in completion_stats['top_repositories'][:5]:
            if repo['completed'] > 0:
                print(f"  {repo['repository'][:30]:30} │ {repo['completed']:2d}/{repo['total']:2d} completed ({repo['completion_rate']:4.1f}%)")
        
        print(f"\n🎯 Completion by Complexity:")
        for complexity, data in completion_stats['complexity_analysis'].items():
            if data['completed'] > 0:
                print(f"  Complexity {complexity} │ {data['completed']:2d}/{data['total']:2d} completed ({data['completion_rate']:4.1f}%)")
                
    except Exception as e:
        print(f"⚠️ Could not generate completion report: {e}")


def main():
    """Main function to run SWE-bench lite benchmark"""
    parser = argparse.ArgumentParser(description="Run SWE-bench Lite Benchmark with roocode SPARC")
    parser.add_argument("--max-tasks", type=int, default=10, help="Maximum number of tasks to process")
    parser.add_argument("--repository", type=str, help="Filter by repository (e.g., 'astropy', 'django')")
    parser.add_argument("--min-complexity", type=int, help="Minimum complexity score")
    parser.add_argument("--max-complexity", type=int, help="Maximum complexity score")
    parser.add_argument("--batch-size", type=int, default=5, help="Batch size for progress reporting")
    parser.add_argument("--dataset", type=str, default="lite", choices=["lite", "test"], help="Dataset type")
    parser.add_argument("--report-only", action="store_true", help="Only show completion report, don't run benchmark")
    
    args = parser.parse_args()
    
    print("🚀 SWE-bench Lite Benchmark with roocode SPARC")
    print("🔧 SQLite-Enhanced Orchestration & Completion Tracking")
    print("="*60)
    
    # Initialize orchestrator
    orchestrator = SWEBenchOrchestrator()
    
    # Check if database exists
    db_file = Path(f"swe_bench_{args.dataset}_tasks.sqlite")
    if not db_file.exists():
        print(f"❌ Database not found: {db_file}")
        print("Please run json_to_sqlite_converter.py first to create the database.")
        sys.exit(1)
    
    # Show current completion status
    print_completion_report(orchestrator, args.dataset)
    
    if args.report_only:
        print("\n✅ Report complete. Use --max-tasks to run benchmark.")
        return
    
    # Prepare filtering options
    complexity_range = None
    if args.min_complexity or args.max_complexity:
        min_c = args.min_complexity or 1
        max_c = args.max_complexity or 10
        complexity_range = (min_c, max_c)
    
    print(f"\n🎯 Running benchmark:")
    print(f"  Dataset: {args.dataset}")
    print(f"  Max tasks: {args.max_tasks}")
    if args.repository:
        print(f"  Repository filter: {args.repository}")
    if complexity_range:
        print(f"  Complexity range: {complexity_range[0]}-{complexity_range[1]}")
    print(f"  Batch size: {args.batch_size}")
    
    # Run the benchmark
    try:
        results = orchestrator.run_benchmark(
            dataset_type=args.dataset,
            max_tasks=args.max_tasks,
            repository_filter=args.repository,
            complexity_range=complexity_range,
            batch_size=args.batch_size
        )
        
        print(f"\n🎉 Benchmark completed successfully!")
        print(f"📊 Results summary:")
        print(f"  Total tasks processed: {results['dataset_statistics']['total_tasks']}")
        print(f"  Successful: {results['dataset_statistics']['successful_tasks']}")
        print(f"  Failed: {results['dataset_statistics']['failed_tasks']}")
        print(f"  Success rate: {results['performance_metrics']['success_rate']:.1%}")
        
        # Show updated completion report
        print_completion_report(orchestrator, args.dataset)
        
        print(f"\n📁 Results saved to: results/benchmark_summary_{args.dataset}.json")
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()