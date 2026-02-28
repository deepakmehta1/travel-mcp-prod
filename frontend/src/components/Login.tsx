import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";

export function Login({
  onSwitchToRegister,
}: {
  onSwitchToRegister: () => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: "400px",
        margin: "0 auto",
        padding: "40px 20px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        minHeight: "100vh",
      }}
    >
      <div
        style={{
          background: "rgba(15, 23, 42, 0.8)",
          border: "1px solid #1e293b",
          borderRadius: "12px",
          padding: "32px",
          backdropFilter: "blur(10px)",
        }}
      >
        <h1
          style={{
            fontSize: "28px",
            fontWeight: 800,
            marginBottom: "8px",
            textAlign: "center",
          }}
        >
          Welcome Back
        </h1>
        <p
          style={{
            fontSize: "14px",
            color: "#94a3b8",
            textAlign: "center",
            marginBottom: "24px",
          }}
        >
          Sign in to continue your travel booking
        </p>

        <form
          onSubmit={handleSubmit}
          style={{ display: "flex", flexDirection: "column", gap: "16px" }}
        >
          <div>
            <label
              style={{
                display: "block",
                marginBottom: "6px",
                fontSize: "14px",
                fontWeight: 600,
              }}
            >
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{
                width: "100%",
                padding: "10px 12px",
                background: "#0f1419",
                border: "1px solid #1e293b",
                borderRadius: "8px",
                color: "#e2e8f0",
                fontSize: "14px",
                boxSizing: "border-box",
              }}
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label
              style={{
                display: "block",
                marginBottom: "6px",
                fontSize: "14px",
                fontWeight: 600,
              }}
            >
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: "100%",
                padding: "10px 12px",
                background: "#0f1419",
                border: "1px solid #1e293b",
                borderRadius: "8px",
                color: "#e2e8f0",
                fontSize: "14px",
                boxSizing: "border-box",
              }}
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div
              style={{
                padding: "10px",
                background: "#7f1d1d",
                border: "1px solid #d32f2f",
                borderRadius: "8px",
                color: "#fecdd3",
                fontSize: "14px",
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: "12px",
              background: "linear-gradient(135deg, #0ea5e9, #22d3ee)",
              color: "#0b1224",
              border: "none",
              borderRadius: "8px",
              fontWeight: 600,
              fontSize: "14px",
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.5 : 1,
            }}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div
          style={{
            marginTop: "20px",
            paddingTop: "20px",
            borderTop: "1px solid #1e293b",
            textAlign: "center",
            fontSize: "14px",
            color: "#94a3b8",
          }}
        >
          Don't have an account?{" "}
          <button
            onClick={onSwitchToRegister}
            style={{
              background: "none",
              border: "none",
              color: "#22d3ee",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Register here
          </button>
        </div>
      </div>
    </div>
  );
}
