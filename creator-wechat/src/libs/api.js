import axios from 'axios'
import { Indicator } from 'mint-ui'
import Cookies from 'js-cookie'
import store from '../store'

export const api = axios.create({
  baseURL: '/v1'
})

const getCookie = (name) => {
  return Cookies.get(name) || null
}

api.interceptors.request.use(config => {
  config.params = Object.assign(config.params || {}, {nonce: Date.now()})
  let csrfCookie = getCookie('creator_auth_csrf_cookie')
  if (csrfCookie) {
    config.headers = {
      'X-CSRF-TOKEN': csrfCookie
    }
  }
  store.commit('setLoading', true)
  Indicator.open({
    text: '加载中...',
    spinnerType: 'fading-circle'
  })
  return config
})
api.interceptors.response.use(response => {
  store.commit('setLoading', false)
  Indicator.close()
  if (!response.data.success) {
    return Promise.reject(new Error(response.data.error.message))
  }
  return response
}, error => {
  store.commit('setLoading', false)
  Indicator.close()
  if (error.response.status === 401) {
    if (error.response.data.redirect_url) {
      let from = window.localStorage.getItem('wechat_from')
      if (!from) {
        window.localStorage.setItem('wechat_from', window.location.href)
      }
      window.location.href = error.response.data.redirect_url
    }
  }
  try {
    return Promise.reject(error.response.data)
  } catch (e) {
    return Promise.reject(error)
  }
})
