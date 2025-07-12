import React, { useState } from "react";
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
  const navigate = useNavigate();
  
  // Mock courses data - replace with actual API call
  const [courses] = useState([
    { id: 1, name: "ECE 250 - Algorithms and Data Structures", term: "Winter 2024" },
    { id: 2, name: "ECE 198 - Programming for Engineers", term: "Winter 2024" },
  ]);

  const handleJoinCourse = (courseId) => {
    // TODO: Implement actual course joining logic here
    console.log("Joining course:", courseId);
    navigate(`/chat?course=${courseId}`);
  };

  const handleInviteLinkSubmit = (e) => {
    e.preventDefault();
    // TODO: Implement actual invite link validation and joining logic
    if (inviteLink.trim()) {
      console.log("Joining via invite link:", inviteLink);
      navigate("/chat");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Select a Course</h2>
          <p className="mt-2 text-gray-600">Join an existing course or enter an invite link</p>
        </div>

        {/* Available Courses Section */}
        <div className="mb-12">
          <h3 className="text-xl font-semibold mb-4">Available Courses</h3>
          <div className="grid gap-4">
            {courses.map((course) => (
              <Card key={course.id}>
                <CardContent className="flex justify-between items-center p-6">
                  <div>
                    <CardTitle className="text-lg">{course.name}</CardTitle>
                    <CardDescription>{course.term}</CardDescription>
                  </div>
                  <Button onClick={() => handleJoinCourse(course.id)}>
                    Join Course
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
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