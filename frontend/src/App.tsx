import React, { useEffect, useMemo, useState } from "react";
import { AgentClient, Message } from "./api/client";
import { Header } from "./components/Header";
import { MessageList } from "./components/MessageList";
import { Composer } from "./components/Composer";
import { Login } from "./components/Login";
import { Register } from "./components/Register";
import { useAuth } from "./context/AuthContext";

const presetIntro: Message = {
  role: "assistant",
  content:
    "Hi! I'm your travel concierge. Tell me where you want to go, your budget, and if you're ready to consent to payment when we find the right option.",
};

function useAgentClient(token: string | null) {
  return useMemo(() => new AgentClient(undefined, token), [token]);
}

function useConversation() {
  const [messages, setMessages] = useState<Message[]>([presetIntro]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  return { messages, setMessages, loading, setLoading, error, setError };
}

function ChatInterface({ token }: { token: string | null }) {
  const client = useAgentClient(token);
  const { messages, setMessages, loading, setLoading, error, setError } =
    useConversation();

  const send = async (text: string) => {
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    setError(null);
    let streamed = "";
    try {
      for await (const chunk of client.streamQuery(text)) {
        for (const ch of chunk) {
          streamed += ch;
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last && last.role === "assistant") {
              copy[copy.length - 1] = { role: "assistant", content: streamed };
            } else {
              copy.push({ role: "assistant", content: streamed });
            }
            return copy;
          });
        }
      }
      setMessages((prev) => {
        const copy = [...prev];
        // finalize streaming message
        const last = copy[copy.length - 1];
        if (last && last.role === "assistant") {
          copy[copy.length - 1] = {
            role: "assistant",
            content: streamed || last.content,
          };
        } else {
          copy.push({ role: "assistant", content: streamed });
        }
        return copy;
      });
    } catch (err: any) {
      setError(err.message || "Failed to reach agent");
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I could not reach the agent." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const reset = async () => {
    await client.reset();
    setMessages([presetIntro]);
  };

  useEffect(() => {
    // simple keyboard shortcut to reset
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        reset();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        background:
          "radial-gradient(circle at 10% 20%, rgba(34,211,238,0.08), transparent 25%), radial-gradient(circle at 90% 10%, rgba(14,165,233,0.12), transparent 22%), #0b1224",
        color: "#e2e8f0",
        fontFamily:
          'Inter, "SF Pro Display", system-ui, -apple-system, sans-serif',
      }}
    >
      <Header />
      <div
        style={{
          flex: 1,
          display: "flex",
          width: "100%",
          maxWidth: "960px",
          margin: "0 auto",
        }}
      >
        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          {error && (
            <div
              style={{
                margin: "12px 16px 0",
                padding: "10px 12px",
                borderRadius: "10px",
                background: "#7f1d1d",
                color: "#fecdd3",
              }}
            >
              {error}
            </div>
          )}
          <MessageList messages={messages} />
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "0 16px 8px",
              color: "#94a3b8",
              fontSize: "12px",
            }}
          >
            <span>
              Tip: Say “I consent to pay by card” to trigger the payment flow.
            </span>
            <button
              onClick={reset}
              style={{
                background: "transparent",
                border: "1px solid #1f2a44",
                color: "#cbd5e1",
                padding: "6px 10px",
                borderRadius: "10px",
                cursor: "pointer",
              }}
            >
              Reset (Ctrl/Cmd+K)
            </button>
          </div>
          <Composer onSend={send} disabled={loading} />
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const { user, loading } = useAuth();
  const [authView, setAuthView] = useState<"login" | "register">("login");

  if (loading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background:
            "radial-gradient(circle at 10% 20%, rgba(34,211,238,0.08), transparent 25%), radial-gradient(circle at 90% 10%, rgba(14,165,233,0.12), transparent 22%), #0b1224",
          color: "#e2e8f0",
        }}
      >
        <div>Loading...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div
        style={{
          minHeight: "100vh",
          background:
            "radial-gradient(circle at 10% 20%, rgba(34,211,238,0.08), transparent 25%), radial-gradient(circle at 90% 10%, rgba(14,165,233,0.12), transparent 22%), #0b1224",
          color: "#e2e8f0",
          fontFamily:
            'Inter, "SF Pro Display", system-ui, -apple-system, sans-serif',
        }}
      >
        {authView === "login" ? (
          <Login onSwitchToRegister={() => setAuthView("register")} />
        ) : (
          <Register onSwitchToLogin={() => setAuthView("login")} />
        )}
      </div>
    );
  }

  return <ChatInterface token={user.token} />;
}
