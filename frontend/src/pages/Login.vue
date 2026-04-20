<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <div class="login-icon">💬</div>
        <h1>Добро пожаловать</h1>
        <p>Войдите в свой аккаунт</p>
      </div>

      <form @submit.prevent="loginUser" class="login-form">
        <div class="input-group">
          <label>👤 Логин</label>
          <input 
            type="text" 
            placeholder="Введите ваш логин" 
            v-model="username" 
            class="login-input"
            autofocus
          />
        </div>

        <div class="input-group">
          <label>🔒 Пароль</label>
          <input 
            type="password" 
            placeholder="Введите пароль" 
            v-model="password" 
            class="login-input"
            @keyup.enter="loginUser"
          />
        </div>

        <button type="submit" class="login-btn" :disabled="isLoading">
          <span v-if="!isLoading">Войти</span>
          <span v-else class="loading">⏳ Вход...</span>
        </button>
      </form>

      <div class="register-link">
        <p>Нет аккаунта?</p>
        <button @click="goRegister" class="link-button">
          Зарегистрироваться →
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import '/style/login.css'
import { login } from '../api/authApi'
import { useRouter } from 'vue-router'

export default {
  setup() {
    const router = useRouter()

    const goRegister = () => {
      router.push('/register')
    }

    return { router, goRegister }
  },

  data() {
    return {
      username: '',
      password: '',
      isLoading: false
    }
  },

  methods: {
    async loginUser() {
      if (!this.username || !this.password) {
        alert("Введите логин и пароль")
        return
      }

      this.isLoading = true

      try {
        await login(this.username, this.password)
        alert("✅ Вы успешно вошли!")
        this.router.push("/chat")
      } catch (err) {
        console.error(err)
        alert(err.response?.data?.detail || "❌ Ошибка при входе")
      } finally {
        this.isLoading = false
      }
    }
  }
}
</script>

