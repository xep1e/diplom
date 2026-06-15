<template>
  <div class="admin-bitrix-container">
    <h1>Управление Bitrix24 сотрудниками</h1>
    
    <!-- Список сотрудников из Bitrix -->
    <div class="bitrix-section">
      <div class="section-header">
        <h2>Сотрудники из Bitrix24</h2>
        <button @click="loadBitrixUsers" :disabled="loading" class="refresh-btn">
          🔄 Обновить список
        </button>
      </div>
      
      <div v-if="loading" class="loading">Загрузка...</div>
      
      <div v-else-if="bitrixUsers.length" class="users-table">
        <table>
          <thead>
            <tr>
              <th>ID в Bitrix</th>
              <th>Имя</th>
              <th>Фамилия</th>
              <th>Email</th>
              <th>Действие</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in bitrixUsers" :key="user.ID">
              <td><code>{{ user.ID }}</code></td>
              <td>{{ user.NAME || '-' }}</td>
              <td>{{ user.LAST_NAME || '-' }}</td>
              <td>{{ user.EMAIL || '-' }}</td>
              <td>
                <button 
                  @click="assignToOperator(user.ID, user.EMAIL || user.NAME)"
                  class="assign-btn"
                  :disabled="assigning === user.ID"
                >
                  {{ assigning === user.ID ? 'Назначение...' : 'Назначить оператору' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div v-else class="empty-state">
        Нет данных из Bitrix24. Проверьте вебхук.
      </div>
    </div>

    <!-- Список операторов сайта -->
    <div class="operators-section">
      <div class="section-header">
        <h2>Операторы сайта</h2>
        <button @click="loadSiteUsers" class="refresh-btn">
          🔄 Обновить
        </button>
      </div>
      
      <div v-if="siteUsers.length" class="users-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Логин</th>
              <th>Роль</th>
              <th>Bitrix ID</th>
              <th>Действие</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in siteUsers" :key="user.id">
              <td>{{ user.id }}</td>
              <td>{{ user.username }}</td>
              <td>{{ user.role }}</td>
              <td>
                <span v-if="user.bitrix_user_id" class="connected">
                  ✅ {{ user.bitrix_user_id }}
                </span>
                <span v-else class="not-connected">
                  ❌ не подключен
                </span>
              </td>
              <td>
                <button 
                  v-if="!user.bitrix_user_id"
                  @click="showAssignModal(user)"
                  class="assign-btn"
                >
                  🔗 Привязать Bitrix
                </button>
                <button 
                  v-else
                  @click="removeBitrixId(user.id)"
                  class="remove-btn"
                >
                  🗑️ Отвязать
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Модалка для назначения Bitrix ID -->
    <div v-if="showModal" class="modal" @click.self="closeModal">
      <div class="modal-content">
        <h3>Назначить Bitrix ID оператору</h3>
        <p>Оператор: <strong>{{ selectedUser?.username }}</strong></p>
        
        <div class="form-group">
          <label>Выберите Bitrix сотрудника:</label>
          <select v-model="selectedBitrixId" class="select-input">
            <option value="">-- Выберите из списка --</option>
            <option 
              v-for="bUser in bitrixUsers" 
              :key="bUser.ID" 
              :value="bUser.ID"
            >
              [{{ bUser.ID }}] {{ bUser.NAME }} {{ bUser.LAST_NAME }} ({{ bUser.EMAIL || 'нет email' }})
            </option>
          </select>
        </div>
        
        <div class="form-group">
          <label>Или введите ID вручную:</label>
          <input 
            v-model="manualBitrixId" 
            type="number" 
            placeholder="Например: 123"
            class="text-input"
          />
        </div>
        
        <div class="modal-buttons">
          <button @click="saveAssignment" class="save-btn" :disabled="saving">
            {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
          <button @click="closeModal" class="cancel-btn">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000'
const token = localStorage.getItem('token')

const loading = ref(false)
const assigning = ref(null)
const saving = ref(false)
const bitrixUsers = ref([])
const siteUsers = ref([])
const showModal = ref(false)
const selectedUser = ref(null)
const selectedBitrixId = ref('')
const manualBitrixId = ref('')

// Загружаем сотрудников из Bitrix
const loadBitrixUsers = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_URL}/bitrix/users`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    bitrixUsers.value = res.data.users || []
  } catch (error) {
    console.error('Ошибка загрузки Bitrix пользователей:', error)
    alert('Ошибка загрузки списка Bitrix: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// Загружаем операторов сайта
const loadSiteUsers = async () => {
  try {
    const res = await axios.get(`${API_URL}/api/users/`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    // Фильтруем только операторов и админов
    siteUsers.value = (res.data || []).filter(u => u.role === 'operator' || u.role === 'admin')
  } catch (error) {
    console.error('Ошибка загрузки операторов:', error)
  }
}

// Показать модалку для назначения
const showAssignModal = (user) => {
  selectedUser.value = user
  selectedBitrixId.value = ''
  manualBitrixId.value = ''
  showModal.value = true
}

// Назначить Bitrix ID оператору напрямую
const assignToOperator = async (bitrixId, identifier) => {
  if (!confirm(`Назначить Bitrix ID ${bitrixId} оператору?\n\nВыберите оператора из списка:`)) {
    return
  }
  
  // Находим оператора без Bitrix ID
  const freeOperators = siteUsers.value.filter(u => !u.bitrix_user_id)
  
  if (freeOperators.length === 0) {
    alert('Нет свободных операторов без Bitrix ID')
    return
  }
  
  let operatorName = prompt('Введите username оператора:\nДоступны: ' + freeOperators.map(o => o.username).join(', '))
  
  const operator = siteUsers.value.find(u => u.username === operatorName && !u.bitrix_user_id)
  
  if (!operator) {
    alert('Оператор не найден или уже имеет Bitrix ID')
    return
  }
  
  assigning.value = bitrixId
  try {
    const res = await axios.post(`${API_URL}/bitrix/assign-bitrix-id`, 
      {
        user_id: operator.id,
        bitrix_user_id: bitrixId
      },
      { headers: { Authorization: `Bearer ${token}` } }
    )
    
    if (res.data.ok) {
      alert(`✅ Bitrix ID ${bitrixId} назначен оператору ${operator.username}`)
      await loadSiteUsers()
    }
  } catch (error) {
    alert('Ошибка: ' + (error.response?.data?.detail || error.message))
  } finally {
    assigning.value = null
  }
}

// Сохранить назначение из модалки
const saveAssignment = async () => {
  const finalBitrixId = selectedBitrixId.value || manualBitrixId.value
  
  if (!finalBitrixId) {
    alert('Выберите или введите Bitrix ID')
    return
  }
  
  if (!selectedUser.value) {
    alert('Оператор не выбран')
    return
  }
  
  saving.value = true
  try {
    const res = await axios.post(`${API_URL}/bitrix/assign-bitrix-id`,
      {
        user_id: selectedUser.value.id,
        bitrix_user_id: parseInt(finalBitrixId)
      },
      { headers: { Authorization: `Bearer ${token}` } }
    )
    
    if (res.data.ok) {
      alert(`✅ Bitrix ID ${finalBitrixId} назначен оператору ${selectedUser.value.username}`)
      await loadSiteUsers()
      closeModal()
    }
  } catch (error) {
    alert('Ошибка: ' + (error.response?.data?.detail || error.message))
  } finally {
    saving.value = false
  }
}

// Отвязать Bitrix ID
const removeBitrixId = async (userId) => {
  if (!confirm('Отвязать Bitrix ID от этого оператора?')) return
  
  try {
    const res = await axios.post(`${API_URL}/bitrix/remove-bitrix-id`,
      { user_id: userId },
      { headers: { Authorization: `Bearer ${token}` } }
    )
    
    if (res.data.ok) {
      alert('✅ Bitrix ID отвязан')
      await loadSiteUsers()
    }
  } catch (error) {
    alert('Ошибка: ' + (error.response?.data?.detail || error.message))
  }
}

const closeModal = () => {
  showModal.value = false
  selectedUser.value = null
  selectedBitrixId.value = ''
  manualBitrixId.value = ''
}

onMounted(() => {
  loadBitrixUsers()
  loadSiteUsers()
})
</script>

<style scoped>
.admin-bitrix-container {
  max-width: 1400px;
  margin: 20px auto;
  padding: 20px;
}

h1 {
  margin-bottom: 30px;
  color: #333;
}

.bitrix-section, .operators-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 30px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #f0f0f0;
}

.section-header h2 {
  margin: 0;
  color: #555;
}

.refresh-btn {
  padding: 8px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.users-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background: #f8f9fa;
  font-weight: 600;
}

.assign-btn {
  padding: 6px 12px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.assign-btn:hover:not(:disabled) {
  background: #059669;
}

.remove-btn {
  padding: 6px 12px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.connected {
  color: #10b981;
  font-weight: 600;
}

.not-connected {
  color: #ef4444;
}

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
  padding: 30px;
  border-radius: 12px;
  min-width: 400px;
  max-width: 500px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
}

.select-input, .text-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.modal-buttons {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.save-btn {
  padding: 8px 20px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.cancel-btn {
  padding: 8px 20px;
  background: #6b7280;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.loading, .empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}
</style>