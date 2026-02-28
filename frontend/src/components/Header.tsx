import React from "react";

export function Header() {
  return (
    <header
      style={{
        padding: "16px 20px",
        background: "linear-gradient(135deg, #0ea5e9, #22d3ee)",
        color: "#0b1224",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        boxShadow: "0 12px 30px rgba(14,165,233,0.35)",
      }}
    >
      <div>
        <div
          style={{
            fontWeight: 800,
            fontSize: "18px",
            letterSpacing: "-0.02em",
          }}
        >
          Travel Concierge
        </div>
        <div style={{ opacity: 0.8, fontSize: "13px" }}>
          MCP multi-agent • Booking + Payment
        </div>
      </div>
      <div
        style={{
          display: "flex",
          gap: "10px",
          alignItems: "center",
          fontSize: "12px",
          fontWeight: 600,
        }}
      >
        <span
          style={{
            background: "#0b1224",
            color: "#22d3ee",
            padding: "6px 10px",
            borderRadius: "10px",
          }}
        >
          Live
        </span>
      </div>
    </header>
  );
}
