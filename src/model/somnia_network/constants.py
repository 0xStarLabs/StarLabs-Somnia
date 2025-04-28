from dataclasses import dataclass
from typing import Protocol
from primp import AsyncClient
from eth_account import Account

from src.model.onchain.web3_custom import Web3Custom
from src.utils.config import Config


class SomniaProtocol(Protocol):
    """Protocol class for Somnia type hints to avoid circular imports"""

    account_index: int
    session: AsyncClient
    web3: Web3Custom
    config: Config
    wallet: Account
    discord_token: str
    twitter_token: str
    proxy: str

    # Инициализируем сервисы        
    somnia_login_token: str = ""

    async def get_account_info(self) -> dict | None: ...
    async def get_account_stats(self) -> dict | None: ...
    async def get_account_referrals(self) -> dict | None: ...
    async def request_faucet(self) -> bool: ...
    async def connect_socials(self) -> bool: ...
