# Kelime Oyunu (Word Guessing Game)

A Turkish word guessing game with a modern UI built using tkinter. The application features theme selection, language switching, and an improved architecture.

## Features

- Clean architecture with separation of concerns
- Word guessing gameplay with time limit
- Score tracking
- Hint system (letter reveal and detailed hints)
- Multiple themes (Blue, Dark, Light, Green)
- Language support (Turkish, English)
- Settings dialog for changing preferences

## Installation

1. Make sure you have Python 3.6+ installed
2. Install required dependencies:
   ```
   pip install pyodbc
   ```
3. Set up a SQL Server database named "kelimeOyunu" with a table named "kelimeler" containing:
   - kelime (word)
   - aciklama (description)
   - detayli (detailed description)
   - zorluk (difficulty level: 'kolay', 'orta', 'zor')

## Running the Application

There are three ways to run the application:

### 1. Simple Way (Recommended if you have import errors)

Run the standalone script:

```
python start_game.py
```

This contains all code in a single file and doesn't use the modular architecture.

### 2. Using run.py (Recommended)

Run the application using the run script:

```
python run.py
```

This script adds the project directory to Python's path and runs the main module correctly.

### 3. Using app.main (For development)

First, install the package in development mode:

```
pip install -e .
```

Then run:

```
python -m app.main
```

## Troubleshooting

If you encounter a "ModuleNotFoundError: No module named 'app'" error, use the first or second method to run the application. 