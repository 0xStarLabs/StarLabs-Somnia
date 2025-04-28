TASKS = ["CAMPAIGNS"]

# FOR EXAMPLE ONLY, USE YOUR OWN TASKS PRESET
FULL_TASK = [
    "faucet",
    "connect_socials",
    "somnia_network_set_username",
    "send_tokens",
    "mint_ping_pong",
    "swaps_ping_pong",
    "quills_chat",
    "campaigns",
    "nerzo_shannon",
    "nerzo_nee",
    "alze_yappers",
    "mintair_deploy",
    "mintaura_somni",
    "somnia_network_info",
]

FAUCET = ["faucet"]
CAMPAIGNS = ["campaigns"]
SEND_TOKENS = ["send_tokens"]
CONNECT_SOCIALS = ["connect_socials"]
MINT_PING_PONG = ["mint_ping_pong"]
SWAPS_PING_PONG = ["swaps_ping_pong"]
QUILLS_CHAT = ["quills_chat"]
SOMNIA_NETWORK_SET_USERNAME = ["somnia_network_set_username"]
SOMNIA_NETWORK_INFO = ["somnia_network_info"]

NERZO_SHANNON = ["nerzo_shannon"]
NERZO_NEE = ["nerzo_nee"]
ALZE_YAPPERS = ["alze_yappers"]
MINTAIR_DEPLOY = ["mintair_deploy"]
MINTAURA_SOMNI = ["mintaura_somni"]

"""
EN:
You can create your own task with the modules you need 
and add it to the TASKS list or use our ready-made preset tasks.

( ) - Means that all of the modules inside the brackets will be executed 
in random order
[ ] - Means that only one of the modules inside the brackets will be executed 
on random
SEE THE EXAMPLE BELOW:

RU:
Вы можете создать свою задачу с модулями, которые вам нужны, 
и добавить ее в список TASKS, см. пример ниже:

( ) - означает, что все модули внутри скобок будут выполнены в случайном порядке
[ ] - означает, что будет выполнен только один из модулей внутри скобок в случайном порядке
СМОТРИТЕ ПРИМЕР НИЖЕ:

CHINESE:
你可以创建自己的任务，使用你需要的模块，
并将其添加到TASKS列表中，请参见下面的示例：

( ) - 表示括号内的所有模块将按随机顺序执行
[ ] - 表示括号内的模块将按随机顺序执行

--------------------------------
!!! IMPORTANT !!!
EXAMPLE | ПРИМЕР | 示例:

TASKS = [
    "CREATE_YOUR_OWN_TASK",
]
CREATE_YOUR_OWN_TASK = [
    "faucet",
    ("faucet_tokens", "swaps"),
    ["storagescan_deploy", "conft_mint"],
    "swaps",
]
--------------------------------


BELOW ARE THE READY-MADE TASKS THAT YOU CAN USE:
СНИЗУ ПРИВЕДЕНЫ ГОТОВЫЕ ПРИМЕРЫ ЗАДАЧ, КОТОРЫЕ ВЫ МОЖЕТЕ ИСПОЛЬЗОВАТЬ:
以下是您可以使用的现成任务：


--- ALL TASKS ---

faucet - Request Faucet on Somnia Network - https://testnet.somnia.network/
send_tokens - Send tokens to random wallets - https://testnet.somnia.network/
connect_socials - Connect socials to your account - https://quest.somnia.network/
somnia_network_set_username - Set username on Somnia Network - https://quest.somnia.network/
campaigns - Complete campaigns on Somnia Network - https://quest.somnia.network/
somnia_network_info - Show account info on Somnia Network (points, referrals, quests, etc.) - https://quest.somnia.network

MINTS
nerzo_shannon - Mint SHANNON NFT https://www.nerzo.xyz/shannon
nerzo_nee - Mint NEE NFT https://www.nerzo.xyz/nee
alze_yappers - Mint YAPPERS NFT https://alze.xyz/nftCheckout/Yappers
mintaura_somni - Mint SOMNI NFT https://www.mintaura.io/somni
quills_chat - Send message in Quills https://quills.fun/
mint_ping_pong - Mint Ping Pong tokens - https://testnet.somnia.network/swap

DEPLOYS
mintair_deploy - Deploy contract on Mintair https://contracts.mintair.xyz/

# SWAPS
swaps_ping_pong - Swaps Ping Pong tokens - https://testnet.somnia.network/swap

"""
