import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useGoogleLogin } from '@react-oauth/google';
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

  const handleGoogleSuccess = async (response) => {
    try {
      // TODO: Implement actual Google authentication logic here
      console.log("Google login success:", response);
      // For now, just navigate based on the selected role
      if (activeTab === "instructor") {
        navigate("/admin");
      } else {
        navigate("/courses");
      }
    } catch (error) {
      setError("Failed to authenticate with Google");
      console.error("Google login error:", error);
    }
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

    // For now, just navigate based on the selected role
    if (activeTab === "instructor") {
      navigate("/admin");
    } else {
      navigate("/courses");
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError(""); // Clear error when user starts typing
  };

  const googleLogin = useGoogleLogin({
    onSuccess: handleGoogleSuccess,
    onError: () => setError("Google login failed"),
  });

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-50 to-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 space-y-8">
        <div className="text-center">
          <h2 className="mt-2 text-3xl font-extrabold text-gray-900">Welcome to Oliver</h2>
          <p className="mt-2 text-sm text-gray-600">Please sign in to continue</p>
        </div>

        <div className="mt-8 space-y-6">
          <div className="flex rounded-md shadow-sm">
            <button
              type="button"
              className={`w-1/2 py-2 px-4 text-sm font-medium rounded-l-md focus:outline-none ${
                activeTab === "student"
                  ? "bg-black text-white"
                  : "bg-white text-gray-700 hover:bg-gray-50"
              }`}
              onClick={() => setActiveTab("student")}
            >
              Student
            </button>
            <button
              type="button"
              className={`w-1/2 py-2 px-4 text-sm font-medium rounded-r-md focus:outline-none ${
                activeTab === "instructor"
                  ? "bg-black text-white"
                  : "bg-white text-gray-700 hover:bg-gray-50"
              }`}
              onClick={() => setActiveTab("instructor")}
            >
              Instructor
            </button>
          </div>

          <Button
            type="button"
            className="w-full flex items-center justify-center gap-2"
            onClick={() => googleLogin()}
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="currentColor"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="currentColor"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="currentColor"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="currentColor"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            Continue with Google
          </Button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or continue with email</span>
            </div>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="rounded-md shadow-sm -space-y-px">
              <div>
                <Label htmlFor="email" className="sr-only">
                  Email address
                </Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className={error ? "border-red-500" : ""}
                  placeholder="Email address"
                  value={formData.email}
                  onChange={handleInputChange}
                />
                <p className="mt-1 text-xs text-gray-500">
                  Use your @gmail.com or @uwaterloo.ca email
                </p>
              </div>
              <div className="mt-4">
                <Label htmlFor="password" className="sr-only">
                  Password
                </Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  placeholder="Password"
                  value={formData.password}
                  onChange={handleInputChange}
                />
              </div>
            </div>

            {error && <p className="text-red-500 text-sm">{error}</p>}

            <Button type="submit" className="w-full">
              Sign in
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
} 