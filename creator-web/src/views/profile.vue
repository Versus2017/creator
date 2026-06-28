<template>
  <div class="profile-container">
    <!-- 简化的背景效果 -->
    <div class="bg-effects">
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
      </div>
      <div class="light-particles">
        <div class="particle particle-1"></div>
        <div class="particle particle-2"></div>
        <div class="particle particle-3"></div>
      </div>
    </div>

    <div class="content-wrapper">
      <div class="profile-content">
        <!-- 左侧Tab菜单 -->
        <div class="tabs-sidebar">
          <div class="sidebar-header">
            <h3>个人中心</h3>
          </div>
          <div class="tabs-menu">
            <div 
              v-for="tab in tabs" 
              :key="tab.key"
              :class="['tab-item', { active: activeTab === tab.key }]"
              @click="switchTab(tab.key)"
            >
              <Icon :type="tab.icon" />
              <span>{{ tab.label }}</span>
            </div>
          </div>
        </div>

        <!-- 右侧内容区域 -->
        <div class="content-area">
          <!-- 主页：展示用户信息 -->
          <div v-if="activeTab === 'home'" class="tab-content">
            <div class="content-card">
              <h2 class="card-title">
                <Icon type="ios-person" />
                个人信息
              </h2>
              
              <div v-if="loading" style="text-align: center; padding: 3rem 0; color: #9CA3AF;">
                <Spin size="large">
                  <Icon type="ios-loading" size="32" class="spin-icon-load"></Icon>
                  <div style="margin-top: 1rem;">正在加载用户信息...</div>
                </Spin>
              </div>
              
              <div v-else-if="!currentUser.id" style="text-align: center; padding: 3rem 0; color: #9CA3AF;">
                <p>未能获取用户信息</p>
                <Button type="primary" @click="reloadUserInfo">重新加载</Button>
              </div>
              
              <div v-else class="user-info-section">
                <div class="avatar-section">
                  <Avatar :src="userAvatar" size="100" icon="ios-person" class="user-avatar-large"/>
                  <div class="user-basic">
                    <h3 class="user-name">{{ currentUser.nickname || currentUser.username }}</h3>
                    <div class="user-username">@{{ currentUser.username }}</div>
                    <!-- 展示 AI 标签 -->
                    <div class="user-tags" v-if="currentUser.tags && currentUser.tags.length > 0">
                      <Tag v-for="(tag, index) in currentUser.tags" :key="index" color="blue" class="profile-tag">{{ tag }}</Tag>
                    </div>
                  </div>
                </div>
                
                <div class="info-list">
                  <div class="info-item">
                    <div class="info-label">
                      <Icon type="ios-person"/>
                      用户名
                    </div>
                    <div class="info-value">{{ currentUser.username }}</div>
                  </div>
                  
                  <div class="info-item">
                    <div class="info-label">
                      <Icon type="ios-chatbubbles"/>
                      昵称
                    </div>
                    <div class="info-value">{{ currentUser.nickname || '未设置' }}</div>
                  </div>
                  
                  <div class="info-item">
                    <div class="info-label">
                      <Icon type="ios-phone-portrait"/>
                      手机号
                    </div>
                    <div class="info-value">{{ currentUser.mobile || '未绑定' }}</div>
                  </div>
                  
                  <div class="info-item">
                    <div class="info-label">
                      <Icon type="ios-calendar"/>
                      注册时间
                    </div>
                    <div class="info-value">{{ formatDate(currentUser.created_at) }}</div>
                  </div>
                  
                  <!-- 简介部分 -->
                  <div class="info-item block-item">
                    <div class="info-label">
                      <Icon type="ios-list-box-outline"/>
                      自我介绍
                    </div>
                    <div class="info-value multi-line">{{ currentUser.introduction || '暂无介绍' }}</div>
                  </div>

                  <!-- AI 总结部分 -->
                  <div class="info-item block-item" v-if="currentUser.ai_summary">
                    <div class="info-label ai-label">
                      <Icon type="md-analytics"/>
                      AI 画像总结
                    </div>
                    <div class="info-value multi-line ai-text">{{ currentUser.ai_summary }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 编辑信息 -->
          <div v-if="activeTab === 'edit'" class="tab-content">
            <div class="content-card">
              <h2 class="card-title">
                <Icon type="ios-create" />
                编辑信息
              </h2>
              
              <Form ref="editProfileForm" :model="editProfileData" :rules="editProfileRules" :label-width="100" class="profile-form">
                <FormItem label="头像">
                  <div class="avatar-upload-wrapper">
                    <Avatar :src="editProfileData.avatar_url || userAvatar" size="80" icon="ios-person" class="edit-avatar"/>
                    <Upload
                      :action="uploadAction"
                      :headers="uploadHeaders"
                      :on-success="handleAvatarUploadSuccess"
                      :on-error="handleAvatarUploadError"
                      :show-upload-list="false"
                      :format="['jpg', 'jpeg', 'png']"
                      :max-size="2048"
                      :on-format-error="handleFormatError"
                      :on-exceeded-size="handleMaxSize"
                      :with-credentials="true"
                      name="image"
                    >
                      <Button icon="ios-cloud-upload">上传头像</Button>
                    </Upload>
                  </div>
                  <div class="form-tip">支持 jpg、png 格式，大小不超过 2MB</div>
                </FormItem>
                
                <FormItem label="用户名">
                  <Input v-model="currentUser.username" disabled placeholder="用户名不可修改"/>
                </FormItem>
                
                <FormItem label="昵称" prop="nickname">
                  <Input 
                    v-model="editProfileData.nickname" 
                    placeholder="请输入昵称"
                    maxlength="50"
                  />
                </FormItem>
                
                <FormItem label="手机号" prop="mobile">
                  <Input 
                    v-model="editProfileData.mobile" 
                    placeholder="请输入手机号"
                    maxlength="11"
                  />
                </FormItem>
                
                <FormItem label="自我介绍" prop="introduction">
                  <Input 
                    v-model="editProfileData.introduction" 
                    type="textarea"
                    :autosize="{minRows: 3, maxRows: 6}"
                    placeholder="请输入自我介绍（500字以内）。AI 将根据您的介绍生成个性化标签和总结，帮助您更好地创作视频。"
                    maxlength="500"
                    show-word-limit
                  />
                  <div class="form-tip">填写详细的自我介绍，AI 会自动分析您的领域和风格，为您提供更精准的创作建议。</div>
                </FormItem>
                
                <FormItem>
                  <Button type="primary" @click="handleUpdateProfile" :loading="updateProfileLoading" size="large">
                    <Icon type="ios-checkmark-circle"/>
                    保存修改
                  </Button>
                </FormItem>
              </Form>
            </div>
          </div>

          <!-- 修改密码 -->
          <div v-if="activeTab === 'password'" class="tab-content">
            <div class="content-card">
              <h2 class="card-title">
                <Icon type="ios-lock" />
                修改密码
              </h2>
              
              <Form ref="changePasswordForm" :model="changePasswordData" :rules="changePasswordRules" :label-width="100" class="profile-form">
                <FormItem label="当前密码" prop="old_password">
                  <Input 
                    v-model="changePasswordData.old_password" 
                    type="password" 
                    placeholder="请输入当前密码"
                    autocomplete="off"
                  />
                </FormItem>
                
                <FormItem label="新密码" prop="new_password">
                  <Input 
                    v-model="changePasswordData.new_password" 
                    type="password" 
                    placeholder="请输入新密码（6-20位）"
                    autocomplete="off"
                  />
                </FormItem>
                
                <FormItem label="确认新密码" prop="confirm_password">
                  <Input 
                    v-model="changePasswordData.confirm_password" 
                    type="password" 
                    placeholder="请再次输入新密码"
                    autocomplete="off"
                  />
                </FormItem>
                
                <FormItem>
                  <Button type="primary" @click="handleChangePassword" :loading="changePasswordLoading" size="large">
                    <Icon type="ios-checkmark-circle"/>
                    确认修改
                  </Button>
                </FormItem>
              </Form>
            </div>
          </div>

          <!-- 退出登录 -->
          <div v-if="activeTab === 'logout'" class="tab-content">
            <div class="content-card">
              <h2 class="card-title">
                <Icon type="ios-log-out" />
                退出登录
              </h2>
              
              <div class="logout-section">
                <h3>确认退出登录？</h3>
                <p>退出后需要重新登录才能访问个人信息</p>
                <Button type="error" size="large" @click="confirmLogout">
                  <Icon type="ios-log-out"/>
                  确认退出
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Profile',

  data() {
    // 验证手机号
    const validateMobile = (rule, value, callback) => {
      if (!value) {
        callback()
      } else if (!/^1[3-9]\d{9}$/.test(value)) {
        callback(new Error('手机号格式错误'))
      } else {
        callback()
      }
    }
    
    // 验证新密码
    const validateNewPassword = (rule, value, callback) => {
      if (!value) {
        callback(new Error('请输入新密码'))
      } else if (value.length < 6 || value.length > 20) {
        callback(new Error('新密码长度为6-20位'))
      } else if (value === this.changePasswordData.old_password) {
        callback(new Error('新密码不能与当前密码相同'))
      } else {
        callback()
      }
    }
    
    // 验证确认密码
    const validateConfirmPassword = (rule, value, callback) => {
      if (!value) {
        callback(new Error('请再次输入新密码'))
      } else if (value !== this.changePasswordData.new_password) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }

    return {
      activeTab: 'home',
      loading: false,
      tabs: [
        { key: 'home', label: '主页', icon: 'ios-home' },
        { key: 'edit', label: '编辑信息', icon: 'ios-create' },
        { key: 'password', label: '修改密码', icon: 'ios-lock' },
        { key: 'logout', label: '退出登录', icon: 'ios-log-out' }
      ],
      
      // 编辑用户信息相关
      updateProfileLoading: false,
      editProfileData: {
        nickname: '',
        mobile: '',
        avatar_id: null,
        avatar_url: '',
        introduction: '' // 新增：自我介绍
      },
      editProfileRules: {
        nickname: [
          { max: 50, message: '昵称长度不能超过50个字符', trigger: 'blur' }
        ],
        mobile: [
          { validator: validateMobile, trigger: 'blur' }
        ],
        introduction: [
          { max: 500, message: '自我介绍长度不能超过500个字符', trigger: 'blur' }
        ]
      },
      
      // 修改密码相关
      changePasswordLoading: false,
      changePasswordData: {
        old_password: '',
        new_password: '',
        confirm_password: ''
      },
      changePasswordRules: {
        old_password: [
          { required: true, message: '请输入当前密码', trigger: 'blur' },
          { min: 6, max: 20, message: '密码长度为6-20位', trigger: 'blur' }
        ],
        new_password: [
          { required: true, message: '请输入新密码', trigger: 'blur' },
          { validator: validateNewPassword, trigger: 'blur' }
        ],
        confirm_password: [
          { required: true, message: '请再次输入新密码', trigger: 'blur' },
          { validator: validateConfirmPassword, trigger: 'blur' }
        ]
      }
    }
  },

  computed: {
    currentUser() {
      return this.$store.getters.user || {}
    },
    
    userAvatar() {
      return this.currentUser.avatar || ''
    },
    
    uploadAction() {
      return '/v1/media'
    },
    
    uploadHeaders() {
      return {
        'source': 'web'
      }
    }
  },

  methods: {
    switchTab(tabKey) {
      this.activeTab = tabKey
    },
    
    async reloadUserInfo() {
      this.loading = true
      try {
        await this.$store.dispatch('refreshUser')
        this.$Message.success('用户信息加载成功')
      } catch (error) {
        console.error('加载用户信息失败:', error)
        this.$Message.error('加载用户信息失败')
      } finally {
        this.loading = false
      }
    },
    
    formatDate(dateStr) {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      })
    },
    
    async handleAvatarUploadSuccess(response) {
      if (response && response.success) {
        this.editProfileData.avatar_id = response.data.id
        this.editProfileData.avatar_url = response.data.url
        this.$Message.success('头像上传成功')
        
        try {
          const updateResponse = await this.$http.post('/web/users/me', {
            avatar_id: response.data.id
          })
          
          if (updateResponse && updateResponse.success) {
            await this.$store.dispatch('refreshUser')
            this.$Message.success('头像已更新')
          }
        } catch (error) {
          console.error('保存头像失败:', error)
        }
      } else {
        this.$Message.error(response.message || '头像上传失败')
      }
    },
    
    handleAvatarUploadError() {
      this.$Message.error('头像上传失败，请重试')
    },
    
    handleFormatError() {
      this.$Message.error('文件格式不正确，请上传 jpg 或 png 格式的图片')
    },
    
    handleMaxSize() {
      this.$Message.error('文件大小不能超过 2MB')
    },
    
    async handleUpdateProfile() {
      const valid = await new Promise((resolve) => {
        this.$refs.editProfileForm.validate((valid) => {
          resolve(valid)
        })
      })
      
      if (!valid) {
        return
      }
      
      this.updateProfileLoading = true
      try {
        // 准备提交的数据
        const submitData = {
          nickname: this.editProfileData.nickname || null,
          mobile: this.editProfileData.mobile || null,
          avatar_id: this.editProfileData.avatar_id || null,
          introduction: this.editProfileData.introduction || null
        }

        const response = await this.$http.post('/web/users/me', submitData)
        
        if (response && response.success) {
          this.$Message.success('信息更新成功')
          // 提示 AI 分析
          if (this.editProfileData.introduction && this.editProfileData.introduction !== this.currentUser.introduction) {
            this.$Message.info({
              content: '正在进行AI画像分析，稍后将为您生成个性化标签',
              duration: 5
            })
          }
          await this.$store.dispatch('refreshUser')
          this.activeTab = 'home'
        } else {
          this.$Message.error(response.message || '信息更新失败')
        }
      } catch (error) {
        console.error('更新用户信息失败:', error)
        const errorMsg = error.response && error.response.data && error.response.data.message || '信息更新失败'
        this.$Message.error(errorMsg)
      } finally {
        this.updateProfileLoading = false
      }
    },
    
    async handleChangePassword() {
      const valid = await new Promise((resolve) => {
        this.$refs.changePasswordForm.validate((valid) => {
          resolve(valid)
        })
      })
      
      if (!valid) {
        return
      }
      
      this.changePasswordLoading = true
      try {
        const response = await this.$http.put('/web/users/me/password', {
          old_password: this.changePasswordData.old_password,
          new_password: this.changePasswordData.new_password,
          confirm_password: this.changePasswordData.confirm_password
        })
        
        if (response && response.success) {
          this.$Message.success('密码修改成功')
          this.changePasswordData = {
            old_password: '',
            new_password: '',
            confirm_password: ''
          }
          this.$refs.changePasswordForm.resetFields()
        } else {
          this.$Message.error(response.message || '密码修改失败')
        }
      } catch (error) {
        console.error('修改密码失败:', error)
        const errorMsg = error.response && error.response.data && error.response.data.message || '密码修改失败'
        this.$Message.error(errorMsg)
      } finally {
        this.changePasswordLoading = false
      }
    },
    
    confirmLogout() {
      this.$Modal.confirm({
        title: '确认退出',
        content: '您确定要退出登录吗？',
        okText: '确认退出',
        cancelText: '取消',
        onOk: () => {
          this.logout()
        }
      })
    },
    
    logout() {
      this.$store.dispatch('logout', { vue: this, makeRequest: true })
    }
  },

  async mounted() {
    if (!this.currentUser || !this.currentUser.id) {
      this.loading = true
      try {
        await this.$store.dispatch('refreshUser')
      } catch (error) {
        console.error('加载用户信息失败:', error)
        this.$Message.error('加载用户信息失败')
      } finally {
        this.loading = false
      }
    }
    
    this.$nextTick(() => {
      this.editProfileData = {
        nickname: this.currentUser.nickname || '',
        mobile: this.currentUser.mobile || '',
        avatar_id: this.currentUser.avatar_id || null,
        avatar_url: this.userAvatar || '',
        introduction: this.currentUser.introduction || ''
      }
    })
  },

  watch: {
    currentUser: {
      handler(newVal) {
        if (newVal) {
          this.editProfileData = {
            nickname: newVal.nickname || '',
            mobile: newVal.mobile || '',
            avatar_id: newVal.avatar_id || null,
            avatar_url: newVal.avatar || '',
            introduction: newVal.introduction || ''
          }
        }
      },
      deep: true
    }
  }
}
</script>

<style lang="less" scoped>
@import '../styles/variables.less';

.profile-container {
  min-height: ~"calc(100vh - 64px)";
  background: @bg-primary;
  position: relative;
  overflow-x: hidden;
}

// 背景效果
.bg-effects {
  position: fixed;
  top: 64px;
  left: 0;
  width: 100%;
  height: ~"calc(100% - 64px)";
  pointer-events: none;
  z-index: 0;
  overflow: hidden;

  .floating-shapes {
    position: absolute;
    width: 100%;
    height: 100%;

    .shape {
      position: absolute;
      border-radius: 50%;
      filter: blur(3.75rem);
      opacity: 0.08;
      animation: float 40s infinite ease-in-out;

      &.shape-1 {
        width: 25rem;
        height: 25rem;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.3), transparent);
        top: 10%;
        left: 10%;
      }

      &.shape-2 {
        width: 21.875rem;
        height: 21.875rem;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.3), transparent);
        top: 50%;
        right: 15%;
        animation-delay: -20s;
      }

      &.shape-3 {
        width: 18.75rem;
        height: 18.75rem;
        background: radial-gradient(circle, rgba(6, 182, 212, 0.3), transparent);
        bottom: 20%;
        left: 20%;
        animation-delay: -10s;
      }
    }
  }

  .light-particles {
    position: absolute;
    width: 100%;
    height: 100%;

    .particle {
      position: absolute;
      width: 0.25rem;
      height: 0.25rem;
      background: @accent-color;
      border-radius: 50%;
      animation: particle-float 15s infinite ease-in-out;
      opacity: 0.6;

      &.particle-1 {
        top: 20%;
        left: 15%;
      }

      &.particle-2 {
        top: 60%;
        left: 80%;
        animation-delay: -5s;
      }

      &.particle-3 {
        top: 40%;
        left: 50%;
        animation-delay: -10s;
      }
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(1.875rem, -1.875rem);
  }
}

@keyframes particle-float {
  0%, 100% {
    transform: translateY(0);
    opacity: 0;
  }
  10%, 90% {
    opacity: 0.6;
  }
  50% {
    transform: translateY(-6.25rem);
  }
}

.content-wrapper {
  position: relative;
  z-index: 1;
  max-width: 75rem;
  margin: 0 auto;
  padding: 2rem 1.25rem;
  min-height: ~"calc(100vh - 64px)";
}

.profile-content {
  display: flex;
  gap: 2rem;
  margin-top: 2rem;
}

// 左侧Tab菜单
.tabs-sidebar {
  width: 15rem;
  flex-shrink: 0;
  background: rgba(26, 26, 26, 0.8);
  backdrop-filter: blur(0.625rem);
  border-radius: @border-radius-xl;
  border: 1px solid rgba(75, 85, 99, 0.3);
  padding: 1.5rem;
  height: fit-content;
  position: sticky;
  top: 6rem;

  .sidebar-header {
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(75, 85, 99, 0.3);

    h3 {
      font-size: @font-size-h5;
      font-weight: @font-weight-semibold;
      color: @text-primary;
      margin: 0;
    }
  }

  .tabs-menu {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;

    .tab-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.875rem 1rem;
      border-radius: @border-radius-md;
      cursor: pointer;
      transition: all @transition-base;
      color: @text-secondary;
      font-size: @font-size-base;
      font-weight: @font-weight-medium;

      .ivu-icon {
        font-size: 1.25rem;
      }

      &:hover {
        background: rgba(59, 130, 246, 0.1);
        color: @primary-light;
      }

      &.active {
        background: linear-gradient(135deg, @primary-color, @accent-color);
        color: @text-primary;
        box-shadow: @shadow-primary;
      }
    }
  }
}

// 右侧内容区域
.content-area {
  flex: 1;
  min-width: 0;
}

.tab-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(0.625rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.content-card {
  background: rgba(26, 26, 26, 0.8);
  backdrop-filter: blur(0.625rem);
  border-radius: @border-radius-xl;
  border: 1px solid rgba(75, 85, 99, 0.3);
  padding: 2rem;

  .card-title {
    font-size: @font-size-h4;
    font-weight: @font-weight-semibold;
    color: @text-primary;
    margin: 0 0 2rem 0;
    display: flex;
    align-items: center;
    gap: 0.75rem;

    .ivu-icon {
      font-size: 1.75rem;
      color: @primary-color;
    }
  }
}

// 用户信息展示
.user-info-section {
  .avatar-section {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 2rem;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(6, 182, 212, 0.1));
    border-radius: @border-radius-lg;
    margin-bottom: 2rem;

    .user-avatar-large {
      background: linear-gradient(135deg, @primary-color, @accent-color) !important;
      box-shadow: @shadow-md;
      flex-shrink: 0;

      /deep/ .ivu-avatar-icon {
        color: @text-primary !important;
      }
    }

    .user-basic {
      flex: 1;
      
      .user-name {
        font-size: @font-size-h3;
        font-weight: @font-weight-semibold;
        color: @text-primary;
        margin: 0 0 0.5rem 0;
      }

      .user-username {
        font-size: @font-size-base;
        color: @text-tertiary;
        margin-bottom: 0.75rem;
      }

      .user-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        
        .profile-tag {
          background: rgba(59, 130, 246, 0.2) !important;
          border: 1px solid rgba(59, 130, 246, 0.4) !important;
          color: @primary-light !important;
          border-radius: 1rem;
          padding: 0 0.75rem;
          height: 1.5rem;
          line-height: 1.5rem;
          
          /deep/ .ivu-tag-text {
            color: @primary-light !important;
          }
        }
      }
    }
  }

  .info-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;

    .info-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 1.25rem;
      background: rgba(15, 15, 15, 0.5);
      border-radius: @border-radius-md;
      transition: all @transition-base;

      &:hover {
        background: rgba(15, 15, 15, 0.8);
        transform: translateX(0.25rem);
      }

      .info-label {
        display: flex;
        align-items: center;
        gap: 0.625rem;
        font-size: @font-size-base;
        color: @text-secondary;
        flex-shrink: 0;

        .ivu-icon {
          font-size: 1.125rem;
        }
        
        &.ai-label {
          color: @accent-color;
          .ivu-icon {
            color: @accent-color;
          }
        }
      }

      .info-value {
        font-size: @font-size-base;
        color: @text-primary;
        font-weight: @font-weight-medium;
        
        &.multi-line {
          white-space: pre-wrap;
          text-align: right;
          max-width: 60%;
          line-height: 1.6;
        }
        
        &.ai-text {
          color: @primary-light;
        }
      }
      
      &.block-item {
        align-items: flex-start;
        
        .info-label {
          margin-top: 0.25rem;
        }
      }
    }
  }
}

// 表单样式
.profile-form {
  max-width: 37.5rem;

  /deep/ .ivu-form-item {
    margin-bottom: 1.5rem;

    .ivu-form-item-label {
      color: @text-secondary;
      font-size: @font-size-base;
      font-weight: @font-weight-medium;
    }

    .ivu-input {
      background: rgba(15, 15, 15, 0.5);
      border: 1px solid rgba(75, 85, 99, 0.3);
      color: @text-primary;
      border-radius: @border-radius-md;
      min-height: 2.75rem;
      font-size: @font-size-base;
      padding: 0.5rem 0.75rem;

      &:hover {
        border-color: rgba(75, 85, 99, 0.5);
      }

      &:focus {
        border-color: @primary-color;
        box-shadow: @shadow-focus;
      }

      &[disabled] {
        background: rgba(15, 15, 15, 0.3);
        color: @text-tertiary;
        cursor: not-allowed;
      }
    }

    .ivu-input::placeholder {
      color: @text-placeholder;
    }
    
    textarea.ivu-input {
      height: auto;
      min-height: 5rem;
    }

    .ivu-btn-large {
      height: 2.75rem;
      padding: 0 2rem;
      font-size: @font-size-base;
      border-radius: @border-radius-md;
      background: linear-gradient(135deg, @primary-color, @accent-color);
      border: none;
      font-weight: @font-weight-medium;

      &:hover {
        background: linear-gradient(135deg, @primary-dark, @primary-color);
        box-shadow: @shadow-primary;
      }

      .ivu-icon {
        margin-right: 0.5rem;
      }
    }
  }

  .avatar-upload-wrapper {
    display: flex;
    align-items: center;
    gap: 1.25rem;

    .edit-avatar {
      background: linear-gradient(135deg, @primary-color, @accent-color) !important;
      box-shadow: @shadow-sm;

      /deep/ .ivu-avatar-icon {
        color: @text-primary !important;
      }
    }

    /deep/ .ivu-btn {
      background: rgba(75, 85, 99, 0.3);
      border: 1px solid rgba(75, 85, 99, 0.5);
      color: @text-primary;
      border-radius: @border-radius-md;
      height: 2.25rem;

      &:hover {
        background: rgba(75, 85, 99, 0.5);
        border-color: rgba(75, 85, 99, 0.7);
      }

      .ivu-icon {
        margin-right: 0.375rem;
      }
    }
  }

  .form-tip {
    margin-top: 0.625rem;
    font-size: @font-size-small;
    color: @text-tertiary;
  }
}

// 退出登录区域
.logout-section {
  text-align: center;
  padding: 3rem 0;

  h3 {
    font-size: @font-size-h4;
    font-weight: @font-weight-semibold;
    color: @text-primary;
    margin: 0 0 1rem 0;
  }

  p {
    font-size: @font-size-base;
    color: @text-secondary;
    margin: 0 0 2rem 0;
  }

  .ivu-btn-error {
    height: 2.75rem;
    padding: 0 2rem;
    font-size: @font-size-base;
    border-radius: @border-radius-md;
    background: linear-gradient(135deg, @error-color, #DC2626);
    border: none;
    font-weight: @font-weight-medium;

    &:hover {
      background: linear-gradient(135deg, #DC2626, #B91C1C);
      box-shadow: 0 0.25rem 0.75rem rgba(239, 68, 68, 0.4);
    }

    .ivu-icon {
      margin-right: 0.5rem;
    }
  }
}

// 响应式设计
@media (max-width: @screen-md) {
  .profile-content {
    flex-direction: column;
  }

  .tabs-sidebar {
    width: 100%;
    position: static;

    .tabs-menu {
      flex-direction: row;
      flex-wrap: wrap;

      .tab-item {
        flex: 1;
        min-width: ~"calc(50% - 0.25rem)";
        justify-content: center;
      }
    }
  }

  .content-card {
    padding: 1.5rem;
  }

  .user-info-section {
    .avatar-section {
      flex-direction: column;
      text-align: center;
    }
    
    .info-list {
      .info-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
        
        .info-value.multi-line {
          text-align: left;
          max-width: 100%;
        }
      }
    }
  }

  .profile-form {
    .avatar-upload-wrapper {
      flex-direction: column;
    }
  }
}

@media (max-width: @screen-sm) {
  .content-wrapper {
    padding: 1rem;
  }

  .tabs-sidebar {
    padding: 1rem;
  }
}
</style>