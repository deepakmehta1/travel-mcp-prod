import React from 'react'

const cards = [
  {
    title: 'Find a Trip',
    prompt: 'I want to look for a trip.',
    description: 'Start a new search by destination and budget.',
  },
  {
    title: 'My Bookings',
    prompt: 'Show me my bookings.',
    description: 'View existing bookings on your profile.',
  },
  {
    title: 'Best Upcoming Trips',
    prompt: 'Tell me the best trips you have in upcoming months.',
    description: 'Get top picks for the next 3 months.',
  },
]

export function LaunchCards({ onSend, disabled }: { onSend: (text: string) => void; disabled?: boolean }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '12px',
        padding: '12px 16px 0',
      }}
    >
      {cards.map((card) => (
        <button
          key={card.title}
          onClick={() => onSend(card.prompt)}
          disabled={disabled}
          style={{
            textAlign: 'left',
            padding: '14px',
            borderRadius: '14px',
            border: '1px solid #1f2a44',
            background: 'rgba(15, 23, 42, 0.9)',
            color: '#e2e8f0',
            cursor: disabled ? 'not-allowed' : 'pointer',
            boxShadow: '0 10px 24px rgba(0,0,0,0.18)',
          }}
        >
          <div style={{ fontSize: '15px', fontWeight: 700, marginBottom: '6px' }}>
            {card.title}
          </div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>{card.description}</div>
        </button>
      ))}
    </div>
  )
}
