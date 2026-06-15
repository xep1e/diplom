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
        <div class="stat-card rating">
          <span class="stat-value">{{ averageRating }}%</span>
          <span class="stat-label">Общий рейтинг</span>
        </div>
      </div>
    </div>

    <!-- Поиск и фильтры -->
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
        <button 
          class="filter-btn rating" 
          :class="{ active: filterType === 'rating' }"
          @click="filterType = 'rating'"
        >
          📈 По рейтингу
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
            <th>Рейтинг</th>
            <th class="red-zone-col">Красная зона</th>
            <th>KPI</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="op in filteredOperators" 
            :key="op.id"
            :class="{ 'red-zone-row': op.red_zone_count > 0, 'top-row': op.kpi_score >= 80 }"
          >
            <td class="operator-cell">
              <div class="operator-info">
                <div class="operator-avatar" :style="{ background: getAvatarColor(op.kpi_score) }">
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
            <td class="rating-cell">
              <div class="rating-badge">
                <span class="likes">👍 {{ op.likes || 0 }}</span>
                <span class="dislikes">👎 {{ op.dislikes || 0 }}</span>
                <div class="rating-bar">
                  <div class="rating-fill" :style="{ width: op.rating_percent + '%' }"></div>
                </div>
                <span class="rating-percent">{{ op.rating_percent }}%</span>
              </div>
            </td>
            <td class="red-zone-cell">
              <div v-if="op.red_zone_count > 0" class="red-zone-badge">
                🔴 {{ op.red_zone_count }}
                <button class="show-details-btn" @click="showRedZoneDetails(op)">
                  👁️
                </button>
              </div>
              <span v-else class="green-badge">✅ Нет</span>
            </td>
            <td class="kpi-cell">
              <div class="kpi-circle" :class="getKpiClass(op.kpi_score)">
                <svg viewBox="0 0 36 36" class="circular-chart">
                  <path class="circle-bg"
                    d="M18 2.0845
                      a 15.9155 15.9155 0 0 1 0 31.831
                      a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path class="circle"
                    :stroke-dasharray="`${op.kpi_score}, 100`"
                    d="M18 2.0845
                      a 15.9155 15.9155 0 0 1 0 31.831
                      a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <text x="18" y="20.35" class="percentage">{{ op.kpi_score }}</text>
                </svg>
              </div>
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

    <!-- Модальное окно с деталями -->
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
            <div class="stat-item">
              <div class="stat-label">👍 Лайки</div>
              <div class="stat-number success">{{ selectedOperator.likes || 0 }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">👎 Дизлайки</div>
              <div class="stat-number danger">{{ selectedOperator.dislikes || 0 }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Рейтинг</div>
              <div class="stat-number">{{ selectedOperator.rating_percent }}%</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">KPI Score</div>
              <div class="stat-number">{{ selectedOperator.kpi_score }}</div>
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
          
          <div class="chart-container">
            <h3>Рейтинги по дням</h3>
            <div class="ratings-chart">
              <div v-for="day in ratingsByDay" :key="day.date" class="rating-bar-container">
                <div class="rating-bars">
                  <div class="like-bar" :style="{ height: (day.likes * 20) + 'px', background: '#27ae60' }">
                    <span class="bar-value">{{ day.likes }}</span>
                  </div>
                  <div class="dislike-bar" :style="{ height: (day.dislikes * 20) + 'px', background: '#e74c3c' }">
                    <span class="bar-value">{{ day.dislikes }}</span>
                  </div>
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
import '/style/metrics.css'

const operators = ref([])
const searchQuery = ref('')
const filterType = ref('all')
const selectedOperator = ref(null)
const operatorDetails = ref([])
const ratingsByDay = ref([])
const averageRating = ref(0)

// Загрузка метрик
const loadMetrics = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get('http://185.125.201.136:8000/metrics/operators', {
      headers: { Authorization: `Bearer ${token}` }
    })
    operators.value = res.data
    
    // Подсчет среднего рейтинга
    const totalRating = operators.value.reduce((sum, op) => sum + (op.rating_percent || 0), 0)
    averageRating.value = operators.value.length ? Math.round(totalRating / operators.value.length) : 0
  } catch (error) {
    console.error('Ошибка загрузки метрик:', error)
  }
}

// Фильтрация
const filteredOperators = computed(() => {
  let filtered = [...operators.value]
  
  if (searchQuery.value) {
    filtered = filtered.filter(op => 
      op.username.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }
  
  if (filterType.value === 'red') {
    filtered = filtered.filter(op => op.red_zone_count > 0)
  } else if (filterType.value === 'top') {
    filtered = filtered.sort((a, b) => (b.kpi_score || 0) - (a.kpi_score || 0)).slice(0, 3)
  } else if (filterType.value === 'rating') {
    filtered = filtered.sort((a, b) => (b.rating_percent || 0) - (a.rating_percent || 0))
  }
  
  return filtered
})

const redZoneCount = computed(() => {
  return operators.value.filter(op => op.red_zone_count > 0).length
})

const totalRedZone = computed(() => {
  return operators.value.reduce((sum, op) => sum + (op.red_zone_count || 0), 0)
})

// Форматирование
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

const getResponseTimeClass = (seconds) => {
  if (!seconds) return 'time-unknown'
  if (seconds > 60) return 'time-bad'
  if (seconds > 30) return 'time-warning'
  return 'time-good'
}

const getKpiClass = (score) => {
  if (score >= 80) return 'kpi-excellent'
  if (score >= 60) return 'kpi-good'
  if (score >= 40) return 'kpi-average'
  return 'kpi-poor'
}

const getAvatarColor = (score) => {
  if (score >= 80) return 'linear-gradient(135deg, #27ae60, #2ecc71)'
  if (score >= 60) return 'linear-gradient(135deg, #f39c12, #f1c40f)'
  return 'linear-gradient(135deg, #e74c3c, #c0392b)'
}

const getBarHeight = (count) => {
  const maxCount = Math.max(...operatorDetails.value.map(d => d.messages), 1)
  return Math.min(100, (count / maxCount) * 80) + 20
}

const showOperatorDetails = async (operator) => {
  selectedOperator.value = operator
  
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(`http://185.125.201.136:8000/metrics/operators/${operator.id}/details`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    operatorDetails.value = res.data.last_7_days || []
    ratingsByDay.value = res.data.ratings_by_day || []
  } catch (error) {
    console.error('Ошибка загрузки деталей:', error)
  }
}

const closeOperatorModal = () => {
  selectedOperator.value = null
  operatorDetails.value = []
  ratingsByDay.value = []
}

const showRedZoneDetails = (operator) => {
  alert(`Красная зона для ${operator.username}:\n${operator.red_zone_messages.map(m => 
    `Чат #${m.chat_id}: ${m.client_message} (${m.response_time_seconds} сек)`
  ).join('\n')}`)
}

onMounted(() => {
  loadMetrics()
})
</script>
