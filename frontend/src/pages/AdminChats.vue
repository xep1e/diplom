<template>
  <div class="admin-page">
    <h1>Распределение чатов</h1>

    <div v-for="chat in chats" :key="chat.id" class="chat-card">

      <div class="info">
        <b>{{ chat.title || ('Чат #' + chat.id) }}</b>

        <p>👥 Клиенты: {{ (chat.clients || []).join(', ') || '—' }}</p>
        <div class="operators">
          <p>👨‍💻 Операторы:</p>

          <div v-if="chat.operators && chat.operators.length">
            <span v-for="op in chat.operators" :key="op" class="operator-tag">
              {{ op }}

              <button class="remove-btn" @click="remove(chat.id, op)">
                ❌
              </button>
            </span>
          </div>

          <div v-else>—</div>
        </div>

      </div>

      <div class="actions">
        <select v-model="selectedUser[chat.id]">
          <option disabled value="">Выбери оператора</option>

          <option v-for="op in operators" :key="op.id" :value="op.username">
            {{ op.username }}
          </option>
        </select>

        <button @click="assign(chat.id)">
          Назначить
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

import { fetchChats, assignChat, fetchOperators, removeOperator } from '../api/adminChatApi'

const chats = ref([])
const operators = ref([])
const selectedUser = ref({})

const load = async () => {
  chats.value = await fetchChats()
  operators.value = await fetchOperators()
}

const remove = async (chatId, username) => {
  await removeOperator(chatId, username)
  await load()
}

const assign = async (chatId) => {
  const username = selectedUser.value[chatId]

  if (!username) {
    alert("Введите логин оператора")
    return
  }

  await assignChat(chatId, username)
  await load()
}

onMounted(load)
</script>