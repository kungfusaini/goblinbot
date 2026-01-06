#!/usr/bin/env python3

import os
import sys
import requests
import csv
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# States for conversation
MAIN_MENU = 0
EXPENSE_NAME = 1
EXPENSE_AMOUNT = 2
EXPENSE_CATEGORY = 3
EXPENSE_PAYMENT = 4
EXPENSE_NOTES = 5
EXPENSE_CONFIRM = 6
INCOME_NAME = 7
INCOME_AMOUNT = 8
INCOME_CONFIRM = 9

# Main menu keyboard
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [["💸 Add Expense"], ["💰 Add Income"]],
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

def add_expense(data, headers):
    """Add expense to API"""
    try:
        response = requests.post(
            "https://vulkan.sumeetsaini.com/vault/spend",
            json=data,
            headers=headers,
            timeout=30
        )
        return response.status_code, response.json()
    except requests.exceptions.Timeout:
        return 0, {"error": "Request timeout - please try again"}
    except Exception as e:
        return 0, {"error": f"Network error: {str(e)}"}

def add_income(data, headers):
    """Add income to API"""
    try:
        response = requests.post(
            "https://vulkan.sumeetsaini.com/vault/income",
            json=data,
            headers=headers,
            timeout=30
        )
        return response.status_code, response.json()
    except requests.exceptions.Timeout:
        return 0, {"error": "Request timeout - please try again"}
    except Exception as e:
        return 0, {"error": f"Network error: {str(e)}"}

def get_categories(headers):
    """Get categories from API"""
    try:
        response = requests.get(
            "https://vulkan.sumeetsaini.com/vault/categories",
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.Timeout:
        print("Error getting categories: Request timeout")
        return None
    except Exception as e:
        print(f"Error getting categories: {e}")
        return None

def validate_amount(amount_str):
    """Validate amount format"""
    try:
        amount = float(amount_str)
        if amount <= 0:
            return False, "Amount must be positive"
        if amount > 999999.99:
            return False, "Amount cannot exceed 999,999.99"
        return True, float(amount)
    except ValueError:
        return False, "Invalid amount format"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the bot and show main menu"""
    await update.message.reply_text(
        "👹 *Goblin Financial Bot Ready!*\n\n"
        "I handle expenses and income.\n"
        "Choose an option:",
        reply_markup=MAIN_KEYBOARD,
        parse_mode='Markdown'
    )
    return MAIN_MENU

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle main menu selection"""
    text = update.message.text.strip()
    
    if text == "💸 Add Expense":
        # Start expense flow with today's date
        context.user_data['expense'] = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'name': '',
            'amount': '',
            'category': '',
            'payment_method': '',
            'notes': ''
        }
        await update.message.reply_text(
            f"📅 *Date: {context.user_data['expense']['date']}*\n\n"
            "📝 Enter expense name/description:",
            parse_mode='Markdown'
        )
        return EXPENSE_NAME
    
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
    
    else:
        await update.message.reply_text(
            "❌ Invalid selection. Please choose from the menu:",
            reply_markup=MAIN_KEYBOARD
        )
        return MAIN_MENU

async def handle_expense_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle expense name input"""
    name = update.message.text.strip()
    if len(name) == 0 or len(name) > 100:
        await update.message.reply_text(
            "❌ Name must be between 1-100 characters. Please try again:",
            parse_mode='Markdown'
        )
        return EXPENSE_NAME
    
    context.user_data['expense']['name'] = name
    await update.message.reply_text(
        f"✅ Name: *{name}*\n\n"
        "💰 Enter amount:",
        parse_mode='Markdown'
    )
    return EXPENSE_AMOUNT

async def handle_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle expense amount input"""
    amount_str = update.message.text.strip()
    valid, result = validate_amount(amount_str)
    
    if not valid:
        await update.message.reply_text(
            f"❌ {result}. Please enter amount again:",
            parse_mode='Markdown'
        )
        return EXPENSE_AMOUNT
    
    context.user_data['expense']['amount'] = result
    
    # Show category selection
    api_key = context.bot_data.get('api_key')
    headers = get_headers(api_key)
    categories = get_categories(headers)
    
    if not categories:
        await update.message.reply_text(
            "❌ Failed to load categories. Please try again later.",
            reply_markup=MAIN_KEYBOARD
        )
        return MAIN_MENU
    
    # Create inline keyboard for categories
    keyboard = []
    if not categories.get('categories'):
        await update.message.reply_text(
            "❌ Invalid categories response. Please try again later.",
            reply_markup=MAIN_KEYBOARD
        )
        return MAIN_MENU
    
    for category in categories['categories'].keys():
        keyboard.append([{"text": category, "callback_data": f"cat_{category}"}])
    
    # Add "Other" option
    keyboard.append([{"text": "📝 Other (specify category)", "callback_data": "other_category"}])
    
    reply_markup = {"inline_keyboard": keyboard}
    await update.message.reply_text(
        "📁 Select category:",
        reply_markup=reply_markup
    )
    return EXPENSE_CATEGORY

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category selection via callback query"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "other_category":
        await query.edit_message_text(
            "📝 Please enter category name:",
            parse_mode='Markdown'
        )
        return EXPENSE_CATEGORY
    
    if query.data == "other_subcategory":
        await query.edit_message_text(
            "📝 Please enter subcategory name:",
            parse_mode='Markdown'
        )
        return EXPENSE_CATEGORY
    
    category = query.data.replace("cat_", "")
    
    # Get categories to check for subcategories
    api_key = context.bot_data.get('api_key')
    headers = get_headers(api_key)
    categories_data = get_categories(headers)
    
    if categories_data and categories_data.get('categories', {}).get(category):
        # Category has subcategories, show them
        subcategories = categories_data['categories'][category]
        keyboard = []
        
        for subcategory in subcategories:
            keyboard.append([{"text": subcategory, "callback_data": f"sub_{subcategory}"}])
        
        keyboard.append([{"text": "📝 Other (specify subcategory)", "callback_data": "other_subcategory"}])
        
        reply_markup = {"inline_keyboard": keyboard}
        await query.edit_message_text(
            f"📁 Category: *{category}*\n\n"
            f"🏷️ Select subcategory:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Store selected category
        context.user_data['expense']['category'] = category
        return EXPENSE_CATEGORY
    else:
        # No subcategories, proceed to payment method
        context.user_data['expense']['category'] = category
        context.user_data['expense']['subcategory'] = ''
        
        await query.edit_message_text(
            f"📁 Category: *{category}*\n\n"
            "💳 Select payment method:",
            reply_markup=PAYMENT_KEYBOARD,
            parse_mode='Markdown'
        )
        return EXPENSE_PAYMENT

async def handle_subcategory_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle subcategory selection via callback query"""
    query = update.callback_query
    await query.answer()
    
    subcategory = query.data.replace("sub_", "")
    context.user_data['expense']['subcategory'] = subcategory
    
    await query.edit_message_text(
        f"🏷️ Subcategory: *{subcategory}*\n\n"
        "💳 Select payment method:",
        reply_markup=PAYMENT_KEYBOARD,
        parse_mode='Markdown'
    )
    return EXPENSE_PAYMENT

async def handle_expense_category_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle manual category entry"""
    category = update.message.text.strip()
    if len(category) == 0 or len(category) > 50:
        await update.message.reply_text(
            "❌ Category must be 1-50 characters. Please try again:",
            parse_mode='Markdown'
        )
        return EXPENSE_CATEGORY
    
    context.user_data['expense']['category'] = category
    context.user_data['expense']['subcategory'] = ''
    
    await update.message.reply_text(
        f"📁 Category: *{category}*\n\n"
        "💳 Select payment method:",
        reply_markup=PAYMENT_KEYBOARD,
        parse_mode='Markdown'
    )
    return EXPENSE_PAYMENT

async def handle_expense_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment method selection"""
    payment = update.message.text.strip().lower()
    if payment not in ['credit', 'debit']:
        await update.message.reply_text(
            "❌ Please select Credit or Debit:",
            reply_markup=PAYMENT_KEYBOARD
        )
        return EXPENSE_PAYMENT
    
    context.user_data['expense']['payment_method'] = payment
    await update.message.reply_text(
        f"💳 Payment: *{payment.title()}*\n\n"
        "📝 Enter notes (optional, send /skip to skip):",
        parse_mode='Markdown'
    )
    return EXPENSE_NOTES

async def handle_expense_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle expense notes"""
    if update.message.text.strip().lower() == '/skip':
        context.user_data['expense']['notes'] = ''
    else:
        context.user_data['expense']['notes'] = update.message.text.strip()
    
    # Show confirmation
    await show_expense_confirmation(update, context)
    return EXPENSE_CONFIRM

async def show_expense_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show expense confirmation"""
    exp = context.user_data['expense']
    confirmation_text = (
        f"🔍 *Confirm Expense*\n\n"
        f"📅 Date: {exp['date']}\n"
        f"📝 Name: {exp['name']}\n"
        f"💰 Amount: ${exp['amount']:.2f}\n"
        f"📁 Category: {exp['category']}\n"
        f"💳 Payment: {exp['payment_method'].title()}\n"
    )
    
    if exp['notes']:
        confirmation_text += f"📝 Notes: {exp['notes']}\n"
    
    confirmation_text += "\n✅ Confirm or ❌ Cancel?"
    
    await update.message.reply_text(
        confirmation_text,
        reply_markup=CONFIRM_KEYBOARD,
        parse_mode='Markdown'
    )

async def handle_expense_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle expense confirmation"""
    if update.message.text.strip() == "✅ Confirm":
        exp = context.user_data['expense']
        
        api_key = context.bot_data.get('api_key')
        headers = get_headers(api_key)
        
        status_code, response = add_expense(exp, headers)
        
        if status_code in [200, 201]:
            await update.message.reply_text(
                f"✅ *Expense added successfully!*\n\n"
                f"💸 ${exp['amount']:.2f} - {exp['name']}\n"
                f"📁 {exp['category']}\n\n"
                f"Back to main menu:",
                reply_markup=MAIN_KEYBOARD,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ *Failed to add expense*\n\n"
                f"Error: {response.get('error', 'Unknown error')}\n\n"
                f"Please try again.",
                reply_markup=MAIN_KEYBOARD,
                parse_mode='Markdown'
            )
        
        context.user_data.clear()
        return MAIN_MENU
    else:
        await update.message.reply_text(
            "❌ Expense cancelled.\n\n"
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
        
        status_code, response = add_income(income, headers)
        
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
            EXPENSE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expense_name)],
            EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expense_amount)],
            EXPENSE_CATEGORY: [CallbackQueryHandler(handle_category_selection, pattern='^cat_'), CallbackQueryHandler(handle_subcategory_selection, pattern='^sub_'), CallbackQueryHandler(handle_category_selection, pattern='^(other_category|other_subcategory)$'), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expense_category_text)],
            EXPENSE_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expense_payment)],
            EXPENSE_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expense_notes)],
            EXPENSE_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expense_confirm)],
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
    
    # Start the bot
    print("👹 Starting Goblin Financial Bot...")
    application.run_polling()

if __name__ == '__main__':
    main()