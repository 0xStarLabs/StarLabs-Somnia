import asyncio
import random
import string
from loguru import logger
from web3 import Web3
from src.model.somnia_network.constants import SomniaProtocol
from src.utils.decorators import retry_async
from src.utils.constants import EXPLORER_URL_SOMNIA
from eth_account import Account
from src.model.onchain.web3_custom import Web3Custom


class SomniaDomains:
    def __init__(
        self, account_index: int, somnia_web3: Web3Custom, config: dict, wallet: Account
    ):
        self.account_index = account_index
        self.somnia_web3 = somnia_web3
        self.config = config
        self.wallet = wallet

    def _is_vowel(self, char):
        return char.lower() in "aeiou"

    def _generate_random_domain(self):
        length = random.randint(7, 15)
        chars = string.ascii_lowercase + string.digits
        domain = []
        consecutive_vowels = 0
        consecutive_consonants = 0

        for i in range(length):
            if (
                i == length - 1 and random.random() < 0.3
            ):  # 30% chance to end with a digit
                char = random.choice(string.digits)
            else:
                char = random.choice(string.ascii_lowercase)

            if self._is_vowel(char):
                if consecutive_vowels >= 2:
                    char = random.choice(
                        [c for c in string.ascii_lowercase if not self._is_vowel(c)]
                    )
                    consecutive_vowels = 0
                    consecutive_consonants = 1
                else:
                    consecutive_vowels += 1
                    consecutive_consonants = 0
            else:
                if consecutive_consonants >= 2:
                    char = random.choice(
                        [c for c in string.ascii_lowercase if self._is_vowel(c)]
                    )
                    consecutive_consonants = 0
                    consecutive_vowels = 1
                else:
                    consecutive_consonants += 1
                    consecutive_vowels = 0

            domain.append(char)

        return "".join(domain)

    @retry_async(default_value=False)
    async def mint_domain(self):
        try:
            logger.info(f"{self.account_index} | Minting Somnia Domain...")

            # Contract address for domain minting
            contract_address = "0xDB4e0A5E7b0d03aA41cBB7940c5e9Bab06cc7157"

            # Check if already has NFT from this contract using ERC721 balanceOf
            try:
                # ERC721 ABI for balanceOf function
                erc721_abi = [
                    {
                        "constant": True,
                        "inputs": [{"name": "_owner", "type": "address"}],
                        "name": "balanceOf",
                        "outputs": [{"name": "balance", "type": "uint256"}],
                        "type": "function",
                    }
                ]

                nft_balance = await self.somnia_web3.get_token_balance(
                    wallet_address=self.wallet.address,
                    token_address=contract_address,
                    token_abi=erc721_abi,
                    decimals=0,  # NFTs don't have decimals
                    symbol="DOMAIN",
                )

                if nft_balance and nft_balance.wei > 0:
                    logger.success(
                        f"{self.account_index} | Domain already minted for this account (NFT balance: {nft_balance.wei})"
                    )
                    return True

            except Exception as balance_check_error:
                logger.warning(
                    f"{self.account_index} | Could not check NFT balance: {balance_check_error}"
                )

            # Check if balance is sufficient (1 STT)
            balance = await self.somnia_web3.web3.eth.get_balance(self.wallet.address)
            if balance < self.somnia_web3.web3.to_wei(1, "ether"):
                logger.error(
                    f"{self.account_index} | Insufficient balance. Need at least 1 STT to mint domain."
                )
                return False

            # Generate random domain
            domain = self._generate_random_domain()
            logger.info(f"{self.account_index} | Generated domain: {domain}")

            # Convert domain to bytes and pad to 32 bytes
            domain_bytes = domain.encode("utf-8")
            domain_hex = domain_bytes.hex().ljust(64, "0")

            # Create payload with method ID 0x54c25e4b
            payload = (
                "0x54c25e4b"
                "0000000000000000000000000000000000000000000000000000000000000020"
                "00000000000000000000000000000000000000000000000000000000000000"
                + hex(len(domain_bytes))[2:].zfill(2)
                + domain_hex
            )

            # Prepare transaction
            transaction = {
                "from": self.wallet.address,
                "to": self.somnia_web3.web3.to_checksum_address(contract_address),
                "value": self.somnia_web3.web3.to_wei(1, "ether"),  # 1 STT
                "nonce": await self.somnia_web3.web3.eth.get_transaction_count(
                    self.wallet.address
                ),
                "chainId": await self.somnia_web3.web3.eth.chain_id,
                "data": payload,
            }

            # Get dynamic gas parameters
            gas_params = await self.somnia_web3.get_gas_params()
            transaction.update(gas_params)

            try:
                # Try to estimate gas directly with Web3
                gas_limit = await self.somnia_web3.web3.eth.estimate_gas(transaction)
                transaction["gas"] = gas_limit
            except Exception as gas_error:
                error_str = str(gas_error)
                if "Already claimed a name" in error_str:
                    logger.info(
                        f"{self.account_index} | Domain already minted for this account"
                    )
                    return True
                raise gas_error

            # Execute transaction
            tx_hash = await self.somnia_web3.execute_transaction(
                transaction,
                self.wallet,
                await self.somnia_web3.web3.eth.chain_id,
                EXPLORER_URL_SOMNIA,
            )

            if tx_hash:
                logger.success(
                    f"{self.account_index} | Successfully minted domain: {domain}"
                )

            return True
        except Exception as e:
            error_str = str(e)
            if (
                "0x08c379a000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000016416c726561647920636c61696d65642061206e616d6500000000000000000000"
                in error_str
            ):
                logger.success(
                    f"{self.account_index} | Domain already minted for this account"
                )
                return True

            random_sleep = random.randint(
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.account_index} | Error minting domain: {e}. Sleeping for {random_sleep} seconds..."
            )
            await asyncio.sleep(random_sleep)
            raise e
