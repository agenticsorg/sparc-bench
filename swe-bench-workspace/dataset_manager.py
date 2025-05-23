#!/usr/bin/env python3
"""
SWE-bench Dataset Manager for roocode SPARC
Loads, parses, and validates SWE-bench datasets for delegation to roocode modes
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add SWE-bench to path
sys.path.insert(0, str(Path(__file__).parent / "SWE-bench"))

from swebench.harness.utils import load_swebench_dataset

class SWEBenchDatasetManager:
    """Manages SWE-bench dataset loading and task preparation for roocode SPARC"""
    
    def __init__(self, workspace_dir: str = "."):
        self.workspace_dir = Path(workspace_dir)
        self.datasets_dir = self.workspace_dir / "datasets"
        self.results_dir = self.workspace_dir / "results"
        self.logs_dir = self.workspace_dir / "logs"
        
        # Ensure directories exist
        self.datasets_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs_dir / "dataset_manager.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.lite_dataset = None
        self.full_dataset = None
        
    def load_lite_dataset(self) -> List[Dict[str, Any]]:
        """Load SWE-bench lite dataset (300 tasks)"""
        self.logger.info("Loading SWE-bench lite dataset...")
        
        try:
            dataset = load_swebench_dataset('princeton-nlp/SWE-bench_Lite')
            self.lite_dataset = dataset
            
            # Save to local file for caching
            lite_file = self.datasets_dir / "swe_bench_lite.json"
            with open(lite_file, 'w') as f:
                json.dump(dataset, f, indent=2)
            
            self.logger.info(f"✅ Loaded {len(dataset)} tasks from SWE-bench lite")
            return dataset
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load lite dataset: {e}")
            raise
    
    def load_full_dataset(self) -> List[Dict[str, Any]]:
        """Load full SWE-bench dataset"""
        self.logger.info("Loading SWE-bench full dataset...")
        
        try:
            dataset = load_swebench_dataset('princeton-nlp/SWE-bench')
            self.full_dataset = dataset
            
            # Save to local file for caching
            full_file = self.datasets_dir / "swe_bench_full.json"
            with open(full_file, 'w') as f:
                json.dump(dataset, f, indent=2)
            
            self.logger.info(f"✅ Loaded {len(dataset)} tasks from SWE-bench full")
            return dataset
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load full dataset: {e}")
            raise
    
    def parse_task_metadata(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Parse task metadata for roocode SPARC delegation"""
        metadata = {
            'instance_id': task.get('instance_id'),
            'repository': task.get('repo'),
            'problem_statement': task.get('problem_statement'),
            'hints': task.get('hints_text', ''),
            'base_commit': task.get('base_commit'),
            'patch': task.get('patch'),
            'test_patch': task.get('test_patch'),
            'fail_to_pass': task.get('FAIL_TO_PASS', []),
            'pass_to_pass': task.get('PASS_TO_PASS', []),
            'environment_setup_commit': task.get('environment_setup_commit'),
            'created_at': task.get('created_at'),
            'version': task.get('version'),
            
            # roocode SPARC delegation info
            'delegation_plan': self._create_delegation_plan(task),
            'complexity_score': self._calculate_complexity(task),
            'estimated_time_minutes': self._estimate_completion_time(task)
        }
        
        return metadata
    
    def _create_delegation_plan(self, task: Dict[str, Any]) -> Dict[str, str]:
        """Create task delegation plan for roocode modes"""
        plan = {
            'specification': 'spec-pseudocode',  # Parse problem statement
            'architecture': 'architect',         # Design solution approach
            'implementation': 'code',           # Generate patch
            'testing': 'tdd',                   # Run and validate tests
            'debugging': 'debug',               # Handle failures
            'security_review': 'security-review', # Check for vulnerabilities
            'documentation': 'docs-writer',     # Document changes
            'integration': 'integration',       # Final validation
            'orchestration': 'sparc'            # Overall coordination
        }
        return plan
    
    def _calculate_complexity(self, task: Dict[str, Any]) -> int:
        """Calculate task complexity score (1-10)"""
        complexity = 1
        
        # Based on problem statement length
        problem_length = len(task.get('problem_statement', ''))
        if problem_length > 1000:
            complexity += 2
        elif problem_length > 500:
            complexity += 1
        
        # Based on number of tests
        fail_to_pass = len(task.get('FAIL_TO_PASS', []))
        pass_to_pass = len(task.get('PASS_TO_PASS', []))
        total_tests = fail_to_pass + pass_to_pass
        
        if total_tests > 10:
            complexity += 3
        elif total_tests > 5:
            complexity += 2
        elif total_tests > 0:
            complexity += 1
        
        # Based on patch size (if available)
        patch = task.get('patch', '')
        if len(patch) > 2000:
            complexity += 2
        elif len(patch) > 1000:
            complexity += 1
        
        return min(complexity, 10)
    
    def _estimate_completion_time(self, task: Dict[str, Any]) -> int:
        """Estimate completion time in minutes"""
        base_time = 15  # Base 15 minutes
        complexity = self._calculate_complexity(task)
        return base_time + (complexity * 5)  # 5 minutes per complexity point
    
    def validate_task_data(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate dataset completeness"""
        self.logger.info("Validating task data...")
        
        validation_report = {
            'total_tasks': len(dataset),
            'valid_tasks': 0,
            'invalid_tasks': 0,
            'missing_fields': {},
            'validation_errors': []
        }
        
        required_fields = ['instance_id', 'repo', 'problem_statement', 'base_commit']
        
        for i, task in enumerate(dataset):
            is_valid = True
            task_errors = []
            
            # Check required fields
            for field in required_fields:
                if not task.get(field):
                    is_valid = False
                    task_errors.append(f"Missing {field}")
                    
                    if field not in validation_report['missing_fields']:
                        validation_report['missing_fields'][field] = 0
                    validation_report['missing_fields'][field] += 1
            
            # Check problem statement quality
            problem = task.get('problem_statement', '')
            if len(problem) < 50:
                is_valid = False
                task_errors.append("Problem statement too short")
            
            if is_valid:
                validation_report['valid_tasks'] += 1
            else:
                validation_report['invalid_tasks'] += 1
                validation_report['validation_errors'].append({
                    'task_index': i,
                    'instance_id': task.get('instance_id', 'unknown'),
                    'errors': task_errors
                })
        
        self.logger.info(f"✅ Validation complete: {validation_report['valid_tasks']} valid, {validation_report['invalid_tasks']} invalid")
        return validation_report
    
    def generate_task_list(self, dataset: List[Dict[str, Any]], 
                          dataset_type: str = "lite") -> Dict[str, Any]:
        """Generate structured task list for delegation"""
        self.logger.info(f"Generating task list for {dataset_type} dataset...")
        
        task_list = {
            'dataset_type': dataset_type,
            'total_tasks': len(dataset),
            'generated_at': datetime.now().isoformat(),
            'tasks': []
        }
        
        for task in dataset:
            parsed_task = self.parse_task_metadata(task)
            task_list['tasks'].append(parsed_task)
        
        # Save task list
        task_list_file = self.datasets_dir / f"task_list_{dataset_type}.json"
        with open(task_list_file, 'w') as f:
            json.dump(task_list, f, indent=2)
        
        self.logger.info(f"✅ Task list saved to {task_list_file}")
        return task_list
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive dataset summary"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'workspace_dir': str(self.workspace_dir),
            'datasets': {}
        }
        
        # Lite dataset summary
        if self.lite_dataset:
            lite_validation = self.validate_task_data(self.lite_dataset)
            report['datasets']['lite'] = {
                'total_tasks': len(self.lite_dataset),
                'validation': lite_validation,
                'complexity_distribution': self._get_complexity_distribution(self.lite_dataset),
                'repository_distribution': self._get_repository_distribution(self.lite_dataset)
            }
        
        # Full dataset summary
        if self.full_dataset:
            full_validation = self.validate_task_data(self.full_dataset)
            report['datasets']['full'] = {
                'total_tasks': len(self.full_dataset),
                'validation': full_validation,
                'complexity_distribution': self._get_complexity_distribution(self.full_dataset),
                'repository_distribution': self._get_repository_distribution(self.full_dataset)
            }
        
        # Save report
        report_file = self.results_dir / "dataset_summary.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"✅ Summary report saved to {report_file}")
        return report

    def _get_complexity_distribution(self, dataset: List[Dict[str, Any]]) -> Dict[int, int]:
        """Get distribution of complexity scores"""
        distribution = {}
        for task in dataset:
            complexity = self._calculate_complexity(task)
            distribution[complexity] = distribution.get(complexity, 0) + 1
        return distribution
    
    def _get_repository_distribution(self, dataset: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of repositories"""
        distribution = {}
        for task in dataset:
            repo = task.get('repo', 'unknown')
            distribution[repo] = distribution.get(repo, 0) + 1
        return distribution


def main():
    """Main execution function"""
    print("🚀 SWE-bench Dataset Manager for roocode SPARC")
    print("=" * 50)
    
    # Initialize manager
    manager = SWEBenchDatasetManager()
    
    # Load datasets
    print("\n📋 Phase 1: Loading Datasets")
    lite_dataset = manager.load_lite_dataset()
    
    # Validate data
    print("\n✅ Phase 2: Validating Data")
    lite_validation = manager.validate_task_data(lite_dataset)
    
    # Generate task lists
    print("\n📝 Phase 3: Generating Task Lists")
    lite_task_list = manager.generate_task_list(lite_dataset, "lite")
    
    # Generate summary report
    print("\n📊 Phase 4: Generating Summary Report")
    summary = manager.generate_summary_report()
    
    print("\n🎉 Dataset preparation complete!")
    print(f"✅ Lite dataset: {len(lite_dataset)} tasks loaded and validated")
    print(f"✅ Valid tasks: {lite_validation['valid_tasks']}")
    print(f"✅ Task list generated and ready for roocode SPARC delegation")
    
    return summary


if __name__ == "__main__":
    summary = main()