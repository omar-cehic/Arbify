import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';

// Remove hardcoded API_URL - use axios defaults from main.jsx

// Always set the Authorization header on app startup if a token exists
const token = localStorage.getItem('access_token');
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load saved user from localStorage on mount
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        console.log('AuthContext: Attempting to fetch user data with token');
        const response = await axios.get('/api/auth/me');
        console.log('AuthContext: User data fetched successfully:', response.data);
        setUser(response.data);
      } catch (error) {
        console.error('AuthContext: Failed to fetch user data:', error.response?.status, error.response?.data);
        
        // If API call fails, try to use saved user data or logout
        if (error.response?.status === 401) {
          console.log('AuthContext: 401 error - token invalid or expired, logging out');
          logout();
        } else {
          // For other errors, try to use cached user data
          try {
            const savedUser = JSON.parse(localStorage.getItem('user'));
            if (savedUser && savedUser.id) {
              console.log('AuthContext: Using cached user data:', savedUser.username);
              setUser(savedUser);
            } else {
              console.log('AuthContext: No valid cached user data, logging out');
              logout();
            }
          } catch {
            console.log('AuthContext: Failed to parse cached user data, logging out');
            logout();
          }
        }
      } finally {
        setLoading(false);
      }
    };

    const token = localStorage.getItem('access_token');
    console.log('AuthContext: Initializing, token exists:', !!token);
    
    if (token && token !== 'null' && token !== 'undefined') {
      // Only try to fetch user data if we have a valid token
      console.log('AuthContext: Valid token found, fetching user data');
      fetchUserData();
    } else {
      // No token, just set loading to false
      console.log('AuthContext: No valid token found');
      setLoading(false);
    }

    const handleStorage = (event) => {
      if ((event.key === 'user' || event.key === 'access_token') && !event.newValue) {
        console.log('AuthContext: Storage cleared, logging out user');
        setUser(null);
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const login = async (username, password) => {
    try {
      console.log('Attempting login for user:', username);
      // Create form data
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await axios.post('/api/auth/token', formData.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        timeout: 10000 // 10 second timeout
      });
      
      console.log('Login successful, received token and user data');
      const { access_token, user_id, username: uname, email, full_name } = response.data;
      
      // Store token in localStorage and set Authorization header
      localStorage.setItem('access_token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // Create user object and update state/localStorage
      const userObj = { 
        id: user_id, 
        username: uname, 
        email: email,
        full_name: full_name || uname
      };
      
      console.log('Setting user in state and localStorage:', userObj);
      setUser(userObj);
      localStorage.setItem('user', JSON.stringify(userObj));
      return true;
    } catch (error) {
      console.error('Login error:', error);
      // Format error message for better user experience
      let errorMessage = 'Login failed. Please try again.';
      
      if (error.code === 'ECONNABORTED') {
        errorMessage = 'Request timed out. The server might be down or unreachable.';
      } else if (error.code === 'ERR_NETWORK' || !error.response) {
        errorMessage = 'Network error. Please check if the backend server is running.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      throw new Error(errorMessage);
    }
  };

  const register = async (formData) => {
    try {
      console.log('Attempting registration with data:', { ...formData, password: '[REDACTED]' });
      const response = await axios.post('/api/auth/register', formData, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 10000 // 10 second timeout
      });
      console.log('Registration successful:', response.data);
      return response.data;
    } catch (error) {
      console.error('Register error:', error);
      // Format error message for better user experience
      let errorMessage = 'Registration failed. Please try again.';
      
      if (error.code === 'ECONNABORTED') {
        errorMessage = 'Request timed out. The server might be down or unreachable.';
      } else if (error.code === 'ERR_NETWORK' || !error.response) {
        errorMessage = 'Network error. Please check if the backend server is running.';
      } else if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail[0].msg || 'Validation error';
        } else if (typeof error.response.data.detail === 'object') {
          errorMessage = error.response.data.detail.msg || 'Validation error';
        } else {
          errorMessage = error.response.data.detail;
        }
      }
      
      throw new Error(errorMessage);
    }
  };

  const logout = () => {
    console.log('Logging out user');
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const updateUser = (updatedUserData) => {
    console.log('Updating user data:', updatedUserData);
    // Update user in context
    setUser(prev => ({ ...prev, ...updatedUserData }));
    // Update localStorage
    const savedUser = JSON.parse(localStorage.getItem('user'));
    if (savedUser) {
      localStorage.setItem('user', JSON.stringify({
        ...savedUser,
        ...updatedUserData
      }));
    }
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    updateUser,
    isAuthenticated: !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}; 