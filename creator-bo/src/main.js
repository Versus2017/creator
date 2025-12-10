// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import VueRouter from 'vue-router'
import App from './app'
import { router } from './router/index'
import store from './store'
import iView from 'iview'
import VueAxios from 'vue-axios'
import VueAuth from '@websanova/vue-auth'
import http from '@websanova/vue-auth/drivers/http/axios.1.x.js'
import i18n from '@/locale'
import VueQrcode from '@xkeshi/vue-qrcode'
import config from '@/config'
import 'iview/dist/styles/iview.css'
import './index.less'
import '@/assets/icons/iconfont.css'
import { api } from './libs/api'
import * as filters from './libs/filters'
import { getCookie } from './libs/util'
import './styles/theme.less'
/* eslint-disable */

Vue.use(iView, {
  i18n: (key, value) => i18n.t(key, value)
})
Vue.component(VueQrcode.name, VueQrcode)
Vue.config.productionTip = false
/**
 * @description 全局注册应用配置
 */
Vue.prototype.$config = config
/**
 * 注册指令
 */

Vue.use(VueAxios, api)
Vue.use(VueRouter)
Vue.router = router

// we already have a http response intercepter which makes axios to return
// resp.data;
// res passed to vue-auth.http._httpData is already res.data
http._httpData = (res) => res

// auth
Vue.use(VueAuth, {
  auth: {
    request: function (req, token) {
      this.options.http._setHeaders.call(this, req, {'X-CSRF-TOKEN': getCookie('creator_auth_csrf_cookie')})
    },
    response: function (res) {
      return true
    }
  },
  http: http,
  router: require('@websanova/vue-auth/drivers/router/vue-router.2.x.js'),
  loginData: { url: '/admin/login', fetchUser: false},
  logoutData: { url: '/admin/logout', methods: 'POST', makeRequest: true },
  refreshData: { enabled: false },
  fetchData: { url: '/admin/users/me', enabled: true },
  parseUserData: (data) => data.user,
  tokenDefaultName: 'creator_auth',
  tokenStore: ['cookie'],
})

// filters
Object.keys(filters).forEach(key => {
  Vue.filter(key, filters[key])
})

Vue.mixin({
  methods: {
    hasPermission (perm) {
      return store.getters['user/hasPermission'](perm)
    },
    hasAnyPermission (perms) {
      return perms.filter(
        p => store.getters['user/hasPermission'](p) === true).length > 0
    }
  }
})

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  i18n,
  store,
  render: h => h(App)
})
