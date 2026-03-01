import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";

export function Register({ onSwitchToLogin }: { onSwitchToLogin: () => void }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!name || !email || !phone || !password) {
      setError("Please fill in all fields");
      return;
    }
    setLoading(true);

    try {
      await register(name, email, phone, password);
    } catch (err: any) {
      setError(err.message || "Registration failed");
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
          Create Account
        </h1>
        <p
          style={{
            fontSize: "14px",
            color: "#94a3b8",
            textAlign: "center",
            marginBottom: "24px",
          }}
        >
          Sign up to start booking travels
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
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
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
              placeholder="Your full name"
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
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
                Phone Number
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
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
                placeholder="+1 (555) 000-0000"
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
              {loading ? "Registering..." : "Create Account"}
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
          Already have an account?{" "}
          <button
            onClick={onSwitchToLogin}
            style={{
              background: "none",
              border: "none",
              color: "#22d3ee",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Sign in here
          </button>
        </div>
      </div>
    </div>
  );
}
