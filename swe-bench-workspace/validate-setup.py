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
