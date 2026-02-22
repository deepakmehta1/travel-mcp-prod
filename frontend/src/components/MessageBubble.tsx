import React from 'react'

export type MessageBubbleProps = {
  role: 'user' | 'assistant'
  content: string
}

const colors = {
  user: '#0f766e',
  assistant: '#1e293b',
}

export function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === 'user'
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '12px',
      }}
    >
      <div
        style={{
          maxWidth: '70%',
          padding: '12px 14px',
          borderRadius: '14px',
          background: isUser ? colors.user : colors.assistant,
          color: '#f8fafc',
          boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
          lineHeight: 1.5,
          fontSize: '15px',
        }}
      >
        {content}
      </div>
    </div>
  )
}
