import React from 'react'
import { MessageBubble } from './MessageBubble'
import { Message } from '../api/client'

export function MessageList({ messages }: { messages: Message[] }) {
  return (
    <div
      style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
      }}
    >
      {messages.map((m, idx) => (
        <MessageBubble key={idx} role={m.role} content={m.content} />
      ))}
    </div>
  )
}
