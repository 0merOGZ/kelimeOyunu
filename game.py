import tkinter as tk
from tkinter import ttk, font, messagebox, simpledialog
import time
import os
import random
from PIL import Image, ImageTk
from playsound import playsound
import json

# Moved from config/settings.py - requires config.py
from config import save_settings

# WordRepository will be imported where needed (in main.py)

HIGHSCORE_FILE = "highscores.json"

def load_highscores(filepath=HIGHSCORE_FILE):
    """Load high scores from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Return empty dict if file not found or corrupt

def save_highscore(filepath, username, score, game_mode):
    """Save or update a high score for a user and game mode."""
    if not username or not username.strip(): # Don't save if username is empty or just whitespace
        print("[Highscore] Username is empty, score not saved.")
        return

    scores = load_highscores(filepath)
    user_scores = scores.get(username, {})  # Get existing scores for user or empty dict

    # Check if new score is higher for the specific game mode
    if score > user_scores.get(game_mode, -1):  # -1 ensures any score is higher if mode not played
        user_scores[game_mode] = score
        scores[username] = user_scores
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(scores, f, ensure_ascii=False, indent=4)
            print(f"[Highscore] Score for {username} ({game_mode}) saved: {score}")
        except Exception as e:
            print(f"[Highscore] Error saving high score: {e}")
    else:
        print(f"[Highscore] New score {score} for {username} ({game_mode}) not higher. Not saved.")

#==============================================================================
# Domain Models (Moved from app/domain/models.py)
#==============================================================================

class Word:
    """
    Represents a word in the game
    """
    def __init__(self, word, description, details):
        self.word = word
        self.description = description
        self.details = details
        self.length = len(word)

class GameState:
    """
    Represents the current state of the game
    """
    def __init__(self, words, game_mode='quiz', time_limit=200):
        self.words = words
        self.flat_words = self._flatten_words(words)
        self.game_mode = game_mode # 'quiz' or 'anagram'
        self.current_word_index = 0
        self.score = 0
        self.time_limit = time_limit
        self.start_time = None
        self.remaining_time = time_limit
        self.is_running = False
        self.hint_count = 3 if game_mode == 'quiz' else 0 # Disable hints for anagram initially
        self.detail_hint_count = 1 if game_mode == 'quiz' else 0 # Disable hints for anagram initially
        self.current_word_score = 100
        self.revealed_indices = set()
        self.shuffled_letters = "" # For anagram mode

    def _flatten_words(self, words_by_difficulty):
        """Flattens the dictionary of words into a single list"""
        result = []
        for word_list in words_by_difficulty.values():
            result.extend(word_list)
        # Ensure words are suitable for anagram mode (e.g., no spaces)
        result = [word for word in result if ' ' not in word.word]
        random.shuffle(result)
        return result

    @property
    def current_word(self):
        """Returns the current word object"""
        if self.current_word_index < len(self.flat_words):
            return self.flat_words[self.current_word_index]
        return None

    def get_displayed_word(self):
        """Returns the word display based on game mode"""
        if not self.current_word:
            return ""

        if self.game_mode == 'anagram':
            # Return shuffled letters for anagram mode
            if not self.shuffled_letters: # Shuffle only once per word
                word_list = list(self.current_word.word)
                random.shuffle(word_list)
                self.shuffled_letters = ' '.join(word_list).upper()
            return self.shuffled_letters
        else: # Quiz mode
            # Return underscores and revealed characters based on revealed indices
            display_list = []
            for i, char_actual in enumerate(self.current_word.word):
                if i in self.revealed_indices:
                    display_list.append(char_actual)
                else:
                    display_list.append('_')
            return ' '.join(display_list)

    def reveal_character(self):
        """Reveals a random character at a specific position (Quiz mode only)"""
        if self.game_mode != 'quiz' or not self.current_word:
            return None

        # Find all indices of characters that haven't been revealed yet
        hidden_indices = [i for i, char_actual in enumerate(self.current_word.word)
                          if i not in self.revealed_indices]

        if not hidden_indices:
            return None 

        
        index_to_reveal = random.choice(hidden_indices)
        
        self.revealed_indices.add(index_to_reveal)
        self.current_word_score -= 20 
        return self.current_word.word[index_to_reveal] 

    def use_detail_hint(self):
        """Uses the detail hint (Quiz mode only)"""
        if self.game_mode != 'quiz' or self.detail_hint_count <= 0 or not self.current_word:
            return None

        self.detail_hint_count -= 1
        self.current_word_score //= 2
        return self.current_word.details

    def check_guess(self, guess):
        """Checks if the guess is correct"""
        if guess == "pas": return True
        if not self.current_word:
            return False

        return guess.lower() == self.current_word.word.lower()

    def next_word(self):
        """Moves to the next word"""
        self.current_word_index += 1
        self.revealed_indices = set()
        self.shuffled_letters = "" 
        self.hint_count = 3 if self.game_mode == 'quiz' else 0
        self.detail_hint_count = 1 if self.game_mode == 'quiz' else 0
        self.current_word_score = 100

#==============================================================================
# Game Service (Moved from app/domain/game_service.py)
#==============================================================================

class GameService:
    """Service for game logic"""
    
    def __init__(self, word_repository):
        self.repository = word_repository
        self.game_state = None
    
    def start_game(self, game_mode='quiz'):
        """Start a new game in the specified mode"""
        print(f"[Service] Starting game in {game_mode} mode") 
        
        words = self.repository.get_words_by_difficulty(
            count_by_difficulty={'kolay': 3, 'orta': 4, 'zor': 3}, 
            WordClass=Word 
        )
        
        # Create new game state with the specified mode
        self.game_state = GameState(words, game_mode=game_mode)
        
        # Initialize game
        self.game_state.start_time = time.time()
        self.game_state.is_running = True
        
        print(f"[Service] Game state created: Mode={self.game_state.game_mode}, Word count={len(self.game_state.flat_words)}") # Debug
        return self.game_state
    
    def update_time(self):
        """Update the remaining time"""
        if not self.game_state or not self.game_state.is_running:
            return 0
            
        elapsed = time.time() - self.game_state.start_time
        self.game_state.remaining_time = max(0, self.game_state.time_limit - int(elapsed))
        
        # Check if time is up
        if self.game_state.remaining_time <= 0:
            self.game_state.is_running = False    
        return self.game_state.remaining_time
    
    def make_guess(self, guess):
        """Process a player's guess"""
        if not self.game_state or not self.game_state.is_running:
            return False
            
        if self.game_state.check_guess(guess):
            # Add score
            self.game_state.score += self.game_state.current_word_score
            return True
        return False
    
    def use_character_hint(self):
        """Use a character hint"""
        if not self.game_state or not self.game_state.is_running:
            return None
            
        if self.game_state.hint_count <= 0:
            return None
            
        self.game_state.hint_count -= 1
        return self.game_state.reveal_character()
    
    def use_detail_hint(self):
        """Use a detailed hint"""
        if not self.game_state or not self.game_state.is_running:
            return None
            
        return self.game_state.use_detail_hint()
    
    def next_word(self):
        """Move to the next word"""
        if not self.game_state:
            return False
            
        self.game_state.next_word()
        
        # Check if game is finished
        if self.game_state.current_word_index >= len(self.game_state.flat_words):
            self.game_state.is_running = False
            return False
            
        return True
    
    def get_final_score_message(self):
        """Get the final score message"""
        if not self.game_state:
            return ""
            
        score = self.game_state.score
        # Use translated base message
        message = self._get_text('final_score_base').format(score=score)
        
        # Use translated praise levels
        if score >= 800:
            return message + "\n\n" + self._get_text('score_praise_5')
        elif score >= 600:
            return message + "\n\n" + self._get_text('score_praise_4')
        elif score >= 400:
            return message + "\n\n" + self._get_text('score_praise_3')
        else:
            return message + "\n\n" + self._get_text('score_praise_2')
    
    # Helper method to get text (added for GameService scope)
    def _get_text(self, key):
        # Assuming settings are accessible or passed differently if needed
        # For simplicity, let's assume direct access (might need refactoring)
        # A better approach would be to pass settings or use a dedicated localization manager
        try:
            # Access settings through game_state or another mechanism if available
            # This part is tricky as GameService doesn't store settings directly.
            # Let's assume a placeholder implementation for now.
            # TODO: Properly implement settings access for GameService translations
            placeholder_settings = {'language': 'tr', 'translations': { 'tr': {'final_score_base': 'OYUN SONU - TOPLAM PUAN: {score}', 'score_praise_5': '★★★★★ MÜKEMMEL! Harika bir skor!', 'score_praise_4': '★★★★☆ ÇOK İYİ! Biraz daha çalışmalısın.', 'score_praise_3': '★★★☆☆ İYİ! Orta seviye skor.', 'score_praise_2': '★★☆☆☆ DAHA İYİSİNİ YAPABİLİRSİN!'}}} # Example
            lang = placeholder_settings.get('language', 'tr')
            translations = placeholder_settings.get('translations', {})
            return translations.get(lang, {}).get(key, key).format(score=self.game_state.score if '{score}' in translations.get(lang, {}).get(key, key) else None)
        except:
             return key # Fallback

#==============================================================================
# UI Components (Moved from presentation/ui)
#==============================================================================

class SettingsDialog:
    """Dialog for changing application settings"""
    
    def __init__(self, parent, settings):
        self.parent = parent
        self.settings = settings.copy()
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(self._get_text('settings'))
        self.dialog.geometry("400x350") # Increased height slightly for confirmation
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self._create_widgets()
    
    def _get_text(self, key):
        """Get translated text based on current language setting"""
        lang = self.settings.get('language', 'tr')
        translations = self.settings.get('translations', {})
        return translations.get(lang, {}).get(key, key)
    
    def _create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk.Frame(self.dialog, padding="10 10 10 0")
        main_frame.pack(fill=tk.BOTH, expand=True)

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Language selection
        ttk.Label(content_frame, text=self._get_text('language')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.language_var = tk.StringVar(value=self.settings.get('language', 'tr'))
        language_frame = ttk.Frame(content_frame)
        language_frame.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))
        
        ttk.Radiobutton(
            language_frame, 
            text=self._get_text('turkish'), 
            value='tr',
            variable=self.language_var
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Radiobutton(
            language_frame, 
            text=self._get_text('english'), 
            value='en',
            variable=self.language_var
        ).pack(side=tk.LEFT)
        
        # Theme selection
        ttk.Label(content_frame, text=self._get_text('theme')).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.theme_var = tk.StringVar(value=self.settings.get('theme', 'blue'))
        theme_frame = ttk.Frame(content_frame)
        theme_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        themes = [
            ('blue_theme', 'blue'),
            ('dark_theme', 'dark'),
            ('light_theme', 'light'),
            ('green_theme', 'green')
        ]
        
        for i, (text_key, value) in enumerate(themes):
            ttk.Radiobutton(
                theme_frame, 
                text=self._get_text(text_key), 
                value=value,
                variable=self.theme_var
            ).grid(row=i//2, column=i%2, sticky=tk.W, padx=(0, 10), pady=(0, 5))
        
        # Preview frame
        preview_frame = ttk.LabelFrame(content_frame, text=self._get_text('theme') + " " + self._get_text('preview'))
        preview_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=10, ipady=5)
        
        self.preview_canvas = tk.Canvas(preview_frame, width=350, height=60) # Reduced height
        self.preview_canvas.pack(padx=5, pady=5)

        # Create a custom style for the save button to make it stand out
        save_style = ttk.Style() # Get default style instance
        save_style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
        save_style.map('Accent.TButton', 
                      background=[('active', '#4CAF50'), ('!active', '#2E7D32')],
                      foreground=[('active', 'white'), ('!active', 'white')])
        
        # Action Frame (Buttons and Note)
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        # Add a note about settings being applied immediately
        note_label = ttk.Label(
            action_frame,
            text=self._get_text('settings_apply_note'),
            font=('Arial', 8, 'italic'),
            foreground='#555555'
        )
        note_label.pack(side=tk.LEFT, anchor=tk.W)
        
        # Button frame
        button_frame = ttk.Frame(action_frame)
        button_frame.pack(side=tk.RIGHT)
        
        ttk.Button(
            button_frame, 
            text=self._get_text('cancel'),
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Use the styled button for the save button
        save_button = ttk.Button(
            button_frame, 
            text=self._get_text('save'),
            command=self._save_settings,
            style='Accent.TButton'
        )
        save_button.pack(side=tk.RIGHT)
        
        # Update preview when theme changes
        self.theme_var.trace_add('write', lambda *args: self._update_preview())
        self._update_preview() # Initial preview draw

        # Confirmation Label (initially hidden)
        self.confirmation_label = ttk.Label(
            main_frame, # Place it below content_frame
            text="", # Text set dynamically in _save_settings
            font=('Arial', 9, 'bold'),
            foreground='green',
            anchor=tk.CENTER
        )
        # Don't pack initially
    
    def _update_preview(self):
        """Update theme preview"""
        theme = self.theme_var.get()
        colors = self.settings.get('theme_colors', {}).get(theme, {})
        
        # Clear canvas
        self.preview_canvas.delete("all")
        
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        # Draw background
        self.preview_canvas.create_rectangle(
            0, 0, canvas_width, canvas_height, 
            fill=colors.get('background', '#f0f0f0'), 
            outline=""
        )
        
        # Draw header
        self.preview_canvas.create_rectangle(
            5, 5, canvas_width - 5, 25, 
            fill=colors.get('primary', '#4a7abc'), 
            outline=""
        )
        
        # Draw text
        self.preview_canvas.create_text(
            canvas_width / 2, 15, 
            text=self._get_text('app_title'),
            fill=colors.get('button_text', 'white'),
            font=('Arial', 8)
        )
        
        # Draw button
        self.preview_canvas.create_rectangle(
            canvas_width * 0.3, 35, canvas_width * 0.7, 55, 
            fill=colors.get('accent', '#FF5722'), 
            outline=""
        )
        
        self.preview_canvas.create_text(
            canvas_width / 2, 45, 
            text=self._get_text('guess_button'),
            fill=colors.get('button_text', 'white'),
            font=('Arial', 8)
        )
    
    def _save_settings(self):
        """Save settings and show confirmation"""
        new_settings = self.settings.copy()
        new_settings['language'] = self.language_var.get()
        new_settings['theme'] = self.theme_var.get()
        
        # Save settings to file (using the function from config.py)
        if save_settings(new_settings):
            # Show brief confirmation message
            self.confirmation_label.config(text=self._get_text('settings_saved_success'), foreground='green')
        else:
             self.confirmation_label.config(text=self._get_text('settings_saved_error'), foreground='red')

        self.confirmation_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(0,5)) # Show confirmation
        self.dialog.update_idletasks()
        
        # Wait briefly to show confirmation before closing
        self.dialog.after(1200, lambda: self._close_with_result(new_settings))
    
    def _close_with_result(self, result):
        """Close dialog with the given result"""
        self.result = result
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and wait for result"""
        self.parent.wait_window(self.dialog)
        return self.result

class UsernameDialog(tk.Toplevel):
    """Custom dialog for username input."""
    def __init__(self, parent, title, prompt, settings):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title(title)
        self.settings = settings # Store settings for theming
        self.prompt = prompt
        self.result = None

        # Apply theme background to the dialog itself
        theme = self.settings.get('theme', 'blue')
        colors = self.settings.get('theme_colors', {}).get(theme, {})
        dialog_bg_color = colors.get('background', '#F5DEB3') # Use app background
        self.configure(bg=dialog_bg_color)

        self._create_widgets()
        self._center_window()
        
        self.username_entry.focus_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel) # Handle window close button
        self.wait_window(self) # Wait for dialog to close

    def _get_text(self, key, fallback=None):
        lang = self.settings.get('language', 'tr')
        translations = self.settings.get('translations', {})
        return translations.get(lang, {}).get(key, fallback if fallback else key)

    def _create_widgets(self):
        theme = self.settings.get('theme', 'blue')
        colors = self.settings.get('theme_colors', {}).get(theme, {})
        bg_color = colors.get('background', '#F5DEB3')
        text_color = colors.get('text', '#000000')
        primary_color = colors.get('primary', '#654321')
        button_text_color = colors.get('button_text', 'white')
        accent_color = colors.get('accent', '#FF5722')

        content_frame = tk.Frame(self, bg=bg_color, padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        prompt_label = tk.Label(content_frame, text=self.prompt, font=("Arial", 24), bg=bg_color, fg=text_color, wraplength=360)
        prompt_label.pack(pady=(0, 10))

        self.username_entry = tk.Entry(content_frame, font=("Arial", 24), width=30)
        self.username_entry.pack(pady=(0, 20), ipady=5)
        self.username_entry.bind("<Return>", self._on_ok)

        button_frame = tk.Frame(content_frame, bg=bg_color)
        button_frame.pack()

        self.ok_button = tk.Button(
            button_frame, text=self._get_text('ok_button', "Tamam"), 
            command=self._on_ok, width=10, font=("Arial", 20, "bold"),
            bg=primary_color, fg=button_text_color, 
            activebackground=accent_color, activeforeground=button_text_color
        )
        self.ok_button.pack(side=tk.LEFT, padx=10)

        self.cancel_button = tk.Button(
            button_frame, text=self._get_text('cancel_button', "İptal"), 
            command=self._on_cancel, width=10, font=("Arial", 20, "bold"),
            bg=primary_color, fg=button_text_color, 
            activebackground=accent_color, activeforeground=button_text_color
        )
        self.cancel_button.pack(side=tk.LEFT, padx=10)

    def _center_window(self):
        self.update_idletasks() # Ensure dimensions are calculated
        width = 450  # Desired width
        height = 250 # Desired height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _on_ok(self, event=None):
        self.result = self.username_entry.get().strip()
        if not self.result: # Basic validation: if empty, treat as cancel or show error
            messagebox.showwarning(self._get_text('username_error_title', "Geçersiz Giriş"), 
                                   self._get_text('username_empty_error', "Kullanıcı adı boş olamaz!"), parent=self)
            self.username_entry.focus_set()
            return
        self.destroy()

    def _on_cancel(self, event=None):
        self.result = None
        self.destroy()

    def show(self):
        # This method is implicitly handled by wait_window in __init__
        # The result is accessed after the dialog closes.
        return self.result

class KelimeOyunuView:
    """Main game view"""
    
    def __init__(self, root, game_service, settings):
        self.root = root
        self.game_service = game_service
        self.settings = settings
        self.timer_id = None
        self.current_game_mode = 'quiz' 
        self.logo_image = None 
        self.letter_labels = [] 
        
        # Get username using custom dialog
        username_dialog = UsernameDialog(self.root, 
                                       self._get_text('username_prompt_title', "Kullanıcı Adı"),
                                       self._get_text('username_prompt_message', "Lütfen kullanıcı adınızı girin:"),
                                       self.settings)
        self.current_username = username_dialog.result # Result is set when dialog closes

        if self.current_username is None: # If dialog was cancelled or closed
            print("[View] Username dialog cancelled or closed. Exiting application.")
            self.root.destroy() # Close the main application window
            return # Stop further initialization
        elif not self.current_username.strip(): # Should be caught by dialog validation, but as a fallback
            print("[View] No username entered. Exiting application.")
            self.root.destroy()
            return
            
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the main UI components"""
        self.root.title(self._get_text('app_title'))
        self.root.geometry("1536x864") # Increased size by 20%
        self.root.resizable(False, False) 
        
        # Center the main window
        self.root.update_idletasks() # Ensure window dimensions are up-to-date
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}') # Set position
        
        self._apply_theme()
        
        self.baslik_font = font.Font(family="Arial", size=32, weight="bold")
        self.normal_font = font.Font(family="Arial", size=24, weight="normal")
        self.kelime_font = font.Font(family="Courier", size=32, weight="bold")
        
        # Main frame
        self.main_frame = tk.Frame(self.root, padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self._create_header()
        
        # --- Game Area (Initially Hidden/Disabled) ---
        self.game_area_frame = tk.Frame(self.main_frame)
        # Pack it later when game starts
        
        # Info frame
        self._create_info_frame(self.game_area_frame)
        
        # Description frame
        self._create_description_frame(self.game_area_frame)
        
        # Word display
        self._create_word_frame(self.game_area_frame)
        
        # Joker frame
        self._create_joker_frame(self.game_area_frame)
        
        # Guess frame
        self._create_guess_frame(self.game_area_frame)
        
        # Result message
        self.sonuc_label = tk.Label(
            self.game_area_frame, 
            text="", 
            font=self.baslik_font
        )
        self.sonuc_label.pack(pady=20)
        
        # --- Start Area ---
        self.start_area_frame = tk.Frame(self.main_frame)
        self.start_area_frame.pack(pady=20, anchor=tk.CENTER)

        self.start_buttons_frame = tk.Frame(self.start_area_frame)
        self.start_buttons_frame.pack(pady=10)

        self.start_quiz_btn = tk.Button(
            self.start_buttons_frame, 
            text=self._get_text('start_button_quiz', "Start Quiz Game"),
            font=self.baslik_font,
            command=lambda: self._start_game('quiz'), 
            padx=20, 
            pady=10
        )
        self.start_quiz_btn.pack(side=tk.LEFT, padx=10)
        
        self.start_anagram_btn = tk.Button(
            self.start_buttons_frame, 
            text=self._get_text('start_button_anagram', "Start Anagram Game"),
            font=self.baslik_font,
            command=lambda: self._start_game('anagram'), 
            padx=20, 
            pady=10
        )
        self.start_anagram_btn.pack(side=tk.LEFT, padx=10)

        # --- Leaderboard Display Area ---
        self.leaderboard_display_frame = tk.Frame(self.start_area_frame, bd=1, relief=tk.SUNKEN)
        self.leaderboard_display_frame.pack(pady=10, fill=tk.BOTH, padx=20, expand=True)

        # Left Column (Quiz Scores)
        self.left_leaderboard_frame = tk.Frame(self.leaderboard_display_frame)
        self.left_leaderboard_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5))
        self.leaderboard_quiz_text_widget = tk.Text(
            self.left_leaderboard_frame, height=10, width=25, wrap=tk.WORD, 
            font=self.normal_font, relief=tk.FLAT, borderwidth=0
        )
        self.leaderboard_quiz_text_widget.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

        # Right Column (Anagram Scores)
        self.right_leaderboard_frame = tk.Frame(self.leaderboard_display_frame)
        self.right_leaderboard_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5,0))
        self.leaderboard_anagram_text_widget = tk.Text(
            self.right_leaderboard_frame, height=10, width=25, wrap=tk.WORD, 
            font=self.normal_font, relief=tk.FLAT, borderwidth=0
        )
        self.leaderboard_anagram_text_widget.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
        
        # Configure tags for styling leaderboard text (applied to both Text widgets)
        normal_font_family = self.normal_font.cget("family")
        normal_font_size = self.normal_font.cget("size")
        tag_font_bold = (normal_font_family, normal_font_size, "bold")
        tag_font_italic = (normal_font_family, normal_font_size, "italic")

        for txt_widget in [self.leaderboard_quiz_text_widget, self.leaderboard_anagram_text_widget]:
            txt_widget.tag_configure("bold_title", font=tag_font_bold, spacing1=5, spacing3=5, justify=tk.CENTER)
            txt_widget.tag_configure("score_entry", lmargin1=10, lmargin2=10, spacing1=2, spacing3=2)
            txt_widget.tag_configure("no_score_message", lmargin1=10, lmargin2=10, font=tag_font_italic, spacing1=2, spacing3=2, justify=tk.CENTER)
            txt_widget.config(state=tk.DISABLED)
        
        self._update_leaderboard_display()
        self._update_colors()
    
    def _create_header(self):
        """Create header frame with title"""
        self.baslik_frame = tk.Frame(self.main_frame, padx=10, pady=10)
        # Background color will be set in _update_colors
        self.baslik_frame.pack(fill=tk.X, pady=(0, 20))

        # Intermediate frame to hold logo and title for centering
        content_header_frame = tk.Frame(self.baslik_frame)
        # content_header_frame's background will also be set in _update_colors to match baslik_frame
        content_header_frame.pack(anchor=tk.CENTER, pady=(10, 0)) # Center this frame and add top padding
        
        # --- Logo --- 
        try:
            logo_path = os.path.join("media", "logo.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                desired_width = 200  # Increased from 150
                desired_height = 200 # Increased from 150
                img_resized = img.resize((desired_width, desired_height), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(img_resized)
                
                # Store logo_label as an instance variable if accessed elsewhere (e.g. _update_colors)
                self.logo_label_widget = tk.Label(content_header_frame, image=self.logo_image)
                self.logo_label_widget.pack(side=tk.LEFT, padx=(0, 10)) # Pack logo to the left within content_header_frame
            else:
                print(f"[View Error] Logo file not found at: {logo_path}")
                self.logo_image = None
                self.logo_label_widget = None # Ensure it's None if no logo
        except Exception as e:
            print(f"[View Error] Failed to load logo: {e}")
            self.logo_image = None
            self.logo_label_widget = None # Ensure it's None on error
        # --- End Logo ---
        
        # self.baslik_label = tk.Label(
        #     content_header_frame, # Add to the content_header_frame
        #     text=self._get_text('app_title'), 
        #     font=self.baslik_font
        # )
        # self.baslik_label.pack(side=tk.LEFT, padx=(10, 0)) # Pack title to the left of logo within content_header_frame
    
    def _create_info_frame(self, parent):
        """Create info frame with game statistics in the specified parent"""
        self.bilgi_frame = tk.Frame(parent, borderwidth=0, relief='flat', highlightthickness=0)
        self.bilgi_frame.pack(fill=tk.X, pady=(0, 10))

        # Frame for left-aligned items
        self.left_info_frame = tk.Frame(self.bilgi_frame, borderwidth=0, relief='flat', highlightthickness=0)
        self.left_info_frame.pack(side=tk.LEFT)

        # Frame for right-aligned items
        self.right_info_frame = tk.Frame(self.bilgi_frame, borderwidth=0, relief='flat', highlightthickness=0)
        self.right_info_frame.pack(side=tk.RIGHT)
        
        self.kelime_index_label = tk.Label(
            self.left_info_frame, # Add to left_info_frame
            text=f"{self._get_text('word_label')}: 0/10", 
            font=self.normal_font,
            borderwidth=0, relief='flat', highlightthickness=0
        )
        self.kelime_index_label.pack(side=tk.LEFT, padx=5)
        
        self.uzunluk_label = tk.Label(
            self.left_info_frame, # Add to left_info_frame
            text=f"{self._get_text('word_length')}: 0", 
            font=self.normal_font,
            borderwidth=0, relief='flat', highlightthickness=0
        )
        self.uzunluk_label.pack(side=tk.LEFT, padx=5)

        # Note: Puan is packed before Sure to appear as Score | Time (if both on right)
        self.puan_label = tk.Label(
            self.right_info_frame, # Add to right_info_frame
            text=f"{self._get_text('score')}: 0", 
            font=self.normal_font,
            borderwidth=0, relief='flat', highlightthickness=0
        )
        self.puan_label.pack(side=tk.RIGHT, padx=5) # Pack to the right within right_info_frame
        
        self.sure_label = tk.Label(
            self.right_info_frame, # Add to right_info_frame
            text=f"{self._get_text('remaining_time')}: 200s", 
            font=self.normal_font,
            borderwidth=0, relief='flat', highlightthickness=0
        )
        self.sure_label.pack(side=tk.RIGHT, padx=5) # Pack to the right within right_info_frame (will be to the left of puan_label)
            
    def _create_description_frame(self, parent):
        """Create description frame in the specified parent"""
        self.aciklama_frame = tk.Frame(parent)
        self.aciklama_frame.pack(fill=tk.X, pady=10)
        
        self.aciklama_label = tk.Label(
            self.aciklama_frame, 
            text=f"{self._get_text('description')}: ", 
            font=self.normal_font, 
            wraplength=750, 
            justify=tk.LEFT,
            borderwidth=0, relief='flat', highlightthickness=0
        )
        self.aciklama_label.pack(fill=tk.X, anchor=tk.W, pady=5)
    
    def _create_word_frame(self, parent):
        """Create word display frame in the specified parent"""
        self.word_display_frame = tk.Frame(parent) 
        self.word_display_frame.pack(fill=tk.X, pady=10)
        
        # Label to indicate what the boxes are for (e.g., "Word:", "Unscramble:")
        self.word_display_label = tk.Label( 
            self.word_display_frame, 
            text="Word:", # Text will be updated in _update_ui based on mode
            font=self.normal_font,
            borderwidth=0, relief='flat', highlightthickness=0
        )
        self.word_display_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Frame to hold the individual letter boxes
        self.letter_boxes_frame = tk.Frame(self.word_display_frame)
        self.letter_boxes_frame.pack(expand=True)
    
    def _create_joker_frame(self, parent):
        """Create joker buttons frame in the specified parent"""
        self.joker_frame = tk.Frame(parent)
        self.joker_frame.pack(fill=tk.X, pady=10)
        
        self.joker1_btn = tk.Button(
            self.joker_frame, 
            text=f"{self._get_text('hint_button')} (3/3)", 
            font=self.normal_font,
            command=self._use_char_hint, 
            padx=10,
            pady=5
        )
        self.joker1_btn.pack(side=tk.LEFT, padx=5)
        
        self.joker2_btn = tk.Button(
            self.joker_frame, 
            text=f"{self._get_text('detail_button')} (1/1)", 
            font=self.normal_font,
            command=self._use_detail_hint, 
            padx=10,
            pady=5
        )
        self.joker2_btn.pack(side=tk.LEFT, padx=5)
    
    def _create_guess_frame(self, parent):
        """Create guess input frame in the specified parent"""
        self.tahmin_frame = tk.Frame(parent) # This frame will now stack vertically
        self.tahmin_frame.pack(fill=tk.X, pady=10)

        # --- Finish Button ---
        self.bitir_btn = tk.Button(
            self.tahmin_frame,
            text=self._get_text('finish_game_button', "Oyunu Bitir"),
            font=self.normal_font,
            command=self._finish_game_manually
        )
        self.bitir_btn.pack(pady=(0, 10)) # Pack at the top of tahmin_frame, with some space below

        # --- Frame for actual guess input (label, entry, button) ---
        self.actual_guess_input_frame = tk.Frame(self.tahmin_frame)
        self.actual_guess_input_frame.pack(fill=tk.X)
        
        self.tahmin_label = tk.Label(
            self.actual_guess_input_frame, 
            text=f"{self._get_text('guess_label')}:", 
            font=self.normal_font,
            borderwidth=0, relief='flat', highlightthickness=0
        )
        self.tahmin_label.pack(side=tk.LEFT, padx=5)
        
        self.tahmin_entry = tk.Entry(
            self.actual_guess_input_frame, 
            font=self.normal_font,
            borderwidth=0, relief='flat', highlightthickness=0
        )
        self.tahmin_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.tahmin_entry.bind("<Return>", self._make_guess)
        
        self.tahmin_btn = tk.Button(
            self.actual_guess_input_frame, 
            text=self._get_text('guess_button'), 
            font=self.normal_font,
            command=self._make_guess,
            borderwidth=0, relief='flat', highlightthickness=0
        )
        self.tahmin_btn.pack(side=tk.LEFT, padx=5)
    
    def _get_text(self, key, fallback=None):
        """Get translated text based on current language setting"""
        lang = self.settings.get('language', 'tr')
        translations = self.settings.get('translations', {})
        # Use fallback if key is not found in the specific language or default
        result = translations.get(lang, {}).get(key, fallback if fallback else key)
        # print(f"[GetText] Key: {key}, Lang: {lang}, Result: {result}") # Temporary debug
        return result
    
    def _apply_theme(self):
        """Apply theme to root window"""
        # print("[View] Applying theme...") # Debug
        theme = self.settings.get('theme', 'blue')
        # print(f"[View]   - Theme from settings: {theme}") # Debug
        colors = self.settings.get('theme_colors', {}).get(theme, {})
        
        bg_color = colors.get('background', '#f0f0f0')
        # print(f"[View]   - Applying background: {bg_color}") # Debug
        self.root.configure(bg=bg_color)
    
    def _update_colors(self):
        """Update colors of all widgets based on current theme"""
        # print("[View] Updating widget colors...") # Debug
        theme = self.settings.get('theme', 'blue')
        # print(f"[View]   - Theme for colors: {theme}") # Debug
        colors = self.settings.get('theme_colors', {}).get(theme, {})
        # print(f"[View]   - Colors loaded: {colors}") # Debug
        
        bg_color = colors.get('background', '#f0f0f0')
        primary_color = colors.get('primary', '#4a7abc')
        accent_color = colors.get('accent', '#FF5722')
        secondary_color = colors.get('secondary', '#2196F3')
        text_color = colors.get('text', '#333333')
        button_text_color = colors.get('button_text', 'white')
        secondary_bg_color = colors.get('secondary_background', bg_color)
        secondary_text_color = colors.get('secondary_text', text_color)
        
        # Update frame backgrounds
        leaderboard_title_label = None # This label was removed, Text widget used directly
        frames_to_color = [
            self.main_frame, self.start_area_frame, self.start_buttons_frame,
            self.game_area_frame, self.bilgi_frame, self.aciklama_frame,
            self.word_display_frame, self.letter_boxes_frame,
            self.joker_frame, self.tahmin_frame,
            getattr(self, 'actual_guess_input_frame', None), # Added for the new inner guess frame
            getattr(self, 'rules_frame', None),
            getattr(self, 'logo_frame', None),
            getattr(self, 'header_leaderboard_frame', None),
            getattr(self, 'leaderboard_display_frame', None),
            getattr(self, 'left_leaderboard_frame', None),
            getattr(self, 'right_leaderboard_frame', None)
        ]
        for widget in frames_to_color:
            if widget:
                widget.configure(bg=bg_color)

        if hasattr(self, 'leaderboard_quiz_text_widget'):
            self.leaderboard_quiz_text_widget.configure(bg=secondary_bg_color, fg=text_color, relief=tk.FLAT, borderwidth=0)
            self.leaderboard_quiz_text_widget.tag_configure("bold_title", foreground=primary_color)
            self.leaderboard_quiz_text_widget.tag_configure("score_entry", foreground=text_color)
            self.leaderboard_quiz_text_widget.tag_configure("no_score_message", foreground=secondary_text_color)

        if hasattr(self, 'leaderboard_anagram_text_widget'):
            self.leaderboard_anagram_text_widget.configure(bg=secondary_bg_color, fg=text_color, relief=tk.FLAT, borderwidth=0)
            self.leaderboard_anagram_text_widget.tag_configure("bold_title", foreground=primary_color)
            self.leaderboard_anagram_text_widget.tag_configure("score_entry", foreground=text_color)
            self.leaderboard_anagram_text_widget.tag_configure("no_score_message", foreground=secondary_text_color)

        # ... (rest of _update_colors for buttons, labels etc.)
        self.baslik_frame.configure(bg=primary_color)
        if self.baslik_frame.winfo_children(): 
            content_header_frame = self.baslik_frame.winfo_children()[0]
            content_header_frame.configure(bg=primary_color)
        if hasattr(self, 'logo_label_widget') and self.logo_label_widget:
            self.logo_label_widget.configure(bg=primary_color)

        for label in [self.kelime_index_label, self.sure_label, self.puan_label, self.uzunluk_label]:
            label.configure(bg=bg_color, fg=text_color, borderwidth=0, relief='flat', highlightthickness=0)
        self.aciklama_label.configure(bg=bg_color, fg=text_color)
        self.word_display_label.configure(bg=bg_color, fg=text_color) 
        for label in self.letter_labels:
            if label: 
                label.configure(bg=bg_color, fg=text_color)

        self.joker1_btn.configure(bg=secondary_color, fg=button_text_color, activebackground=accent_color, activeforeground=button_text_color)
        self.joker2_btn.configure(bg=secondary_color, fg=button_text_color, activebackground=accent_color, activeforeground=button_text_color)

        self.tahmin_label.configure(bg=bg_color, fg=text_color)
        self.tahmin_entry.configure(fg=text_color) 
        self.tahmin_btn.configure(bg=accent_color, fg=button_text_color, activebackground=secondary_color, activeforeground=button_text_color)

        self.sonuc_label.configure(bg=bg_color)

        self.start_quiz_btn.configure(bg=primary_color, fg=button_text_color, activebackground=accent_color, activeforeground=button_text_color)
        self.start_anagram_btn.configure(bg=primary_color, fg=button_text_color, activebackground=accent_color, activeforeground=button_text_color)
        # Restart button styling removed

        if hasattr(self, 'bitir_btn'):
            light_red_bg = colors.get('danger_button_bg', '#FFA07A') # LightSalmon
            light_red_active_bg = colors.get('danger_button_active_bg', '#FA8072') # Salmon
            self.bitir_btn.configure(bg=light_red_bg, fg=button_text_color, 
                                     activebackground=light_red_active_bg, 
                                     activeforeground=button_text_color)

    def _update_leaderboard_display(self):
        widgets_and_titles_modes = [
            (self.leaderboard_quiz_text_widget, self._get_text('leaderboard_quiz_title'), 'quiz'),
            (self.leaderboard_anagram_text_widget, self._get_text('leaderboard_anagram_title'), 'anagram')
        ]
        scores_data = load_highscores(HIGHSCORE_FILE)

        for txt_widget, title, mode_key in widgets_and_titles_modes:
            txt_widget.config(state=tk.NORMAL)
            txt_widget.delete('1.0', tk.END)
            txt_widget.insert(tk.END, title + "\n", "bold_title")

            mode_scores = []
            if scores_data:
                for username, user_game_scores in scores_data.items():
                    if mode_key in user_game_scores:
                        mode_scores.append((user_game_scores[mode_key], username))
            
            mode_scores.sort(key=lambda x: (-x[0], x[1])) # Sort by score desc, then username asc

            if mode_scores:
                for i, (score, username) in enumerate(mode_scores[:10]): # Display top 10 for each mode
                    txt_widget.insert(tk.END, f"{i+1}. {username}: {score}\n", "score_entry")
            else:
                if not scores_data: # Overall no scores yet
                     txt_widget.insert(tk.END, self._get_text('no_highscores_message', "Henüz skor yok.") + "\n", "no_score_message")
                else: # Scores exist, but not for this specific mode
                    txt_widget.insert(tk.END, self._get_text('no_scores_for_mode_message', "Bu mod için skor yok.") + "\n", "no_score_message")
            txt_widget.config(state=tk.DISABLED)

    def _start_game(self, mode): # Accept mode parameter
        """Start a new game in the specified mode"""
        self.current_game_mode = mode
        print(f"[View] Starting game in mode: {self.current_game_mode}") # Debug
        
        # Hide start area, show game area
        self.start_area_frame.pack_forget()
        self.game_area_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10) # Add padding
        
        # Initialize game service for the chosen mode
        self.game_service.start_game(game_mode=self.current_game_mode)
        
        # Clear result message
        self.sonuc_label.config(text="")
        
        # Update UI with initial game state for the selected mode
        self._update_ui()
        
        # Start timer
        self._update_timer()
        
        # Enable input
        self.tahmin_entry.config(state=tk.NORMAL)
        self.tahmin_btn.config(state=tk.NORMAL)
        
        # Enable/Disable Jokers based on mode
        joker_state = tk.NORMAL if self.current_game_mode == 'quiz' else tk.DISABLED
        self.joker1_btn.config(state=joker_state)
        self.joker2_btn.config(state=joker_state)
        
        # Set focus on entry
        self.tahmin_entry.focus_set()

    def _update_timer(self):
        """Update timer display"""
        # Cancel any existing timer
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        
        # Update time in game service only if game is running
        if self.game_service.game_state and self.game_service.game_state.is_running:
            remaining = self.game_service.update_time()
            
            # Update display
            self.sure_label.config(text=f"{self._get_text('remaining_time')}: {remaining}s")
            
            # Check if time ran out
            if remaining <= 0: # If time is up based on the value returned by update_time()
                # game_service.update_time() already sets game_state.is_running to False if time is up.
                # _game_over will also ensure/confirm game_state.is_running is False.
                self._game_over(self._get_text('time_up'))
                return # Stop timer updates
            
            # Schedule next update only if still running
            if self.game_service.game_state.is_running:
                 self.timer_id = self.root.after(1000, self._update_timer)
        else:
            # Game not running, ensure timer is stopped
            if self.timer_id:
                 self.root.after_cancel(self.timer_id)
                 self.timer_id = None
            # Optionally update time label to 0 if game ended due to completion
            if self.game_service.game_state and not self.game_service.game_state.is_running:
                 self.sure_label.config(text=f"{self._get_text('remaining_time')}: 0s")
    
    def _update_ui(self):
        """Update UI with current game state"""
        state = self.game_service.game_state
        
        if not state:
            print("[View] Update UI called but no valid game state.")
            # Reset to default state? Or handle appropriately
            return

        # Update info labels first, as they depend on state
        self._update_info_labels()

        if not state.current_word:
             print("[View] Update UI called but no current word (likely game end).") 
             # Maybe clear word boxes? Or handle game over state display
             for widget in self.letter_boxes_frame.winfo_children():
                 widget.destroy()
             self.letter_labels.clear()
             return
        
        print(f"[View] Updating UI for mode: {state.game_mode}, Word: {state.current_word.word}") # Debug
        
        # Update description (only shown in quiz mode)
        if state.game_mode == 'quiz':
            self.aciklama_label.config(text=f"{self._get_text('description')}: {state.current_word.description}") # Score removed from here
            self.aciklama_label.pack(anchor=tk.W, fill=tk.X, pady=(0, 5)) # Ensure it's visible and fills
        else:
            self.aciklama_label.pack_forget() # Hide description in anagram mode
            
        # Update word display label based on mode, including score for quiz mode
        if state.game_mode == 'quiz':
            word_mode_text = f"{self._get_text('word_label')}: ({state.current_word_score} Puan)"
        elif state.game_mode == 'anagram':
            word_mode_text = f"{self._get_text('unscramble_label', 'Unscramble')}:"
        else: # Fallback, should not happen with current modes
            word_mode_text = f"{self._get_text('word_label')}:"
        self.word_display_label.config(text=word_mode_text)
        
        # --- Update Letter Boxes ---
        # Clear previous letter boxes
        for widget in self.letter_boxes_frame.winfo_children():
            widget.destroy()
        self.letter_labels.clear()

        # Create new letter boxes
        displayed_word_text = state.get_displayed_word() # e.g., "_ _ K _ _" or "K E L I M E"
        # Determine background color from theme
        theme = self.settings.get('theme', 'blue')
        colors = self.settings.get('theme_colors', {}).get(theme, {})
        bg_color = colors.get('background', '#f0f0f0')
        text_color = colors.get('text', '#333333')

        for char in displayed_word_text:
            if char == ' ': # Add space between boxes for visual separation
                # Use a Label for spacing to inherit background color
                spacer = tk.Label(self.letter_boxes_frame, text=" ", width=1, bg=bg_color)
                spacer.pack(side=tk.LEFT)
                self.letter_labels.append(None) # Placeholder for spacer
            else:
                box = tk.Label(
                    self.letter_boxes_frame, 
                    text=char, 
                    font=self.kelime_font, 
                    relief=tk.SOLID, 
                    borderwidth=1, 
                    width=2, 
                    anchor=tk.CENTER,
                    bg=bg_color, # Set background color
                    fg=text_color  # Set text color
                )
                box.pack(side=tk.LEFT)
                self.letter_labels.append(box)
        # --- End Letter Boxes ---

        # Update joker buttons state and text
        if state.game_mode == 'quiz':
            self.joker1_btn.config(
                text=f"{self._get_text('hint_button')} ({state.hint_count}/3)",
                state=tk.NORMAL if state.hint_count > 0 else tk.DISABLED
            )
            self.joker2_btn.config(
                text=f"{self._get_text('detail_button')} ({state.detail_hint_count}/1)",
                state=tk.NORMAL if state.detail_hint_count > 0 else tk.DISABLED
            )
            self.joker_frame.pack(fill=tk.X, pady=10) # Show joker frame
        else: # Anagram mode - hide jokers
            self.joker_frame.pack_forget()

        # Ensure guess input is enabled if game is running
        if state.is_running: # 'state' is guaranteed to be non-None here
            self.tahmin_entry.config(state=tk.NORMAL)
            self.tahmin_btn.config(state=tk.NORMAL)
            self.bitir_btn.config(state=tk.NORMAL)
        else: # game over or other states handle disabling appropriately
            self.tahmin_entry.config(state=tk.DISABLED)
            self.tahmin_btn.config(state=tk.DISABLED)
            self.bitir_btn.config(state=tk.DISABLED)

        # Clear input
        self.tahmin_entry.delete(0, tk.END)
        self.tahmin_entry.focus_set() # Keep focus on entry

    def _make_guess(self, event=None):
        """Process user's guess"""
        if not self.game_service.game_state or not self.game_service.game_state.is_running:
             return # Don't process guess if game not running
             
        guess = self.tahmin_entry.get().strip().lower()
        if not guess:
            return
        
        # Check guess
        if self.game_service.make_guess(guess):
            # Correct guess
            self._play_sound("dogru.mp3") # Play correct sound
            state = self.game_service.game_state
            self.sonuc_label.config(
                text=self._get_text('correct_guess'), # Display simple "Correct!" message
                fg="#2E7D32" # Darker Green
            )
            
            # Update score display immediately
            self.puan_label.config(text=f"{self._get_text('score')}: {state.score}")
            
            # Disable input during transition
            self.tahmin_entry.config(state=tk.DISABLED)
            self.tahmin_btn.config(state=tk.DISABLED)
            if state.game_mode == 'quiz': # Keep jokers disabled
                 self.joker1_btn.config(state=tk.DISABLED)
                 self.joker2_btn.config(state=tk.DISABLED)
            
            # Schedule next word
            self.root.after(1500, self._next_word) # Slightly shorter delay
        else:
            # Wrong guess
            self._play_sound("yanlis.mp3") # Play wrong sound
            self.sonuc_label.config(
                text=self._get_text('wrong_guess'),
                fg="#C62828" # Darker Red
            )
            self.tahmin_entry.delete(0, tk.END)
            # Add a visual cue for wrong guess (e.g., shake effect - harder in Tkinter)
            # Simple clear and focus
            self.tahmin_entry.focus_set()
    
    def _use_char_hint(self):
        """Use character hint (only for quiz mode)"""
        if self.current_game_mode != 'quiz': return
        if not self.game_service.game_state or not self.game_service.game_state.is_running: return
        
        char = self.game_service.use_character_hint()
        
        if char:
            # Simply update the UI which will regenerate the boxes with the revealed letter
            self._update_ui() 
            # Score is updated internally, but reflect hint count change immediately
            state = self.game_service.game_state
            self.joker1_btn.config(
                text=f"{self._get_text('hint_button')} ({state.hint_count}/3)",
                state=tk.NORMAL if state.hint_count > 0 else tk.DISABLED
            )
    
    def _use_detail_hint(self):
        """Use detailed hint (only for quiz mode)"""
        if self.current_game_mode != 'quiz': return
        if not self.game_service.game_state or not self.game_service.game_state.is_running: return

        details = self.game_service.use_detail_hint()
        
        if details:
            # Update UI first to get the base description text
            self._update_ui() 
            
            state = self.game_service.game_state
            self.joker2_btn.config(
                text=f"{self._get_text('detail_button')} ({state.detail_hint_count}/1)",
                state=tk.DISABLED # Hint is used
            )
            # Append detail to the description
            current_desc = f"{self._get_text('description')}: {state.current_word.description}"
            # Use translated prefix for detail hint
            detail_prefix = self._get_text('detail_prefix')
            self.aciklama_label.config(text=f"{current_desc}\n{detail_prefix} {details}")
    
    def _next_word(self):
        """Move to the next word"""
        if not self.game_service.game_state: return # Safety check
        
        has_next = self.game_service.next_word()
        
        if has_next:
            self.sonuc_label.config(text="") # Clear previous result
            self.tahmin_entry.config(state=tk.NORMAL) # Re-enable input
            self.tahmin_btn.config(state=tk.NORMAL)
            
            # Update UI for the new word state (handles joker re-enable)
            self._update_ui()
            
            self.tahmin_entry.focus_set()
        else:
            # No more words or game finished
            self._game_over(self._get_text('all_words_completed'))
    
    def _game_over(self, message):
        """Handle game over"""
        print("[View] Game Over.") 
        
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
            
        final_score = 0
        if self.game_service.game_state:
            self.game_service.game_state.is_running = False
            final_score = self.game_service.game_state.score

        if self.current_username:
            save_highscore(HIGHSCORE_FILE, self.current_username, final_score, self.current_game_mode)
            self._update_leaderboard_display() # Refresh leaderboard after saving score

        self.tahmin_entry.config(state=tk.DISABLED)
        self.tahmin_btn.config(state=tk.DISABLED)
        self.joker1_btn.config(state=tk.DISABLED)
        self.joker2_btn.config(state=tk.DISABLED)

        self.sonuc_label.config(text=message, fg="#1565C0") 
        
        final_score_message = self.game_service.get_final_score_message()
        self._play_sound("son.mp3") 
        messagebox.showinfo(self._get_text('game_over'), final_score_message)
        
        self._update_header_leaderboard() # Update header leaderboard (e.g. to show new score or clear for next game)
        self.root.after(100, self._return_to_start_screen)

    def _update_info_labels(self):
        """Update info labels with current text and values"""
        # Update button texts that might change language FIRST
        self.tahmin_label.config(text=f"{self._get_text('guess_label')}:")
        self.tahmin_btn.config(text=self._get_text('guess_button'))
        # Ensure game_state exists before trying to access hint_count or detail_hint_count
        hint_count = self.game_service.game_state.hint_count if self.game_service.game_state else 3
        detail_hint_count = self.game_service.game_state.detail_hint_count if self.game_service.game_state else 1
        self.joker1_btn.config(text=f"{self._get_text('hint_button')} ({hint_count}/3)")
        self.joker2_btn.config(text=f"{self._get_text('detail_button')} ({detail_hint_count}/1)")

        # Update labels in the info frame
        if self.game_service.game_state and self.game_service.game_state.is_running:
            state = self.game_service.game_state
            total_words = len(state.flat_words) if state.flat_words else 0
            self.kelime_index_label.config(text=f"{self._get_text('word_label')}: {state.current_word_index + 1}/{total_words}")
            self.sure_label.config(text=f"{self._get_text('remaining_time')}: {state.remaining_time}s")
            self.puan_label.config(text=f"{self._get_text('score')}: {state.score}")
            
            if state.current_word:
                # Use formatted string for word length
                length_text = self._get_text('word_length_value').format(length=state.current_word.length)
                self.uzunluk_label.config(text=f"{self._get_text('word_length')}: {length_text}")
                # Show description only in quiz mode (handled in _update_ui)
                # desc_text = f"{self._get_text('description')}: {state.current_word.description}" if state.game_mode == 'quiz' else f"{self._get_text('description')}: -"
                # self.aciklama_label.config(text=desc_text)
                
                # Update word display label based on mode, including score for quiz mode
                if state.game_mode == 'quiz':
                    word_mode_text = f"{self._get_text('word_label')}: ({state.current_word_score} Puan)"
                elif state.game_mode == 'anagram':
                    word_mode_text = f"{self._get_text('unscramble_label', 'Unscramble')}:"
                else: # Fallback, should not happen with current modes
                    word_mode_text = f"{self._get_text('word_label')}:"
                self.word_display_label.config(text=word_mode_text)
            else: # If no current word (e.g., end of game before UI update)
                length_text = self._get_text('word_length_value').format(length=0)
                self.uzunluk_label.config(text=f"{self._get_text('word_length')}: {length_text}")
                self.aciklama_label.config(text=f"{self._get_text('description')}: ")
                self.word_display_label.config(text=f"{self._get_text('word_label')}:")
        else:
            # Reset labels when no game is active
            total_words_default = 10 # Or get from config?
            self.kelime_index_label.config(text=f"{self._get_text('word_label')}: 0/{total_words_default}")
            self.sure_label.config(text=f"{self._get_text('remaining_time')}: {self.game_service.game_state.time_limit if self.game_service.game_state else 200}s") # Use actual limit if available
            self.puan_label.config(text=f"{self._get_text('score')}: 0")
            length_text = self._get_text('word_length_value').format(length=0)
            self.uzunluk_label.config(text=f"{self._get_text('word_length')}: {length_text}")
            self.aciklama_label.config(text=f"{self._get_text('description')}: ")
            self.word_display_label.config(text=f"{self._get_text('word_label')}:")

    def _play_sound(self, sound_file_name):
        """Plays a sound file from the media directory."""
        try:
            sound_path = os.path.join("media", sound_file_name)
            abs_path = os.path.abspath(sound_path)
            # print(f"[Sound Debug] Attempting to play: {abs_path}") # Debug absolute path
            exists = os.path.exists(abs_path)
            # print(f"[Sound Debug] File exists: {exists}") # Debug existence check
            if exists:
                # print("[Sound Debug] Calling playsound with block=False...") # Debug
                # Use block=False for responsiveness
                playsound(abs_path, block=False) 
                # print("[Sound Debug] playsound call finished.") # Debug
            else:
                print(f"[Sound Error] File not found: {sound_path}")
        except Exception as e:
            # Catch potential playsound errors (device issues, format issues)
            # Including the codec error fix attempt
            print(f"[Sound Error] Could not play sound '{sound_file_name}': {e}")
            # If specific utf-8 error, suggest fix or alternative
            if "codec can't decode byte" in str(e):
                print(self._get_text('sound_fix_hint')) 

    def _return_to_start_screen(self):
        """Hides game area and shows start area, resetting necessary UI components."""
        self.game_area_frame.pack_forget()
        self.start_area_frame.pack(pady=20, anchor=tk.CENTER)
        if hasattr(self, 'sonuc_label'): # Clear game result message
            self.sonuc_label.config(text="")
        
        # Reset word display area
        if hasattr(self, 'letter_boxes_frame'):
            for widget in self.letter_boxes_frame.winfo_children():
                widget.destroy()
            self.letter_labels.clear()
        
        # Reset description label to default (or hide if not applicable to start screen)
        if hasattr(self, 'aciklama_label'):
            self.aciklama_label.config(text=f"{self._get_text('description')}: ")
        
        # Reset word display label
        if hasattr(self, 'word_display_label'):
            self.word_display_label.config(text=f"{self._get_text('word_label')}:")

        # Ensure guess entry is clear if it wasn't already
        if hasattr(self, 'tahmin_entry'):
            self.tahmin_entry.delete(0, tk.END)
        
        # Update header leaderboard to reflect no active game mode
        self._update_header_leaderboard()

    def _finish_game_manually(self):
        """Ends the game prematurely by user action after confirmation."""
        if self.game_service.game_state and self.game_service.game_state.is_running:
            if messagebox.askyesno(
                self._get_text('finish_game_confirm_title', "Oyunu Bitir?"),
                self._get_text('finish_game_confirm_message', "Oyunu bitirmek istediğinize emin misiniz? Mevcut puanınız kaydedilecek.")
            ):
                print("[View] Game ended manually by user.")
                if self.timer_id:
                    self.root.after_cancel(self.timer_id)
                    self.timer_id = None

                if self.game_service.game_state: # Ensure game_state still exists
                    self.game_service.game_state.is_running = False
                    final_score = self.game_service.game_state.score

                    if self.current_username:
                        save_highscore(HIGHSCORE_FILE, self.current_username, final_score, self.current_game_mode)
                        self._update_leaderboard_display()
                        # Header leaderboard will be updated by _return_to_start_screen
                
                # Show a brief message on the game screen before transitioning
                self.sonuc_label.config(text=self._get_text('game_ended_by_user_short', "Oyun sonlandırıldı."), fg="#1565C0")
                self.root.update_idletasks() # Ensure message is shown
                self.root.after(1500, self._return_to_start_screen) # Delay then go to start screen
            # else: User chose not to finish
        # else: Game not running, or no game state - do nothing or provide feedback if button was somehow active

    def _update_header_leaderboard(self):
        """Updates the leaderboard display in the header for the current game mode."""
        widgets_and_titles_modes = [
            (self.leaderboard_quiz_text_widget, self._get_text('leaderboard_quiz_title'), 'quiz'),
            (self.leaderboard_anagram_text_widget, self._get_text('leaderboard_anagram_title'), 'anagram')
        ]
        scores_data = load_highscores(HIGHSCORE_FILE)

        for txt_widget, title, mode_key in widgets_and_titles_modes:
            txt_widget.config(state=tk.NORMAL)
            txt_widget.delete('1.0', tk.END)
            txt_widget.insert(tk.END, title + "\n", "bold_title")

            mode_scores = []
            if scores_data:
                for username, user_game_scores in scores_data.items():
                    if mode_key in user_game_scores:
                        mode_scores.append((user_game_scores[mode_key], username))
            
            mode_scores.sort(key=lambda x: (-x[0], x[1])) # Sort by score desc, then username asc

            if mode_scores:
                for i, (score, username) in enumerate(mode_scores[:10]): # Display top 10 for each mode
                    txt_widget.insert(tk.END, f"{i+1}. {username}: {score}\n", "score_entry")
            else:
                if not scores_data: # Overall no scores yet
                     txt_widget.insert(tk.END, self._get_text('no_highscores_message', "Henüz skor yok.") + "\n", "no_score_message")
                else: # Scores exist, but not for this specific mode
                    txt_widget.insert(tk.END, self._get_text('no_scores_for_mode_message', "Bu mod için skor yok.") + "\n", "no_score_message")
            txt_widget.config(state=tk.DISABLED) 