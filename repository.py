import pyodbc


class WordRepository:
    """Repository for word data access"""
    
    def __init__(self, server, database):
        self.server = server
        self.database = database
        self.connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    

    def get_words_by_difficulty(self, count_by_difficulty, WordClass):
        """
        Get words by difficulty level
        
        Args:
            count_by_difficulty: Dictionary with difficulty levels as keys and counts as values
            WordClass: The Word class reference (from game.py)
        
        Returns:
            Dictionary of word lists by difficulty
        """
        result = {}
        
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            for difficulty, count in count_by_difficulty.items():
                cursor.execute(
                    "SELECT kelime, aciklama, detayli FROM kelimeler WHERE zorluk = ? ORDER BY NEWID()",
                    difficulty
                )
                words = cursor.fetchmany(count)
                # Use the passed WordClass to create instances
                result[difficulty] = [WordClass(word, description, details) for word, description, details in words]
            
            conn.close()
            
        except Exception as e:
            print(f"Database connection error: {e}")
            raise
            
        return result 