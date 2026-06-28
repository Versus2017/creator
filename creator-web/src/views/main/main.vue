<template>
  <Layout style="height: 100%" class="main">
    <Layout>
      <Header class="header-con">
        <header-bar :collapsed="collapsed" @on-coll-change="handleCollapsedChange">
          <user />
<!--          <fullscreen v-model="isFullscreen" style="margin-right: 10px;"/>-->
        </header-bar>
      </Header>
      <Content class="main-content-con">
        <Layout class="main-layout-con">
          <Content class="content-wrapper">
            <div class="page-content">
              <router-view :key="$route.fullPath"/>
            </div>
          </Content>
        </Layout>
      </Content>
    </Layout>
  </Layout>
</template>
<script>
import HeaderBar from './components/header-bar'
import User from './components/user'
import Fullscreen from './components/fullscreen'
import Language from './components/language'
import { mapMutations } from 'vuex'
import minLogo from '@/assets/images/logo-min.png'
import maxLogo from '@/assets/images/logo.png'
import './main.less'
export default {
  name: 'Main',
  components: {
    HeaderBar,
    Language,
    Fullscreen,
    User
  },
  data () {
    return {
      collapsed: false,
      minLogo,
      maxLogo,
      isFullscreen: false
    }
  },
  computed: {
    menuList () {
      return this.$store.getters.menuList
    },
    local () {
      return this.$store.state.app.local
    }
  },
  methods: {
    ...mapMutations([
      'setBreadCrumb',
    ]),

    turnToPage (name) {
      if (name.indexOf('isTurnByHref_') > -1) {
        window.open(name.split('_')[1])
        return
      }
      this.$router.push({
        name: name
      })
    },
    handleCollapsedChange (state) {
      this.collapsed = state
    }
  },
  watch: {
    '$route' (newRoute) {
      this.setBreadCrumb(newRoute.matched)
    }
  },
  mounted () {
    /**
     * @description 初始化设置面包屑导航
     */
    this.setBreadCrumb(this.$route.matched)
  }
}
</script>

<style lang="less" scoped>
  .header-con {
    padding: 0;
    height: 64px;  // 固定header高度

    /deep/ .header-bar {
      height: 100%;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);  // 添加subtle阴影
      padding: 0;
    }
  }

  .content-wrapper {
    height: ~"calc(100vh - 64px)";  // 减去header高度
    overflow-y: auto;
    
    .page-content {
      width: 100%;
      height: 100%;
    }
  }
</style>
