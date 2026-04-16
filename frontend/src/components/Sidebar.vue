<script setup>
import { ref, onMounted } from 'vue'
import { getMe } from '../api/authApi'
import { useRouter } from 'vue-router'

const router = useRouter()
const user = ref(null)

const loadUser = async () => {
  try {
    user.value = await getMe()
  } catch {
    user.value = null
  }
}

const logout = () => {
  localStorage.removeItem('token')
  user.value = null
  router.push('/login')
}

onMounted(loadUser)
</script>

<template>
  <div class="sidebar">

    <div class="menu">
      <router-link to="/chat">Чат</router-link>
      <router-link to="/metrics">Метрики</router-link>
      <router-link to="/tasks">Задачи</router-link>

      <router-link v-if="user?.role === 'admin'" to="/admin/chats">
        Распределение чатов
      </router-link>
    </div>

    <div class="user">

      <!-- 👤 LOGGED -->
      <div v-if="user" class="user-block">
        <router-link to="/profile" class="user-btn">
          {{ user.username }}
        </router-link>

        <button class="logout-btn" @click="logout">
          Выйти
        </button>
      </div>

      <!-- 🚪 GUEST -->
      <div v-else class="guest-block">
        <button class="login-btn" @click="$router.push('/login')">
          Войти в систему
        </button>
      </div>

    </div>

  </div>
</template>