import React from "react";
import ReactMarkdown from "react-markdown";

export type MessageBubbleProps = {
  role: "user" | "assistant";
  content: string;
};

const colors = {
  user: "#0ea5e9",
  assistant: "#e2e8f0",
  userIconBg: "#0f172a",
  assistantIconBg: "#0f172a",
};

export function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === "user";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "16px",
        gap: "10px",
        alignItems: "flex-start",
      }}
    >
      {!isUser && (
        <div
          style={{
            width: "28px",
            height: "28px",
            borderRadius: "50%",
            background: colors.assistantIconBg,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#38bdf8",
            fontSize: "14px",
            border: "1px solid #1f2a44",
          }}
        >
          A
        </div>
      )}
      <div
        style={{
          maxWidth: "70%",
          padding: "0",
          borderRadius: "0",
          background: "transparent",
          color: isUser ? colors.user : colors.assistant,
          lineHeight: 1.6,
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
                  backgroundColor: "rgba(14,165,233,0.15)",
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
      {isUser && (
        <div
          style={{
            width: "28px",
            height: "28px",
            borderRadius: "50%",
            background: colors.userIconBg,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#22d3ee",
            fontSize: "14px",
            border: "1px solid #1f2a44",
          }}
        >
          U
        </div>
      )}
    </div>
  );
}
