from fastapi.testclient import TestClient
from main import app
import database

client = TestClient(app)


def setup_module():
    """Ensure database is initialized before running tests."""
    database.init_db()


def test_crud_student_lifecycle():
    # 1. View all students
    response = client.get("/api/students")
    assert response.status_code == 200
    initial_students = response.json()
    assert isinstance(initial_students, list)
    assert len(initial_students) >= 1

    # 2. Register a new student (CREATE)
    new_student_data = {
        "name": "David Miller",
        "email": "david.miller.test@university.edu",
        "age": 22,
        "course": "Artificial Intelligence",
        "gpa": 3.85,
    }
    create_res = client.post("/api/students", json=new_student_data)
    assert create_res.status_code == 201, f"Create failed: {create_res.text}"
    created_student = create_res.json()
    student_id = created_student["id"]

    assert created_student["name"] == "David Miller"
    assert created_student["email"] == "david.miller.test@university.edu"
    assert created_student["age"] == 22
    assert created_student["course"] == "Artificial Intelligence"
    assert created_student["gpa"] == 3.85
    assert "created_at" in created_student

    # 3. Prevent duplicate email registration
    dup_res = client.post("/api/students", json=new_student_data)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 4. View single student by ID (READ)
    view_res = client.get(f"/api/students/{student_id}")
    assert view_res.status_code == 200
    assert view_res.json()["id"] == student_id
    assert view_res.json()["name"] == "David Miller"

    # 5. Search for the student
    search_res = client.get("/api/students?search=Miller")
    assert search_res.status_code == 200
    search_matches = search_res.json()
    assert any(s["id"] == student_id for s in search_matches)

    # 6. Update student details (UPDATE)
    update_data = {
        "course": "Robotics & AI",
        "gpa": 3.95,
    }
    update_res = client.put(f"/api/students/{student_id}", json=update_data)
    assert update_res.status_code == 200
    updated_student = update_res.json()
    assert updated_student["course"] == "Robotics & AI"
    assert updated_student["gpa"] == 3.95
    assert updated_student["name"] == "David Miller"  # Unchanged field remains intact

    # 7. Delete student (DELETE)
    del_res = client.delete(f"/api/students/{student_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 8. Verify student is deleted (READ after DELETE -> 404)
    after_del_res = client.get(f"/api/students/{student_id}")
    assert after_del_res.status_code == 404


def test_dashboard_ui_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    assert "Student Manager" in res.text
    assert "<table" in res.text


def test_stats_endpoint():
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_students" in data
    assert "average_gpa" in data
    assert "total_courses" in data


if __name__ == "__main__":
    setup_module()
    test_crud_student_lifecycle()
    test_dashboard_ui_endpoint()
    test_stats_endpoint()
    print("All CRUD and endpoint tests passed successfully!")
