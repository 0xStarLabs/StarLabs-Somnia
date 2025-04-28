import asyncio
import random
from loguru import logger
from eth_account import Account
from src.model.help.captcha import NoCaptcha
from src.model.onchain.web3_custom import Web3Custom
import primp

from src.utils.decorators import retry_async
from src.utils.config import Config
from src.model.somnia_network.constants import SomniaProtocol
from src.utils.constants import EXPLORER_URL_SOMNIA


class FaucetService:
    def __init__(self, somnia_instance: SomniaProtocol):
        self.somnia = somnia_instance

    @retry_async(default_value=False)
    async def request_faucet(self):
        try:
            logger.info(f"{self.somnia.account_index} | Starting faucet...")

            headers = {
                "accept": "*/*",
                "content-type": "application/json",
                "origin": "https://testnet.somnia.network",
                "referer": "https://testnet.somnia.network/",
            }

            json_data = {
                "address": self.somnia.wallet.address,
            }

            response = await self.somnia.session.post(
                "https://testnet.somnia.network/api/faucet",
                headers=headers,
                json=json_data,
            )

            if "Bot detected" in response.text:
                logger.error(f"{self.somnia.account_index} | Your wallet is not available for the faucet. Wallet must have some transactions")
                return False
            
            if response.status_code != 200:
                raise Exception(
                    f"failed to request faucet: {response.status_code} | {response.text}"
                )

            if response.json()["success"]:
                logger.success(
                    f"{self.somnia.account_index} | Successfully requested faucet"
                )
                return True
            elif "Please wait 24 hours between requests" in response.text:
                logger.success(
                    f"{self.somnia.account_index} | Wait 24 hours before next request"
                )
                return True
            else:
                raise Exception(
                    f"failed to request faucet: {response.status_code} | Message: {response.json()['message']} | Status: {response.json()['data']['status']}"
                )

        except Exception as e:
            random_pause = random.randint(
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.somnia.account_index} | Faucet error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    async def request_ping_pong_faucet(self):
        try:
            logger.info(
                f"{self.somnia.account_index} | Starting PING and PONG tokens faucet..."
            )

            # Mint PING token first
            ping_address = "0x33e7fab0a8a5da1a923180989bd617c9c2d1c493"
            ping_result = await self._mint_token(ping_address, "PING")
            if not ping_result:
                logger.warning(
                    f"{self.somnia.account_index} | Failed to mint PING token"
                )

            # Add a small delay between transactions
            random_pause = random.randint(
                self.somnia.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[0],
                self.somnia.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[1],
            )
            await asyncio.sleep(random_pause)

            # Then mint PONG token
            pong_address = "0x9beaa0016c22b646ac311ab171270b0ecf23098f"
            pong_result = await self._mint_token(pong_address, "PONG")
            if not pong_result:
                logger.warning(
                    f"{self.somnia.account_index} | Failed to mint PONG token"
                )

            # Return True if at least one of the mints succeeded
            return ping_result or pong_result

        except Exception as e:
            random_pause = random.randint(
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.somnia.account_index} | PING/PONG Faucet error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            return False

    @retry_async(default_value=False)
    async def _mint_token(self, token_address, token_name):
        """Helper function to mint a specific token."""
        try:
            logger.info(f"{self.somnia.account_index} | Minting {token_name} token...")

            # Convert address to checksum format
            checksum_address = self.somnia.web3.web3.to_checksum_address(token_address)

            # Mint function has method ID: 0x1249c58b
            mint_function_data = "0x1249c58b"  # Function signature for mint()

            # Send transaction to call the mint() function
            tx_hash = await self.somnia.web3.send_transaction(
                to=checksum_address,
                data=mint_function_data,
                wallet=self.somnia.wallet,
                value=0,  # No value needed for mint
            )

            logger.success(
                f"{self.somnia.account_index} | Successfully minted {token_name} token. TX: {EXPLORER_URL_SOMNIA}{tx_hash}"
            )
            return True

        except Exception as e:
            logger.error(
                f"{self.somnia.account_index} | Failed to mint {token_name} token: {e}"
            )
            return False
