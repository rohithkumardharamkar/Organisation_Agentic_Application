import React, { createContext, useContext, useState } from "react";
import { api } from "../lib/api";

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  userEmail: string | null;
  userRole: string | null;
  login: (email: string, pass: string) => Promise<void>;
  otpLogin: (email: string, otp: string) => Promise<void>;
  googleLogin: (email: string, name: string) => Promise<void>;
  signup: (email: string, pass: string, name: string, role?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem("finpilot_token"));
  const [userEmail, setUserEmail] = useState<string | null>(localStorage.getItem("finpilot_email"));
  const [userRole, setUserRole] = useState<string | null>(localStorage.getItem("finpilot_role"));

  const login = async (email: string, pass: string) => {
    const params = new URLSearchParams();
    params.append("username", email);
    params.append("password", pass);
    
    const data = await api.auth.login(params);
    localStorage.setItem("finpilot_token", data.access_token);
    localStorage.setItem("finpilot_email", email);
    localStorage.setItem("finpilot_role", data.user.role || "Employee");
    setToken(data.access_token);
    setUserEmail(email);
    setUserRole(data.user.role || "Employee");
  };

  const otpLogin = async (email: string, otp: string) => {
    const data = await api.auth.otpLogin({ email, otp });
    localStorage.setItem("finpilot_token", data.access_token);
    localStorage.setItem("finpilot_email", email);
    localStorage.setItem("finpilot_role", data.user.role || "Employee");
    setToken(data.access_token);
    setUserEmail(email);
    setUserRole(data.user.role || "Employee");
  };

  const googleLogin = async (email: string, name: string) => {
    const data = await api.auth.googleLogin({ email, name });
    localStorage.setItem("finpilot_token", data.access_token);
    localStorage.setItem("finpilot_email", email);
    localStorage.setItem("finpilot_role", data.user.role || "Employee");
    setToken(data.access_token);
    setUserEmail(email);
    setUserRole(data.user.role || "Employee");
  };

  const signup = async (email: string, pass: string, name: string, role: string = "Employee") => {
    await api.auth.signup({ email, password: pass, full_name: name, role: role });
    await login(email, pass);
  };

  const logout = () => {
    localStorage.removeItem("finpilot_token");
    localStorage.removeItem("finpilot_email");
    localStorage.removeItem("finpilot_role");
    setToken(null);
    setUserEmail(null);
    setUserRole(null);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        isAuthenticated: !!token,
        userEmail,
        userRole,
        login,
        otpLogin,
        googleLogin,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
