<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <div class="mx-auto h-12 w-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg"></div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white">
          创建账户
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
          已有账户？
          <router-link to="/login" class="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400">
            立即登录
          </router-link>
        </p>
      </div>
      
      <form class="mt-8 space-y-6" @submit.prevent="handleRegister">
        <div v-if="userStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {{ userStore.error }}
        </div>
        
        <div class="space-y-4">
          <div>
            <label for="username" class="label">用户名</label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              required
              class="input"
              placeholder="请输入用户名"
            >
          </div>
          
          <div>
            <label for="email" class="label">邮箱</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              class="input"
              placeholder="请输入邮箱地址"
            >
          </div>
          
          <div>
            <label for="full_name" class="label">姓名</label>
            <input
              id="full_name"
              v-model="form.full_name"
              type="text"
              required
              class="input"
              placeholder="请输入真实姓名"
            >
          </div>
          
          <div>
            <label for="affiliation" class="label">所属机构</label>
            <input
              id="affiliation"
              v-model="form.affiliation"
              type="text"
              class="input"
              placeholder="请输入所属机构（可选）"
            >
          </div>
          
          <div>
            <label for="password" class="label">密码</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              required
              class="input"
              placeholder="请输入密码"
            >
          </div>
          
          <div>
            <label for="confirm_password" class="label">确认密码</label>
            <input
              id="confirm_password"
              v-model="form.confirm_password"
              type="password"
              required
              class="input"
              placeholder="请再次输入密码"
            >
          </div>
        </div>

        <div class="flex items-center">
          <input
            id="agree"
            v-model="form.agree"
            type="checkbox"
            required
            class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          >
          <label for="agree" class="ml-2 block text-sm text-gray-900 dark:text-gray-300">
            我同意
            <a href="#" class="text-blue-600 hover:text-blue-500 dark:text-blue-400">服务条款</a>
            和
            <a href="#" class="text-blue-600 hover:text-blue-500 dark:text-blue-400">隐私政策</a>
          </label>
        </div>

        <div>
          <button
            type="submit"
            :disabled="userStore.loading || !isFormValid"
            class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="userStore.loading" class="spinner mr-2"></span>
            {{ userStore.loading ? '注册中...' : '注册' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const form = ref({
  username: '',
  email: '',
  full_name: '',
  affiliation: '',
  password: '',
  confirm_password: '',
  agree: false,
  research_interests: []
})

const isFormValid = computed(() => {
  return form.value.password === form.value.confirm_password && 
         form.value.agree &&
         form.value.username &&
         form.value.email &&
         form.value.full_name &&
         form.value.password
})

const handleRegister = async () => {
  if (!isFormValid.value) {
    return
  }
  
  try {
    await userStore.register({
      username: form.value.username,
      email: form.value.email,
      full_name: form.value.full_name,
      affiliation: form.value.affiliation,
      password: form.value.password,
      research_interests: form.value.research_interests
    })
    
    // 注册成功后重定向到首页
    router.push('/')
  } catch (error) {
    // 错误已在store中处理
  }
}
</script>

