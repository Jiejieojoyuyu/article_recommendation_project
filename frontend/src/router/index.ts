import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

// 路由组件懒加载
const Home = () => import('../views/Home.vue')
const Login = () => import('../views/Login.vue')
const Register = () => import('../views/Register.vue')
const Search = () => import('../views/Search.vue')
const Papers = () => import('../views/Papers.vue')
const PaperDetail = () => import('../views/PaperDetail.vue')
const Authors = () => import('../views/Authors.vue')
const AuthorDetail = () => import('../views/AuthorDetail.vue')
const Workspace = () => import('../views/Workspace.vue')
const Profile = () => import('../views/Profile.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home,
      meta: { title: '首页' }
    },
    {
      path: '/login',
      name: 'Login',
      component: Login,
      meta: { title: '登录', requiresGuest: true }
    },
    {
      path: '/register',
      name: 'Register', 
      component: Register,
      meta: { title: '注册', requiresGuest: true }
    },
    {
      path: '/search',
      name: 'Search',
      component: Search,
      meta: { title: '智能搜索' }
    },
    {
      path: '/papers',
      name: 'Papers',
      component: Papers,
      meta: { title: '论文库' }
    },
    {
      path: '/papers/:id',
      name: 'PaperDetail',
      component: PaperDetail,
      meta: { title: '论文详情' }
    },
    {
      path: '/authors',
      name: 'Authors',
      component: Authors,
      meta: { title: '学者' }
    },
    {
      path: '/authors/:id',
      name: 'AuthorDetail',
      component: AuthorDetail,
      meta: { title: '学者详情' }
    },
    {
      path: '/workspace',
      name: 'Workspace',
      component: Workspace,
      meta: { title: '个人工作台', requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'Profile',
      component: Profile,
      meta: { title: '个人资料', requiresAuth: true }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('../views/NotFound.vue'),
      meta: { title: '页面未找到' }
    }
  ],
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 学术推荐系统` : '学术推荐系统'
  
  // 检查认证状态
  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }
  
  // 已登录用户访问登录/注册页面
  if (to.meta.requiresGuest && userStore.isAuthenticated) {
    next({ name: 'Home' })
    return
  }
  
  next()
})

export default router

