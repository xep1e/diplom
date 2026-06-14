<template>
  <div class="profile-container">
    <div class="profile-card">
      <h1>Профиль</h1>
      
      <div v-if="user" class="user-info">
        <div class="info-row">
          <span class="label">Имя пользователя:</span>
          <span class="value">{{ user.username }}</span>
        </div>
        
        <div class="info-row">
          <span class="label">Роль:</span>
          <span class="value">{{ user.role }}</span>
        </div>
        
        <div class="info-row">
          <span class="label">Bitrix24:</span>
          <div class="bitrix-status">
            <span v-if="user.bitrix_connected" class="status-connected">
              ✅ Подключен (ID: {{ user.bitrix_user_id }})
            </span>
            <span v-else class="status-disconnected">
              ⚠️ Не подключен
            </span>
          </div>
        </div>
        
        <!-- Кнопка подключения -->
        <button 
          v-if="!user.bitrix_connected" 
          @click="connectBitrix" 
          :disabled="loading"
          class="connect-btn"
        >
          {{ loading ? 'Подключение...' : '🔗 Подключить Bitrix24' }}
        </button>
      </div>
      
      <div v-if="status" :class="['status-message', statusType]">
        {{ status }}
      </div>
      
      <button @click="logout" class="logout-btn">
        Выйти
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const user = ref(null)
const loading = ref(false)
const status = ref('')
const statusType = ref('')

const API_URL = 'http://127.0.0.1:8000'

// Загружаем данные пользователя
const loadUser = async () => {
  const token = localStorage.getItem('token')
  if (!token) {
    router.push('/login')
    return
  }
  
  try {
    const res = await axios.get(`${API_URL}/api/users/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    user.value = res.data
  } catch (error) {
    console.error('Ошибка загрузки профиля:', error)
    localStorage.removeItem('token')
    router.push('/login')
  }
}

// Подключение к Bitrix
const connectBitrix = async () => {
  loading.value = true
  const token = localStorage.getItem('token')
  
  try {
    const res = await axios.get(`${API_URL}/bitrix/connect`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    // Редиректим на Bitrix OAuth
    window.location.href = res.data.url
  } catch (error) {
    console.error('Ошибка подключения:', error)
    status.value = error.response?.data?.detail || 'Ошибка подключения к Bitrix'
    statusType.value = 'error'
    loading.value = false
  }
}

// Выход
const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}

// Проверяем параметры в URL (возврат из Bitrix)
onMounted(() => {
  loadUser()
  
  if (route.query.bitrix === 'success') {
    status.value = '✅ Bitrix успешно подключен!'
    statusType.value = 'success'
    loadUser() // Перезагружаем данные
  }
  
  if (route.query.bitrix === 'error_token') {
    status.value = '❌ Ошибка подключения Bitrix: не удалось получить токен'
    statusType.value = 'error'
  }
  
  if (route.query.bitrix === 'error_user') {
    status.value = '❌ Ошибка: пользователь не найден'
    statusType.value = 'error'
  }
  
  // Убираем параметры из URL
  if (route.query.bitrix) {
    router.replace('/profile')
  }
})
</script>

<style scoped>
.profile-container {
  max-width: 600px;
  margin: 50px auto;
  padding: 20px;
}

.profile-card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

h1 {
  margin: 0 0 30px 0;
  color: #333;
}

.user-info {
  margin-bottom: 30px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}

.label {
  font-weight: 600;
  color: #666;
}

.value {
  color: #333;
}

.bitrix-status {
  font-size: 14px;
}

.status-connected {
  color: #10b981;
}

.status-disconnected {
  color: #ef4444;
}

.connect-btn {
  width: 100%;
  padding: 12px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  margin-top: 20px;
  transition: background 0.2s;
}

.connect-btn:hover:not(:disabled) {
  background: #2563eb;
}

.connect-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.logout-btn {
  width: 100%;
  padding: 12px;
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  margin-top: 20px;
  transition: background 0.2s;
}

.logout-btn:hover {
  background: #e5e7eb;
}

.status-message {
  margin-top: 20px;
  padding: 12px;
  border-radius: 8px;
  text-align: center;
}

.status-message.success {
  background: #d1fae5;
  color: #065f46;
}

.status-message.error {
  background: #fee2e2;
  color: #991b1b;
}
</style>