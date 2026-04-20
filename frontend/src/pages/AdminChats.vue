<template>
  <div class="admin-page">
    <div class="page-header">
      <h1>📋 Распределение чатов</h1>
      <div class="stats">
        <div class="stat-card">
          <span class="stat-value">{{ filteredChats.length }}</span>
          <span class="stat-label">Найдено чатов</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ operators.length }}</span>
          <span class="stat-label">Операторов</span>
        </div>
      </div>
    </div>

    <!-- ПОИСК ЧАТОВ -->
    <div class="search-chats-section">
      <div class="search-chats-container">
        <input
          type="text"
          v-model="chatSearchQuery"
          placeholder="🔍 Поиск чатов по ID, названию, клиентам или операторам..."
          class="search-chats-input"
        />
        <button v-if="chatSearchQuery" class="clear-search-btn" @click="clearSearch">
          ✕
        </button>
      </div>
      <div class="search-stats" v-if="chatSearchQuery">
        Найдено {{ filteredChats.length }} из {{ chats.length }} чатов
      </div>
    </div>

    <div v-for="chat in filteredChats" :key="chat.id" class="chat-card">
      <div class="chat-header">
        <div class="chat-icon">
          💬
        </div>
        <div class="info">
          <b class="chat-title">{{ chat.title || ('Чат #' + chat.id) }}</b>
          <div class="chat-meta">
            <span class="meta-badge">ID: {{ chat.id }}</span>
          </div>
        </div>
      </div>

      <div class="chat-body">
        <div class="clients-section">
          <div class="section-title">
            👥 Клиенты
            <span class="count">{{ (chat.clients || []).length }}</span>
          </div>
          <div class="clients-list">
            <span v-for="client in (chat.clients || [])" :key="client" class="client-tag">
              {{ client }}
            </span>
            <span v-if="!chat.clients || chat.clients.length === 0" class="empty-text">
              Нет клиентов
            </span>
          </div>
        </div>

        <div class="operators-section">
          <div class="section-title">
            👨‍💻 Операторы
            <span class="count">{{ (chat.operators || []).length }}</span>
          </div>
          <div class="operators-list">
            <div v-if="chat.operators && chat.operators.length" class="operators-grid">
              <span v-for="op in chat.operators" :key="op" class="operator-tag">
                👤 {{ op }}
                <button class="remove-btn" @click="remove(chat.id, op)" title="Удалить оператора">
                  ✕
                </button>
              </span>
            </div>
            <div v-else class="empty-text">Нет операторов</div>
          </div>
        </div>
      </div>

      <div class="chat-footer">
        <div class="assign-section">
          <div class="search-container">
            <div class="custom-select" :class="{ 'is-open': openDropdown === chat.id }">
              <div class="select-trigger" @click="toggleDropdown(chat.id)">
                <span class="selected-value">
                  {{ selectedUser[chat.id] || 'Выберите оператора' }}
                </span>
                <span class="arrow">▼</span>
              </div>
              
              <teleport to="body">
                <div 
                  v-if="openDropdown === chat.id" 
                  class="select-dropdown-global"
                  :style="dropdownStyle"
                  @click.stop
                >
                  <div class="search-box">
                    <input
                      type="text"
                      v-model="operatorSearch[chat.id]"
                      @input="filterOperators(chat.id)"
                      placeholder="🔍 Поиск оператора..."
                      class="search-input"
                      @click.stop
                      autofocus
                    />
                  </div>
                  
                  <div class="options-list">
                    <div
                      v-for="op in filteredOperators[chat.id]"
                      :key="op.id"
                      class="option-item"
                      @click="selectOperator(chat.id, op.username)"
                    >
                      <div class="option-name">👤 {{ op.username }}</div>
                      <div class="option-email">{{ op.email || '' }}</div>
                    </div>
                    <div v-if="filteredOperators[chat.id].length === 0" class="no-options">
                      Операторы не найдены
                    </div>
                  </div>
                </div>
              </teleport>
            </div>
          </div>
          
          <button 
            class="assign-btn" 
            @click="assign(chat.id)"
            :disabled="!selectedUser[chat.id]"
          >
            ✚ Назначить
          </button>
        </div>
      </div>
    </div>

    <div v-if="filteredChats.length === 0" class="empty-state">
      <div class="empty-icon">🔍</div>
      <p>Чаты не найдены</p>
      <span v-if="chatSearchQuery">Попробуйте изменить поисковый запрос</span>
      <span v-else>Нет активных чатов</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { fetchChats, assignChat, fetchOperators, removeOperator } from '../api/adminChatApi'
import '/style/adminPanel.css'
const chats = ref([])
const operators = ref([])
const selectedUser = ref({})
const operatorSearch = ref({})
const filteredOperators = ref({})
const openDropdown = ref(null)
const dropdownStyle = ref({})
const chatSearchQuery = ref('')

// Фильтрация чатов
const filteredChats = computed(() => {
  if (!chatSearchQuery.value.trim()) {
    return chats.value
  }
  
  const query = chatSearchQuery.value.toLowerCase().trim()
  
  return chats.value.filter(chat => {
    // Поиск по ID
    if (chat.id.toString().includes(query)) return true
    
    // Поиск по названию
    if (chat.title && chat.title.toLowerCase().includes(query)) return true
    
    // Поиск по клиентам
    if (chat.clients && chat.clients.some(client => 
      client.toLowerCase().includes(query)
    )) return true
    
    // Поиск по операторам
    if (chat.operators && chat.operators.some(operator => 
      operator.toLowerCase().includes(query)
    )) return true
    
    return false
  })
})

const clearSearch = () => {
  chatSearchQuery.value = ''
}

const load = async () => {
  chats.value = await fetchChats()
  operators.value = await fetchOperators()
  
  // Инициализация фильтров для каждого чата
  chats.value.forEach(chat => {
    if (!filteredOperators.value[chat.id]) {
      filteredOperators.value[chat.id] = [...operators.value]
    }
    if (!operatorSearch.value[chat.id]) {
      operatorSearch.value[chat.id] = ''
    }
  })
}

const toggleDropdown = async (chatId) => {
  if (openDropdown.value === chatId) {
    closeDropdown()
  } else {
    closeDropdown()
    openDropdown.value = chatId
    
    // Сбрасываем поиск при открытии
    operatorSearch.value[chatId] = ''
    filteredOperators.value[chatId] = [...operators.value]
    
    // Ждем отрисовки и вычисляем позицию
    await nextTick()
    calculateDropdownPosition(chatId)
    
    // Закрываем при клике вне
    setTimeout(() => {
      document.addEventListener('click', closeDropdownOnClickOutside)
    }, 0)
  }
}

const calculateDropdownPosition = (chatId) => {
  // Находим триггер для этого чата
  const trigger = document.querySelector(`.custom-select.is-open .select-trigger`)
  if (trigger) {
    const rect = trigger.getBoundingClientRect()
    dropdownStyle.value = {
      top: `${rect.bottom + window.scrollY + 5}px`,
      left: `${rect.left + window.scrollX}px`,
      width: `${rect.width}px`
    }
  }
}

const closeDropdown = () => {
  openDropdown.value = null
  document.removeEventListener('click', closeDropdownOnClickOutside)
}

const closeDropdownOnClickOutside = (event) => {
  if (!event.target.closest('.custom-select') && !event.target.closest('.select-dropdown-global')) {
    closeDropdown()
  }
}

const filterOperators = (chatId) => {
  const searchTerm = operatorSearch.value[chatId]?.toLowerCase() || ''
  
  if (searchTerm === '') {
    filteredOperators.value[chatId] = [...operators.value]
  } else {
    filteredOperators.value[chatId] = operators.value.filter(op => 
      op.username.toLowerCase().includes(searchTerm) ||
      (op.email && op.email.toLowerCase().includes(searchTerm))
    )
  }
}

const selectOperator = (chatId, username) => {
  selectedUser.value[chatId] = username
  closeDropdown()
}

const remove = async (chatId, username) => {
  if (confirm(`Удалить оператора ${username} из этого чата?`)) {
    await removeOperator(chatId, username)
    await load()
  }
}

const assign = async (chatId) => {
  const username = selectedUser.value[chatId]

  if (!username) {
    alert("Выберите оператора")
    return
  }

  await assignChat(chatId, username)
  await load()
  
  // Очистка полей после назначения
  selectedUser.value[chatId] = ''
  operatorSearch.value[chatId] = ''
  filteredOperators.value[chatId] = [...operators.value]
}

onMounted(load)
</script>

