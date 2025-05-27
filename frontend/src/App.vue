<template>
    <!-- <h1>{{ message }}</h1> -->
  <el-container id="app" class="app-container">
    <el-header><Head /></el-header>
      <el-container>
        <el-aside width="180px"><Sidebar /></el-aside>
        <el-main><router-view class="content-area"/></el-main>
      </el-container>
  </el-container>
</template>

<script>
import axios from 'axios'
import Sidebar from './components/Sidebar.vue'
import Head from './components/Head.vue'

export default {
  name: "App",

  components: {
    Sidebar,
    Head
  },

  data() {
    return {
      message: 'Loading...'
    }
  },
}
</script>

<style scoped>
.app-container {
  display: flex;
  height:100vh;
  background-color: #f2f2f2fd;
}
.el-container {
  display: flex;
  flex-direction: row;
  height: 100vh;
}
.el-header {
  --el-header-padding: 0 0px;
}
.el-aside {
    border-right-color: #dcdfe6;
    height: 920px;
    background-color: #fff;
}
.content-area {
   /* 内容区域占据剩余空间 */
  overflow-y: auto; /* 内容过多时滚动 */
}

</style>