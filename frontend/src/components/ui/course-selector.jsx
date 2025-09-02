import { useState, useEffect } from "react";
import { Button } from "./button";
import { Input } from "./input";
import { Label } from "./label";
import { CustomSelect } from "./custom-select";

export function CourseSelector({ value, onChange, className = "" }) {
  const [courses, setCourses] = useState([]);
  const [isCreating, setIsCreating] = useState(false);
  const [newCourseName, setNewCourseName] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const response = await fetch(
        `http://${import.meta.env.VITE_API_BASE_URL}/chat/courses`
      );
      if (response.ok) {
        const data = await response.json();
        setCourses(data.courses || []);
      }
    } catch (error) {
      console.error("Error fetching courses:", error);
    }
  };

  const handleCreateCourse = async () => {
    if (!newCourseName.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(
        `http://${import.meta.env.VITE_API_BASE_URL}/chat/courses`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            title: newCourseName.trim(),
            description: "",
            term: "",
            created_by: "A1",
          }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        const newCourse = data.course;
        if (newCourse) {
          setCourses((prev) => [...prev, newCourse]);
          onChange(newCourse.course_id);
          setNewCourseName("");
          setIsCreating(false);
        }
      }
    } catch (error) {
      console.error("Error creating course:", error);
    } finally {
      setLoading(false);
    }
  };

  const courseOptions = courses.map((course) => ({
    label: course.title,
    value: course.course_id,
  }));

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="space-y-2">
        <Label>Course</Label>
        {!isCreating ? (
          <div className="flex gap-2">
            <div className="flex-1">
              <CustomSelect
                value={value}
                onChange={onChange}
                options={courseOptions}
                placeholder="Select a course"
              />
            </div>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsCreating(true)}
            >
              New
            </Button>
          </div>
        ) : (
          <div className="flex gap-2">
            <div className="flex-1">
              <Input
                value={newCourseName}
                onChange={(e) => setNewCourseName(e.target.value)}
                placeholder="Enter course name"
                onKeyPress={(e) => e.key === "Enter" && handleCreateCourse()}
              />
            </div>
            <Button
              type="button"
              onClick={handleCreateCourse}
              disabled={!newCourseName.trim() || loading}
            >
              {loading ? "Creating..." : "Create"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsCreating(false);
                setNewCourseName("");
              }}
            >
              Cancel
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
