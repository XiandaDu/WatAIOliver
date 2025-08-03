export const getStoredUser = () => {
  const userData = localStorage.getItem('user');
  return userData ? JSON.parse(userData) : null;
};

export const getAccessToken = () => {
  return localStorage.getItem('access_token');
};

export const isAuthenticated = () => {
  return getStoredUser() !== null;
};

export const hasRole = (requiredRoles) => {
  const user = getStoredUser();
  if (!user) return false;
  
  if (Array.isArray(requiredRoles)) {
    return requiredRoles.includes(user.role);
  }
  
  return user.role === requiredRoles;
};

export const isInstructor = () => {
  return hasRole(['instructor', 'admin']);
};

export const isAdmin = () => {
  return hasRole('admin');
};

export const logout = () => {
  localStorage.removeItem('user');
  localStorage.removeItem('access_token');
  window.location.href = '/login';
};

export const makeAuthenticatedRequest = async (url, options = {}) => {
  const token = getAccessToken();
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  if (response.status === 401) {
    logout();
    throw new Error('Authentication failed');
  }
  
  return response;
};