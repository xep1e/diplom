<template>
  <div class="sidebar">
    <div class="menu">
      <router-link to="/chat">Чат</router-link>
      <router-link to="/metrics">Метрики</router-link>
      <router-link to="/tasks">Задачи</router-link>
    </div>
    <div class="user">
      <template v-if="user">
        <router-link :to="`/profile/${user.id}`">{{ user.username }}</router-link>
      </template>
      <template v-else>
        <button @click="$router.push('/login')">Войти</button>
      </template>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import '/style/sidebar.css'

export default {
  setup() {
    const user = ref(null)

    const loadUser = () => {
      const userData = localStorage.getItem("user")
      user.value = userData ? JSON.parse(userData) : null
    }

    onMounted(() => {
      loadUser()
      window.addEventListener("storage", loadUser)
    })

    onUnmounted(() => {
      window.removeEventListener("storage", loadUser)
    })

    return { user }
  }
}
</script>