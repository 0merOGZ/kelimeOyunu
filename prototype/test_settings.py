import os
import json
from pathlib import Path

def test_settings_file():
    # Get home directory path
    home_dir = Path(os.path.expanduser("~"))
    print(f"Home directory: {home_dir}")
    
    # Create app directory path
    app_dir = home_dir / ".kelime_oyunu"
    print(f"App directory: {app_dir}")
    
    # Create directory if doesn't exist
    try:
        os.makedirs(str(app_dir), exist_ok=True)
        print(f"Directory created/verified: {app_dir}")
        print(f"Directory exists: {os.path.exists(str(app_dir))}")
    except Exception as e:
        print(f"Error creating directory: {e}")
        return
    
    # Create settings file path
    settings_file = app_dir / "settings.json"
    print(f"Settings file path: {settings_file}")
    
    # Try to write to settings file
    test_settings = {
        'language': 'tr',
        'theme': 'blue'
    }
    
    try:
        with open(str(settings_file), 'w', encoding='utf-8') as f:
            json.dump(test_settings, f, ensure_ascii=False, indent=4)
        print(f"Settings successfully written to {settings_file}")
    except Exception as e:
        print(f"Error writing settings: {e}")
        import traceback
        print(f"Error details: {traceback.format_exc()}")
        return
    
    # Try to read the settings file
    try:
        with open(str(settings_file), 'r', encoding='utf-8') as f:
            read_settings = json.load(f)
        print(f"Settings successfully read from file: {read_settings}")
    except Exception as e:
        print(f"Error reading settings: {e}")
        import traceback
        print(f"Error details: {traceback.format_exc()}")

if __name__ == "__main__":
    test_settings_file() 