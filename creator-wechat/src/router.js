import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/home.vue'
import Auth from './views/auth'
import BindBoUser from './views/bind-bo-user'
import BoWorkbench from './views/bo-workbench'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'home',
      meta: {
        title: 'Wechat title',
        needAuth: true
      },
      component: Home
    },
    {
      path: '/wechat-auth',
      name: 'wechat-auth',
      meta: {
        title: 'Wechat title',
        needAuth: false
      },
      component: Auth
    },
    {
      path: '/bind-bo-user',
      name: 'bind-bo-user',
      meta: {
        title: 'Wechat title',
        needAuth: true
      },
      component: BindBoUser
    },
    {
      path: '/workbench',
      name: 'workbench',
      meta: {
        title: 'Wechat title',
        needAuth: true
      },
      component: BoWorkbench
    }
  ]
})
