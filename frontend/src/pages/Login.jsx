import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Login() {
    const [session, setSession] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const [userProfile, setUserProfile] = useState(null);
    const navigate = useNavigate();
    
    // UI Components (same as before)
    const Card = ({ className, ...props }) => (
        <div className={`rounded-lg border bg-white text-gray-900 shadow-sm ${className || ""}`} {...props} />
    );
    
    const CardHeader = ({ className, ...props }) => (
        <div className={`flex flex-col space-y-1.5 p-6 ${className || ""}`} {...props} />
    );
    
    const CardTitle = ({ className, ...props }) => (
        <h3 className={`text-2xl font-semibold leading-none tracking-tight ${className || ""}`} {...props} />
    );
    
    const CardDescription = ({ className, ...props }) => (
        <p className={`text-sm text-gray-500 ${className || ""}`} {...props} />
    );
    
    const CardContent = ({ className, ...props }) => (
        <div className={`p-6 pt-0 ${className || ""}`} {...props} />
    );
    
    const CardFooter = ({ className, ...props }) => (
        <div className={`flex items-center p-6 pt-0 ${className || ""}`} {...props} />
    );
    
    const Button = ({ className, variant = "default", type = "button", disabled = false, ...props }) => {
        const getVariantClass = () => {
            switch(variant) {
                case "google":
                    return "bg-white text-gray-800 border border-gray-300 hover:bg-gray-100";
                case "outline":
                    return "bg-white text-gray-800 border border-gray-300 hover:bg-gray-100";
                default:
                    return "bg-blue-600 text-white hover:bg-blue-700";
            }
        };
        
        return (
            <button
                type={type}
                disabled={disabled || loading}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${getVariantClass()} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className || ""}`}
                {...props}
            />
        );
    };

    // Check session and handle callback parameters on component mount
    useEffect(() => {
        // Check for any callback parameters in the URL
        const url = new URL(window.location.href);
        const code = url.searchParams.get('code');
        const hashParams = new URLSearchParams(url.hash.substring(1));
        
        console.log("URL parameters:", { 
            code: code ? `${code.substring(0, 10)}...` : null,
            hash: Object.fromEntries(hashParams.entries())
        });
        
        // If we have a code or success hash, the user has been redirected back after authentication
        if (code || hashParams.has('success')) {
            console.log("Auth callback detected, checking session...");
        }
        
        // Check if there was an error in the callback
        if (hashParams.has('error')) {
            setError(hashParams.get('error') || 'Authentication failed');
            // Clean the URL
            window.history.replaceState(null, '', window.location.pathname);
        }
        
        // Always check session on mount
        checkSession();
    }, []);

    // Function to check current session
    const checkSession = async () => {
        try {
            setLoading(true);
            console.log("Checking current session...");
            
            const response = await fetch("http://localhost:8000/auth/session", {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            const data = await response.json();
            console.log("Session response:", data);
            
            if (response.ok && data && data.user) {
                console.log("Active session found");
                setSession(data);
                
                // Now fetch user profile details
                fetchUserProfile();
            } else {
                console.log("No active session found");
                setSession(null);
            }
        } catch (error) {
            console.error("Error checking session:", error);
            setSession(null);
        } finally {
            setLoading(false);
        }
    };

    // Function to fetch user profile from database
    const fetchUserProfile = async () => {
        try {
            console.log("Fetching user profile...");
            
            const response = await fetch("http://localhost:8000/user/", {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            const data = await response.json();
            console.log("User profile response:", data);
            
            if (response.ok && data && data.data) {
                setUserProfile(data.data);
            } else if (data.error === "User not found") {
                console.log("User not found in database, will be created by backend");
            }
        } catch (error) {
            console.error("Error fetching user profile:", error);
        }
    };

    // Function to handle Google sign-in button click
// Function to handle Google sign-in button click
const handleGoogleSignIn = async () => {
    setError(null);
    setLoading(true);
    
    try {
        console.log("Initiating Google sign-in process");
        
        // The URL that Google will redirect to after authentication
        const redirectUrl = `${window.location.origin}/login`;
        console.log("Using redirect URL:", redirectUrl);
        
        // Add query parameters to track the request
        const timestamp = new Date().getTime();
        const requestId = Math.random().toString(36).substring(2, 15);
        
        // Get the authorization URL from the backend with debugging params
        const authEndpoint = `http://localhost:8000/auth/signin/google?redirect_to=${encodeURIComponent(redirectUrl)}&_t=${timestamp}&_r=${requestId}`;
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
            <div className="flex items-center justify-center min-h-screen bg-gray-50 p-4">
                <Card className="w-[400px] max-w-full">
                    <CardHeader>
                        <CardTitle>Logged In</CardTitle>
                        <CardDescription>You are successfully logged in with Google.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {session.user && (
                            <div className="text-center mb-4">
                                {session.user.user_metadata?.avatar_url && (
                                    <img 
                                        src={session.user.user_metadata.avatar_url} 
                                        alt="Profile" 
                                        className="rounded-full w-20 h-20 mx-auto mb-3"
                                    />
                                )}
                                <p className="font-medium text-lg">
                                    {session.user.user_metadata?.full_name || session.user.email}
                                </p>
                                <p className="text-sm text-gray-500 mb-2">{session.user.email}</p>
                                
                                {userProfile && (
                                    <div className="bg-gray-50 p-3 rounded-md mt-3 text-left">
                                        <p className="text-xs text-gray-500 mb-1">User Profile</p>
                                        <p className="text-sm"><span className="font-medium">Username:</span> {userProfile.username}</p>
                                        <p className="text-sm"><span className="font-medium">Role:</span> {userProfile.role}</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </CardContent>
                    <CardFooter className="flex justify-between">
                        <Button onClick={() => navigate("/")}>Go to Dashboard</Button>
                        <Button variant="outline" onClick={handleSignOut}>
                            Sign Out
                        </Button>
                    </CardFooter>
                </Card>
            </div>
        );
    }

    // Render login view for unauthenticated users
    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-50 p-4">
            <Card className="w-[350px] max-w-full">
                <CardHeader>
                    <CardTitle>Sign in to WatAI</CardTitle>
                    <CardDescription>Sign in using your Google account</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex flex-col space-y-4">
                        <Button 
                            onClick={handleGoogleSignIn} 
                            className="w-full flex items-center justify-center gap-2" 
                            disabled={loading}
                            variant="google"
                        >
                            {/* Google icon */}
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" className="w-5 h-5">
                                <path fill="#EA4335" d="M5.26620003,9.76452941 C6.19878754,6.93863203 8.85444915,4.90909091 12,4.90909091 C13.6909091,4.90909091 15.2181818,5.50909091 16.4181818,6.49090909 L19.9090909,3 C17.7818182,1.14545455 15.0545455,0 12,0 C7.27006974,0 3.1977497,2.69829785 1.23999023,6.65002441 L5.26620003,9.76452941 Z"/>
                                <path fill="#34A853" d="M16.0407269,18.0125889 C14.9509167,18.7163016 13.5660892,19.0909091 12,19.0909091 C8.86648613,19.0909091 6.21911939,17.076871 5.27698177,14.2678769 L1.23746264,17.3349879 C3.19279051,21.2936293 7.26500293,24 12,24 C14.9328362,24 17.7353462,22.9573905 19.834192,20.9995801 L16.0407269,18.0125889 Z"/>
                                <path fill="#4A90E2" d="M19.834192,20.9995801 C22.0291676,18.9520994 23.4545455,15.903663 23.4545455,12 C23.4545455,11.2909091 23.3454545,10.5272727 23.1818182,9.81818182 L12,9.81818182 L12,14.4545455 L18.4363636,14.4545455 C18.1187732,16.013626 17.2662994,17.2212117 16.0407269,18.0125889 L19.834192,20.9995801 Z"/>
                                <path fill="#FBBC05" d="M5.27698177,14.2678769 C5.03832634,13.556323 4.90909091,12.7937589 4.90909091,12 C4.90909091,11.2182781 5.03443647,10.4668121 5.26620003,9.76452941 L1.23999023,6.65002441 C0.43658717,8.26043162 0,10.0753848 0,12 C0,13.9195484 0.444780743,15.7301709 1.23746264,17.3349879 L5.27698177,14.2678769 Z"/>
                            </svg>
                            {loading ? 'Signing in...' : 'Sign in with Google'}
                        </Button>
                        
                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-600 px-3 py-2 rounded-md text-sm">
                                {error}
                            </div>
                        )}
                    </div>
                </CardContent>
                <CardFooter>
                    <p className="text-xs text-gray-500 w-full text-center">
                        By continuing, you agree to our Terms of Service and Privacy Policy
                    </p>
                </CardFooter>
            </Card>
        </div>
    );
}