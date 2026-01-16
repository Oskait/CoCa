import sqlite3

DB_FILE = "compounds.db"

def init_db():
    """
    Initializes the database. Creates the table if it doesn't exist and
    alters the table to add new columns if they are missing, ensuring
    backward compatibility.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Create table if it doesn't exist
    c.execute("""
        CREATE TABLE IF NOT EXISTS compounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            molecular_weight REAL NOT NULL,
            standard_concentration REAL,
            standard_volume REAL
        )
    """)

    # --- Schema Migration (idempotent) ---
    c.execute("PRAGMA table_info(compounds)")
    columns = [row[1] for row in c.fetchall()]
    if 'standard_concentration' not in columns:
        c.execute("ALTER TABLE compounds ADD COLUMN standard_concentration REAL")
    if 'standard_volume' not in columns:
        c.execute("ALTER TABLE compounds ADD COLUMN standard_volume REAL")

    conn.commit()
    conn.close()

def add_compound(name, molecular_weight, standard_concentration=None, standard_volume=None):
    """Adds a single new compound to the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            INSERT INTO compounds (name, molecular_weight, standard_concentration, standard_volume)
            VALUES (?, ?, ?, ?)
        """, (name, molecular_weight, standard_concentration, standard_volume))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def upsert_compounds(compounds_data):
    """
    Inserts or updates multiple compounds in the database.
    'compounds_data' should be a list of tuples:
    [(name, mw, std_conc, std_vol), ...]
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        sql = """
            INSERT INTO compounds (name, molecular_weight, standard_concentration, standard_volume)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                molecular_weight = excluded.molecular_weight,
                standard_concentration = excluded.standard_concentration,
                standard_volume = excluded.standard_volume
        """
        c.executemany(sql, compounds_data)
        conn.commit()
        return c.rowcount, None
    except Exception as e:
        conn.rollback()
        return 0, e
    finally:
        conn.close()

def get_compound(name):
    """Retrieves a compound's data by its name."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM compounds WHERE name=?", (name,))
    result = c.fetchone()
    conn.close()
    return dict(result) if result else None

def get_all_compound_names():
    """Retrieves all compound names from the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name FROM compounds ORDER BY name")
    results = c.fetchall()
    conn.close()
    return [row[0] for row in results]
