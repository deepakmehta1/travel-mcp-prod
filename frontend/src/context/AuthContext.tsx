import React, { createContext, useContext, useState, useEffect } from "react";

const DEFAULT_AGENT_URL =
  import.meta.env.VITE_AGENT_URL || "http://localhost:8000";

export type User = {
  email: string;
  phone: string;
  token: string;
};

type AuthContextType = {
  user: User | null;
  loading: boolean;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, phone: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Check if user is logged in on mount
  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const res = await fetch(`${DEFAULT_AGENT_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      throw new Error("Login failed");
    }
    const data = await res.json();
    const userData = {
      email: data.email,
      phone: data.phone,
      token: data.token,
    };
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
  };

  const register = async (name: string, email: string, phone: string, password: string) => {
    const res = await fetch(`${DEFAULT_AGENT_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        email,
        phone,
        password,
      }),
    });
    if (!res.ok) {
      throw new Error("Registration failed");
    }
    const data = await res.json();
    const userData = {
      email: data.email,
      phone: data.phone,
      token: data.token,
    };
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
  };

  const logout = async () => {
    setUser(null);
    localStorage.removeItem("user");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        token: user?.token || null,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
