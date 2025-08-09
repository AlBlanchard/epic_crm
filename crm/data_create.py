from sqlalchemy.orm import Session
from typing import Optional

class DataCreate:
    """Classe pour créer des données de test dans la base de données."""
    
        def __init__(self, session: Session, user_id: Optional[int] = None):
            self.session = session
            self._user_id = user_id
            self._current_user = None