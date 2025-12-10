import { get } from 'lodash'


export const FormErrorMixin = {

  data () {
    return {
      serverErrors: {},
    }
  },

  methods: {
    setFormErrors (error) {
      let errorInfo = get(error, 'response.data.error.errors')
      if (errorInfo) {
        Object.keys(errorInfo).forEach(key => {
          errorInfo[key] = errorInfo[key].join('，')
        })
        this.serverErrors = Object.assign(this.serverErrors, errorInfo)
      }
    },

    clearErrors () {
      if (this.serverErrors) {
        Object.keys(this.serverErrors).forEach(key => {
          this.serverErrors[key] = null
        })
      }
    }
  }
}