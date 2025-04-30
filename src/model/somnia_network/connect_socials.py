import random
import asyncio
import secrets
from loguru import logger

from src.model.somnia_network.constants import SomniaProtocol
from src.utils.decorators import retry_async


class ConnectSocials:
    def __init__(self, somnia_instance: SomniaProtocol):
        self.somnia = somnia_instance

    async def connect_socials(self):
        try:
            success = True
            logger.info(f"{self.somnia.account_index} | Starting connect socials...")

            account_info = await self.somnia.get_account_info()

            if account_info is None:
                raise Exception("Account info is None")

            if account_info["twitterName"] is None:
                if not self.somnia.twitter_token:
                    logger.error(
                        f"{self.somnia.account_index} | Twitter token is None. Please add token to data/twitter_tokens.txt"
                    )
                else:
                    if not await self.connect_twitter():
                        success = False
            else:
                logger.success(
                    f"{self.somnia.account_index} | Twitter already connected"
                )

            if account_info["discordName"] is None:
                if not self.somnia.discord_token:
                    logger.error(
                        f"{self.somnia.account_index} | Discord token is None. Please add token to data/discord_tokens.txt"
                    )
                else:
                    if not await self.connect_discord():
                        success = False
            else:
                logger.success(
                    f"{self.somnia.account_index} | Discord already connected"
                )

            if success:
                logger.success(
                    f"{self.somnia.account_index} | Successfully connected socials"
                )
            else:
                logger.error(f"{self.somnia.account_index} | Failed to connect socials")

            return success

        except Exception as e:
            random_pause = random.randint(
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.somnia.account_index} | Connect socials error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            return False

    @retry_async(default_value=False)
    async def connect_twitter(self):
        try:
            logger.info(f"{self.somnia.account_index} | Starting connect twitter...")

            generated_csrf_token = secrets.token_hex(16)

            cookies = {"ct0": generated_csrf_token, "auth_token": self.somnia.twitter_token}
            cookies_headers = "; ".join(f"{k}={v}" for k, v in cookies.items())

            headers = {
                "cookie": cookies_headers,
                "x-csrf-token": generated_csrf_token,
                'upgrade-insecure-requests': '1',
                "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
                'referer': 'https://quest.somnia.network/',
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            }

            client_id = "WS1FeDNoZnlqTEw1WFpvX1laWkc6MTpjaQ"
            code_challenge = "challenge123"
            state = "eyJ0eXBlIjoiQ09OTkVDVF9UV0lUVEVSIn0="
            params = {
                'client_id': client_id,
                'code_challenge': code_challenge,
                'code_challenge_method': 'plain',
                'redirect_uri': 'https://quest.somnia.network/twitter',
                'response_type': 'code',
                'scope': 'users.read follows.write tweet.write like.write tweet.read',
                'state': state,
            }

            response = await self.somnia.session.get('https://x.com/i/api/2/oauth2/authorize', params=params, headers=headers)

            if not response.json().get("auth_code"):
                raise Exception(f"Failed to connect twitter: no auth_code in response: {response.status_code} | {response.text}")
            
            auth_code = response.json().get("auth_code")

            data = {
                'approval': 'true',
                'code': auth_code,
            }

            response = await self.somnia.session.post('https://x.com/i/api/2/oauth2/authorize', headers=headers, data=data)
        
            redirect_url = response.json()['redirect_uri']

            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'referer': 'https://twitter.com/',
                'priority': 'u=0, i',
            }

            response = await self.somnia.session.get(redirect_url, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"Failed to connect twitter send auth_code: status code is {response.status_code} | {response.text}")

            headers = {
                'authorization': f'Bearer {self.somnia.somnia_login_token}',
                'content-type': 'application/json',
                'origin': 'https://quest.somnia.network',
                'referer': f'https://quest.somnia.network/twitter?state={state}&code={auth_code}',
            }

            json_data = {
                'code': auth_code,
                'codeChallenge': code_challenge,
                'provider': 'twitter',
            }

            response = await self.somnia.session.post('https://quest.somnia.network/api/auth/socials', headers=headers, json=json_data)

            if not response.json().get("success"):
                raise Exception(f"Failed to confirm twitter connection: {response.status_code} | {response.text}")
            
            if response.json()["success"]:
                logger.success(f"{self.somnia.account_index} | Successfully connected twitter")
                return True
            else:
                raise Exception(f"Failed to confirm twitter connection: {response.status_code} | {response.text}")

        except Exception as e:
            if "Could not authenticate you" in str(e):
                logger.error(f"{self.somnia.account_index} | Twitter token is invalid")
                return False
            
            random_pause = random.randint(
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.somnia.account_index} | Connect twitter error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=False)
    async def connect_discord(self):
        try:
            logger.info(f"{self.somnia.account_index} | Starting connect discord...")

            headers = {
                "Referer": "https://quest.somnia.network/",
                "Upgrade-Insecure-Requests": "1",
            }

            response = await self.somnia.session.get(
                "https://discord.com/oauth2/authorize?response_type=code&client_id=1318915934878040064&redirect_uri=https%3A%2F%2Fquest.somnia.network%2Fdiscord&scope=identify&state=eyJ0eXBlIjoiQ09OTkVDVF9ESVNDT1JEIn0=",
                headers=headers,
            )

            headers = {
                'authorization': self.somnia.discord_token,
                'referer': 'https://discord.com/oauth2/authorize?response_type=code&client_id=1318915934878040064&redirect_uri=https%3A%2F%2Fquest.somnia.network%2Fdiscord&scope=identify&state=eyJ0eXBlIjoiQ09OTkVDVF9ESVNDT1JEIn0=',
                'x-debug-options': 'bugReporterEnabled',
                'x-discord-locale': 'en-US',
              }

            params = {
                'client_id': '1318915934878040064',
                'response_type': 'code',
                'redirect_uri': 'https://quest.somnia.network/discord',
                'scope': 'identify',
                'state': 'eyJ0eXBlIjoiQ09OTkVDVF9ESVNDT1JEIn0=',
                'integration_type': '0',
            }

            response = await self.somnia.session.get('https://discord.com/api/v9/oauth2/authorize', params=params, headers=headers)
                        
            headers = {
                'authorization': self.somnia.discord_token,
                'content-type': 'application/json',
                'origin': 'https://discord.com',
                'referer': 'https://discord.com/oauth2/authorize?response_type=code&client_id=1318915934878040064&redirect_uri=https%3A%2F%2Fquest.somnia.network%2Fdiscord&scope=identify&state=eyJ0eXBlIjoiQ09OTkVDVF9ESVNDT1JEIn0=',
                'x-debug-options': 'bugReporterEnabled',
                'x-discord-locale': 'en-US',
                }

            params = {
                'client_id': '1318915934878040064',
                'response_type': 'code',
                'redirect_uri': 'https://quest.somnia.network/discord',
                'scope': 'identify',
                'state': 'eyJ0eXBlIjoiQ09OTkVDVF9ESVNDT1JEIn0=',
            }

            json_data = {
                'permissions': '0',
                'authorize': True,
                'integration_type': 0,
                'location_context': {
                    'guild_id': '10000',
                    'channel_id': '10000',
                    'channel_type': 10000,
                },
                'dm_settings': {
                    'allow_mobile_push': False,
                },
            }

            response = await self.somnia.session.post(
                'https://discord.com/api/v9/oauth2/authorize',
                params=params,
                headers=headers,
                json=json_data,
            )

            if not response.json()['location']:
                raise Exception("Failed to connect discord: no location in response")
            
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'referer': 'https://discord.com/',
                'upgrade-insecure-requests': '1',
                }

            
            code = response.json()['location'].split('code=')[1].split('&')[0]

            response = await self.somnia.session.get(response.json()['location'], headers=headers)

            if response.status_code != 200:
                raise Exception(f"Failed to connect discord: status code is {response.status_code} | {response.text}")


            headers = {
                'accept': '*/*',
                'accept-language': 'ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4',
                'authorization': f'Bearer {self.somnia.somnia_login_token}',
                'content-type': 'application/json',
                'origin': 'https://quest.somnia.network',
                'priority': 'u=1, i',
                'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            }

            json_data = {
                'code': code,
                'provider': 'discord',
            }

            response = await self.somnia.session.post('https://quest.somnia.network/api/auth/socials', headers=headers, json=json_data)

            if not response.json().get("success"):
                raise Exception(f"Failed to confirm discord connection: {response.status_code} | {response.text}")
            
            if response.json()["success"]:
                logger.success(f"{self.somnia.account_index} | Successfully connected discord")
                return True
            else:
                raise Exception(f"Failed to confirm discord connection: {response.status_code} | {response.text}")
            
        except Exception as e:
            random_pause = random.randint(
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.somnia.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.somnia.account_index} | Connect discord error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise
