import React, { useState, useEffect, useRef } from 'react';
import { X, Send, Bot, User, Loader2 } from 'lucide-react';
import { useAppContext } from '../../contexts/AppContext';

export const ChatPanel = ({ isOpen, onClose }) => {
    const { role } = useAppContext();
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef(null);

    const [messages, setMessages] = useState([
        { id: '1', role: 'assistant', content: 'Hello! I am TunaTax AI. How can I help you today?' },
    ]);

    const workerSuggestions = [
        "What invoices are unmatched?",
        "Show my compliance deadlines",
        "Generate the UK VAT return"
    ];

    const businessSuggestions = [
        "What's my total tax liability?",
        "How does this quarter compare to last?",
        "When is my next filing due?"
    ];

    const suggestions = role === 'worker' ? workerSuggestions : businessSuggestions;

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        if (isOpen) {
            scrollToBottom();
        }
    }, [isOpen, messages]);

    const handleSend = (text) => {
        if (!text.trim()) return;

        const userMsg = { id: Date.now().toString(), role: 'user', content: text };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsTyping(true);

        // Simulate API call
        setTimeout(() => {
            const toolMsg = {
                id: (Date.now() + 1).toString(),
                role: 'system',
                content: text.includes('invoice') ? '🔍 Querying transactions...' : '📄 Analyzing data...'
            };
            setMessages(prev => [...prev, toolMsg]);

            setTimeout(() => {
                setMessages(prev => {
                    const m = [...prev];
                    m.pop(); // remove tool usage label
                    m.push({
                        id: (Date.now() + 2).toString(),
                        role: 'assistant',
                        content: `I've analyzed the request for "${text}". Based on the current company data, everything looks in order. (Mock response)`
                    });
                    return m;
                });
                setIsTyping(false);
            }, 1500);

        }, 800);
    };

    if (!isOpen) return null;

    return (
        <>
            <div
                style={{
                    position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 40,
                }}
                onClick={onClose}
            />
            <div
                style={{
                    position: 'fixed', top: 0, right: 0, bottom: 0, width: '400px',
                    backgroundColor: 'var(--color-bg-base)',
                    borderLeft: '1px solid var(--color-border)',
                    zIndex: 50,
                    display: 'flex', flexDirection: 'column',
                    boxShadow: '-10px 0 25px rgba(0,0,0,0.5)',
                    animation: 'slideIn 0.3s ease-out forwards',
                }}
            >
                <div style={{
                    padding: '16px 20px',
                    borderBottom: '1px solid var(--color-border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    backgroundColor: 'var(--color-bg-surface)'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{
                            width: '8px', height: '8px', borderRadius: '50%',
                            backgroundColor: 'var(--color-success)',
                            boxShadow: '0 0 8px var(--color-success)'
                        }} />
                        <span style={{ fontWeight: '600', fontFamily: 'var(--font-display)', fontSize: '18px' }}>TunaTax AI</span>
                    </div>
                    <button onClick={onClose} style={{ color: 'var(--color-text-muted)', padding: '4px', cursor: 'pointer', background: 'none', border: 'none' }}>
                        <X size={20} />
                    </button>
                </div>

                <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {messages.map((m) => (
                        <div
                            key={m.id}
                            style={{
                                display: 'flex',
                                gap: '12px',
                                alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                                maxWidth: '85%',
                                flexDirection: m.role === 'user' ? 'row-reverse' : 'row'
                            }}
                        >
                            {m.role !== 'system' && (
                                <div style={{
                                    width: '28px', height: '28px', borderRadius: '50%',
                                    backgroundColor: m.role === 'user' ? 'var(--color-accent)' : 'var(--color-bg-surface)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                                    border: m.role === 'user' ? 'none' : '1px solid var(--color-border)'
                                }}>
                                    {m.role === 'user' ? <User size={14} color="#fff" /> : <Bot size={14} color="var(--color-accent)" />}
                                </div>
                            )}

                            {m.role === 'system' ? (
                                <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <Loader2 size={12} className="animate-spin" /> {m.content}
                                </div>
                            ) : (
                                <div style={{
                                    backgroundColor: m.role === 'user' ? 'var(--color-accent)' : 'var(--color-bg-surface)',
                                    color: m.role === 'user' ? '#fff' : 'var(--color-text-primary)',
                                    padding: '12px 16px',
                                    borderRadius: '12px',
                                    borderTopRightRadius: m.role === 'user' ? '0' : '12px',
                                    borderTopLeftRadius: m.role === 'assistant' ? '0' : '12px',
                                    fontSize: '14px',
                                    lineHeight: '1.5',
                                    border: m.role === 'user' ? 'none' : '1px solid var(--color-border)'
                                }}>
                                    {m.content}
                                </div>
                            )}
                        </div>
                    ))}
                    {isTyping && !messages.some(m => m.role === 'system') && (
                        <div style={{ display: 'flex', gap: '4px', alignSelf: 'flex-start', padding: '16px 20px', backgroundColor: 'var(--color-bg-surface)', borderRadius: '12px', borderTopLeftRadius: '0', border: '1px solid var(--color-border)' }}>
                            <div className="typing-dot" style={{ width: '6px', height: '6px', backgroundColor: 'var(--color-text-muted)', borderRadius: '50%' }}></div>
                            <div className="typing-dot" style={{ width: '6px', height: '6px', backgroundColor: 'var(--color-text-muted)', borderRadius: '50%', animationDelay: '0.2s' }}></div>
                            <div className="typing-dot" style={{ width: '6px', height: '6px', backgroundColor: 'var(--color-text-muted)', borderRadius: '50%', animationDelay: '0.4s' }}></div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {messages.length === 1 && (
                    <div style={{ padding: '0 20px', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>Suggested questions:</div>
                        {suggestions.map((s, i) => (
                            <button
                                key={i}
                                onClick={() => handleSend(s)}
                                style={{
                                    textAlign: 'left',
                                    padding: '8px 12px',
                                    backgroundColor: 'transparent',
                                    border: '1px solid var(--color-border)',
                                    borderRadius: '6px',
                                    fontSize: '13px',
                                    color: 'var(--color-text-primary)',
                                    cursor: 'pointer',
                                    transition: 'background-color 0.2s',
                                    lineHeight: '1.4'
                                }}
                                onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--color-bg-surface)'}
                                onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                            >
                                {s}
                            </button>
                        ))}
                    </div>
                )}

                <div style={{ padding: '16px 20px', borderTop: '1px solid var(--color-border)' }}>
                    <form
                        onSubmit={(e) => { e.preventDefault(); handleSend(input); }}
                        style={{ display: 'flex', gap: '8px' }}
                    >
                        <input
                            type="text"
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            placeholder="Ask TunaTax..."
                            disabled={isTyping}
                            style={{
                                flex: 1,
                                backgroundColor: 'var(--color-bg-surface)',
                                border: '1px solid var(--color-border)',
                                borderRadius: '8px',
                                padding: '10px 14px',
                                color: 'var(--color-text-primary)',
                                outline: 'none',
                                fontFamily: 'var(--font-body)',
                                fontSize: '14px'
                            }}
                            onFocus={e => e.target.style.borderColor = 'var(--color-accent)'}
                            onBlur={e => e.target.style.borderColor = 'var(--color-border)'}
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || isTyping}
                            style={{
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                backgroundColor: input.trim() && !isTyping ? 'var(--color-accent)' : 'var(--color-bg-surface)',
                                color: input.trim() && !isTyping ? '#fff' : 'var(--color-text-muted)',
                                border: 'none',
                                borderRadius: '8px',
                                width: '42px', height: '42px',
                                cursor: input.trim() && !isTyping ? 'pointer' : 'not-allowed',
                                transition: 'background-color 0.2s'
                            }}
                        >
                            <Send size={18} />
                        </button>
                    </form>
                </div>
            </div>
            <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
        .typing-dot {
          animation: typingscale 1.4s infinite ease-in-out both;
        }
        @keyframes typingscale {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }
        .animate-spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
        </>
    );
};
