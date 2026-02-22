import React, { useState } from 'react'

export function Composer({ onSend, disabled }: { onSend: (text: string) => void; disabled?: boolean }) {
  const [text, setText] = useState('')

  const submit = () => {
    const trimmed = text.trim()
    if (!trimmed) return
    onSend(trimmed)
    setText('')
  }

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div
      style={{
        borderTop: '1px solid #0f172a1a',
        padding: '12px 16px',
        background: '#0b1224',
      }}
    >
      <div
        style={{
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-end',
        }}
      >
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask anything about booking, or provide consent to pay..."
          style={{
            flex: 1,
            minHeight: '72px',
            padding: '12px',
            borderRadius: '12px',
            border: '1px solid #1f2a44',
            background: '#0f172a',
            color: '#e2e8f0',
            resize: 'vertical',
            fontSize: '15px',
            lineHeight: 1.5,
            fontFamily: 'Inter, "SF Pro Display", system-ui, -apple-system, sans-serif',
          }}
          disabled={disabled}
        />
        <button
          onClick={submit}
          disabled={disabled}
          style={{
            padding: '12px 18px',
            borderRadius: '12px',
            border: 'none',
            background: '#22d3ee',
            color: '#0f172a',
            fontWeight: 700,
            cursor: disabled ? 'not-allowed' : 'pointer',
            boxShadow: '0 10px 30px rgba(34, 211, 238, 0.3)',
            transition: 'transform 120ms ease, box-shadow 120ms ease',
          }}
        >
          Send
        </button>
      </div>
    </div>
  )
}
