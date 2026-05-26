<template>
  <div class="chat-layout">

    <!-- LEFT -->
    <div class="chat-list">
      <div
        v-for="c in chats"
        :key="c.id"
        class="chat-item"
        :class="{ active: activeChat?.id===c.id, closed:c.status==='closed'}"
        @click="openChat(c)"
      >
        <div class="chat-item-content">

          <div class="chat-title">
            <b>{{ c.title }}</b>

            <span
              v-if="c.status==='closed'"
              class="closed-badge"
            >
              Закрыт
            </span>

            <span
              v-if="c.status==='new'"
              class="new-badge"
            >
              Новый
            </span>

          </div>

          <p class="last">
            {{ c.last_message || 'Нет сообщений' }}
          </p>

        </div>

        <div class="chat-time">
          {{ formatTime(c.updated_at) }}
        </div>

      </div>

      <div
        v-if="chats.length===0"
        class="empty-chats"
      >
        💬 Нет активных чатов
      </div>

    </div>


    <!-- RIGHT -->

    <div
      class="chat-window"
      v-if="activeChat"
    >

      <div class="header">

        <div class="header-info">

          <div class="chat-title-header">

            <span>
              {{activeChat.title}}
            </span>

            <span
              v-if="activeChat.status==='closed'"
              class="closed-status"
            >
              🔒 Закрыт
            </span>

            <span
              v-if="activeChat.status==='new'"
              class="new-status"
            >
              🆕 Новый
            </span>

          </div>

          <div class="chat-id">
            Чат #{{activeChat.id}}
          </div>

        </div>


        <div class="header-actions">

          <button
            class="task-btn"
            @click="showTaskModal=true"
          >
            📋 Создать задачу
          </button>


          <button
            v-if="activeChat.status!=='closed'"
            class="close-chat-btn"
            @click="closeChat"
            :disabled="isClosing"
          >
            {{isClosing ? 'Закрытие...' : '🔒 Закрыть диалог'}}
          </button>

        </div>

      </div>



      <div
        class="messages"
        ref="messagesBox"
      >

        <div
          v-for="m in messages"
          :key="m.id"
          :class="['msg',getMessageClass(m)]"
        >

          <div class="sender">
            {{m.sender}}
          </div>

          <div
            v-if="m.text&&!m.media_url"
            class="message-text"
          >
            {{m.text}}
          </div>

          <div
            v-if="m.media_type==='image'&&m.media_url"
          >

            <img
              :src="getPhotoUrl(m.media_url)"
              class="media-image"
              @click="openImage(getPhotoUrl(m.media_url))"
              @load="scrollToBottom"
              @error="handleImageError(m)"
            >

            <div class="media-caption">
              {{m.text}}
            </div>

          </div>

        </div>


        <div
          v-if="activeChat.status==='closed'"
          class="system-message"
        >
          🔒 Диалог закрыт
          {{formatDate(activeChat.closed_at)}}
        </div>

      </div>



      <div
        class="input-area"
        v-if="activeChat.status!=='closed'"
      >

        <div class="input-tools">

          <button
            @click="triggerPhotoUpload"
            class="tool-btn"
          >
            📷 Фото
          </button>

        </div>


        <div class="input">

          <input
            v-model="text"
            @keyup.enter="send"
            placeholder="Сообщение..."
          >

          <button
            @click="send"
            :disabled="!text.trim()"
          >
            ➤
          </button>

        </div>

      </div>

    </div>


    <div
      v-else
      class="no-chat-selected"
    >

      <div class="no-chat-content">

        <div class="no-chat-icon">
          💬
        </div>

        <h3>
          Выберите чат
        </h3>

        <p>
          Нажмите на диалог
        </p>

      </div>

    </div>



    <div
      v-if="showImageModal"
      class="modal"
      @click="closeImage"
    >
      <img
        :src="selectedImage"
        class="modal-image"
      >
    </div>


    <CreateTask
      v-if="showTaskModal"
      :chatId="activeChat.id"
      @close="showTaskModal=false"
    />

  </div>
</template>

<script setup>

import {ref,onMounted,onUnmounted,nextTick} from "vue"
import axios from "axios"
import {getMe} from "../api/authApi"

import CreateTask from "./CreateTask.vue"

import "/style/chat.css"

const showTaskModal=ref(false)

const chats=ref([])
const activeChat=ref(null)
const messages=ref([])
const text=ref("")
const me=ref({})
const showImageModal=ref(false)
const selectedImage=ref("")
const isClosing=ref(false)

let socket=null
const messagesBox=ref(null)

let refreshInterval=null


const formatTime=(date)=>{

if(!date) return ""

const d=new Date(date)

const now=new Date()

const diff=now-d

if(diff<60000)return"только что"

if(diff<3600000)
return `${Math.floor(diff/60000)} мин`

if(diff<86400000)
return `${Math.floor(diff/3600000)} ч`

return d.toLocaleDateString()

}


const formatDate=(date)=>{

if(!date)return""

return new Date(date).toLocaleString()

}


const getPhotoUrl=(photoKey)=>{

return `http://127.0.0.1:8000/photo/${encodeURIComponent(photoKey)}`

}


const getMessageClass=(m)=>{

if(m.sender_type==="operator")
return"my"

if(m.sender_type==="client")
return"other"

return"system"

}


const loadMe=async()=>{

me.value=await getMe()

}


const loadChats=async()=>{

const token=localStorage.getItem("token")

const res=await axios.get(
"http://127.0.0.1:8000/operator/chats/",
{
headers:{
Authorization:`Bearer ${token}`
}
}
)

chats.value=res.data

}


const loadMessages=async(chatId)=>{

const token=localStorage.getItem("token")

const res=await axios.get(
`http://127.0.0.1:8000/chats/${chatId}/messages`,
{
headers:{
Authorization:`Bearer ${token}`
}
}
)

messages.value=res.data

scrollToBottom()

}


const connectWebSocket=(chatId)=>{

if(socket){

socket.close()

socket=null

}

const token=localStorage.getItem("token")

socket=new WebSocket(
`ws://127.0.0.1:8000/ws/chat/${chatId}?token=${token}`
)


socket.onmessage=(event)=>{

const msg=JSON.parse(
event.data
)

messages.value.push(msg)

scrollToBottom()

}

}


const openChat=async(chat)=>{

activeChat.value=chat

await loadMessages(chat.id)

connectWebSocket(chat.id)

}


const send=()=>{

if(!text.value.trim())return

socket.send(
JSON.stringify({
text:text.value
})
)

text.value=""

}


const closeChat=async()=>{

isClosing.value=true

const token=
localStorage.getItem(
"token"
)

await axios.post(
`http://127.0.0.1:8000/chat/${activeChat.value.id}/close`,
{},
{
headers:{
Authorization:`Bearer ${token}`
}
}
)

activeChat.value.status="closed"

isClosing.value=false

}


const triggerPhotoUpload=()=>{

const input=
document.createElement(
"input"
)

input.type="file"

input.accept="image/*"

input.onchange=async(e)=>{

const file=
e.target.files[0]

await uploadPhoto(file)

}

input.click()

}


const uploadPhoto=async(file)=>{

const formData=
new FormData()

formData.append(
"file",
file
)

formData.append(
"chat_id",
activeChat.value.id
)

const token=
localStorage.getItem(
"token"
)

await axios.post(
"http://127.0.0.1:8000/upload/photo",
formData,
{
headers:{
Authorization:`Bearer ${token}`
}
}
)

}


const openImage=(url)=>{

selectedImage.value=url

showImageModal.value=true

}

const closeImage=()=>{

showImageModal.value=false

}

const handleImageError=(m)=>{

m.media_url=null

}


const scrollToBottom=async()=>{

await nextTick()

if(messagesBox.value){

messagesBox.value.scrollTop=
messagesBox.value.scrollHeight

}

}


onMounted(async()=>{

await loadMe()

await loadChats()

refreshInterval=
setInterval(()=>{

loadChats()

},30000)

})


onUnmounted(()=>{

if(refreshInterval)
clearInterval(
refreshInterval
)

if(socket)
socket.close()

})

</script>