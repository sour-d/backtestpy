# Makefile for the backtesty project

# Use .PHONY to ensure commands run even if files with the same name exist.
.PHONY: help install clean download run visualize

# Default command: `make` or `make help`
help:
	@echo "Available commands:"
	@echo "  make install          - Install project dependencies"
	@echo "  make download         - Smart download data (skips existing files)"
	@echo "  make download force=true - Force re-download of all data"
	@echo "  make run              - Run backtest for all combinations in the config"
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
run:
	@echo "🚀 Running backtest..."
	@python main.py
	@echo "✅ Backtest run finished."

# Command to start the visualizer web server.
visualize:
	@echo "📈 Starting visualizer server..."
	@cd visualizer && npm run dev

# Command to clean generated files
clean:
	@echo "🧹 Cleaning generated data..."
	@# Use -f to ignore errors if the directories or files don't exist
	@rm -f data/processed/*
	@rm -f data/result/*
	@rm -f data/summary/*
	@rm -f data/raw/*
	@echo "✅ Done."
