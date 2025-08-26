<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full text-center">
      <div class="mb-8">
        <h1 class="text-9xl font-bold text-gray-300 dark:text-gray-600">404</h1>
      </div>
      
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
        页面未找到
      </h2>
      
      <p class="text-gray-600 dark:text-gray-400 mb-8">
        抱歉，您访问的页面不存在或已被移动。
      </p>
      
      <div class="space-y-4">
        <router-link to="/" class="btn-primary block">
          返回首页
        </router-link>
        
        <button
          @click="$router.go(-1)"
          class="btn-secondary block w-full"
        >
          返回上一页
        </button>
      </div>
    </div>
  </div>
</template>

