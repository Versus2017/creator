<template>
  <div class="home">
    <h1>首页</h1>
    <mt-button v-if="boundBoUser" @click.native="handleClick">显示工作台</mt-button>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'Home',

  computed: {
    ...mapGetters(['boundBoUser'])
  },

  methods: {
    handleClick () {
      this.$router.push('/workbench')
    }
  }
}
</script>
