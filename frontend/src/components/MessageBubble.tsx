import React from "react";
import ReactMarkdown from "react-markdown";

export type MessageBubbleProps = {
  role: "user" | "assistant";
  content: string;
};

const colors = {
  user: "#0f766e",
  assistant: "#1e293b",
};

export function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === "user";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "12px",
      }}
    >
      <div
        style={{
          maxWidth: "70%",
          padding: "12px 14px",
          borderRadius: "14px",
          background: isUser ? colors.user : colors.assistant,
          color: "#f8fafc",
          boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
          lineHeight: 1.5,
          fontSize: "15px",
          whiteSpace: "pre-wrap",
          wordWrap: "break-word",
        }}
      >
        <ReactMarkdown
          components={{
            p: ({ children }) => <p style={{ margin: "4px 0" }}>{children}</p>,
            strong: ({ children }) => (
              <strong style={{ fontWeight: "bold" }}>{children}</strong>
            ),
            em: ({ children }) => (
              <em style={{ fontStyle: "italic" }}>{children}</em>
            ),
            ol: ({ children }) => (
              <ol style={{ margin: "8px 0", paddingLeft: "20px" }}>
                {children}
              </ol>
            ),
            ul: ({ children }) => (
              <ul style={{ margin: "8px 0", paddingLeft: "20px" }}>
                {children}
              </ul>
            ),
            li: ({ children }) => (
              <li style={{ marginBottom: "4px" }}>{children}</li>
            ),
            code: ({ children }) => (
              <code
                style={{
                  backgroundColor: "rgba(255,255,255,0.1)",
                  padding: "2px 4px",
                  borderRadius: "3px",
                }}
              >
                {children}
              </code>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
