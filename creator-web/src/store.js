import Vue from 'vue'
import Vuex from 'vuex'
import {get} from 'lodash'
import routers from '@/router/routers'
import {getBreadCrumbList, getMenuByRouter, getHomeRoute} from '@/libs/util'
import {api} from './libs/api'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    breadCrumbList: [],
    homeRoute: getHomeRoute(routers),
    loading: false,
    fixtures: {},
    user: {}
  },
  mutations: {
    setBreadCrumb (state, routeMetched) {
      state.breadCrumbList = getBreadCrumbList(routeMetched, state.homeRoute)
    },

    setLoading (state, value) {
      state.loading = value
    },

    setUser (state, user) {
      if (!user) {
        user = {}
      }
      state.user = Object.assign({}, user)
    },

    setFixtures (state, fixtures) {
      state.fixtures = fixtures
    }
  },

  getters: {
    user: state => state.user,
    fixtures: state => state.fixtures,
    authorized: state => !!state.user.id,
  },

  actions: {
    getFixtures ({ commit }) {
      return api.get('/admin/fixtures').then(resp => {
        commit('setFixtures', resp.fixtures)
      })
    },

    authSuccess ({ commit }, { $auth }) {
      commit('setUser', $auth.user())
    },

    login ({ commit, dispatch }, { vue, loginData }) {
      // let redirect = vue.$auth.redirect()
      return vue.$auth.login({
        data: loginData,
        rememberMe: true,
        redirect: null,
        fetchUser: false, // we'll manually fetch if this is not 2FA login
        success (res) {
          vue.$auth.fetch({
            success: async () => {
              await dispatch('refreshUser', vue)
              // await dispatch('getConfigs', vue)
              vue.$router.replace({ name: 'home' })
            }
          })
        }
      })
    },


    logout ({ commit }, { vue, makeRequest = true }) {
      commit('setUser')
      vue.$auth.logout({
        makeRequest: makeRequest,
        redirect: { name: 'login' }
      })
    },

    async refreshUser ({ commit }) {
      let resp = await api.get('/web/users/me')
      commit('setUser', resp.user)
    }
  }
})
