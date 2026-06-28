import { getBreadCrumbList, getMenuByRouter, getHomeRoute } from '@/libs/util'
import routers from '@/router/routers'
import {startsWith } from 'lodash'

export default {
  state: {
    breadCrumbList: [],
    homeRoute: getHomeRoute(routers),
    local: '',
    configs: {},
    listQuery: {
      // 列表页的过滤、搜索、排序参数
      // pageKey: {}
    }
  },
  getters: {
    menuList: (state, getters, rootState) => getMenuByRouter(routers, rootState.user.user.permissions),
    listQuery: state => pageKey => {
      // filter/search/sort parameters of a table page
      return state.listQuery[pageKey]
    }
  },
  actions: {
    async fetchConfig ({commit}, {vue}) {
      let resp  = await vue.$http.get('/admin/configs')
      commit('setConfigs', resp.configs)
    }
  },
  mutations: {
    setBreadCrumb (state, routeMetched) {
      state.breadCrumbList = getBreadCrumbList(routeMetched, state.homeRoute)
    },

    setConfigs ( state, configs ) {
      state.configs = configs
    },

    clearPageQueryCache (state, page) {
      Object.keys(state.listQuery).forEach(key => {
        if (startsWith(key, page)) {
          delete state.listQuery[key]
        }
      })
    },

    setListQuery(state, {pageKey, params}) {
      state.listQuery[pageKey] = params
    }
  }
}
