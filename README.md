StarLabs-Somnia Bot 🚀
A powerful and flexible automation tool for Somnia Network with multiple features for testnet activities.

TUTORIAL >>> star-labs.gitbook.io/star-labs/software/somnia/ru <<< TUTORIAL >>> star-labs.gitbook.io/star-labs/software/somnia/ru <<< TUTORIAL >>> star-labs.gitbook.io/star-labs/software/somnia/ru <<<

🌟 Features
✨ Multi-threaded processing
🔄 Automatic retries with configurable attempts
🔐 Proxy support
📊 Account range selection
🎲 Random pauses between operations
🔔 Telegram logging integration
📝 Detailed transaction tracking
🧩 Modular task system
🤖 Social media integration (Twitter, Discord)
⚠️ Discord inviter

🎯 Available Actions:
Network Operations:
- Somnia Network Faucet
- Send Tokens
- Set Username
- Network Info
- Connect Socials (Twitter, Discord)
- Complete Campaigns

Minting & NFTs:
- Mint Ping Pong Tokens
- Mint SHANNON NFT (Nerzo)
- Mint NEE NFT (Nerzo)
- Mint YAPPERS NFT (Alze)
- Mint SOMNI NFT (Mintaura)
- Deploy Contracts (Mintair)

Trading & Swaps:
- Ping Pong Token Swaps
- Quills Chat Messages (Blockchain messaging)

📋 Requirements
- Python 3.11.1 - 3.11.6
- Private keys for Somnia Network wallets
- Proxies for enhanced security
- Twitter tokens for social media integration
- Discord tokens for social media integration


🚀 Installation
1. Clone the repository:
```bash
git clone https://github.com/0xStarLabs/StarLabs-Somnia.git
cd StarLabs-Somnia
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your settings in config.yaml
4. Add your private keys to data/private_keys.txt
5. Add proxies to data/proxies.txt
6. Add Twitter tokens to data/twitter_tokens.txt
7. Add Discord tokens to data/discord_tokens.txt
8. Add Quills messages to data/random_message_quills.txt

📁 Project Structure
StarLabs-Somnia/
├── data/
│   ├── private_keys.txt         # Wallet private keys
│   ├── proxies.txt              # Proxy addresses
│   ├── twitter_tokens.txt       # Twitter authentication tokens
│   ├── discord_tokens.txt       # Discord authentication tokens
│   └── random_message_quills.txt # Messages for Quills blockchain
├── src/
│   ├── modules/                 # Task-specific modules
│   └── utils/                   # Helper utilities
├── config.yaml                  # Main configuration file
└── tasks.py                     # Task definitions

📝 Configuration
1. data files
- private_keys.txt: One private key per line
- proxies.txt: One proxy per line (format: http://user:pass@ip:port)
- twitter_tokens.txt: One Twitter token per line
- discord_tokens.txt: One Discord token per line
- random_message_quills.txt: One message per line for Quills blockchain

2. config.yaml Settings
```yaml
SETTINGS:
  THREADS: 1                      # Number of parallel threads
  ATTEMPTS: 5                     # Retry attempts for failed actions
  ACCOUNTS_RANGE: [0, 0]          # Wallet range to use (default: all)
  EXACT_ACCOUNTS_TO_USE: []       # Specific wallets to use (default: all)
  SHUFFLE_WALLETS: true           # Randomize wallet processing order
  PAUSE_BETWEEN_ATTEMPTS: [3, 10] # Random pause between retries
  PAUSE_BETWEEN_SWAPS: [3, 10]    # Random pause between swap operations
```

3. Module Configurations
```yaml
SOMNIA_NETWORK:
  SOMNIA_SWAPS:
    BALANCE_PERCENT_TO_SWAP: [5, 10]
    NUMBER_OF_SWAPS: [1, 2]

  SOMNIA_TOKEN_SENDER:
    BALANCE_PERCENT_TO_SEND: [1.5, 3]
    NUMBER_OF_SENDS: [1, 1]
    SEND_ALL_TO_DEVS_CHANCE: 50

  SOMNIA_CAMPAIGNS:
    REPLACE_FAILED_TWITTER_ACCOUNT: false
```

🎮 Usage
Task Configuration
Edit tasks.py to select which modules to run:
```python
TASKS = ["CAMPAIGNS"]  # Replace with your desired tasks
```

Available task presets:
- CAMPAIGNS - Complete Somnia Network campaigns
- FAUCET - Claim Somnia Network tokens
- SEND_TOKENS - Send tokens to random wallets
- CONNECT_SOCIALS - Connect social media accounts (Twitter, Discord)
- MINT_PING_PONG - Mint Ping Pong tokens
- SWAPS_PING_PONG - Swap Ping Pong tokens
- QUILLS_CHAT - Send messages in Quills blockchain
- SOMNIA_NETWORK_SET_USERNAME - Set username on Somnia Network
- SOMNIA_NETWORK_INFO - Show account information

Custom Task Sequences
You can create custom task sequences combining different modules:
```python
TASKS = ["MY_CUSTOM_TASK"]

MY_CUSTOM_TASK = [
    "faucet",                           # Run faucet first
    ("mint_ping_pong", "swaps_ping_pong"), # Then run both in random order
    ["nerzo_shannon", "nerzo_nee"],     # Then run only one randomly
    "quills_chat",                      # Send message in Quills
    "connect_socials"                   # Connect social media accounts
]
```

Run the bot:
```bash
python main.py
```

📜 License
MIT License

⚠️ Disclaimer
This tool is for educational purposes only. Use at your own risk and in accordance with relevant terms of service.
