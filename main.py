import tkinter as tk
# Updated imports for the new flat structure hello world exampleeee
from config import load_settings
from repository import WordRepository
from game import GameService, KelimeOyunuView, Word # Import Word here for repository

def main():

    settings = load_settings()
    

    root = tk.Tk()

    repository = WordRepository(server='localhost', database='kelimeOyunu') 
    game_service = GameService(repository)
    

    

    app = KelimeOyunuView(root, game_service, settings)
    

    root.mainloop()

if __name__ == "__main__":
    main() 