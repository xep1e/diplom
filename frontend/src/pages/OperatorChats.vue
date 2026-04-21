<template>
  <div class="operator-chats">
    <div class="header">
      <h2>📋 Мои чаты</h2>
      <div class="tabs">
        <button 
          class="tab" 
          :class="{ active: activeTab === 'active' }"
          @click="activeTab = 'active'"
        >
          Активные ({{ activeChats.length }})
        </button>
        <button 
          class="tab" 
          :class="{ active: activeTab === 'closed' }"
          @click="activeTab = 'closed'"
        >
          Закрытые ({{ closedChats.length }})
        </button>
      </div>
    </div>

    <div class="chats-list">
      <div
        v-for="chat in displayedChats"
        :key="chat.id"
        class="chat-card"
        :class="{ closed: chat.status === 'closed' }"
        @click="$emit('select-chat', chat)"
      >
        <div class="chat-info">
          <div class="chat-title">
            {{ chat.title }}
            <span v-if="chat.status === 'closed'" class="closed-badge">Закрыт</span>
            <span v-if="chat.status === 'new'" class="new-badge">Новый</span>
          </div>
          <div class="chat-preview">{{ chat.last_message || 'Нет сообщений' }}</div>
        </div>
        <div class="chat-meta">
          <div class="chat-time">{{ formatTime(chat.updated_at) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  chats: Array
})

const activeTab = ref('active')

const activeChats = computed(() => {
  return (props.chats || []).filter(c => c.status !== 'closed')
})

const closedChats = computed(() => {
  return (props.chats || []).filter(c => c.status === 'closed')
})

const displayedChats = computed(() => {
  return activeTab.value === 'active' ? activeChats.value : closedChats.value
})

const formatTime = (date) => {
  if (!date) return ''
  const d = new Date(date)
  const now = new Date()
  const diff = now - d
  
  if (diff < 60000) return 'только что'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} мин назад`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} ч назад`
  return d.toLocaleDateString()
}
</script>

<style scoped>
.operator-chats {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.header {
  padding: 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.header h2 {
  margin: 0 0 12px 0;
  font-size: 18px;
}

.tabs {
  display: flex;
  gap: 8px;
}

.tab {
  background: rgba(255,255,255,0.1);
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  font-size: 13px;
}

.tab.active {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.chats-list {
  flex: 1;
  overflow-y: auto;
}

.chat-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  cursor: pointer;
  transition: background 0.2s;
}

.chat-card:hover {
  background: rgba(255,255,255,0.1);
}

.chat-card.closed {
  opacity: 0.7;
}

.chat-title {
  font-weight: 500;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.closed-badge {
  font-size: 10px;
  background: #95a5a6;
  padding: 2px 6px;
  border-radius: 4px;
}

.new-badge {
  font-size: 10px;
  background: #e74c3c;
  padding: 2px 6px;
  border-radius: 4px;
}

.chat-preview {
  font-size: 12px;
  opacity: 0.7;
}

.chat-time {
  font-size: 11px;
  opacity: 0.5;
}
</style>