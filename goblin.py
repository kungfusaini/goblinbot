#!/usr/bin/env python3

import os
import sys
import requests
import csv
import io
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# States for conversation
MAIN_MENU = 0
TRANSACTION_NAME = 1
TRANSACTION_AMOUNT = 2
TRANSACTION_CATEGORY = 3
TRANSACTION_SUBCATEGORY = 4
TRANSACTION_PAYMENT = 5
TRANSACTION_NOTES = 6
TRANSACTION_CONFIRM = 7
INCOME_NAME = 8
INCOME_AMOUNT = 9
INCOME_CONFIRM = 10

# Main menu keyboard
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [["💸 Add Transaction"], ["💰 Add Income"], ["📊 View Recent"], ["📋 Categories"], ["❓ Help"]],
    resize_keyboard=True,
    one_time_keyboard=False
)

# Payment method keyboard
PAYMENT_KEYBOARD = ReplyKeyboardMarkup(
    [["Credit"], ["Debit"]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Confirmation keyboard
CONFIRM_KEYBOARD = ReplyKeyboardMarkup(
    [["✅ Confirm"], ["❌ Cancel"]],
    resize_keyboard=True,
    one_time_keyboard=True
)

def load_config():
    """Load API key and bot token from environment variables"""
    bot_token = os.getenv('GOBLINBOT_TOKEN')
    api_key = os.getenv('WELL_API_KEY')
    
    if not bot_token:
        print("Error: GOBLINBOT_TOKEN environment variable not set")
        sys.exit(1)
    
    if not api_key:
        print("Error: WELL_API_KEY environment variable not set")
        sys.exit(1)
    
    return bot_token, api_key

def get_headers(api_key):
    """Get API headers"""
    return {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    }

async def add_transaction(data, headers):
    """Add transaction to API"""
    try:
        response = requests.post(
            "https://vulkan.sumeetsaini.com/vault/spend",
            json=data,
            headers=headers
        )
        return response.status_code, response.json()
    except Exception as e:
        return 0, {"error": f"Network error: {str(e)}"}

async def add_income(data, headers):
    """Add income to API"""
    try:
        response = requests.post(
            "https://vulkan.sumeetsaini.com/vault/income",
            json=data,
            headers=headers
        )
        return response.status_code, response.json()
    except Exception as e:
        return 0, {"error": f"Network error: {str(e)}"}

async def get_categories(headers):
    """Get categories from API"""
    try:
        response = requests.get(
            "https://vulkan.sumeetsaini.com/vault/categories",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error getting categories: {e}")
        return None

async def get_recent_transactions(headers, limit=10):
    """Get recent transactions from API"""
    try:
        response = requests.get(
            "https://vulkan.sumeetsaini.com/vault/data",
            headers=headers
        )
        if response.status_code == 200:
            # Parse CSV and get recent entries
            csv_data = response.text
            if csv_data:
                lines = csv_data.strip().split('\n')
                if len(lines) > 1:  # Skip header
                    reader = csv.DictReader(lines[1:])
                    entries = list(reader)
                    return entries[-limit:]  # Return last 'limit' entries
        return []
    except Exception as e:
        print(f"Error getting transactions: {e}")
        return []

async def get_recent_income(headers, limit=5):
    """Get recent income from API"""
    try:
        response = requests.get(
            "https://vulkan.sumeetsaini.com/vault/income",
            headers=headers
        )
        if response.status_code == 200:
            csv_data = response.text
            if csv_data:
                lines = csv_data.strip().split('\n')
                if len(lines) > 1:  # Skip header
                    reader = csv.DictReader(lines[1:])
                    entries = list(reader)
                    return entries[-limit:]  # Return last 'limit' entries
        return []
    except Exception as e:
        print(f"Error getting income: {e}")
        return []

def validate_date(date_str):
    """Validate date format YYYY-MM-DD"""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_amount(amount_str):
    """Validate amount format"""
    try:
        amount = float(amount_str)
        if amount <= 0:
            return False, "Amount must be positive"
        if amount > 999999.99:
            return False, "Amount cannot exceed 999,999.99"
        # Check decimal places
        if len(str(amount).split('.')[-1]) > 2:
            return False, "Amount cannot have more than 2 decimal places"
        return True, float(amount)
    except ValueError:
        return False, "Invalid amount format"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the bot and show main menu"""
    await update.message.reply_text(
        "👹 *Goblin Financial Bot Ready!*\n\n"
        "I handle your financial transactions and income.\n"
        "Choose an option:",
        reply_markup=MAIN_KEYBOARD,
        parse_mode='Markdown'
    )
    return MAIN_MENU

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle main menu selection"""
    text = update.message.text.strip()
    
    if text == "💸 Add Transaction":
        # Start transaction flow with today's date
        context.user_data['transaction'] = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'name': '',
            'amount': '',
            'category': '',
            'subcategory': '',
            'payment_method': '',
            'notes': ''
        }
        await update.message.reply_text(
            f"📅 *Date: {context.user_data['transaction']['date']}*\n\n"
            "📝 Enter transaction name/description:",
            parse_mode='Markdown'
        )
        return TRANSACTION_NAME
    
    elif text == "💰 Add Income":
        # Start income flow with today's date
        context.user_data['income'] = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'name': '',
            'amount': ''
        }
        await update.message.reply_text(
            f"📅 *Date: {context.user_data['income']['date']}*\n\n"
            "📝 Enter income name/description:",
            parse_mode='Markdown'
        )
        return INCOME_NAME
    
    elif text == "📊 View Recent":
        await show_recent_data(update, context)
        return MAIN_MENU
    
    elif text == "📋 Categories":
        await show_categories(update, context)
        return MAIN_MENU
    
    elif text == "❓ Help":
        await show_help(update, context)
        return MAIN_MENU
    
    else:
        await update.message.reply_text(
            "❌ Invalid selection. Please choose from the menu:",
            reply_markup=MAIN_KEYBOARD
        )
        return MAIN_MENU

async def handle_transaction_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle transaction name input"""
    name = update.message.text.strip()
    if len(name) == 0 or len(name) > 100:
        await update.message.reply_text(
            "❌ Name must be between 1-100 characters. Please try again:",
            parse_mode='Markdown'
        )
        return TRANSACTION_NAME
    
    context.user_data['transaction']['name'] = name
    await update.message.reply_text(
        f"✅ Name: *{name}*\n\n"
        "💰 Enter amount:",
        parse_mode='Markdown'
    )
    return TRANSACTION_AMOUNT

async def handle_transaction_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle transaction amount input"""
    amount_str = update.message.text.strip()
    valid, result = validate_amount(amount_str)
    
    if not valid:
        await update.message.reply_text(
            f"❌ {result}. Please enter amount again:",
            parse_mode='Markdown'
        )
        return TRANSACTION_AMOUNT
    
    context.user_data['transaction']['amount'] = result
    await update.message.reply_text(
        f"✅ Amount: *${result:.2f}*\n\n"
        "📁 Loading categories...",
        parse_mode='Markdown'
    )
    
    # Show category selection
    await show_category_selection(update, context)
    return TRANSACTION_CATEGORY

async def show_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show category selection"""
    api_key = context.bot_data.get('api_key')
    headers = get_headers(api_key)
    categories = await get_categories(headers)
    
    if not categories:
        await update.message.reply_text(
            "❌ Failed to load categories. Please try again later.",
            reply_markup=MAIN_KEYBOARD
        )
        return
    
    # Create inline keyboard for categories
    keyboard = []
    for category in categories.keys():
        keyboard.append([InlineKeyboardButton(category, callback_data=f"cat_{category}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📁 Select category:",
        reply_markup=reply_markup
    )

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category selection via callback query"""
    query = update.callback_query
    await query.answer()
    
    category = query.data.replace("cat_", "")
    context.user_data['transaction']['category'] = category
    
    # Get subcategories for this category
    api_key = context.bot_data.get('api_key')
    headers = get_headers(api_key)
    categories = await get_categories(headers)
    
    if categories and category in categories and categories[category]:
        # Show subcategory selection
        keyboard = []
        for subcategory in categories[category]:
            keyboard.append([InlineKeyboardButton(subcategory, callback_data=f"sub_{subcategory}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"📁 Category: *{category}*\n\n"
            "📂 Select subcategory:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return TRANSACTION_SUBCATEGORY
    else:
        # No subcategories, go to payment method
        context.user_data['transaction']['subcategory'] = ''
        await query.edit_message_text(
            f"📁 Category: *{category}*\n\n"
            "💳 Select payment method:",
            reply_markup=PAYMENT_KEYBOARD,
            parse_mode='Markdown'
        )
        return TRANSACTION_PAYMENT

async def handle_subcategory_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle subcategory selection via callback query"""
    query = update.callback_query
    await query.answer()
    
    subcategory = query.data.replace("sub_", "")
    context.user_data['transaction']['subcategory'] = subcategory
    
    await query.edit_message_text(
        f"📁 Category: *{context.user_data['transaction']['category']}*\n"
        f"📂 Subcategory: *{subcategory}*\n\n"
        "💳 Select payment method:",
        reply_markup=PAYMENT_KEYBOARD,
        parse_mode='Markdown'
    )
    return TRANSACTION_PAYMENT

async def handle_transaction_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment method selection"""
    payment = update.message.text.strip().lower()
    if payment not in ['credit', 'debit']:
        await update.message.reply_text(
            "❌ Please select Credit or Debit:",
            reply_markup=PAYMENT_KEYBOARD
        )
        return TRANSACTION_PAYMENT
    
    context.user_data['transaction']['payment_method'] = payment
    await update.message.reply_text(
        f"💳 Payment: *{payment.title()}*\n\n"
        "📝 Enter notes (optional, send /skip to skip):",
        parse_mode='Markdown'
    )
    return TRANSACTION_NOTES

async def handle_transaction_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle transaction notes"""
    if update.message.text.strip().lower() == '/skip':
        context.user_data['transaction']['notes'] = ''
    else:
        context.user_data['transaction']['notes'] = update.message.text.strip()
    
    # Show confirmation
    await show_transaction_confirmation(update, context)
    return TRANSACTION_CONFIRM

async def show_transaction_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show transaction confirmation"""
    trans = context.user_data['transaction']
    confirmation_text = (
        f"🔍 *Confirm Transaction*\n\n"
        f"📅 Date: {trans['date']}\n"
        f"📝 Name: {trans['name']}\n"
        f"💰 Amount: ${trans['amount']:.2f}\n"
        f"📁 Category: {trans['category']}\n"
        f"📂 Subcategory: {trans['subcategory']}\n"
        f"💳 Payment: {trans['payment_method'].title()}\n"
    )
    
    if trans['notes']:
        confirmation_text += f"📝 Notes: {trans['notes']}\n"
    
    confirmation_text += "\n✅ Confirm or ❌ Cancel?"
    
    await update.message.reply_text(
        confirmation_text,
        reply_markup=CONFIRM_KEYBOARD,
        parse_mode='Markdown'
    )

async def handle_transaction_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle transaction confirmation"""
    if update.message.text.strip() == "✅ Confirm":
        trans = context.user_data['transaction']
        
        api_key = context.bot_data.get('api_key')
        headers = get_headers(api_key)
        
        status_code, response = await add_transaction(trans, headers)
        
        if status_code in [200, 201]:
            await update.message.reply_text(
                f"✅ *Transaction added successfully!*\n\n"
                f"💸 ${trans['amount']:.2f} - {trans['name']}\n"
                f"📁 {trans['category']}/{trans['subcategory']}\n\n"
                f"Back to main menu:",
                reply_markup=MAIN_KEYBOARD,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ *Failed to add transaction*\n\n"
                f"Error: {response.get('error', 'Unknown error')}\n\n"
                f"Please try again.",
                reply_markup=MAIN_KEYBOARD,
                parse_mode='Markdown'
            )
        
        context.user_data.clear()
        return MAIN_MENU
    else:
        await update.message.reply_text(
            "❌ Transaction cancelled.\n\n"
            "Back to main menu:",
            reply_markup=MAIN_KEYBOARD
        )
        context.user_data.clear()
        return MAIN_MENU

async def handle_income_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle income name input"""
    name = update.message.text.strip()
    if len(name) == 0 or len(name) > 100:
        await update.message.reply_text(
            "❌ Name must be between 1-100 characters. Please try again:",
            parse_mode='Markdown'
        )
        return INCOME_NAME
    
    context.user_data['income']['name'] = name
    await update.message.reply_text(
        f"✅ Name: *{name}*\n\n"
        "💰 Enter amount:",
        parse_mode='Markdown'
    )
    return INCOME_AMOUNT

async def handle_income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle income amount input"""
    amount_str = update.message.text.strip()
    valid, result = validate_amount(amount_str)
    
    if not valid:
        await update.message.reply_text(
            f"❌ {result}. Please enter amount again:",
            parse_mode='Markdown'
        )
        return INCOME_AMOUNT
    
    context.user_data['income']['amount'] = result
    
    # Show confirmation
    await show_income_confirmation(update, context)
    return INCOME_CONFIRM

async def show_income_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show income confirmation"""
    income = context.user_data['income']
    confirmation_text = (
        f"🔍 *Confirm Income*\n\n"
        f"📅 Date: {income['date']}\n"
        f"📝 Name: {income['name']}\n"
        f"💰 Amount: ${income['amount']:.2f}\n\n"
        f"✅ Confirm or ❌ Cancel?"
    )
    
    await update.message.reply_text(
        confirmation_text,
        reply_markup=CONFIRM_KEYBOARD,
        parse_mode='Markdown'
    )

async def handle_income_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle income confirmation"""
    if update.message.text.strip() == "✅ Confirm":
        income = context.user_data['income']
        
        api_key = context.bot_data.get('api_key')
        headers = get_headers(api_key)
        
        status_code, response = await add_income(income, headers)
        
        if status_code in [200, 201]:
            await update.message.reply_text(
                f"✅ *Income added successfully!*\n\n"
                f"💰 ${income['amount']:.2f} - {income['name']}\n\n"
                f"Back to main menu:",
                reply_markup=MAIN_KEYBOARD,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ *Failed to add income*\n\n"
                f"Error: {response.get('error', 'Unknown error')}\n\n"
                f"Please try again.",
                reply_markup=MAIN_KEYBOARD,
                parse_mode='Markdown'
            )
        
        context.user_data.clear()
        return MAIN_MENU
    else:
        await update.message.reply_text(
            "❌ Income cancelled.\n\n"
            "Back to main menu:",
            reply_markup=MAIN_KEYBOARD
        )
        context.user_data.clear()
        return MAIN_MENU

async def show_recent_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show recent transactions and income"""
    api_key = context.bot_data.get('api_key')
    headers = get_headers(api_key)
    
    transactions = await get_recent_transactions(headers, 5)
    income_entries = await get_recent_income(headers, 3)
    
    message = "📊 *Recent Financial Data*\n\n"
    
    if transactions:
        message += "💸 *Recent Transactions (5):*\n"
        for trans in reversed(transactions):  # Show newest first
            message += f"• {trans['Date']}: ${trans['Amount']} - {trans['Name']}\n"
            message += f"  📁 {trans['Category']}/{trans['Subcategory']}\n\n"
    else:
        message += "💸 No recent transactions\n\n"
    
    if income_entries:
        message += "💰 *Recent Income (3):*\n"
        for income in reversed(income_entries):  # Show newest first
            message += f"• {income['Date']}: ${income['Amount']} - {income['Name']}\n\n"
    else:
        message += "💰 No recent income\n\n"
    
    await update.message.reply_text(
        message,
        reply_markup=MAIN_KEYBOARD,
        parse_mode='Markdown'
    )

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available categories"""
    api_key = context.bot_data.get('api_key')
    headers = get_headers(api_key)
    categories = await get_categories(headers)
    
    if not categories:
        await update.message.reply_text(
            "❌ Failed to load categories.",
            reply_markup=MAIN_KEYBOARD
        )
        return
    
    message = "📋 *Available Categories*\n\n"
    
    for category, subcategories in categories.items():
        message += f"📁 *{category}*\n"
        if subcategories:
            for subcat in subcategories:
                message += f"  📂 {subcat}\n"
        else:
            message += "  (no subcategories)\n"
        message += "\n"
    
    await update.message.reply_text(
        message,
        reply_markup=MAIN_KEYBOARD,
        parse_mode='Markdown'
    )

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help message"""
    help_text = (
        "👹 *Goblin Financial Bot Help*\n\n"
        "🤖 *What I do:*\n"
        "• Add financial transactions (expenses)\n"
        "• Add income entries\n"
        "• View recent transactions and income\n"
        "• Show available categories\n\n"
        "📝 *How to use:*\n"
        "1. Use the menu buttons to navigate\n"
        "2. Follow the prompts for each entry\n"
        "3. Confirm before submitting\n\n"
        "💡 *Tips:*\n"
        "• Amount format: 25.50 or 100\n"
        "• Date defaults to today\n"
        "• Payment method: Credit or Debit\n"
        "• Notes are optional\n\n"
        "Commands:\n"
        "/start - Show main menu\n"
        "/help - Show this help\n"
        "/cancel - Cancel current operation\n\n"
        "Ready to manage your finances!"
    )
    
    await update.message.reply_text(
        help_text,
        reply_markup=MAIN_KEYBOARD,
        parse_mode='Markdown'
    )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current operation"""
    await update.message.reply_text(
        "❌ Operation cancelled.\n\n"
        "Back to main menu:",
        reply_markup=MAIN_KEYBOARD
    )
    context.user_data.clear()
    return MAIN_MENU

def main():
    """Main bot function"""
    # Load configuration
    bot_token, api_key = load_config()
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Store API key in bot_data
    application.bot_data['api_key'] = api_key
    
    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_selection)],
            TRANSACTION_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction_name)],
            TRANSACTION_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction_amount)],
            TRANSACTION_CATEGORY: [CallbackQueryHandler(handle_category_selection)],
            TRANSACTION_SUBCATEGORY: [CallbackQueryHandler(handle_subcategory_selection)],
            TRANSACTION_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction_payment)],
            TRANSACTION_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction_notes)],
            TRANSACTION_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction_confirm)],
            INCOME_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_income_name)],
            INCOME_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_income_amount)],
            INCOME_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_income_confirm)],
        },
        fallbacks=[CommandHandler('cancel', cancel_command)],
        per_user=True,
        per_chat=True,
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', show_help))
    
    # Start the bot
    print("👹 Starting Goblin Financial Bot...")
    application.run_polling()

if __name__ == '__main__':
    main()