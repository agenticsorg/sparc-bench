#!/usr/bin/env python3
"""
SWE-bench Native Execution Script for roocode SPARC
Runs SWE-bench tasks using native Python execution instead of Docker
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

class NativeSWEBenchRunner:
    """Native SWE-bench runner that integrates with roocode SPARC modes"""
    
    def __init__(self, config_path="config/roocode-config.yaml"):
        self.config_path = Path(config_path)
        self.load_config()
        self.setup_environment()
    
    def load_config(self):
        """Load roocode SPARC configuration"""
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        print(f"✅ Loaded configuration for {self.config['agent_system']}")
        print(f"📋 Benchmark mode: {self.config['benchmark_mode']}")
        print(f"🐳 Docker disabled: {self.config['docker_enabled'] == False}")
    
    def setup_environment(self):
        """Configure environment for native execution"""
        os.environ['SWE_BENCH_DOCKER_DISABLED'] = 'true'
        os.environ['SWE_BENCH_NATIVE_MODE'] = 'true'
        
        # Add SWE-bench to Python path
        swe_bench_path = Path("SWE-bench").resolve()
        if str(swe_bench_path) not in sys.path:
            sys.path.insert(0, str(swe_bench_path))
        
        print(f"🔧 Environment configured for native execution")
        print(f"📦 SWE-bench path: {swe_bench_path}")
    
    def run_task(self, task_instance, mode=None):
        """Execute a single SWE-bench task using roocode SPARC"""
        task_id = task_instance.get('instance_id', 'unknown')
        task_type = self.classify_task(task_instance)
        
        # Route to appropriate roocode mode
        target_mode = mode or self.config['task_routing'].get(task_type, 'code')
        
        print(f"🎯 Running task {task_id}")
        print(f"📁 Task type: {task_type}")
        print(f"🤖 Target mode: {target_mode}")
        
        # Create task workspace
        task_workspace = Path(f"results/{task_id}")
        task_workspace.mkdir(parents=True, exist_ok=True)
        
        # Extract task details
        repo = task_instance.get('repo', '')
        problem_statement = task_instance.get('problem_statement', '')
        
        # Save task context
        task_context = {
            'instance_id': task_id,
            'repo': repo,
            'problem_statement': problem_statement,
            'mode': target_mode,
            'workspace': str(task_workspace),
            'timestamp': os.environ.get('TIMESTAMP', ''),
        }
        
        with open(task_workspace / 'task_context.json', 'w') as f:
            json.dump(task_context, f, indent=2)
        
        print(f"💾 Task context saved to {task_workspace}/task_context.json")
        
        # This would integrate with roocode SPARC modes
        # For now, we simulate the execution
        result = self.simulate_roocode_execution(task_context)
        
        # Save results
        with open(task_workspace / 'results.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    
    def classify_task(self, task_instance):
        """Classify SWE-bench task to determine appropriate roocode mode"""
        problem = task_instance.get('problem_statement', '').lower()
        
        if any(word in problem for word in ['test', 'testing', 'unittest']):
            return 'test_execution'
        elif any(word in problem for word in ['security', 'vulnerability', 'auth']):
            return 'security_review'
        elif any(word in problem for word in ['debug', 'error', 'exception', 'traceback']):
            return 'code_analysis'
        elif any(word in problem for word in ['integrate', 'merge', 'combine']):
            return 'integration'
        else:
            return 'patch_generation'
    
    def simulate_roocode_execution(self, task_context):
        """Simulate roocode SPARC execution (replace with actual integration)"""
        mode = task_context['mode']
        task_id = task_context['instance_id']
        
        print(f"🧠 Simulating {mode} mode execution for {task_id}")
        
        # This would be replaced with actual roocode SPARC integration
        # using the new_task functionality to delegate to appropriate modes
        
        result = {
            'task_id': task_id,
            'mode_used': mode,
            'status': 'completed',
            'execution_type': 'native',
            'docker_used': False,
            'roocode_sparc': True,
            'message': f'Task processed by roocode SPARC {mode} mode'
        }
        
        return result
    
    def run_benchmark_suite(self, dataset_name='swe-bench-lite', limit=None):
        """Run a full benchmark suite using roocode SPARC"""
        print(f"🚀 Starting {dataset_name} benchmark with roocode SPARC")
        print(f"⏱️  Max concurrent tasks: {self.config['swe_bench']['max_concurrent_tasks']}")
        
        # This would load actual SWE-bench dataset
        # For demonstration, we create a sample task
        sample_tasks = [
            {
                'instance_id': 'sample_task_001',
                'repo': 'example/repo',
                'problem_statement': 'Fix the authentication bug in the login system',
            }
        ]
        
        results = []
        for i, task in enumerate(sample_tasks):
            if limit and i >= limit:
                break
            
            try:
                result = self.run_task(task)
                results.append(result)
                print(f"✅ Completed task {task['instance_id']}")
            except Exception as e:
                print(f"❌ Failed task {task['instance_id']}: {e}")
                results.append({
                    'task_id': task['instance_id'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Save benchmark summary
        summary = {
            'dataset': dataset_name,
            'total_tasks': len(results),
            'completed': len([r for r in results if r.get('status') == 'completed']),
            'failed': len([r for r in results if r.get('status') == 'failed']),
            'results': results
        }
        
        summary_path = Path('results/benchmark_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📊 Benchmark summary saved to {summary_path}")
        return summary

def main():
    """Main execution function"""
    print("🚀 SWE-bench Native Runner for roocode SPARC")
    print("=" * 50)
    
    runner = NativeSWEBenchRunner()
    
    # Run a small test benchmark
    summary = runner.run_benchmark_suite(limit=1)
    
    print("\n📈 Benchmark Results:")
    print(f"   Total tasks: {summary['total_tasks']}")
    print(f"   Completed: {summary['completed']}")
    print(f"   Failed: {summary['failed']}")
    print("\n🎯 Ready for full roocode SPARC benchmarking!")

if __name__ == "__main__":
    main()