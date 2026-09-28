# Simple FastAPI Student CRUD Application

A simple, fast, and modern Student Management CRUD system built with **FastAPI**, **Pydantic v2**, and **SQLite3**, featuring an interactive web dashboard and OpenAPI Swagger documentation.

---

## Features

- **Register (Create)**: Register students with full name, email, age, course/major, and GPA. Includes validation and email uniqueness checks.
- **View (Read)**:
  - View all registered students (`GET /api/students`).
  - Search students dynamically by name, email, or course (`GET /api/students?search=...`).
  - View a single student by ID (`GET /api/students/{id}`).
- **Update (Update)**: Update student fields partially or completely (`PUT /api/students/{id}`).
- **Delete (Delete)**: Permanently remove a student record (`DELETE /api/students/{id}`).
- **Built-in Web Dashboard**: Modern UI served directly at `http://127.0.0.1:8000/`.
- **Interactive API Docs**: Auto-generated Swagger UI at `http://127.0.0.1:8000/docs`.

---

## Project Structure

```text
crud/
├── main.py           # FastAPI application, endpoints & built-in dashboard UI
├── database.py       # SQLite connection, table schema, and query helpers
├── schemas.py        # Pydantic data validation and response models
├── test_api.py       # Automated integration test suite
├── requirements.txt  # Project dependencies
└── README.md         # Documentation
```

---

## How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python -m uvicorn main:app --reload
```

Server will start on:
- **Web Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/students` | **Register** a new student |
| `GET` | `/api/students` | **View** all students (optional `?search=term`) |
| `GET` | `/api/students/{id}` | **View** student details by ID |
| `PUT` | `/api/students/{id}` | **Update** student details |
| `DELETE` | `/api/students/{id}` | **Delete** a student by ID |
| `GET` | `/api/stats` | Summary statistics (counts, avg GPA) |
| `GET` | `/` | Web Management Dashboard |

---

## Example API Requests (cURL)

### 1. Register a Student (Create)
```bash
curl -X POST "http://127.0.0.1:8000/api/students" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah Connor",
    "email": "sarah.connor@example.com",
    "age": 21,
    "course": "Cybernetics",
    "gpa": 3.9
  }'
```

### 2. View All Students (Read)
```bash
curl -X GET "http://127.0.0.1:8000/api/students"
```

### 3. View Student by ID (Read)
```bash
curl -X GET "http://127.0.0.1:8000/api/students/1"
```

### 4. Update Student (Update)
```bash
curl -X PUT "http://127.0.0.1:8000/api/students/1" \
  -H "Content-Type: application/json" \
  -d '{
    "gpa": 3.95,
    "course": "Artificial Intelligence"
  }'
```

### 5. Delete Student (Delete)
```bash
curl -X DELETE "http://127.0.0.1:8000/api/students/1"
```

---

## Running the Automated Tests

Run the test suite to verify all CRUD actions:
```bash
python test_api.py
```
