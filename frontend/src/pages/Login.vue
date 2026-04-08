<template>
  <div class="form-container">
    <h1>Вход</h1>
    <form @submit.prevent="loginUser">
      <input type="text" placeholder="Логин" v-model="username" />
      <input type="password" placeholder="Пароль" v-model="password" />
      <button type="submit">Войти</button>
    </form>
    <p>Нет аккаунта? <button @click="goRegister" class="link-button">Зарегистрироваться</button></p>
  </div>
</template>

<script>
import '/style/form.css'
import axios from 'axios'
import { useRouter } from 'vue-router'

const API_URL = 'http://127.0.0.1:8000/api/users'

export default {
  setup() {
    const router = useRouter()
    const goRegister = () => router.push("/register")
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
        const res = await axios.post(`${API_URL}/login`, {
          username: this.username,
          password: this.password
        })

        localStorage.setItem("user", JSON.stringify(res.data))
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

<style>
.link-button {
  background: none;
  border: none;
  color: #3498db;
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
  font-size: 14px;
}
.link-button:hover {
  color: #2980b9;
}
</style>