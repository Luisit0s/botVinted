def calculate_profit(buy_price: float, market_price: float):
    """
    Calcule le profit ET la rentabilité (ROI).
    """
    # 1. Calcul des frais (Protection 5% + 0.70€)
    fees = 0.70 + (buy_price * 0.05)
    
    # 2. Frais de port (Estimation standard)
    shipping = 3.79
    
    # 3. Ce que tu sors de ta poche (Prix TTC)
    total_invested = buy_price + fees + shipping
    
    # 4. Profit Net
    net_profit = market_price - total_invested
    
    # 5. ROI (Retour sur investissement en %)
    # Formule : (Profit / Investissement Total) * 100
    if total_invested > 0:
        roi = (net_profit / total_invested) * 100
    else:
        roi = 0

    return {
        "profit": round(net_profit, 2),
        "total_cost": round(total_invested, 2),
        "market_value": round(market_price, 2),
        "roi": round(roi, 2) # Le pourcentage de gain (ex: +45%)
    }