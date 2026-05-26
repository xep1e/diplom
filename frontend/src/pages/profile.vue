<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const user = ref(null)
const bitrixLinked = ref(false)

const load = async () => {
  const token = localStorage.getItem("token")

  const res = await axios.get("http://127.0.0.1:8000/api/users/me", {
    headers: { Authorization: `Bearer ${token}` }
  })

  user.value = res.data
  bitrixLinked.value = !!res.data.bitrix_user_id
}

const connectBitrix = async () => {
  const token = localStorage.getItem("token")

  const res = await axios.get("http://127.0.0.1:8000/bitrix/connect", {
    headers: { Authorization: `Bearer ${token}` }
  })

  window.location.href = res.data.url
}

onMounted(load)
</script>

<template>
  <div class="profile">

    <h2>👤 Профиль оператора</h2>

    <div v-if="user">
      <p><b>Имя:</b> {{ user.username }}</p>
      <p><b>Роль:</b> {{ user.role }}</p>

      <hr />

      <div v-if="bitrixLinked">
        <p>✅ Bitrix подключен (ID: {{ user.bitrix_user_id }})</p>
      </div>

      <div v-else>
        <p>❌ Bitrix не подключен</p>

        <button @click="connectBitrix">
          🔗 Подключить Bitrix
        </button>
      </div>
    </div>

  </div>
</template>