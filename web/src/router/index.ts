import { createRouter, createWebHistory } from 'vue-router'
import ScreenView from '@/views/ScreenView.vue'
import TradingView from '@/views/TradingView.vue'
import ReplayView from '@/views/ReplayView.vue'
import SettingsView from '@/views/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/screen'
    },
    {
      path: '/screen',
      name: 'screen',
      component: ScreenView,
      meta: { title: '股票筛选' }
    },
    {
      path: '/trading',
      name: 'trading',
      component: TradingView,
      meta: { title: '交易看板' }
    },
    {
      path: '/replay',
      name: 'replay',
      component: ReplayView,
      meta: { title: '盘口回放' }
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
      meta: { title: '系统设置' }
    }
  ]
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'Stock Review'} - Stock Review`
  next()
})

export default router
