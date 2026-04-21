<template>
  <div class="chat-layout">
    <!-- LEFT -->
    <div class="chat-list">
      <div
        v-for="c in chats"
        :key="c.id"
        class="chat-item"
        :class="{ active: activeChat?.id === c.id, closed: c.status === 'closed' }"
        @click="openChat(c)"
      >
        <div class="chat-item-content">
          <div class="chat-title">
            <b>{{ c.title }}</b>
            <span v-if="c.status === 'closed'" class="closed-badge">Закрыт</span>
            <span v-if="c.status === 'new'" class="new-badge">Новый</span>
          </div>
          <p class="last">{{ c.last_message || 'Нет сообщений' }}</p>
        </div>
        <div class="chat-time">{{ formatTime(c.updated_at) }}</div>
      </div>
      
      <div v-if="chats.length === 0" class="empty-chats">
        💬 Нет активных чатов
      </div>
    </div>

    <!-- RIGHT -->
    <div class="chat-window" v-if="activeChat">
      <div class="header">
        <div class="header-info">
          <div class="chat-title-header">
            <span>{{ activeChat.title }}</span>
            <span v-if="activeChat.status === 'closed'" class="closed-status">🔒 Закрыт</span>
            <span v-if="activeChat.status === 'new'" class="new-status">🆕 Новый</span>
          </div>
          <div class="chat-id">Чат #{{ activeChat.id }}</div>
        </div>
        <div class="header-actions">
          <button 
            v-if="activeChat.status !== 'closed'"
            class="close-chat-btn" 
            @click="closeChat"
            :disabled="isClosing"
          >
            {{ isClosing ? 'Закрытие...' : '🔒 Закрыть диалог' }}
          </button>
        </div>
      </div>

      <div class="messages" ref="messagesBox">
        <div
          v-for="m in messages"
          :key="m.id"
          :class="['msg', getMessageClass(m)]"
        >
          <div class="sender">{{ m.sender }}</div>
          
          <!-- Текстовое сообщение -->
          <div v-if="m.text && !m.media_url" class="message-text">{{ m.text }}</div>
          
          <!-- Фото из кэша Redis -->
          <div v-if="m.media_type === 'image' && m.media_url">
            <img 
              :src="getPhotoUrl(m.media_url)"
              class="media-image"
              @click="openImage(getPhotoUrl(m.media_url))"
              @load="scrollToBottom"
              @error="handleImageError(m)"
            />
            <div class="media-caption">{{ m.text }}</div>
          </div>
        </div>
        
        <!-- Сообщение о закрытии чата -->
        <div v-if="activeChat.status === 'closed'" class="system-message">
          🔒 Диалог закрыт {{ formatDate(activeChat.closed_at) }}
        </div>
        
        <div ref="messagesEnd"></div>
      </div>

      <div class="input-area" v-if="activeChat.status !== 'closed'">
        <div class="input-tools">
          <button @click="triggerPhotoUpload" class="tool-btn" title="Отправить фото">
            📷 Фото
          </button>
        </div>
        
        <div class="input">
          <input 
            v-model="text" 
            @keyup.enter="send" 
            placeholder="Сообщение..." 
          />
          <button @click="send" :disabled="!text.trim()">
            ➤
          </button>
        </div>
      </div>
      
      <div v-else class="closed-message">
        💬 Диалог закрыт. Спасибо за обращение!
      </div>
    </div>

    <div v-else class="no-chat-selected">
      <div class="no-chat-content">
        <div class="no-chat-icon">💬</div>
        <h3>Выберите чат</h3>
        <p>Нажмите на диалог слева, чтобы начать общение</p>
      </div>
    </div>

    <!-- Модальное окно для просмотра изображений -->
    <div v-if="showImageModal" class="modal" @click="closeImage">
      <img :src="selectedImage" class="modal-image" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'
import { getMe } from '../api/authApi'

import '/style/chat.css'

const chats = ref([])
const activeChat = ref(null)
const messages = ref([])
const text = ref("")
const me = ref({})
const showImageModal = ref(false)
const selectedImage = ref("")
const isClosing = ref(false)

let socket = null
const messagesBox = ref(null)
let refreshInterval = null

// Форматирование времени
const formatTime = (date) => {
  if (!date) return ''
  const d = new Date(date)
  const now = new Date()
  const diff = now - d
  
  if (diff < 60000) return 'только что'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} мин`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} ч`
  return d.toLocaleDateString()
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString()
}

// Функция для получения URL фото
const getPhotoUrl = (photoKey) => {
  return `http://127.0.0.1:8000/photo/${encodeURIComponent(photoKey)}`
}

// Класс сообщения
const getMessageClass = (m) => {
  if (m.sender_type === 'operator') return 'my'
  if (m.sender_type === 'client') return 'other'
  return 'system'
}

const loadMe = async () => {
  try {
    me.value = await getMe()
  } catch (error) {
    console.error('Ошибка загрузки пользователя:', error)
  }
}

const loadChats = async () => {
  try {
    const token = localStorage.getItem('token')
    if (!token) return
    
    const res = await axios.get('http://127.0.0.1:8000/operator/chats/', {
      headers: { Authorization: `Bearer ${token}` }
    })
    chats.value = res.data
  } catch (error) {
    console.error('Ошибка загрузки чатов:', error)
  }
}

const loadMessages = async (chatId) => {
  try {
    const token = localStorage.getItem('token')
    if (!token) return
    
    const res = await axios.get(`http://127.0.0.1:8000/chats/${chatId}/messages`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    messages.value = res.data
    await scrollToBottom()
  } catch (error) {
    console.error('Ошибка загрузки сообщений:', error)
  }
}

const connectWebSocket = (chatId) => {
  if (socket) {
    socket.close()
    socket = null
  }
  
  const token = localStorage.getItem('token')
  if (!token) {
    console.error('Нет токена для WebSocket')
    return
  }
  
  socket = new WebSocket(`ws://127.0.0.1:8000/ws/chat/${chatId}?token=${token}`)
  
  socket.onopen = () => {
    console.log('WebSocket подключен')
  }
  
  socket.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    
    if (msg.type === 'chat_closed') {
      activeChat.value.status = 'closed'
      activeChat.value.closed_at = msg.closed_at
      const chatItem = chats.value.find(c => c.id === msg.chat_id)
      if (chatItem) {
        chatItem.status = 'closed'
      }
      
      messages.value.push({
        id: Date.now(),
        text: `🔒 Диалог закрыт оператором ${msg.closed_by}`,
        sender_type: 'system',
        type: 'system'
      })
      scrollToBottom()
    } else {
      messages.value.push(msg)
      
      const chatItem = chats.value.find(c => c.id === msg.chat_id)
      if (chatItem) {
        chatItem.last_message = msg.media_type === 'image' ? '📷 Фото' : msg.text
        chatItem.updated_at = new Date().toISOString()
      }
      scrollToBottom()
    }
  }
  
  socket.onerror = (error) => {
    console.error('WebSocket ошибка:', error)
  }
  
  socket.onclose = () => {
    console.log('WebSocket отключен')
    socket = null
    // Пробуем переподключиться через 3 секунды
    if (activeChat.value && activeChat.value.status !== 'closed') {
      setTimeout(() => {
        if (activeChat.value && activeChat.value.status !== 'closed') {
          connectWebSocket(activeChat.value.id)
        }
      }, 3000)
    }
  }
}

const openChat = async (chat) => {
  if (activeChat.value?.id === chat.id) return
  
  activeChat.value = chat
  await loadMessages(chat.id)
  connectWebSocket(chat.id)
}

const send = () => {
  if (!text.value.trim()) return
  
  // Если сокет не подключен, показываем сообщение
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    console.error('WebSocket не подключен')
    alert('Подключение к чату... Подождите секунду')
    return
  }

  socket.send(JSON.stringify({
    text: text.value.trim()
  }))
  text.value = ""
  scrollToBottom()
}

const closeChat = async () => {
  if (!confirm('Закрыть диалог? Клиент сможет оценить качество обслуживания.')) {
    return
  }
  
  isClosing.value = true
  
  try {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        action: 'close_chat'
      }))
    }
    
    const token = localStorage.getItem('token')
    await axios.post(`http://127.0.0.1:8000/chat/${activeChat.value.id}/close`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    activeChat.value.status = 'closed'
    activeChat.value.closed_at = new Date().toISOString()
    const chatItem = chats.value.find(c => c.id === activeChat.value.id)
    if (chatItem) {
      chatItem.status = 'closed'
    }
    
    messages.value.push({
      id: Date.now(),
      text: `🔒 Диалог закрыт`,
      sender_type: 'system',
      type: 'system'
    })
    scrollToBottom()
    
  } catch (error) {
    console.error('Ошибка закрытия чата:', error)
    alert('Не удалось закрыть диалог')
  } finally {
    isClosing.value = false
  }
}

const triggerPhotoUpload = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    
    if (file.size > 10 * 1024 * 1024) {
      alert('Файл слишком большой. Максимум 10MB')
      return
    }
    
    await uploadPhoto(file)
  }
  input.click()
}

const uploadPhoto = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('chat_id', activeChat.value.id)

  try {
    const token = localStorage.getItem('token')
    await axios.post('http://127.0.0.1:8000/upload/photo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${token}`
      }
    })
  } catch (error) {
    console.error('Ошибка отправки фото:', error)
    alert('Не удалось отправить фото')
  }
}

const openImage = (url) => {
  selectedImage.value = url
  showImageModal.value = true
}

const closeImage = () => {
  showImageModal.value = false
  selectedImage.value = ""
}

const handleImageError = (message) => {
  console.error('Ошибка загрузки фото:', message)
  message.media_url = null
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesBox.value) {
    messagesBox.value.scrollTop = messagesBox.value.scrollHeight
  }
}

onMounted(async () => {
  await loadMe()
  await loadChats()
  
  refreshInterval = setInterval(() => {
    if (activeChat.value?.status !== 'closed') {
      loadChats()
    }
  }, 30000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
  if (socket) socket.close()
})
</script>