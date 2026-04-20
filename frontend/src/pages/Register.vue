<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-header">
        <div class="register-icon">✨</div>
        <h1>Создать аккаунт</h1>
        <p>Присоединяйтесь к нам прямо сейчас</p>
      </div>

      <form @submit.prevent="registerUser" class="register-form">
        <div class="input-group">
          <label>👤 Логин</label>
          <input 
            type="text" 
            placeholder="Придумайте логин" 
            v-model="username" 
            class="register-input"
            autofocus
          />
        </div>

        <div class="input-group">
          <label>🔒 Пароль</label>
          <input 
            type="password" 
            placeholder="Придумайте пароль" 
            v-model="password" 
            class="register-input"
            @keyup.enter="registerUser"
          />
        </div>

        <div class="input-group" v-if="password">
          <label>✅ Подтверждение</label>
          <input 
            type="password" 
            placeholder="Повторите пароль" 
            v-model="confirmPassword" 
            class="register-input"
            :class="{ 'error': confirmPassword && password !== confirmPassword }"
            @keyup.enter="registerUser"
          />
          <span v-if="confirmPassword && password !== confirmPassword" class="error-message">
            ⚠️ Пароли не совпадают
          </span>
        </div>

        <button 
          type="submit" 
          class="register-btn" 
          :disabled="isLoading || (confirmPassword && password !== confirmPassword)"
        >
          <span v-if="!isLoading">Зарегистрироваться</span>
          <span v-else class="loading">⏳ Регистрация...</span>
        </button>
      </form>

      <div class="login-link">
        <p>Уже есть аккаунт?</p>
        <button @click="goLogin" class="link-button">
          Войти →
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import '/style/register.css'
import { register } from '../api/userApi'
import { useRouter } from 'vue-router'

export default {
  setup() {
    const router = useRouter()

    const goLogin = () => {
      router.push('/login')
    }

    return { router, goLogin }
  },

  data() {
    return {
      username: '',
      password: '',
      confirmPassword: '',
      isLoading: false
    }
  },

  methods: {
    async registerUser() {
      if (!this.username || !this.password) {
        alert("❌ Введите логин и пароль")
        return
      }

      if (this.password !== this.confirmPassword) {
        alert("❌ Пароли не совпадают")
        return
      }

      if (this.password.length < 4) {
        alert("❌ Пароль должен содержать минимум 4 символа")
        return
      }

      this.isLoading = true

      try {
        await register(this.username, this.password)
        alert("✅ Регистрация успешна! Теперь вы можете войти.")
        this.router.push("/login")
      } catch (err) {
        console.error(err)
        const errorMsg = err.response?.data?.detail || "Ошибка при регистрации"
        if (errorMsg.includes("already exists") || errorMsg.includes("существует")) {
          alert("❌ Пользователь с таким логином уже существует")
        } else {
          alert(`❌ ${errorMsg}`)
        }
      } finally {
        this.isLoading = false
      }
    }
  }
}
</script>

