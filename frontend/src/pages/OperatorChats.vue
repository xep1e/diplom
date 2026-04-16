<template>
  <div class="chat-layout">

    <!-- LEFT -->
    <div class="chat-list">
      <div
        v-for="chat in chats"
        :key="chat.id"
        class="chat-item"
        @click="openChat(chat)"
      >
        <b>{{ chat.title }}</b>
        <p class="last">{{ chat.last_message }}</p>
      </div>
    </div>

    <!-- RIGHT -->
    <div class="chat-window">
      <div v-if="activeChat">
        <h2>{{ activeChat.title }}</h2>

        <div class="messages">
          <div v-for="m in messages" :key="m.id">
            {{ m.text }}
          </div>
        </div>
      </div>

      <div v-else>
        Выбери чат 👈
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const chats = ref([])
const activeChat = ref(null)
const messages = ref([])

const loadChats = async () => {
  const res = await axios.get('http://127.0.0.1:8000/operator/chats/', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('token')}`
    }
  })

  chats.value = res.data
}

const openChat = async (chat) => {
  activeChat.value = chat

  const res = await axios.get(
    `http://127.0.0.1:8000/chats/${chat.id}/messages`,
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    }
  )

  messages.value = res.data
}

onMounted(loadChats)
</script>

<style>
.chat-layout {
  display: flex;
  height: 100vh;
}

.chat-list {
  width: 300px;
  border-right: 1px solid #ddd;
  overflow-y: auto;
}

.chat-item {
  padding: 10px;
  cursor: pointer;
  border-bottom: 1px solid #eee;
}

.chat-item:hover {
  background: #f5f5f5;
}

.last {
  font-size: 12px;
  color: gray;
}

.chat-window {
  flex: 1;
  padding: 20px;
}
</style>