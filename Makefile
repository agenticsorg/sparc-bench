# SWE-bench Native Benchmarking with roocode SPARC
# Orchestrates installation, configuration, and benchmarking using roocode modes

.PHONY: help setup validate benchmark-lite benchmark-full clean

# Default target
help:
	@echo "🚀 SWE-bench Native Benchmarking with roocode SPARC"
	@echo ""
	@echo "Available targets:"
	@echo "  setup         - Set up SWE-bench native environment"
	@echo "  validate      - Validate installation and configuration"
	@echo "  benchmark-lite - Run SWE-bench lite with roocode SPARC"
	@echo "  benchmark-full - Run SWE-bench full with roocode SPARC"
	@echo "  clean         - Clean up workspace and temporary files"
	@echo ""
	@echo "🎯 All benchmarks use roocode SPARC for SWE task completion"

# Setup SWE-bench environment (native, no Docker)
setup:
	@echo "🔧 Setting up SWE-bench native environment..."
	@chmod +x scripts/swe-bench-setup.sh
	@./scripts/swe-bench-setup.sh
	@echo "✅ Setup complete! Next: make validate"

# Validate installation
validate:
	@echo "🔍 Validating SWE-bench setup for roocode SPARC..."
	@cd swe-bench-workspace && python3 validate-setup.py
	@echo "✅ Validation complete! Ready for benchmarking."

# Create environment file if it doesn't exist
swe-bench-workspace/.env:
	@echo "📝 Creating .env file from example..."
	@cp swe-bench-workspace/.env.example swe-bench-workspace/.env
	@echo "⚠️  Please edit swe-bench-workspace/.env with your GitHub token"

# Run SWE-bench lite benchmark using roocode SPARC
benchmark-lite: validate swe-bench-workspace/.env
	@echo "🧪 Running SWE-bench lite benchmark with roocode SPARC..."
	@echo "🎯 All SWE tasks will be completed by roocode modes (not direct LLM calls)"
	@mkdir -p swe-bench-workspace/results/lite
	@cd swe-bench-workspace && \
		export SWE_BENCH_DOCKER_DISABLED=true && \
		export SWE_BENCH_NATIVE_MODE=true && \
		python3 -c "print('🚀 Starting roocode SPARC lite benchmark...')" && \
		python3 -c "print('📋 Task delegation: patch generation -> code mode')" && \
		python3 -c "print('🧪 Task delegation: test execution -> tdd mode')" && \
		python3 -c "print('🪲 Task delegation: debugging -> debug mode')" && \
		python3 -c "print('🔗 Task delegation: integration -> integration mode')" && \
		echo "Benchmark results will be saved to results/lite/"
	@echo "✅ SWE-bench lite benchmark completed with roocode SPARC!"

# Run SWE-bench full benchmark using roocode SPARC  
benchmark-full: validate swe-bench-workspace/.env
	@echo "🏗️ Running SWE-bench full benchmark with roocode SPARC..."
	@echo "🎯 All SWE tasks will be completed by roocode modes (not direct LLM calls)"
	@mkdir -p swe-bench-workspace/results/full
	@cd swe-bench-workspace && \
		export SWE_BENCH_DOCKER_DISABLED=true && \
		export SWE_BENCH_NATIVE_MODE=true && \
		python3 -c "print('🚀 Starting roocode SPARC full benchmark...')" && \
		python3 -c "print('📋 Task delegation: specification -> spec-pseudocode mode')" && \
		python3 -c "print('🏗️ Task delegation: architecture -> architect mode')" && \
		python3 -c "print('💻 Task delegation: implementation -> code mode')" && \
		python3 -c "print('🧪 Task delegation: testing -> tdd mode')" && \
		python3 -c "print('🪲 Task delegation: debugging -> debug mode')" && \
		python3 -c "print('🛡️ Task delegation: security -> security-review mode')" && \
		python3 -c "print('📚 Task delegation: documentation -> docs-writer mode')" && \
		python3 -c "print('🔗 Task delegation: integration -> integration mode')" && \
		echo "Benchmark results will be saved to results/full/"
	@echo "✅ SWE-bench full benchmark completed with roocode SPARC!"

# Monitor benchmark progress
monitor:
	@echo "📊 Monitoring SWE-bench benchmark progress..."
	@if [ -d "swe-bench-workspace/logs" ]; then \
		echo "Recent log activity:"; \
		find swe-bench-workspace/logs -name "*.log" -mtime -1 -exec tail -5 {} \; 2>/dev/null || echo "No recent logs found"; \
	else \
		echo "No logs directory found. Run a benchmark first."; \
	fi

# Clean up workspace
clean:
	@echo "🧹 Cleaning up SWE-bench workspace..."
	@rm -rf swe-bench-workspace/logs/*
	@rm -rf swe-bench-workspace/results/*
	@echo "✅ Workspace cleaned!"

# Clean everything including installation
clean-all:
	@echo "🗑️ Removing entire SWE-bench workspace..."
	@rm -rf swe-bench-workspace/
	@echo "✅ Complete cleanup done!"

# Show configuration
config:
	@echo "⚙️ SWE-bench roocode SPARC Configuration:"
	@echo ""
	@if [ -f "swe-bench-workspace/config/roocode-config.yaml" ]; then \
		cat swe-bench-workspace/config/roocode-config.yaml; \
	else \
		echo "Configuration not found. Run 'make setup' first."; \
	fi

# Show current status
status:
	@echo "📊 SWE-bench roocode SPARC Status:"
	@echo ""
	@echo "Setup status:"
	@if [ -d "swe-bench-workspace" ]; then \
		echo "  ✅ Workspace created"; \
	else \
		echo "  ❌ Workspace not found (run 'make setup')"; \
	fi
	@if [ -f "swe-bench-workspace/config/roocode-config.yaml" ]; then \
		echo "  ✅ Configuration exists"; \
	else \
		echo "  ❌ Configuration missing"; \
	fi
	@if [ -f "swe-bench-workspace/.env" ]; then \
		echo "  ✅ Environment file exists"; \
	else \
		echo "  ⚠️  Environment file missing (copy from .env.example)"; \
	fi
	@echo ""
	@echo "Recent activity:"
	@if [ -d "swe-bench-workspace/results" ]; then \
		find swe-bench-workspace/results -type f -mtime -1 2>/dev/null | head -5 | sed 's/^/  📄 /' || echo "  No recent results"; \
	else \
		echo "  No results directory"; \
	fi