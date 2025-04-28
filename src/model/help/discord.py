import asyncio
import base64
from dataclasses import dataclass
import json
import random
import time
from loguru import logger
from curl_cffi.requests import AsyncSession, Response
from src.utils.config import Config


class DiscordInviter:
    def __init__(self, account_index: int, discord_token: str, proxy: str, config: Config):
        self.account_index = account_index
        self.discord_token = discord_token
        self.proxy = proxy
        self.config = config
        self.session: AsyncSession | None = None

    async def invite(self, invite_code: str) -> dict:
        self.session = await create_client(self.proxy)

        for retry in range(self.config.SETTINGS.ATTEMPTS):
            try:
                if not await init_cf(self.account_index, self.session):
                    raise Exception("Failed to initialize cf")

                guild_id, channel_id, success = await get_guild_ids(
                    self.session, invite_code, self.account_index, self.discord_token
                )
                if not success:
                    continue

                result = await self.send_invite_request(
                    invite_code, guild_id, channel_id
                )
                if result is None:
                    return False
                elif result:
                    return True
                else:
                    continue
                
            except Exception as e:
                random_sleep = random.randint(
                    self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                    self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
                )
                logger.error(
                    f"{self.account_index} | Error: {e}. Retrying in {random_sleep} seconds..."
                )
                await asyncio.sleep(random_sleep)
        return False

    async def send_invite_request(
        self, invite_code: str, guild_id: str, channel_id: str
    ) -> bool:
        for retry in range(self.config.SETTINGS.ATTEMPTS):
            try:
                headers = {
                    "accept": "*/*",
                    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,zh-TW;q=0.6,zh;q=0.5",
                    "authorization": f"{self.discord_token}",
                    "content-type": "application/json",
                    "origin": "https://discord.com",
                    "priority": "u=1, i",
                    "referer": f"https://discord.com/invite/{invite_code}",
                    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="131", "Chromium";v="131"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "x-context-properties": create_x_context_properties(
                        guild_id, channel_id
                    ),
                    "x-debug-options": "bugReporterEnabled",
                    "x-discord-locale": "en-US",
                    "x-discord-timezone": "Etc/GMT-2",
                    "x-super-properties": create_x_super_properties(),
                }

                json_data = {
                    "session_id": None,
                }

                response = await self.session.post(
                    f"https://discord.com/api/v9/invites/{invite_code}",
                    headers=headers,
                    json=json_data,
                )

                if (
                    "You need to update your app to join this server." in response.text
                    or "captcha_rqdata" in response.text
                ):
                    logger.error(f"{self.account_index} | Captcha detected. Can't solve it.")
                    return None

                elif response.status_code == 200 and response.json()["type"] == 0:
                    logger.success(f"{self.account_index} | Account joined the server!")
                    return True

                elif "Unauthorized" in response.text:
                    logger.error(
                        f"{self.account_index} | Incorrect discord token or your account is blocked."
                    )
                    return False

                elif "You need to verify your account in order to" in response.text:
                    logger.error(
                        f"{self.account_index} | Account needs verification (Email code etc)."
                    )
                    return False

                else:
                    logger.error(
                        f"{self.account_index} | Unknown error: {response.text}"
                    )

            except Exception as e:
                random_sleep = random.randint(
                    self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                    self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
                )
                logger.error(
                    f"{self.account_index} | Send invite error: {e}. Retrying in {random_sleep} seconds..."
                )
                await asyncio.sleep(random_sleep)

        return False


def calculate_nonce() -> str:
    unix_ts = time.time()
    return str((int(unix_ts) * 1000 - 1420070400000) * 4194304)


def create_x_super_properties() -> str:
    return base64.b64encode(json.dumps({
   "os":"Windows",
   "browser":"Chrome",
   "device":"",
   "system_locale":"ru",
   "browser_user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
   "browser_version":"133.0.0.0",
   "os_version":"10",
   "referrer":"https://discord.com/",
   "referring_domain":"discord.com",
   "referrer_current":"",
   "referring_domain_current":"",
   "release_channel":"stable",
   "client_build_number":370533,
   "client_event_source":None,
   "has_client_mods":False
}, separators=(',', ':')).encode('utf-8')).decode('utf-8')


async def get_guild_ids(client: AsyncSession, invite_code: str, account_index: int, discord_token: str) -> tuple[str, str, bool]:
    try:
        headers = {
            'sec-ch-ua-platform': '"Windows"',
            'Authorization': f'{discord_token}',
            'Referer': f'https://discord.com/invite/{invite_code}',
            'X-Debug-Options': 'bugReporterEnabled',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="131", "Chromium";v="131"',
            'sec-ch-ua-mobile': '?0',
            'X-Discord-Timezone': 'Etc/GMT-2',
            'X-Super-Properties': create_x_super_properties(),
            'X-Discord-Locale': 'en-US',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        }

        params = {
            'with_counts': 'true',
            'with_expiration': 'true',
            'with_permissions': 'false',
        }

        response = await client.get(f'https://discord.com/api/v9/invites/{invite_code}', params=params, headers=headers)
        
        if "You need to verify your account" in response.text:
            logger.error(f"{account_index} | Account needs verification (Email code etc).")
            return "verification_failed", "", False

        location_guild_id = response.json()['guild_id']
        location_channel_id = response.json()['channel']['id']

        return location_guild_id, location_channel_id, True

    except Exception as err:
        logger.error(f"{account_index} | Failed to get guild ids: {err}")
        return None, None, False
    

def create_x_context_properties(location_guild_id: str, location_channel_id: str) -> str:
    return base64.b64encode(json.dumps({
        "location": "Accept Invite Page",
        "location_guild_id": location_guild_id,
        "location_channel_id": location_channel_id,
        "location_channel_type": 0
    }, separators=(',', ':')).encode('utf-8')).decode('utf-8')


async def init_cf(account_index: int, client: AsyncSession) -> bool:
    try:
        resp = await client.get("https://discord.com/login",
                          headers={
                              'authority': 'discord.com',
                              'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                              'accept-language': 'en-US,en;q=0.9',
                              'sec-ch-ua': '"Chromium";v="131", "Not A(Brand";v="24", "Google Chrome";v="131"',
                              'sec-ch-ua-mobile': '?0',
                              'sec-ch-ua-platform': '"Windows"',
                              'sec-fetch-dest': 'document',
                              'sec-fetch-mode': 'navigate',
                              'sec-fetch-site': 'none',
                              'sec-fetch-user': '?1',
                              'upgrade-insecure-requests': '1',
                          }
                          )

        if await set_response_cookies(client, resp):
            logger.success(f"{account_index} | Initialized new cookies.")
            return True
        else:
            logger.error(f"{account_index} | Failed to initialize new cookies.")
            return False

    except Exception as err:
        logger.error(f"{account_index} | Failed to initialize new cookies: {err}")
        return False


async def set_response_cookies(client: AsyncSession, response: Response) -> bool:
    try:
        cookies = response.headers.get_list("set-cookie")
        for cookie in cookies:
            try:
                key, value = cookie.split(';')[0].strip().split("=")
                client.cookies.set(name=key, value=value, domain="discord.com", path="/")

            except:
                pass

        return True

    except Exception as err:
        logger.error(f"Failed to set response cookies: {err}")
        return False

async def create_client(proxy: str) -> AsyncSession:
    session = AsyncSession(
                impersonate="chrome131",
                verify=False,
                timeout=60,
            )
    if proxy:
        session.proxies.update({
            "http": "http://" + proxy,
            "https": "http://" + proxy,
        })

    session.headers.update(HEADERS)

    return session

HEADERS = {
    'accept': '*/*',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,zh-TW;q=0.6,zh;q=0.5',
    'content-type': 'application/json',
    'priority': 'u=1, i',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}
