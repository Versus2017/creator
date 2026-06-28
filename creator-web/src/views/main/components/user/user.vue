<template>
  <div>
    <div class="user-avatar-wrapper" @click="goToProfile">
      <div class="user-name-display">
        <span>{{ name }}</span>
      </div>
      <div class="avatar-container">
        <Avatar :src="userAvatar" class="user-avatar" icon="ios-person"/>
      </div>
    </div>
  </div>
</template>

<script>
  import './user.less'

  export default {
    name: 'User',

    computed: {
      // 获取当前用户信息
      currentUser() {
        return this.$store.getters.user || {}
      },
      
      name () {
        return this.currentUser.nickname || this.currentUser.username || ''
      },
      
      // 从 store 中获取头像
      userAvatar() {
        return this.currentUser.avatar || ''
      }
    },

    methods: {
      // 跳转到个人中心页面
      goToProfile() {
        this.$router.push({ name: 'profile' })
      }
    },

    async mounted () {
      // 确保认证状态已加载
      await this.$auth.ready()
      
      // 刷新用户信息
      if (this.$auth.check()) {
        await this.$store.dispatch('refreshUser')
      }
    }
  }
</script>
