---
applyTo: '**'
---

# Copilot Instructions for This Project

This project is a **Python-based backtesting and live trading framework**.
All AI-generated code must follow these principles, conventions, and architectural guidelines.

---

## 🔑 General Coding Principles

* Follow **SOLID principles**:

  * **S**ingle Responsibility → each module/class should do one thing.
  * **O**pen/Closed → new features should extend existing code, not modify core logic unnecessarily.
  * **L**iskov Substitution → strategy/engine subclasses must remain interchangeable with their base class.
  * **I**nterface Segregation → keep interfaces small (no “god classes”).
  * **D**ependency Inversion → depend on abstractions (base classes/interfaces), not implementations.
* Follow **PEP8** strictly.
* Use **type hints** everywhere (`mypy` friendly).
* Add **docstrings** to all public classes/methods/functions (`Google` or `NumPy` style).
* Functions/methods should ideally be **<30 lines**; refactor if longer.
* Use **logging** (`utils/logger.py`) instead of `print`.
* Write **unit-testable code** (avoid hardcoded dependencies).

---

## 📂 Project Structure & Responsibilities

### `src/main.py`, `src/paper_main.py`

* Entry points for running **live trading** or **paper trading/backtests**.
* Should **only orchestrate** → never contain business logic.
* Import engines/strategies from `module/`.

---

### `module/data_manager/`

* Handles **market data ingestion** (historical & live).
* Each data manager must extend `data_manager_base.py`.
* Keep separation:

  * `historical_data_manager.py` → loads candles from storage/CSV/API.
  * `live_data_manager.py` → streams live market data.
* Should not handle portfolio or strategy logic.

---

### `module/engine/`

* Coordinates the **core trading loop**.
* `backtest_engine.py` → simulates strategies against historical data.
* `paper_engine.py` → simulates in near-real-time with live data feeds.
* Future extension: `live_engine.py` → full live trading execution.
* Engines should:

  * Take a `Strategy`, `Portfolio`, and `DataManager` as dependencies.
  * Call `strategy.generate_signals()`.
  * Update the `Portfolio` based on signals.
  * Record performance stats.

---

### `module/env/`

* Contains **trading environments** (integration points, e.g., OpenAI Gym-style).
* Must not duplicate engine/strategy logic.
* Responsible for **wrapping environment state** for RL or simulation.

---

### `module/exchange/`

* Handles **exchange-specific execution logic** (order placement, cancellation).
* Keep a clean abstraction so it can be replaced (Bybit, Binance, paper, etc.).

---

### `module/indicators/`

* Contains **technical indicators** (SMA, EMA, Supertrend, etc.).
* All indicators must extend `base.py` and expose a **uniform API**:

  ```python
  class IndicatorBase(ABC):
      @abstractmethod
      def calculate(self, data: pd.DataFrame) -> pd.Series:
          ...
  ```
* `factory.py` → must be used to build indicators dynamically (avoid importing directly everywhere).

---

### `module/portfolio/`

* Handles **position sizing, PnL calculation, order tracking**.
* Portfolio must:

  * Maintain account balance.
  * Handle fills and slippage.
  * Provide risk management hooks.
* Strategies must never directly manipulate portfolio state.

---

### `module/storage_manager/`

* Responsible for **storing/retrieving data** (files, DB, cloud).
* Always extend `storage_manager_base.py`.
* Keep it separate from trading logic.

---

### `module/strategies/`

* Contains all **trading strategies**.
* All strategies must extend `base_strategy.py`:

  ```python
  class BaseStrategy(ABC):
      @abstractmethod
      def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
          ...
  ```
* Examples: SMA crossover, MACD, Multi-timeframe momentum.
* Strategies should:

  * Only read data and emit **signals** (`buy/sell/hold`).
  * Never update portfolio directly.
  * Never fetch data directly.

---

### `utils/`

* Contains **helpers, loggers, event system**.
* `logger.py` → the only place where logging should be configured.
* `event_emitter.py` → provides event-driven hooks between modules.
* Keep **stateless utility functions** here (avoid business logic).

---

## 🧪 Testing Guidelines

* Use `pytest`.
* Place tests under `tests/` (mirror the `module/` structure).
* Cover:

  * Strategy signal correctness.
  * Portfolio updates (PnL, positions).
  * Engine loops (backtest execution).
  * Data integrity (historical/live).
* Aim for **>85% test coverage**.

---

## ⚡ Performance

* Use **NumPy/pandas vectorization** for computations.
* Avoid Python loops where possible.
* Optimize only where bottlenecks are proven (use profiling).

---

## 🔒 Error Handling

* Never silently fail.
* Raise custom exceptions (e.g., `DataManagerError`, `StrategyError`).
* Catch exceptions at the engine level, log them, and continue gracefully.

---

## ✅ Copilot Must

1. Extend existing base classes instead of rewriting logic.
2. Place new code in the **correct folder**.
3. Write docstrings + type hints for every function.
4. Follow **separation of concerns** (no strategy logic in engines, no portfolio logic in strategies).
5. Use the existing **logger** for all logs.
