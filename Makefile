# Makefile for the backtesty project

# Use .PHONY to ensure commands run even if files with the same name exist.
.PHONY: help install clean download run

# Default command: `make` or `make help`
help:
	@echo "Available commands:"
	@echo "  make install          - Install project dependencies"
	@echo "  make download         - Download historical data for all pairs in config"
	@echo "  make run index=<n>    - Run backtest for the n-th pair in the config"
	@echo "  make run index=all    - Run backtest for all pairs in the config"
	@echo "  make clean            - Clean generated data (processed files and results)"

# Command to install dependencies from requirements.txt
install:
	@echo "📦 Installing dependencies..."
	@pip install -r requirements.txt
	@echo "✅ Dependencies installed."

# Command to download data
download:
	@echo "🌐 Downloading data..."
	@python scripts/fetch_bybit_data.py
	@echo "✅ Data download complete."

# Command to run the backtest. Defaults to 'all' if no index is provided.
index ?= all
run:
	@echo "🚀 Running backtest for index: ${index}..."
	@python main.py ${index}
	@echo "✅ Backtest run finished."

# Command to clean generated files
clean:
	@echo "🧹 Cleaning generated data..."
	@# Use -f to ignore errors if the directories or files don't exist
	@rm -f data/processed/*
	@rm -f data/result/*
	@echo "✅ Done."
