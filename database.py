import sqlite3
from contextlib import contextmanager
from typing import List, Optional, Dict, Any

DB_NAME = "students.db"


@contextmanager
def get_db():
    """Context manager for SQLite database connection."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database tables and insert sample records if empty."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                age INTEGER NOT NULL,
                course TEXT NOT NULL,
                gpa REAL NOT NULL DEFAULT 3.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

        # Seed sample data if the table is currently empty
        cursor.execute("SELECT COUNT(*) AS cnt FROM students")
        count = cursor.fetchone()["cnt"]
        if count == 0:
            sample_students = [
                ("Sophia Martinez", "sophia.m@university.edu", 20, "Computer Science", 3.88),
                ("Liam Chen", "liam.chen@university.edu", 22, "Mechanical Engineering", 3.75),
                ("Emma Watson", "emma.w@university.edu", 21, "Data Science", 3.92),
                ("Noah Patel", "noah.patel@university.edu", 23, "Business Administration", 3.60),
            ]
            cursor.executemany(
                """
                INSERT INTO students (name, email, age, course, gpa)
                VALUES (?, ?, ?, ?, ?)
                """,
                sample_students,
            )
            conn.commit()


def get_student_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve a student record by email."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE email = ?", (email.lower(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_student_by_id(student_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single student by primary key ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_students(search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all students, optionally filtered by name, email, or course."""
    with get_db() as conn:
        cursor = conn.cursor()
        if search:
            query = """
                SELECT * FROM students
                WHERE name LIKE ? OR email LIKE ? OR course LIKE ?
                ORDER BY id DESC
            """
            pattern = f"%{search.strip()}%"
            cursor.execute(query, (pattern, pattern, pattern))
        else:
            cursor.execute("SELECT * FROM students ORDER BY id DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def create_student(data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a new student and return the inserted record."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO students (name, email, age, course, gpa)
            VALUES (?, ?, ?, ?, ?)
            """,
            (data["name"], data["email"].lower(), data["age"], data["course"], data["gpa"]),
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM students WHERE id = ?", (new_id,))
        return dict(cursor.fetchone())


def update_student(student_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update fields of an existing student."""
    # Filter out None values
    fields = {k: v for k, v in updates.items() if v is not None}
    if not fields:
        return get_student_by_id(student_id)

    set_clauses = []
    values = []
    for key, val in fields.items():
        set_clauses.append(f"{key} = ?")
        if key == "email" and isinstance(val, str):
            values.append(val.lower())
        else:
            values.append(val)

    values.append(student_id)
    sql = f"UPDATE students SET {', '.join(set_clauses)} WHERE id = ?"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(values))
        conn.commit()
        if cursor.rowcount == 0:
            return None
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_student(student_id: int) -> bool:
    """Delete a student by ID. Returns True if deleted, False if not found."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        return cursor.rowcount > 0
