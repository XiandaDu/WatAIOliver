from pydantic import BaseModel


class CourseModelCreate(BaseModel):
    course_id: str
    model_id: str


class CourseModelDelete(BaseModel):
    course_id: str
    model_id: str


class CourseModelResponse(BaseModel):
    course_id: str
    model_id: str
