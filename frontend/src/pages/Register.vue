<template>
  <div class="form-container">
    <h1>Регистрация оператора</h1>
    <form @submit.prevent="register">
      <input type="text" placeholder="Логин" v-model="username" />
      <input type="password" placeholder="Пароль" v-model="password" />
      <button type="submit">Зарегистрироваться</button>
    </form>
  </div>
</template>

<script>
import '/style/form.css'
import { createUser, fetchUsers } from '../api/userApi.js'

export default {
  data() {
    return {
      username: '',
      password: ''
    }
  },
  async mounted() {
    const users = await fetchUsers()
    console.log(users)
  },
  methods: {
    async register() {
      if (!this.username || !this.password) {
        alert('Введите логин и пароль')
        return
      }
      try {
        const user = await createUser(this.username, this.password)
        console.log('Создан пользователь:', user)
        alert('Пользователь успешно зарегистрирован!')
        // Очистка формы
        this.username = ''
        this.password = ''
      } catch (err) {
        console.error(err)
        alert('Ошибка при регистрации')
      }
    }
  }
}
</script>