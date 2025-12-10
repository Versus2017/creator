import Vue from 'vue'
import VueAxios from 'vue-axios'
import App from './App.vue'
import { router } from './router/index'
import store from './store'
import { api } from './libs/api'
import VueRouter from 'vue-router'
import iView from 'iview'
import VueAuth from '@websanova/vue-auth'
import http from '@websanova/vue-auth/drivers/http/axios.1.x.js'
import './styles/theme.less'
import 'iview/dist/styles/iview.css'
import './index.less'
import config from '@/config'
import '@/assets/icons/iconfont.css'
import { getCookie } from './libs/util'
import i18n from '@/locale'

Vue.use(iView, {
  i18n: (key, value) => i18n.t(key, value)
})

Vue.config.productionTip = false
Vue.prototype.$config = config

Vue.use(VueAxios, api)
Vue.use(VueRouter)
Vue.router = router

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
  loginData: { url: '/web/login', fetchUser: false},
  logoutData: { url: '/web/logout', methods: 'POST', makeRequest: true },
  refreshData: { enabled: false },
  fetchData: { url: '/web/users/me', enabled: true },
  parseUserData: (data) => data.user,
  tokenDefaultName: 'creator_auth',
  tokenStore: ['cookie'],
})


new Vue({
  router,
  i18n,
  store,
  render: h => h(App)
}).$mount('#app')
