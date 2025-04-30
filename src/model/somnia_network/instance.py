import asyncio
import random
from loguru import logger
from eth_account import Account
import primp
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from src.model.somnia_network.ping_pong_swaps import PingPongSwaps
from src.model.somnia_network.send_random_tokens import RandomTokenSender
from src.model.somnia_network.connect_socials import ConnectSocials
from src.model.onchain.web3_custom import Web3Custom
from src.utils.decorators import retry_async
from src.utils.config import Config
from src.model.somnia_network.faucet import FaucetService


class Somnia:
    def __init__(
        self,
        account_index: int,
        session: primp.AsyncClient,
        web3: Web3Custom,
        config: Config,
        wallet: Account,
        discord_token: str,
        twitter_token: str,
        proxy: str,
    ):
        self.account_index = account_index
        self.session = session
        self.web3 = web3
        self.config = config
        self.wallet = wallet
        self.discord_token = discord_token
        self.twitter_token = twitter_token
        self.proxy = proxy
        # Инициализируем сервисы
        self.somnia_login_token: str = ""

    @retry_async(default_value=False)
    async def login(self) -> bool:
        try:
            message_to_sign = '{"onboardingUrl":"https://quest.somnia.network"}'
            signature = self.web3.get_signature(message_to_sign, self.wallet)

            headers = {
                "accept": "application/json",
                "origin": "https://quest.somnia.network",
                "referer": "https://quest.somnia.network/connect?redirect=%2Faccount",
            }

            json_data = {
                "signature": "0x" + signature,
                "walletAddress": self.wallet.address,
            }

            response = await self.session.post(
                "https://quest.somnia.network/api/auth/onboard",
                headers=headers,
                json=json_data,
            )

            if not response.json()["token"]:
                raise Exception(
                    f"Failed to login: {response.status_code} | {response.text}"
                )

            self.somnia_login_token = response.json()["token"]
            logger.success(f"{self.account_index} | Successfully logged in Somnia")
            return True

        except Exception as e:
            random_pause = random.randint(
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.account_index} | Login error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=None)
    async def get_account_info(self) -> dict | None:
        """
        Get account info, returns None if failed. Example of response:
        {
            "id": int,
            "walletAddress": str,
            "username": str | None,
            "discordName": str | None,
            "twitterName": str | None,
            "isOg": bool,
            "type": str,
            "referralCode": str | None,
            "telegramName": str | None,
            "imgUrl": str | None,
            "createdAt": str,
            "updatedAt": str,
            "deletedAt": str | None,
            "referralPoint": int,
            "referralCount": int
        }
        """
        try:
            headers = {
                "accept": "application/json",
                "authorization": f"Bearer {self.somnia_login_token}",
                "referer": "https://quest.somnia.network/account",
            }

            response = await self.session.get(
                "https://quest.somnia.network/api/users/me", headers=headers
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get account info: {response.status_code} | {response.text}"
                )

            return response.json()

        except Exception as e:
            random_pause = random.randint(
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.account_index} | Get account info error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=None)
    async def get_account_stats(self) -> dict | None:
        """
        Get account stats, returns None if failed. Example of response:
        {
            "walletAddress": str,
            "totalPoints": str,
            "totalBoosters": str,
            "finalPoints": str,
            "rank": str | None,
            "seasonId": str,
            "totalReferrals": str,
            "questsCompleted": str,
            "dailyBooster": float,
            "streakCount": str
        }
        """
        try:
            headers = {
                "accept": "application/json",
                "authorization": f"Bearer {self.somnia_login_token}",
                "referer": "https://quest.somnia.network/account",
            }

            response = await self.session.get(
                "https://quest.somnia.network/api/stats", headers=headers
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get account info: {response.status_code} | {response.text}"
                )

            return response.json()

        except Exception as e:
            random_pause = random.randint(
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.account_index} | Get account info error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=None)
    async def get_account_referrals(self) -> dict | None:
        """
        Get account referrals, returns None if failed. Example of response:
        {
            "isOg": bool,
            "id": int,
            "walletAddress": str,
            "referralCode": str,
            "type": str,
            "username": str | None,
            "discordName": str | None,
            "twitterName": str | None,
            "telegramName": str | None,
            "imgUrl": str | None,
            "createdAt": str,
            "updatedAt": str,
            "deletedAt": str | None
        }
        """
        try:
            headers = {
                "accept": "application/json",
                "authorization": f"Bearer {self.somnia_login_token}",
                "referer": "https://quest.somnia.network/account",
            }

            response = await self.session.get(
                "https://quest.somnia.network/api/referrals", headers=headers
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get account info: {response.status_code} | {response.text}"
                )

            return response.json()

        except Exception as e:
            random_pause = random.randint(
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.account_index} | Get account info error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=False)
    async def set_username(self):
        try:
            vowels = "aeiouy"
            consonants = "bcdfghjklmnpqrstvwxz"

            # Generate random username length between 5 and 8 characters
            name_length = random.randint(5, 8)

            # Start with a consonant or vowel randomly
            start_with_consonant = random.choice([True, False])

            username = ""
            for i in range(name_length):
                if (i % 2 == 0 and start_with_consonant) or (
                    i % 2 == 1 and not start_with_consonant
                ):
                    username += random.choice(consonants)
                else:
                    username += random.choice(vowels)

            # 50% chance to add digits at the end
            if random.random() < 0.5:
                # Add 1-3 random digits
                digit_count = random.randint(1, 3)
                for _ in range(digit_count):
                    username += str(random.randint(0, 9))

            headers = {
                "accept": "application/json",
                "authorization": f"Bearer {self.somnia_login_token}",
                "content-type": "application/json",
                "origin": "https://quest.somnia.network",
                "referer": "https://quest.somnia.network/account",
            }

            json_data = {
                "username": username,
            }

            response = await self.session.patch(
                "https://quest.somnia.network/api/users/username",
                headers=headers,
                json=json_data,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to set username: {response.status_code} | {response.text}"
                )

            if response.json()["message"] != "Success":
                raise Exception(
                    f"Failed to set username: {response.status_code} | {response.text}"
                )

            logger.success(
                f"{self.account_index} | Successfully set username: {username}"
            )

            return True
        except Exception as e:
            random_pause = random.randint(
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.account_index} | Set username error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            return False

    # Удобный метод-прокси для faucet, если нужен
    async def request_faucet(self):
        self.faucet_service = FaucetService(self)
        return await self.faucet_service.request_faucet()

    async def mint_ping_pong(self):
        self.faucet_service = FaucetService(self)
        return await self.faucet_service.request_ping_pong_faucet()

    async def swaps_ping_pong(self):
        self.ping_pong_swaps_service = PingPongSwaps(self)
        return await self.ping_pong_swaps_service.swaps()

    async def connect_socials(self):
        self.connect_socials_service = ConnectSocials(self)
        return await self.connect_socials_service.connect_socials()

    async def send_tokens_task(self):
        self.send_tokens_service = RandomTokenSender(self)
        return await self.send_tokens_service.send_tokens()

    async def show_account_info(self):
        try:
            account_info = await self.get_account_info()
            account_stats = await self.get_account_stats()
            if account_info and account_stats:
                console = Console()

                # Create a table for account info
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="green")

                # Add account information
                table.add_row("Address", str(account_info["walletAddress"]))
                table.add_row("Somnia Username", str(account_info["username"] or "Not set"))
                table.add_row("Total Points", str(account_stats["totalPoints"]))
                table.add_row("Total Boosters", str(account_stats["totalBoosters"]))
                table.add_row("Final Points", str(account_stats["finalPoints"]))
                table.add_row("Rank", str(account_stats["rank"] or "Not ranked"))
                table.add_row("Total Referrals", str(account_stats["totalReferrals"]))
                table.add_row("Quests Completed", str(account_stats["questsCompleted"]))
                table.add_row("Daily Booster", str(account_stats["dailyBooster"]))
                table.add_row("Streak Count", str(account_stats["streakCount"]))
                table.add_row("Discord", str(account_info["discordName"] or "Not connected"))
                table.add_row("Twitter", str(account_info["twitterName"] or "Not connected"))
                table.add_row("Telegram", str(account_info["telegramName"] or "Not connected"))
                table.add_row("Referral Code", str(account_info["referralCode"] or "Not set"))
                table.add_row("Referral Points", str(account_info["referralPoint"]))

                # Print the table
                console.print(
                    f"\n[bold yellow]Account #{self.account_index} Information:[/bold yellow]"
                )
                console.print(table)
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"{self.account_index} | Show account info error: {e}")
            return False
