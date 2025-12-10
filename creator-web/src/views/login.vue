<template>
  <div class="login-container">
    <!-- 动态背景效果 -->
    <div class="bg-effects">
      <!-- 动态几何图形 -->
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
        <div class="shape shape-5"></div>
        <div class="shape shape-6"></div>
      </div>

      <!-- 光点效果 -->
      <div class="light-particles">
        <div class="particle particle-1"></div>
        <div class="particle particle-2"></div>
        <div class="particle particle-3"></div>
        <div class="particle particle-4"></div>
        <div class="particle particle-5"></div>
        <div class="particle particle-6"></div>
        <div class="particle particle-7"></div>
        <div class="particle particle-8"></div>
      </div>

      <!-- 网格线条 -->
      <div class="grid-lines">
        <div class="grid-line grid-line-1"></div>
        <div class="grid-line grid-line-2"></div>
        <div class="grid-line grid-line-3"></div>
      </div>
    </div>

    <div class="login-content">
      <!-- 左侧：品牌展示 -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="logo">
            <h1 class="brand-title">
              <svg class="logo-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-label="创思Logo">
                <defs>
                  <linearGradient id="login-logo-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#3B82F6;stop-opacity:1" />
                    <stop offset="50%" style="stop-color:#8B5CF6;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#06B6D4;stop-opacity:1" />
                  </linearGradient>
                </defs>
                <!-- 创意灯泡图标 -->
                <path d="M 50 20 Q 35 20 25 30 Q 15 40 15 55 Q 15 65 20 72 L 30 72 L 30 80 Q 30 85 35 85 L 65 85 Q 70 85 70 80 L 70 72 L 80 72 Q 85 65 85 55 Q 85 40 75 30 Q 65 20 50 20 Z M 40 75 L 60 75 L 60 72 L 40 72 Z" 
                      fill="url(#login-logo-gradient)" 
                      stroke="url(#login-logo-gradient)" 
                      stroke-width="2"/>
                <!-- 闪电图标（灵感） -->
                <path d="M 50 30 L 45 50 L 52 50 L 48 65 L 60 45 L 53 45 Z" 
                      fill="#FFFFFF" 
                      opacity="0.9"/>
              </svg>
              创思
            </h1>
          </div>
          <h2>✨ AI智能视频脚本创作平台</h2>
          <p>
            基于先进的AI大模型技术，为内容创作者提供专业的视频脚本创作服务。
            通过智能对话和个性化学习，助您高效创作优质脚本，让创意更自由
          </p>

          <div class="features">
            <div class="feature">
              <Icon type="ios-checkmark-circle" />
              <span>智能对话创作</span>
            </div>
            <div class="feature">
              <Icon type="ios-checkmark-circle" />
              <span>个性化风格学习</span>
            </div>
            <div class="feature">
              <Icon type="ios-checkmark-circle" />
              <span>规范化脚本输出</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：登录表单 -->
      <div class="form-section">
        <Card class="login-card">
          <div class="form-header">
            <h3>手机号登录</h3>
            <p>使用手机号和验证码登录创思平台</p>
          </div>

          <!-- 登录表单 -->
          <Form ref="loginForm" @submit.native.prevent="onLogin">
            <FormItem>
              <Input
                v-model="form.mobile"
                placeholder="请输入手机号"
                size="large"
                prefix="ios-phone-portrait"
                :maxlength="11"
              />
            </FormItem>

            <FormItem>
              <Input
                v-model="form.code"
                placeholder="请输入验证码"
                size="large"
                prefix="ios-lock"
                :maxlength="6"
              >
                <Button 
                  slot="append" 
                  :disabled="countdown > 0"
                  :loading="isSendingCode"
                  @click="sendCode"
                >
                  {{ countdown > 0 ? `${countdown}秒后重试` : '获取验证码' }}
                </Button>
              </Input>
            </FormItem>

            <FormItem>
              <Button
                type="primary"
                long
                size="large"
                :loading="isLoading"
                html-type="submit"
              >
                登录
              </Button>
            </FormItem>
          </Form>

          <div class="form-footer">
            <p class="tips">
              新用户首次登录将自动注册账号
            </p>
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'Login',

    data () {
      return {
        isLoading: false,
        isSendingCode: false,
        countdown: 0,
        countdownTimer: null,
        form: {
          mobile: '',
          code: ''
        }
      }
    },

    methods: {
      // 验证手机号格式
      validateMobile () {
        if (!this.form.mobile || this.form.mobile.trim().length === 0) {
          this.$Message.error('请输入手机号')
          return false
        }

        if (!/^1[3-9]\d{9}$/.test(this.form.mobile)) {
          this.$Message.error('请输入正确的手机号')
          return false
        }

        return true
      },

      // 发送验证码
      async sendCode () {
        if (!this.validateMobile()) {
          return
        }

        this.isSendingCode = true

        try {
          const response = await this.$http.post('/web/send_code', {
            mobile: this.form.mobile
          })

          if (response && response.success) {
            this.$Message.success('验证码已发送，请注意查收')
            
            // 开始倒计时
            this.countdown = 60
            this.countdownTimer = setInterval(() => {
              this.countdown--
              if (this.countdown <= 0) {
                clearInterval(this.countdownTimer)
                this.countdownTimer = null
              }
            }, 1000)
          }
        } catch (error) {
          console.error('发送验证码失败:', error)
          // 错误信息由 api.js 拦截器统一处理
        } finally {
          this.isSendingCode = false
        }
      },

      // 登录
      async onLogin () {
        // 验证手机号
        if (!this.validateMobile()) {
          return
        }

        // 验证验证码
        if (!this.form.code || this.form.code.trim().length === 0) {
          this.$Message.error('请输入验证码')
          return
        }

        if (!/^\d{6}$/.test(this.form.code)) {
          this.$Message.error('请输入6位数字验证码')
          return
        }

        this.isLoading = true

        try {
          await this.$store.dispatch('login', {
            vue: this,
            loginData: {
              mobile: this.form.mobile,
              code: this.form.code
            }
          })
          this.$Message.success('登录成功')
        } catch (error) {
          console.error('登录失败:', error)
          this.handleLoginError(error)
        } finally {
          this.isLoading = false
        }
      },

      // 处理登录错误
      handleLoginError (error) {
        let errorMessage = '登录失败，请重试'
        
        if (error.response && error.response.data) {
          const data = error.response.data
          errorMessage = data.detail || data.message || errorMessage
        }

        // 识别不同类型的错误
        if (errorMessage.includes('已被禁用')) {
          this.$Modal.error({
            title: '账号已被禁用',
            content: '该账号已被管理员禁用，无法登录系统。如有疑问，请联系管理员了解详情。',
            okText: '我知道了'
          })
        } else if (errorMessage.includes('验证码')) {
          // 验证码相关错误直接显示
          this.$Message.error(errorMessage)
        } else {
          // 其他错误
          this.$Message.error(errorMessage)
        }
      }
    },

    mounted () {
      // 如果已经登录，直接跳转
      if (this.$auth.check()) {
        const redirect = this.$route.query.redirect || '/'
        this.$router.push(redirect)
      }
    },

    beforeDestroy () {
      // 清理倒计时定时器
      if (this.countdownTimer) {
        clearInterval(this.countdownTimer)
        this.countdownTimer = null
      }
    }
  }
</script>

<style lang="less" scoped>
  // 导入设计系统变量
  @import '../styles/variables.less';

  .login-container {
    min-height: 100vh;
    background: linear-gradient(135deg, @bg-primary 0%, @bg-secondary 50%, @bg-tertiary 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1.25rem;
    position: relative;
    overflow: hidden;
  }

  // 背景特效
  .bg-effects {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
  }

  // 浮动几何图形
  .floating-shapes {
    position: absolute;
    width: 100%;
    height: 100%;

    .shape {
      position: absolute;
      border-radius: 50%;
      opacity: 0.15;
      animation: float 20s infinite linear;
      filter: blur(0.5rem);
      box-shadow: 0 0 1.875rem rgba(59, 130, 246, 0.3),
      0 0 3.75rem rgba(59, 130, 246, 0.2),
      inset 0 0 1.875rem rgba(255, 255, 255, 0.05);

      &.shape-1 {
        width: 7.5rem;
        height: 7.5rem;
        background: linear-gradient(45deg, @primary-color, @accent-color);
        top: 10%;
        left: 10%;
        animation-delay: 0s;
        animation-duration: 25s;
      }

      &.shape-2 {
        width: 5rem;
        height: 5rem;
        background: linear-gradient(45deg, @accent-color, @primary-light);
        top: 60%;
        left: 80%;
        animation-delay: -5s;
        animation-duration: 30s;
      }

      &.shape-3 {
        width: 9.375rem;
        height: 9.375rem;
        background: linear-gradient(45deg, @secondary-color, @primary-color);
        top: 80%;
        left: 20%;
        animation-delay: -10s;
        animation-duration: 35s;
      }

      &.shape-4 {
        width: 3.75rem;
        height: 3.75rem;
        background: linear-gradient(45deg, @primary-light, @secondary-color);
        top: 20%;
        left: 70%;
        animation-delay: -15s;
        animation-duration: 20s;
      }

      &.shape-5 {
        width: 6.25rem;
        height: 6.25rem;
        background: linear-gradient(45deg, @accent-color, @primary-color);
        top: 50%;
        left: 5%;
        animation-delay: -20s;
        animation-duration: 28s;
      }

      &.shape-6 {
        width: 5.625rem;
        height: 5.625rem;
        background: linear-gradient(45deg, @primary-color, @secondary-color);
        top: 30%;
        left: 90%;
        animation-delay: -25s;
        animation-duration: 32s;
      }
    }
  }

  @keyframes float {
    0% {
      transform: translateY(0) translateX(0) rotate(0deg);
    }
    33% {
      transform: translateY(-1.875rem) translateX(1.875rem) rotate(120deg);
    }
    66% {
      transform: translateY(1.25rem) translateX(-1.25rem) rotate(240deg);
    }
    100% {
      transform: translateY(0) translateX(0) rotate(360deg);
    }
  }

  // 光点粒子效果
  .light-particles {
    position: absolute;
    width: 100%;
    height: 100%;

    .particle {
      position: absolute;
      width: 0.375rem;
      height: 0.375rem;
      background: @accent-color;
      border-radius: 50%;
      opacity: 0;
      animation: sparkle 3s infinite;
      box-shadow: 0 0 0.625rem @accent-color,
      0 0 1.25rem @accent-color,
      0 0 1.875rem @accent-color;

      &.particle-1 {
        top: 15%;
        left: 25%;
        animation-delay: 0s;
      }

      &.particle-2 {
        top: 35%;
        left: 75%;
        animation-delay: 0.5s;
      }

      &.particle-3 {
        top: 65%;
        left: 45%;
        animation-delay: 1s;
      }

      &.particle-4 {
        top: 85%;
        left: 15%;
        animation-delay: 1.5s;
      }

      &.particle-5 {
        top: 25%;
        left: 85%;
        animation-delay: 2s;
      }

      &.particle-6 {
        top: 75%;
        left: 65%;
        animation-delay: 2.5s;
      }

      &.particle-7 {
        top: 45%;
        left: 25%;
        animation-delay: 1.2s;
      }

      &.particle-8 {
        top: 55%;
        left: 85%;
        animation-delay: 1.8s;
      }
    }
  }

  @keyframes sparkle {
    0%, 100% {
      opacity: 0;
      transform: scale(0.5);
    }
    50% {
      opacity: 1;
      transform: scale(1.5);
    }
  }

  // 网格线条
  .grid-lines {
    position: absolute;
    width: 100%;
    height: 100%;

    .grid-line {
      position: absolute;
      background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.3), transparent);
      opacity: 0;
      animation: gridMove 8s infinite;
      box-shadow: 0 0 1.25rem rgba(59, 130, 246, 0.2);

      &.grid-line-1 {
      width: 100%;
        height: 1px;
        top: 20%;
        animation-delay: 0s;
      }

      &.grid-line-2 {
        width: 1px;
      height: 100%;
        left: 30%;
        background: linear-gradient(0deg, transparent, rgba(59, 130, 246, 0.3), transparent);
        animation-delay: 2s;
      }

      &.grid-line-3 {
        width: 100%;
        height: 1px;
        top: 80%;
        animation-delay: 4s;
      }
    }
  }

  @keyframes gridMove {
    0%, 100% {
      opacity: 0;
      transform: translateX(-100%);
    }
    50% {
      opacity: 0.6;
      transform: translateX(0%);
    }
  }

  .login-content {
    max-width: 68.75rem;
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 30rem;
    gap: 3.75rem;
      align-items: center;
    position: relative;
    z-index: 2;
  }

  // 品牌展示区域
  .brand-section {
    color: @text-primary;
      position: relative;
    z-index: 3;

    .brand-content {
      max-width: 37.5rem;
      
      .logo {
        margin-bottom: 1.875rem;

        .brand-title {
          font-size: 3rem;
          font-weight: @font-weight-bold;
          margin: 0;
          color: @text-primary;
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .logo-svg {
          width: 3.5rem;
          height: 3.5rem;
          flex-shrink: 0;
          filter: drop-shadow(0 0 1.25rem rgba(59, 130, 246, 0.5));
        }
      }

      h2 {
        font-size: 1.75rem;
        margin-bottom: 1.25rem;
        line-height: @line-height-tight;
        color: @text-primary;
        font-weight: @font-weight-semibold;
      }

      p {
        font-size: 1rem;
        line-height: @line-height-relaxed;
        color: @text-secondary;
        margin-bottom: 2.5rem;
      }

      .features {
        .feature {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 0.9375rem;
          font-size: 1rem;
          color: @text-secondary;

          .ivu-icon {
            color: @accent-color;
            font-size: 1.25rem;
            flex-shrink: 0;
          }
        }
      }
    }
  }

  // 表单区域
  .form-section {
    flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
    position: relative;
    z-index: 3;

    .login-card {
      width: 100%;
      max-width: 30rem;
      background: rgba(26, 26, 26, 0.95);
      border: 1px solid rgba(59, 130, 246, 0.2);
      border-radius: @border-radius-xl;
      backdrop-filter: blur(1.25rem);
      box-shadow: 0 1.25rem 2.5rem rgba(0, 0, 0, 0.5),
      0 0 5rem rgba(59, 130, 246, 0.1),
      inset 0 0.0625rem 0 rgba(255, 255, 255, 0.05);
      transition: all @transition-slow;

      &:hover {
        border-color: rgba(59, 130, 246, 0.3);
        box-shadow: 0 1.5625rem 3.125rem rgba(0, 0, 0, 0.6),
        0 0 6.25rem rgba(59, 130, 246, 0.15),
        inset 0 0.0625rem 0 rgba(255, 255, 255, 0.08);
        transform: translateY(-0.125rem);
      }

      /deep/ .ivu-card-body {
        padding: 2.5rem;
      }
    }

    .form-header {
      text-align: center;
      margin-bottom: 1.875rem;

      h3 {
        font-size: 1.5rem;
        margin-bottom: 0.625rem;
        color: @text-primary;
        font-weight: @font-weight-semibold;
      }

      p {
        color: @text-secondary;
        font-size: @font-size-small;
      }
    }

    .ivu-btn-primary {
      background: linear-gradient(135deg, @primary-color, @accent-color);
      border: none;
      height: 2.8125rem;
      font-size: 1rem;
      font-weight: @font-weight-medium;
      box-shadow: @shadow-primary;
      transition: all @transition-slow;

      &:hover:not(:disabled) {
        background: linear-gradient(135deg, @primary-dark, @primary-color);
        box-shadow: 0 0.5rem 1.5rem rgba(59, 130, 246, 0.4);
        transform: translateY(-0.125rem);
      }

      &:disabled {
        background: rgba(59, 130, 246, 0.3);
        color: @text-tertiary;
        box-shadow: none;
        transform: none;
      }
    }

    .form-footer {
      text-align: center;
      margin-top: 1.5625rem;

      p.tips {
        color: @text-secondary;
        font-size: @font-size-small;
      }
    }
  }

  // 表单样式覆盖
  /deep/ .ivu-form-item {
    margin-bottom: 1.25rem;

    .ivu-input-wrapper {
      .ivu-input {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(75, 85, 99, 0.5);
        color: @text-primary;
        transition: all @transition-base;
        height: 2.8125rem;
        font-size: @font-size-base;

        &::placeholder {
          color: @text-placeholder;
        }

        &:hover {
          border-color: rgba(59, 130, 246, 0.4);
          background: rgba(255, 255, 255, 0.08);
        }

        &:focus {
          border-color: @primary-color;
          box-shadow: @shadow-focus;
          background: rgba(255, 255, 255, 0.1);
        }
      }

      .ivu-input-prefix {
        color: @text-tertiary;
        font-size: 1.125rem;
      }
    }
  }

  // 响应式设计
  @media (max-width: @screen-md) {
    .login-content {
      grid-template-columns: 1fr;
      gap: 2.5rem;
    }

    .brand-section {
      text-align: center;

      .brand-content {
        margin: 0 auto;

        .logo {
          .brand-title {
            justify-content: center;
            font-size: 2.5rem;
          }

          .logo-svg {
            width: 3rem;
            height: 3rem;
          }
        }

        h2 {
          font-size: 1.5rem;
        }

        .features {
          display: inline-block;
          text-align: left;
        }
      }
    }

    .form-section {
      .login-card {
        max-width: 26rem;
      }
    }

    // 简化背景效果
    .floating-shapes .shape {
      opacity: 0.1;
    }

    .light-particles .particle {
      display: none;
    }

    .grid-lines .grid-line {
      opacity: 0.5;
    }
  }

  @media (max-width: @screen-sm) {
    .login-container {
      padding: 1rem;
    }

    .login-content {
      gap: 2rem;
    }

    .brand-section {
      .brand-content {
        .logo {
          margin-bottom: 1.25rem;

          .brand-title {
            font-size: 2rem;
          }

          .logo-svg {
            width: 2.5rem;
            height: 2.5rem;
          }
        }

        h2 {
          font-size: 1.25rem;
          margin-bottom: 1rem;
        }

        p {
          font-size: 0.875rem;
          margin-bottom: 1.5rem;
        }

        .features {
          .feature {
            font-size: 0.875rem;
            margin-bottom: 0.75rem;

            .ivu-icon {
              font-size: 1rem;
            }
          }
        }
      }
    }

    .form-section {
      .login-card {
        /deep/ .ivu-card-body {
          padding: 1.875rem 1.25rem;
        }
      }

      .form-header {
        margin-bottom: 1.5rem;

        h3 {
          font-size: 1.25rem;
        }
      }
    }

    // 移动端隐藏背景效果
    .floating-shapes,
    .light-particles,
    .grid-lines {
      display: none;
    }
  }
</style>
