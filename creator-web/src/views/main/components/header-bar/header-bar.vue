<template>
  <div class="header-bar">
    <!-- 左侧品牌区域 -->
    <div class="brand-section">
      <div class="logo-wrapper" @click="goHome">
        <div class="logo-icon">
          <svg class="logo-image" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-label="创思Logo">
            <defs>
              <linearGradient id="header-logo-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#3B82F6;stop-opacity:1" />
                <stop offset="50%" style="stop-color:#8B5CF6;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#06B6D4;stop-opacity:1" />
              </linearGradient>
            </defs>
            <!-- 创意灯泡图标 -->
            <path d="M 50 20 Q 35 20 25 30 Q 15 40 15 55 Q 15 65 20 72 L 30 72 L 30 80 Q 30 85 35 85 L 65 85 Q 70 85 70 80 L 70 72 L 80 72 Q 85 65 85 55 Q 85 40 75 30 Q 65 20 50 20 Z M 40 75 L 60 75 L 60 72 L 40 72 Z" 
                  fill="url(#header-logo-gradient)" 
                  stroke="url(#header-logo-gradient)" 
                  stroke-width="2"/>
            <!-- 闪电图标（灵感） -->
            <path d="M 50 30 L 45 50 L 52 50 L 48 65 L 60 45 L 53 45 Z" 
                  fill="#FFFFFF" 
                  opacity="0.9"/>
          </svg>
        </div>
        <div class="brand-info">
          <h1 class="brand-name">创思</h1>
          <span class="brand-tagline">AI智能脚本创作</span>
        </div>
      </div>
    </div>
    
    <!-- 中间导航区域 -->
    <div class="nav-section">
      <nav class="main-nav">
        <a 
          href="#" 
          class="nav-item" 
          :class="{ active: $route.name === 'home' }" 
          @click.prevent="goToPage('home')"
        >
          <Icon type="md-home" />
          <span>首页</span>
        </a>
        <a 
          href="#" 
          class="nav-item" 
          :class="{ active: $route.name === 'creativity' }" 
          @click.prevent="goToPage('creativity')"
        >
          <Icon type="ios-bulb" />
          <span>创意</span>
        </a>
        <a 
          href="#" 
          class="nav-item" 
          :class="{ active: $route.name === 'scripts' || $route.name === 'script-detail' }" 
          @click.prevent="goToPage('scripts')"
        >
          <Icon type="ios-document-outline" />
          <span>脚本</span>
        </a>
        <a 
          href="#" 
          class="nav-item" 
          :class="{ active: $route.name === 'research-list' || $route.name === 'research-chat' || $route.name === 'research-detail' }" 
          @click.prevent="goToPage('research-list')"
        >
          <Icon type="ios-flask" />
          <span>研究</span>
        </a>
      </nav>
    </div>
    
    <!-- 右侧用户区域 -->
    <div class="user-section">
      <!-- 未登录状态 -->
      <div v-if="!$auth.check()" class="auth-buttons">
        <Button type="text" class="login-btn" @click="goToLogin">登录</Button>
      </div>
      
      <!-- 已登录状态 -->
      <div v-else class="user-info">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script>
import siderTrigger from './sider-trigger'
import customBreadCrumb from './custom-bread-crumb'
import './header-bar.less'

export default {
  name: 'HeaderBar',
  components: {
    siderTrigger,
    customBreadCrumb
  },
  props: {
    collapsed: Boolean
  },
  computed: {
    breadCrumbList () {
      return this.$store.state.breadCrumbList
    },

    isLoggedIn () {
      return this.$store.getters.authorized
    }
  },
  methods: {
    goHome () {
      this.$router.push('/')
    },
    
    goToPage(name) {
      this.$router.push({ name })
      
      // 路由切换后滚动到顶部
      this.$nextTick(() => {
        setTimeout(() => {
          // 找到内容滚动容器
          const contentWrapper = document.querySelector('.content-wrapper')
          if (contentWrapper) {
            // 滚动内容容器到顶部
            contentWrapper.scrollTo({
              top: 0,
              left: 0,
              behavior: 'smooth'
            })
          } else {
            // 如果找不到内容容器，就滚动window
            window.scrollTo({
              top: 0,
              left: 0,
              behavior: 'smooth'
            })
          }
        }, 100)
      })
    },
    
    goToLogin() {
      this.$router.push('/login')
    },
    
    goToRegister() {
      // TODO: 跳转到注册页面
      this.$Message.info('注册功能开发中...')
    },
    
    showPricing() {
      // 跳转到定价页面
      this.$router.push('/pricing')
    },

    handleCollpasedChange (state) {
      this.$emit('on-coll-change', state)
    }
  }
}
</script>

<style lang="less" scoped>
// 样式已移动到独立的 header-bar.less 文件中
</style>