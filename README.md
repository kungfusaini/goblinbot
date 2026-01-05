# 👹 Goblin Financial Bot

A Telegram bot for managing financial transactions and income. Goblin focuses solely on the financial aspects of the bucket system - adding transactions and income entries.

## Features

- 💸 **Add Transactions**: Record expenses with categories, payment methods, and notes
- 💰 **Add Income**: Track income sources and amounts  
- 📊 **View Recent**: See latest transactions and income entries
- 📋 **Categories**: Browse available spending categories and subcategories
- ❓ **Help**: Built-in help and guidance

## How It Works

Goblin integrates with the Vulkan API to manage financial data:

- **Transactions**: Stored via `POST /vault/spend`
- **Income**: Stored via `POST /vault/income`
- **Categories**: Fetched from `GET /vault/categories`
- **Recent Data**: Retrieved from `GET /vault/data` and `GET /vault/income`

## Setup

### Prerequisites

- Python 3.13+
- Telegram Bot Token
- Vulkan API Key

### Environment Variables

```bash
GOBLINBOT_TOKEN=your_telegram_bot_token
WELL_API_KEY=your_vulkan_api_key
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python goblin.py
```

### Docker Deployment

```bash
# Build image
docker build -f Dockerfile.prod -t goblin-bot .

# Run container
docker run -d \
  --name goblin-bot \
  -e GOBLINBOT_TOKEN=your_telegram_bot_token \
  -e WELL_API_KEY=your_vulkan_api_key \
  goblin-bot
```

## Usage

### Commands

- `/start` - Show main menu
- `/help` - Display help information
- `/cancel` - Cancel current operation

### Menu Navigation

1. **💸 Add Transaction**:
   - Enter transaction name
   - Enter amount (e.g., 25.50)
   - Select category from available options
   - Select subcategory (if applicable)
   - Choose payment method (Credit/Debit)
   - Add optional notes
   - Confirm and submit

2. **💰 Add Income**:
   - Enter income source name
   - Enter amount
   - Confirm and submit

3. **📊 View Recent**:
   - Shows last 5 transactions
   - Shows last 3 income entries

4. **📋 Categories**:
   - Browse all available spending categories
   - View subcategories for each category

## Validation Rules

- **Name**: 1-100 characters required
- **Amount**: Positive numbers, max 999,999.99, 2 decimal places
- **Payment Method**: Only "Credit" or "Debit"
- **Date**: Auto-populated with today's date (YYYY-MM-DD format)
- **Categories**: Must exist in the system

## Error Handling

The bot provides clear error messages for:

- Invalid amounts (negative, too large, wrong format)
- Missing required fields
- Network/API errors
- Invalid categories

## Integration

Goblin is designed to work alongside other services in the bucket ecosystem:

- **Bucketbot**: Handles tasks, notes, and bookmarks
- **Goblin**: Handles financial transactions and income
- **Vulkan**: Provides the API backend for all operations

**Authentication**: Both bucketbot and goblin use the same `WELL_API_KEY` to authenticate with the Vulkan API endpoints (`/well/*` and `/vault/*`). Goblin uses its own `GOBLINBOT_TOKEN` for Telegram bot authentication.

## Architecture

```
goblin/
├── goblin.py           # Main bot implementation
├── requirements.txt    # Python dependencies
├── Dockerfile.prod    # Production Docker image
├── README.md          # This file
└── .gitignore         # Git ignore patterns
```

The bot uses:
- `python-telegram-bot` for Telegram integration
- `requests` for API communication
- Conversation handlers for user flow management
- Inline keyboards for category selection

## Security

- API key authentication via `X-API-Key` header
- Input validation on all user data
- No sensitive data stored in logs
- Environment-based configuration

## Deployment Notes

- Uses multi-stage Docker build for minimal production image
- Runs on Python 3.13 Alpine for efficiency
- Shared infrastructure with other bucket services
- Health checks and monitoring integration ready

## Support

For issues or questions:
1. Check the `/help` command in the bot
2. Verify environment variables are set correctly
3. Ensure Vulkan API is accessible with provided key
4. Check network connectivity to vulkan.sumeetsaini.com