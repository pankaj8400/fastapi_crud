import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class StudentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the student", examples=["Alice Johnson"])
    email: str = Field(..., description="Unique email address", examples=["alice@university.edu"])
    age: int = Field(..., ge=10, le=120, description="Age of the student (10-120)", examples=[21])
    course: str = Field(..., min_length=2, max_length=100, description="Enrolled major or course", examples=["Computer Science"])
    gpa: float = Field(default=3.5, ge=0.0, le=4.0, description="GPA score between 0.0 and 4.0", examples=[3.85])

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format (e.g., student@example.com)")
        return v

    @field_validator("name", "course")
    @classmethod
    def clean_text(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Field must contain at least 2 characters")
        return clean


class StudentCreate(StudentBase):
    """Schema for registering a new student."""
    pass


class StudentUpdate(BaseModel):
    """Schema for updating student details (all fields optional)."""
    name: Optional[str] = Field(None, min_length=2, max_length=100, examples=["Alice Smith"])
    email: Optional[str] = Field(None, examples=["alice.smith@university.edu"])
    age: Optional[int] = Field(None, ge=10, le=120, examples=[22])
    course: Optional[str] = Field(None, min_length=2, max_length=100, examples=["Data Science"])
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0, examples=[3.95])

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().lower()
            if not re.match(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$", v):
                raise ValueError("Invalid email format")
            return v
        return v

    @field_validator("name", "course")
    @classmethod
    def clean_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if len(clean) < 2:
                raise ValueError("Field must contain at least 2 characters")
            return clean
        return v


class StudentResponse(StudentBase):
    """Schema for student responses including system-generated ID and creation time."""
    id: int
    created_at: str

    class Config:
        from_attributes = True
