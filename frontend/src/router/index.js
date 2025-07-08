import { createRouter, createWebHistory } from "vue-router";

// 引入视图组件
import Home from '../views/Home.vue'
import Invoice from '../views/Invoice.vue'
import Declaration from '../views/Declaration.vue'
import Contract from '../views/Contract.vue'
import Landing from '../views/Landing.vue'
import Test from '../views/Test.vue'
import Documents from '../views/Documents.vue'


// 创建路由
const routes = [
  { path: '/home', component: Home },
  // { path: '/invoice', name: 'Invoice', component: Invoice },
  // { path: '/declaration', name: 'Declaration', component: Declaration },
  // { path: '/contract', name: 'Contract', component: Contract },
  // { path: '/landing', name: 'Landing', component: Landing},
  { path: '/invoice/:fileId?', name: 'Invoice', component: Invoice },
  { path: '/declaration/:fileId?', name: 'Declaration', component: Declaration },
  { path: '/contract/:fileId?', name: 'Contract', component: Contract },
  { path: '/landing/:fileId?', name: 'Landing', component: Landing},
  { path: '/test', name: 'Test', component: Test},
  { path: '/documents', name: 'Docuemnts', component: Documents},
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router;