import asyncio
import random
from loguru import logger
from web3 import Web3
from src.model.somnia_network.constants import SomniaProtocol
from src.utils.decorators import retry_async
from src.utils.constants import EXPLORER_URL_SOMNIA
from eth_account import Account
from src.model.projects.swaps.somnia_exchange.constants import (
    WSTT_ADDRESS,
    TOK1_ADDRESS,
    USDTG_ADDRESS,
    ROUTER_ADDRESS,
    ROUTER_ABI,
)


class SomniaExchange:
    def __init__(self, instance: SomniaProtocol):
        self.somnia = instance
        self.router_address = ROUTER_ADDRESS
        self.tokens = {
            "STT": "0x0000000000000000000000000000000000000000",  # Native token
            "WSTT": WSTT_ADDRESS,
            "TOK1": TOK1_ADDRESS,
            "USDTG": USDTG_ADDRESS,
        }
        self.swap_method_id = "0x7ff36ab5"  # swapExactETHForTokens
        self.token_swap_method_id = "0x38ed1739"  # swapExactTokensForTokens
        self.approve_method_id = "0x095ea7b3"  # ERC20 approve
        # WSTT contract minimal ABI - just deposit and withdraw functions
        self.wstt_abi = [
            {
                "constant": False,
                "inputs": [],
                "name": "deposit",
                "outputs": [],
                "payable": True,
                "stateMutability": "payable",
                "type": "function",
            },
            {
                "constant": False,
                "inputs": [{"name": "_amount", "type": "uint256"}],
                "name": "withdraw",
                "outputs": [],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function",
            },
        ]

    async def check_token_balance(self, token):
        """Check token balance for the account"""
        if token == "STT":
            # For native token, use get_balance method
            balance = await self.somnia.web3.get_balance(self.somnia.wallet.address)
            return balance.wei
        else:
            # For ERC20 tokens
            token_address = self.tokens[token]
            balance = await self.somnia.web3.get_token_balance(
                self.somnia.wallet.address, token_address
            )
            return balance.wei

    async def check_all_token_balances(self):
        """Check balances for all tokens"""
        balances = {}
        for token in self.tokens.keys():
            balance = await self.check_token_balance(token)
            if balance > 0:
                balances[token] = balance

        return balances

    async def approve_token(self, token, amount):
        """Approve tokens for router"""
        token_address = self.tokens[token]

        try:
            # Use the built-in approve_token method from Web3Custom
            tx_hash = await self.somnia.web3.approve_token(
                token_address=token_address,
                spender_address=self.router_address,
                amount=amount,
                wallet=self.somnia.wallet,
                chain_id=50312,
                explorer_url=EXPLORER_URL_SOMNIA,
            )

            if tx_hash:
                logger.success(
                    f"{self.somnia.account_index} | Approved {amount/(10**18)} {token} for router. "
                    f"Tx: {EXPLORER_URL_SOMNIA}/tx/{tx_hash}"
                )
            return True

        except Exception as e:
            logger.error(
                f"{self.somnia.account_index} | Failed to approve {token}: {str(e)}"
            )
            return False

    async def get_amounts_out(self, amount_in, path):
        """Get expected output amount for a given input amount and path"""
        web3 = self.somnia.web3.web3
        router_contract = web3.eth.contract(address=self.router_address, abi=ROUTER_ABI)

        try:
            amounts = await asyncio.to_thread(
                router_contract.functions.getAmountsOut(amount_in, path).call
            )
            return amounts[-1]  # Return the output amount
        except Exception as e:
            logger.error(
                f"{self.somnia.account_index} | Error getting amounts out: {e}"
            )
            return 0

    async def deposit_stt_to_wstt(self, amount_in):
        """
        Convert STT to WSTT directly using the WSTT contract's deposit function

        Args:
            amount_in: Amount of STT to convert in wei

        Returns:
            Transaction hash if successful, None otherwise
        """
        try:
            web3 = self.somnia.web3.web3
            account = self.somnia.wallet
            wstt_address = self.tokens["WSTT"]

            # Create WSTT contract instance
            wstt_contract = web3.eth.contract(address=wstt_address, abi=self.wstt_abi)

            # Build transaction data for deposit function
            deposit_function = wstt_contract.functions.deposit()

            # Get function data
            function_data = deposit_function._encode_transaction_data()

            # Estimate gas
            gas_estimate = await self.somnia.web3.estimate_gas(
                {
                    "from": account.address,
                    "to": wstt_address,
                    "data": function_data,
                    "value": amount_in,
                }
            )

            # Prepare transaction parameters
            tx_data = {
                "to": wstt_address,
                "data": function_data,
                "value": amount_in,
                "gas": gas_estimate,
            }

            # Execute transaction
            tx_hash = await self.somnia.web3.execute_transaction(
                tx_data,
                wallet=account,
                chain_id=50312,
                explorer_url=EXPLORER_URL_SOMNIA,
            )

            if tx_hash:
                logger.success(
                    f"{self.somnia.account_index} | Successfully converted {amount_in/(10**18)} STT to WSTT. "
                    f"Tx: {EXPLORER_URL_SOMNIA}/tx/{tx_hash}"
                )
                return tx_hash
            else:
                logger.error(
                    f"{self.somnia.account_index} | Failed to convert STT to WSTT."
                )
                return None

        except Exception as e:
            logger.error(
                f"{self.somnia.account_index} | STT to WSTT conversion error: {str(e)}"
            )
            return None

    async def withdraw_wstt_to_stt(self, amount_in):
        """
        Convert WSTT to STT directly using the WSTT contract's withdraw function

        Args:
            amount_in: Amount of WSTT to convert in wei

        Returns:
            Transaction hash if successful, None otherwise
        """
        try:
            web3 = self.somnia.web3.web3
            account = self.somnia.wallet
            wstt_address = self.tokens["WSTT"]

            # Create WSTT contract instance
            wstt_contract = web3.eth.contract(address=wstt_address, abi=self.wstt_abi)

            # Build transaction data for withdraw function
            withdraw_function = wstt_contract.functions.withdraw(amount_in)

            # Get function data
            function_data = withdraw_function._encode_transaction_data()

            # Estimate gas
            gas_estimate = await self.somnia.web3.estimate_gas(
                {
                    "from": account.address,
                    "to": wstt_address,
                    "data": function_data,
                    "value": 0,
                }
            )

            # Prepare transaction parameters
            tx_data = {
                "to": wstt_address,
                "data": function_data,
                "value": 0,
                "gas": gas_estimate,
            }

            # Execute transaction
            tx_hash = await self.somnia.web3.execute_transaction(
                tx_data,
                wallet=account,
                chain_id=50312,
                explorer_url=EXPLORER_URL_SOMNIA,
            )

            if tx_hash:
                logger.success(
                    f"{self.somnia.account_index} | Successfully converted {amount_in/(10**18)} WSTT to STT. "
                    f"Tx: {EXPLORER_URL_SOMNIA}/tx/{tx_hash}"
                )
                return tx_hash
            else:
                logger.error(
                    f"{self.somnia.account_index} | Failed to convert WSTT to STT."
                )
                return None

        except Exception as e:
            logger.error(
                f"{self.somnia.account_index} | WSTT to STT conversion error: {str(e)}"
            )
            return None

    async def swap_tokens(self, from_token, to_token, amount_in):
        """
        Swap tokens on Somnia Exchange

        Args:
            from_token: Token to swap from
            to_token: Token to swap to
            amount_in: Amount to swap in wei

        Returns:
            Transaction hash if successful, None otherwise
        """
        try:
            # Special case: STT to WSTT direct conversion
            if from_token == "STT" and to_token == "WSTT":
                return await self.deposit_stt_to_wstt(amount_in)

            # Special case: WSTT to STT direct conversion
            if from_token == "WSTT" and to_token == "STT":
                return await self.withdraw_wstt_to_stt(amount_in)

            web3 = self.somnia.web3.web3
            account = self.somnia.wallet
            router = self.router_address
            router_contract = web3.eth.contract(address=router, abi=ROUTER_ABI)

            # Deadline for the transaction
            deadline = await web3.eth.get_block("latest")
            deadline = deadline.timestamp + 1200  # 20 minutes

            # Case 1: Native STT to Token
            if from_token == "STT":
                # Define the swap path
                path = [self.tokens["WSTT"], self.tokens[to_token]]

                # Using 0 for amountOutMin to ensure swap goes through
                amount_out_min = 0

                # Build transaction data for swapExactETHForTokens
                swap_function = router_contract.functions.swapExactETHForTokens(
                    amount_out_min, path, account.address, deadline
                )

                # Get function data
                function_data = swap_function._encode_transaction_data()

                # Estimate gas first
                gas_estimate = await self.somnia.web3.estimate_gas(
                    {
                        "from": account.address,
                        "to": router,
                        "data": function_data,
                        "value": amount_in,
                    }
                )

                # Prepare transaction parameters with gas estimate
                tx_data = {
                    "to": router,
                    "data": function_data,
                    "value": amount_in,
                    "gas": gas_estimate,
                }

            # Case 2: Token to Token or Token to STT
            else:
                # If token to STT, path is [token, WSTT]
                if to_token == "STT":
                    path = [self.tokens[from_token], self.tokens["WSTT"]]

                    # First approve tokens
                    approved = await self.approve_token(from_token, amount_in)
                    if not approved:
                        return None

                    # Using 0 for amountOutMin to ensure swap goes through
                    amount_out_min = 0

                    # Build transaction data for swapExactTokensForETH
                    swap_function = router_contract.functions.swapExactTokensForETH(
                        amount_in, amount_out_min, path, account.address, deadline
                    )

                else:
                    # If token to other token, path is [from_token, WSTT, to_token]
                    if from_token == "WSTT" and to_token in ["TOK1", "USDTG"]:
                        # Direct path for WSTT to tokens
                        path = [self.tokens[from_token], self.tokens[to_token]]
                    elif from_token in ["TOK1", "USDTG"] and to_token == "WSTT":
                        # Direct path for tokens to WSTT
                        path = [self.tokens[from_token], self.tokens[to_token]]
                    else:
                        # Path through WSTT for other token pairs
                        path = [
                            self.tokens[from_token],
                            self.tokens["WSTT"],
                            self.tokens[to_token],
                        ]

                    # First approve tokens
                    approved = await self.approve_token(from_token, amount_in)
                    if not approved:
                        return None

                    # Using 0 for amountOutMin to ensure swap goes through
                    amount_out_min = 0

                    # Build transaction data for swapExactTokensForTokens
                    swap_function = router_contract.functions.swapExactTokensForTokens(
                        amount_in, amount_out_min, path, account.address, deadline
                    )

                # Get function data
                function_data = swap_function._encode_transaction_data()

                # Estimate gas first
                gas_estimate = await self.somnia.web3.estimate_gas(
                    {
                        "from": account.address,
                        "to": router,
                        "data": function_data,
                        "value": 0,
                    }
                )

                # Prepare transaction parameters with gas estimate
                tx_data = {
                    "to": router,
                    "data": function_data,
                    "value": 0,
                    "gas": gas_estimate,
                }

            # Execute transaction using Web3Custom
            tx_hash = await self.somnia.web3.execute_transaction(
                tx_data,
                wallet=account,
                chain_id=50312,
                explorer_url=EXPLORER_URL_SOMNIA,
            )

            if tx_hash:
                logger.success(
                    f"{self.somnia.account_index} | Successfully swapped {amount_in/(10**18)} {from_token} to {to_token}. "
                    f"Tx: {EXPLORER_URL_SOMNIA}/tx/{tx_hash}"
                )
                return tx_hash
            else:
                logger.error(
                    f"{self.somnia.account_index} | Failed to swap {from_token} to {to_token}."
                )
                return None

        except Exception as e:
            logger.error(f"{self.somnia.account_index} | Swap error: {str(e)}")
            return None

    @retry_async()
    async def swaps(self):
        try:
            success_count = 0

            # Available tokens
            token_options = ["STT", "WSTT", "TOK1", "USDTG"]

            # Check config settings
            balance_percent_range = (
                self.somnia.config.SOMNIA_NETWORK.SOMNIA_SWAPS.BALANCE_PERCENT_TO_SWAP
            )
            num_swaps_range = (
                self.somnia.config.SOMNIA_NETWORK.SOMNIA_SWAPS.NUMBER_OF_SWAPS
            )
            swap_all_to_stt = (
                self.somnia.config.SOMNIA_NETWORK.SOMNIA_SWAPS.SWAP_ALL_TO_STT
            )

            # Get random number of swaps from config range
            num_swaps = random.randint(num_swaps_range[0], num_swaps_range[1])

            # If swap_all_to_stt is enabled, only swap all tokens to STT
            if swap_all_to_stt:
                logger.info(
                    f"{self.somnia.account_index} | SWAP_ALL_TO_STT enabled, converting all tokens to STT"
                )
                token_balances = await self.check_all_token_balances()

                # Remove STT from the balances dict since we're swapping to STT
                if "STT" in token_balances:
                    del token_balances["STT"]

                # If we have non-STT tokens with balance, swap them to STT
                for token, balance in token_balances.items():
                    if balance > 0:
                        # Swap 99-100% of the balance to ensure we capture all tokens
                        amount_to_swap = int(balance * random.uniform(0.99, 0.999))
                        if amount_to_swap > 0:
                            logger.info(
                                f"{self.somnia.account_index} | Swapping {amount_to_swap/(10**18)} {token} to STT (100% of balance)"
                            )
                            tx_hash = await self.swap_tokens(
                                token, "STT", amount_to_swap
                            )
                            if tx_hash:
                                success_count += 1
                                # Wait between swaps
                                sleep_time = random.randint(5, 15)
                                await asyncio.sleep(sleep_time)

                return success_count > 0

            # If SWAP_ALL_TO_STT is not enabled, perform random swaps according to config
            logger.info(
                f"{self.somnia.account_index} | Planning to perform {num_swaps} random swaps"
            )
            for _ in range(num_swaps):
                # Select random token pair
                from_token = random.choice(token_options)
                to_token = random.choice([t for t in token_options if t != from_token])

                # Check balance
                balance = await self.check_token_balance(from_token)

                # Skip if no balance
                if balance == 0:
                    logger.warning(
                        f"{self.somnia.account_index} | No {from_token} balance for swap"
                    )
                    continue

                # Calculate swap amount based on config percentage range
                min_percent = balance_percent_range[0] / 100
                max_percent = balance_percent_range[1] / 100
                swap_percent = random.uniform(min_percent, max_percent)

                # For STT, ensure we have enough for gas
                if from_token == "STT":
                    gas_buffer = 0.002 * 10**18  # Buffer for gas
                    amount = int((balance - gas_buffer) * swap_percent)

                    # Ensure minimum amount for swap
                    min_amount = 0.005 * 10**18  # Minimum 0.005 STT
                    if amount < min_amount:
                        logger.warning(
                            f"{self.somnia.account_index} | STT amount too small for swap, min required: {min_amount/(10**18)}"
                        )
                        continue
                else:
                    amount = int(balance * swap_percent)

                    # Skip if amount is 0
                    if amount == 0:
                        logger.warning(
                            f"{self.somnia.account_index} | {from_token} amount too small for swap"
                        )
                        continue

                # Log the swap details
                logger.info(
                    f"{self.somnia.account_index} | Swapping {amount/(10**18)} {from_token} to {to_token} ({swap_percent*100:.2f}% of balance)"
                )

                # Execute the swap
                tx_hash = await self.swap_tokens(from_token, to_token, amount)

                if tx_hash:
                    success_count += 1

                # Wait between swaps
                sleep_time = random.randint(5, 15)
                await asyncio.sleep(sleep_time)

            return success_count > 0

        except Exception as e:
            random_pause = random.randint(
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.somnia.account_index} | Somnia exchange swaps error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            return False
