import axios from 'axios'
import iView from 'iview'
import { get } from 'lodash'
import router from '../router'
import { getCSRFToken } from './util'

export const api = axios.create({
  baseURL: '/v1',
  timeout: 300000,
  // 确保携带cookie认证信息
  withCredentials: true
})

api.interceptors.request.use(config => {
  config.headers.source = 'web'
  const csrfToken = getCSRFToken()
  if (csrfToken) {
    config.headers['X-CSRF-TOKEN'] = csrfToken
  }
  config.params = Object.assign(config.params || {}, { nonce: Date.now() })
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
  const data = response.data
  if (data && data.success === false) {
    if (!response.config.hideProgress) {
      iView.LoadingBar.error()
    }
    if (!response.config.hideError) {
      const errMsg = data.message || '请求失败'
      iView.Message.error({
        content: errMsg,
        duration: 2.5
      })
    }
    return Promise.reject({
      response: {
        config: response.config,
        status: data.code || response.status,
        data
      }
    })
  }
  return data
}, (error) => {
  let config = get(error, 'response.config')
  let status = get(error, 'response.status')
  if (!config.hideError) {
    iView.LoadingBar.error()
    console.log(error.response.data, '------- error')
    let errMsg = get(error, 'response.data.message', '请求失败')
    if (status === 422) {
        let formErrors = get(error, 'response.data.detail', '请求失败')
        if (formErrors && formErrors.length > 0) {
            errMsg = formErrors.map(item => {
              return item.msg
            }).join('\n')
        }
    }
    iView.Message.error({
      content: errMsg,
      duration: 2.5
    })
  }

  if (status === 401) {
    router.replace('/login')
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
    router.replace('/login')
    // TODO: refresh user
  }
  return Promise.reject(error)
})

// 提示词相关API
export const promptApi = {
  // 获取AI模型列表
  getAiModels() {
    return this.$http.get('/web/ai_models')
  },
  
  // 生成提示词
  generatePrompt(data) {
    return this.$http.post('/web/prompts/generate', data)
  },
  
  // 基于已有提示词创建新的生成步骤
  createPromptStep(data) {
    return this.$http.post('/web/prompt_steps', data)
  },
  
  // 获取用户提示词列表
  getPrompts(params) {
    return this.$http.get('/web/prompts', { params })
  },
  
  // 获取提示词详情
  getPromptDetail(promptId) {
    return this.$http.get(`/web/prompts/${promptId}`)
  },
  
  // 更新提示词
  updatePrompt(promptId, data) {
    return this.$http.put(`/web/prompts/${promptId}`, data)
  },
  
  // 删除提示词
  deletePrompt(promptId) {
    return this.$http.delete(`/web/prompts/${promptId}`)
  }
}
