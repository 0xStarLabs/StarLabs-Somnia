import asyncio
import random
from loguru import logger
from web3 import Web3
from src.model.somnia_network.constants import SomniaProtocol
from src.utils.decorators import retry_async
from src.utils.constants import EXPLORER_URL_SOMNIA
from eth_account import Account


class RandomTokenSender:
    def __init__(self, instance: SomniaProtocol):
        self.somnia = instance

    async def send_tokens(self):
        result = True
        balance = await self.somnia.web3.get_balance(self.somnia.wallet.address)
        if balance.wei == 0:
            logger.warning(f"{self.somnia.account_index} | No balance to send tokens")
            return False

        # Получаем количество транзакций из конфига
        min_txs, max_txs = self.somnia.config.SOMNIA_NETWORK.SOMNIA_TOKEN_SENDER.NUMBER_OF_SENDS
        num_transactions = random.randint(min_txs, max_txs)

        logger.info(
            f"{self.somnia.account_index} | Planning to send {num_transactions} transactions"
        )

        for i in range(num_transactions):
            # Определяем процент баланса для отправки
            min_percent, max_percent = (
                self.somnia.config.SOMNIA_NETWORK.SOMNIA_TOKEN_SENDER.BALANCE_PERCENT_TO_SEND
            )
            percent_to_send = random.uniform(min_percent, max_percent)

            # Определяем получателя на основе шанса отправки разработчикам
            dev_chance = self.somnia.config.SOMNIA_NETWORK.SOMNIA_TOKEN_SENDER.SEND_ALL_TO_DEVS_CHANCE

            if random.randint(1, 100) <= dev_chance:
                # Отправляем на кошелек разработчика
                recipient = random.choice(DEVS_RECIPIENTS)
                recipient = Web3.to_checksum_address(recipient)
                logger.info(
                    f"{self.somnia.account_index} | Transaction {i+1}/{num_transactions}: Sending to dev wallet {recipient}"
                )
            else:
                # Генерируем случайный приватный ключ
                private_key = Account.create().key

                # Создаем аккаунт из приватного ключа и получаем адрес
                random_account = Account.from_key(private_key)
                recipient = random_account.address

                logger.info(
                    f"{self.somnia.account_index} | Transaction {i+1}/{num_transactions}: Sending to random wallet {recipient}"
                )

            # Вызываем метод для фактической отправки
            result = await self._send(recipient, percent_to_send)

            # Небольшая пауза между транзакциями
            await asyncio.sleep(
                random.uniform(
                    self.somnia.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[0],
                    self.somnia.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[1],
                )
            )

        return result

    @retry_async(default_value=False)
    async def _send(self, recipient, percent_to_send):
        try:
            # Получаем баланс кошелька
            wallet_address = self.somnia.wallet.address
            balance = await self.somnia.web3.get_balance(wallet_address)

            # Рассчитываем сумму для отправки (процент от баланса)
            amount_ether = balance.ether * percent_to_send / 100

            # Округляем до 4 знаков после запятой для естественности
            amount_ether = round(amount_ether, 4)

            # Конвертируем обратно в wei для транзакции
            amount_to_send = self.somnia.web3.convert_to_wei(amount_ether, 18)

            # Оставляем небольшой запас на газ (95% от суммы)
            amount_to_send = int(amount_to_send * 0.95)

            logger.info(
                f"{self.somnia.account_index} | Starting send {amount_ether:.4f} "
                f"tokens to {recipient}, {percent_to_send:.4f}% of balance..."
            )

            # Формируем данные транзакции
            tx_data = {
                "to": recipient,
                "value": amount_to_send,
            }

            # Добавляем газ
            try:
                gas_limit = await self.somnia.web3.estimate_gas(tx_data)
                tx_data["gas"] = gas_limit
            except Exception as e:
                raise Exception(f"Gas estimation failed: {e}.")

            # Выполняем транзакцию
            tx_hash = await self.somnia.web3.execute_transaction(
                tx_data=tx_data,
                wallet=self.somnia.wallet,
                chain_id=50312,  # Chain ID для Somnia из constants.py
                explorer_url=EXPLORER_URL_SOMNIA,
            )

            if tx_hash:
                logger.success(
                    f"{self.somnia.account_index} | Successfully sent {amount_ether:.4f} "
                    f"tokens to {recipient}. TX: {EXPLORER_URL_SOMNIA}{tx_hash}"
                )
                return True
            else:
                raise Exception(f"{self.somnia.account_index} | Transaction failed")

        except Exception as e:
            random_pause = random.randint(
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.somnia.account_index} | Send tokens error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise


DEVS_RECIPIENTS = [
    "0xDA1feA7873338F34C6915A44028aA4D9aBA1346B",
    "0x018604C67a7423c03dE3057a49709aaD1D178B85",
    "0xcF8D30A5Ee0D9d5ad1D7087822bA5Bab1081FdB7",
    "0x95222290DD7278Aa3Ddd389Cc1E1d165CC4BAfe5",
]
