<script lang="ts">
  import { demos, type AgentChatResult } from '$lib/api';

  interface Message {
    role: 'user' | 'assistant';
    content: string;
    reasoning_steps?: string[];
    confidence?: number;
  }

  let messages: Message[] = [];
  let inputMessage = '';
  let agentPersona: 'legal' | 'risk' | 'compliance' | 'general' = 'legal';
  let loading = false;

  const personas = {
    legal: { name: 'Legal Analyst', icon: '⚖️', color: '#3b82f6' },
    risk: { name: 'Risk Advisor', icon: '🎯', color: '#8b5cf6' },
    compliance: { name: 'Compliance Officer', icon: '📋', color: '#059669' },
    general: { name: 'General Assistant', icon: '🤖', color: '#6b7280' },
  };

  const sampleQuestions = [
    'What are the key risks in a force majeure clause?',
    'How do I evaluate vendor contract dependencies?',
    'What compliance requirements apply to data processing?',
    'Explain the difference between indemnity and liability caps',
  ];

  async function sendMessage() {
    if (!inputMessage.trim() || loading) return;

    const userMessage = inputMessage.trim();
    inputMessage = '';

    messages = [...messages, { role: 'user', content: userMessage }];
    loading = true;

    try {
      const response: AgentChatResult = await demos.agentChat({
        message: userMessage,
        persona: agentPersona,
        context: messages.slice(-5).map(m => ({ role: m.role, content: m.content })),
      });

      messages = [
        ...messages,
        {
          role: 'assistant',
          content: response.response,
          reasoning_steps: response.reasoning_steps,
          confidence: response.confidence,
        },
      ];
    } catch (e) {
      messages = [
        ...messages,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
        },
      ];
    } finally {
      loading = false;
    }
  }

  function loadSampleQuestion(q: string) {
    inputMessage = q;
  }

  function clearChat() {
    messages = [];
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }
</script>

<div class="demo-container">
  <div class="demo-header">
    <h2>🤖 AI Agent Chat</h2>
    <p>Chat with AION's specialized AI agents for instant expert guidance.</p>
  </div>

  <div class="chat-container">
    <div class="chat-sidebar">
      <div class="persona-selector">
        <h4>Select Agent</h4>
        {#each Object.entries(personas) as [key, persona]}
          <button
            class="persona-btn"
            class:active={agentPersona === key}
            style="--persona-color: {persona.color}"
            on:click={() => (agentPersona = key)}
          >
            <span class="persona-icon">{persona.icon}</span>
            <span class="persona-name">{persona.name}</span>
          </button>
        {/each}
      </div>

      <div class="sample-questions">
        <h4>Try asking...</h4>
        {#each sampleQuestions as q}
          <button class="sample-btn" on:click={() => loadSampleQuestion(q)}>
            {q}
          </button>
        {/each}
      </div>

      <button class="clear-btn" on:click={clearChat} disabled={messages.length === 0}>
        Clear Chat
      </button>
    </div>

    <div class="chat-main">
      <div class="chat-header" style="--header-color: {personas[agentPersona].color}">
        <span class="header-icon">{personas[agentPersona].icon}</span>
        <span class="header-name">{personas[agentPersona].name}</span>
        <span class="header-status">● Online</span>
      </div>

      <div class="messages-container">
        {#if messages.length === 0}
          <div class="empty-state">
            <div class="empty-icon">{personas[agentPersona].icon}</div>
            <p>Hi! I'm your {personas[agentPersona].name}.</p>
            <p class="empty-hint">Ask me anything about contracts, risks, or compliance.</p>
          </div>
        {:else}
          {#each messages as msg}
            <div class="message {msg.role}">
              {#if msg.role === 'assistant'}
                <div class="message-avatar" style="background: {personas[agentPersona].color}">
                  {personas[agentPersona].icon}
                </div>
              {/if}
              <div class="message-content">
                <p>{msg.content}</p>
                {#if msg.reasoning_steps && msg.reasoning_steps.length > 0}
                  <details class="reasoning">
                    <summary>View reasoning ({msg.reasoning_steps.length} steps)</summary>
                    <ol>
                      {#each msg.reasoning_steps as step}
                        <li>{step}</li>
                      {/each}
                    </ol>
                  </details>
                {/if}
                {#if msg.confidence}
                  <span class="confidence">Confidence: {(msg.confidence * 100).toFixed(0)}%</span>
                {/if}
              </div>
              {#if msg.role === 'user'}
                <div class="message-avatar user">👤</div>
              {/if}
            </div>
          {/each}
          {#if loading}
            <div class="message assistant">
              <div class="message-avatar" style="background: {personas[agentPersona].color}">
                {personas[agentPersona].icon}
              </div>
              <div class="message-content typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          {/if}
        {/if}
      </div>

      <div class="chat-input">
        <textarea
          bind:value={inputMessage}
          on:keydown={handleKeydown}
          placeholder="Type your question..."
          rows="2"
          disabled={loading}
        ></textarea>
        <button class="send-btn" on:click={sendMessage} disabled={loading || !inputMessage.trim()}>
          ➤
        </button>
      </div>
    </div>
  </div>
</div>

<style>
  .demo-container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 2rem;
  }

  .demo-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .demo-header h2 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
  }

  .demo-header p {
    color: #6b7280;
  }

  .chat-container {
    display: grid;
    grid-template-columns: 280px 1fr;
    gap: 1.5rem;
    height: 600px;
  }

  .chat-sidebar {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .persona-selector, .sample-questions {
    background: white;
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  }

  h4 {
    font-size: 0.85rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.75rem;
  }

  .persona-btn {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    padding: 0.75rem;
    border: 2px solid transparent;
    border-radius: 8px;
    background: #f9fafb;
    cursor: pointer;
    margin-bottom: 0.5rem;
    transition: all 0.2s;
  }

  .persona-btn:hover {
    border-color: var(--persona-color);
  }

  .persona-btn.active {
    border-color: var(--persona-color);
    background: white;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }

  .persona-icon {
    font-size: 1.25rem;
  }

  .persona-name {
    font-weight: 500;
    color: #374151;
  }

  .sample-btn {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background: white;
    font-size: 0.8rem;
    color: #6b7280;
    text-align: left;
    cursor: pointer;
    margin-bottom: 0.5rem;
    transition: all 0.2s;
  }

  .sample-btn:hover {
    border-color: #3b82f6;
    color: #3b82f6;
  }

  .clear-btn {
    padding: 0.75rem;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    background: white;
    color: #6b7280;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .clear-btn:hover:not(:disabled) {
    border-color: #dc2626;
    color: #dc2626;
  }

  .clear-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .chat-main {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .chat-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #e5e7eb;
    background: linear-gradient(135deg, var(--header-color), color-mix(in srgb, var(--header-color) 80%, black));
    color: white;
  }

  .header-icon {
    font-size: 1.5rem;
  }

  .header-name {
    font-weight: 600;
    font-size: 1.1rem;
  }

  .header-status {
    margin-left: auto;
    font-size: 0.8rem;
    opacity: 0.9;
  }

  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #9ca3af;
    text-align: center;
  }

  .empty-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  .empty-hint {
    font-size: 0.9rem;
    margin-top: 0.5rem;
  }

  .message {
    display: flex;
    gap: 0.75rem;
    max-width: 85%;
  }

  .message.user {
    align-self: flex-end;
    flex-direction: row-reverse;
  }

  .message-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
  }

  .message-avatar.user {
    background: #e5e7eb;
  }

  .message-content {
    padding: 0.75rem 1rem;
    border-radius: 16px;
    background: #f3f4f6;
  }

  .message.user .message-content {
    background: #3b82f6;
    color: white;
  }

  .message-content p {
    margin: 0;
    line-height: 1.5;
  }

  .reasoning {
    margin-top: 0.75rem;
    font-size: 0.85rem;
  }

  .reasoning summary {
    cursor: pointer;
    color: #6b7280;
  }

  .reasoning ol {
    margin: 0.5rem 0 0;
    padding-left: 1.25rem;
    color: #6b7280;
  }

  .reasoning li {
    margin-bottom: 0.25rem;
  }

  .confidence {
    display: inline-block;
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: #9ca3af;
  }

  .typing {
    display: flex;
    gap: 4px;
    padding: 1rem !important;
  }

  .typing span {
    width: 8px;
    height: 8px;
    background: #9ca3af;
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out;
  }

  .typing span:nth-child(1) { animation-delay: 0s; }
  .typing span:nth-child(2) { animation-delay: 0.2s; }
  .typing span:nth-child(3) { animation-delay: 0.4s; }

  @keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  }

  .chat-input {
    display: flex;
    gap: 0.75rem;
    padding: 1rem;
    border-top: 1px solid #e5e7eb;
  }

  .chat-input textarea {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    resize: none;
    font-family: inherit;
    font-size: 0.95rem;
  }

  .send-btn {
    width: 48px;
    height: 48px;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 50%;
    font-size: 1.25rem;
    cursor: pointer;
    transition: opacity 0.2s;
  }

  .send-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  @media (max-width: 768px) {
    .chat-container {
      grid-template-columns: 1fr;
      height: auto;
    }

    .chat-sidebar {
      flex-direction: row;
      flex-wrap: wrap;
    }

    .persona-selector, .sample-questions {
      flex: 1;
      min-width: 200px;
    }

    .chat-main {
      height: 500px;
    }
  }
</style>
