from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

import database
from schemas import StudentCreate, StudentResponse, StudentUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and default seed data
    database.init_db()
    yield


app = FastAPI(
    title="Student Management CRUD API",
    description="Simple, robust FastAPI application to Register, View, Update, and Delete students.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# REST API ENDPOINTS (CRUD)
# ==========================================

@app.post(
    "/api/students",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student",
    tags=["Students"],
)
def register_student(student_data: StudentCreate):
    """
    Register a new student with name, email, age, course, and GPA.
    - **email**: Must be unique
    - **gpa**: Scale 0.0 - 4.0
    """
    existing = database.get_student_by_email(student_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student with email '{student_data.email}' already exists.",
        )
    created = database.create_student(student_data.model_dump())
    return created


@app.get(
    "/api/students",
    response_model=List[StudentResponse],
    summary="View all students (with optional search)",
    tags=["Students"],
)
def get_all_students(
    search: Optional[str] = Query(
        None, description="Search term for name, email, or course"
    )
):
    """Retrieve all students, or filter results by keyword matching name, email, or course."""
    return database.get_all_students(search=search)


@app.get(
    "/api/students/{student_id}",
    response_model=StudentResponse,
    summary="View a single student by ID",
    tags=["Students"],
)
def get_student(student_id: int):
    """Fetch details of a single student by their unique ID."""
    student = database.get_student_by_id(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )
    return student


@app.put(
    "/api/students/{student_id}",
    response_model=StudentResponse,
    summary="Update an existing student",
    tags=["Students"],
)
def update_student(student_id: int, student_data: StudentUpdate):
    """
    Update fields of an existing student.
    All fields are optional; only provided fields will be modified.
    """
    existing = database.get_student_by_id(student_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )

    # Check if updated email collides with another student
    if student_data.email and student_data.email.lower() != existing["email"].lower():
        email_owner = database.get_student_by_email(student_data.email)
        if email_owner and email_owner["id"] != student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{student_data.email}' is already taken by another student.",
            )

    updated = database.update_student(student_id, student_data.model_dump(exclude_unset=True))
    return updated


@app.delete(
    "/api/students/{student_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a student",
    tags=["Students"],
)
def delete_student(student_id: int):
    """Delete a student record permanently by ID."""
    existing = database.get_student_by_id(student_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )
    database.delete_student(student_id)
    return {
        "success": True,
        "message": f"Student '{existing['name']}' (ID {student_id}) deleted successfully.",
        "id": student_id,
    }


@app.get("/api/stats", summary="Get overall student statistics", tags=["Stats"])
def get_stats():
    """Summary metrics for the dashboard."""
    students = database.get_all_students()
    total = len(students)
    avg_gpa = round(sum(s["gpa"] for s in students) / total, 2) if total > 0 else 0.0
    courses = list({s["course"] for s in students})
    return {
        "total_students": total,
        "average_gpa": avg_gpa,
        "total_courses": len(courses),
    }


# ==========================================
# INTERACTIVE DASHBOARD UI
# ==========================================

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_dashboard():
    """Returns a modern, reactive student management interface."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Manager | FastAPI CRUD</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-body: #0b0f19;
            --bg-card: rgba(17, 24, 39, 0.75);
            --bg-card-hover: rgba(31, 41, 55, 0.8);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(255, 255, 255, 0.16);
            --accent-primary: #6366f1;
            --accent-primary-hover: #4f46e5;
            --accent-secondary: #06b6d4;
            --accent-success: #10b981;
            --accent-danger: #ef4444;
            --accent-warning: #f59e0b;
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
            --text-faint: #6b7280;
            --radius-md: 12px;
            --radius-lg: 16px;
            --shadow-card: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
            --transition-smooth: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        body {
            background-color: var(--bg-body);
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(6, 182, 212, 0.1) 0px, transparent 50%);
            background-attachment: fixed;
            color: var(--text-main);
            min-height: 100vh;
            padding: 24px 16px;
        }

        .container {
            max-width: 1180px;
            margin: 0 auto;
        }

        /* Top Navigation Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 18px 24px;
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            margin-bottom: 28px;
            box-shadow: var(--shadow-card);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-icon {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
        }

        .brand-title h1 {
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #ffffff, #d1d5db);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-title p {
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .header-links {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .btn-swagger {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: var(--transition-smooth);
        }

        .btn-swagger:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--border-hover);
            transform: translateY(-1px);
        }

        /* Metric Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 18px;
            margin-bottom: 28px;
        }

        .stat-card {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: var(--shadow-card);
            transition: var(--transition-smooth);
        }

        .stat-card:hover {
            border-color: var(--border-hover);
            transform: translateY(-2px);
        }

        .stat-info p {
            font-size: 0.82rem;
            color: var(--text-muted);
            font-weight: 500;
            margin-bottom: 4px;
        }

        .stat-info h2 {
            font-size: 1.8rem;
            font-weight: 800;
            color: #ffffff;
        }

        .stat-badge {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Controls Section (Search & Register button) */
        .controls-panel {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }

        .search-box {
            position: relative;
            flex: 1;
            min-width: 260px;
        }

        .search-box input {
            width: 100%;
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 11px 16px 11px 40px;
            color: var(--text-main);
            font-size: 0.9rem;
            outline: none;
            transition: var(--transition-smooth);
        }

        .search-box input:focus {
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25);
        }

        .search-icon {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-faint);
            pointer-events: none;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-primary-hover));
            color: #ffffff;
            border: none;
            border-radius: 10px;
            padding: 11px 20px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: var(--transition-smooth);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
        }

        .btn-primary:hover {
            filter: brightness(1.1);
            transform: translateY(-1px);
        }

        /* Table Styling */
        .table-card {
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-card);
        }

        .table-responsive {
            width: 100%;
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }

        th {
            background: rgba(255, 255, 255, 0.02);
            padding: 14px 20px;
            font-size: 0.8rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--border-color);
        }

        td {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.9rem;
            vertical-align: middle;
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover td {
            background: rgba(255, 255, 255, 0.025);
        }

        .student-profile {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, #374151, #1f2937);
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.85rem;
            border: 1px solid var(--border-color);
        }

        .student-name {
            font-weight: 600;
            color: #ffffff;
        }

        .student-email {
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .badge-course {
            display: inline-block;
            background: rgba(99, 102, 241, 0.12);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.25);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .badge-gpa {
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 0.85rem;
            display: inline-block;
        }

        .gpa-high {
            background: rgba(16, 185, 129, 0.12);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .gpa-med {
            background: rgba(245, 158, 11, 0.12);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .gpa-low {
            background: rgba(239, 68, 68, 0.12);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        /* Action Buttons */
        .actions-cell {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-action {
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            padding: 7px 11px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            transition: var(--transition-smooth);
        }

        .btn-action:hover {
            color: #ffffff;
            border-color: var(--border-hover);
            background: rgba(255, 255, 255, 0.05);
        }

        .btn-action.edit:hover {
            border-color: var(--accent-primary);
            color: #818cf8;
            background: rgba(99, 102, 241, 0.1);
        }

        .btn-action.delete:hover {
            border-color: var(--accent-danger);
            color: #f87171;
            background: rgba(239, 68, 68, 0.1);
        }

        /* Empty State */
        .empty-state {
            padding: 48px 20px;
            text-align: center;
            color: var(--text-muted);
        }

        .empty-state svg {
            width: 48px;
            height: 48px;
            margin-bottom: 12px;
            color: var(--text-faint);
        }

        /* Modal Dialog */
        .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px;
            z-index: 100;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
        }

        .modal-overlay.active {
            opacity: 1;
            pointer-events: auto;
        }

        .modal-content {
            background: #131b2e;
            border: 1px solid var(--border-hover);
            border-radius: var(--radius-lg);
            width: 100%;
            max-width: 480px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.8);
            transform: scale(0.95);
            transition: transform 0.2s ease;
            overflow: hidden;
        }

        .modal-overlay.active .modal-content {
            transform: scale(1);
        }

        .modal-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-header h3 {
            font-size: 1.15rem;
            font-weight: 700;
        }

        .btn-close {
            background: none;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 1.25rem;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 4px;
            border-radius: 6px;
        }

        .btn-close:hover {
            color: #ffffff;
            background: rgba(255, 255, 255, 0.1);
        }

        .modal-body {
            padding: 24px;
        }

        .form-group {
            margin-bottom: 18px;
        }

        .form-group label {
            display: block;
            font-size: 0.82rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 6px;
        }

        .form-group input {
            width: 100%;
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px 14px;
            color: #ffffff;
            font-size: 0.9rem;
            outline: none;
            transition: var(--transition-smooth);
        }

        .form-group input:focus {
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
        }

        .modal-footer {
            padding: 16px 24px;
            background: rgba(0, 0, 0, 0.2);
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }

        .btn-secondary {
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            padding: 9px 16px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.05);
            color: #ffffff;
        }

        /* Toast Notifications */
        .toast-container {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 200;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .toast {
            background: #1f2937;
            border: 1px solid var(--border-color);
            color: #ffffff;
            padding: 12px 18px;
            border-radius: 10px;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.6);
            animation: slideIn 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        .toast.success { border-left: 4px solid var(--accent-success); }
        .toast.error { border-left: 4px solid var(--accent-danger); }

        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <div class="brand">
                <div class="brand-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
                        <path d="M6 12v5c3 3 9 3 12 0v-5"/>
                    </svg>
                </div>
                <div class="brand-title">
                    <h1>FastAPI Student CRUD</h1>
                    <p>Register, View, Update & Delete Records</p>
                </div>
            </div>
            <div class="header-links">
                <a href="/docs" target="_blank" class="btn-swagger">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="16 18 22 12 16 6"></polyline>
                        <polyline points="8 6 2 12 8 18"></polyline>
                    </svg>
                    Interactive Swagger Docs
                </a>
            </div>
        </header>

        <!-- Stats Overview -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-info">
                    <p>Total Registered Students</p>
                    <h2 id="stat-total">0</h2>
                </div>
                <div class="stat-badge" style="background: rgba(99, 102, 241, 0.15); color: #818cf8;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                        <circle cx="9" cy="7" r="4"></circle>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                    </svg>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-info">
                    <p>Average Student GPA</p>
                    <h2 id="stat-gpa">0.00</h2>
                </div>
                <div class="stat-badge" style="background: rgba(16, 185, 129, 0.15); color: #34d399;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="8" r="7"></circle>
                        <polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"></polyline>
                    </svg>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-info">
                    <p>Active Academic Courses</p>
                    <h2 id="stat-courses">0</h2>
                </div>
                <div class="stat-badge" style="background: rgba(6, 182, 212, 0.15); color: #22d3ee;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                    </svg>
                </div>
            </div>
        </div>

        <!-- Controls (Search & Register) -->
        <div class="controls-panel">
            <div class="search-box">
                <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                <input type="text" id="searchInput" placeholder="Search by name, email, or course..." oninput="handleSearch()">
            </div>
            <button class="btn-primary" onclick="openCreateModal()">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                Register Student
            </button>
        </div>

        <!-- Students Table -->
        <div class="table-card">
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Student ID</th>
                            <th>Student</th>
                            <th>Age</th>
                            <th>Course</th>
                            <th>GPA</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="studentTableBody">
                        <!-- Populated dynamically via JS -->
                    </tbody>
                </table>
            </div>
            <div id="emptyState" class="empty-state" style="display: none;">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <line x1="23" y1="11" x2="17" y2="11"></line>
                </svg>
                <h3>No Students Found</h3>
                <p>No student records match your query. Click "Register Student" to add one.</p>
            </div>
        </div>
    </div>

    <!-- Student Form Modal (Create & Update) -->
    <div class="modal-overlay" id="studentModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="modalTitle">Register New Student</h3>
                <button class="btn-close" onclick="closeModal()">&times;</button>
            </div>
            <form id="studentForm" onsubmit="handleFormSubmit(event)">
                <input type="hidden" id="studentId">
                <div class="modal-body">
                    <div class="form-group">
                        <label for="name">Full Name *</label>
                        <input type="text" id="name" required placeholder="e.g. Alexander Pierce" minlength="2">
                    </div>
                    <div class="form-group">
                        <label for="email">Email Address *</label>
                        <input type="email" id="email" required placeholder="e.g. alex@university.edu">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="age">Age *</label>
                            <input type="number" id="age" required min="10" max="120" placeholder="e.g. 21">
                        </div>
                        <div class="form-group">
                            <label for="gpa">GPA (0.0 - 4.0) *</label>
                            <input type="number" id="gpa" required min="0" max="4.0" step="0.01" placeholder="e.g. 3.85">
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="course">Academic Course / Major *</label>
                        <input type="text" id="course" required placeholder="e.g. Software Engineering" minlength="2">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn-primary" id="btnSubmitForm">Save Student</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Toast Notifications Container -->
    <div class="toast-container" id="toastContainer"></div>

    <script>
        let searchTimeout = null;

        // Fetch students & dashboard stats on load
        document.addEventListener('DOMContentLoaded', () => {
            loadStudents();
            loadStats();
        });

        async function loadStats() {
            try {
                const res = await fetch('/api/stats');
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('stat-total').innerText = data.total_students;
                    document.getElementById('stat-gpa').innerText = Number(data.average_gpa).toFixed(2);
                    document.getElementById('stat-courses').innerText = data.total_courses;
                }
            } catch (err) {
                console.error("Failed to load statistics:", err);
            }
        }

        async function loadStudents(query = '') {
            try {
                const url = query ? `/api/students?search=${encodeURIComponent(query)}` : '/api/students';
                const res = await fetch(url);
                const students = await res.json();
                renderTable(students);
            } catch (err) {
                showToast("Failed to fetch students from API.", "error");
            }
        }

        function handleSearch() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const q = document.getElementById('searchInput').value.trim();
                loadStudents(q);
            }, 250);
        }

        function renderTable(students) {
            const tbody = document.getElementById('studentTableBody');
            const emptyState = document.getElementById('emptyState');
            tbody.innerHTML = '';

            if (!students || students.length === 0) {
                emptyState.style.display = 'block';
                return;
            }
            emptyState.style.display = 'none';

            students.forEach(s => {
                const initials = s.name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase();
                let gpaClass = 'gpa-med';
                if (s.gpa >= 3.7) gpaClass = 'gpa-high';
                else if (s.gpa < 3.0) gpaClass = 'gpa-low';

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="color: var(--text-muted); font-weight: 600;">#${s.id}</td>
                    <td>
                        <div class="student-profile">
                            <div class="avatar">${initials}</div>
                            <div>
                                <div class="student-name">${escapeHtml(s.name)}</div>
                                <div class="student-email">${escapeHtml(s.email)}</div>
                            </div>
                        </div>
                    </td>
                    <td>${s.age}</td>
                    <td><span class="badge-course">${escapeHtml(s.course)}</span></td>
                    <td><span class="badge-gpa ${gpaClass}">${Number(s.gpa).toFixed(2)}</span></td>
                    <td>
                        <div class="actions-cell">
                            <button class="btn-action edit" onclick="openEditModal(${s.id})" title="Edit Student">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                </svg>
                                Edit
                            </button>
                            <button class="btn-action delete" onclick="confirmDelete(${s.id}, '${escapeHtml(s.name)}')" title="Delete Student">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="3 6 5 6 21 6"></polyline>
                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                </svg>
                                Delete
                            </button>
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function openCreateModal() {
            document.getElementById('modalTitle').innerText = 'Register New Student';
            document.getElementById('studentId').value = '';
            document.getElementById('studentForm').reset();
            document.getElementById('studentModal').classList.add('active');
        }

        async function openEditModal(id) {
            try {
                const res = await fetch(`/api/students/${id}`);
                if (!res.ok) throw new Error("Could not find student");
                const student = await res.json();

                document.getElementById('modalTitle').innerText = `Update Student #${student.id}`;
                document.getElementById('studentId').value = student.id;
                document.getElementById('name').value = student.name;
                document.getElementById('email').value = student.email;
                document.getElementById('age').value = student.age;
                document.getElementById('course').value = student.course;
                document.getElementById('gpa').value = student.gpa;

                document.getElementById('studentModal').classList.add('active');
            } catch (err) {
                showToast(err.message, "error");
            }
        }

        function closeModal() {
            document.getElementById('studentModal').classList.remove('active');
        }

        async function handleFormSubmit(e) {
            e.preventDefault();
            const id = document.getElementById('studentId').value;
            const payload = {
                name: document.getElementById('name').value.trim(),
                email: document.getElementById('email').value.trim(),
                age: parseInt(document.getElementById('age').value),
                course: document.getElementById('course').value.trim(),
                gpa: parseFloat(document.getElementById('gpa').value)
            };

            const isEdit = Boolean(id);
            const endpoint = isEdit ? `/api/students/${id}` : '/api/students';
            const method = isEdit ? 'PUT' : 'POST';

            try {
                const res = await fetch(endpoint, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const result = await res.json();
                if (!res.ok) {
                    const errorMsg = result.detail || (Array.isArray(result) ? result[0].msg : 'Failed to save student.');
                    showToast(errorMsg, 'error');
                    return;
                }

                closeModal();
                showToast(isEdit ? "Student updated successfully!" : "Student registered successfully!", "success");
                loadStudents(document.getElementById('searchInput').value.trim());
                loadStats();
            } catch (err) {
                showToast("Network error. Please try again.", "error");
            }
        }

        async function confirmDelete(id, name) {
            if (!confirm(`Are you sure you want to delete student "${name}" (ID #${id})?`)) {
                return;
            }

            try {
                const res = await fetch(`/api/students/${id}`, { method: 'DELETE' });
                const result = await res.json();
                if (!res.ok) {
                    showToast(result.detail || "Failed to delete student.", "error");
                    return;
                }
                showToast(`Student #${id} deleted successfully.`, "success");
                loadStudents(document.getElementById('searchInput').value.trim());
                loadStats();
            } catch (err) {
                showToast("Network error when deleting.", "error");
            }
        }

        function showToast(message, type = 'success') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerText = message;
            container.appendChild(toast);

            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(10px)';
                toast.style.transition = 'all 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }, 3500);
        }

        function escapeHtml(str) {
            if (!str) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }
    </script>
</body>
</html>
"""
