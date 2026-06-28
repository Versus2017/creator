import { api } from '../../libs/api'
import { getCookie } from '../../libs/util'

const defaultUser = {permissions: []}

const user = {
  namespaced: true,
  state: {
    twoFA: {},
    twoFAVerifying: false,
    user: defaultUser,
  },
  getters: {
    isTwoFA: state => !!state.twoFA.to,
    twoFAVerifying: state => state.twoFAVerifying,
    authorized: state => !!state.user.username,
    username: state => state.user.username,
    nickname: state => state.user.nickname,
    role: state => state.user.role,
    hasPermission: state => perm => (
      // returns if a user has the exact permission
      state.user.permissions.includes(perm)
    ),
    hasAnyPermission: state => routeName => (
      // returns if a user can view a page
      state.user.permissions.includes(`${routeName}-view`) ||
      state.user.permissions.includes(`${routeName}-manage`)
    ),
    hasManagePermission: state => routeName => (
      // returns if a user can manage a page
      state.user.permissions.includes(`${routeName}-manage`)
    ),
  },
  actions: {
    login ({commit, dispatch}, {vue, loginData}) {
      let redirect = vue.$auth.redirect()
      return vue.$auth.login({
        data: loginData,
        rememberMe: true,
        redirect: null,
        fetchUser: false, // we'll manually fetch if this is not 2FA login
        success (res) {
          if (res['2fa_to']) {
            // current token is two FA token
            // it can only be used to access the verify code endpoint
            // we stay on this page to allow the user to input code
            commit('setTwoFA', {to: res['2fa_to']})
            // make vue-auth believe we have not logged-in yet
            dispatch('logout', {vue: vue, makeRequest: false})
          } else {
            vue.$auth.fetch({
              success: () => {
                dispatch('authSuccess', vue)
                vue.$router.push({name: redirect ? redirect.from.name : 'home'})
              },
            })
          }
        },
      })
    },

    verify ({ dispatch, commit }, { vue, verifyData }) {
      let redirect = vue.$auth.redirect()
      redirect = {name: redirect ? redirect.from.name : 'home'}
      return vue.$auth.login({
        url: '/admin/2fa/verify',
        data: verifyData,
        headers: {'X-CSRF-TOKEN': getCookie('creator_auth_csrf_cookie')},
        rememberMe: true,
        redirect: redirect,
        success () {
          vue.$auth.fetch({
            success: () => {
              dispatch('authSuccess', vue)
              // commit('setTwoFA') // clear previous 2fa state
            },
          })
        },
        error (e) {
          commit('setTwoFAVerifying', false)
          if (e.response && e.response.status === 401) {
            // 2FA token expired, the user must login again
            commit('setTwoFA')
          }
        },
      })
    },

    logout ({ commit }, { vue, makeRequest = true }) {
      commit('setUser')
      vue.$auth.logout({
        makeRequest: makeRequest,
        redirect: {name: 'login'},
      })
    },

    async refreshUser ({ commit }) {
      let resp = await api.get('/admin/users/me')
      commit('setUser', resp.user)
    },

    authSuccess ({ commit }, { $auth }) {
      commit('setUser', $auth.user())
    },
  },

  mutations: {
    setUser (state, user) {
      if (!user) {
        user = defaultUser
      }
      state.user = Object.assign({}, user)
    },

    setTwoFA (state, twoFA = {to: ''}) {
      state.twoFA = Object.assign({}, twoFA)
    },

    setTwoFAVerifying (state, verifying) {
      state.twoFAVerifying = verifying
    }
  },
}

export default user
