from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
from dotenv import load_dotenv
from pathlib import Path
import logging
import os

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class StudyBotTelegram:
    def __init__(self):
        load_dotenv()
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
        
        self.application = Application.builder().token(self.bot_token).build()
        self.setup_handlers()
        
        # Load available subjects
        self.load_subjects()
    
    def load_subjects(self):
        """Load available subjects from sources.json and notes_link.json"""
        try:
            with open("data/sources.json", "r") as f:
                self.sources = json.load(f)

            with open("data/notes_link.json", "r") as f:
                self.notes_links = json.load(f)
                
        except FileNotFoundError:
            self.sources = {}
            self.notes_links = {}
    
    def setup_handlers(self):
        """Set up all command and message handlers"""
        # Commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("subjects", self.subjects_command))
        self.application.add_handler(CommandHandler("download", self.download_command))
        self.application.add_handler(CommandHandler("ask", self.ask_command))
        self.application.add_handler(CommandHandler("notes", self.notes_command))  # New command
        self.application.add_handler(CommandHandler("send", self.send_notes_command))  # New command
        
        # Callback handlers for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🎓 **Welcome to StudyBot!** 🎓

I'm your AI-powered study assistant. Here's what I can do for you:

📚 **Download Study Materials**: Get PDFs for your subjects
🤖 **Answer Questions**: Ask me anything about your study materials
📄 **Send Notes**: Get your downloaded notes as files
📖 **Subject Management**: Browse available subjects

**Quick Start:**
• Use /subjects to see available subjects
• Use /download <branch> <subject_code> to download materials
• Use /notes <subject_code> to get your notes as files
• Just type your question to get AI-powered answers!

Type /help for detailed instructions.
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 View Subjects", callback_data="subjects")],
            [InlineKeyboardButton("📥 Download Materials", callback_data="download")],
            [InlineKeyboardButton("📄 Get Notes", callback_data="notes")],
            [InlineKeyboardButton("❓ Ask Question", callback_data="ask")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📖 **StudyBot Help Guide**

**Available Commands:**
• `/start` - Start the bot and see main menu
• `/help` - Show this help message
• `/subjects` - List all available subjects
• `/download <branch> <subject_code>` - Download study materials
• `/ask <question>` - Ask a question about your materials
• `/notes <subject_code>` - Get downloaded notes as PDF files
• `/send <subject_code>` - Alternative command to get notes

**Usage Examples:**
• `/download cse BCS503` - Download Computer Networks materials
• `/notes BCS503` - Get BCS503 PDF files
• `/ask explain DBMS normalization` - Ask about database concepts

**Supported Branches:**
• CSE (Computer Science)
• ECE (Electronics)
• And more...

**Tips:**
• Make sure to download materials before asking questions or requesting notes
• Be specific with your questions for better answers
• Use proper subject codes (e.g., BCS503, BEC304)

Need more help? Just type your question!
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def subjects_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subjects command"""
        self.load_subjects()  # Refresh subjects list
        
        if not self.sources and not self.notes_links:
            await update.message.reply_text(
                "📚 No subjects available yet. Use /download to add some!"
            )
            return
        
        all_subjects = set(list(self.sources.keys()) + list(self.notes_links.keys()))
        
        subjects_text = "📚 **Available Subjects:**\n\n"
        for subject in sorted(all_subjects):
            # Check if files exist locally
            notes_path = Path(f"notes/{subject}")
            has_files = notes_path.exists() and any(notes_path.glob("*.pdf"))
            
            if has_files:
                status = "✅📄"
            elif subject in self.notes_links:
                status = "✅"
            else:
                status = "📥"
            
            subjects_text += f"{status} `{subject}`\n"
        
        subjects_text += "\n✅📄 = Downloaded with files\n✅ = Downloaded\n📥 = Available for download"
        
        keyboard = [
            [InlineKeyboardButton("📥 Download Materials", callback_data="download")],
            [InlineKeyboardButton("📄 Get Notes", callback_data="notes")],
            [InlineKeyboardButton("❓ Ask Question", callback_data="ask")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            subjects_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def notes_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /notes command - send PDF files to user"""
        if not context.args:
            await update.message.reply_text(
                "❌ **Usage:** `/notes <subject_code>`\n\n"
                "**Example:** `/notes BCS503`\n\n"
                "Use `/subjects` to see available subjects.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        subject_code = context.args[0].upper()
        await self.send_notes_files(update, subject_code)
    
    async def send_notes_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /send command - alternative to /notes"""
        if not context.args:
            await update.message.reply_text(
                "❌ **Usage:** `/send <subject_code>`\n\n"
                "**Example:** `/send BCS503`\n\n"
                "Use `/subjects` to see available subjects.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        subject_code = context.args[0].upper()
        await self.send_notes_files(update, subject_code)
    
    async def send_notes_files(self, update: Update, subject_code: str):
        """Send PDF files for a specific subject"""
        notes_path = Path(f"notes/{subject_code}")
        
        if not notes_path.exists():
            await update.message.reply_text(
                f"❌ **No notes found for {subject_code}**\n\n"
                f"Use `/download <branch> {subject_code}` to download materials first.\n\n"
                "Use `/subjects` to see available subjects.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Get all PDF files
        pdf_files = list(notes_path.glob("*.pdf"))
        
        if not pdf_files:
            await update.message.reply_text(
                f"❌ **No PDF files found for {subject_code}**\n\n"
                f"The notes folder exists but contains no PDF files.\n"
                f"Try downloading again: `/download <branch> {subject_code}`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Send initial message
        status_message = await update.message.reply_text(
            f"📄 **Sending {len(pdf_files)} PDF files for {subject_code}...**\n\n"
            "⏳ Please wait while I upload the files...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Send each PDF file
        sent_files = 0
        failed_files = 0
        
        for pdf_file in pdf_files:
            try:
                await update.message.reply_document(pdf_file)
                sent_files += 1
            except Exception as e:
                logger.error(f"Failed to send {pdf_file}: {e}")
                failed_files += 1
        
        # Send completion message
        completion_text = f"✅ **File transfer complete for {subject_code}!**\n\n"
        completion_text += f"📄 Files sent: {sent_files}\n"
        if failed_files > 0:
            completion_text += f"❌ Failed: {failed_files}\n"
        completion_text += f"\n📚 Total size: {sum(f.stat().st_size for f in pdf_files) / (1024*1024):.1f}MB"
        
        await status_message.edit_text(
            completion_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def download_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /download command"""
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ **Usage:** `/download <branch> <subject_code>`\n\n"
                "**Example:** `/download cse BCS503`\n\n"
                "**Available branches:** cse, ece, mechanical, etc.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        branch = context.args[0].lower()
        subject_code = context.args[1].upper()
        
        # Send initial message
        status_message = await update.message.reply_text(
            f"📥 **Downloading materials for {subject_code}...**\n\n"
            "⏳ This may take a few minutes. Please wait...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Run scraper in a separate thread to avoid blocking
            def download_materials():
                # Call the scraper function here
                pass
            
            # Use thread for blocking operation
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, download_materials)
            
            if result:
                await status_message.edit_text(
                    f"✅ **Successfully downloaded materials for {subject_code}!**",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await status_message.edit_text(
                    f"❌ **Failed to download materials for {subject_code}.**",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        except Exception as e:
            await status_message.edit_text(
                f"❌ **Error downloading {subject_code}:**\n\n"
                f"`{str(e)}`\n\n"
                "Please try again later.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask command"""
        if not context.args:
            await update.message.reply_text(
                "❓ **Usage:** `/ask <your question>`\n\n"
                "**Example:** `/ask explain advantages of DBMS`\n\n"
                "Or just type your question directly without /ask!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        question = " ".join(context.args)
        await self.process_question(update, question)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages as questions"""
        message_text = update.message.text.lower()
        
        # Check if user is asking for notes
        if any(keyword in message_text for keyword in ["send notes", "get notes", "download notes", "notes for"]):
            # Try to extract subject code
            words = update.message.text.split()
            subject_codes = [word.upper() for word in words if word.upper() in self.get_all_subjects()]
            
            if subject_codes:
                await self.send_notes_files(update, subject_codes[0])
            else:
                await update.message.reply_text(
                    "❌ **Could not identify the subject code.**\n\n"
                    "Please specify a valid subject code.",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        # Otherwise, treat as a question
        question = update.message.text
        await self.process_question(update, question)
    
    def get_all_subjects(self):
        """Get all available subject codes"""
        self.load_subjects()
        return set(list(self.sources.keys()) + list(self.notes_links.keys()))
    
    async def process_question(self, update: Update, question: str):
        """Process a question using RAG"""
        # Send typing indicator
        await update.message.chat.send_action("typing")
        
        # Send initial message
        thinking_message = await update.message.reply_text(
            "🤔 **Thinking...**\n\n"
            "⏳ Searching through your study materials...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Get answer using RAG
            answer = "Your answer here"  # Replace with actual RAG processing
            
            await thinking_message.edit_text(
                f"✅ **Answer:**\n\n{answer}",
                parse_mode=ParseMode.MARKDOWN
            )
        
        except Exception as e:
            await thinking_message.edit_text(
                f"❌ **Error processing your question:**\n\n"
                f"`{str(e)}`",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button presses"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "subjects":
            await self.subjects_command(update, context)
        elif query.data == "download":
            await self.download_command(update, context)
        elif query.data == "notes":
            await self.notes_command(update, context)
        elif query.data == "ask":
            await self.ask_command(update, context)
        elif query.data == "help":
            await self.help_command(update, context)
    
    def run(self):
        """Start the bot"""
        print("🤖 StudyBot is starting...")
        print(f"Bot token: {self.bot_token[:10]}...")
        
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

def main():
    """Main function to run the bot"""
    try:
        bot = StudyBotTelegram()
        bot.run()
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        print("Make sure TELEGRAM_BOT_TOKEN is set in your .env file")

if __name__ == "__main__":
    main()