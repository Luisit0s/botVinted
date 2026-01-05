def calculate_profit(buy_price: float, market_price: float):
    """
    Calcule le profit net et le ROI de manière réaliste.
    Prend en compte les frais de protection Vinted et une estimation de port.
    """
    # 1. Calcul des frais de protection acheteur (0.70€ + 5%)
    # C'est ce que l'acheteur paie en plus du prix affiché
    vinted_fees = 0.70 + (buy_price * 0.05)
    
    # 2. Frais de port (Estimation moyenne Mondial Relay)
    shipping_estimate = 3.28
    
    # 3. Investissement Total (Prix de l'article + frais + port)
    total_invested = buy_price + vinted_fees + shipping_estimate
    
    # 4. Profit Net (Prix du marché estimé - Investissement total)
    # Si market_price est 0, on considère le profit comme non calculable
    if market_price > 0:
        net_profit = market_price - total_invested
        roi = (net_profit / total_invested) * 100 if total_invested > 0 else 0
    else:
        net_profit = 0
        roi = 0

    return {
        "profit": round(net_profit, 2),
        "total_cost": round(total_invested, 2),
        "market_value": round(market_price, 2) if market_price > 0 else "Inconnue",
        "roi": round(roi, 2)
    }
