import { useState, useRef, useEffect, Fragment, KeyboardEvent } from "react";
import { AdminAgentClient, Message } from "../api/client";

interface ChatInterfaceProps {
  client: AdminAgentClient;
}

export const ChatInterface = ({ client }: ChatInterfaceProps) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I'm your administrative AI assistant. I can help you with bookings, customers, tours, and revenue reports. What would you like to know?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      let streamedResponse = "";
      
      // Add empty assistant message
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
      
      for await (const chunk of client.streamQuery(userMessage)) {
        streamedResponse += chunk;
        setMessages((prev) => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1] = {
            role: "assistant",
            content: streamedResponse,
          };
          return newMessages;
        });
      }
    } catch (error: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${error.message}. Please make sure the admin agent is running.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-bubble">
              {msg.content.split('\n').map((line, i) => (
                <Fragment key={i}>
                  {line}
                  {i < msg.content.split('\n').length - 1 && <br />}
                </Fragment>
              ))}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about bookings, customers, tours, or revenue..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          {loading ? <span className="loading"></span> : "Send"}
        </button>
      </div>
    </div>
  );
};
