import Main from '@/views/main'

/**
 * iview-admin中meta除了原生参数外可配置的参数:
 * meta: {
 *  hideInMenu: (false) 设为true后在左侧菜单不会显示该页面选项
 *  notCache: (false) 设为true后页面不会缓存
 *  access: (null) 可访问该页面的权限数组，当前路由设置的权限会影响子路由
 *  icon: (-) 该页面在左侧菜单、面包屑和标签导航处显示的图标，如果是自定义图标，需要在图标名称前加下划线'_'
 * }
 */

export default [
  {
    path: '/login',
    name: 'login',
    meta: {
      title: 'Login - 登录',
      hideInMenu: true
    },
    component: () => import('@/views/login.vue')
  },
  {
    path: '/',
    name: '_home',
    redirect: '/home',
    component: Main,
    meta: {
      hideInMenu: true,
      hide: true,
      notCache: true,
      auth: true,
    },
    children: [
      {
        path: '/home',
        name: 'home',
        meta: {
          title: '首页',
          hide: true,
        },
        component: () => import('@/views/home.vue')
      },
      {
        path: '/creativity',
        name: 'creativity',
        meta: {
          title: '创意',
          hide: true,
        },
        component: () => import('@/views/creativity.vue')
      },
      {
        path: '/scripts',
        name: 'scripts',
        meta: {
          title: '脚本管理',
          hide: true,
        },
        component: () => import('@/views/scripts.vue')
      },
      {
        path: '/scripts/:id',
        name: 'script-detail',
        meta: {
          title: '脚本详情',
          hide: true,
        },
        component: () => import('@/views/script-detail.vue')
      },
      {
        path: '/profile',
        name: 'profile',
        meta: {
          title: '个人中心',
          hide: true,
        },
        component: () => import('@/views/profile.vue')
      },
      {
        path: '/research/chat',
        name: 'research-chat',
        meta: {
          title: '脚本研究',
          hide: true,
        },
        component: () => import('@/views/research-chat.vue')
      },
      {
        path: '/research/list',
        name: 'research-list',
        meta: {
          title: '研究记录',
          hide: true,
        },
        component: () => import('@/views/research-list.vue')
      },
    ]
  }
]
