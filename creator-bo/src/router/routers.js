import Main from '@/view/main'

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
    component: () => import('@/view/login/login.vue')
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
          hideInMenu: true,
          title: '首页',
          hide: true,
          notCache: true
        },
        component: () => import('@/view/single-page/home')
      }
    ]
  },
  {
    path: '/user',
    name: 'user',
    meta: {
      icon: 'md-lock',
      title: '账号管理'
    },
    component: Main,
    children: [
      {
        path: 'roles',
        name: 'roles',
        meta: {
          icon: 'ios-ribbon',
          title: '角色管理',
          requiredPerms: ['bo_roles_view', 'bo_roles_manage']
        },
        component: () => import('@/view/users/role-list.vue')
      },
      {
        path: 'roles/create',
        name: 'role_creator',
        meta: {
          icon: 'ios-create',
          title: '创建角色',
          hideInMenu: true,
          requiredPerms: ['bo_roles_manage']
        },
        component: () => import('@/view/users/role-editor.vue')
      },
      {
        path: 'roles/:roleId/edit',
        name: 'role_editor',
        meta: {
          icon: 'ios-create',
          title: '编辑角色',
          hideInMenu: true,
          requiredPerms: ['bo_roles_manage']
        },
        component: () => import('@/view/users/role-editor.vue')
      },
      {
        path: 'bo_users',
        name: 'bo_users',
        meta: {
          icon: 'ios-people',
          title: '用户管理',
          requiredPerms: ['bo_users_view']
        },
        component: () => import('@/view/users/bo-user-list.vue')
      }
    ]
  },
  {
    path: '/system',
    name: 'system',
    meta: {
      icon: 'ios-construct',
      title: '系统设置'
    },
    component: Main,
    children: [
      {
        path: 'settings',
        name: 'settings',
        meta: {
          icon: 'md-settings',
          title: '配置',
          requiredPerms: ['live_settings_manage']
        },
        component: () => import('@/view/system/Config.vue')
      },
    ]
  },
  {
    path: '/401',
    name: 'error_401',
    meta: {
      hideInMenu: true
    },
    component: () => import('@/view/error-page/401.vue')
  },
  {
    path: '/403',
    name: 'error_403',
    meta: {
      hideInMenu: true
    },
    component: () => import('@/view/error-page/403.vue')
  },
  {
    path: '/500',
    name: 'error_500',
    meta: {
      hideInMenu: true
    },
    component: () => import('@/view/error-page/500.vue')
  },
  {
    path: '*',
    name: 'error_404',
    meta: {
      hideInMenu: true
    },
    component: () => import('@/view/error-page/404.vue')
  }
]
