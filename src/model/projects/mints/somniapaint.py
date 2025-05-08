import asyncio
import random
from loguru import logger
from web3 import Web3
from src.model.somnia_network.constants import SomniaProtocol
from src.utils.decorators import retry_async
from src.utils.constants import EXPLORER_URL_SOMNIA
from eth_account import Account
from src.model.onchain.web3_custom import Web3Custom


class SomniaPaint:
    def __init__(
        self, account_index: int, somnia_web3: Web3Custom, config: dict, wallet: Account
    ):
        self.account_index = account_index
        self.somnia_web3 = somnia_web3
        self.config = config
        self.wallet = wallet

    @retry_async(default_value=False)
    async def send_pixel(self):
        try:
            logger.info(
                f"{self.account_index} | Sending random pixel at Somnia Paint..."
            )

            # Paint contract address
            contract_address = "0x496eF0E9944ff8c83fa74FeB580f2FB581ecFfFd"

            COLORS = [
                "FF3B30",
                "FF9500",
                "FFCC00",
                "34C759",
                "007AFF",
                "5856D6",
                "AF52DE",
                "FFD1DC",
                "FFAAA5",
                "FFD3B6",
                "DCEDC1",
                "A8E6CF",
                "AA96DA",
                "C7CEEA",
                "FE019A",
                "BC13FE",
                "5961FF",
                "00FFDD",
                "00FF5B",
                "FFE600",
                "FF9900",
                "FFFFFF",
                "DDDDDD",
                "999999",
                "555555",
                "111111",
                "000000",
            ]

            # Generate random x, y coordinates
            # Canvas size: 0-123 for width, 0-63 for height
            x_coordinate = random.randint(0, 123)
            y_coordinate = random.randint(0, 63)

            # Select a random color from COLORS and convert to lowercase
            color = random.choice(COLORS).lower()

            # Function selector
            method_id = "0xa0561481"

            # Pad coordinates and color to 32 bytes each (64 hex chars)
            x_hex = hex(x_coordinate)[2:].zfill(64)
            y_hex = hex(y_coordinate)[2:].zfill(64)
            color_hex = "0" * 58 + color  # Must be exactly 64 chars (32 bytes)

            # Construct the payload
            payload = method_id + x_hex + y_hex + color_hex

            # Debug: print the payload
            # input(payload)

            # Prepare transaction
            transaction = {
                "from": self.wallet.address,
                "to": self.somnia_web3.web3.to_checksum_address(contract_address),
                "value": Web3.to_wei(0.01, "ether"),
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
                logger.success(
                    f"{self.account_index} | Successfully sent random pixel at Somnia Paint: x={x_coordinate}, y={y_coordinate}, color=#{color}"
                )

            return True
        except Exception as e:
            random_sleep = random.randint(
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.account_index} | Error sending random pixel at Somnia Paint: {e}. Sleeping for {random_sleep} seconds..."
            )
            await asyncio.sleep(random_sleep)
            return False
