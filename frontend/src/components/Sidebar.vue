<!-- src/components/Sidebar.vue -->
<template>
  <!-- <el-aside width="200px" class="sidebar"> -->
  <div class="sidebar">
    <el-menu default-active="/document" class="el-menu-vertical" @select="handleSelect">
      <el-sub-menu index="1" @click.native="handleSubMenuClick">
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
      </el-sub-menu>


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
      },
      handleSubMenuClick(event) {
        // 判断是否点击的是标题区域，防止误触子菜单
        const titleEl = event.target.closest('.el-sub-menu__title');
        console.log('SubMenu Clicked:', titleEl);
        // 移除自动跳转到documents的逻辑，让用户主动选择子菜单项
        if (titleEl) {
          this.$router.push('/documents');
        }
      }
    }
  }
</script>

<style scoped>
el-menu {
    border-right-color: #dcdfe6;
}
</style>