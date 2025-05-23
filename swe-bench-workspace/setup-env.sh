#!/bin/bash

# SWE-bench Environment Setup Script
# This script sets up the environment for running SWE-bench with roocode SPARC

set -e

echo "Setting up SWE-bench environment..."

# Check if required environment variables are set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Warning: GITHUB_TOKEN environment variable is not set"
    echo "Please set your GitHub Personal Access Token:"
    echo "export GITHUB_TOKEN=your_token_here"
fi

# Create necessary directories
mkdir -p logs
mkdir -p results

# Install SWE-bench if not already installed
if [ ! -d "SWE-bench" ]; then
    echo "Cloning SWE-bench repository..."
    git clone https://github.com/princeton-nlp/SWE-bench.git
fi

# Install dependencies
echo "Installing SWE-bench dependencies..."
cd SWE-bench
pip install -e .
cd ..

echo "Environment setup complete!"
echo "You can now run: python run-native-benchmark.py"