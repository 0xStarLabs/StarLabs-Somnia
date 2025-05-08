import asyncio
import random
from loguru import logger
from web3 import Web3
from src.model.somnia_network.constants import SomniaProtocol
from src.utils.decorators import retry_async
from src.utils.constants import EXPLORER_URL_SOMNIA
from eth_account import Account
from src.model.onchain.web3_custom import Web3Custom


PAYLOAD = "0x6080604052737500a83df2af99b2755c47b6b321a8217d876a856000806101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff160217905550652d79883d20003410156100a1576040517f08c379a000000000000000000000000000000000000000000000000000000000815260040161009890610170565b60405180910390fd5b60008054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff166108fc652d79883d20009081150290604051600060405180830381858888f1935050505015801561010d573d6000803e3d6000fd5b50610190565b600082825260208201905092915050565b7f496e73756666696369656e74206465706c6f796d656e74206665650000000000600082015250565b600061015a601b83610113565b915061016582610124565b602082019050919050565b600060208201905081810360008301526101898161014d565b9050919050565b61016b8061019f6000396000f3fe608060405234801561001057600080fd5b50600436106100365760003560e01c80634690484014610038578063a8f3225114610059575b600080fd5b610043610074565b60405161004d91906100e6565b60405180910390f35b61006161009b565b60405161006b9190610113565b60405180910390f35b60008054906101000a900473ffffffffffffffffffffffffffffffffffffffff1681565b652d79883d200081565b600073ffffffffffffffffffffffffffffffffffffffff82169050919050565b60006100cc826100a5565b9050919050565b6100dc816100c5565b82525050565b60006020820190506100f760008301846100d7565b92915050565b6000819050919050565b61011081610101565b82525050565b600060208201905061012b6000830184610107565b9291505056fea2646970667358221220d08b6ffa72e04c90cdfb72b342dda2a82efd1b23a7f85f2c844f98cd8a915f3964736f6c63430008130033"


class OnchainGM:
    def __init__(
        self, account_index: int, somnia_web3: Web3Custom, config: dict, wallet: Account
    ):
        self.account_index = account_index
        self.somnia_web3 = somnia_web3
        self.config = config
        self.wallet = wallet

    @retry_async(default_value=False)
    async def deploy_onchaingm(self):
        try:
            logger.info(f"{self.account_index} | Deploying OnchainGM...")
            # Prepare transaction
            transaction = {
                "from": self.wallet.address,
                "value": Web3.to_wei(0.00005, "ether"),
                "nonce": await self.somnia_web3.web3.eth.get_transaction_count(
                    self.wallet.address
                ),
                "chainId": await self.somnia_web3.web3.eth.chain_id,
                "data": PAYLOAD,
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
                logger.success(
                    f"{self.account_index} | Successfully deployed OnchainGM"
                )

            return True
        except Exception as e:
            random_sleep = random.randint(
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.account_index} | Error deploying OnchainGM: {e}. Sleeping for {random_sleep} seconds..."
            )
            await asyncio.sleep(random_sleep)
            return False

    @retry_async(default_value=False)
    async def gm(self):
        try:
            logger.info(f"{self.account_index} | GM on OnchainGM...")

            # YAPPERS contract address
            contract_address = "0xA0692f67ffcEd633f9c5CfAefd83FC4F21973D01"

            # Base payload with method ID 0x84bb1e42
            payload = "0x5011b71c"

            # Prepare transaction
            transaction = {
                "from": self.wallet.address,
                "to": self.somnia_web3.web3.to_checksum_address(contract_address),
                "value": Web3.to_wei(0.000029, "ether"),
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
            estimated = await self.somnia_web3.web3.eth.estimate_gas(transaction)
            # Добавляем 10% к estimated gas для безопасности
            gas_limit = int(estimated * 2.2)
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
                    f"{self.account_index} | Successfully GM on OnchainGM"
                )

            return True
        except Exception as e:
            str_error = str(e)
            if "execution reverted" in str_error and "0x08c379a00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000d5761697420323420686f75727300000000000000000000000000000000000000" in str_error:
                logger.success(
                    f"{self.account_index} | Already GMed. Wait 24 hours..."
                )
                return True

            random_sleep = random.randint(
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.account_index} | Error GM on OnchainGM: {e}. Sleeping for {random_sleep} seconds..."
            )
            await asyncio.sleep(random_sleep)
            return False