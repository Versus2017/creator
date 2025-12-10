import Vue from 'vue'
import Vuex from 'vuex'
import { get } from 'lodash'
import { api } from './libs/api'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    loading: false,
    auth: {
      user: {}
    }
  },
  mutations: {
    setLoading (state, value) {
      state.loading = value
    },

    setUser (state, user) {
      state.auth.user = Object.assign({}, user || {})
    }
  },

  getters: {
    user: state => {
      return state.auth.user
    },

    boundBoUser: state => {
      return get(state, 'auth.user.bo_user')
    }
  },

  actions: {
    async getUser (context) {
      let resp = await api.get('/users/me')
      context.commit('setUser', resp.data.user)
    }
  }
})
