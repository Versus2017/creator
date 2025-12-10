<template><div></div></template>

<script>
import { mapActions, mapGetters } from 'vuex'
import { MessageBox } from 'mint-ui'
import { get } from 'lodash'
export default {
  name: 'BindBoUser',

  data () {
    return {
    }
  },

  computed: {
    token () {
      return this.$route.query.token
    },

    boUserId () {
      return this.$route.query.id
    },

    ...mapGetters(['user'])
  },

  async mounted () {
    if (!this.token) {
      MessageBox.alert('您扫的绑定二维码有误！').then(() => {
        this.$router.replace('/')
      })
      return
    }
    await this.getUser()
    if (this.user && this.user.bo_user) {
      MessageBox.alert('该微信账户已绑定过后台账户，不可重复绑定！').then(() => {
        this.$router.replace('/')
      })
      return
    }

    try {
      let resp = await this.$http.get(
        `/users/bo_user`,
        {params: {token: this.token, bo_users_id: this.boUserId}})
      let boUser = resp.data.bo_user
      MessageBox.confirm(
        `您确定您要绑定${boUser.nickname || boUser.username}吗？`,
        '绑定后台用户'
      ).then((action) => {
        if (action === 'confirm') {
          this.bind()
          return
        }
        this.$router.replace('/')
      })
    } catch (error) {
      this.handleError(error)
    }
  },

  methods: {
    handleError (error) {
      let errors = get(error, 'error.errors.token')
      let msg = errors ? errors.join(',') : '绑定失败，请检查二维码及网络是否正常'
      MessageBox.alert(msg).then(() => {
        this.$router.replace('/')
      })
    },

    async bind () {
      try {
        await this.$http.post('/users/bo_user', {token: this.token, bo_users_id: this.boUserId})
        this.getUser()
        MessageBox.alert('绑定成功').then(() => {
          this.$router.replace('/workbench')
        })
      } catch (error) {
        this.handleError(error)
      }
    },

    ...mapActions(['getUser'])
  }
}
</script>
