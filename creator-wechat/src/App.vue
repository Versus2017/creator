<template>
  <div id="app">
    <div
      style="width: 100vw; height: 100vh; display: flex; justify-content: space-around; align-items: center; color: #fff; font-size: 14px;"
      v-if="landscape">
      请将手机竖置
    </div>
    <div v-else id="nav">
      <router-view v-wechat-title="title"/>
    </div>
  </div>
</template>

<script>
export default {
  data () {
    return {
      landscape: false
    }
  },

  created () {
    window.addEventListener('orientationchange', this.handleOrientationchange)
    if (this.$route.meta.needAuth) {
      this.$store.dispatch('getUser')
    }
  },

  mounted () {
    this.configWechat()
  },

  beforeDestroy () {
    window.removeEventListener('orientationchange', this.handleOrientationchange)
  },

  computed: {
    // https://github.com/deboyblog/vue-wechat-title/issues/25
    title: {
      cache: false,
      get () {
        return this.$route.query.title || this.$route.meta.title
      }
    }
  },

  methods: {
    handleOrientationchange () {
      switch (window.orientation) {
        case -90:
        case 90:
          this.landscape = true
          break
        default:
          this.landscape = false
      }
    },

    async configWechat () {
      try {
        let resp = await this.$http.get('/wx_configs', {
          params: { url: window.location.href }
        })
        let wxConfigs = resp.data
        if (wxConfigs.success) {
          this.$wechat.config({
            appId: wxConfigs.appid,
            timestamp: wxConfigs.timestamp,
            nonceStr: wxConfigs.noncestr,
            signature: wxConfigs.signature,
            jsApiList: [
              'closeWindow',
              'chooseImage',
              'uploadImage',
              'getLocalImgData'
            ],
            debug: false})
        }
      } catch (e) {
        // fetch js configs error
      }

      this.$wechat.ready(function () {
        console.log('wx ready')
      })
    }
  }
}
</script>

<style lang="less">
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}
#nav {
  padding: 30px;
  a {
    font-weight: bold;
    color: #2c3e50;
    &.router-link-exact-active {
      color: #42b983;
    }
  }
}
</style>
