<template>
  <div class="container">
    <h1>微信工作台</h1>
    <mt-button @click.native="handleClick">显示首页</mt-button>
    <img v-if="qrImg" class="qr-img" :src="qrImg"/>
  </div>
</template>

<script>
export default {
  name: 'BoWorkbench',

  data () {
    return {
      qrImg: null
    }
  },

  mounted () {
    this.loadQRImage()
  },

  methods: {
    handleClick () {
      this.$router.push('/')
    },

    async loadQRImage () {
      let resp = await this.$http.get('/users/me/qr_code')
      resp = resp.data
      this.qrImg = resp.qr_img

    }
  }
}
</script>

<style scoped lang="less">
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.qr-img {
  width: 200px;
}
</style>
