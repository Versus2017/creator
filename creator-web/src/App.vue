<template>
  <div v-if="$auth.ready()" id="app" class="app">
    <router-view/>
  </div>
  <div v-else class="app">载入中...</div>
</template>

<script>
export default {
  data () {
    return {
      landscape: false
    }
  },

  beforeCreate () {
    this.$store.dispatch('getFixtures', {vue: this})
  },

  async created () {
    this.$auth.ready(function () {
      console.log(this.$auth.check(), 'check')
      console.log(this.$auth.user(), 'user')
      if (this.$auth.check()) {
        this.$store.dispatch('refreshUser', this)
      }
    })
  },

  mounted () {

  },

  beforeDestroy () {

  },

  computed: {

  },

  methods: {

  }
}
</script>

<style lang="less" scoped>
  .app {
    background-color: #eaeaea;
    width: 100vw;
    height: 100vh;
    //-ms-overflow-style: -ms-autohiding-scrollbar;
  }
</style>

<style lang="less">
  .size {
    width: 100vw;
    height: 100vh;
  }

  html, body {
    .size;
    overflow: hidden;
    margin: 0;
    padding: 0;
  }

  #app {
    .size;
  }

  ::-webkit-input-placeholder { /* WebKit browsers */
    color: rgba(0, 0, 0, 0.5);
    font-size: 14px;
  }

  :-moz-placeholder { /* Mozilla Firefox 4 to 18 */
    color: rgba(0, 0, 0, 0.5);
    font-size: 14px;
  }

  ::-moz-placeholder { /* Mozilla Firefox 19+ */
    color: rgba(0, 0, 0, 0.5);
    font-size: 14px;
  }

  :-ms-input-placeholder { /* Internet Explorer 10+ */
    color: rgba(0, 0, 0, 0.5);
    font-size: 14px;
  }

  ::placeholder { /* Modern browsers */
    color: rgba(0, 0, 0, 0.5);
    font-size: 14px;
  }

  /*::-webkit-scrollbar {*/
  /*  width: 5px;*/
  /*}*/

  /*::-webkit-scrollbar-track {*/
  /*  background-color: #D9D9D9;*/
  /*  !* 滚动条轨道背景颜色 /*/
  /*   border-radius: 5px; / 滚动条轨道圆角 *!*/
  /*}*/

  /*::-webkit-scrollbar-thumb {*/
  /*  width: 1px;*/
  /*  background-color: #333333;*/
  /*  !* 滚动条滑块背景颜色 /*/
  /*   border-radius: 5px; / 滚动条滑块圆角 *!*/
  /*}*/

  //.ivu-input-wrapper .ive-input-inner-container .ivu-input {
  //  color: red !important;
  //}
</style>
