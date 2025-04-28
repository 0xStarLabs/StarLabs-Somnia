import asyncio
import random
from loguru import logger
from web3 import Web3
from src.model.somnia_network.constants import SomniaProtocol
from src.utils.decorators import retry_async
from src.utils.constants import EXPLORER_URL_SOMNIA
from eth_account import Account
from src.model.onchain.web3_custom import Web3Custom


PAYLOAD = "0x6080604052348015600f57600080fd5b5061018d8061001f6000396000f3fe608060405234801561001057600080fd5b50600436106100365760003560e01c8063557ed1ba1461003b578063d09de08a14610059575b600080fd5b610043610063565b60405161005091906100d9565b60405180910390f35b61006161006c565b005b60008054905090565b600160008082825461007e9190610123565b925050819055507f3912982a97a34e42bab8ea0e99df061a563ce1fe3333c5e14386fd4c940ef6bc6000546040516100b691906100d9565b60405180910390a1565b6000819050919050565b6100d3816100c0565b82525050565b60006020820190506100ee60008301846100ca565b92915050565b7f4e487b7100000000000000000000000000000000000000000000000000000000600052601160045260246000fd5b600061012e826100c0565b9150610139836100c0565b9250828201905080821115610151576101506100f4565b5b9291505056fea2646970667358221220801aef4e99d827a7630c9f3ce9c8c00d708b58053b756fed98cd9f2f5928d10f64736f6c634300081c0033"


class Mintair:
    def __init__(
        self, account_index: int, somnia_web3: Web3Custom, config: dict, wallet: Account
    ):
        self.account_index = account_index
        self.somnia_web3 = somnia_web3
        self.config = config
        self.wallet = wallet

    @retry_async(default_value=False)
    async def deploy_mintair(self):
        try:
            logger.info(f"{self.account_index} | Deploying Mintair...")
            # Prepare transaction
            transaction = {
                "from": self.wallet.address,
                "value": 0,
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
                    f"{self.account_index} | Successfully deployed Mintair"
                )

            return True
        except Exception as e:
            random_sleep = random.randint(
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.account_index} | Error deploying Mintair: {e}. Sleeping for {random_sleep} seconds..."
            )
            await asyncio.sleep(random_sleep)
            raise e
