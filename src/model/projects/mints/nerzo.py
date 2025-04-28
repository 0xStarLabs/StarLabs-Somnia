import asyncio
import random
from loguru import logger
from web3 import Web3
from src.model.somnia_network.constants import SomniaProtocol
from src.utils.decorators import retry_async
from src.utils.constants import EXPLORER_URL_SOMNIA
from eth_account import Account
from src.model.onchain.web3_custom import Web3Custom


class Nerzo:
    def __init__(
        self, account_index: int, somnia_web3: Web3Custom, config: dict, wallet: Account
    ):
        self.account_index = account_index
        self.somnia_web3 = somnia_web3
        self.config = config
        self.wallet = wallet

    @retry_async(default_value=False)
    async def mint_nee(self):
        try:
            logger.info(f"{self.account_index} | Minting NEE NFT on Nerzo...")

            # NEE contract address
            contract_address = "0x939cCD6129561EFcBE8402a7159C1c09b9D34231"

            # Wallet address without 0x prefix in lowercase
            wallet_address_no_prefix = self.wallet.address[2:].lower()

            # Base payload with method ID 0x84bb1e42
            payload = (
                "0x84bb1e42"
                "000000000000000000000000"
                + wallet_address_no_prefix
                + "0000000000000000000000000000000000000000000000000000000000000001"
                "000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
                "0000000000000000000000000000000000000000000000000000000000000000"
                "00000000000000000000000000000000000000000000000000000000000000c0"
                "0000000000000000000000000000000000000000000000000000000000000160"
                "0000000000000000000000000000000000000000000000000000000000000080"
                "0000000000000000000000000000000000000000000000000000000000000000"
                "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
                "0000000000000000000000000000000000000000000000000000000000000000"
                "0000000000000000000000000000000000000000000000000000000000000000"
                "0000000000000000000000000000000000000000000000000000000000000000"
            )

            # Prepare transaction
            transaction = {
                "from": self.wallet.address,
                "to": self.somnia_web3.web3.to_checksum_address(contract_address),
                "value": 0,  # 0 STT as in the example transaction
                "nonce": await self.somnia_web3.web3.eth.get_transaction_count(
                    self.wallet.address
                ),
                "chainId": await self.somnia_web3.web3.eth.chain_id,
                "data": payload,
            }

            # Get dynamic gas parameters instead of hardcoded 30 Gwei
            gas_params = await self.somnia_web3.get_gas_params()
            transaction.update(gas_params)

            # Estimate gas
            gas_limit = await self.somnia_web3.estimate_gas(transaction)
            transaction["gas"] = gas_limit

            # Execute transaction
            tx_hash = await self.somnia_web3.execute_transaction(
                transaction,
                self.wallet,
                await self.somnia_web3.web3.eth.chain_id,
                EXPLORER_URL_SOMNIA,
            )

            if tx_hash:
                logger.success(f"{self.account_index} | Successfully minted NEE NFT")

            return True
        except Exception as e:
            random_sleep = random.randint(
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.account_index} | Error minting NEE NFT: {e}. Sleeping for {random_sleep} seconds..."
            )
            await asyncio.sleep(random_sleep)
            raise e

    @retry_async(default_value=False)
    async def mint_shannon(self):
        try:
            logger.info(f"{self.account_index} | Minting SHANNON NFT on Nerzo...")

            # SHANNON contract address
            contract_address = "0x715A73f6C71aB9cB32c7Cc1Aa95967a1b5da468D"

            # Wallet address without 0x prefix in lowercase
            wallet_address_no_prefix = self.wallet.address[2:].lower()

            # Base payload with method ID 0x84bb1e42
            payload = (
                "0x84bb1e42"
                "000000000000000000000000"
                + wallet_address_no_prefix
                + "0000000000000000000000000000000000000000000000000000000000000001"
                "000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
                "00000000000000000000000000000000000000000000000000038d7ea4c68000"
                "00000000000000000000000000000000000000000000000000000000000000c0"
                "0000000000000000000000000000000000000000000000000000000000000160"
                "0000000000000000000000000000000000000000000000000000000000000080"
                "0000000000000000000000000000000000000000000000000000000000000000"
                "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
                "0000000000000000000000000000000000000000000000000000000000000000"
                "0000000000000000000000000000000000000000000000000000000000000000"
                "0000000000000000000000000000000000000000000000000000000000000000"
            )

            # Prepare transaction with 0.001 STT value
            transaction = {
                "from": self.wallet.address,
                "to": self.somnia_web3.web3.to_checksum_address(contract_address),
                "value": Web3.to_wei(
                    0.001, "ether"
                ),  # 0.001 STT as in the example transaction
                "nonce": await self.somnia_web3.web3.eth.get_transaction_count(
                    self.wallet.address
                ),
                "chainId": await self.somnia_web3.web3.eth.chain_id,
                "data": payload,
            }

            # Get dynamic gas parameters
            gas_params = await self.somnia_web3.get_gas_params()
            transaction.update(gas_params)

            # Estimate gas
            gas_limit = await self.somnia_web3.estimate_gas(transaction)
            transaction["gas"] = gas_limit

            # Execute transaction
            tx_hash = await self.somnia_web3.execute_transaction(
                transaction,
                self.wallet,
                await self.somnia_web3.web3.eth.chain_id,
                EXPLORER_URL_SOMNIA,
            )

            if tx_hash:
                logger.success(
                    f"{self.account_index} | Successfully minted SHANNON NFT"
                )

            return True
        except Exception as e:
            random_sleep = random.randint(
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.account_index} | Error minting SHANNON NFT: {e}. Sleeping for {random_sleep} seconds..."
            )
            await asyncio.sleep(random_sleep)
            raise e
