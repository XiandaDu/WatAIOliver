import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useGoogleLogin } from "@react-oauth/google";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";

export default function Login() {
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState("student");
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Check for suggested login type from URL parameters
  useEffect(() => {
    const suggested = searchParams.get("suggested");
    if (suggested === "student") {
      setActiveTab("student");
    } else if (suggested === "instructor") {
      setActiveTab("instructor");
    }
  }, [searchParams]);

  const validateEmail = (email) => {
    const allowedDomains = ["@gmail.com", "@uwaterloo.ca"];
    return allowedDomains.some((domain) =>
      email.toLowerCase().endsWith(domain)
    );
  };

  const handleGoogleSuccess = async (tokenResponse) => {
    setLoading(true);
    setError("");

    try {
      // Send the access token to our backend
      const response = await fetch("/auth/google", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          access_token: tokenResponse.access_token,
          account_type: activeTab,
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Store auth info in localStorage
        if (data.access_token) {
          localStorage.setItem("access_token", data.access_token);
        }
        localStorage.setItem("user", JSON.stringify(data.user));

        // Navigate based on user role
        if (data.user.role === "instructor" || data.user.role === "admin") {
          navigate("/admin");
        } else {
          navigate("/courses");
        }
      } else {
        setError(data.message || "Authentication failed");
      }
    } catch (err) {
      console.error("Authentication error:", err);
      setError("Failed to authenticate. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = useGoogleLogin({
    onSuccess: handleGoogleSuccess,
    onError: () => {
      setError("Failed to login with Google. Please try again.");
      setLoading(false);
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    setError("");

    // Validate email domain
    if (!validateEmail(formData.email)) {
      setError("Please use a valid @gmail.com or @uwaterloo.ca email address");
      return;
    }

    // For now, redirect to Google OAuth since we're focusing on Google SSO
    setError("Please use Google Sign-In for authentication");
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (name === "email") {
      setError("");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-lg">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            Welcome to Oliver
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Please sign in to continue
          </p>
        </div>

        {/* Login Type Selector */}
        <div className="flex rounded-lg overflow-hidden border border-gray-200 mt-8">
          <button
            className={`flex-1 py-3 px-4 text-sm font-medium ${
              activeTab === "student"
                ? "bg-black text-white"
                : "bg-white text-gray-700 hover:bg-gray-50"
            }`}
            onClick={() => setActiveTab("student")}
            disabled={loading}
          >
            Student
          </button>
          <button
            className={`flex-1 py-3 px-4 text-sm font-medium ${
              activeTab === "instructor"
                ? "bg-black text-white"
                : "bg-white text-gray-700 hover:bg-gray-50"
            }`}
            onClick={() => setActiveTab("instructor")}
            disabled={loading}
          >
            Instructor
          </button>
        </div>

        {/* Google SSO Button */}
        <div>
          <Button
            type="button"
            onClick={() => {
              setLoading(true);
              loginWithGoogle();
            }}
            disabled={loading}
            className="w-full bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 disabled:opacity-50"
          >
            <img
              src="https://www.google.com/favicon.ico"
              alt="Google"
              className="w-5 h-5 mr-2"
            />
            {loading
              ? "Signing in..."
              : `Continue with Google as ${
                  activeTab === "instructor" ? "Instructor" : "Student"
                }`}
          </Button>
        </div>

        {/*
         * Email login temporarily disabled for cleaner UI. Email/password login can be re-enabled
         * when needed by uncommenting this section.
         */}
        {/*
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-gray-500">Or continue with email</span>
          </div>
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
                disabled={loading}
              />
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
                disabled={loading}
              />
            </div>
          </div>

          {error && (
            <div className="text-sm text-red-600 text-center">
              {error}
            </div>
          )}

          <div>
            <Button type="submit" disabled={loading} className="w-full">
              Sign in as {activeTab === "instructor" ? "Instructor" : "Student"}
            </Button>
          </div>
        </form>

        <div className="text-center mt-4">
          <a href="#" className="text-sm text-blue-600 hover:text-blue-800">
            Forgot your password?
          </a>
        </div>
        */}
      </div>
    </div>
  );
}
