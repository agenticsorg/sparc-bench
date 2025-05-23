#!/bin/bash

# SWE-bench Environment Setup Script
# Configures environment variables without hardcoding values

set -e

echo "🔧 Setting up SWE-bench environment configuration..."

# Source parent .env file if it exists
if [ -f "../.env" ]; then
    echo "📄 Loading environment from parent .env file..."
    source "../.env"
else
    echo "⚠️  No parent .env file found, using environment defaults"
fi

# Validate required environment variables
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN not found in environment"
    echo "   Please set GITHUB_TOKEN in parent .env file or environment"
    exit 1
fi

echo "✅ GITHUB_TOKEN found in environment"

# Create .env file with environment variable references
cat > .env << EOF
# SWE-bench Environment Configuration
# Values sourced from environment variables

# GitHub token for API access (from environment)
GITHUB_TOKEN=\${GITHUB_TOKEN}

# roocode SPARC configuration
ROOCODE_API_ENDPOINT=\${ROOCODE_API_ENDPOINT:-http://localhost:8080}

# SWE-bench native mode settings
SWE_BENCH_DOCKER_DISABLED=true
SWE_BENCH_NATIVE_MODE=true

# Workspace paths (auto-detected)
SWE_BENCH_WORKSPACE=\$(pwd)
PYTHONPATH=\$(pwd)/SWE-bench:\$PYTHONPATH
EOF

echo "✅ Environment configuration created"
echo "🔐 GitHub token will be loaded from environment variables"
echo "📁 Workspace paths will be auto-detected"

# Export environment variables for current session
export SWE_BENCH_DOCKER_DISABLED=true
export SWE_BENCH_NATIVE_MODE=true
export SWE_BENCH_WORKSPACE=$(pwd)
export PYTHONPATH=$(pwd)/SWE-bench:$PYTHONPATH

echo "🚀 Environment setup complete!"
echo ""
echo "Current environment:"
echo "   GITHUB_TOKEN: ${GITHUB_TOKEN:0:7}... (masked)"
echo "   SWE_BENCH_WORKSPACE: $SWE_BENCH_WORKSPACE"
echo "   SWE_BENCH_NATIVE_MODE: $SWE_BENCH_NATIVE_MODE"