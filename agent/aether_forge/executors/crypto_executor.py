"""
🪙 Aether Crypto Intelligence
=============================
External API Wrapper for CoinGecko.
Pattern: Command.
"""

import logging
from typing import Any, Dict, Optional
from ..registry import AetherSuperpower

logger = logging.getLogger("🧬 CryptoExecutor")

class AetherCoinGeckoExecutor(AetherSuperpower):
    """
    Fetches real-time crypto data.
    Requires an httpx.AsyncClient instance in context['client'].
    """
    
    async def execute(self, args: Dict[str, Any]) -> Any:
        client = self.context.get('client')
        if not client:
            return {"error": "Internal Fault: HTTP Client not injected into context."}

        coins = args.get("coin_id", "bitcoin")
        # Handle both string and list for flexibility
        coin_list = [coins] if isinstance(coins, str) else coins
        vs_currency = args.get("vs_currency", "usd")

        try:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": ",".join(coin_list),
                    "vs_currencies": vs_currency,
                    "include_24hr_change": "true",
                    "include_market_cap": "true"
                }
            )
            resp.raise_for_status()
            data = resp.json()
                
            refined = {}
            for coin, val in data.items():
                change = val.get(f"{vs_currency}_24h_change", 0)
                refined[coin.upper()] = {
                    "Price": f"{val.get(vs_currency, 0):,.2f} {vs_currency.upper()}",
                    "Trend_24h": f"{'🟢' if change > 0 else '🔴'} {change:.2f}%",
                    "MarketCap": f"{val.get(f'{vs_currency}_market_cap', 0)/1e9:.1f}B",
                    "trend_data": [0.1, 0.4, 0.3, 0.8, 0.9, 0.7, 1.0] # High-fidelity mock
                }
            
            # Metadata for the Aether visualizer
            if refined:
                first_coin = list(refined.keys())[0]
                refined["primary_trend"] = refined[first_coin]["trend_data"]

            return refined
        except Exception as e:
            logger.error(f"❌ CoinGecko API failure: {e}")
            return {"error": f"Failed to retrieve crypto data: {str(e)}"}
