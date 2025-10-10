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
  const [showEmailLogin, setShowEmailLogin] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [verificationCode, setVerificationCode] = useState("");
  const [userEmail, setUserEmail] = useState("");
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

  const handleSendCode = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    // Validate email domain
    if (!validateEmail(formData.email)) {
      setError("Please use a valid @gmail.com or @uwaterloo.ca email address");
      setLoading(false);
      return;
    }

    try {
      console.log("Sending request to /auth/send-code with email:", formData.email);
      const response = await fetch("/auth/send-code", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: formData.email,
        }),
      });

      console.log("Response status:", response.status);
      console.log("Response headers:", response.headers);
      
      const data = await response.json();
      console.log("Response data:", data);

      if (data.success) {
        setUserEmail(formData.email);
        setEmailSent(true);
        setError("");
      } else {
        setError(data.message || "Failed to send verification code");
      }
    } catch (err) {
      console.error("Send code error:", err);
      setError("Failed to send verification code. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      console.log("Sending verification request to /auth/verify-code with email:", userEmail, "code:", verificationCode);
      const response = await fetch("/auth/verify-code", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: userEmail,
          code: verificationCode,
        }),
      });

      console.log("Verification response status:", response.status);
      console.log("Verification response headers:", response.headers);
      
      const data = await response.json();
      console.log("Verification response data:", data);

      if (data.success) {
        // Store auth info in localStorage
        localStorage.setItem("user", JSON.stringify(data.user));

        // Navigate based on user role
        if (data.user.role === "instructor" || data.user.role === "admin") {
          navigate("/admin");
        } else {
          navigate("/courses");
        }
      } else {
        setError(data.message || "Verification failed");
      }
    } catch (err) {
      console.error("Verification error:", err);
      setError("Failed to verify code. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleBackToEmail = () => {
    setEmailSent(false);
    setVerificationCode("");
    setError("");
  };

  const handleBackToGoogle = () => {
    setShowEmailLogin(false);
    setEmailSent(false);
    setVerificationCode("");
    setUserEmail("");
    setError("");
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

        {!showEmailLogin ? (
          // Google Login View
          <>
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

            {/* Email Login Option */}
            <div className="mt-4">
              <Button
                type="button"
                onClick={() => setShowEmailLogin(true)}
                disabled={loading}
                className="w-full bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200 disabled:opacity-50"
              >
                Login by Email
              </Button>
            </div>
          </>
        ) : !emailSent ? (
          // Email Input View
          <>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-medium text-gray-900">Login by Email</h3>
              <Button
                type="button"
                onClick={handleBackToGoogle}
                variant="ghost"
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                ← Back to Google
              </Button>
            </div>

            <form onSubmit={handleSendCode} className="space-y-6">
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

              {error && (
                <div className="text-sm text-red-600 text-center">
                  {error}
                </div>
              )}

              <div>
                <Button type="submit" disabled={loading} className="w-full">
                  {loading ? "Sending..." : "Send Verification Code"}
                </Button>
              </div>
            </form>
          </>
        ) : (
          // Verification Code View
          <>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-medium text-gray-900">Enter Verification Code</h3>
              <Button
                type="button"
                onClick={handleBackToEmail}
                variant="ghost"
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                ← Back to Email
              </Button>
            </div>

            <div className="text-center mb-6">
              <p className="text-sm text-gray-600">
                We sent a verification code to
              </p>
              <p className="font-medium text-gray-900">{userEmail}</p>
            </div>

            <form onSubmit={handleVerifyCode} className="space-y-6">
              <div>
                <Label htmlFor="verificationCode">Verification Code</Label>
                <Input
                  id="verificationCode"
                  name="verificationCode"
                  type="text"
                  required
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  className={`mt-1 ${error ? 'border-red-500' : ''}`}
                  placeholder="Enter 6-digit code"
                  disabled={loading}
                  maxLength={6}
                />
              </div>

              {error && (
                <div className="text-sm text-red-600 text-center">
                  {error}
                </div>
              )}

              <div>
                <Button type="submit" disabled={loading} className="w-full">
                  {loading ? "Verifying..." : "Verify Code"}
                </Button>
              </div>

              <div className="text-center">
                <Button
                  type="button"
                  onClick={handleSendCode}
                  variant="ghost"
                  className="text-sm text-blue-600 hover:text-blue-800"
                  disabled={loading}
                >
                  Resend Code
                </Button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
