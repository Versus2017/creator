import VueRouter from 'vue-router'
import iView from 'iview'
import { get } from 'lodash'
import routes from './routers'
import store from '../store'
import { setTitle } from '../libs/util'

export const router = new VueRouter({
  routes,
  // mode: 'history'
})

const LOGIN_PAGE_NAME = 'login'

router.beforeEach((to, from, next) => {
  iView.LoadingBar.start();
  if (store.getters['user/authorized'] && to.path !== '/') {
    // auth is actually checked by vue-auth
    // here we only care about permissions
    const requiredPerm = get(to, 'meta.requiredPerms')
    let ok = false
    if (requiredPerm) {
      // a route can explicitly state what permission it requires
      ok = requiredPerm.filter(p => store.getters['user/hasPermission'](p) === true).length > 0
    } else {
      // if it doesn't, there is no limit to this path
      ok = true
    }
    if (!ok) {
      next({name: 'error_403'})
    }
  }
  setTitle(to.meta.title)
  if (to.name !== LOGIN_PAGE_NAME && !to.query.nonce) {
    let nonce = (new Date).getTime()
    let query = Object.assign({nonce: nonce}, to.query)

    // See https://github.com/vuejs/vue-router/pull/1906
    // 目前在 beforeEach 中无法知晓路由变化是由 push 还是 replace 引发的，这里会
    // 导致 replace 失效，如果需要可以暂时在这里 hack 一下，等到 vue-router 问题
    // 修复之后，这里可以直接根据调用的是 push 还是 replace 来设置 next 的 replace
    // 参数
    let replace = false
    next({ path: to.path, query: query, replace: replace })
  } else {
    next()
  }
})

router.afterEach(() => {
  iView.LoadingBar.finish()
  window.scrollTo(0, 0)
})

export default router

