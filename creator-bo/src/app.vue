<template>
  <div v-if="$auth.ready()" id="app" class="app-main">
    <router-view/>
  </div>
  <div v-else class="app-main">载入中...</div>
</template>

<script>
export default {
  name: 'App',

  beforeCreate () {
    this.$store.dispatch('fetchConfig', {vue: this})
  },

  created () {
    this.$auth.ready(function () {
      console.log(this.$auth.check(), 'check')
      console.log(this.$auth.user(), 'user')
      if (this.$auth.check()) {
        this.$store.dispatch('user/authSuccess', this)
      }
    })
  },
}
</script>

<style lang="less" scoped>
  .app-main {
    width: 100%;
    height: 100%;
    -ms-overflow-style: -ms-autohiding-scrollbar;
  }
</style>

<style lang="less">
  .size{
    width: 100%;
    height: 100%;
  }
  html,body{
    .size;
    overflow: hidden;
    margin: 0;
    padding: 0;
  }
  #app {
    .size;
  }
</style>
