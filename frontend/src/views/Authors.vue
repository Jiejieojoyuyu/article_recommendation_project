<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">学者库</h1>
        <p class="text-gray-600 dark:text-gray-300">探索学术界的杰出学者</p>
      </div>

      <!-- 学者列表 -->
      <div v-if="authors.length > 0" class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="author in authors"
          :key="author.id"
          class="card-hover p-6 cursor-pointer"
          @click="$router.push(`/authors/${author.id}`)"
        >
          <div class="text-center">
            <div class="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <span class="text-white font-bold text-lg">
                {{ getInitials(author.name) }}
              </span>
            </div>
            
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              {{ author.name }}
            </h3>
            
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
              {{ author.affiliation }}
            </p>
            
            <div class="flex justify-center space-x-4 text-sm text-gray-500">
              <span>H指数: {{ author.h_index }}</span>
              <span>论文: {{ author.paper_count }}</span>
            </div>
            
            <div class="mt-3 flex flex-wrap justify-center gap-1">
              <span
                v-for="area in author.research_areas.slice(0, 3)"
                :key="area"
                class="badge-secondary text-xs"
              >
                {{ area }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-else-if="loading" class="text-center py-12">
        <div class="spinner mx-auto"></div>
        <p class="text-gray-500 dark:text-gray-400 mt-4">加载中...</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'

const authors = ref([])
const loading = ref(false)

const getInitials = (name: string) => {
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

const fetchAuthors = async () => {
  try {
    loading.value = true
    const response = await api.authors.list({
      limit: 20,
      sort_by: 'h_index',
      order: 'desc'
    })
    authors.value = response.data
  } catch (error) {
    console.error('获取学者失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAuthors()
})
</script>

