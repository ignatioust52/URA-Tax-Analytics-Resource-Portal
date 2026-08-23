"use client";
import { useState, useRef, useEffect } from 'react';
import { AdminGuard } from '../../components/AdminGuard';

export default function ChatPage() {
  const [messages, setMessages] = useState<{role: 'user' | 'assistant', content: string}[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    const newMessages = [...messages, { role: 'user', content: userMessage } as const];
    setMessages(newMessages);
    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMessage, 
          history: messages.map(m => ({ role: m.role, content: m.content })) 
        }),
      });

      if (!res.ok) throw new Error('Unauthorized or Server Error');
      const data = await res.json();
      
      setMessages([...newMessages, { role: 'assistant', content: data.reply }]);
    } catch (err) {
      setMessages([...newMessages, { role: 'assistant', content: 'Error: Could not reach the AI Assistant. Please ensure you are logged in.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AdminGuard>
      <main className="main-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h1 className="header-title" style={{ fontSize: '1.5rem', margin: 0 }}>URA AI Assistant</h1>
        </div>
        <a href="/" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>← Dashboard</a>
      </div>

      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 0 }}>
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: '40px' }}>
              <div style={{ fontSize: '2rem', marginBottom: '16px' }}>🤖</div>
              <h3>How can I help you today?</h3>
              <p>Ask me about tax codes, resources, or dashboard data.</p>
            </div>
          ) : (
            messages.map((m, idx) => (
              <div key={idx} style={{ 
                alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                background: m.role === 'user' ? '#3b82f6' : 'rgba(255,255,255,0.1)',
                padding: '12px 16px',
                borderRadius: '16px',
                borderBottomRightRadius: m.role === 'user' ? '4px' : '16px',
                borderBottomLeftRadius: m.role === 'assistant' ? '4px' : '16px',
                maxWidth: '80%',
                color: 'white',
                lineHeight: '1.5'
              }}>
                {m.content}
              </div>
            ))
          )}
          {loading && (
            <div style={{ alignSelf: 'flex-start', background: 'rgba(255,255,255,0.1)', padding: '12px 16px', borderRadius: '16px', color: 'var(--text-secondary)' }}>
              Thinking...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSend} style={{ display: 'flex', padding: '16px', borderTop: '1px solid var(--border)', background: 'rgba(0,0,0,0.2)' }}>
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            style={{ flex: 1, padding: '12px 16px', borderRadius: '24px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.3)', color: 'white', marginRight: '16px' }}
            disabled={loading}
          />
          <button type="submit" className="btn-primary" style={{ borderRadius: '24px', padding: '12px 24px' }} disabled={loading}>
            Send
          </button>
        </form>
      </div>
      </main>
    </AdminGuard>
  );
}
