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
  const [inviteLink, setInviteLink] = useState("");
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [courses, setCourses] = useState([]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const response = await fetch('http://localhost:8000/course/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
        
        if (!response.ok) {
          throw new Error(`Failed to fetch courses: ${response.statusText}`);
        }
        
        const data = await response.json();
        setCourses(data || []);
      } catch (err) {
        console.error('Error fetching courses:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchCourses();
  }, []);

  useEffect(() => {
    // Check if user is authenticated
    const userData = localStorage.getItem('user');
    if (!userData) {
      navigate('/login');
      return;
    }
    
    const parsedUser = JSON.parse(userData);
    setUser(parsedUser);
    
    // Redirect instructors/admins to admin panel
    if (parsedUser.role === 'instructor' || parsedUser.role === 'admin') {
      navigate('/admin');
      return;
    }
  }, [navigate]);

  const handleJoinCourse = (courseId) => {
    if (!courseId) {
      throw new Error('Course ID is required to join a course');
    }
    console.log("Joining course:", courseId);
    navigate(`/chat?course=${courseId}`);
  };

  const handleInviteLinkSubmit = (e) => {
    e.preventDefault();
    if (!inviteLink.trim()) {
      throw new Error('Invite link cannot be empty');
    }
    throw new Error('Invite link functionality not implemented - API endpoint required');
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('access_token');
    navigate('/login');
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
            <h2 className="text-3xl font-bold text-gray-900">Select a Course</h2>
            <p className="mt-2 text-gray-600">Welcome back, {user?.username || user?.email}</p>
          </div>
          <Button
            onClick={handleLogout}
            variant="outline"
            className="ml-4"
          >
            Logout
          </Button>
        </div>

        {/* Available Courses Section */}
        <div className="mb-12">
          <h3 className="text-xl font-semibold mb-4">Available Courses</h3>
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading courses...</p>
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <p className="text-red-600 mb-4">Error loading courses: {error}</p>
              <Button onClick={() => window.location.reload()}>
                Retry
              </Button>
            </div>
          ) : courses.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-600">No courses available. Contact your administrator.</p>
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
                      Join Course
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Invite Link Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Have an Invite Link?</CardTitle>
            <CardDescription>Enter your course invite link below</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleInviteLinkSubmit} className="space-y-4">
              <div>
                <Label htmlFor="inviteLink">Enter your invite link</Label>
                <Input
                  id="inviteLink"
                  type="text"
                  value={inviteLink}
                  onChange={(e) => setInviteLink(e.target.value)}
                  placeholder="Paste your invite link here"
                  className="mt-1 block w-full"
                />
              </div>
              <Button type="submit" className="w-full">
                Join via Invite Link
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}