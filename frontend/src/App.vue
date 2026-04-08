<template>
  <Sidebar />
  <div class="content">
    <router-view />
  </div>
</template>

<script>
import Sidebar from './components/Sidebar.vue'
import '/style/app.css'  // глобальные стили
import '/style/sidebar.css' // стили сайдбара

export default {
  components: { Sidebar }
}
</script>

<style>
.content {
  flex: 1; 
  padding: 20px;
  overflow-y: auto; 
}
</style>