import random
import asyncio
import secrets
from loguru import logger

from src.model.help.discord import DiscordInviter
from src.model.help.twitter import Twitter
from src.model.somnia_network.constants import SomniaProtocol
from src.model.somnia_network.connect_socials import ConnectSocials
from src.utils.decorators import retry_async


SKIP_CAMPAIGNS_IDS = [
    9,
    7,
    11,
    12,
]


CAMPAIGNS_NAMES = {
    23: "Ecosystem on the Horizon",
    21: "QRusader",
    20: "Migration Discord Points",
    19: "SocialFi on Somnia",
    18: "Masks of the Void",
    17: "Intersection of DeFi & AI",
    16: "Mullet Cop",
    15: "Somnia Gaming Room",
    14: "Onchain Gaming Frenzy",
    13: "Netherak Demons",
    12: "Somnia Yapstorm",
    11: "Somnia Playground",
    10: "Darktable x Somnia",
    9: "Somnia Testnet Odyssey - Mascot Memecoin",
    8: "Somnia Testnet Odyssey - Socials",
    7: "Somnia Testnet Odyssey - Sharing is Caring",
    5: "Somnia Devnet Odyssey - Socials 2",
    2: "Somnia Devnet Odyssey - Socials",
    1: "Migration Campaign",
}

# Map task names to campaign IDs
CAMPAIGN_ID_MAPPING = {
    "somnia_quest_ecosystem_on_the_horizon": 23,
    "somnia_quest_qrusader": 21,
    "somnia_quest_migration_discord_points": 20,
    "somnia_quest_socialfi_on_somnia": 19,
    "somnia_quest_masks_of_the_void": 18,
    "somnia_quest_intersection_of_defi_ai": 17,
    "somnia_quest_mullet_cop": 16,
    "somnia_quest_somnia_gaming_room": 15,
    "somnia_quest_onchain_gaming_frenzy": 14,
    "somnia_quest_netherak_demons": 13,
    "somnia_quest_darktable_x_somnia": 10,
    "somnia_quest_testnet_odyssey_socials": 8,
    "somnia_quest_somnia_devnet_odyssey_socials_two": 5,
    "somnia_quest_somnia_devnet_odyssey_socials": 2,
    "somnia_quest_migration_campaign": 1,
}


class Campaigns:
    def __init__(self, somnia_instance: SomniaProtocol):
        self.somnia = somnia_instance
        self.twitter_instance: Twitter | None = None
        self.connect_socials = ConnectSocials(somnia_instance)

    async def execute_specific_quest(self, task_name: str):
        """
        Execute a specific quest based on task name.
        Returns True if the quest was completed successfully, False otherwise.
        """
        if not task_name.startswith("somnia_quest_"):
            logger.error(
                f"{self.somnia.account_index} | Invalid quest task name: {task_name}"
            )
            return False

        if task_name not in CAMPAIGN_ID_MAPPING:
            logger.error(
                f"{self.somnia.account_index} | Unknown campaign task: {task_name}"
            )
            return False

        campaign_id = CAMPAIGN_ID_MAPPING[task_name]
        logger.info(
            f"{self.somnia.account_index} | Executing specific campaign: {CAMPAIGNS_NAMES.get(campaign_id, 'Unknown')} (ID: {campaign_id})"
        )

        # Initialize Twitter account for campaign
        if not await self._initialize_twitter():
            return False

        campaigns = await self._get_all_campaigns()

        # Find the specific campaign
        target_campaign = None
        for campaign in campaigns:
            if campaign["id"] == campaign_id:
                target_campaign = campaign
                break

        if not target_campaign:
            logger.error(
                f"{self.somnia.account_index} | Campaign with ID {campaign_id} not found"
            )
            return False

        # Complete the specific campaign
        campaign_info = await self._get_campaign_info(campaign_id)
        logger.info(
            f"{self.somnia.account_index} | Completing campaign {campaign_info['name']}..."
        )

        for quest in campaign_info["quests"]:
            if not quest["isParticipated"] and quest["status"] == "OPEN":
                if not await self._complete_quest(quest):
                    logger.error(
                        f"{self.somnia.account_index} | Failed to complete quest {quest['title']} from campaign {campaign_info['name']}."
                    )

        return True

    async def complete_campaigns(self):
        try:
            logger.info(
                f"{self.somnia.account_index} | Starting campaigns completion..."
            )

            campaigns = await self._get_all_campaigns()

            if not await self._initialize_twitter():
                return False

            for campaign in campaigns:
                if campaign["id"] in SKIP_CAMPAIGNS_IDS:
                    continue

                campaign_info = await self._get_campaign_info(campaign["id"])

                logger.info(
                    f"{self.somnia.account_index} | Completing campaign {campaign_info['name']}..."
                )

                for quest in campaign_info["quests"]:
                    if not quest["isParticipated"] and quest["status"] == "OPEN":
                        if not await self._complete_quest(quest):
                            logger.error(
                                f"{self.somnia.account_index} | Failed to complete quest {quest['title']} from campaign {campaign_info['name']}. Skipping to the next campaign."
                            )

            return True

        except Exception as e:
            logger.error(f"{self.somnia.account_index} | Campaigns error: {e}.")
            return False

    async def _initialize_twitter(self):
        """Initialize Twitter instance for campaign completion"""
        try:
            while True:
                self.twitter_instance = Twitter(
                    self.somnia.account_index,
                    self.somnia.twitter_token,
                    self.somnia.proxy,
                    self.somnia.config,
                )
                ok = await self.twitter_instance.initialize()
                if not ok:
                    if (
                        not self.somnia.config.SOMNIA_NETWORK.SOMNIA_CAMPAIGNS.REPLACE_FAILED_TWITTER_ACCOUNT
                    ):
                        logger.error(
                            f"{self.somnia.account_index} | Failed to initialize twitter instance. Skipping campaigns completion."
                        )
                        return False
                    else:
                        if not await self._replace_twitter_token():
                            return False
                        continue
                break
            return True
        except Exception as e:
            logger.error(
                f"{self.somnia.account_index} | Error initializing Twitter: {e}"
            )
            return False

    @retry_async(default_value=False)
    async def _complete_quest(self, quest: dict):
        try:
            if quest["type"] == "TWITTER_FOLLOW" or quest["type"] == "RETWEET":
                if quest["type"] == "TWITTER_FOLLOW":
                    if await self.twitter_instance.follow(
                        quest["customConfig"]["twitterHandle"]
                    ):
                        return await self._verify_quest_completion(
                            quest, "social/twitter/follow"
                        )
                    else:
                        return False

                if quest["type"] == "RETWEET":
                    description = quest["description"]
                    if "like" in description.lower():
                        if not await self.twitter_instance.like(
                            quest["customConfig"]["tweetId"]
                        ):
                            return False

                    for _ in range(self.somnia.config.SETTINGS.ATTEMPTS):
                        ok = await self.twitter_instance.retweet(
                            quest["customConfig"]["tweetId"]
                        )
                        if not ok:
                            continue

                        return await self._verify_quest_completion(
                            quest, "social/twitter/retweet"
                        )

                    return False

            elif quest["type"] == "JOIN_DISCORD_SERVER":
                discord_inviter = DiscordInviter(
                    self.somnia.account_index,
                    self.somnia.discord_token,
                    self.somnia.proxy,
                    self.somnia.config,
                )
                description = quest["description"]
                if "https://discord.gg/" in description:
                    invite_code = (
                        description.split("https://discord.gg/")[1]
                        .split('"')[0]
                        .strip()
                    )
                else:
                    invite_code = (
                        quest["description"]
                        .split("https://discord.com/invite/")[1]
                        .split('"')[0]
                        .strip()
                    )

                if await discord_inviter.invite(invite_code):
                    return await self._verify_quest_completion(
                        quest, "social/discord/join"
                    )
                else:
                    return False

            elif quest["type"] == "LINK_USERNAME":
                return await self._verify_quest_completion(
                    quest, "social/verify-username"
                )

            elif quest["type"] == "CONNECT_DISCORD":
                return await self._verify_quest_completion(
                    quest, "social/discord/connect"
                )

            elif quest["type"] == "CONNECT_TWITTER":
                return await self._verify_quest_completion(
                    quest, "social/twitter/connect"
                )

            elif quest["type"] == "CONNECT_TELEGRAM":
                return await self._verify_quest_completion(
                    quest, "social/telegram/connect"
                )

            else:
                logger.error(
                    f"{self.somnia.account_index} | Unknown quest type: {quest['type']} | {quest['title']} | {quest['campaignId']}"
                )
                return False

        except Exception as e:
            random_pause = random.randint(
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            if "You have reached your daily limit for sending" in str(e):
                logger.error(
                    f"{self.somnia.account_index} | Twitter error. Try again later."
                )
                await asyncio.sleep(random_pause)
                return False

            logger.error(
                f"{self.somnia.account_index} | Complete quest error: {e}. Sleeping {random_pause} seconds..."
            )

            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=False)
    async def _verify_quest_completion(self, quest: dict, endpoint: str):
        try:
            random_pause = random.randint(
                self.somnia.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[0],
                self.somnia.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[1],
            )
            logger.info(
                f"{self.somnia.account_index} | Waiting for {random_pause} seconds before verifying quest completion..."
            )
            await asyncio.sleep(random_pause)

            headers = {
                "accept": "*/*",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "authorization": f"Bearer {self.somnia.somnia_login_token}",
                "content-type": "application/json",
                "origin": "https://quest.somnia.network",
                "priority": "u=1, i",
                "referer": f'https://quest.somnia.network/campaigns/{quest["campaignId"]}',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
            }

            json_data = {
                "questId": quest["id"],
            }

            response = await self.somnia.session.post(
                f"https://quest.somnia.network/api/{endpoint}",
                headers=headers,
                json=json_data,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to verify quest completion: {response.status_code} | {response.text}"
                )

            if response.json()["success"]:
                logger.success(
                    f"{self.somnia.account_index} | Quest completed: {quest['title']}"
                )
                return True
            else:
                logger.error(
                    f"{self.somnia.account_index} | Failed to verify quest completion: {response.json()['reason']}"
                )
                return False

        except Exception as e:
            random_pause = random.randint(
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.somnia.account_index} | Verify quest completion error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise e

    @retry_async(default_value=None)
    async def _get_campaign_info(self, campaign_id: int):
        try:
            headers = {
                "accept": "application/json",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "authorization": f"Bearer {self.somnia.somnia_login_token}",
                "content-type": "application/json",
                "priority": "u=1, i",
                "referer": f"https://quest.somnia.network/campaigns/{campaign_id}",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
            }

            response = await self.somnia.session.get(
                f"https://quest.somnia.network/api/campaigns/{campaign_id}",
                headers=headers,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get campaign info: {response.status_code} | {response.text}"
                )

            return response.json()

        except Exception as e:
            random_pause = random.randint(
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.somnia.account_index} | Get campaign info error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=None)
    async def _get_all_campaigns(self):
        try:
            headers = {
                "accept": "application/json",
                "accept-language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
                "authorization": f"Bearer {self.somnia.somnia_login_token}",
                "content-type": "application/json",
                "priority": "u=1, i",
                "referer": "https://quest.somnia.network/campaigns",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
            }

            response = await self.somnia.session.get(
                "https://quest.somnia.network/api/campaigns", headers=headers
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get all campaigns: {response.status_code} | {response.text}"
                )

            return response.json()

        except Exception as e:
            random_pause = random.randint(
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.somnia.account_index} | Get all campaigns error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    async def _replace_twitter_token(self) -> bool:
        """
        Replaces the current Twitter token with a new one from spare tokens.
        Returns True if replacement was successful, False otherwise.
        """
        try:
            async with self.somnia.config.lock:
                if (
                    not self.somnia.config.spare_twitter_tokens
                    or len(self.somnia.config.spare_twitter_tokens) == 0
                ):
                    logger.error(
                        f"{self.somnia.account_index} | Twitter token is invalid and no spare tokens available. Please check your twitter token!"
                    )
                    return False

                # Get a new token from the spare tokens list
                new_token = self.somnia.config.spare_twitter_tokens.pop(0)
                old_token = self.somnia.twitter_token
                self.somnia.twitter_token = new_token

                # Update the token in the file
                try:
                    with open("data/twitter_tokens.txt", "r", encoding="utf-8") as f:
                        tokens = f.readlines()

                    # Process tokens to replace old with new and remove duplicates
                    processed_tokens = []
                    replaced = False

                    for token in tokens:
                        stripped_token = token.strip()

                        # Skip if it's a duplicate of the new token
                        if stripped_token == new_token:
                            continue

                        # Replace old token with new token
                        if stripped_token == old_token:
                            if not replaced:
                                processed_tokens.append(f"{new_token}\n")
                                replaced = True
                        else:
                            processed_tokens.append(token)

                    # If we didn't replace anything (old token not found), add new token
                    if not replaced:
                        processed_tokens.append(f"{new_token}\n")

                    with open("data/twitter_tokens.txt", "w", encoding="utf-8") as f:
                        f.writelines(processed_tokens)

                    logger.info(
                        f"{self.somnia.account_index} | Replaced invalid Twitter token with a new one"
                    )

                    # Try to connect the new token
                    if await self.connect_socials.connect_twitter():
                        logger.success(
                            f"{self.somnia.account_index} | Successfully connected new Twitter token"
                        )
                        return True
                    else:
                        logger.error(
                            f"{self.somnia.account_index} | Failed to connect new Twitter token, trying another one..."
                        )
                        return False

                except Exception as file_err:
                    logger.error(
                        f"{self.somnia.account_index} | Failed to update token in file: {file_err}"
                    )
                    return False

        except Exception as e:
            logger.error(
                f"{self.somnia.account_index} | Error replacing Twitter token: {e}"
            )
            return False
