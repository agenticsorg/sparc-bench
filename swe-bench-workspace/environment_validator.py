#!/usr/bin/env python3
"""
SWE-bench Environment Validator & Monitor
Comprehensive validation of SWE-bench lite environment for roocode SPARC benchmarking
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class EnvironmentValidator:
    """Validates and monitors SWE-bench environment for roocode SPARC"""
    
    def __init__(self, workspace_dir: str = "."):
        self.workspace_dir = Path(workspace_dir)
        self.logs_dir = self.workspace_dir / "logs"
        self.results_dir = self.workspace_dir / "results"
        
        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        
        # Setup logging
        log_file = self.logs_dir / "environment_validation.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Validation results
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'environment': {},
            'dependencies': {},
            'swe_bench': {},
            'roocode_config': {},
            'datasets': {},
            'workspace': {},
            'overall_status': 'unknown'
        }
    
    def check_python_environment(self) -> Dict[str, Any]:
        """Check Python version and environment"""
        self.logger.info("🐍 Checking Python environment...")
        
        python_info = {
            'version': sys.version,
            'version_info': {
                'major': sys.version_info.major,
                'minor': sys.version_info.minor,
                'micro': sys.version_info.micro
            },
            'executable': sys.executable,
            'platform': sys.platform,
            'status': 'unknown'
        }
        
        # Check Python version requirements (3.8+)
        if sys.version_info >= (3, 8):
            python_info['status'] = 'valid'
            self.logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} - Compatible")
        else:
            python_info['status'] = 'invalid'
            self.logger.error(f"❌ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} - Requires 3.8+")
        
        return python_info
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check required Python dependencies"""
        self.logger.info("📦 Checking dependencies...")
        
        required_packages = [
            'numpy', 'scipy', 'pandas', 'matplotlib', 'requests',
            'yaml', 'datasets', 'transformers', 'torch'
        ]
        
        optional_packages = [
            'jupyter', 'notebook', 'tqdm', 'pytest'
        ]
        
        dependencies = {
            'required': {},
            'optional': {},
            'missing_required': [],
            'missing_optional': [],
            'status': 'unknown'
        }
        
        # Check required packages
        for package in required_packages:
            try:
                __import__(package)
                dependencies['required'][package] = 'installed'
                self.logger.info(f"✅ {package} - Available")
            except ImportError:
                dependencies['required'][package] = 'missing'
                dependencies['missing_required'].append(package)
                self.logger.warning(f"⚠️ {package} - Missing")
        
        # Check optional packages
        for package in optional_packages:
            try:
                __import__(package)
                dependencies['optional'][package] = 'installed'
                self.logger.info(f"✅ {package} - Available (optional)")
            except ImportError:
                dependencies['optional'][package] = 'missing'
                dependencies['missing_optional'].append(package)
                self.logger.info(f"ℹ️ {package} - Missing (optional)")
        
        # Overall status
        if not dependencies['missing_required']:
            dependencies['status'] = 'valid'
            self.logger.info("✅ All required dependencies available")
        else:
            dependencies['status'] = 'invalid'
            self.logger.error(f"❌ Missing required dependencies: {dependencies['missing_required']}")
        
        return dependencies
    
    def check_swe_bench_installation(self) -> Dict[str, Any]:
        """Check SWE-bench installation and accessibility"""
        self.logger.info("🔧 Checking SWE-bench installation...")
        
        swe_bench = {
            'installation_path': None,
            'version': None,
            'importable': False,
            'cli_accessible': False,
            'dataset_loadable': False,
            'status': 'unknown'
        }
        
        # Check if SWE-bench directory exists
        swe_bench_dir = self.workspace_dir / "SWE-bench"
        if swe_bench_dir.exists():
            swe_bench['installation_path'] = str(swe_bench_dir)
            self.logger.info(f"✅ SWE-bench directory found: {swe_bench_dir}")
        else:
            self.logger.error("❌ SWE-bench directory not found")
            swe_bench['status'] = 'invalid'
            return swe_bench
        
        # Check if swebench module is importable
        try:
            sys.path.insert(0, str(swe_bench_dir))
            import swebench
            swe_bench['importable'] = True
            swe_bench['version'] = getattr(swebench, '__version__', 'unknown')
            self.logger.info(f"✅ SWE-bench module importable, version: {swe_bench['version']}")
        except ImportError as e:
            self.logger.error(f"❌ SWE-bench module import failed: {e}")
            swe_bench['status'] = 'invalid'
            return swe_bench
        
        # Check if datasets can be loaded
        try:
            from swebench.harness.utils import load_swebench_dataset
            # Try loading a small sample
            dataset = load_swebench_dataset('princeton-nlp/SWE-bench_Lite')
            if dataset and len(dataset) > 0:
                swe_bench['dataset_loadable'] = True
                self.logger.info(f"✅ SWE-bench dataset loadable: {len(dataset)} tasks")
            else:
                self.logger.error("❌ SWE-bench dataset empty or invalid")
        except Exception as e:
            self.logger.error(f"❌ SWE-bench dataset loading failed: {e}")
            swe_bench['status'] = 'invalid'
            return swe_bench
        
        swe_bench['status'] = 'valid'
        self.logger.info("✅ SWE-bench installation validated")
        return swe_bench
    
    def check_roocode_configuration(self) -> Dict[str, Any]:
        """Check roocode SPARC configuration"""
        self.logger.info("⚙️ Checking roocode configuration...")
        
        config = {
            'config_file_exists': False,
            'env_file_exists': False,
            'github_token_configured': False,
            'native_mode_enabled': False,
            'docker_disabled': False,
            'agent_system_correct': False,
            'status': 'unknown'
        }
        
        # Check config file
        config_file = self.workspace_dir / "config" / "roocode-config.yaml"
        if config_file.exists():
            config['config_file_exists'] = True
            self.logger.info("✅ roocode-config.yaml found")
            
            try:
                import yaml
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Check key configuration values
                if config_data.get('docker_enabled') == False:
                    config['docker_disabled'] = True
                    self.logger.info("✅ Docker disabled (native mode)")
                
                if config_data.get('agent_system') == 'roocode_sparc':
                    config['agent_system_correct'] = True
                    self.logger.info("✅ Agent system set to roocode_sparc")
                
                if config_data.get('benchmark_mode') == 'native':
                    config['native_mode_enabled'] = True
                    self.logger.info("✅ Native benchmark mode enabled")
                
                if config_data.get('github_token'):
                    config['github_token_configured'] = True
                    self.logger.info("✅ GitHub token configured")
                
            except Exception as e:
                self.logger.error(f"❌ Error reading config file: {e}")
        else:
            self.logger.error("❌ roocode-config.yaml not found")
        
        # Check environment file
        env_file = self.workspace_dir / ".env"
        if env_file.exists():
            config['env_file_exists'] = True
            self.logger.info("✅ .env file found")
        else:
            self.logger.warning("⚠️ .env file not found")
        
        # Overall status
        required_checks = [
            config['config_file_exists'],
            config['docker_disabled'],
            config['agent_system_correct'],
            config['native_mode_enabled']
        ]
        
        if all(required_checks):
            config['status'] = 'valid'
            self.logger.info("✅ roocode configuration validated")
        else:
            config['status'] = 'invalid'
            self.logger.error("❌ roocode configuration incomplete")
        
        return config
    
    def check_datasets(self) -> Dict[str, Any]:
        """Check dataset availability and status"""
        self.logger.info("📊 Checking datasets...")
        
        datasets = {
            'datasets_dir_exists': False,
            'lite_dataset_available': False,
            'lite_task_list_exists': False,
            'full_dataset_available': False,
            'dataset_summary_exists': False,
            'lite_task_count': 0,
            'status': 'unknown'
        }
        
        datasets_dir = self.workspace_dir / "datasets"
        if datasets_dir.exists():
            datasets['datasets_dir_exists'] = True
            self.logger.info("✅ Datasets directory found")
        else:
            self.logger.error("❌ Datasets directory not found")
            datasets['status'] = 'invalid'
            return datasets
        
        # Check lite dataset files
        lite_dataset_file = datasets_dir / "swe_bench_lite.json"
        if lite_dataset_file.exists():
            datasets['lite_dataset_available'] = True
            self.logger.info("✅ SWE-bench lite dataset file found")
        
        lite_task_list = datasets_dir / "task_list_lite.json"
        if lite_task_list.exists():
            datasets['lite_task_list_exists'] = True
            try:
                with open(lite_task_list, 'r') as f:
                    task_data = json.load(f)
                datasets['lite_task_count'] = len(task_data.get('tasks', []))
                self.logger.info(f"✅ Lite task list found: {datasets['lite_task_count']} tasks")
            except Exception as e:
                self.logger.error(f"❌ Error reading task list: {e}")
        
        # Check dataset summary
        summary_file = self.results_dir / "dataset_summary.json"
        if summary_file.exists():
            datasets['dataset_summary_exists'] = True
            self.logger.info("✅ Dataset summary found")
        
        # Overall status
        if datasets['datasets_dir_exists'] and datasets['lite_task_list_exists'] and datasets['lite_task_count'] > 0:
            datasets['status'] = 'valid'
            self.logger.info("✅ Datasets validated")
        else:
            datasets['status'] = 'invalid'
            self.logger.error("❌ Dataset validation failed")
        
        return datasets
    
    def check_workspace_structure(self) -> Dict[str, Any]:
        """Check workspace directory structure"""
        self.logger.info("📁 Checking workspace structure...")
        
        workspace = {
            'required_dirs': {},
            'optional_dirs': {},
            'key_files': {},
            'permissions': {},
            'status': 'unknown'
        }
        
        # Required directories
        required_dirs = ['datasets', 'logs', 'results', 'config', 'SWE-bench']
        for dir_name in required_dirs:
            dir_path = self.workspace_dir / dir_name
            workspace['required_dirs'][dir_name] = {
                'exists': dir_path.exists(),
                'writable': dir_path.exists() and os.access(dir_path, os.W_OK),
                'path': str(dir_path)
            }
            
            if dir_path.exists():
                self.logger.info(f"✅ Required directory: {dir_name}")
            else:
                self.logger.error(f"❌ Missing required directory: {dir_name}")
        
        # Optional directories  
        optional_dirs = ['temp', 'cache', 'backups']
        for dir_name in optional_dirs:
            dir_path = self.workspace_dir / dir_name
            workspace['optional_dirs'][dir_name] = {
                'exists': dir_path.exists(),
                'writable': dir_path.exists() and os.access(dir_path, os.W_OK),
                'path': str(dir_path)
            }
        
        # Key files
        key_files = [
            'validate-setup.py',
            'dataset_manager.py', 
            'swe_bench_orchestrator.py',
            'environment_validator.py'
        ]
        
        for file_name in key_files:
            file_path = self.workspace_dir / file_name
            workspace['key_files'][file_name] = {
                'exists': file_path.exists(),
                'executable': file_path.exists() and os.access(file_path, os.X_OK),
                'path': str(file_path)
            }
            
            if file_path.exists():
                self.logger.info(f"✅ Key file: {file_name}")
            else:
                self.logger.warning(f"⚠️ Missing key file: {file_name}")
        
        # Check overall permissions
        workspace['permissions']['workspace_writable'] = os.access(self.workspace_dir, os.W_OK)
        workspace['permissions']['workspace_readable'] = os.access(self.workspace_dir, os.R_OK)
        
        # Overall status
        all_required_dirs = all(info['exists'] for info in workspace['required_dirs'].values())
        all_key_files = all(info['exists'] for info in workspace['key_files'].values())
        
        if all_required_dirs and workspace['permissions']['workspace_writable']:
            workspace['status'] = 'valid'
            self.logger.info("✅ Workspace structure validated")
        else:
            workspace['status'] = 'invalid'
            self.logger.error("❌ Workspace structure validation failed")
        
        return workspace
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete environment validation"""
        self.logger.info("🔍 Starting comprehensive environment validation...")
        self.logger.info("=" * 60)
        
        # Run all validation checks
        self.validation_results['environment'] = self.check_python_environment()
        self.validation_results['dependencies'] = self.check_dependencies()
        self.validation_results['swe_bench'] = self.check_swe_bench_installation()
        self.validation_results['roocode_config'] = self.check_roocode_configuration()
        self.validation_results['datasets'] = self.check_datasets()
        self.validation_results['workspace'] = self.check_workspace_structure()
        
        # Determine overall status
        all_checks = [
            self.validation_results['environment']['status'],
            self.validation_results['dependencies']['status'],
            self.validation_results['swe_bench']['status'],
            self.validation_results['roocode_config']['status'],
            self.validation_results['datasets']['status'],
            self.validation_results['workspace']['status']
        ]
        
        if all(status == 'valid' for status in all_checks):
            self.validation_results['overall_status'] = 'valid'
            self.logger.info("🎉 Environment validation PASSED - Ready for benchmarking!")
        else:
            self.validation_results['overall_status'] = 'invalid'
            failed_checks = [name for name, status in zip(
                ['environment', 'dependencies', 'swe_bench', 'roocode_config', 'datasets', 'workspace'],
                all_checks
            ) if status != 'valid']
            self.logger.error(f"❌ Environment validation FAILED - Issues in: {failed_checks}")
        
        # Save validation report
        report_file = self.results_dir / "environment_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        self.logger.info(f"📄 Validation report saved to: {report_file}")
        return self.validation_results
    
    def generate_readiness_summary(self) -> str:
        """Generate human-readable readiness summary"""
        if not self.validation_results or self.validation_results['overall_status'] == 'unknown':
            return "⚠️ Validation not yet performed. Run comprehensive validation first."
        
        summary_lines = [
            "🚀 SWE-bench Environment Readiness Summary",
            "=" * 50,
            f"Overall Status: {'✅ READY' if self.validation_results['overall_status'] == 'valid' else '❌ NOT READY'}",
            f"Validation Time: {self.validation_results['timestamp']}",
            "",
            "Component Status:"
        ]
        
        components = [
            ('Python Environment', self.validation_results['environment']['status']),
            ('Dependencies', self.validation_results['dependencies']['status']),
            ('SWE-bench Installation', self.validation_results['swe_bench']['status']),
            ('roocode Configuration', self.validation_results['roocode_config']['status']),
            ('Datasets', self.validation_results['datasets']['status']),
            ('Workspace Structure', self.validation_results['workspace']['status'])
        ]
        
        for name, status in components:
            icon = "✅" if status == 'valid' else "❌"
            summary_lines.append(f"  {icon} {name}: {status.upper()}")
        
        if self.validation_results['overall_status'] == 'valid':
            summary_lines.extend([
                "",
                "🎯 Ready for SWE-bench benchmarking with roocode SPARC!",
                "📋 Available tasks: " + str(self.validation_results['datasets'].get('lite_task_count', 0)),
                "🚀 Run: python3 swe_bench_orchestrator.py"
            ])
        else:
            summary_lines.extend([
                "",
                "⚠️ Issues must be resolved before benchmarking:",
                "1. Check the detailed validation report",
                "2. Fix any missing dependencies or configuration",
                "3. Re-run validation"
            ])
        
        return "\n".join(summary_lines)


def main():
    """Main execution function"""
    print("🔍 SWE-bench Environment Validator for roocode SPARC")
    print("=" * 60)
    
    # Initialize validator
    validator = EnvironmentValidator()
    
    # Run comprehensive validation
    results = validator.run_comprehensive_validation()
    
    # Print summary
    print("\n" + validator.generate_readiness_summary())
    
    # Return appropriate exit code
    return 0 if results['overall_status'] == 'valid' else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)