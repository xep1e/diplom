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

const chats = ref([])
const activeChat = ref(null)
const messages = ref([])
const text = ref("")
const me = ref({})

let socket = null
const messagesBox = ref(null)


// 🔥 загрузка пользователя
const loadMe = async () => {
  me.value = await getMe()
}

// 🔥 загрузка чатов
const loadChats = async () => {
  const res = await axios.get('http://127.0.0.1:8000/operator/chats/', {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  })

  chats.value = res.data
}

// 🔥 загрузка истории
const loadMessages = async (chatId) => {
  const res = await axios.get(`http://127.0.0.1:8000/chats/${chatId}/messages`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  })

  messages.value = res.data
  scrollDown()
}

// 🔥 открыть чат
const openChat = async (chat) => {
  activeChat.value = chat

  if (socket) socket.close()

  await loadMessages(chat.id)

  const token = localStorage.getItem('token')

  socket = new WebSocket(`ws://127.0.0.1:8000/ws/chat/${chat.id}?token=${token}`)

  socket.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    messages.value.push(msg)
    scrollDown()
  }
}

// 🔥 отправка
const send = () => {
  if (!text.value || !socket) return

  socket.send(JSON.stringify({
    text: text.value
  }))

  text.value = ""
}

// 🔥 автоскролл
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

<style>
.chat-layout {
  display: flex;
  height: 100vh;
  background: #0f172a;
  color: white;
}

/* LEFT */
.chat-list {
  width: 320px;
  border-right: 1px solid #1e293b;
  overflow-y: auto;
}

.chat-item {
  padding: 12px;
  cursor: pointer;
  border-bottom: 1px solid #1e293b;
}

.chat-item:hover {
  background: #1e293b;
}

.last {
  font-size: 12px;
  color: #94a3b8;
}

/* RIGHT */
.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* HEADER */
.header {
  padding: 15px;
  border-bottom: 1px solid #1e293b;
  font-weight: bold;
}

/* MESSAGES */
.messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

/* MESSAGE */
.msg {
  padding: 10px 14px;
  margin-bottom: 10px;
  border-radius: 12px;
  max-width: 60%;
  word-break: break-word;
}

/* мои */
.msg.my {
  background: #3b82f6;
  margin-left: auto;
}

/* чужие */
.msg.other {
  background: #1e293b;
  margin-right: auto;
}

.sender {
  font-size: 11px;
  opacity: 0.6;
  margin-bottom: 4px;
}

/* INPUT */
.input {
  display: flex;
  padding: 10px;
  border-top: 1px solid #1e293b;
}

.input input {
  flex: 1;
  padding: 10px;
  border-radius: 8px;
  border: none;
}

.input button {
  margin-left: 10px;
  padding: 10px 15px;
  background: #3b82f6;
  border: none;
  color: white;
  border-radius: 8px;
}
</style>