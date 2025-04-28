import asyncio
import random
from loguru import logger
from web3 import Web3
from src.model.somnia_network.constants import SomniaProtocol
from src.utils.decorators import retry_async
from src.utils.constants import EXPLORER_URL_SOMNIA
from src.model.projects.swaps.quickswap.constants import (
    USDC_ADDRESS,
    WETH_ADDRESS,
    WSTT_ADDRESS,
    ROUTER_ADDRESS,
    TOKEN_INFO,
    DEFAULT_FEE,
    FEE_TIERS,
)
from eth_account import Account


class Quickswap:
    def __init__(self, instance: SomniaProtocol):
        self.somnia = instance

    async def swaps(self):
        try:
            # Router address
            router_address = Web3.to_checksum_address(ROUTER_ADDRESS)

            # Token addresses
            usdc_address = Web3.to_checksum_address(USDC_ADDRESS)
            weth_address = Web3.to_checksum_address(WETH_ADDRESS)
            wstt_address = Web3.to_checksum_address(WSTT_ADDRESS)

            # List of available tokens for swapping
            tokens = [
                {"address": usdc_address, "symbol": "USDC", "decimals": 6},
                {"address": weth_address, "symbol": "WETH", "decimals": 18},
                {
                    "address": wstt_address,
                    "symbol": "WSTT",
                    "decimals": 18,
                    "is_native_wrapped": True,
                },
            ]

            # Minimal ABIs for the tokens and router
            token_abi = [
                {
                    "inputs": [
                        {"internalType": "address", "name": "owner", "type": "address"}
                    ],
                    "name": "balanceOf",
                    "outputs": [
                        {"internalType": "uint256", "name": "", "type": "uint256"}
                    ],
                    "stateMutability": "view",
                    "type": "function",
                },
                {
                    "inputs": [
                        {
                            "internalType": "address",
                            "name": "spender",
                            "type": "address",
                        },
                        {
                            "internalType": "uint256",
                            "name": "amount",
                            "type": "uint256",
                        },
                    ],
                    "name": "approve",
                    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function",
                },
                {
                    "name": "allowance",
                    "inputs": [
                        {"name": "owner", "type": "address", "internalType": "address"},
                        {
                            "name": "spender",
                            "type": "address",
                            "internalType": "address",
                        },
                    ],
                    "outputs": [
                        {"name": "", "type": "uint256", "internalType": "uint256"}
                    ],
                    "stateMutability": "view",
                    "type": "function",
                },
                {
                    "name": "transfer",
                    "inputs": [
                        {"name": "to", "type": "address", "internalType": "address"},
                        {"name": "value", "type": "uint256", "internalType": "uint256"},
                    ],
                    "outputs": [{"name": "", "type": "bool", "internalType": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function",
                },
                {
                    "name": "transferFrom",
                    "inputs": [
                        {"name": "from", "type": "address", "internalType": "address"},
                        {"name": "to", "type": "address", "internalType": "address"},
                        {"name": "value", "type": "uint256", "internalType": "uint256"},
                    ],
                    "outputs": [{"name": "", "type": "bool", "internalType": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function",
                },
                {
                    "name": "decimals",
                    "inputs": [],
                    "outputs": [{"name": "", "type": "uint8", "internalType": "uint8"}],
                    "stateMutability": "view",
                    "type": "function",
                },
                {
                    "name": "mint",
                    "inputs": [],
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function",
                },
            ]

            router_abi = [
                {
                    "inputs": [
                        {
                            "components": [
                                {
                                    "internalType": "address",
                                    "name": "tokenIn",
                                    "type": "address",
                                },
                                {
                                    "internalType": "address",
                                    "name": "tokenOut",
                                    "type": "address",
                                },
                                {
                                    "internalType": "uint24",
                                    "name": "fee",
                                    "type": "uint24",
                                },
                                {
                                    "internalType": "address",
                                    "name": "recipient",
                                    "type": "address",
                                },
                                {
                                    "internalType": "uint256",
                                    "name": "amountIn",
                                    "type": "uint256",
                                },
                                {
                                    "internalType": "uint256",
                                    "name": "amountOutMinimum",
                                    "type": "uint256",
                                },
                                {
                                    "internalType": "uint160",
                                    "name": "sqrtPriceLimitX96",
                                    "type": "uint160",
                                },
                            ],
                            "internalType": "struct ISwapRouter.ExactInputSingleParams",
                            "name": "params",
                            "type": "tuple",
                        }
                    ],
                    "name": "exactInputSingle",
                    "outputs": [
                        {
                            "internalType": "uint256",
                            "name": "amountOut",
                            "type": "uint256",
                        }
                    ],
                    "stateMutability": "payable",
                    "type": "function",
                },
                {
                    "inputs": [
                        {"internalType": "bytes[]", "name": "data", "type": "bytes[]"}
                    ],
                    "name": "multicall",
                    "outputs": [
                        {
                            "internalType": "bytes[]",
                            "name": "results",
                            "type": "bytes[]",
                        }
                    ],
                    "stateMutability": "payable",
                    "type": "function",
                },
                {
                    "inputs": [
                        {
                            "internalType": "uint256",
                            "name": "amountMinimum",
                            "type": "uint256",
                        },
                        {
                            "internalType": "address",
                            "name": "recipient",
                            "type": "address",
                        },
                    ],
                    "name": "unwrapWETH9",
                    "outputs": [],
                    "stateMutability": "payable",
                    "type": "function",
                },
            ]

            # Check token balances
            token_balances = {}
            for token in tokens:
                balance = await self.somnia.web3.get_token_balance(
                    self.somnia.wallet.address,
                    token["address"],
                    token_abi,
                    decimals=token["decimals"],
                    symbol=token["symbol"],
                )
                token_balances[token["address"]] = balance
                logger.info(
                    f"{self.somnia.account_index} | Token balance: {balance.formatted:.6f} {token['symbol']}"
                )

            # Get native STT balance
            stt_balance = await self.somnia.web3.get_balance(self.somnia.wallet.address)
            logger.info(
                f"{self.somnia.account_index} | Native STT balance: {stt_balance.formatted:.6f} STT"
            )

            # Check if all balances are zero
            if (
                all(balance.wei == 0 for balance in token_balances.values())
                and stt_balance.wei == 0
            ):
                logger.error(
                    f"{self.somnia.account_index} | No tokens to swap. All token balances are zero."
                )
                return False

            # Get number of swaps from config
            min_txs, max_txs = self.somnia.config.SOMNIA_NETWORK.SOMNIA_SWAPS.NUMBER_OF_SWAPS
            num_swaps = random.randint(min_txs, max_txs)

            logger.info(
                f"{self.somnia.account_index} | Planning to execute {num_swaps} swaps"
            )

            success_count = 0

            for i in range(num_swaps):
                # Refresh token balances before each swap
                if i > 0:
                    for token in tokens:
                        balance = await self.somnia.web3.get_token_balance(
                            self.somnia.wallet.address,
                            token["address"],
                            token_abi,
                            decimals=token["decimals"],
                            symbol=token["symbol"],
                        )
                        token_balances[token["address"]] = balance
                        logger.info(
                            f"{self.somnia.account_index} | Updated token balance: {balance.formatted:.6f} {token['symbol']}"
                        )

                    # Update native STT balance
                    stt_balance = await self.somnia.web3.get_balance(
                        self.somnia.wallet.address
                    )
                    logger.info(
                        f"{self.somnia.account_index} | Updated native STT balance: {stt_balance.formatted:.6f} STT"
                    )

                # Decide on swap type:
                # 1. Token to Token
                # 2. Token to STT (native)
                # 3. STT (native) to Token
                swap_types = []
                if any(token_balances[token["address"]].wei > 0 for token in tokens):
                    swap_types.append("token_to_token")
                    swap_types.append("token_to_stt")
                if stt_balance.wei > 0:
                    swap_types.append("stt_to_token")

                if not swap_types:
                    logger.warning(
                        f"{self.somnia.account_index} | No tokens or STT left to swap. Ending swap sequence."
                    )
                    break

                # Randomly select swap type
                swap_type = random.choice(swap_types)

                if swap_type == "stt_to_token":
                    # Swapping native STT for token
                    # Get tokens that are not WSTT
                    available_tokens_out = [
                        token
                        for token in tokens
                        if not token.get("is_native_wrapped", False)
                    ]

                    if not available_tokens_out:
                        logger.warning(
                            f"{self.somnia.account_index} | No suitable tokens available for swap from STT."
                        )
                        continue

                    token_out = random.choice(available_tokens_out)

                    logger.info(
                        f"{self.somnia.account_index} | Swap {i+1}/{num_swaps}: STT (native) to {token_out['symbol']}"
                    )

                    # Calculate amount to swap (10-35% of STT balance)
                    min_percent, max_percent = (
                        self.somnia.config.SOMNIA_NETWORK.SOMNIA_SWAPS.BALANCE_PERCENT_TO_SWAP
                    )
                    random_percentage = random.uniform(min_percent, max_percent)

                    # Calculate amount in wei, and keep some for gas
                    gas_reserve = 0.005 * 10**18  # 0.005 STT reserved for gas (in wei)
                    max_amount = max(0, stt_balance.wei - gas_reserve)
                    amount_to_swap = int(max_amount * (random_percentage / 100))

                    if amount_to_swap <= 0:
                        logger.warning(
                            f"{self.somnia.account_index} | Not enough STT for gas after swap. Skipping."
                        )
                        continue

                    logger.info(
                        f"{self.somnia.account_index} | Swapping {amount_to_swap / 10**18:.6f} "
                        f"STT to {token_out['symbol']} ({random_percentage:.2f}% of available balance)"
                    )

                    # Execute the native STT to token swap
                    success = await self.swap_native_stt_to_token(
                        token_out=token_out, amount_in=amount_to_swap
                    )

                    if success:
                        success_count += 1

                elif swap_type == "token_to_stt":
                    # Swapping token for native STT
                    # Get tokens with non-zero balance (excluding WSTT)
                    available_tokens = [
                        token
                        for token in tokens
                        if token_balances[token["address"]].wei > 0
                        and not token.get("is_native_wrapped", False)
                    ]

                    if not available_tokens:
                        logger.warning(
                            f"{self.somnia.account_index} | No tokens available to swap to STT."
                        )
                        continue

                    token_in = random.choice(available_tokens)

                    logger.info(
                        f"{self.somnia.account_index} | Swap {i+1}/{num_swaps}: {token_in['symbol']} to STT (native)"
                    )

                    # Find the WSTT token
                    wstt_token = next(
                        (t for t in tokens if t["address"] == wstt_address), None
                    )
                    if not wstt_token:
                        logger.error(
                            f"{self.somnia.account_index} | WSTT token not found in tokens list"
                        )
                        continue

                    # Calculate amount to swap (10-35% of balance)
                    min_percent, max_percent = (
                        self.somnia.config.SOMNIA_NETWORK.SOMNIA_SWAPS.BALANCE_PERCENT_TO_SWAP
                    )
                    random_percentage = random.uniform(min_percent, max_percent)
                    token_balance = token_balances[token_in["address"]]
                    amount_to_swap = int(token_balance.wei * (random_percentage / 100))

                    logger.info(
                        f"{self.somnia.account_index} | Swapping {token_balance.formatted * random_percentage / 100:.6f} "
                        f"{token_in['symbol']} to STT ({random_percentage:.2f}% of balance)"
                    )

                    # Execute the token to native STT swap
                    success = await self.swap_tokens_to_native_stt(
                        token_in=token_in, amount_to_swap=amount_to_swap
                    )

                    if success:
                        success_count += 1

                else:  # token_to_token
                    # Get tokens with non-zero balance
                    available_tokens = [
                        token
                        for token in tokens
                        if token_balances[token["address"]].wei > 0
                    ]

                    if not available_tokens:
                        logger.warning(
                            f"{self.somnia.account_index} | No tokens left to swap. Ending swap sequence."
                        )
                        break

                    # Select token_in from available tokens
                    token_in = random.choice(available_tokens)

                    # Select token_out different from token_in
                    available_tokens_out = [
                        token
                        for token in tokens
                        if token["address"] != token_in["address"]
                    ]

                    if not available_tokens_out:
                        logger.warning(
                            f"{self.somnia.account_index} | No different tokens available for swap output."
                        )
                        break

                    token_out = random.choice(available_tokens_out)

                    logger.info(
                        f"{self.somnia.account_index} | Swap {i+1}/{num_swaps}: {token_in['symbol']} to {token_out['symbol']}"
                    )

                    # Calculate amount to swap (10-35% of balance)
                    min_percent, max_percent = (
                        self.somnia.config.SOMNIA_NETWORK.SOMNIA_SWAPS.BALANCE_PERCENT_TO_SWAP
                    )
                    random_percentage = random.uniform(min_percent, max_percent)
                    token_balance = token_balances[token_in["address"]]
                    amount_to_swap = int(token_balance.wei * (random_percentage / 100))

                    logger.info(
                        f"{self.somnia.account_index} | Swapping {token_balance.formatted * random_percentage / 100:.6f} "
                        f"{token_in['symbol']} to {token_out['symbol']} ({random_percentage:.2f}% of balance)"
                    )

                    # Approve tokens
                    approve_result = await self.somnia.web3.approve_token(
                        token_address=token_in["address"],
                        spender_address=router_address,
                        amount=amount_to_swap,
                        wallet=self.somnia.wallet,
                        chain_id=50312,  # Somnia chain ID
                        token_abi=token_abi,
                        explorer_url=EXPLORER_URL_SOMNIA,
                    )

                    if approve_result:
                        logger.success(
                            f"{self.somnia.account_index} | Successfully approved {token_in['symbol']}"
                        )
                    else:
                        logger.error(
                            f"{self.somnia.account_index} | Failed to approve {token_in['symbol']}"
                        )
                        continue

                    # Prepare swap params - using exactInputSingle
                    swap_params = (
                        token_in["address"],  # tokenIn
                        token_out["address"],  # tokenOut
                        DEFAULT_FEE,  # fee
                        self.somnia.wallet.address,  # recipient
                        amount_to_swap,  # amountIn
                        0,  # amountOutMinimum (0 for simplicity)
                        0,  # sqrtPriceLimitX96 (0 for no limit)
                    )

                    # Create router contract
                    router_contract = self.somnia.web3.web3.eth.contract(
                        address=router_address, abi=router_abi
                    )

                    # Prepare and execute transaction
                    try:
                        # Build the transaction using the contract's functions
                        swap_function = router_contract.functions.exactInputSingle(
                            swap_params
                        )

                        # Get transaction parameters
                        tx_params = {
                            "from": self.somnia.wallet.address,
                            "nonce": await self.somnia.web3.web3.eth.get_transaction_count(
                                self.somnia.wallet.address
                            ),
                            "chainId": 50312,  # Somnia chain ID
                        }

                        # Estimate gas
                        try:
                            gas_estimate = await swap_function.estimate_gas(tx_params)
                            tx_params["gas"] = int(gas_estimate * 1.2)  # Add 20% buffer
                        except Exception as e:
                            logger.error(
                                f"{self.somnia.account_index} | Gas estimation failed: {e}"
                            )
                            continue

                        # Build the transaction
                        transaction = await swap_function.build_transaction(tx_params)

                        # Execute the transaction
                        tx_hash = await self.somnia.web3.execute_transaction(
                            tx_data=transaction,
                            wallet=self.somnia.wallet,
                            chain_id=50312,  # Somnia chain ID
                            explorer_url=EXPLORER_URL_SOMNIA,
                        )

                    except Exception as e:
                        logger.error(
                            f"{self.somnia.account_index} | Failed to build or execute swap transaction: {e}"
                        )
                        continue

                    if tx_hash:
                        logger.success(
                            f"{self.somnia.account_index} | Successfully swapped {token_in['symbol']} to {token_out['symbol']}. "
                            f"TX: {EXPLORER_URL_SOMNIA}{tx_hash}"
                        )
                        success_count += 1
                    else:
                        logger.error(
                            f"{self.somnia.account_index} | Failed to swap {token_in['symbol']} to {token_out['symbol']}"
                        )

                # Sleep between swaps
                if i < num_swaps - 1:  # Don't sleep after the last swap
                    await asyncio.sleep(
                        random.uniform(
                            self.somnia.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[0],
                            self.somnia.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[1],
                        )
                    )

            return success_count > 0

        except Exception as e:
            random_pause = random.randint(
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.somnia.account_index} | Swap error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            return False

    async def swap_exact_tokens(self, token_in, token_out, amount_to_swap):
        """Swap an exact amount of token_in for token_out"""
        try:
            router_address = Web3.to_checksum_address(ROUTER_ADDRESS)
            token_in_address = Web3.to_checksum_address(token_in["address"])
            token_out_address = Web3.to_checksum_address(token_out["address"])

            # ABIs
            token_abi = [
                {
                    "inputs": [
                        {"internalType": "address", "name": "owner", "type": "address"}
                    ],
                    "name": "balanceOf",
                    "outputs": [
                        {"internalType": "uint256", "name": "", "type": "uint256"}
                    ],
                    "stateMutability": "view",
                    "type": "function",
                },
                {
                    "inputs": [
                        {
                            "internalType": "address",
                            "name": "spender",
                            "type": "address",
                        },
                        {
                            "internalType": "uint256",
                            "name": "amount",
                            "type": "uint256",
                        },
                    ],
                    "name": "approve",
                    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function",
                },
            ]

            router_abi = [
                {
                    "inputs": [
                        {
                            "components": [
                                {
                                    "internalType": "address",
                                    "name": "tokenIn",
                                    "type": "address",
                                },
                                {
                                    "internalType": "address",
                                    "name": "tokenOut",
                                    "type": "address",
                                },
                                {
                                    "internalType": "uint24",
                                    "name": "fee",
                                    "type": "uint24",
                                },
                                {
                                    "internalType": "address",
                                    "name": "recipient",
                                    "type": "address",
                                },
                                {
                                    "internalType": "uint256",
                                    "name": "amountIn",
                                    "type": "uint256",
                                },
                                {
                                    "internalType": "uint256",
                                    "name": "amountOutMinimum",
                                    "type": "uint256",
                                },
                                {
                                    "internalType": "uint160",
                                    "name": "sqrtPriceLimitX96",
                                    "type": "uint160",
                                },
                            ],
                            "internalType": "struct ISwapRouter.ExactInputSingleParams",
                            "name": "params",
                            "type": "tuple",
                        }
                    ],
                    "name": "exactInputSingle",
                    "outputs": [
                        {
                            "internalType": "uint256",
                            "name": "amountOut",
                            "type": "uint256",
                        }
                    ],
                    "stateMutability": "nonpayable",
                    "type": "function",
                }
            ]

            logger.info(
                f"{self.somnia.account_index} | Swapping {amount_to_swap / (10 ** token_in['decimals']):.6f} "
                f"{token_in['symbol']} to {token_out['symbol']}"
            )

            # Approve tokens first
            approve_result = await self.somnia.web3.approve_token(
                token_address=token_in_address,
                spender_address=router_address,
                amount=amount_to_swap,
                wallet=self.somnia.wallet,
                chain_id=50312,  # Somnia chain ID
                token_abi=token_abi,
                explorer_url=EXPLORER_URL_SOMNIA,
            )

            if not approve_result:
                logger.error(
                    f"{self.somnia.account_index} | Failed to approve {token_in['symbol']}"
                )
                return False

            logger.success(
                f"{self.somnia.account_index} | Successfully approved {token_in['symbol']}"
            )

            # Prepare swap params
            swap_params = (
                token_in_address,  # tokenIn
                token_out_address,  # tokenOut
                DEFAULT_FEE,  # fee
                self.somnia.wallet.address,  # recipient
                amount_to_swap,  # amountIn
                0,  # amountOutMinimum (0 for simplicity)
                0,  # sqrtPriceLimitX96 (0 for no limit)
            )

            # Create router contract
            router_contract = self.somnia.web3.web3.eth.contract(
                address=router_address, abi=router_abi
            )

            # Build the transaction using the contract's functions
            swap_function = router_contract.functions.exactInputSingle(swap_params)

            # Get transaction parameters
            tx_params = {
                "from": self.somnia.wallet.address,
                "nonce": await self.somnia.web3.web3.eth.get_transaction_count(
                    self.somnia.wallet.address
                ),
                "chainId": 50312,  # Somnia chain ID
            }

            # Estimate gas
            gas_estimate = await swap_function.estimate_gas(tx_params)
            tx_params["gas"] = int(gas_estimate * 1.2)  # Add 20% buffer

            # Build the transaction
            transaction = await swap_function.build_transaction(tx_params)

            # Execute the transaction
            tx_hash = await self.somnia.web3.execute_transaction(
                tx_data=transaction,
                wallet=self.somnia.wallet,
                chain_id=50312,  # Somnia chain ID
                explorer_url=EXPLORER_URL_SOMNIA,
            )

            if tx_hash:
                logger.success(
                    f"{self.somnia.account_index} | Successfully swapped {token_in['symbol']} to {token_out['symbol']}. "
                    f"TX: {EXPLORER_URL_SOMNIA}{tx_hash}"
                )
                return True
            else:
                logger.error(
                    f"{self.somnia.account_index} | Failed to swap {token_in['symbol']} to {token_out['symbol']}"
                )
                return False

        except Exception as e:
            logger.error(f"{self.somnia.account_index} | Swap error: {e}")
            return False

    # Method to swap tokens to native STT
    async def swap_tokens_to_native_stt(self, token_in, amount_to_swap):
        """Swap tokens for native STT"""
        try:
            router_address = Web3.to_checksum_address(ROUTER_ADDRESS)
            token_in_address = Web3.to_checksum_address(token_in["address"])
            wstt_address = Web3.to_checksum_address(WSTT_ADDRESS)

            # ABIs
            token_abi = [
                {
                    "inputs": [
                        {
                            "internalType": "address",
                            "name": "spender",
                            "type": "address",
                        },
                        {
                            "internalType": "uint256",
                            "name": "amount",
                            "type": "uint256",
                        },
                    ],
                    "name": "approve",
                    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function",
                },
            ]

            router_abi = [
                {
                    "inputs": [
                        {
                            "components": [
                                {
                                    "internalType": "address",
                                    "name": "tokenIn",
                                    "type": "address",
                                },
                                {
                                    "internalType": "address",
                                    "name": "tokenOut",
                                    "type": "address",
                                },
                                {
                                    "internalType": "uint24",
                                    "name": "fee",
                                    "type": "uint24",
                                },
                                {
                                    "internalType": "address",
                                    "name": "recipient",
                                    "type": "address",
                                },
                                {
                                    "internalType": "uint256",
                                    "name": "deadline",
                                    "type": "uint256",
                                },
                                {
                                    "internalType": "uint256",
                                    "name": "amountIn",
                                    "type": "uint256",
                                },
                                {
                                    "internalType": "uint256",
                                    "name": "amountOutMinimum",
                                    "type": "uint256",
                                },
                                {
                                    "internalType": "uint160",
                                    "name": "sqrtPriceLimitX96",
                                    "type": "uint160",
                                },
                            ],
                            "internalType": "struct ISwapRouter.ExactInputSingleParams",
                            "name": "params",
                            "type": "tuple",
                        }
                    ],
                    "name": "exactInputSingle",
                    "outputs": [
                        {
                            "internalType": "uint256",
                            "name": "amountOut",
                            "type": "uint256",
                        }
                    ],
                    "stateMutability": "nonpayable",
                    "type": "function",
                },
                {
                    "inputs": [
                        {"internalType": "bytes[]", "name": "data", "type": "bytes[]"}
                    ],
                    "name": "multicall",
                    "outputs": [
                        {
                            "internalType": "bytes[]",
                            "name": "results",
                            "type": "bytes[]",
                        }
                    ],
                    "stateMutability": "payable",
                    "type": "function",
                },
                {
                    "inputs": [
                        {
                            "internalType": "uint256",
                            "name": "amountMinimum",
                            "type": "uint256",
                        },
                        {
                            "internalType": "address",
                            "name": "recipient",
                            "type": "address",
                        },
                    ],
                    "name": "unwrapWETH9",
                    "outputs": [],
                    "stateMutability": "payable",
                    "type": "function",
                },
            ]

            logger.info(
                f"{self.somnia.account_index} | Swapping {amount_to_swap / (10 ** token_in['decimals']):.6f} "
                f"{token_in['symbol']} to STT (native)"
            )

            # Approve tokens first
            approve_result = await self.somnia.web3.approve_token(
                token_address=token_in_address,
                spender_address=router_address,
                amount=amount_to_swap,
                wallet=self.somnia.wallet,
                chain_id=50312,  # Somnia chain ID
                token_abi=token_abi,
                explorer_url=EXPLORER_URL_SOMNIA,
            )

            if not approve_result:
                logger.error(
                    f"{self.somnia.account_index} | Failed to approve {token_in['symbol']}"
                )
                return False

            logger.success(
                f"{self.somnia.account_index} | Successfully approved {token_in['symbol']}"
            )

            # Create router contract
            router_contract = self.somnia.web3.web3.eth.contract(
                address=router_address, abi=router_abi
            )

            # Set deadline to 20 minutes from now
            latest_block = await self.somnia.web3.web3.eth.get_block("latest")
            deadline = int(latest_block.timestamp) + 1200

            # Step 1: Prepare parameters for exactInputSingle (token to WSTT)
            swap_params = (
                token_in_address,  # tokenIn
                wstt_address,  # tokenOut (WSTT)
                500,  # fee (0.05%)
                router_address,  # recipient (router itself for unwrapping)
                deadline,  # deadline
                amount_to_swap,  # amountIn
                0,  # amountOutMinimum (0 for simplicity)
                0,  # sqrtPriceLimitX96 (0 for no limit)
            )

            # Try alternative fees if first attempt fails
            for fee in FEE_TIERS:  # Try 0.05%, 0.3%, and 1% fees
                swap_params = (
                    token_in_address,  # tokenIn
                    wstt_address,  # tokenOut (WSTT)
                    fee,  # fee
                    router_address,  # recipient (router itself for unwrapping)
                    deadline,  # deadline
                    amount_to_swap,  # amountIn
                    0,  # amountOutMinimum (0 for simplicity)
                    0,  # sqrtPriceLimitX96 (0 for no limit)
                )

                # Encode the exactInputSingle call data
                exact_input_single_data = router_contract.encodeABI(
                    fn_name="exactInputSingle", args=[swap_params]
                )

                # Step 2: Encode the unwrapWETH9 call data
                # This unwraps WSTT to native STT and sends it to the wallet address
                unwrap_data = router_contract.encodeABI(
                    fn_name="unwrapWETH9",
                    args=[0, self.somnia.wallet.address],  # minAmount, recipient
                )

                # Create a multicall to execute both operations in one transaction
                multicall_fn = router_contract.functions.multicall(
                    [exact_input_single_data, unwrap_data]
                )

                # Get transaction parameters
                tx_params = {
                    "from": self.somnia.wallet.address,
                    "nonce": await self.somnia.web3.web3.eth.get_transaction_count(
                        self.somnia.wallet.address
                    ),
                    "chainId": 50312,  # Somnia chain ID
                }

                # Try to estimate gas
                try:
                    gas_estimate = await multicall_fn.estimate_gas(tx_params)
                    tx_params["gas"] = int(gas_estimate * 1.2)  # Add 20% buffer
                    logger.info(
                        f"{self.somnia.account_index} | Gas estimation successful with {fee/10000}% fee: {gas_estimate}"
                    )

                    # If successful, build the transaction
                    transaction = await multicall_fn.build_transaction(tx_params)

                    # Execute the transaction
                    tx_hash = await self.somnia.web3.execute_transaction(
                        tx_data=transaction,
                        wallet=self.somnia.wallet,
                        chain_id=50312,
                        explorer_url=EXPLORER_URL_SOMNIA,
                    )

                    if tx_hash:
                        logger.success(
                            f"{self.somnia.account_index} | Successfully swapped {token_in['symbol']} to STT. "
                            f"TX: {EXPLORER_URL_SOMNIA}{tx_hash}"
                        )
                        return True
                    else:
                        logger.error(
                            f"{self.somnia.account_index} | Failed to swap {token_in['symbol']} to STT"
                        )
                        # Try next fee
                        continue
                except Exception as e:
                    logger.error(
                        f"{self.somnia.account_index} | Gas estimation failed with {fee/10000}% fee: {e}"
                    )
                    # Try next fee
                    continue

            # If all fee attempts failed
            logger.error(
                f"{self.somnia.account_index} | All fee attempts failed for swap {token_in['symbol']} to STT"
            )
            return False

        except Exception as e:
            logger.error(f"{self.somnia.account_index} | Swap error: {e}")
            return False

    # Method to swap native STT to tokens
    async def swap_native_stt_to_token(self, token_out, amount_in):
        """Swap native STT for tokens"""
        try:
            router_address = Web3.to_checksum_address(ROUTER_ADDRESS)
            token_out_address = Web3.to_checksum_address(token_out["address"])
            wstt_address = Web3.to_checksum_address(WSTT_ADDRESS)

            logger.info(
                f"{self.somnia.account_index} | Swapping {amount_in / 10**18:.6f} "
                f"STT (native) to {token_out['symbol']}"
            )

            # Router ABI with the correct parameters for exactInputSingle
            router_abi = [
                {
                    "inputs": [
                        {
                            "components": [
                                {
                                    "internalType": "address",
                                    "name": "tokenIn",
                                    "type": "address",
                                },
                                {
                                    "internalType": "address",
                                    "name": "tokenOut",
                                    "type": "address",
                                },
                                {
                                    "internalType": "uint24",
                                    "name": "fee",
                                    "type": "uint24",
                                },
                                {
                                    "internalType": "address",
                                    "name": "recipient",
                                    "type": "address",
                                },
                                {
                                    "internalType": "uint256",
                                    "name": "deadline",
                                    "type": "uint256",
                                },
                                {
                                    "internalType": "uint256",
                                    "name": "amountIn",
                                    "type": "uint256",
                                },
                                {
                                    "internalType": "uint256",
                                    "name": "amountOutMinimum",
                                    "type": "uint256",
                                },
                                {
                                    "internalType": "uint160",
                                    "name": "sqrtPriceLimitX96",
                                    "type": "uint160",
                                },
                            ],
                            "internalType": "struct ISwapRouter.ExactInputSingleParams",
                            "name": "params",
                            "type": "tuple",
                        }
                    ],
                    "name": "exactInputSingle",
                    "outputs": [
                        {
                            "internalType": "uint256",
                            "name": "amountOut",
                            "type": "uint256",
                        }
                    ],
                    "stateMutability": "payable",
                    "type": "function",
                }
            ]

            # Create router contract
            router_contract = self.somnia.web3.web3.eth.contract(
                address=router_address, abi=router_abi
            )

            # Set deadline to 20 minutes from now
            latest_block = await self.somnia.web3.web3.eth.get_block("latest")
            deadline = int(latest_block.timestamp) + 1200

            # Try different fee values (0.05%, 0.3%, 1%)
            for fee in FEE_TIERS:
                # Prepare swap parameters - when swapping ETH, we use WETH/WSTT as tokenIn
                swap_params = (
                    wstt_address,  # tokenIn (WSTT - wrapped STT)
                    token_out_address,  # tokenOut
                    fee,  # fee
                    self.somnia.wallet.address,  # recipient
                    deadline,  # deadline
                    amount_in,  # amountIn
                    0,  # amountOutMinimum (0 for simplicity)
                    0,  # sqrtPriceLimitX96 (0 for no limit)
                )

                # Create the function call
                swap_function = router_contract.functions.exactInputSingle(swap_params)

                # Transaction parameters - include value to send STT
                tx_params = {
                    "from": self.somnia.wallet.address,
                    "value": amount_in,  # Sending STT with the transaction
                    "nonce": await self.somnia.web3.web3.eth.get_transaction_count(
                        self.somnia.wallet.address
                    ),
                    "chainId": 50312,  # Somnia chain ID
                }

                # Estimate gas
                try:
                    gas_estimate = await swap_function.estimate_gas(tx_params)
                    tx_params["gas"] = int(gas_estimate * 1.2)  # Add 20% buffer
                    logger.info(
                        f"{self.somnia.account_index} | Gas estimation successful with {fee/10000}% fee: {gas_estimate}"
                    )

                    # If successful, build the transaction
                    transaction = await swap_function.build_transaction(tx_params)

                    # Execute the transaction
                    tx_hash = await self.somnia.web3.execute_transaction(
                        tx_data=transaction,
                        wallet=self.somnia.wallet,
                        chain_id=50312,
                        explorer_url=EXPLORER_URL_SOMNIA,
                    )

                    if tx_hash:
                        logger.success(
                            f"{self.somnia.account_index} | Successfully swapped STT to {token_out['symbol']}. "
                            f"TX: {EXPLORER_URL_SOMNIA}{tx_hash}"
                        )
                        return True
                    else:
                        logger.error(
                            f"{self.somnia.account_index} | Failed to swap STT to {token_out['symbol']}"
                        )
                        # Try next fee
                        continue
                except Exception as e:
                    logger.error(
                        f"{self.somnia.account_index} | Gas estimation failed with {fee/10000}% fee: {e}"
                    )
                    # Continue to next fee value
                    continue

            # If all fee attempts failed
            logger.error(
                f"{self.somnia.account_index} | All fee attempts failed for swap STT to {token_out['symbol']}"
            )
            return False

        except Exception as e:
            logger.error(
                f"{self.somnia.account_index} | Failed to swap STT to token: {e}"
            )
            return False
