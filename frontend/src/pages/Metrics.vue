<template>
  <div class="metrics-page">
    <div class="page-header">
      <h1>📊 Метрики сотрудников</h1>
      <div class="header-stats">
        <div class="stat-card">
          <span class="stat-value">{{ operators.length }}</span>
          <span class="stat-label">Сотрудников</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ totalRedZone }}</span>
          <span class="stat-label">Красная зона</span>
        </div>
      </div>
    </div>

    <!-- Поиск -->
    <div class="search-section">
      <div class="search-container">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="🔍 Поиск по имени сотрудника..."
          class="search-input"
        />
        <button v-if="searchQuery" class="clear-search" @click="searchQuery = ''">
          ✕
        </button>
      </div>
      <div class="filter-buttons">
        <button 
          class="filter-btn" 
          :class="{ active: filterType === 'all' }"
          @click="filterType = 'all'"
        >
          Все ({{ operators.length }})
        </button>
        <button 
          class="filter-btn red" 
          :class="{ active: filterType === 'red' }"
          @click="filterType = 'red'"
        >
          🔴 Красная зона ({{ redZoneCount }})
        </button>
        <button 
          class="filter-btn top" 
          :class="{ active: filterType === 'top' }"
          @click="filterType = 'top'"
        >
          ⭐ Топ-3
        </button>
      </div>
    </div>

    <!-- Таблица сотрудников -->
    <div class="table-container">
      <table class="metrics-table">
        <thead>
          <tr>
            <th>Сотрудник</th>
            <th>Чатов</th>
            <th>Ср. время ответа</th>
            <th>Закрыто за 7 дней</th>
            <th>Ср. время решения</th>
            <th class="red-zone-col">Красная зона</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="op in filteredOperators" 
            :key="op.id"
            :class="{ 'red-zone-row': op.red_zone_count > 0 }"
          >
            <td class="operator-cell">
              <div class="operator-info">
                <div class="operator-avatar">
                  {{ op.username.charAt(0).toUpperCase() }}
                </div>
                <div class="operator-details">
                  <span class="operator-name">{{ op.username }}</span>
                  <span class="operator-role">Оператор</span>
                </div>
              </div>
            </td>
            <td>{{ op.total_chats }}</td>
            <td>
              <span :class="getResponseTimeClass(op.avg_response_time)">
                {{ formatTime(op.avg_response_time) }}
              </span>
            </td>
            <td>{{ op.closed_chats }}</td>
            <td>{{ formatTimeMinutes(op.avg_resolution_time) }}</td>
            <td class="red-zone-cell">
              <div v-if="op.red_zone_count > 0" class="red-zone-badge">
                🔴 {{ op.red_zone_count }}
                <button class="show-details-btn" @click="showRedZoneDetails(op)">
                  👁️
                </button>
              </div>
              <span v-else class="green-badge">✅ Нет</span>
            </td>
            <td>
              <button class="details-btn" @click="showOperatorDetails(op)">
                Подробнее
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Модальное окно с деталями красной зоны -->
    <div v-if="selectedRedZone" class="modal" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>🔴 Красная зона - {{ selectedRedZone.username }}</h2>
          <button class="close-btn" @click="closeModal">✕</button>
        </div>
        <div class="modal-body">
          <div class="warning-message">
            ⚠️ Просроченные ответы (более 1 минуты)
          </div>
          <div class="red-zone-list">
            <div v-for="(msg, idx) in selectedRedZone.red_zone_messages" :key="idx" class="red-zone-item">
              <div class="message-header">
                <span class="chat-id">Чат #{{ msg.chat_id }}</span>
                <span class="response-time">⏱️ {{ msg.response_time_seconds }} сек.</span>
                <span class="message-time">📅 {{ msg.created_at }}</span>
              </div>
              <div class="message-text">
                "{{ msg.client_message }}"
              </div>
            </div>
            <div v-if="selectedRedZone.red_zone_messages.length === 0" class="no-messages">
              Нет просроченных сообщений
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно с деталями оператора -->
    <div v-if="selectedOperator" class="modal" @click="closeOperatorModal">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h2>📈 Детальная статистика - {{ selectedOperator.username }}</h2>
          <button class="close-btn" @click="closeOperatorModal">✕</button>
        </div>
        <div class="modal-body">
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-label">Всего чатов</div>
              <div class="stat-number">{{ selectedOperator.total_chats }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Среднее время ответа</div>
              <div class="stat-number">{{ formatTime(selectedOperator.avg_response_time) }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Закрыто чатов (7 дней)</div>
              <div class="stat-number">{{ selectedOperator.closed_chats }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Среднее время решения</div>
              <div class="stat-number">{{ formatTimeMinutes(selectedOperator.avg_resolution_time) }}</div>
            </div>
          </div>
          
          <div class="chart-container">
            <h3>Активность за последние 7 дней</h3>
            <div class="activity-chart">
              <div v-for="day in operatorDetails" :key="day.date" class="chart-bar-container">
                <div class="chart-bar" :style="{ height: getBarHeight(day.messages) + 'px' }">
                  <span class="bar-value">{{ day.messages }}</span>
                </div>
                <div class="chart-label">{{ formatDate(day.date) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const operators = ref([])
const searchQuery = ref('')
const filterType = ref('all')
const selectedRedZone = ref(null)
const selectedOperator = ref(null)
const operatorDetails = ref([])

// Загрузка метрик
const loadMetrics = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get('http://127.0.0.1:8000/metrics/operators', {
      headers: { Authorization: `Bearer ${token}` }
    })
    operators.value = res.data
  } catch (error) {
    console.error('Ошибка загрузки метрик:', error)
  }
}

// Фильтрация
const filteredOperators = computed(() => {
  let filtered = operators.value
  
  // Поиск
  if (searchQuery.value) {
    filtered = filtered.filter(op => 
      op.username.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }
  
  // Фильтр по типу
  if (filterType.value === 'red') {
    filtered = filtered.filter(op => op.red_zone_count > 0)
  } else if (filterType.value === 'top') {
    filtered = [...filtered].sort((a, b) => 
      (b.closed_chats || 0) - (a.closed_chats || 0)
    ).slice(0, 3)
  }
  
  return filtered
})

// Подсчет красной зоны
const redZoneCount = computed(() => {
  return operators.value.filter(op => op.red_zone_count > 0).length
})

const totalRedZone = computed(() => {
  return operators.value.reduce((sum, op) => sum + (op.red_zone_count || 0), 0)
})

// Форматирование времени
const formatTime = (seconds) => {
  if (!seconds) return '—'
  if (seconds < 60) return `${Math.round(seconds)} сек`
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes} мин ${Math.round(secs)} сек`
}

const formatTimeMinutes = (minutes) => {
  if (!minutes) return '—'
  if (minutes < 60) return `${minutes} мин`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return `${hours} ч ${mins} мин`
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return `${date.getDate()}/${date.getMonth() + 1}`
}

// Класс для времени ответа
const getResponseTimeClass = (seconds) => {
  if (!seconds) return 'time-unknown'
  if (seconds > 60) return 'time-bad'
  if (seconds > 30) return 'time-warning'
  return 'time-good'
}

// Высота бара в графике
const getBarHeight = (count) => {
  const maxCount = Math.max(...operatorDetails.value.map(d => d.messages), 1)
  return Math.min(100, (count / maxCount) * 80) + 20
}

// Показать детали красной зоны
const showRedZoneDetails = (operator) => {
  selectedRedZone.value = operator
}

// Показать детали оператора
const showOperatorDetails = async (operator) => {
  selectedOperator.value = operator
  
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(`http://127.0.0.1:8000/metrics/operators/${operator.id}/details`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    operatorDetails.value = res.data.last_7_days.reverse()
  } catch (error) {
    console.error('Ошибка загрузки деталей:', error)
  }
}

// Закрыть модалки
const closeModal = () => {
  selectedRedZone.value = null
}

const closeOperatorModal = () => {
  selectedOperator.value = null
  operatorDetails.value = []
}

onMounted(() => {
  loadMetrics()
})
</script>

<style scoped>
.metrics-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #2c3e50;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-card {
  text-align: center;
  padding: 8px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  color: white;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  display: block;
}

.stat-label {
  font-size: 12px;
  opacity: 0.9;
}

.search-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.search-container {
  position: relative;
  margin-bottom: 16px;
}

.search-input {
  width: 100%;
  padding: 12px 40px 12px 16px;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.clear-search {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  font-size: 18px;
}

.filter-buttons {
  display: flex;
  gap: 12px;
}

.filter-btn {
  padding: 8px 20px;
  border: 1px solid #e1e5e9;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.filter-btn:hover {
  border-color: #667eea;
}

.filter-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
}

.filter-btn.red.active {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.filter-btn.top.active {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.table-container {
  background: white;
  border-radius: 12px;
  overflow-x: auto;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.metrics-table {
  width: 100%;
  border-collapse: collapse;
}

.metrics-table th {
  padding: 16px;
  text-align: left;
  background: #f8f9fa;
  color: #2c3e50;
  font-weight: 600;
  border-bottom: 2px solid #e1e5e9;
}

.metrics-table td {
  padding: 16px;
  border-bottom: 1px solid #e1e5e9;
}

.operator-cell {
  min-width: 200px;
}

.operator-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.operator-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 18px;
}

.operator-details {
  display: flex;
  flex-direction: column;
}

.operator-name {
  font-weight: 600;
  color: #2c3e50;
}

.operator-role {
  font-size: 12px;
  color: #7f8c8d;
}

.time-good {
  color: #27ae60;
  font-weight: 600;
}

.time-warning {
  color: #f39c12;
  font-weight: 600;
}

.time-bad {
  color: #e74c3c;
  font-weight: 600;
}

.time-unknown {
  color: #95a5a6;
}

.red-zone-col {
  text-align: center;
}

.red-zone-cell {
  text-align: center;
}

.red-zone-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #fee;
  color: #e74c3c;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 600;
}

.green-badge {
  color: #27ae60;
  font-weight: 600;
}

.show-details-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;
}

.details-btn {
  padding: 6px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: transform 0.2s;
}

.details-btn:hover {
  transform: scale(1.05);
}

.red-zone-row {
  background: rgba(231, 76, 60, 0.05);
}

/* Модальные окна */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-content.large {
  max-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e1e5e9;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.modal-body {
  padding: 20px;
}

.warning-message {
  background: #fff3cd;
  color: #856404;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.red-zone-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.red-zone-item {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 8px;
  border-left: 3px solid #e74c3c;
}

.message-header {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #7f8c8d;
}

.message-text {
  font-size: 14px;
  color: #2c3e50;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 30px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 10px;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: #667eea;
  margin-top: 8px;
}

.chart-container {
  margin-top: 20px;
}

.chart-container h3 {
  margin-bottom: 16px;
  font-size: 16px;
}

.activity-chart {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  gap: 12px;
  height: 150px;
}

.chart-bar-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.chart-bar {
  width: 100%;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 4px;
  transition: height 0.3s;
  min-height: 30px;
  position: relative;
}

.bar-value {
  font-size: 12px;
  color: white;
  font-weight: bold;
}

.chart-label {
  font-size: 11px;
  color: #7f8c8d;
}

@media (max-width: 768px) {
  .metrics-table {
    font-size: 12px;
  }
  
  .metrics-table th,
  .metrics-table td {
    padding: 10px;
  }
  
  .operator-avatar {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }
  
  .red-zone-badge {
    font-size: 11px;
    padding: 2px 8px;
  }
}
</style>