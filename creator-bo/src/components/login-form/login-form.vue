<template>
  <div>
    <div class="form-con" key="login-form" v-if="!isTwoFA"
         @keydown.enter="handleSubmit">
      <Form ref="loginForm" :model="form" :rules="rules">
        <FormItem prop="username">
          <Input v-model="form.username" placeholder="请输入用户名">
            <span slot="prepend">
              <Icon :size="16" type="ios-person"></Icon>
            </span>
          </Input>
        </FormItem>
        <FormItem prop="password">
          <Input type="password" v-model="form.password" placeholder="请输入密码">
            <span slot="prepend">
              <Icon :size="14" type="md-lock"></Icon>
            </span>
          </Input>
        </FormItem>
        <FormItem>
          <Button @click="handleSubmit" type="primary" long>登录</Button>
        </FormItem>
      </Form>
    </div>
    <div class="form-con" key="verify-form" v-else
         @keydown.enter="handleVerify">
      <Alert>我们已经向您的手机{{twoFAto}}发送了验证码短信，请查收</Alert>
      <Form ref="verifyForm" :model="verifyForm" :rules="verifyFormRules">
        <FormItem prop="code">
          <Input v-model="verifyForm.code" placeholder="请输入验证码">
            <span slot="prepend">
              <Icon :size="16" type="android-textsms"></Icon>
            </span>
          </Input>
        </FormItem>
        <FormItem>
          <Button @click="handleSubmit" type="success"
                  class="verify-btn verify-btn-resend"
                  :disabled="seconds !== 0">{{ seconds ? seconds + '秒' : '重发验证码' }}
          </Button>
          <Button @click="handleVerify" type="primary"
                  :loading="twoFAVerifying && !!twoFAto"
                  class="verify-btn">
            验证
          </Button>
        </FormItem>
      </Form>
    </div>
  </div>

</template>
<script>
export default {
  name: 'LoginForm',

  data () {
    return {
      form: {
        username: '',
        password: ''
      },
      verifyForm: {
        code: '',
      },
      verifyFormRules: {
        code: [
          {required: true, message: '验证码不能为空', trigger: 'blur'}
        ],
      },
      timer: null,
      seconds: 0,
    }
  },
  computed: {
    rules () {
      return {
        username: [
          {required: true, message: '账号不能为空', trigger: 'blur'},
        ],
        password: [
          {required: true, message: '密码不能为空', trigger: 'blur'},
        ],
      }
    },

    isTwoFA() {
      return this.$store.getters['user/isTwoFA']
    },

    twoFAto () {
      return this.$store.state.user.twoFA.to
    },

    twoFAVerifying () {
      return this.$store.getters['user/twoFAVerifying']
    },
  },
  methods: {
    setTimer () {
      if (this.timer) {
        clearTimeout(this.timer)
      }
      this.timer = setTimeout(() => {
        if (this.seconds > 0) {
          this.seconds = this.seconds - 1
          this.setTimer()
        } else {
          this.timer = null
        }
      }, 1000)
    },

    handleSubmit (e) {
      e.preventDefault()
      this.$store.commit('user/setTwoFAVerifying', false)
      this.$refs.loginForm.validate((valid) => {
        if (!valid) {
          return
        }
        this.$store.dispatch('user/login', {vue: this, loginData: this.form})
        this.seconds = 60
        this.setTimer()
      })
    },

    handleVerify (e) {
      e.preventDefault()
      this.$refs.verifyForm.validate((valid) => {
        if (valid) {
          this.$store.commit('user/setTwoFAVerifying', true)
          this.$store.dispatch('user/verify', {
            vue: this,
            verifyData: this.verifyForm
          })
        }
      })
    },
  },

  beforeDestroy () {
    this.$store.commit('user/setTwoFA')
  }
}
</script>

<style lang="less" scoped>
  @import '../../styles/common.less';

  .verify-btn {
    width: 49%;
    float: right;
    &.verify-btn-resend {
      float: left;
    }
  }
</style>
