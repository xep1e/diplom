<template>
  <div class="form-container">
    <h1>Вход</h1>

    <form @submit.prevent="loginUser">
      <input type="text" placeholder="Логин" v-model="username" />
      <input type="password" placeholder="Пароль" v-model="password" />
      <button type="submit">Войти</button>
    </form>

    <p>
      Нет аккаунта?
      <button @click="goRegister" class="link-button">
        Зарегистрироваться
      </button>
    </p>
  </div>
</template>

<script>
import '/style/form.css'
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
      password: ''
    }
  },

  methods: {
    async loginUser() {
      if (!this.username || !this.password) {
        alert("Введите логин и пароль")
        return
      }

      try {
        await login(this.username, this.password)

        alert("Вы успешно вошли!")
        this.router.push("/chat")
      } catch (err) {
        console.error(err)
        alert(err.response?.data?.detail || "Ошибка при входе")
      }
    }
  }
}
</script>