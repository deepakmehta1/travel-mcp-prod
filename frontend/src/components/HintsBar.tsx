import React from "react";

export function HintsBar({
  hints,
  onSend,
  disabled,
}: {
  hints: string[];
  onSend: (text: string) => void;
  disabled?: boolean;
}) {
  if (!hints || !hints.length) return null;

  return (
    <div
      style={{
        display: "flex",
        gap: "8px",
        flexWrap: "wrap",
        padding: "8px 16px",
        background: "#0b1224",
        borderTop: "1px solid #1f2a44",
      }}
    >
      {hints.map((h, i) => (
        <button
          key={`${h}-${i}`}
          onClick={() => onSend(h)}
          disabled={disabled}
          style={{
            padding: "6px 10px",
            borderRadius: "999px",
            border: "1px solid #1f2a44",
            background: "transparent",
            color: "#cbd5e1",
            cursor: disabled ? "not-allowed" : "pointer",
            fontSize: "12px",
            lineHeight: 1.4,
          }}
        >
          {h}
        </button>
      ))}
    </div>
  );
}
