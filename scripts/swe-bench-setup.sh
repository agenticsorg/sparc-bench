#!/bin/bash

# SWE-bench Native Setup Script for roocode SPARC
# This script sets up SWE-bench without Docker for benchmarking the roocode system

set -e

echo "🚀 Setting up SWE-bench (Native Mode) for roocode SPARC benchmarking..."

# Check requirements
echo "📋 Checking system requirements..."
python3 --version || { echo "❌ Python 3.8+ required"; exit 1; }
git --version || { echo "❌ Git required"; exit 1; }

# Create workspace directories
echo "📁 Creating workspace directories..."
mkdir -p swe-bench-workspace/{datasets,logs,results,config}

# Clone SWE-bench repository
echo "📦 Cloning SWE-bench repository..."
if [ ! -d "swe-bench-workspace/SWE-bench" ]; then
    git clone https://github.com/SWE-bench/SWE-bench.git swe-bench-workspace/SWE-bench
fi

# Install SWE-bench dependencies (native mode)
echo "🔧 Installing SWE-bench dependencies (native mode)..."
cd swe-bench-workspace/SWE-bench
pip install -e . --no-deps
pip install datasets transformers jsonlines tqdm

# Create roocode configuration
echo "⚙️ Creating roocode configuration..."
cd ../../
cat > swe-bench-workspace/config/roocode-config.yaml << EOF
# roocode SPARC Configuration for SWE-bench
github_token: '${GITHUB_TOKEN:-your_github_token_here}'
benchmark_mode: 'native'
docker_enabled: false
agent_system: 'roocode_sparc'

# roocode mode assignments for SWE tasks
task_routing:
  patch_generation: 'code'
  test_execution: 'tdd' 
  code_analysis: 'debug'
  security_review: 'security-review'
  integration: 'integration'
  
# Benchmark settings
swe_bench:
  lite_enabled: true
  full_enabled: true
  max_concurrent_tasks: 4
  timeout_minutes: 30

# Logging and monitoring
logging:
  level: 'INFO'
  log_dir: './logs'
  metrics_enabled: true
EOF

# Create environment configuration
echo "🔐 Creating environment configuration..."
cat > swe-bench-workspace/.env.example << EOF
# SWE-bench Environment Configuration
# Copy to .env and fill in your values

GITHUB_TOKEN=your_github_token_here
ROOCODE_API_ENDPOINT=your_roocode_endpoint
SWE_BENCH_DOCKER_DISABLED=true
SWE_BENCH_NATIVE_MODE=true
EOF

# Create validation script
echo "✅ Creating validation script..."
cat > swe-bench-workspace/validate-setup.py << 'EOF'
#!/usr/bin/env python3
"""
SWE-bench Native Setup Validation
Validates that SWE-bench is properly configured for roocode SPARC
"""

import sys
import os
import yaml
from pathlib import Path

def validate_setup():
    print("🔍 Validating SWE-bench native setup for roocode SPARC...")
    
    # Check workspace structure
    workspace = Path(".")
    required_dirs = ["datasets", "logs", "results", "config", "SWE-bench"]
    
    for dir_name in required_dirs:
        if not (workspace / dir_name).exists():
            print(f"❌ Missing directory: {dir_name}")
            return False
        print(f"✅ Found directory: {dir_name}")
    
    # Check configuration
    config_file = workspace / "config" / "roocode-config.yaml"
    if not config_file.exists():
        print("❌ Missing roocode-config.yaml")
        return False
    
    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        required_keys = ["benchmark_mode", "docker_enabled", "agent_system"]
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing config key: {key}")
                return False
            print(f"✅ Found config key: {key}")
        
        # Validate native mode
        if config["docker_enabled"]:
            print("❌ Docker should be disabled for native mode")
            return False
        
        if config["agent_system"] != "roocode_sparc":
            print("❌ Agent system should be 'roocode_sparc'")
            return False
            
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False
    
    # Check SWE-bench installation
    try:
        sys.path.insert(0, str(workspace / "SWE-bench"))
        import swebench
        print("✅ SWE-bench package available")
    except ImportError as e:
        print(f"❌ SWE-bench import failed: {e}")
        return False
    
    print("🎉 Setup validation complete! Ready for roocode SPARC benchmarking.")
    return True

if __name__ == "__main__":
    success = validate_setup()
    sys.exit(0 if success else 1)
EOF

chmod +x swe-bench-workspace/validate-setup.py

# Run validation
echo "🔍 Running setup validation..."
cd swe-bench-workspace
python3 validate-setup.py

echo ""
echo "✨ SWE-bench native setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Copy .env.example to .env and add your GitHub token"
echo "   2. Review roocode-config.yaml and adjust settings"
echo "   3. Use roocode SPARC orchestrator to run benchmarks:"
echo "      - new_task to 'sparc' mode for benchmark coordination"
echo "      - All SWE tasks will be routed through roocode modes"
echo "   4. Monitor results in swe-bench-workspace/results/"
echo ""
echo "🎯 Ready to benchmark roocode SPARC system on SWE-bench!"