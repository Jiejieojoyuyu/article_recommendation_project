<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <div v-if="author" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- 作者信息 -->
      <div class="card p-8 mb-8">
        <div class="flex items-start space-x-6">
          <div class="w-24 h-24 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <span class="text-white font-bold text-2xl">
              {{ getInitials(author.name) }}
            </span>
          </div>
          
          <div class="flex-1">
            <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              {{ author.name }}
            </h1>
            
            <p class="text-lg text-gray-600 dark:text-gray-400 mb-4">
              {{ author.affiliation }}
            </p>
            
            <div class="grid grid-cols-3 gap-6 mb-6">
              <div class="text-center">
                <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ author.h_index }}</div>
                <div class="text-sm text-gray-500">H指数</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ author.citation_count }}</div>
                <div class="text-sm text-gray-500">引用数</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ author.paper_count }}</div>
                <div class="text-sm text-gray-500">论文数</div>
              </div>
            </div>
            
            <div class="mb-6">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">研究领域</h3>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="area in author.research_areas"
                  :key="area"
                  class="badge-primary"
                >
                  {{ area }}
                </span>
              </div>
            </div>
            
            <div v-if="author.bio" class="mb-6">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">简介</h3>
              <p class="text-gray-700 dark:text-gray-300">{{ author.bio }}</p>
            </div>
            
            <!-- 操作按钮 -->
            <div class="flex gap-4">
              <button
                @click="toggleFollow"
                :class="[
                  'btn',
                  isFollowing ? 'btn-danger' : 'btn-primary'
                ]"
              >
                {{ isFollowing ? '取消关注' : '关注学者' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 代表作品 -->
      <div class="card p-6 mb-8">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">代表作品</h2>
        <div v-if="papers.length > 0" class="space-y-4">
          <div
            v-for="paper in papers"
            :key="paper.id"
            class="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 p-4 rounded"
            @click="$router.push(`/papers/${paper.short_id || paper.id}`)"
          >
            <h3 class="font-medium text-gray-900 dark:text-white mb-1">{{ paper.title }}</h3>
            <div class="flex items-center justify-between text-sm text-gray-500">
              <span>{{ paper.year }} • {{ paper.journal }}</span>
              <span>{{ paper.citation_count }} 引用</span>
            </div>
          </div>
        </div>
        <p v-else class="text-gray-500 dark:text-gray-400">暂无论文数据</p>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="loading" class="min-h-screen flex items-center justify-center">
      <div class="text-center">
        <div class="spinner mx-auto mb-4"></div>
        <p class="text-gray-500 dark:text-gray-400">加载学者信息...</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/services/api'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()

const author = ref(null)
const papers = ref([])
const loading = ref(false)
const isFollowing = ref(false)

const getInitials = (name: string) => {
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

const fetchAuthor = async () => {
  try {
    loading.value = true
    const authorId = route.params.id as string
    
    const [authorRes, papersRes] = await Promise.all([
      api.authors.get(authorId),
      api.authors.papers(authorId, { limit: 10, sort_by: 'citation', order: 'desc' })
    ])
    
    author.value = authorRes.data
    papers.value = papersRes.data
  } catch (error) {
    console.error('获取学者信息失败:', error)
  } finally {
    loading.value = false
  }
}

const toggleFollow = async () => {
  if (!userStore.isAuthenticated) {
    return
  }
  
  try {
    const authorId = route.params.id as string
    
    if (isFollowing.value) {
      await api.authors.unfollow(authorId)
      isFollowing.value = false
    } else {
      await api.authors.follow(authorId)
      isFollowing.value = true
    }
  } catch (error) {
    console.error('关注操作失败:', error)
  }
}

onMounted(() => {
  fetchAuthor()
})
</script>

