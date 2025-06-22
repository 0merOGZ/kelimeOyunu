import os
import json
from pathlib import Path

DEFAULT_SETTINGS = {
    'language': 'tr',  # 'tr' for Turkish, 'en' for English
    'theme': 'blue',   # 'blue', 'dark', 'light', 'green'
    'theme_colors': {
        'blue': {
            'primary': '#654321',
            'secondary': '#8B4513',
            'accent': '#FF5722',
            'background': '#F5DEB3',
            'text': '#000000',
            'button_text': 'white'
        },
        'dark': {
            'primary': '#333333',
            'secondary': '#555555',
            'accent': '#FF5722',
            'background': '#F5DEB3',
            'text': '#000000',
            'button_text': 'white'
        },
        'light': {
            'primary': '#A0A0A0',
            'secondary': '#D3D3D3',
            'accent': '#2196F3',
            'background': '#F5DEB3',
            'text': '#000000',
            'button_text': 'white'
        },
        'green': {
            'primary': '#4CAF50',
            'secondary': '#388E3C',
            'accent': '#FF9800',
            'background': '#F5DEB3',
            'text': '#000000',
            'button_text': 'white'
        }
    },
    'translations': {
        'tr': {
            'app_title': 'Kelime Avı',
            'start_button': 'OYUNU BAŞLAT',
            'restart_button': 'YENİDEN BAŞLAT',
            'word_label': 'Kelime',
            'remaining_time': 'Kalan Süre',
            'score': 'Puan',
            'word_length': 'Kelime Uzunluğu',
            'description': 'Açıklama',
            'hint_button': 'Harf Al',
            'detail_button': 'Detay Aç',
            'guess_label': 'Tahmininiz',
            'guess_button': 'Tahmin Et',
            'correct_guess': 'TEBRİKLER! Doğru Tahmin',
            'wrong_guess': 'Yanlış tahmin! Tekrar deneyin.',
            'time_up': 'ZAMAN DOLDU!',
            'all_words_completed': 'TÜM KELİMELER TAMAMLANDI!',
            'game_over': 'OYUN SONU - TOPLAM PUAN',
            'settings': 'Ayarlar',
            'language': 'Dil',
            'theme': 'Tema',
            'save': 'Kaydet',
            'cancel': 'İptal',
            'turkish': 'Türkçe',
            'english': 'İngilizce',
            'blue_theme': 'Mavi',
            'dark_theme': 'Koyu',
            'light_theme': 'Açık',
            'green_theme': 'Yeşil',
            'preview': 'Önizleme',
            'start_button_quiz': 'Klasik Mod Başlat',
            'start_button_anagram': 'Anagram Mod Başlat',
            'unscramble_label': 'Harfleri Diz',
            'exit_label': 'Çıkış',
            'settings_apply_note': 'Not: Değişiklikler kaydedildiğinde hemen uygulanacaktır.',
            'settings_saved_success': 'Ayarlar kaydedildi ve uygulandı!',
            'settings_saved_error': 'Ayarlar kaydedilemedi!',
            'settings_applied_success': 'Ayarlarınız başarıyla uygulandı!',
            'word_length_value': '{length} Harf',
            'detail_prefix': '[Detay]',
            'final_score_base': 'OYUN SONU - TOPLAM PUAN: {score}',
            'score_praise_5': '★★★★★ MÜKEMMEL! Harika bir skor!',
            'score_praise_4': '★★★★☆ ÇOK İYİ! Biraz daha çalışmalısın.',
            'score_praise_3': '★★★☆☆ İYİ! Orta seviye skor.',
            'score_praise_2': '★★☆☆☆ DAHA İYİSİNİ YAPABİLİRSİN!',
            'sound_fix_hint': "[İpucu] Ses dosyalarını WAV formatına dönüştürmeyi veya özel karakter içermeyen dosya adları kullanmayı deneyin.",
            'username_prompt_title': 'Kullanıcı Adı',
            'username_prompt_message': 'Lütfen kullanıcı adınızı girin:',
            'leaderboard_button': 'Skor Tablosu',
            'leaderboard_title': '🏆 SKOR TABLOSU 🏆',
            'leaderboard_quiz_title': 'Klasik Mod Skorları',
            'leaderboard_anagram_title': 'Anagram Mod Skorları',
            'no_highscores_message': 'Henüz kaydedilmiş skor bulunmamaktadır.',
            'no_scores_for_mode_message': 'Bu mod için skor yok.',
            'quiz_mode_label': 'Klasik',
            'anagram_mode_label': 'Anagram',
            'ok_button': 'Tamam',
            'cancel_button': 'İptal',
            'username_error_title': 'Geçersiz Giriş',
            'username_empty_error': 'Kullanıcı adı boş olamaz!'
        },
        'en': {
            'app_title': 'Word Hunt',
            'start_button': 'START GAME',
            'restart_button': 'RESTART',
            'word_label': 'Word',
            'remaining_time': 'Time Left',
            'score': 'Score',
            'word_length': 'Word Length',
            'description': 'Description',
            'hint_button': 'Get Letter',
            'detail_button': 'Show Detail',
            'guess_label': 'Your Guess',
            'guess_button': 'Guess',
            'correct_guess': 'CONGRATULATIONS! Correct Guess',
            'wrong_guess': 'Wrong guess! Try again.',
            'time_up': 'TIME\'S UP!',
            'all_words_completed': 'ALL WORDS COMPLETED!',
            'game_over': 'GAME OVER - TOTAL SCORE',
            'settings': 'Settings',
            'language': 'Language',
            'theme': 'Theme',
            'save': 'Save',
            'cancel': 'Cancel',
            'turkish': 'Turkish',
            'english': 'English',
            'blue_theme': 'Blue',
            'dark_theme': 'Dark',
            'light_theme': 'Light',
            'green_theme': 'Green',
            'preview': 'Preview',
            'start_button_quiz': 'Start Quiz Mode',
            'start_button_anagram': 'Start Anagram Mode',
            'unscramble_label': 'Unscramble',
            'exit_label': 'Exit',
            'settings_apply_note': 'Note: Changes will be applied immediately upon saving.',
            'settings_saved_success': 'Settings saved and applied!',
            'settings_saved_error': 'Could not save settings!',
            'settings_applied_success': 'Your settings have been applied successfully!',
            'word_length_value': '{length} Letters',
            'detail_prefix': '[Detail]',
            'final_score_base': 'GAME OVER - TOTAL SCORE: {score}',
            'score_praise_5': '★★★★★ EXCELLENT! Great score!',
            'score_praise_4': '★★★★☆ VERY GOOD! Keep practicing.',
            'score_praise_3': '★★★☆☆ GOOD! Average score.',
            'score_praise_2': '★★☆☆☆ YOU CAN DO BETTER!',
            'sound_fix_hint': "[Hint] Try converting sound files to WAV format or using filenames without special characters.",
            'username_prompt_title': 'Username',
            'username_prompt_message': 'Please enter your username:',
            'leaderboard_button': 'Leaderboard',
            'leaderboard_title': '🏆 LEADERBOARD 🏆',
            'leaderboard_quiz_title': 'Quiz Mode Scores',
            'leaderboard_anagram_title': 'Anagram Mode Scores',
            'no_highscores_message': 'No high scores recorded yet.',
            'no_scores_for_mode_message': 'No scores for this mode.',
            'quiz_mode_label': 'Quiz',
            'anagram_mode_label': 'Anagram',
            'ok_button': 'OK',
            'cancel_button': 'Cancel',
            'username_error_title': 'Invalid Input',
            'username_empty_error': 'Username cannot be empty!'
        }
    }
}

def get_settings_file_path():
    """Get the path to the settings file"""
    # Use Path to handle cross-platform path creation
    app_dir = Path(os.path.expanduser("~")) / ".kelime_oyunu"
    
    # Create directory if it doesn't exist
    try:
        os.makedirs(str(app_dir), exist_ok=True)
        print(f"[Settings] Directory created/verified: {app_dir}")
    except Exception as e:
        print(f"[Settings] Error creating directory: {e}")
    
    settings_path = app_dir / "settings.json"
    print(f"[Settings] Path: {settings_path}") # Debug
    return settings_path

def load_settings():
    """Load settings from file or return defaults"""
    settings_file = get_settings_file_path()
    print(f"[Settings] Attempting to load from: {settings_file}") # Debug
    
    if settings_file.exists():
        try:
            with open(str(settings_file), 'r', encoding='utf-8') as f:
                user_settings = json.load(f)
                # print(f"[Settings] Loaded settings from file: {user_settings}") # Debug
                
            # Merge with default settings in case of missing keys
            merged_settings = DEFAULT_SETTINGS.copy()
            # Deep merge dictionaries (theme_colors, translations)
            for key, value in user_settings.items():
                if isinstance(value, dict) and key in merged_settings and isinstance(merged_settings[key], dict):
                     merged_settings[key].update(value)
                else:
                     merged_settings[key] = value

            # Ensure all essential keys exist after merge
            if 'theme_colors' not in merged_settings:
                 merged_settings['theme_colors'] = DEFAULT_SETTINGS['theme_colors']
            if 'translations' not in merged_settings:
                 merged_settings['translations'] = DEFAULT_SETTINGS['translations']

            # print(f"[Settings] Merged settings: {merged_settings}") # Debug
            return merged_settings
        except Exception as e:
            print(f"[Settings] Error loading settings: {e}. Using defaults.") # Debug
            import traceback
            print(f"[Settings] Error details: {traceback.format_exc()}")
    else:
        print("[Settings] Settings file not found. Using defaults.") # Debug
    
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Save settings to file"""
    settings_file = get_settings_file_path()
    print(f"[Settings] Attempting to save to: {settings_file}") # Debug
    print(f"[Settings] Settings to save: {settings}") # Debug
    
    try:
        # Only save language and theme preference, not entire structure
        settings_to_save = {
            'language': settings.get('language', DEFAULT_SETTINGS['language']),
            'theme': settings.get('theme', DEFAULT_SETTINGS['theme'])
        }
        
        # Convert to string path to avoid any potential issues
        with open(str(settings_file), 'w', encoding='utf-8') as f:
            json.dump(settings_to_save, f, ensure_ascii=False, indent=4)
        print("[Settings] Settings saved successfully.") # Debug
        return True
    except Exception as e:
        print(f"[Settings] Error saving settings: {e}") # Debug
        # Try to get more detailed error information
        import traceback
        print(f"[Settings] Error details: {traceback.format_exc()}")
        return False 