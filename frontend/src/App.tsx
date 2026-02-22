import React, { useEffect, useMemo, useState } from 'react'
import { AgentClient, Message } from './api/client'
import { Header } from './components/Header'
import { MessageList } from './components/MessageList'
import { Composer } from './components/Composer'

const presetIntro: Message = {
  role: 'assistant',
  content:
    "Hi! I'm your travel concierge. Tell me where you want to go, your budget, and if you're ready to consent to payment when we find the right option.",
}

function useAgentClient() {
  return useMemo(() => new AgentClient(), [])
}

function useConversation() {
  const [messages, setMessages] = useState<Message[]>([presetIntro])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  return { messages, setMessages, loading, setLoading, error, setError }
}

export default function App() {
  const client = useAgentClient()
  const { messages, setMessages, loading, setLoading, error, setError } = useConversation()

  const send = async (text: string) => {
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)
    setError(null)
    try {
      const res = await client.sendQuery(text)
      if (res.success) {
        setMessages((prev) => [...prev, { role: 'assistant', content: res.response }])
      } else {
        setMessages((prev) => [...prev, { role: 'assistant', content: res.error || 'Something went wrong' }])
      }
    } catch (err: any) {
      setError(err.message || 'Failed to reach agent')
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I could not reach the agent.' }])
    } finally {
      setLoading(false)
    }
  }

  const reset = async () => {
    await client.reset()
    setMessages([presetIntro])
  }

  useEffect(() => {
    // simple keyboard shortcut to reset
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        reset()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: 'radial-gradient(circle at 10% 20%, rgba(34,211,238,0.08), transparent 25%), radial-gradient(circle at 90% 10%, rgba(14,165,233,0.12), transparent 22%), #0b1224',
        color: '#e2e8f0',
        fontFamily: 'Inter, "SF Pro Display", system-ui, -apple-system, sans-serif',
      }}
    >
      <Header />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', maxWidth: '960px', width: '100%', margin: '0 auto' }}>
        {error && (
          <div
            style={{
              margin: '12px 16px 0',
              padding: '10px 12px',
              borderRadius: '10px',
              background: '#7f1d1d',
              color: '#fecdd3',
            }}
          >
            {error}
          </div>
        )}
        <MessageList messages={messages} />
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0 16px 8px', color: '#94a3b8', fontSize: '12px' }}>
          <span>Tip: Say “I consent to pay by card” to trigger the payment flow.</span>
          <button
            onClick={reset}
            style={{
              background: 'transparent',
              border: '1px solid #1f2a44',
              color: '#cbd5e1',
              padding: '6px 10px',
              borderRadius: '10px',
              cursor: 'pointer',
            }}
          >
            Reset (Ctrl/Cmd+K)
          </button>
        </div>
        <Composer onSend={send} disabled={loading} />
      </div>
    </div>
  )
}
