<!-- src/components/Sidebar.vue -->
<template>
  <!-- <el-aside width="200px" class="sidebar"> -->
  <div class="sidebar">
    <el-menu default-active="/invoice" class="el-menu-vertical" @select="handleSelect">
      <el-sub-menu index="1">
        <template #title>
          <el-icon><Document /></el-icon>
          <span>单证识别</span>
        </template>
        <el-menu-item-group>
          <el-menu-item index="/invoice" class="invoice">发票</el-menu-item>
        </el-menu-item-group>
        <el-menu-item-group>
          <el-menu-item index="/declaration" class="declaration">报关单</el-menu-item>
        </el-menu-item-group>
        <el-menu-item-group>
          <el-menu-item index="/contract" class="contract">合同</el-menu-item>
        </el-menu-item-group>
        <el-menu-item-group>
          <el-menu-item index="/landing" class="landing">提单</el-menu-item>
        </el-menu-item-group>
        <!-- <el-menu-item-group>
          <el-menu-item index="/test" class="test">测试</el-menu-item>
        </el-menu-item-group> -->
      </el-sub-menu>

      <!-- <el-menu-item index="2">
        <el-icon><icon-menu /></el-icon>
        <span>报关单</span>
      </el-menu-item>

      <el-menu-item index="3">
        <el-icon><Document /></el-icon>
        <span>合同</span>
      </el-menu-item>

      <el-menu-item index="4">
        <el-icon><icon-menu /></el-icon>
        <span>提单</span>
      </el-menu-item> -->
    </el-menu>
  <!-- </el-aside> -->
  </div>
</template>

<script>
  export default {
    name: 'Sidebar',
    methods: {
    handleSelect(index, indexPath, item) {
      console.log('Selected Index:', index)
      this.$router.push(index)
    }
  }
  }
</script>

<style scoped>
el-menu {
    border-right-color: #dcdfe6;
}
</style>