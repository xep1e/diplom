import { createApp } from 'vue'
import App from './App.vue'
import { createRouter, createWebHistory } from 'vue-router'

import Register from './pages/Register.vue'
import Login from './pages/Login.vue'
import Chat from './pages/Chat.vue'
import Metrics from './pages/Metrics.vue'
import Tasks from './pages/Tasks.vue'

const routes = [
  { path: '/', component: Login },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/chat', component: Chat },
  { path: '/metrics', component: Metrics },
  { path: '/tasks', component: Tasks },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

createApp(App).use(router).mount('#app')