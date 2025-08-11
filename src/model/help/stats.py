from eth_account import Account
from typing import Optional, Tuple
from dataclasses import dataclass
from threading import Lock
from loguru import logger
from src.utils.config import Config
from src.model.onchain.web3_custom import Web3Custom


from src.utils.config import WalletInfo


class WalletStats:
    def __init__(self, config: Config, web3: Web3Custom):
        # Используем публичную RPC ноду Base
        self.w3 = web3
        self.config = config
        self._lock = Lock()

    async def get_wallet_stats(
        self, private_key: str, account_index: int
    ) -> Optional[bool]:
        """
        Получает статистику кошелька и сохраняет в конфиг

        Args:
            private_key: Приватный ключ кошелька
            account_index: Индекс аккаунта

        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            # Получаем адрес из приватного ключа
            account = Account.from_key(private_key)
            address = account.address

            # Получаем баланс
            balance = await self.w3.get_balance(address)
            balance_eth = balance.ether

            # Получаем количество транзакций (nonce)
            tx_count = await self.w3.web3.eth.get_transaction_count(address)

            wallet_info = WalletInfo(
                account_index=account_index,
                private_key=private_key,
                address=address,
                balance=float(balance_eth),
                transactions=tx_count,
            )

            with self._lock:
                self.config.WALLETS.wallets.append(wallet_info)

            logger.info(
                f"{account_index} | {address} | "
                f"Balance = {balance_eth:.4f} STT, "
                f"Transactions = {tx_count}"
            )

            return True

        except Exception as e:
            logger.error(f"Error getting wallet stats: {e}")
            return False

    def update_somnia_stats(self, private_key: str, final_points: str = None, rank: str = None, quests_completed: str = None):
        """
        Обновляет Somnia статистику для кошелька
        
        Args:
            private_key: Приватный ключ кошелька
            final_points: Финальные очки
            rank: Ранг пользователя
            quests_completed: Количество выполненных квестов
        """
        try:
            with self._lock:
                for wallet in self.config.WALLETS.wallets:
                    if wallet.private_key == private_key:
                        if final_points is not None:
                            wallet.final_points = final_points
                        if rank is not None:
                            wallet.rank = rank
                        if quests_completed is not None:
                            wallet.quests_completed = quests_completed
                        logger.info(f"Updated Somnia stats for wallet {wallet.address}")
                        break
        except Exception as e:
            logger.error(f"Error updating Somnia stats: {e}")

    def update_somnia_stats_by_address(self, wallet_address: str, final_points: str = None, rank: str = None, quests_completed: str = None):
        """
        Обновляет Somnia статистику для кошелька по адресу
        
        Args:
            wallet_address: Адрес кошелька
            final_points: Финальные очки
            rank: Ранг пользователя
            quests_completed: Количество выполненных квестов
        """
        try:
            with self._lock:
                found = False
                for wallet in self.config.WALLETS.wallets:
                    # Сравниваем адреса в нижнем регистре для надежности
                    if wallet.address.lower() == wallet_address.lower():
                        if final_points is not None:
                            wallet.final_points = final_points
                        if rank is not None:
                            wallet.rank = rank
                        if quests_completed is not None:
                            wallet.quests_completed = quests_completed
                        logger.info(f"Updated Somnia stats for wallet {wallet.address}: Points={final_points}, Rank={rank}, Quests={quests_completed}")
                        found = True
                        break
                
                if not found:
                    logger.warning(f"Wallet with address {wallet_address} not found in wallet stats")
                    
        except Exception as e:
            logger.error(f"Error updating Somnia stats by address: {e}")
