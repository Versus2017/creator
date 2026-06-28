import moment from 'moment'

let filters = {}

export default filters

let formatMoney = (value) => {
  if (value === null) {
    return 'N/A'
  }
  if (isNaN(value * 1)) {
    return ''
  }
  let negativeFlag = value < 0 ? '-' : ''
  value = Math.abs(value)
  if (value === Math.round(value)) {
    value = value.toFixed(0)
  } else {
    value = value.toFixed(2)
  }
  value = parseFloat(value)
  return `${negativeFlag}￥${value.toLocaleString('en-US')}`
}

let formatEmpty = (value) => {
  return value || '-'
}

let formatDatetimeUTC = (value, fmt = 'YYYY-MM-DD HH:mm:ss') => {
  return formatDatetime(value, fmt, 'utc', 'local')
}

let formatDatetime = (value, fmt = 'YYYY-MM-DD HH:mm:ss', from = 'local', to = 'utc') => {
  if (!value) {
    return ''
  }
  if (!fmt) {
    fmt = 'YYYY-MM-DD HH:mm:ss'
  }
  let dt = moment(value)
  if (from !== to) {
    if (from === 'utc') {
      dt = moment(moment.utc(value).toDate()).local()
    }
    if (to === 'utc') {
      dt = moment.utc(value)
    }
  }
  return dt.format(fmt)
}

let formatClientInfo = (info = []) => {
  return info.filter(item => !!item).join(', ')
}

let formatNull = (value) => {
  if (value === null || value === undefined || value === '') {
    return '-'
  } else {
    return value
  }
}

export {
  formatDatetime,
  formatDatetimeUTC,
  formatMoney,
  formatClientInfo,
  formatEmpty,
  formatNull,
}
