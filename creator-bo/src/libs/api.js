import axios from 'axios'
import iView from 'iview'
import { get } from 'lodash'
import router from '../router'
import store from '../store'

export const api = axios.create({
  baseURL: '/v1',
  timeout: 30000,
})

api.interceptors.request.use(config => {
  config.headers.source = 'bo'
  config.params = Object.assign(config.params || {}, {nonce: Date.now()})
  if (!config.hideProgress) {
    iView.LoadingBar.start()
  }
  return config
}, (error) => {
  iView.LoadingBar.error()
  return Promise.reject(error)
})

api.interceptors.response.use(response => {
  if (!response.config.hideProgress) {
    iView.LoadingBar.finish()
  }
  return response.data
}, (error) => {
  iView.LoadingBar.error()
  let errMsg = get(error, 'response.data.error.message', '请求失败')
  iView.Message.error({
    content: errMsg,
    duration: 2.5,
  })

  let status = get(error, 'response.status')
  if (status === 401) {
    store.dispatch('user/logout', {vue: router.app, makeRequest: true})
  }

  // normally if a user don't have permission to a page, he won't even be able
  // to see the page, as a result he won't hit any API which he has no access to
  //
  // if a user paste the url of a forbidden page when the vue app is already
  // fully loaded, vue knows he has no permission so redirects him to 403 page
  // directly
  //
  // in case a user paste the url of a forbidden page in a **new tab**
  // and vue-auth hasn't got back user permission info yet,
  // he can actually go to the page and fire some API calls
  // The calls would return 403s and we redirect him to 403.vue
  if (status === 403 && (!router.currentRoute || router.currentRoute.name !== 'error_403')) {
    router.push({name: 'error_403'})
    // TODO: refresh user
  }
  return Promise.reject(error)
})
