import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";

export default function Login() {
  const [activeTab, setActiveTab] = useState("student");
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const validateEmail = (email) => {
    const allowedDomains = ["@gmail.com", "@uwaterloo.ca"];
    return allowedDomains.some(domain => email.toLowerCase().endsWith(domain));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(""); // Clear any previous errors

    // Validate email domain
    if (!validateEmail(formData.email)) {
      setError("Please use a valid @gmail.com or @uwaterloo.ca email address");
      return;
    }

    // TODO: Implement actual authentication logic here
    console.log("Login attempt for", activeTab, "with data:", formData);
    // For now, just navigate to the appropriate page
    if (activeTab === "instructor") {
      navigate("/admin");
    } else {
      navigate("/chat");
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    // Clear error when user starts typing
    if (name === "email") {
      setError("");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-lg">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-bold text-gray-900">Welcome to Oliver</h2>
          <p className="mt-2 text-sm text-gray-600">Please sign in to continue</p>
        </div>

        {/* Login Type Selector */}
        <div className="flex rounded-lg overflow-hidden border border-gray-200 mt-8">
          <button
            className={`flex-1 py-3 px-4 text-sm font-medium ${
              activeTab === "student"
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-700 hover:bg-gray-50"
            }`}
            onClick={() => setActiveTab("student")}
          >
            Student
          </button>
          <button
            className={`flex-1 py-3 px-4 text-sm font-medium ${
              activeTab === "instructor"
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-700 hover:bg-gray-50"
            }`}
            onClick={() => setActiveTab("instructor")}
          >
            Instructor
          </button>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleInputChange}
                className={`mt-1 ${error ? 'border-red-500' : ''}`}
                placeholder={`Enter your ${activeTab === "instructor" ? "instructor" : "student"} email`}
              />
              {error && (
                <p className="mt-1 text-sm text-red-600">
                  {error}
                </p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Use your @gmail.com or @uwaterloo.ca email
              </p>
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={formData.password}
                onChange={handleInputChange}
                className="mt-1"
                placeholder="Enter your password"
              />
            </div>
          </div>

          <div>
            <Button type="submit" className="w-full">
              Sign in as {activeTab === "instructor" ? "Instructor" : "Student"}
            </Button>
          </div>
        </form>

        <div className="text-center mt-4">
          <a href="#" className="text-sm text-blue-600 hover:text-blue-800">
            Forgot your password?
          </a>
        </div>
      </div>
    </div>
  );
} 