"""
SuperClarity AI - Embedded SQLite Relational Database Engine
Manages user authentication, product catalog items, multi-version history,
project folders, and batch processing queues.
"""

import os
import sqlite3
import json
import time
from werkzeug.security import generate_password_hash, check_password_hash

if os.environ.get("VERCEL"):
    DB_PATH = os.path.join("/tmp", "supplier_clarity.db")
else:
    DB_PATH = os.path.join("data", "supplier_clarity.db")


def get_db_connection():
    """Returns a SQLite connection with row factory enabled."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'merchant',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS catalog_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        project_id INTEGER,
        title TEXT NOT NULL,
        category TEXT,
        original_filename TEXT,
        original_path TEXT,
        enhanced_path TEXT,
        original_resolution TEXT,
        enhanced_resolution TEXT,
        scale INTEGER DEFAULT 4,
        method TEXT DEFAULT 'realesrgan',
        quality_score INTEGER DEFAULT 80,
        tags TEXT,
        phash TEXT,
        is_favorite INTEGER DEFAULT 0,
        status TEXT DEFAULT 'catalog_ready',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS image_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        catalog_id INTEGER NOT NULL,
        version_num INTEGER NOT NULL,
        filepath TEXT NOT NULL,
        action_type TEXT,
        parameters TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (catalog_id) REFERENCES catalog_items(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS batch_jobs (
        id TEXT PRIMARY KEY,
        user_id INTEGER DEFAULT 1,
        total_count INTEGER DEFAULT 0,
        completed_count INTEGER DEFAULT 0,
        failed_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'queued',
        zip_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create default demo user and project if missing
    cursor.execute("SELECT id FROM users WHERE username = 'demo_seller'")
    if not cursor.fetchone():
        pwd_hash = generate_password_hash("clarity2026")
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                       ("demo_seller", pwd_hash, "merchant"))
        demo_user_id = cursor.lastrowid
        cursor.execute("INSERT INTO projects (user_id, name, description) VALUES (?, ?, ?)",
                       (demo_user_id, "Q4 Catalog Launch", "Main holiday season vendor uploads"))
        
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# USER AUTHENTICATION
# ---------------------------------------------------------------------

def register_user(username: str, password: str, role: str = "merchant"):
    """Registers a new user."""
    conn = get_db_connection()
    try:
        pwd_hash = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                       (username.strip(), pwd_hash, role))
        conn.commit()
        return {"success": True, "user_id": cursor.lastrowid, "username": username}
    except sqlite3.IntegrityError:
        return {"success": False, "error": f"Username '{username}' already exists."}
    finally:
        conn.close()


def authenticate_user(username: str, password: str):
    """Authenticates credentials against the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username.strip(),))
    row = cursor.fetchone()
    conn.close()

    if row and check_password_hash(row["password_hash"], password):
        return {
            "success": True,
            "user": {
                "id": row["id"],
                "username": row["username"],
                "role": row["role"]
            }
        }
    return {"success": False, "error": "Invalid username or password."}


def get_user_by_id(user_id: int):
    """Fetches user record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------------
# CATALOG MANAGEMENT
# ---------------------------------------------------------------------

def add_catalog_item(
    title: str,
    original_path: str,
    enhanced_path: str,
    user_id: int = 1,
    project_id: int = None,
    category: str = "General Product",
    original_filename: str = None,
    original_resolution: str = "128x128",
    enhanced_resolution: str = "512x512",
    scale: int = 4,
    method: str = "realesrgan",
    quality_score: int = 85,
    tags: list = None,
    phash: str = None
):
    """Adds a new enhanced item to the product catalog."""
    conn = get_db_connection()
    cursor = conn.cursor()
    tags_str = json.dumps(tags if tags else [])

    cursor.execute("""
    INSERT INTO catalog_items (
        user_id, project_id, title, category, original_filename, original_path,
        enhanced_path, original_resolution, enhanced_resolution, scale,
        method, quality_score, tags, phash
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, project_id, title, category, original_filename, original_path,
        enhanced_path, original_resolution, enhanced_resolution, scale,
        method, quality_score, tags_str, phash
    ))
    item_id = cursor.lastrowid

    # Record Version 1 in history
    cursor.execute("""
    INSERT INTO image_versions (catalog_id, version_num, filepath, action_type, parameters)
    VALUES (?, ?, ?, ?, ?)
    """, (item_id, 1, enhanced_path, f"{scale}x_{method}", json.dumps({"scale": scale, "method": method})))

    conn.commit()
    conn.close()
    return item_id


def get_catalog_items(user_id: int = None, category: str = None, search: str = None, is_favorite: bool = None, limit: int = 50, query: str = None):
    """Queries catalog items with optional filtering."""
    if query and not search:
        search = query

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM catalog_items WHERE 1=1"
    params = []

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (title LIKE ? OR category LIKE ? OR tags LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    if is_favorite is not None:
        query += " AND is_favorite = ?"
        params.append(1 if is_favorite else 0)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    items = []
    for r in rows:
        d = dict(r)
        try:
            d["tags"] = json.loads(d["tags"]) if d["tags"] else []
        except Exception:
            d["tags"] = []
        items.append(d)
    return items


def get_catalog_item(item_id: int):
    """Retrieves a single catalog item along with its version history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM catalog_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    item = dict(row)
    try:
        item["tags"] = json.loads(item["tags"]) if item["tags"] else []
    except Exception:
        item["tags"] = []

    cursor.execute("SELECT * FROM image_versions WHERE catalog_id = ? ORDER BY version_num DESC", (item_id,))
    item["versions"] = [dict(v) for v in cursor.fetchall()]

    conn.close()
    return item


def toggle_favorite(item_id: int):
    """Toggles favorite bookmark flag on a catalog item."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE catalog_items SET is_favorite = 1 - is_favorite WHERE id = ?", (item_id,))
    conn.commit()
    cursor.execute("SELECT is_favorite FROM catalog_items WHERE id = ?", (item_id,))
    val = cursor.fetchone()["is_favorite"]
    conn.close()
    return bool(val)


def delete_catalog_item(item_id: int):
    """Deletes an item and associated version records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM image_versions WHERE catalog_id = ?", (item_id,))
    cursor.execute("DELETE FROM catalog_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return True


def add_catalog_version(catalog_id: int, filepath: str, action_type: str, parameters: dict):
    """Appends a new version to an existing catalog image."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(version_num) as max_v FROM image_versions WHERE catalog_id = ?", (catalog_id,))
    res = cursor.fetchone()
    next_v = (res["max_v"] or 0) + 1

    cursor.execute("""
    INSERT INTO image_versions (catalog_id, version_num, filepath, action_type, parameters)
    VALUES (?, ?, ?, ?, ?)
    """, (catalog_id, next_v, filepath, action_type, json.dumps(parameters)))

    # Update latest enhanced path in main catalog item
    cursor.execute("UPDATE catalog_items SET enhanced_path = ? WHERE id = ?", (filepath, catalog_id))
    conn.commit()
    conn.close()
    return next_v


# ---------------------------------------------------------------------
# BATCH JOBS TRACKING
# ---------------------------------------------------------------------

def create_batch_job(job_id: str, total_count: int, user_id: int = 1):
    """Registers a new batch job in the queue."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO batch_jobs (id, user_id, total_count, completed_count, failed_count, status)
    VALUES (?, ?, ?, 0, 0, 'queued')
    """, (job_id, user_id, total_count))
    conn.commit()
    conn.close()


def update_batch_progress(job_id: str, completed_count: int, failed_count: int = 0, status: str = "running", zip_path: str = None):
    """Updates batch processing progress and terminal status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if zip_path:
        cursor.execute("""
        UPDATE batch_jobs SET completed_count = ?, failed_count = ?, status = ?, zip_path = ? WHERE id = ?
        """, (completed_count, failed_count, status, zip_path, job_id))
    else:
        cursor.execute("""
        UPDATE batch_jobs SET completed_count = ?, failed_count = ?, status = ? WHERE id = ?
        """, (completed_count, failed_count, status, job_id))
    conn.commit()
    conn.close()


def get_batch_job(job_id: str):
    """Retrieves batch job status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM batch_jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# Auto-initialize database on import
init_db()
