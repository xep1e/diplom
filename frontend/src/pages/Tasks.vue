<template>
  <div class="tasks-container">
    <h1>Мои задачи из Битрикс24</h1>
    
    <!-- Индикатор загрузки -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Загрузка задач...</p>
    </div>
    
    <!-- Сообщение об ошибке -->
    <div v-else-if="error" class="error-message">
      <p>⚠️ {{ error }}</p>
      <button @click="loadTasks" class="retry-btn">Повторить</button>
    </div>
    
    <!-- Информация о подключении -->
    <div v-else-if="!hasBitrixId" class="info-message">
      <p>❌ Bitrix ID не назначен</p>
      <p>Обратитесь к администратору для настройки интеграции с Битрикс24</p>
    </div>
    
    <!-- Список задач -->
    <div v-else-if="tasks.length === 0" class="empty-state">
      <p>📭 У вас нет активных задач</p>
      <p>Задачи будут появляться здесь после назначения</p>
    </div>
    
    <div v-else class="tasks-list">
      <div 
        v-for="task in tasks" 
        :key="task.id" 
        :class="['task-card', `status-${task.status}`]"
      >
        <div class="task-header">
          <h3>{{ task.title }}</h3>
          <span :class="['status-badge', `status-${task.status}`]">
            {{ task.status_label }}
          </span>
        </div>
        
        <div class="task-body">
          <div class="task-description" v-if="task.description">
            {{ truncateText(task.description, 200) }}
          </div>
          
          <div class="task-meta">
            <div class="meta-item" v-if="task.created_date">
              <span class="label">📅 Создана:</span>
              <span>{{ formatDate(task.created_date) }}</span>
            </div>
            <div class="meta-item" v-if="task.deadline">
              <span class="label">⏰ Дедлайн:</span>
              <span :class="{ 'deadline-overdue': isOverdue(task.deadline) }">
                {{ formatDate(task.deadline) }}
              </span>
            </div>
          </div>
          
          <div class="task-actions">
            <select 
              v-model="task.newStatus" 
              @change="updateStatus(task)"
              class="status-select"
            >
              <option value="1">Новая</option>
              <option value="2">В работе</option>
              <option value="3">Проверка</option>
              <option value="4">Завершена</option>
              <option value="5">Отклонена</option>
              <option value="6">Отложена</option>
            </select>
            
            <a 
              :href="`https://b24-rej6pr.bitrix24.ru/workgroups/group/1/tasks/task/view/${task.id}/`" 
              target="_blank" 
              class="open-btn"
            >
              Открыть в Битрикс24 ↗
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { getMe } from '../api/authApi'

const API_URL = 'http://127.0.0.1:8000'
const tasks = ref([])
const loading = ref(false)
const error = ref(null)
const currentUser = ref(null)
const hasBitrixId = ref(false)

// Загружаем задачи
const loadTasks = async () => {
  loading.value = true
  error.value = null
  
  try {
    const token = localStorage.getItem('token')
    
    // Сначала получаем инфо о пользователе
    const userRes = await axios.get(`${API_URL}/api/users/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    currentUser.value = userRes.data
    hasBitrixId.value = !!currentUser.value.bitrix_user_id
    
    if (!hasBitrixId.value) {
      loading.value = false
      return
    }
    
    // Получаем задачи
    const tasksRes = await axios.get(`${API_URL}/bitrix/my-tasks`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (tasksRes.data.ok) {
      tasks.value = tasksRes.data.tasks.map(task => ({
        ...task,
        newStatus: task.status
      }))
    } else {
      error.value = tasksRes.data.error || 'Ошибка загрузки задач'
    }
    
  } catch (err) {
    console.error('Ошибка загрузки задач:', err)
    error.value = err.response?.data?.detail || 'Не удалось загрузить задачи'
  } finally {
    loading.value = false
  }
}

// Обновляем статус задачи
const updateStatus = async (task) => {
  if (task.newStatus === task.status) return
  
  try {
    const token = localStorage.getItem('token')
    const res = await axios.post(
      `${API_URL}/bitrix/update-task-status`,
      null,
      {
        params: { task_id: task.id, status: task.newStatus },
        headers: { Authorization: `Bearer ${token}` }
      }
    )
    
    if (res.data.ok) {
      task.status = task.newStatus
      task.status_label = getStatusLabel(task.newStatus)
      // Показываем уведомление
      showNotification('Статус обновлен', 'success')
    } else {
      showNotification('Ошибка обновления статуса', 'error')
      task.newStatus = task.status
    }
  } catch (err) {
    console.error('Ошибка:', err)
    showNotification('Ошибка обновления статуса', 'error')
    task.newStatus = task.status
  }
}

// Вспомогательные функции
const getStatusLabel = (status) => {
  const map = {
    '1': 'Новая',
    '2': 'Выполняется',
    '3': 'Проверка',
    '4': 'Завершена',
    '5': 'Отклонена',
    '6': 'Отложена'
  }
  return map[status] || 'Неизвестно'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const isOverdue = (deadlineStr) => {
  if (!deadlineStr) return false
  const deadline = new Date(deadlineStr)
  const now = new Date()
  return deadline < now
}

const truncateText = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const showNotification = (message, type) => {
  // Простой alert, можешь заменить на красивый тост
  alert(message)
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.tasks-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  margin-bottom: 30px;
  color: #333;
}

.loading {
  text-align: center;
  padding: 50px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message, .info-message, .empty-state {
  text-align: center;
  padding: 50px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.error-message {
  color: #ef4444;
}

.info-message {
  color: #f59e0b;
}

.empty-state {
  color: #6b7280;
}

.retry-btn {
  margin-top: 20px;
  padding: 8px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.task-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border-left: 4px solid #ccc;
  transition: transform 0.2s, box-shadow 0.2s;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.task-card.status-1 {
  border-left-color: #3b82f6;
}

.task-card.status-2 {
  border-left-color: #f59e0b;
}

.task-card.status-3 {
  border-left-color: #8b5cf6;
}

.task-card.status-4 {
  border-left-color: #10b981;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 15px;
}

.task-header h3 {
  margin: 0;
  color: #333;
  font-size: 18px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.status-1 {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.status-2 {
  background: #fed7aa;
  color: #9a3412;
}

.status-badge.status-3 {
  background: #e9d5ff;
  color: #5b21b6;
}

.status-badge.status-4 {
  background: #d1fae5;
  color: #065f46;
}

.task-body {
  margin-top: 10px;
}

.task-description {
  color: #4b5563;
  line-height: 1.5;
  margin-bottom: 15px;
}

.task-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
  font-size: 13px;
  color: #6b7280;
}

.meta-item {
  display: flex;
  gap: 5px;
}

.label {
  font-weight: 600;
}

.deadline-overdue {
  color: #ef4444;
  font-weight: 600;
}

.task-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e5e7eb;
}

.status-select {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}

.open-btn {
  padding: 6px 12px;
  background: #f3f4f6;
  color: #374151;
  text-decoration: none;
  border-radius: 6px;
  font-size: 13px;
  transition: background 0.2s;
}

.open-btn:hover {
  background: #e5e7eb;
}
</style>