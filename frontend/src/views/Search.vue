<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- 搜索头部 -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-4">智能论文搜索</h1>
        <div class="max-w-3xl mx-auto">
          <div class="relative">
            <input
              v-model="searchQuery"
              @keyup.enter="handleSearch"
              type="text"
              placeholder="搜索论文、作者或关键词..."
              class="w-full px-6 py-4 pr-16 text-lg rounded-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
            <button
              @click="handleSearch"
              :disabled="loading"
              class="absolute right-2 top-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-full transition-colors disabled:opacity-50"
            >
              {{ loading ? '搜索中...' : '搜索' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 搜索结果 -->
      <div v-if="searchResults.length > 0" class="space-y-6">
        <div class="text-sm text-gray-600 dark:text-gray-400">
          找到 {{ totalResults }} 篇相关论文
        </div>
        
        <div class="grid gap-6">
          <div
            v-for="paper in searchResults"
            :key="paper.id"
            class="card-hover p-6 cursor-pointer"
            @click="$router.push(`/papers/${paper.short_id || paper.id}`)"
          >
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              {{ paper.title }}
            </h3>
            <p class="text-gray-600 dark:text-gray-400 text-sm mb-3">
              {{ paper.author_names.join(', ') }}
            </p>
            <div class="flex items-center justify-between text-sm text-gray-500">
              <span>{{ paper.year }} • {{ paper.journal }}</span>
              <span>{{ paper.citation_count }} 引用</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!loading && searchQuery" class="text-center py-12">
        <p class="text-gray-500 dark:text-gray-400">未找到相关论文，请尝试其他关键词</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/services/api'

const route = useRoute()

const searchQuery = ref('')
const searchResults = ref([])
const totalResults = ref(0)
const loading = ref(false)

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return
  
  try {
    loading.value = true
    const response = await api.search.papers({
      query: searchQuery.value,
      search_type: 'hybrid',
      limit: 20
    })
    
    searchResults.value = response.data.papers
    totalResults.value = response.data.total
  } catch (error) {
    console.error('搜索失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const q = route.query.q as string
  if (q) {
    searchQuery.value = q
    handleSearch()
  }
})
</script>

