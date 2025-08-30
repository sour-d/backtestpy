from src.module.exchange.exchange import Exchange

exchange = Exchange()

# Show USDT balance
print("USDT balance:", exchange.fetch_balance("USDT"))

# Test unified place_order method with CCXT
print("\nTesting unified place_order with CCXT...")

print("\n=== Test 2: Limit order with stop-loss (OrderConfig) ===")
try:
    bracket_order = exchange.create_limit_order(
        symbol="BTC/USDT",
        side="BUY",
        amount=0.001,
        price=120000.0,
        stop_loss=106000.0,
        client_order_id="test_bracket_002",
    )
    print("Bracket order response:", bracket_order)
except Exception as e:
    print("Bracket order error:", e)
