import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { isAuthenticated, hasRole } from '../utils/auth';

const ProtectedRoute = ({ children, requiredRoles = null }) => {
  const navigate = useNavigate();
  const [authState, setAuthState] = useState('checking'); // checking, authorized, denied

  useEffect(() => {
    let mounted = true;

    const checkAccess = async () => {
      if (!isAuthenticated()) {
        navigate('/login');
        return;
      }

      if (requiredRoles && !hasRole(requiredRoles)) {
        const user = JSON.parse(localStorage.getItem('user'));
        if (user?.role === 'instructor' || user?.role === 'admin') {
          navigate('/admin');
        } else {
          navigate('/courses');
        }
        return;
      }

      const requiresInstructor = Array.isArray(requiredRoles)
        ? requiredRoles.includes('instructor')
        : requiredRoles === 'instructor';
      const user = JSON.parse(localStorage.getItem('user'));
      
      if (requiresInstructor && user?.role === 'instructor') {
        try {
          const token = localStorage.getItem('access_token');
          const resp = await fetch('http://localhost:8000/auth/verify-instructor', {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (mounted) {
            setAuthState(resp.ok ? 'authorized' : 'denied');
          }
        } catch (error) {
          if (mounted) {
            setAuthState('denied');
          }
        }
      } else {
        if (mounted) {
          setAuthState('authorized');
        }
      }
    };

    checkAccess();

    return () => {
      mounted = false;
    };
  }, [navigate, requiredRoles]);

  if (!isAuthenticated() || authState === 'checking') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
          <p className="mt-4 text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  if (authState === 'denied') {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    const handleLogout = () => {
      // Clear current auth data
      localStorage.removeItem('user');
      localStorage.removeItem('access_token');
      // Redirect to login
      navigate('/login');
    };

    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Access Denied</h1>
          <p className="text-gray-600 mb-4">
            Your email ({user.email}) is not authorized for instructor access.
          </p>
          <p className="text-gray-600 mb-6">
            Please contact your administrator to be added to the instructor whitelist.
          </p>
          <button
            onClick={handleLogout}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            Logout
          </button>
        </div>
      </div>
    );
  }

  return children;
};

export default ProtectedRoute;