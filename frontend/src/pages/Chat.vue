<template>
  <div class="chat-layout">

    <!-- LEFT -->
    <div class="chat-list">
      <div
        v-for="c in chats"
        :key="c.id"
        class="chat-item"
        @click="openChat(c)"
      >
        <b>{{ c.title }}</b>
        <p class="last">{{ c.last_message }}</p>
      </div>
    </div>

    <!-- RIGHT -->
    <div class="chat-window" v-if="activeChat">

      <div class="header">
        {{ activeChat.title }}
      </div>

      <div class="messages" ref="messagesBox">
        <div
          v-for="m in messages"
          :key="m.id"
          :class="['msg', m.sender === me.username ? 'my' : 'other']"
        >
          <div class="sender">{{ m.sender }}</div>
          {{ m.text }}
        </div>
      </div>

      <div class="input">
        <input v-model="text" @keyup.enter="send" placeholder="Сообщение..." />
        <button @click="send">➤</button>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'
import { getMe } from '../api/authApi'

// Импорт стилей
import '/style/chat.css'

const chats = ref([])
const activeChat = ref(null)
const messages = ref([])
const text = ref("")
const me = ref({})

let socket = null
const messagesBox = ref(null)

// загрузка пользователя
const loadMe = async () => {
  me.value = await getMe()
}

// загрузка чатов
const loadChats = async () => {
  const res = await axios.get('http://127.0.0.1:8000/operator/chats/', {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  })

  chats.value = res.data
}

// загрузка истории
const loadMessages = async (chatId) => {
  const res = await axios.get(`http://127.0.0.1:8000/chats/${chatId}/messages`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  })

  messages.value = res.data
  scrollDown()
}

// открыть чат
const openChat = async (chat) => {
  activeChat.value = chat

  if (socket) socket.close()

  await loadMessages(chat.id)

  const token = localStorage.getItem('token')

  socket = new WebSocket(`ws://127.0.0.1:8000/ws/chat/${chat.id}?token=${token}`)

  socket.onmessage = (event) => {
    const msg = JSON.parse(event.data)

    messages.value.push(msg)

    // обновляем список чатов
    const chatItem = chats.value.find(c => c.id === msg.chat_id)
    if (chatItem) {
      chatItem.last_message = msg.text
    }

    scrollDown()
  }
}

// отправка
const send = () => {
  if (!text.value || !socket) return

  socket.send(JSON.stringify({
    text: text.value
  }))

  text.value = ""
}

// автоскролл
const scrollDown = async () => {
  await nextTick()
  if (messagesBox.value) {
    messagesBox.value.scrollTop = messagesBox.value.scrollHeight
  }
}

onMounted(async () => {
  await loadMe()
  await loadChats()
})
</script>