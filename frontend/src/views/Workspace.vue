<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">个人工作台</h1>
        <p class="text-gray-600 dark:text-gray-300">管理您的学术研究资料</p>
      </div>

      <!-- 统计卡片 -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
        <div class="card p-6 text-center">
          <div class="text-2xl font-bold text-blue-600 dark:text-blue-400 mb-2">
            {{ stats.total_bookmarks }}
          </div>
          <div class="text-sm text-gray-500">收藏论文</div>
        </div>
        <div class="card p-6 text-center">
          <div class="text-2xl font-bold text-green-600 dark:text-green-400 mb-2">
            {{ stats.total_folders }}
          </div>
          <div class="text-sm text-gray-500">收藏夹</div>
        </div>
        <div class="card p-6 text-center">
          <div class="text-2xl font-bold text-purple-600 dark:text-purple-400 mb-2">
            {{ stats.followed_authors_count }}
          </div>
          <div class="text-sm text-gray-500">关注学者</div>
        </div>
        <div class="card p-6 text-center">
          <div class="text-2xl font-bold text-orange-600 dark:text-orange-400 mb-2">
            {{ stats.reading_history_count }}
          </div>
          <div class="text-sm text-gray-500">阅读历史</div>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <div class="grid lg:grid-cols-3 gap-8">
        <!-- 左侧：收藏和推荐 -->
        <div class="lg:col-span-2 space-y-8">
          <!-- 智能推荐 -->
          <div class="card p-6">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">为您推荐</h2>
            <div v-if="recommendations.length > 0" class="space-y-4">
              <div
                v-for="rec in recommendations"
                :key="rec.paper.id"
                class="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 p-4 rounded"
                @click="$router.push(`/papers/${rec.paper.short_id || rec.paper.id}`)"
              >
                <h3 class="font-medium text-gray-900 dark:text-white mb-1">{{ rec.paper.title }}</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">{{ rec.paper.author_names.join(', ') }}</p>
                <p class="text-xs text-blue-600 dark:text-blue-400">{{ rec.reason }}</p>
              </div>
            </div>
            <p v-else class="text-gray-500 dark:text-gray-400">暂无推荐内容</p>
          </div>

          <!-- 最近收藏 -->
          <div class="card p-6">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">最近收藏</h2>
            <div v-if="recentBookmarks.length > 0" class="space-y-4">
              <div
                v-for="paper in recentBookmarks"
                :key="paper.id"
                class="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 p-4 rounded"
                @click="$router.push(`/papers/${paper.short_id || paper.id}`)"
              >
                <h3 class="font-medium text-gray-900 dark:text-white mb-1">{{ paper.title }}</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">{{ paper.author_names.join(', ') }}</p>
              </div>
            </div>
            <p v-else class="text-gray-500 dark:text-gray-400">暂无收藏内容</p>
          </div>
        </div>

        <!-- 右侧：关注的学者 -->
        <div class="space-y-8">
          <div class="card p-6">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">关注的学者</h2>
            <div v-if="followedAuthors.length > 0" class="space-y-4">
              <div
                v-for="author in followedAuthors"
                :key="author.id"
                class="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 p-3 rounded"
                @click="$router.push(`/authors/${author.id}`)"
              >
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <span class="text-white font-bold text-sm">
                      {{ getInitials(author.name) }}
                    </span>
                  </div>
                  <div>
                    <h3 class="font-medium text-gray-900 dark:text-white text-sm">{{ author.name }}</h3>
                    <p class="text-xs text-gray-500 dark:text-gray-400">{{ author.affiliation }}</p>
                  </div>
                </div>
              </div>
            </div>
            <p v-else class="text-gray-500 dark:text-gray-400">暂无关注的学者</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'

const stats = ref({
  total_bookmarks: 0,
  total_folders: 0,
  followed_authors_count: 0,
  reading_history_count: 0
})
const recommendations = ref([])
const recentBookmarks = ref([])
const followedAuthors = ref([])

const getInitials = (name: string) => {
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

const fetchDashboard = async () => {
  try {
    const [dashboardRes, recommendationsRes] = await Promise.all([
      api.workspace.dashboard(),
      api.workspace.recommendations({ limit: 5 })
    ])
    
    const dashboard = dashboardRes.data
    stats.value = dashboard.user_stats
    recentBookmarks.value = dashboard.recent_bookmarks
    followedAuthors.value = dashboard.followed_authors
    recommendations.value = recommendationsRes.data.recommendations
  } catch (error) {
    console.error('获取工作台数据失败:', error)
  }
}

onMounted(() => {
  fetchDashboard()
})
</script>

