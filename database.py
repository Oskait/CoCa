import sqlite3

DB_FILE = "compounds.db"

def init_db():
    """
    Initializes the database. Creates the table if it doesn't exist and
    migrates the schema from the old 'name' column to the new 'shortname'
    and 'longname' columns if needed.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("PRAGMA table_info(compounds)")
    columns = [row[1] for row in c.fetchall()]

    # If 'name' column exists, we need to migrate the schema.
    if 'name' in columns:
        # 1. Rename the old table
        c.execute("ALTER TABLE compounds RENAME TO compounds_old")

        # 2. Create the new table
        c.execute("""
            CREATE TABLE compounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shortname TEXT NOT NULL UNIQUE,
                longname TEXT,
                molecular_weight REAL NOT NULL,
                standard_concentration REAL,
                standard_volume REAL
            )
        """)

        # 3. Copy data from the old table to the new one
        c.execute("""
            INSERT INTO compounds (id, shortname, longname, molecular_weight, standard_concentration, standard_volume)
            SELECT id, name, name, molecular_weight, standard_concentration, standard_volume
            FROM compounds_old
        """)

        # 4. Drop the old table
        c.execute("DROP TABLE compounds_old")
    else:
        # If no 'name' column, just ensure the new table exists
        c.execute("""
            CREATE TABLE IF NOT EXISTS compounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shortname TEXT NOT NULL UNIQUE,
                longname TEXT,
                molecular_weight REAL NOT NULL,
                standard_concentration REAL,
                standard_volume REAL
            )
        """)

    # --- Schema Migration for concentration units (M to mM) ---
    c.execute("PRAGMA table_info(compounds)")
    columns = [row[1] for row in c.fetchall()]
    if 'conc_in_mM_migrated' not in columns:
        c.execute("UPDATE compounds SET standard_concentration = standard_concentration * 1000 WHERE standard_concentration IS NOT NULL")
        c.execute("ALTER TABLE compounds ADD COLUMN conc_in_mM_migrated INTEGER DEFAULT 1")

    conn.commit()
    conn.close()

def add_compound(shortname, longname, molecular_weight, standard_concentration=None, standard_volume=None):
    """Adds a single new compound to the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO compounds (shortname, longname, molecular_weight, standard_concentration, standard_volume)
            VALUES (?, ?, ?, ?, ?)
        """, (shortname, longname, molecular_weight, standard_concentration, standard_volume))
        conn.commit()
        return c.lastrowid, None
    except Exception as e:
        conn.rollback()
        return None, e
    finally:
        conn.close()

def update_compound(compound_id, shortname, longname, molecular_weight, standard_concentration, standard_volume):
    """Updates an existing compound's data by its ID."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("""
            UPDATE compounds SET
                shortname = ?,
                longname = ?,
                molecular_weight = ?,
                standard_concentration = ?,
                standard_volume = ?
            WHERE id = ?
        """, (shortname, longname, molecular_weight, standard_concentration, standard_volume, compound_id))
        conn.commit()
        return c.rowcount, None
    except Exception as e:
        conn.rollback()
        return 0, e
    finally:
        conn.close()

def delete_compound(compound_id):
    """Deletes a compound from the database by its ID."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM compounds WHERE id = ?", (compound_id,))
        conn.commit()
        return c.rowcount, None
    except Exception as e:
        conn.rollback()
        return 0, e
    finally:
        conn.close()

def get_compound_by_shortname(shortname):
    """Retrieves a compound's data by its shortname."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM compounds WHERE shortname=?", (shortname,))
    result = c.fetchone()
    conn.close()
    return dict(result) if result else None

def get_all_compounds():
    """Retrieves all compounds from the database, ordered by shortname."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, shortname, longname, molecular_weight, standard_concentration, standard_volume FROM compounds ORDER BY shortname")
    results = c.fetchall()
    conn.close()
    return [dict(row) for row in results]
