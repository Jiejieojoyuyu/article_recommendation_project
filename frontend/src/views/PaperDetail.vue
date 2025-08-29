<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <div v-if="paper" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- 论文标题和基本信息 -->
      <div class="card p-8 mb-8">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          {{ paper.title }}
        </h1>
        
        <div class="flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-6">
          <span>{{ paper.author_names.join(', ') }}</span>
          <span>•</span>
          <span>{{ paper.year }}</span>
          <span>•</span>
          <span>{{ paper.journal }}</span>
          <span>•</span>
          <span>{{ paper.citation_count }} 引用</span>
        </div>

        <!-- 真值分数 -->
        <div v-if="paper.truth_value_score" class="mb-6">
          <div class="inline-flex items-center bg-blue-100 dark:bg-blue-900 px-3 py-1 rounded-full">
            <span class="text-blue-800 dark:text-blue-200 font-medium">
              真值分数: {{ paper.truth_value_score.toFixed(1) }}/10
            </span>
          </div>
        </div>

        <!-- 摘要 -->
        <div class="mb-6">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-3">摘要</h2>
          <p class="text-gray-700 dark:text-gray-300 leading-relaxed">
            {{ paper.abstract }}
          </p>
        </div>

        <!-- 关键词 -->
        <div class="mb-6">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-3">关键词</h2>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="keyword in paper.keywords"
              :key="keyword"
              class="badge-secondary"
            >
              {{ keyword }}
            </span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="flex gap-4">
          <button
            @click="toggleBookmark"
            :class="[
              'btn',
              isBookmarked ? 'btn-danger' : 'btn-primary'
            ]"
          >
            {{ isBookmarked ? '取消收藏' : '收藏论文' }}
          </button>
          
          <button
            @click="generateSummary"
            :disabled="summaryLoading"
            class="btn-secondary"
          >
            {{ summaryLoading ? '生成中...' : 'AI总结' }}
          </button>
        </div>
      </div>

      <!-- AI总结 -->
      <div v-if="aiSummary" class="card p-6 mb-8">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">AI总结</h3>
        <p class="text-gray-700 dark:text-gray-300">{{ aiSummary.content }}</p>
      </div>

      <!-- 引用和参考文献 -->
      <div class="grid md:grid-cols-2 gap-8">
        <div class="card p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">参考文献</h3>
          <div v-if="references.length > 0" class="space-y-3">
            <div
              v-for="ref in references"
              :key="ref.id"
              class="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 p-3 rounded"
              @click="$router.push(`/papers/${ref.short_id || ref.id}`)"
            >
              <h4 class="font-medium text-gray-900 dark:text-white text-sm">{{ ref.title }}</h4>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ ref.author_names.join(', ') }}</p>
            </div>
          </div>
          <p v-else class="text-gray-500 dark:text-gray-400">暂无参考文献</p>
        </div>

        <div class="card p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">被引文献</h3>
          <div v-if="citations.length > 0" class="space-y-3">
            <div
              v-for="citation in citations"
              :key="citation.id"
              class="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 p-3 rounded"
              @click="$router.push(`/papers/${citation.short_id || citation.id}`)"
            >
              <h4 class="font-medium text-gray-900 dark:text-white text-sm">{{ citation.title }}</h4>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ citation.author_names.join(', ') }}</p>
            </div>
          </div>
          <p v-else class="text-gray-500 dark:text-gray-400">暂无被引文献</p>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="loading" class="min-h-screen flex items-center justify-center">
      <div class="text-center">
        <div class="spinner mx-auto mb-4"></div>
        <p class="text-gray-500 dark:text-gray-400">加载论文详情...</p>
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

const paper = ref(null)
const references = ref([])
const citations = ref([])
const aiSummary = ref(null)
const loading = ref(false)
const summaryLoading = ref(false)
const isBookmarked = ref(false)

const fetchPaper = async () => {
  try {
    loading.value = true
    const paperId = route.params.id as string
    
    const [paperRes, referencesRes, citationsRes] = await Promise.all([
      api.papers.get(paperId),
      api.papers.references(paperId),
      api.papers.citations(paperId)
    ])
    
    paper.value = paperRes.data
    references.value = referencesRes.data
    citations.value = citationsRes.data
    
    // 添加阅读记录
    if (userStore.isAuthenticated) {
      api.workspace.addReading(paperId)
    }
  } catch (error) {
    console.error('获取论文详情失败:', error)
  } finally {
    loading.value = false
  }
}

const toggleBookmark = async () => {
  if (!userStore.isAuthenticated) {
    return
  }
  
  try {
    const paperId = route.params.id as string
    
    if (isBookmarked.value) {
      await api.papers.unbookmark(paperId)
      isBookmarked.value = false
    } else {
      await api.papers.bookmark(paperId)
      isBookmarked.value = true
    }
  } catch (error) {
    console.error('收藏操作失败:', error)
  }
}

const generateSummary = async () => {
  try {
    summaryLoading.value = true
    const paperId = route.params.id as string
    const response = await api.ai.summarize(paperId)
    aiSummary.value = response.data
  } catch (error) {
    console.error('生成总结失败:', error)
  } finally {
    summaryLoading.value = false
  }
}

onMounted(() => {
  fetchPaper()
})
</script>

