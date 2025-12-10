<template><div></div></template>

<script>
export default {
  name: 'Auth',

  data () {
    return {
      token: null
    }
  },

  mounted () {
    this.init()
  },

  methods: {
    init () {
      this.token = this.$route.query.token
      this.auth()
    },

    async auth () {
      let resp = await this.$http.post('/wechat_auth', {
        token: this.token
      })
      resp = resp.data
      window.localStorage.removeItem('vuex')
      let from_ = window.localStorage.getItem('wechat_from')
      if (from_) {
        window.localStorage.removeItem('wechat_from')
        window.location.href = from_
      } else {
        window.location.href = `/${resp.redirect_url}`
      }
    }
  }
}
</script>
