# Auto-generated tool: compute_rsi
# Created: 2026-02-08T08:08:33.049649
# Approved by: cli_user
# Risk Tier: SAFE

from langchain_core.tools import tool

@tool
def compute_rsi(prices: list, period: int) -> str:
    """
    Calculates Relative Strength Index (RSI) of an asset's price movement
    
    Args:
        prices: List of historical prices
        period: Time period for RSI calculation
    
    Returns:
        Result message as string
    """
    try:
        gains = [p - p_prev for p, p_prev in zip(prices[1:], prices[:-1]) if p > p_prev]
        losses = [-p + p_prev for p, p_prev in zip(prices[1:], prices[:-1]) if p < p_prev]
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        return f'RSI: {rsi:.2f} for period {period}'
    except Exception as e:
        return f'ERROR: {str(e)}'

