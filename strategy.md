### MovingAverageStrategy: Buy, Sell, and Liquidate Logic

This document outlines the conditions and actions for initiating buy and sell orders, as well as liquidating existing long and short positions within the `MovingAverageStrategy` class, simplified to exclude `limitPriceGap` considerations.

---

#### 1. Buy Logic (`buy()` method)

This method attempts to place a "Buy" order based on specific technical conditions.

**Conditions for Buy Order:**

A buy order is considered if **all** the following conditions are met for the current trading period (`today`) and the previous period (`yesterday`):

*   `today.close > today.ma20high`: The current closing price is above the 20-period moving average of the high.
*   `today.body > 0`: The current candle has a positive body (closing price is higher than opening price).
*   `yesterday.body > 0`: The previous candle also had a positive body.
*   `today.superTrendDirection === "Buy"`: The SuperTrend indicator signals a "Buy" direction.

**Order Placement Details:**

If all conditions are met:

1.  **`buyingPrice` Calculation:** The `buyingPrice` is set to `today.close`.
2.  **`initialStopLoss` Calculation:** The `initialStopLoss` is set to `today.ma20low` (20-period moving average of the low).
3.  **Stop Loss Validation:** A check `if (initialStopLoss >= buyingPrice) return;` ensures that the calculated stop loss is below the buying price. If not, the buy operation is aborted.
4.  **`riskForOneStock` Calculation:** The risk per stock is calculated as `buyingPrice - initialStopLoss`.
5.  **`placeOrder` Call:** The `placeOrder` method is called with the calculated `riskForOneStock`, `buyingPrice`, a quantity of `0` (likely determined internally by `placeOrder` based on capital and risk), and the type "Buy". The `true` argument likely indicates a new position.

---

#### 2. Sell Logic (`sell()` method)

This method attempts to place a "Sell" (short) order based on specific technical conditions.

**Conditions for Sell Order:**

A sell order is considered if **all** the following conditions are met for the current trading period (`today`) and the previous period (`yesterday`):

*   `today.close < today.ma20low`: The current closing price is below the 20-period moving average of the low.
*   `today.body < 0`: The current candle has a negative body (closing price is lower than opening price).
*   `yesterday.body < 0`: The previous candle also had a negative body.
*   `today.superTrendDirection === "Sell"`: The SuperTrend indicator signals a "Sell" direction.

**Order Placement Details:**

If all conditions are met:

1.  **`sellingPrice` Calculation:** The `sellingPrice` is set to `this.stock.now().close`.
2.  **`initialStopLoss` Calculation:** The `initialStopLoss` is set to `today.ma20high` (20-period moving average of the high).
3.  **Stop Loss Validation:** A check `if (initialStopLoss <= sellingPrice) return;` ensures that the calculated stop loss is above the selling price. If not, the sell operation is aborted.
4.  **`riskForOneStock` Calculation:** The risk per stock is calculated as `initialStopLoss - sellingPrice`.
5.  **`placeOrder` Call:** The `placeOrder` method is called with the calculated `riskForOneStock`, `sellingPrice`, a quantity of `0`, and the type "Sell". The `true` argument likely indicates a new position.

---

#### 3. Long Position Liquidation (`longSquareOff()` method)

This method handles the liquidation (selling) of an existing long position. It checks for conditions that suggest a reversal or a need to exit the long trade.

**Conditions for Squaring Off a Long Position:**

The method checks for three distinct sets of conditions. If any of these sets are met, the long position is exited:

*   **Condition Set 1 (MA20high Crossover and Negative Body):**
    *   `today.ma20high > today.close`: The 20-period moving average of the high is above the current closing price.
    *   `today.ma20high > today.open`: The 20-period moving average of the high is also above the current opening price.
    *   `today.body < 0`: The current candle has a negative body.
*   **Condition Set 2 (Consecutive MA20high Crossover and Negative Body):**
    *   `yesterday.ma20high > yesterday.close`: The previous day's 20-period moving average of the high was above its closing price.
    *   `today.ma20high > today.close`: The current day's 20-period moving average of the high is above its closing price.
    *   `today.body < 0`: The current candle has a negative body.
*   **Condition Set 3 (SuperTrend Sell Signal):**
    *   `today.superTrendDirection === "Sell"`: The SuperTrend indicator signals a "Sell" direction.

**Action on Condition Met:**

If any of the above condition sets are met:

1.  **`forceExit("Sell")`:** The `forceExit` method is called with "Sell", indicating an immediate exit from the long position.
2.  **`return this.sell()`:** After forcing the exit, the `sell()` method is called. This might be to attempt to initiate a new short position immediately after closing the long one, or it could be a redundant call if `forceExit` already handles the actual trade execution.

---

#### 4. Short Position Liquidation (`shortSquareOff()` method)

This method handles the liquidation (buying back) of an existing short position. It checks for conditions that suggest a reversal or a need to exit the short trade.

**Conditions for Squaring Off a Short Position:**

The method checks for three distinct sets of conditions. If any of these sets are met, the short position is exited:

*   **Condition Set 1 (MA20low Crossover and Positive Body):**
    *   `today.close > today.ma20low`: The current closing price is above the 20-period moving average of the low.
    *   `today.open > today.ma20low`: The current opening price is also above the 20-period moving average of the low.
    *   `today.body > 0`: The current candle has a positive body.
*   **Condition Set 2 (Consecutive MA20low Crossover and Positive Body):**
    *   `yesterday.close > yesterday.ma20low`: The previous day's closing price was above its 20-period moving average of the low.
    *   `today.close > today.ma20low`: The current day's closing price is above its 20-period moving average of the low.
    *   `today.body > 0`: The current candle has a positive body.
*   **Condition Set 3 (SuperTrend Buy Signal):**
    *   `today.superTrendDirection === "Buy"`: The SuperTrend indicator signals a "Buy" direction.

**Action on Condition Met:**

If any of the above condition sets are met:

1.  **`forceExit("Buy")`:** The `forceExit` method is called with "Buy", indicating an immediate exit from the short position.
2.  **`return this.buy()`:** After forcing the exit, the `buy()` method is called. Similar to `longSquareOff`, this might be to attempt to initiate a new long position immediately after closing the short one, or it could be a redundant call.

---

#### 5. Indicators Used and Their Logic

The `MovingAverageStrategy` relies on the following technical indicators:

*   **MA20high (20-period Moving Average of Highs):**
    *   **Logic:** This is a simple moving average calculated over the past 20 periods (e.g., 20 days, 20 hours) using the *high* price of each period. It smooths out price data to identify the average high price over the specified period.
    *   **Usage in Strategy:** Used as a dynamic resistance level or a benchmark for bullish momentum. For instance, a close above `ma20high` suggests strength. It also serves as an `initialStopLoss` for short positions.

*   **MA20low (20-period Moving Average of Lows):**
    *   **Logic:** Similar to `ma20high`, but calculated using the *low* price of each period over the past 20 periods. It smooths out price data to identify the average low price over the specified period.
    *   **Usage in Strategy:** Used as a dynamic support level or a benchmark for bearish momentum. For instance, a close below `ma20low` suggests weakness. It also serves as an `initialStopLoss` for long positions.

*   **Candle Body (`body`):
    *   **Logic:** The "body" of a candlestick represents the difference between its opening and closing price.
        *   A `body > 0` (positive body) indicates a bullish candle where the closing price is higher than the opening price.
        *   A `body < 0` (negative body) indicates a bearish candle where the closing price is lower than the opening price.
    *   **Usage in Strategy:** Used to confirm the direction of price movement within a period. For example, a positive body reinforces a bullish signal, while a negative body reinforces a bearish signal. The strategy often looks for consecutive positive or negative bodies to confirm trend strength.

*   **SuperTrend (`superTrendDirection`):
    *   **Logic:** The SuperTrend indicator is a trend-following overlay indicator that provides clear "Buy" or "Sell" signals. Its calculation is based on the following steps and relies on the Average True Range (ATR):

        1.  **`src` (Source Price):** Calculated as the midpoint of the current candle: `(High + Low) / 2`.
        2.  **Average True Range (ATR):** This is a measure of market volatility. It's the greatest of the following:
            *   Current High minus Current Low
            *   Absolute value of Current High minus Previous Close
            *   Absolute value of Current Low minus Previous Close
            ATR is typically smoothed over a period (e.g., 10 or 14 periods) using a moving average. The `superTrend.js` code assumes `quote.atr` is pre-calculated, meaning ATR is an input to the SuperTrend calculation.
        3.  **Basic Upper and Lower Bands:**
            *   `Upper Band = src + (Multiplier * ATR)`
            *   `Lower Band = src - (Multiplier * ATR)`
            The `Multiplier` is a configurable value (e.g., 3).
        4.  **Final Upper and Lower Bands (Dynamic Adjustment):** These bands are adjusted dynamically to prevent them from moving against the trend too quickly.
            *   The `lowerBand` will only move up or stay flat if the current `lowerBand` is greater than the `prevLowerBand` or if the `prevClose` was below the `prevLowerBand`. Otherwise, it retains its `prevLowerBand` value.
            *   The `upperBand` will only move down or stay flat if the current `upperBand` is less than the `prevUpperBand` or if the `prevClose` was above the `prevUpperBand`. Otherwise, it retains its `prevUpperBand` value.
        5.  **Trend Direction Determination:**
            *   If the `prevSuperTrend` was the `prevUpperBand` (indicating a downtrend), the `direction` changes to "Buy" if the `currentClose` crosses above the `upperBand`. Otherwise, it remains "Sell".
            *   If the `prevSuperTrend` was the `prevLowerBand` (indicating an uptrend), the `direction` changes to "Sell" if the `currentClose` crosses below the `lowerBand`. Otherwise, it remains "Buy".
        6.  **SuperTrend Value:** The final SuperTrend value is either the `finalLowerBand` (if the direction is "Buy") or the `finalUpperBand` (if the direction is "Sell").

    *   **Usage in Strategy:** Acts as a primary trend filter and confirmation tool. It's a crucial component for both initiating new trades and for liquidating existing positions, ensuring trades are aligned with the prevailing trend.
