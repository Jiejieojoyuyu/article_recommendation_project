<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">个人资料</h1>
        <p class="text-gray-600 dark:text-gray-300">管理您的账户信息</p>
      </div>

      <!-- 基本信息 -->
      <div class="card p-6 mb-8">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">基本信息</h2>
        
        <form @submit.prevent="updateProfile" class="space-y-4">
          <div>
            <label class="label">用户名</label>
            <input
              v-model="form.username"
              type="text"
              disabled
              class="input bg-gray-100 dark:bg-gray-600"
            >
          </div>
          
          <div>
            <label class="label">邮箱</label>
            <input
              v-model="form.email"
              type="email"
              required
              class="input"
            >
          </div>
          
          <div>
            <label class="label">姓名</label>
            <input
              v-model="form.full_name"
              type="text"
              required
              class="input"
            >
          </div>
          
          <div>
            <label class="label">所属机构</label>
            <input
              v-model="form.affiliation"
              type="text"
              class="input"
            >
          </div>
          
          <div>
            <label class="label">研究兴趣</label>
            <textarea
              v-model="researchInterestsText"
              class="input min-h-[100px]"
              placeholder="请输入研究兴趣，用逗号分隔"
            ></textarea>
          </div>
          
          <div class="flex gap-4">
            <button
              type="submit"
              :disabled="userStore.loading"
              class="btn-primary"
            >
              {{ userStore.loading ? '保存中...' : '保存更改' }}
            </button>
          </div>
        </form>
      </div>

      <!-- 修改密码 -->
      <div class="card p-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">修改密码</h2>
        
        <form @submit.prevent="changePassword" class="space-y-4">
          <div>
            <label class="label">当前密码</label>
            <input
              v-model="passwordForm.current_password"
              type="password"
              required
              class="input"
            >
          </div>
          
          <div>
            <label class="label">新密码</label>
            <input
              v-model="passwordForm.new_password"
              type="password"
              required
              class="input"
            >
          </div>
          
          <div>
            <label class="label">确认新密码</label>
            <input
              v-model="passwordForm.confirm_password"
              type="password"
              required
              class="input"
            >
          </div>
          
          <div class="flex gap-4">
            <button
              type="submit"
              :disabled="!isPasswordFormValid || userStore.loading"
              class="btn-primary"
            >
              修改密码
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const form = ref({
  username: '',
  email: '',
  full_name: '',
  affiliation: '',
  research_interests: []
})

const passwordForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const researchInterestsText = ref('')

const isPasswordFormValid = computed(() => {
  return passwordForm.value.new_password === passwordForm.value.confirm_password &&
         passwordForm.value.new_password.length >= 8
})

const updateProfile = async () => {
  try {
    const interests = researchInterestsText.value
      .split(',')
      .map(item => item.trim())
      .filter(item => item.length > 0)
    
    await userStore.updateProfile({
      email: form.value.email,
      full_name: form.value.full_name,
      affiliation: form.value.affiliation,
      research_interests: interests
    })
    
    alert('资料更新成功！')
  } catch (error) {
    alert('更新失败，请重试')
  }
}

const changePassword = async () => {
  try {
    await userStore.changePassword({
      current_password: passwordForm.value.current_password,
      new_password: passwordForm.value.new_password
    })
    
    // 清空表单
    passwordForm.value = {
      current_password: '',
      new_password: '',
      confirm_password: ''
    }
    
    alert('密码修改成功！')
  } catch (error) {
    alert('密码修改失败，请检查当前密码是否正确')
  }
}

onMounted(() => {
  if (userStore.user) {
    form.value = {
      username: userStore.user.username,
      email: userStore.user.email,
      full_name: userStore.user.full_name,
      affiliation: userStore.user.affiliation || '',
      research_interests: userStore.user.research_interests
    }
    researchInterestsText.value = userStore.user.research_interests.join(', ')
  }
})
</script>

