from setuptools import setup, find_packages

setup(
    name="telegram-study-bot",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Telegram bot for managing study materials and answering questions.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/telegram-study-bot",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "python-telegram-bot==20.0a3",
        "beautifulsoup4",
        "requests",
        "pymupdf",
        "chromadb",
        "openai",
        "python-dotenv"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)