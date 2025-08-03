import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";

export default function Login() {
    const [session, setSession] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const [userProfile, setUserProfile] = useState(null);
    const [activeTab, setActiveTab] = useState("student");
    const [formData, setFormData] = useState({
        email: "",
        password: "",
    });
    const navigate = useNavigate();

    const validateEmail = (email) => {
        const allowedDomains = ["@gmail.com", "@uwaterloo.ca"];
        return allowedDomains.some(domain => email.toLowerCase().endsWith(domain));
    };

    // Check session on component mount
    useEffect(() => {
        checkSession();
    }, []);

    // Function to check current session
    const checkSession = async () => {
        try {
            setLoading(true);
            const response = await fetch("http://localhost:8000/auth/email/me", {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (response.ok && data.success && data.user) {
                setSession(data);
                // Navigate based on user role
                if (data.user.role === "instructor") {
                    navigate("/admin");
                } else {
                    navigate("/chat");
                }
            } else {
                setSession(null);
            }
        } catch (error) {
            console.error("Error checking session:", error);
            setSession(null);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(""); // Clear any previous errors

        // Validate email domain
        if (!validateEmail(formData.email)) {
            setError("Please use a valid @gmail.com or @uwaterloo.ca email address");
            return;
        }

        setLoading(true);
        try {
            // First, try to login
            const loginResponse = await fetch("http://localhost:8000/auth/email/login", {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: formData.email,
                    password: formData.password
                })
            });

            const loginData = await loginResponse.json();

            if (loginResponse.ok && loginData.success) {
                // Login successful
                setSession(loginData);
                
                // Navigate based on user role
                if (loginData.user.role === "instructor") {
                    navigate("/admin");
                } else {
                    navigate("/chat");
                }
            } else if (loginResponse.status === 401) {
                // If login fails with 401, try to sign up
                const signupResponse = await fetch("http://localhost:8000/auth/email/signup", {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: formData.email,
                        password: formData.password,
                        username: formData.email.split('@')[0],
                        role: activeTab // Include the selected role
                    })
                });

                const signupData = await signupResponse.json();

                if (signupResponse.ok && signupData.success) {
                    setSession(signupData);
                    // Show success message and navigate
                    setError("Account created successfully! Please check your email for verification.");
                    setTimeout(() => {
                        if (activeTab === "instructor") {
                            navigate("/admin");
                        } else {
                            navigate("/chat");
                        }
                    }, 2000);
                } else {
                    setError(signupData.message || "Failed to create account");
                }
            } else {
                setError(loginData.message || "Failed to sign in");
            }
        } catch (error) {
            console.error("Authentication error:", error);
            setError("Failed to authenticate. Please try again.");
        } finally {
            setLoading(false);
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

    // Function to handle Google sign-in button click
    const handleGoogleSignIn = async () => {
        setError(null);
        setLoading(true);
        
        try {
            console.log("Initiating Google sign-in process");
            
            // The URL that Google will redirect to after authentication
            const redirectUrl = `${window.location.origin}/login`;
            console.log("Using redirect URL:", redirectUrl);
            
            // Add query parameters to track the request and user role
            const timestamp = new Date().getTime();
            const requestId = Math.random().toString(36).substring(2, 15);
            
            // Get the authorization URL from the backend with debugging params
            const authEndpoint = `http://localhost:8000/auth/signin/google?redirect_to=${encodeURIComponent(redirectUrl)}&_t=${timestamp}&_r=${requestId}&role=${activeTab}`;
            console.log("Calling auth endpoint:", authEndpoint);
            
            const response = await fetch(authEndpoint, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache'  // Prevent caching
                }
            });
            
            console.log("Auth response status:", response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`Auth endpoint error: ${response.status}`, errorText);
                throw new Error(`Authentication server error (${response.status}): ${errorText}`);
            }
            
            const data = await response.json();
            console.log("Auth response data:", data);
            
            // Extract the URL where we should redirect the user
            let authUrl;
            if (data?.data?.url) {
                authUrl = data.data.url;
            } else if (data?.url) {
                authUrl = data.url;
            }
            
            if (!authUrl) {
                console.error("No auth URL in response data:", data);
                throw new Error("No authentication URL found in response");
            }
            
            // Redirect the user to the authentication URL
            console.log("Redirecting to:", authUrl);
            window.location.href = authUrl;
            
        } catch (error) {
            console.error("Google sign-in error:", error);
            setError(`Failed to initiate sign-in process: ${error.message}`);
        } finally {
            setLoading(false);  // Ensure loading state is reset
        }
    };

    // Function to handle sign out
    const handleSignOut = async () => {
        try {
            setLoading(true);
            console.log("Signing out...");
            
            const response = await fetch("http://localhost:8000/auth/signout", {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            });
            
            if (response.ok) {
                console.log("Sign out successful");
                setSession(null);
                setUserProfile(null);
                setError(null);
                navigate("/");
            } else {
                const errorData = await response.json();
                setError(errorData.detail || "Failed to sign out");
            }
        } catch (error) {
            console.error("Sign out error:", error);
            setError("Failed to sign out");
        } finally {
            setLoading(false);
        }
    };

    // Render authenticated user view
    if (session) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
                <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-lg">
                    <div className="text-center">
                        <h2 className="text-3xl font-bold text-gray-900">Welcome Back</h2>
                        {session.user && (
                            <div className="mt-4">
                                <p className="font-medium text-lg">
                                    {session.user.full_name || session.user.email}
                                </p>
                                <p className="text-sm text-gray-500 mb-2">{session.user.email}</p>
                                
                                <div className="bg-gray-50 p-3 rounded-md mt-3 text-left">
                                    <p className="text-xs text-gray-500 mb-1">User Profile</p>
                                    <p className="text-sm"><span className="font-medium">Username:</span> {session.user.username}</p>
                                    <p className="text-sm"><span className="font-medium">Role:</span> {session.user.role}</p>
                                </div>
                            </div>
                        )}
                    </div>
                    <div className="flex flex-col space-y-4">
                        <Button onClick={() => navigate("/")}>Go to Dashboard</Button>
                        <Button variant="outline" onClick={handleSignOut}>
                            Sign Out
                        </Button>
                    </div>
                </div>
            </div>
        );
    }

    // Render login view for unauthenticated users
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
                        <Button type="submit" className="w-full" disabled={loading}>
                            {loading ? "Signing in..." : `Sign in as ${activeTab === "instructor" ? "Instructor" : "Student"}`}
                        </Button>
                    </div>
                </form>

                <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-gray-300"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                        <span className="px-2 bg-white text-gray-500">Or continue with</span>
                    </div>
                </div>

                <Button 
                    onClick={handleGoogleSignIn} 
                    className="w-full flex items-center justify-center gap-2" 
                    disabled={loading}
                    variant="google"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" className="w-5 h-5">
                        <path fill="#EA4335" d="M5.26620003,9.76452941 C6.19878754,6.93863203 8.85444915,4.90909091 12,4.90909091 C13.6909091,4.90909091 15.2181818,5.50909091 16.4181818,6.49090909 L19.9090909,3 C17.7818182,1.14545455 15.0545455,0 12,0 C7.27006974,0 3.1977497,2.69829785 1.23999023,6.65002441 L5.26620003,9.76452941 Z"/>
                        <path fill="#34A853" d="M16.0407269,18.0125889 C14.9509167,18.7163016 13.5660892,19.0909091 12,19.0909091 C8.86648613,19.0909091 6.21911939,17.076871 5.27698177,14.2678769 L1.23746264,17.3349879 C3.19279051,21.2936293 7.26500293,24 12,24 C14.9328362,24 17.7353462,22.9573905 19.834192,20.9995801 L16.0407269,18.0125889 Z"/>
                        <path fill="#4A90E2" d="M19.834192,20.9995801 C22.0291676,18.9520994 23.4545455,15.903663 23.4545455,12 C23.4545455,11.2909091 23.3454545,10.5272727 23.1818182,9.81818182 L12,9.81818182 L12,14.4545455 L18.4363636,14.4545455 C18.1187732,16.013626 17.2662994,17.2212117 16.0407269,18.0125889 L19.834192,20.9995801 Z"/>
                        <path fill="#FBBC05" d="M5.27698177,14.2678769 C5.03832634,13.556323 4.90909091,12.7937589 4.90909091,12 C4.90909091,11.2182781 5.03443647,10.4668121 5.26620003,9.76452941 L1.23999023,6.65002441 C0.43658717,8.26043162 0,10.0753848 0,12 C0,13.9195484 0.444780743,15.7301709 1.23746264,17.3349879 L5.27698177,14.2678769 Z"/>
                    </svg>
                    {loading ? 'Signing in...' : `Continue with Google as ${activeTab === "instructor" ? "Instructor" : "Student"}`}
                </Button>

                <div className="text-center mt-4">
                    <a href="#" className="text-sm text-blue-600 hover:text-blue-800">
                        Forgot your password?
                    </a>
                </div>
            </div>
        </div>
    );
}