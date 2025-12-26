'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, BookOpen, Network, Brain, ChevronRight, ChevronDown, User, Bot, Loader2 } from 'lucide-react';

interface ChatResponse {
  answer: string;
  sources: Array<{ source: string; text: string }>;
  graph_path: Array<any>;
  thought_process: {
    steps: string[];
    cypher_query?: string;
    context_size?: number;
  };
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  details?: ChatResponse;
}

export default function ChatInterface() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      // In production, use an environment variable for the API URL
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!response.ok) throw new Error('Failed to fetch response');

      const data: ChatResponse = await response.json();
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        details: data
      }]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Sorry, I encountered an error connecting to the Orion brain."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-6xl mx-auto p-4 bg-gray-50 text-gray-900 font-sans">
      <header className="mb-6 flex items-center gap-3 border-b pb-4">
        <div className="p-2 bg-blue-600 rounded-lg text-white">
          <Brain size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Orion Intelligence</h1>
          <p className="text-sm text-gray-500">RAG-powered Knowledge Graph Assistant</p>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto mb-4 space-y-6 pr-4 scrollbar-thin scrollbar-thumb-gray-200">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 flex-shrink-0 mt-1">
                <Bot size={18} />
              </div>
            )}
            
            <div className={`max-w-[80%] space-y-2`}>
              <div className={`p-4 rounded-2xl shadow-sm ${
                msg.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-tr-sm' 
                  : 'bg-white border border-gray-100 rounded-tl-sm'
              }`}>
                <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              </div>

              {/* RAG Details (Sources & Graph) */}
              {msg.details && (
                <div className="space-y-3 mt-2 animate-in fade-in slide-in-from-top-2 duration-500">
                  {/* Thought Process Accordion */}
                  <DetailAccordion 
                    icon={<Brain size={16} />} 
                    title="Reasoning Process" 
                    defaultOpen={true}
                  >
                    <div className="space-y-2 text-sm">
                      {msg.details.thought_process.steps.map((step, i) => (
                        <div key={i} className="flex items-center gap-2 text-gray-600">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                          {step}
                        </div>
                      ))}
                      {msg.details.thought_process.cypher_query && (
                        <div className="mt-2 bg-gray-900 text-green-400 p-3 rounded-md font-mono text-xs overflow-x-auto">
                          {msg.details.thought_process.cypher_query}
                        </div>
                      )}
                    </div>
                  </DetailAccordion>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {/* Sources */}
                    <DetailAccordion icon={<BookOpen size={16} />} title="Filed Sources">
                      {msg.details.sources.length > 0 ? (
                        <div className="space-y-2 text-sm text-gray-600">
                          {msg.details.sources.map((src, i) => (
                            <div key={i} className="bg-gray-50 p-2 rounded border border-gray-100">
                              <div className="font-semibold text-gray-800 text-xs mb-1">{src.source}</div>
                              <div className="line-clamp-3 text-xs">{src.text}</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-gray-400 text-sm italic">No specific filings cited.</div>
                      )}
                    </DetailAccordion>

                    {/* Graph Path */}
                    <DetailAccordion icon={<Network size={16} />} title="Graph Connections">
                      {msg.details.graph_path.length > 0 ? (
                         <div className="bg-gray-50 p-2 rounded border border-gray-100 text-xs font-mono text-gray-700 overflow-auto max-h-40">
                           <pre>{JSON.stringify(msg.details.graph_path, null, 2)}</pre>
                         </div>
                      ) : (
                        <div className="text-gray-400 text-sm italic">No graph path traversed.</div>
                      )}
                    </DetailAccordion>
                  </div>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-500 flex-shrink-0 mt-1">
                <User size={18} />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-4">
             <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 flex-shrink-0">
                <Bot size={18} />
              </div>
              <div className="bg-white border border-gray-100 p-4 rounded-2xl rounded-tl-sm shadow-sm flex items-center gap-2">
                <Loader2 size={16} className="animate-spin text-blue-600" />
                <span className="text-sm text-gray-500">Thinking...</span>
              </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about companies, filings, or relationships..."
          className="w-full p-4 pr-12 rounded-xl border border-gray-200 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-800 placeholder-gray-400"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="absolute right-2 top-2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send size={20} />
        </button>
      </form>
    </div>
  );
}

function DetailAccordion({ icon, title, children, defaultOpen = false }: { icon: React.ReactNode, title: string, children: React.ReactNode, defaultOpen?: boolean }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-gray-200 rounded-lg bg-white overflow-hidden">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
      >
        <div className="flex items-center gap-2 text-gray-700 font-medium text-sm">
          {icon}
          <span>{title}</span>
        </div>
        {isOpen ? <ChevronDown size={16} className="text-gray-400" /> : <ChevronRight size={16} className="text-gray-400" />}
      </button>
      
      {isOpen && (
        <div className="p-3 border-t border-gray-100">
          {children}
        </div>
      )}
    </div>
  );
}
