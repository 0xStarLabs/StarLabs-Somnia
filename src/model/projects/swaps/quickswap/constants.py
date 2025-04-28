# Token addresses
USDC_ADDRESS = "0xE9CC37904875B459Fa5D0FE37680d36F1ED55e38"  # decimals: 6
WETH_ADDRESS = "0xd2480162Aa7F02Ead7BF4C127465446150D58452"  # decimals: 18
WSTT_ADDRESS = "0x4A3BC48C156384f9564Fd65A53a2f3D534D8f2b7"  # decimals: 18

# Router address
ROUTER_ADDRESS = "0xE94de02e52Eaf9F0f6Bf7f16E4927FcBc2c09bC7"

# Token information
TOKEN_INFO = {
    USDC_ADDRESS: {"symbol": "USDC", "decimals": 6},
    WETH_ADDRESS: {"symbol": "WETH", "decimals": 18},
    WSTT_ADDRESS: {"symbol": "WSTT", "decimals": 18},
}

# Fee tiers to try
FEE_TIERS = [500, 3000, 10000]  # 0.05%, 0.3%, 1%

# Default fee
DEFAULT_FEE = 3000  # 0.3%
