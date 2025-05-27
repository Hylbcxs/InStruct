<template>
    <!-- 顶部导航栏 -->
    <el-menu :default-active="activeIndex" class="el-menu-demo" mode="horizontal" :ellipsis="false">
      <el-menu-item index="0">
        <!-- <img
          style="width: 100px"
          src="/images/element-plus-logo.svg"
          alt="Element logo"
        /> -->
        智能结构化系统
      </el-menu-item>
      <el-menu-item index="1">使用文档</el-menu-item>
      <el-menu-item index="2">联系我们</el-menu-item>
    </el-menu>
</template>

<script>
export default {
  name: 'Head',
  data() {
    return {
      activeIndex: '1'
    }
  }
}
</script>

<style scoped>
.el-menu--horizontal > .el-menu-item:nth-child(1) {
  margin-right: auto;
}
.el-menu-demo.el-header {
  --el-header-padding: 0;
}
</style>