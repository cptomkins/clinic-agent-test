<!-- src/lib/clinic-agent/ClinicChatView.svelte -->
<!-- Author: Claude -->
<!-- Created Date: 2026-03-15 -->
<!-- Updated: 2026-03-15 — v0.15.0: markdown rendering for assistant messages -->
<!-- Updated: 2026-03-16 — v0.17: auto-greet on first-ever conversation -->
<script lang="ts">
  import './styles.css';
  import { onMount, tick } from 'svelte';
  import { marked } from 'marked';
  import {
    sendMessage,
    streamResponse,
    listConversations,
    getMessages,
    getAccountData,
    createNewConversation,
    type MessageOut,
    type ConversationOut,
    type AccountData,
  } from '$lib/api/solutions/clinic-agent/chat';

  // ── Markdown ───────────────────────────────────────────────

  marked.setOptions({ breaks: true, gfm: true });

  function renderMarkdown(text: string): string {
    return marked.parse(text) as string;
  }

  // ── State ────────────────────────────────────────────────────

  let conversations: ConversationOut[] = [];
  let currentConversationId: string | null = null;
  let messages: MessageOut[] = [];
  let inputText = '';
  let isSending = false;
  let isStreaming = false;
  let streamingContent = '';
  let errorMsg: string | null = null;
  let messagesContainer: HTMLDivElement;
  let activeStreamController: AbortController | null = null;

  // ── Account panel ──────────────────────────────────────────

  let accountData: AccountData | null = null;
  let panelOpen = false;

  // ── Bootstrap ────────────────────────────────────────────────

  onMount(async () => {
    await loadConversations();
    const res = await getAccountData();
    if (res.success) accountData = res.data;

    // v0.17: If user has no conversations, create one and auto-greet
    if (conversations.length === 0) {
      const newRes = await createNewConversation();
      if (newRes.success) {
        await loadConversations();
        if (newRes.data.auto_greet) {
          await triggerAutoGreet(newRes.data.conversation_id);
        }
      }
    }
  });

  async function loadConversations() {
    const res = await listConversations();
    if (res.success) {
      conversations = res.data;
      if (conversations.length > 0 && !currentConversationId) {
        await selectConversation(conversations[0].id);
      }
    }
  }

  async function selectConversation(id: string) {
    // Cancel any active stream
    if (activeStreamController) {
      activeStreamController.abort();
      activeStreamController = null;
    }

    currentConversationId = id;
    isStreaming = false;
    streamingContent = '';
    errorMsg = null;

    const res = await getMessages(id);
    if (res.success) {
      messages = res.data;
      await scrollToBottom();
    } else {
      errorMsg = 'Failed to load messages.';
    }
  }

  // ── Send ─────────────────────────────────────────────────────

  async function handleSend() {
    const text = inputText.trim();
    if (!text || isSending || isStreaming) return;

    errorMsg = null;
    isSending = true;
    inputText = '';

    // Optimistic user message
    const tempUserMsg: MessageOut = {
      id: Math.random().toString(36).slice(2),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    messages = [...messages, tempUserMsg];
    await scrollToBottom();

    // POST to store user message and get conversation_id
    const res = await sendMessage({
      message: text,
      conversation_id: currentConversationId ?? undefined,
    });

    if (!res.success) {
      errorMsg = res.error?.message ?? 'Failed to send message.';
      isSending = false;
      return;
    }

    const conversationId = res.data.conversation_id;

    if (!currentConversationId) {
      currentConversationId = conversationId;
      await loadConversations();
    }

    // Replace optimistic message with the server version
    messages = messages.map((m) =>
      m.id === tempUserMsg.id ? res.data.message : m,
    );

    isSending = false;
    isStreaming = true;
    streamingContent = '';

    // Open SSE stream for AI response
    activeStreamController = streamResponse(conversationId, {
      onToken(text) {
        streamingContent += text;
        scrollToBottom();
      },
      onDone(msg) {
        // Add the final assistant message to the list
        messages = [
          ...messages,
          {
            id: msg.id,
            role: 'assistant',
            content: msg.content,
            created_at: msg.created_at,
          },
        ];
        isStreaming = false;
        streamingContent = '';
        activeStreamController = null;
        scrollToBottom();
      },
      onError(message) {
        errorMsg = message;
        isStreaming = false;
        streamingContent = '';
        activeStreamController = null;
      },
    });
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  // ── New conversation ─────────────────────────────────────────

  async function startNewConversation() {
    if (activeStreamController) {
      activeStreamController.abort();
      activeStreamController = null;
    }
    currentConversationId = null;
    messages = [];
    isStreaming = false;
    streamingContent = '';
    errorMsg = null;

    // v0.17: Pre-create the conversation via the new endpoint.
    // auto_greet will be false since user already has history.
    const res = await createNewConversation();
    if (res.success) {
      currentConversationId = res.data.conversation_id;
      await loadConversations();
    }
  }

  // ── Auto-greet ───────────────────────────────────────────────

  async function triggerAutoGreet(conversationId: string) {
    currentConversationId = conversationId;
    isStreaming = true;
    streamingContent = '';

    activeStreamController = streamResponse(conversationId, {
      onToken(text) {
        streamingContent += text;
        scrollToBottom();
      },
      onDone(msg) {
        messages = [
          ...messages,
          {
            id: msg.id,
            role: 'assistant',
            content: msg.content,
            created_at: msg.created_at,
          },
        ];
        isStreaming = false;
        streamingContent = '';
        activeStreamController = null;
        scrollToBottom();
      },
      onError(message) {
        errorMsg = message;
        isStreaming = false;
        streamingContent = '';
        activeStreamController = null;
      },
    });
  }

  // ── Panel ────────────────────────────────────────────────────

  function togglePanel() {
    panelOpen = !panelOpen;
  }

  function formatDate(iso: string | null) {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  }

  function formatTime(iso: string) {
    return new Date(iso).toLocaleString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function capitalize(s: string) {
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  // ── Scroll ───────────────────────────────────────────────────

  async function scrollToBottom() {
    await tick();
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }
</script>

<div class="ca-chat">
  <!-- Sidebar -->
  <aside class="ca-chat__sidebar">
    <button class="ca-chat__new-btn" on:click={startNewConversation}>
      + New Chat
    </button>
    <div class="ca-chat__conversations">
      {#each conversations as convo}
        <button
          class="ca-chat__convo-item"
          class:active={convo.id === currentConversationId}
          on:click={() => selectConversation(convo.id)}
        >
          {new Date(convo.created_at).toLocaleDateString(undefined, {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </button>
      {/each}
    </div>
  </aside>

  <!-- Chat area -->
  <div class="ca-chat__main">
    <div class="ca-chat__messages" bind:this={messagesContainer}>
      {#if messages.length === 0 && !isStreaming}
        <div class="ca-chat__empty">
          <p>Start a conversation by typing a message below.</p>
        </div>
      {/if}
      {#each messages as msg}
        <div class="ca-chat__bubble" class:user={msg.role === 'user'} class:assistant={msg.role === 'assistant'}>
          <span class="ca-chat__role">{msg.role === 'user' ? 'You' : 'Agent'}</span>
          {#if msg.role === 'assistant'}
            <div class="ca-chat__content ca-chat__markdown">{@html renderMarkdown(msg.content)}</div>
          {:else}
            <p class="ca-chat__content">{msg.content}</p>
          {/if}
        </div>
      {/each}
      {#if isStreaming}
        <div class="ca-chat__bubble assistant">
          <span class="ca-chat__role">Agent</span>
          <div class="ca-chat__content ca-chat__markdown">{@html renderMarkdown(streamingContent || '…')}</div>
        </div>
      {/if}
    </div>

    {#if errorMsg}
      <div class="ca-chat__error">{errorMsg}</div>
    {/if}

    <div class="ca-chat__input-bar">
      <textarea
        class="ca-chat__input"
        bind:value={inputText}
        on:keydown={handleKeydown}
        placeholder="Ask about features, billing, troubleshooting, or upgrades…"
        rows="1"
        disabled={isSending || isStreaming}
      ></textarea>
      <button
        class="ca-chat__send-btn"
        on:click={handleSend}
        disabled={!inputText.trim() || isSending || isStreaming}
      >
        Send
      </button>
    </div>
  </div>

  <!-- Floating account panel button -->
  {#if !panelOpen}
    <button class="ca-panel__fab" on:click={togglePanel}>
      Customer Account
    </button>
  {/if}

  <!-- Customer account panel -->
  <aside class="ca-panel" class:open={panelOpen}>
    {#if panelOpen}
      <div class="ca-panel__header">
        <h3 class="ca-panel__title">Customer Account</h3>
        <button class="ca-panel__close" on:click={togglePanel}>✕</button>
      </div>

      {#if accountData}
        <div class="ca-panel__body">
          <!-- Account info -->
          <div class="ca-panel__section">
            <h4 class="ca-panel__section-title">{accountData.clinic_name}</h4>
            <div class="ca-panel__field">
              <span class="ca-panel__label">Plan</span>
              <span class="ca-panel__value">{capitalize(accountData.plan)}</span>
            </div>
            <div class="ca-panel__field">
              <span class="ca-panel__label">Seats</span>
              <span class="ca-panel__value">{accountData.seats}</span>
            </div>
            <div class="ca-panel__field">
              <span class="ca-panel__label">Billing</span>
              <span class="ca-panel__value">{capitalize(accountData.billing_cycle)}</span>
            </div>
            <div class="ca-panel__field">
              <span class="ca-panel__label">Next invoice</span>
              <span class="ca-panel__value">{formatDate(accountData.next_billing_date)}</span>
            </div>
          </div>

          <!-- Support tickets -->
          <div class="ca-panel__section">
            <h4 class="ca-panel__section-title">Support Tickets</h4>
            {#if accountData.tickets.length === 0}
              <p class="ca-panel__empty">No support tickets.</p>
            {:else}
              <div class="ca-panel__list">
                {#each accountData.tickets as ticket}
                  <div class="ca-panel__item">
                    <div class="ca-panel__item-row">
                      <span class="ca-panel__item-primary">{ticket.subject}</span>
                      <span class="ca-panel__ticket-status" class:open={ticket.status === 'open'} class:in_progress={ticket.status === 'in_progress'} class:resolved={ticket.status === 'resolved'}>
                        {ticket.status === 'in_progress' ? 'In Progress' : capitalize(ticket.status)}
                      </span>
                    </div>
                    <span class="ca-panel__item-meta">{formatDate(ticket.created_at)}</span>
                  </div>
                {/each}
              </div>
            {/if}
          </div>
        </div>
      {:else}
        <div class="ca-panel__body">
          <p class="ca-panel__empty">Loading account data…</p>
        </div>
      {/if}
    {/if}
  </aside>
</div>
