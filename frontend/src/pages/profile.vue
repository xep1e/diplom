<template>
  <div class="profile-container">

    <div class="profile-card">

      <h1>Профиль</h1>

      <div
        v-if="user"
        class="user-info"
      >

        <div class="info-row">
          <span class="label">
            Имя пользователя:
          </span>

          <span class="value">
            {{ user.username }}
          </span>
        </div>


        <div class="info-row">
          <span class="label">
            Роль:
          </span>

          <span class="value">
            {{ user.role }}
          </span>
        </div>


        <!-- BITRIX -->

        <div class="info-row">

          <span class="label">
            Bitrix24:
          </span>

          <div>

            <span
              v-if="user.bitrix_connected"
              class="status-connected"
            >
              ✅ Подключен
              (ID:
              {{ user.bitrix_user_id }})
            </span>

            <span
              v-else
              class="status-disconnected"
            >
              ⚠️ Не подключен
            </span>

          </div>

        </div>


        <button
          v-if="!user.bitrix_connected"
          @click="connectBitrix"
          :disabled="loading"
          class="connect-btn"
        >

          {{
            loading
              ? 'Подключение...'
              : '🔗 Подключить Bitrix24'
          }}

        </button>


        <!-- TELEGRAM -->

        <div class="info-row">

          <span class="label">
            Telegram:
          </span>

          <div>

            <span
              v-if="user.telegram_connected"
              class="status-connected"
            >
              ✅ Подключен

              <br>

              ID:
              {{ user.telegram_chat_id }}

            </span>

            <span
              v-else
              class="status-disconnected"
            >
              ⚠️ Не подключен
            </span>

          </div>

        </div>


        <button
          v-if="!user.telegram_connected"
          @click="connectTelegram"
          :disabled="telegramLoading"
          class="tg-btn"
        >

          {{
            telegramLoading
              ? 'Создание кода...'
              : '📨 Подключить Telegram'
          }}

        </button>


        <div
          v-if="telegramCommand"
          class="telegram-box"
        >

          <div class="command">

            {{ telegramCommand }}

          </div>

          <button
            class="copy-btn"
            @click="copyTelegram"
          >
            Скопировать
          </button>

          <div class="hint">

            Откройте Telegram-бота
            и отправьте команду

          </div>

        </div>

      </div>


      <div
        v-if="status"
        :class="[
          'status-message',
          statusType
        ]"
      >
        {{ status }}
      </div>


      <button
        @click="logout"
        class="logout-btn"
      >
        Выйти
      </button>

    </div>

  </div>
</template>

<script setup>

import {
ref,
onMounted
}
from 'vue'

import {
useRouter,
useRoute
}
from 'vue-router'

import axios from 'axios'


const router =
useRouter()

const route =
useRoute()


const API_URL =
'http://127.0.0.1:8000'


const user =
ref(null)

const loading =
ref(false)

const telegramLoading =
ref(false)

const telegramCommand =
ref('')

const status =
ref('')

const statusType =
ref('')


const loadUser =
async () => {

const token =
localStorage.getItem(
'token'
)

if (!token) {

router.push(
'/login'
)

return

}

try {

const res =
await axios.get(
`${API_URL}/api/users/me`,
{
headers:{
Authorization:
`Bearer ${token}`
}
}
)

user.value =
res.data


user.value.telegram_connected =
!!user.value.telegram_chat_id

}
catch {

localStorage.removeItem(
'token'
)

router.push(
'/login'
)

}

}



const connectBitrix =
async () => {

loading.value =
true

const token =
localStorage.getItem(
'token'
)

try {

const res =
await axios.get(
`${API_URL}/bitrix/connect`,
{
headers:{
Authorization:
`Bearer ${token}`
}
}
)

window.location.href =
res.data.url

}
catch {

status.value =
'Ошибка подключения'

statusType.value =
'error'

}
finally {

loading.value =
false

}

}



const connectTelegram =
async () => {

telegramLoading.value =
true

const token =
localStorage.getItem(
'token'
)

try {

const res =
await axios.post(
`${API_URL}/telegram/generate-token`,
{},
{
headers:{
Authorization:
`Bearer ${token}`
}
}
)

telegramCommand.value =
res.data.command

status.value =
'Скопируйте команду и отправьте её боту'

statusType.value =
'success'


const interval =
setInterval(
async () => {

await loadUser()

if (
user.value?.telegram_connected
) {

clearInterval(
interval
)

telegramCommand.value =
''

status.value =
'✅ Telegram подключён'

statusType.value =
'success'

}

},
2000
)

}
catch {

status.value =
'Ошибка подключения Telegram'

statusType.value =
'error'

}
finally {

telegramLoading.value =
false

}

}



const copyTelegram =
async () => {

await navigator
.clipboard
.writeText(
telegramCommand.value
)

status.value =
'✅ Команда скопирована'

statusType.value =
'success'

}



const logout =
() => {

localStorage.removeItem(
'token'
)

router.push(
'/login'
)

}



onMounted(
async () => {

await loadUser()

if (
route.query.bitrix
===
'success'
) {

status.value =
'✅ Bitrix подключён'

statusType.value =
'success'

}

router.replace(
'/profile'
)

}
)

</script>


<style scoped>

.profile-container{

max-width:700px;

margin:50px auto;

padding:20px;

}


.profile-card{

background:white;

padding:30px;

border-radius:12px;

box-shadow:0 2px 12px rgba(0,0,0,.1);

}


.info-row{

display:flex;

justify-content:space-between;

padding:14px 0;

border-bottom:1px solid #eee;

}


.label{

font-weight:600;

}


.connect-btn,
.tg-btn,
.logout-btn,
.copy-btn{

width:100%;

padding:12px;

border:none;

border-radius:8px;

cursor:pointer;

margin-top:15px;

}


.connect-btn{

background:#2563eb;

color:white;

}


.tg-btn{

background:#229ED9;

color:white;

}


.logout-btn{

background:#f3f4f6;

}


.copy-btn{

background:#0ea5e9;

color:white;

}


.telegram-box{

margin-top:20px;

padding:20px;

background:#f8fafc;

border-radius:10px;

}


.command{

padding:14px;

background:white;

border:1px solid #ddd;

border-radius:8px;

font-family:monospace;

text-align:center;

margin-bottom:10px;

}


.status-connected{

color:#10b981;

font-weight:600;

}


.status-disconnected{

color:#ef4444;

}


.status-message{

margin-top:20px;

padding:12px;

border-radius:8px;

}


.status-message.success{

background:#dcfce7;

}


.status-message.error{

background:#fee2e2;

}


.hint{

margin-top:10px;

color:#666;

text-align:center;

}

</style>