<template>
  <div class="form-container">
    <h1>Регистрация</h1>

    <form @submit.prevent="registerUser">
      <input type="text" placeholder="Логин" v-model="username" />
      <input type="password" placeholder="Пароль" v-model="password" />
      <button type="submit">Зарегистрироваться</button>
    </form>

    <p>
      Уже есть аккаунт?
      <button @click="goLogin" class="link-button">
        Войти
      </button>
    </p>
  </div>
</template>

<script>
import '/style/form.css'
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
      password: ''
    }
  },

  methods: {
    async registerUser() {
      if (!this.username || !this.password) {
        alert("Введите логин и пароль")
        return
      }

      try {
        await register(this.username, this.password)

        alert("Регистрация успешна!")
        this.router.push("/login")
      } catch (err) {
        console.error(err)
        alert(err.response?.data?.detail || "Ошибка при регистрации")
      }
    }
  }
}
</script>