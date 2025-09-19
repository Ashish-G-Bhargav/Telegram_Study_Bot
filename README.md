# Telegram Study Bot

## Overview
The Telegram Study Bot is an AI-powered assistant designed to help students manage their study materials, download notes, and answer questions related to their subjects. The bot interacts with users through Telegram, providing a user-friendly interface for accessing educational resources.

## Project Structure
```
telegram-study-bot
├── src
│   ├── telegram_bot.py       # Main logic for the Telegram bot
│   ├── scraper.py            # Web scraper for downloading study materials
│   ├── rag.py                # Handles retrieval-augmented generation (RAG)
│   └── __init__.py           # Marks the directory as a Python package
├── data
│   ├── sources.json          # Subject codes and their source URLs
│   ├── notes_link.json       # Subject codes and downloadable notes links
│   └── .gitkeep              # Keeps the data directory tracked by Git
├── notes
│   └── .gitkeep              # Keeps the notes directory tracked by Git
├── vector_db
│   └── .gitkeep              # Keeps the vector_db directory tracked by Git
├── requirements.txt           # Python dependencies for the project
├── .env.example               # Example environment variables configuration
├── .gitignore                 # Files and directories to ignore by Git
├── README.md                  # Documentation for the project
└── setup.py                   # Packaging information for the project
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd telegram-study-bot
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env` and fill in the required values.

## Usage
1. Run the bot:
   ```
   python src/telegram_bot.py
   ```

2. Interact with the bot on Telegram using the commands:
   - `/start` - Start the bot and see the main menu.
   - `/help` - Show the help message.
   - `/subjects` - List all available subjects.
   - `/download <branch> <subject_code>` - Download study materials.
   - `/ask <question>` - Ask a question about your materials.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.