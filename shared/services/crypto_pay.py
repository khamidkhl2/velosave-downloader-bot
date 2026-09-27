import logging
import aiohttp
from typing import Optional, Dict, Any
from shared.config_base import shared_config

logger = logging.getLogger(__name__)

class CryptoPayService:
    def __init__(self):
        self.token = shared_config.CRYPTO_PAY_TOKEN
        self.base_url = (
            "https://testnet-pay.crypt.bot/api"
            if shared_config.CRYPTO_PAY_NET == "testnet"
            else "https://pay.crypt.bot/api"
        )

    def is_configured(self) -> bool:
        return bool(self.token and len(self.token) > 10)

    async def create_invoice(
        self,
        amount_usd: float,
        description: str,
        payload: str,
        bot_username: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Creates an invoice via CryptoPay API in fiat (USD) equivalent (payable in USDT, TON, BTC)
        """
        if not self.is_configured():
            return None

        url = f"{self.base_url}/createInvoice"
        headers = {"Crypto-Pay-API-Token": self.token}
        data = {
            "currency_type": "fiat",
            "fiat": "USD",
            "amount": str(amount_usd),
            "description": description,
            "payload": payload
        }
        if bot_username:
            data["paid_btn_name"] = "openBot"
            data["paid_btn_url"] = f"https://t.me/{bot_username}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    res = await response.json()
                    if res.get("ok"):
                        result = res.get("result", {})
                        return {
                            "invoice_id": str(result.get("invoice_id")),
                            "pay_url": result.get("bot_invoice_url") or result.get("mini_app_invoice_url"),
                            "status": result.get("status")
                        }
                    else:
                        logger.error(f"CryptoPay error: {res}")
        except Exception as e:
            logger.error(f"Failed to create CryptoPay invoice: {e}")
        return None

    async def check_invoice_status(self, invoice_id: str) -> Optional[str]:
        if not self.is_configured():
            return None

        url = f"{self.base_url}/getInvoices"
        headers = {"Crypto-Pay-API-Token": self.token}
        params = {"invoice_ids": invoice_id}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    res = await response.json()
                    if res.get("ok"):
                        items = res.get("result", {}).get("items", [])
                        if items:
                            return items[0].get("status")
        except Exception as e:
            logger.error(f"Failed to check CryptoPay invoice {invoice_id}: {e}")
        return None

crypto_pay = CryptoPayService()
