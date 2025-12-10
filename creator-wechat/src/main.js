import Vue from 'vue'
import VueAxios from 'vue-axios'
import Mint from 'mint-ui'
import App from './App.vue'
import router from './router'
import store from './store'
import { api } from './libs/api'
import WechatPlugin from './plugin/wechat'

import 'mint-ui/lib/style.css'

Vue.config.productionTip = false
Vue.use(Mint)
Vue.use(VueAxios, api)
Vue.use(require('vue-wechat-title'))
Vue.use(WechatPlugin)

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
