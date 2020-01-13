import sqlite3
from pathlib import Path


class HandledItemTracker:
    def __init__(self, database_filename: Path):
        """Set up a connection to the database, creating it if required"""

        self.database = sqlite3.connect(str(database_filename))
        c = self.database.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS handled(id TEXT PRIMARY KEY)')
        self.database.commit()

    def add(self, item: str) -> None:
        """Mark the given item as handled"""

        c = self.database.cursor()
        c.execute("INSERT INTO handled VALUES (?)", (item,))
        self.database.commit()

    def __contains__(self, item: str) -> bool:
        """Check if the given item is handled"""

        c = self.database.cursor()
        c.execute("SELECT COUNT(*) FROM handled WHERE id=?", (item,))
        (count,) = c.fetchone()

        return count > 0
