import asyncio
import random
from loguru import logger
from web3 import Web3
from src.model.somnia_network.constants import SomniaProtocol
from src.utils.decorators import retry_async
from src.utils.constants import EXPLORER_URL_SOMNIA
from eth_account import Account


class PingPongSwaps:
    def __init__(self, instance: SomniaProtocol):
        self.somnia = instance

    async def swaps(self):
        """Execute swaps between PING and PONG tokens"""
        try:
            # Contract addresses
            ping_token_address = Web3.to_checksum_address(
                "0x33e7fab0a8a5da1a923180989bd617c9c2d1c493"
            )
            pong_token_address = Web3.to_checksum_address(
                "0x9beaA0016c22B646Ac311Ab171270B0ECf23098F"
            )
            router_address = Web3.to_checksum_address(
                "0x6aac14f090a35eea150705f72d90e4cdc4a49b2c"
            )

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
                    "stateMutability": "nonpayable",
                    "type": "function",
                }
            ]

            # Check balances of both tokens first
            ping_balance = await self.somnia.web3.get_token_balance(
                self.somnia.wallet.address,
                ping_token_address,
                token_abi,
                decimals=18,
                symbol="PING",
            )

            pong_balance = await self.somnia.web3.get_token_balance(
                self.somnia.wallet.address,
                pong_token_address,
                token_abi,
                decimals=18,
                symbol="PONG",
            )

            logger.info(
                f"{self.somnia.account_index} | Token balances: {ping_balance.formatted:.6f} PING, {pong_balance.formatted:.6f} PONG"
            )

            # Check if both balances are zero
            if ping_balance.wei == 0 and pong_balance.wei == 0:
                logger.error(
                    f"{self.somnia.account_index} | No tokens to swap. Both PING and PONG balances are zero."
                )
                return False

            # Получаем количество свапов из конфига
            min_txs, max_txs = self.somnia.config.SOMNIA_NETWORK.SOMNIA_SWAPS.NUMBER_OF_SWAPS
            num_swaps = random.randint(min_txs, max_txs)

            logger.info(
                f"{self.somnia.account_index} | Planning to execute {num_swaps} swaps"
            )

            success_count = 0

            for i in range(num_swaps):
                # Determine which token to swap based on balances
                # Always check updated balances before each swap
                if i > 0:
                    # Re-check balances after previous swap
                    ping_balance = await self.somnia.web3.get_token_balance(
                        self.somnia.wallet.address,
                        ping_token_address,
                        token_abi,
                        decimals=18,
                        symbol="PING",
                    )

                    pong_balance = await self.somnia.web3.get_token_balance(
                        self.somnia.wallet.address,
                        pong_token_address,
                        token_abi,
                        decimals=18,
                        symbol="PONG",
                    )

                    logger.info(
                        f"{self.somnia.account_index} | Updated token balances: {ping_balance.formatted:.6f} PING, {pong_balance.formatted:.6f} PONG"
                    )

                # Skip if both tokens have zero balance now
                if ping_balance.wei == 0 and pong_balance.wei == 0:
                    logger.warning(
                        f"{self.somnia.account_index} | No tokens left to swap. Ending swap sequence."
                    )
                    break

                # Decide which token to swap
                if ping_balance.wei > 0 and pong_balance.wei > 0:
                    # If both have balance, randomly select or use larger balance
                    if random.choice([True, False]):
                        token_in_address = ping_token_address
                        token_in_name = "PING"
                        token_out_address = pong_token_address
                        token_out_name = "PONG"
                        token_balance = ping_balance
                    else:
                        token_in_address = pong_token_address
                        token_in_name = "PONG"
                        token_out_address = ping_token_address
                        token_out_name = "PING"
                        token_balance = pong_balance
                elif ping_balance.wei > 0:
                    # Only PING has balance
                    token_in_address = ping_token_address
                    token_in_name = "PING"
                    token_out_address = pong_token_address
                    token_out_name = "PONG"
                    token_balance = ping_balance
                else:
                    # Only PONG has balance
                    token_in_address = pong_token_address
                    token_in_name = "PONG"
                    token_out_address = ping_token_address
                    token_out_name = "PING"
                    token_balance = pong_balance

                logger.info(
                    f"{self.somnia.account_index} | Swap {i+1}/{num_swaps}: {token_in_name} to {token_out_name}"
                )

                # Calculate amount to swap (10-35% of balance)
                min_percent, max_percent = (
                    self.somnia.config.SOMNIA_NETWORK.SOMNIA_SWAPS.BALANCE_PERCENT_TO_SWAP
                )
                random_percentage = random.uniform(min_percent, max_percent)
                amount_to_swap = int(token_balance.wei * (random_percentage / 100))

                logger.info(
                    f"{self.somnia.account_index} | Swapping {token_balance.formatted * random_percentage / 100:.4f} "
                    f"{token_in_name} to {token_out_name} ({random_percentage:.2f}% of balance)"
                )

                # Approve tokens
                approve_result = await self.somnia.web3.approve_token(
                    token_address=token_in_address,
                    spender_address=router_address,
                    amount=amount_to_swap,
                    wallet=self.somnia.wallet,
                    chain_id=50312,  # Somnia chain ID
                    token_abi=token_abi,
                    explorer_url=EXPLORER_URL_SOMNIA,
                )

                if approve_result:
                    logger.success(
                        f"{self.somnia.account_index} | Successfully approved {token_in_name}"
                    )

                # Prepare swap params
                swap_params = (
                    token_in_address,
                    token_out_address,
                    500,  # Fee (0.05%)
                    self.somnia.wallet.address,
                    amount_to_swap,
                    0,  # amountOutMinimum (0 for simplicity)
                    0,  # sqrtPriceLimitX96 (0 for no limit)
                )

                # Create router contract
                router_contract = self.somnia.web3.web3.eth.contract(
                    address=router_address, abi=router_abi
                )

                # Prepare transaction using contract functions
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
                        f"{self.somnia.account_index} | Successfully swapped {token_in_name} to {token_out_name}. "
                        f"TX: {EXPLORER_URL_SOMNIA}{tx_hash}"
                    )
                    success_count += 1
                else:
                    logger.error(
                        f"{self.somnia.account_index} | Failed to swap {token_in_name} to {token_out_name}"
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
                f"{self.somnia.account_index} | Ping-pong swap error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            return False

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
