"use client";
import { useState, useRef, useEffect } from 'react';
import { AdminGuard } from '../../components/AdminGuard';
import { apiFetch } from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';

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
      const data = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMessage, 
          history: messages.map(m => ({ role: m.role, content: m.content })) 
        }),
      });

      setMessages([...newMessages, { role: 'assistant', content: data.reply }]);
    } catch (err) {
      setMessages([...newMessages, { role: 'assistant', content: 'Error: Could not reach the AI Assistant. Please ensure you are logged in.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AdminGuard>
      <main className="main-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: 'var(--space-4)' }}>
      <div className="flex-between" style={{ marginBottom: 'var(--space-4)' }}>
        <div>
          <h1 className="page-title" style={{ margin: 0, fontSize: '1.5rem' }}>URA AI Assistant</h1>
        </div>
        <Button as="a" href="/" variant="secondary">← Dashboard</Button>
      </div>

      <Card noPadding style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {messages.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: 'var(--space-6)' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-3)' }}>🤖</div>
              <h3 style={{ color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>How can I help you today?</h3>
              <p>Ask me about tax codes, resources, or dashboard data.</p>
            </div>
          ) : (
            messages.map((m, idx) => (
              <div key={idx} style={{ 
                alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                background: m.role === 'user' ? 'var(--ura-blue)' : 'var(--surface-hover)',
                padding: '12px 16px',
                borderRadius: 'var(--radius-lg)',
                borderBottomRightRadius: m.role === 'user' ? '4px' : 'var(--radius-lg)',
                borderBottomLeftRadius: m.role === 'assistant' ? '4px' : 'var(--radius-lg)',
                maxWidth: '80%',
                color: m.role === 'user' ? 'var(--text-inverse)' : 'var(--text-primary)',
                lineHeight: '1.5',
                fontSize: '0.95rem'
              }}>
                {m.content}
              </div>
            ))
          )}
          {loading && (
            <div style={{ alignSelf: 'flex-start', background: 'var(--surface-hover)', padding: '12px 16px', borderRadius: 'var(--radius-lg)', color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
              Thinking...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSend} style={{ display: 'flex', padding: 'var(--space-3)', borderTop: '1px solid var(--border-light)', background: 'var(--surface)' }}>
          <div style={{ flex: 1, marginRight: 'var(--space-3)' }}>
            <Input 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              disabled={loading}
              style={{ marginBottom: 0 }}
            />
          </div>
          <Button type="submit" disabled={loading}>
            Send
          </Button>
        </form>
      </Card>
      </main>
    </AdminGuard>
  );
}
