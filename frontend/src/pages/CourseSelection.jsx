import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "../components/ui/card";

export default function CourseSelection() {
  const [inviteCode, setInviteCode] = useState("");
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [courses, setCourses] = useState([]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/course/`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("access_token")}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch courses: ${response.statusText}`);
        }

        const data = await response.json();
        setCourses(data || []);
      } catch (err) {
        console.error("Error fetching courses:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchCourses();
  }, []);

  useEffect(() => {
    // Check if user is authenticated
    const userData = localStorage.getItem("user");
    if (!userData) {
      navigate("/login");
      return;
    }

    const parsedUser = JSON.parse(userData);
    setUser(parsedUser);

    // Redirect instructors/admins to admin panel
    if (parsedUser.role === "instructor" || parsedUser.role === "admin") {
      navigate("/admin");
      return;
    }
  }, [navigate]);

  const handleJoinCourse = (courseId) => {
    if (!courseId) {
      throw new Error("Course ID is required to join a course");
    }
    // console.log("Joining course:", courseId);
    navigate(`/chat?course=${courseId}`);
  };

  const handleInviteCodeSubmit = async (e) => {
    e.preventDefault();
    const code = inviteCode.trim();
    if (!code || code.length !== 6) {
      alert("Please enter a valid 6-digit invite code.");
      return;
    }
    try {
      const formData = new FormData();
      formData.append("invite_code", code);
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/course/join-by-code`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
          body: formData,
        }
      );
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to join: ${response.statusText}`);
      }
      const data = await response.json();

      // Success! Clear the invite code and refresh the courses list
      setInviteCode("");
      alert(
        `Successfully joined "${data.title}"! You can now select it from your courses below.`
      );

      // Refresh courses to show the newly joined course
      try {
        const coursesResponse = await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/course/`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("access_token")}`,
            },
          }
        );
        if (coursesResponse.ok) {
          const coursesData = await coursesResponse.json();
          setCourses(coursesData || []);
        }
      } catch (refreshErr) {
        console.error("Error refreshing courses:", refreshErr);
        // Still show success message even if refresh fails
      }
    } catch (err) {
      console.error("Join by code failed:", err);
      alert(err.message || "Failed to join course");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("access_token");
    navigate("/login");
  };

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div className="text-center flex-1">
            <h2 className="text-3xl font-bold text-gray-900">
              Select a Course
            </h2>
            <p className="mt-2 text-gray-600">
              Welcome back, {user?.username || user?.email}
            </p>
          </div>
          <Button
            onClick={handleLogout}
            variant="outline"
            className="ml-4 text-red-600 border-red-300 hover:bg-red-50 hover:text-red-700"
          >
            Logout
          </Button>
        </div>

        {/* Joined Courses Section */}
        <div className="mb-12">
          <h3 className="text-xl font-semibold mb-4">Your Courses</h3>
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading courses...</p>
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <p className="text-red-600 mb-4">
                Error loading courses: {error}
              </p>
              <Button onClick={() => window.location.reload()}>Retry</Button>
            </div>
          ) : courses.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-600">
                No courses joined yet. Join a course below.
              </p>
            </div>
          ) : (
            <div className="grid gap-4">
              {courses.map((course) => (
                <Card key={course.course_id}>
                  <CardContent className="flex justify-between items-center p-6">
                    <div>
                      <CardTitle className="text-lg">{course.title}</CardTitle>
                      <CardDescription>{course.term}</CardDescription>
                    </div>
                    <Button onClick={() => handleJoinCourse(course.course_id)}>
                      Enter Chat
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Invite Code Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Have an Invite Code?</CardTitle>
            <CardDescription>
              Enter your 6-digit invite code below
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleInviteCodeSubmit} className="space-y-4">
              <div>
                <Label htmlFor="inviteCode">Invite code</Label>
                <Input
                  id="inviteCode"
                  type="text"
                  value={inviteCode}
                  onChange={(e) =>
                    setInviteCode(e.target.value.replace(/\D/g, "").slice(0, 6))
                  }
                  placeholder="e.g. 123456"
                  className="mt-1 block w-full"
                />
              </div>
              <Button type="submit" className="w-full">
                Join via Code
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
