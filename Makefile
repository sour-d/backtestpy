# Makefile for the backtesty project

# Use .PHONY to ensure commands run even if files with the same name exist.
.PHONY: help install clean download run visualize start

# Default command: `make` or `make help`
help:
	@echo "Available commands:"
	@echo "  make install          - Install project dependencies"
	@echo "  make download         - Smart download data (skips existing files)"
	@echo "  make download force=true - Force re-download of all data"
	@echo "  make run              - Run backtest for all combinations in the config"
	@echo "  make live             - Run the live trading bot"
	@echo "  make health-check     - Run a quick health check of the live trading system"
	@echo "  make visualize        - Start the web server to visualize results"
	@echo "  make clean            - Clean generated data (processed files and results)"

# Command to install dependencies from requirements.txt
install:
	@echo "📦 Installing dependencies..."
	@pip install -r requirements.txt
	@echo "✅ Dependencies installed."

# Command to download data. Use `make download force=true` to force.
force ?= false
download:
	@echo "🌐 Downloading data (force=${force})..."
	@if [ "${force}" = "true" ]; then \
		python download_data.py --force; \
	else \
		python download_data.py; \
	fi
	@echo "✅ Data download complete."

# Command to run the backtest.
backtest:
	@echo "🚀 Running backtest..."
	@python src/main.py
	@echo "✅ Backtest run finished."

# command for live trading
live:
	@echo "🚀 Starting live trading..."
	@python src/live_main.py
	@echo "✅ Live trading started."

# command for health check
health-check:
	@echo "👩‍⚕️ Running health check..."
	@python src/health_check.py
	@echo "✅ Health check finished."

# Command to start the visualizer web server.
visualize:
	@echo "📈 Starting visualizer server..."
	@cd visualizer && npm run dev

start-dev:
	@echo "🚀 Starting development server and ping script..."
	@cd visualizer && PORT=${PORT:-3000} npm run dev &
	@sleep 5 # Give the server a moment to start
	@python src/ping_server.py &
	@echo "✅ Development server and ping script started."

# Command to clean generated files
clean:
	@echo "🧹 Cleaning generated data..."
	@# Use -f to ignore errors if the directories or files don't exist
	@rm -fr data/live/*
	@rm -fr data/backtest/*
	@rm -fr logs/*
	@echo "✅ Done."

setup:
	@echo "Setting up for Backtesty..."
	@pip install -r requirements.txt
	@cd visualizer && yarn install
	@mkdir -p data/live data/backtest logs
	@echo "✅ Setup complete."


