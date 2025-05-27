import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    watch: {
      // 使用轮询而不是 inotify
      usePolling: true,
      interval: 1000 // 每隔 1 秒检查一次文件变化
    }
  }
})