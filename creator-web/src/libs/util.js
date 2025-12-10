import { forEach, hasOneOf } from '@/libs/tools'
import { BO_NAME } from './constants'

export const hasChild = (item) => {
  return item.children && item.children.length !== 0
}

const showThisMenuEle = (item, permissions) => {
  let perms = permissions || []
  if (item.meta && item.meta.requiredPerms && item.meta.requiredPerms.length) {
    if (hasOneOf(item.meta.requiredPerms, perms)) return true
    else return false
  } else return true
}
/**
 * @param {Array} list 通过路由列表得到菜单列表
 * @returns {Array}
 */
export const getMenuByRouter = (list, permissions) => {
  let res = []
  forEach(list, item => {
    if (!item.meta || (item.meta && !item.meta.hideInMenu)) {
      let obj = {
        icon: (item.meta && item.meta.icon) || '',
        name: item.name,
        meta: item.meta
      }
      if (item.meta && item.meta.href) obj.href = item.meta.href
      if (hasChild(item)) {
        obj.children = getMenuByRouter(item.children, permissions)
        if (obj.children && obj.children.length > 0) {
          res.push(obj)
        }
      } else if (showThisMenuEle(item, permissions)) {
        res.push(obj)
      }
    }
  })
  return res
}

/**
 * @param {Array} routeMetched 当前路由metched
 * @returns {Array}
 */
export const getBreadCrumbList = (routeMetched, homeRoute) => {
  let res = routeMetched.filter(item => {
    return item.meta === undefined || !item.meta.hide
  }).map(item => {
    let obj = {
      icon: (item.meta && item.meta.icon) || '',
      name: item.name,
      meta: item.meta
    }
    return obj
  })
  return [...res]
}

export const showTitle = (item, vm) => vm.$config.useI18n ? vm.$t(item.name) : ((item.meta && item.meta.title) || item.name)


/**
 * @param {Array} routers 路由列表数组
 * @description 用于找到路由列表中name为home的对象
 */
export const getHomeRoute = routers => {
  let i = -1
  let len = routers.length
  let homeRoute = {}
  while (++i < len) {
    let item = routers[i]
    if (item.children && item.children.length) {
      let res = getHomeRoute(item.children)
      if (res.name) return res
    } else {
      if (item.name === 'home') homeRoute = item
    }
  }
  return homeRoute
}

/**
 * @param {String} url
 * @description 从URL中解析参数
 */

export const getParams = (url) => {
  let params
  if (url.indexOf('?') > -1) {
    let paramStr = url.split('?')[1]
    if (paramStr.indexOf('&')) {
      paramStr.split('&').forEach(item => {
        let parts = item.split('=')
        let values = {}
        values[parts[0]] = parts[1]
        params = Object.assign({}, values, params)
      })
    } else {
      let parts = paramStr.split('=')
      let values = {}
      values[parts[0]] = parts[1]
      params = Object.assign({}, values, params)
    }
  }
  return params
}
export const getCookie = (name) => {
  return decodeURIComponent(document.cookie.replace(new RegExp('(?:(?:^|.*;)\\s*' + encodeURIComponent(name).replace(/[\-\.\+\*]/g, '\\$&') + '\\s*\\=\\s*([^;]*).*$)|^.*$'), '$1')) || null
}

export const getCSRFToken = () => {
  return getCookie('creator_auth_csrf_cookie')
}

export const setTitle = (title) => {
  if (title) {
    window.document.title = `${title} - ${BO_NAME}`
  } else {
    window.document.title = BO_NAME
  }
}

export const getFilterValue = (values) => {
  return values && values.length > 0 ? values[0] : null
}

export const isValidMobile = (mobile) => {
  return /^1[3|4|5|6|7|8|9][0-9]{9}$/.test(mobile)
}

const huaweiObs = 'orangefuture-bj1.obs.cn-north-1.myhuaweicloud.com'
export const onDownloadImage = (url) => {
  if (url.indexOf('obs.orangefuture.cn') > -1) {
    url = url.replace('obs.orangefuture.cn', huaweiObs)
  }
  const xhr = new XMLHttpRequest();
  xhr.open('GET', url, true);
  xhr.responseType = 'blob';
  xhr.onload = function() {
    if (this.status === 200) {
      const blob = this.response;
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = url.split('/').pop();
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };
  xhr.send();
}



export const sendMessageToMobile = (methodName, params, jsAction = null) => {
  let newParams = Object.assign({}, params, { jsAction: jsAction })
  if (window.system.ios && window.webkit) {
    window.webkit.messageHandlers[methodName].postMessage(newParams)
  }
  if (window.system.android && window.android) {
    window.android[methodName](JSON.stringify(newParams))
  }
}

//获取32位uuid方法
export function getUuid() {
  return ('xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, //随机生成 0 - 15的数字
        v = c == 'x' ? r : (r & 0x3 | 0x8); //c为y时只取8、9、a、b中的一个
    return v.toString(16); //把数字转成16进制的字符串
  }));
}