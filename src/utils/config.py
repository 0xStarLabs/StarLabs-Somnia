from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
import yaml
from pathlib import Path
import asyncio


@dataclass
class SettingsConfig:
    THREADS: int
    ATTEMPTS: int
    ACCOUNTS_RANGE: Tuple[int, int]
    EXACT_ACCOUNTS_TO_USE: List[int]
    PAUSE_BETWEEN_ATTEMPTS: Tuple[int, int]
    PAUSE_BETWEEN_SWAPS: Tuple[int, int]
    RANDOM_PAUSE_BETWEEN_ACCOUNTS: Tuple[int, int]
    RANDOM_PAUSE_BETWEEN_ACTIONS: Tuple[int, int]
    RANDOM_INITIALIZATION_PAUSE: Tuple[int, int]
    TELEGRAM_USERS_IDS: List[int]
    TELEGRAM_BOT_TOKEN: str
    SEND_TELEGRAM_LOGS: bool
    SHUFFLE_WALLETS: bool


@dataclass
class FlowConfig:
    TASKS: List
    SKIP_FAILED_TASKS: bool


@dataclass
class SomniaSwapsConfig:
    BALANCE_PERCENT_TO_SWAP: Tuple[int, int]
    NUMBER_OF_SWAPS: Tuple[int, int]
    SWAP_ALL_TO_STT: bool

@dataclass
class SomniaTokenSenderConfig:
    BALANCE_PERCENT_TO_SEND: Tuple[float, float]
    NUMBER_OF_SENDS: Tuple[int, int]
    SEND_ALL_TO_DEVS_CHANCE: int


@dataclass
class SomniaCampaignsConfig:
    REPLACE_FAILED_TWITTER_ACCOUNT: bool


@dataclass
class SomniaNetworkConfig:
    SOMNIA_SWAPS: SomniaSwapsConfig
    SOMNIA_TOKEN_SENDER: SomniaTokenSenderConfig
    SOMNIA_CAMPAIGNS: SomniaCampaignsConfig


@dataclass
class RpcsConfig:
    SOMNIA: List[str]


@dataclass
class OthersConfig:
    SKIP_SSL_VERIFICATION: bool
    USE_PROXY_FOR_RPC: bool


@dataclass
class WalletInfo:
    account_index: int
    private_key: str
    address: str
    balance: float
    transactions: int


@dataclass
class WalletsConfig:
    wallets: List[WalletInfo] = field(default_factory=list)


@dataclass
class QuillsConfig:
    QUILLS_MESSAGES: List[str] = field(
        default_factory=lambda: [
            "Hello",
        ]
    )


@dataclass
class Config:
    SETTINGS: SettingsConfig
    FLOW: FlowConfig
    SOMNIA_NETWORK: SomniaNetworkConfig
    RPCS: RpcsConfig
    OTHERS: OthersConfig
    WALLETS: WalletsConfig = field(default_factory=WalletsConfig)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    QUILLS: QuillsConfig = field(default_factory=QuillsConfig)
    spare_twitter_tokens: List[str] = field(default_factory=list)
    
    @classmethod
    def load(cls, path: str = "config.yaml") -> "Config":
        """Load configuration from yaml file"""
        with open(path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        # Load tasks from tasks.py
        try:
            import tasks

            if hasattr(tasks, "TASKS"):
                tasks_list = tasks.TASKS

            else:
                error_msg = "No TASKS list found in tasks.py"
                print(f"Error: {error_msg}")
                raise ValueError(error_msg)
        except ImportError as e:
            error_msg = f"Could not import tasks.py: {e}"
            print(f"Error: {error_msg}")
            raise ImportError(error_msg) from e

        return cls(
            SETTINGS=SettingsConfig(
                THREADS=data["SETTINGS"]["THREADS"],
                ATTEMPTS=data["SETTINGS"]["ATTEMPTS"],
                ACCOUNTS_RANGE=tuple(data["SETTINGS"]["ACCOUNTS_RANGE"]),
                EXACT_ACCOUNTS_TO_USE=data["SETTINGS"]["EXACT_ACCOUNTS_TO_USE"],
                PAUSE_BETWEEN_ATTEMPTS=tuple(
                    data["SETTINGS"]["PAUSE_BETWEEN_ATTEMPTS"]
                ),
                PAUSE_BETWEEN_SWAPS=tuple(data["SETTINGS"]["PAUSE_BETWEEN_SWAPS"]),
                RANDOM_PAUSE_BETWEEN_ACCOUNTS=tuple(
                    data["SETTINGS"]["RANDOM_PAUSE_BETWEEN_ACCOUNTS"]
                ),
                RANDOM_PAUSE_BETWEEN_ACTIONS=tuple(
                    data["SETTINGS"]["RANDOM_PAUSE_BETWEEN_ACTIONS"]
                ),
                RANDOM_INITIALIZATION_PAUSE=tuple(
                    data["SETTINGS"]["RANDOM_INITIALIZATION_PAUSE"]
                ),
                TELEGRAM_USERS_IDS=data["SETTINGS"]["TELEGRAM_USERS_IDS"],
                TELEGRAM_BOT_TOKEN=data["SETTINGS"]["TELEGRAM_BOT_TOKEN"],
                SEND_TELEGRAM_LOGS=data["SETTINGS"]["SEND_TELEGRAM_LOGS"],
                SHUFFLE_WALLETS=data["SETTINGS"].get("SHUFFLE_WALLETS", True),
            ),
            FLOW=FlowConfig(
                TASKS=tasks_list,
                SKIP_FAILED_TASKS=data["FLOW"]["SKIP_FAILED_TASKS"],
            ),
            SOMNIA_NETWORK=SomniaNetworkConfig(
                SOMNIA_SWAPS=SomniaSwapsConfig(
                    BALANCE_PERCENT_TO_SWAP=tuple(
                        data["SOMNIA_NETWORK"]["SOMNIA_SWAPS"][
                            "BALANCE_PERCENT_TO_SWAP"
                        ]
                    ),
                    NUMBER_OF_SWAPS=tuple(
                        data["SOMNIA_NETWORK"]["SOMNIA_SWAPS"]["NUMBER_OF_SWAPS"]
                    ),
                    SWAP_ALL_TO_STT=data["SOMNIA_NETWORK"]["SOMNIA_SWAPS"]["SWAP_ALL_TO_STT"],
                ),
                SOMNIA_TOKEN_SENDER=SomniaTokenSenderConfig(
                    BALANCE_PERCENT_TO_SEND=tuple(
                        data["SOMNIA_NETWORK"]["SOMNIA_TOKEN_SENDER"][
                            "BALANCE_PERCENT_TO_SEND"
                        ]
                    ),
                    NUMBER_OF_SENDS=tuple(
                        data["SOMNIA_NETWORK"]["SOMNIA_TOKEN_SENDER"]["NUMBER_OF_SENDS"]
                    ),
                    SEND_ALL_TO_DEVS_CHANCE=data["SOMNIA_NETWORK"][
                        "SOMNIA_TOKEN_SENDER"
                    ]["SEND_ALL_TO_DEVS_CHANCE"],
                ),
                SOMNIA_CAMPAIGNS=SomniaCampaignsConfig(
                    REPLACE_FAILED_TWITTER_ACCOUNT=data["SOMNIA_NETWORK"][
                        "SOMNIA_CAMPAIGNS"
                    ]["REPLACE_FAILED_TWITTER_ACCOUNT"],
                ),
            ),
            RPCS=RpcsConfig(
                SOMNIA=data["RPCS"]["SOMNIA"],
            ),
            OTHERS=OthersConfig(
                SKIP_SSL_VERIFICATION=data["OTHERS"]["SKIP_SSL_VERIFICATION"],
                USE_PROXY_FOR_RPC=data["OTHERS"]["USE_PROXY_FOR_RPC"],
            ),
        )


# Singleton pattern
def get_config() -> Config:
    """Get configuration singleton"""
    if not hasattr(get_config, "_config"):
        get_config._config = Config.load()
    return get_config._config
