from eth_account import Account
from loguru import logger
import primp
import random
import asyncio

from src.model.somnia_network.campaigns import Campaigns
from src.model.projects.swaps.quickswap.instance import Quickswap
from src.model.projects.mints.mintaura import Mintaura
from src.model.projects.deploy.mintair import Mintair
from src.model.projects.mints.alze import Alze
from src.model.projects.mints.nerzo import Nerzo
from src.model.projects.others import Quills
from src.model.somnia_network.instance import Somnia
from src.model.help.stats import WalletStats
from src.model.onchain.web3_custom import Web3Custom
from src.utils.client import create_client
from src.utils.config import Config
from src.model.database.db_manager import Database
from src.utils.telegram_logger import send_telegram_message
from src.utils.decorators import retry_async


class Start:
    def __init__(
        self,
        account_index: int,
        proxy: str,
        private_key: str,
        config: Config,
        discord_token: str,
        twitter_token: str,
    ):
        self.account_index = account_index
        self.proxy = proxy
        self.private_key = private_key
        self.config = config
        self.discord_token = discord_token
        self.twitter_token = twitter_token

        self.session: primp.AsyncClient | None = None
        self.somnia_web3: Web3Custom | None = None
        self.somnia_instance: Somnia | None = None

        self.wallet = Account.from_key(self.private_key)
        self.wallet_address = self.wallet.address

    @retry_async(default_value=False)
    async def initialize(self):
        try:
            self.session = await create_client(
                self.proxy, self.config.OTHERS.SKIP_SSL_VERIFICATION
            )
            self.somnia_web3 = await Web3Custom.create(
                self.account_index,
                self.config.RPCS.SOMNIA,
                self.config.OTHERS.USE_PROXY_FOR_RPC,
                self.proxy,
                self.config.OTHERS.SKIP_SSL_VERIFICATION,
            )

            self.somnia_instance = Somnia(
                self.account_index,
                self.session,
                self.somnia_web3,
                self.config,
                self.wallet,
                self.discord_token,
                self.twitter_token,
                self.proxy,
            )
            if not await self.somnia_instance.login():
                return False

            return True
        except Exception as e:
            logger.error(f"{self.account_index} | Error: {e}")
            raise

    async def flow(self):
        try:
            try:
                wallet_stats = WalletStats(self.config, self.somnia_web3)
                await wallet_stats.get_wallet_stats(
                    self.private_key, self.account_index
                )
            except Exception as e:
                pass

            db = Database()
            try:
                tasks = await db.get_wallet_pending_tasks(self.private_key)
            except Exception as e:
                if "no such table: wallets" in str(e):
                    logger.error(
                        f"{self.account_index} | Database not created or wallets table not found"
                    )
                    if self.config.SETTINGS.SEND_TELEGRAM_LOGS:
                        error_message = (
                            f"⚠️ Database error\n\n"
                            f"Account #{self.account_index}\n"
                            f"Wallet: <code>{self.private_key[:6]}...{self.private_key[-4:]}</code>\n"
                            f"Error: Database not created or wallets table not found"
                        )
                        await send_telegram_message(self.config, error_message)
                    return False
                else:
                    logger.error(
                        f"{self.account_index} | Error getting tasks from database: {e}"
                    )
                    raise

            if not tasks:
                logger.warning(
                    f"{self.account_index} | No pending tasks found in database for this wallet. Exiting..."
                )
                if self.somnia_web3:
                    await self.somnia_web3.cleanup()
                return True

            pause = random.randint(
                self.config.SETTINGS.RANDOM_INITIALIZATION_PAUSE[0],
                self.config.SETTINGS.RANDOM_INITIALIZATION_PAUSE[1],
            )
            logger.info(
                f"[{self.account_index}] Sleeping for {pause} seconds before start..."
            )
            await asyncio.sleep(pause)

            task_plan_msg = [f"{i+1}. {task['name']}" for i, task in enumerate(tasks)]
            logger.info(
                f"{self.account_index} | Task execution plan: {' | '.join(task_plan_msg)}"
            )

            completed_tasks = []
            failed_tasks = []

            # Выполняем задачи
            for task in tasks:
                task_name = task["name"]
                if task_name == "skip":
                    logger.info(f"{self.account_index} | Skipping task: {task_name}")
                    await db.update_task_status(
                        self.private_key, task_name, "completed"
                    )
                    completed_tasks.append(task_name)
                    await self.sleep(task_name)
                    continue

                logger.info(f"{self.account_index} | Executing task: {task_name}")

                success = await self.execute_task(task_name)

                if success:
                    await db.update_task_status(
                        self.private_key, task_name, "completed"
                    )
                    completed_tasks.append(task_name)
                    await self.sleep(task_name)
                else:
                    failed_tasks.append(task_name)
                    if not self.config.FLOW.SKIP_FAILED_TASKS:
                        logger.error(
                            f"{self.account_index} | Failed to complete task {task_name}. Stopping wallet execution."
                        )
                        break
                    else:
                        logger.warning(
                            f"{self.account_index} | Failed to complete task {task_name}. Skipping to next task."
                        )
                        await self.sleep(task_name)

            # Отправляем сообщение в Telegram только в конце всей работы
            if self.config.SETTINGS.SEND_TELEGRAM_LOGS:
                message = (
                    f"🤖 StarLabs Somnia Bot Report\n\n"
                    f"💳 Wallet: {self.account_index} | <code>{self.private_key[:6]}...{self.private_key[-4:]}</code>\n\n"
                )

                if completed_tasks:
                    message += f"✅ Completed Tasks:\n"
                    for i, task in enumerate(completed_tasks, 1):
                        message += f"{i}. {task}\n"
                    message += "\n"

                if failed_tasks:
                    message += f"❌ Failed Tasks:\n"
                    for i, task in enumerate(failed_tasks, 1):
                        message += f"{i}. {task}\n"
                    message += "\n"

                total_tasks = len(tasks)
                completed_count = len(completed_tasks)
                message += (
                    f"📊 Statistics:\n"
                    f"Total Tasks: {total_tasks}\n"
                    f"Completed: {completed_count}\n"
                    f"Failed: {len(failed_tasks)}\n"
                    f"Success Rate: {(completed_count/total_tasks)*100:.1f}%\n\n"
                    f"⚙️ Settings:\n"
                    f"Skip Failed: {'Yes' if self.config.FLOW.SKIP_FAILED_TASKS else 'No'}\n"
                )

                await send_telegram_message(self.config, message)

            return len(failed_tasks) == 0

        except Exception as e:
            logger.error(f"{self.account_index} | Error: {e}")

            if self.config.SETTINGS.SEND_TELEGRAM_LOGS:
                error_message = (
                    f"⚠️ Error Report\n\n"
                    f"Account #{self.account_index}\n"
                    f"Wallet: <code>{self.private_key[:6]}...{self.private_key[-4:]}</code>\n"
                    f"Error: {str(e)}"
                )
                await send_telegram_message(self.config, error_message)

            return False
        finally:
            # Cleanup resources
            try:
                if self.somnia_web3:
                    await self.somnia_web3.cleanup()
                logger.info(f"{self.account_index} | All sessions closed successfully")
            except Exception as e:
                logger.error(f"{self.account_index} | Error during cleanup: {e}")

            pause = random.randint(
                self.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACCOUNTS[0],
                self.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACCOUNTS[1],
            )
            logger.info(
                f"[{self.account_index}] Sleeping for {pause} seconds before next account..."
            )
            await asyncio.sleep(pause)

    async def execute_task(self, task):
        """Execute a single task"""
        task = task.lower()

        if task == "connect_socials":
            return await self.somnia_instance.connect_socials()

        if task == "faucet":
            return await self.somnia_instance.request_faucet()

        if task == "campaigns":
            campaigns = Campaigns(self.somnia_instance)
            return await campaigns.complete_campaigns()

        # Handle specific campaign tasks
        if task.startswith("somnia_quest_"):
            campaigns = Campaigns(self.somnia_instance)
            return await campaigns.execute_specific_quest(task)

        if task == "somnia_network_set_username":
            return await self.somnia_instance.set_username()

        if task == "send_tokens":
            return await self.somnia_instance.send_tokens_task()

        if task == "mint_ping_pong":
            return await self.somnia_instance.mint_ping_pong()

        if task == "swaps_ping_pong":
            return await self.somnia_instance.swaps_ping_pong()

        if task == "quills_chat":
            quills = Quills(
                self.account_index, self.somnia_web3, self.config, self.wallet
            )
            return await quills.chat()

        if "nerzo" in task:
            nerzo = Nerzo(
                self.account_index, self.somnia_web3, self.config, self.wallet
            )
            if task == "nerzo_shannon":
                return await nerzo.mint_shannon()
            elif task == "nerzo_nee":
                return await nerzo.mint_nee()

        if "alze" in task:
            alze = Alze(self.account_index, self.somnia_web3, self.config, self.wallet)
            if task == "alze_yappers":
                return await alze.mint_yappers()

        if task == "mintair_deploy":
            mintair = Mintair(
                self.account_index, self.somnia_web3, self.config, self.wallet
            )
            return await mintair.deploy_mintair()

        if "mintaura" in task:
            mintaura = Mintaura(
                self.account_index, self.somnia_web3, self.config, self.wallet
            )
            if task == "mintaura_somni":
                return await mintaura.mint_somni()

        if task == "somnia_network_info":
            return await self.somnia_instance.show_account_info()

        # if task == "quickswap":
        #     quickswap = Quickswap(self.somnia_instance)
        #     return await quickswap.swaps()

        logger.error(f"{self.account_index} | Unknown task: {task}")
        return False

    async def sleep(self, task_name: str):
        """Делает рандомную паузу между действиями"""
        pause = random.randint(
            self.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[0],
            self.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[1],
        )
        logger.info(
            f"{self.account_index} | Sleeping {pause} seconds after {task_name}"
        )
        await asyncio.sleep(pause)
