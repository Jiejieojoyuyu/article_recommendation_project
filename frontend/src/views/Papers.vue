<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">论文库</h1>
        <p class="text-gray-600 dark:text-gray-300">浏览和发现学术论文</p>
      </div>

      <!-- 论文列表 -->
      <div v-if="papers.length > 0" class="grid gap-6">
        <div
          v-for="paper in papers"
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
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-500">{{ paper.year }} • {{ paper.journal }}</span>
            <div class="flex items-center space-x-4">
              <span class="text-blue-600 dark:text-blue-400">{{ paper.citation_count }} 引用</span>
              <span v-if="paper.truth_value_score" class="badge-primary">
                真值: {{ paper.truth_value_score.toFixed(1) }}
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

const papers = ref([])
const loading = ref(false)

const fetchPapers = async () => {
  try {
    loading.value = true
    const response = await api.papers.list({
      limit: 20,
      sort_by: 'date',
      order: 'desc'
    })
    papers.value = response.data
  } catch (error) {
    console.error('获取论文失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchPapers()
})
</script>

