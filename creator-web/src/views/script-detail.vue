<template>
  <div class="script-detail-page">
    <!-- 科技感背景效果 -->
    <div class="bg-effects">
      <div class="mind-grid"></div>
      
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
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <Button 
            type="text" 
            size="large"
            class="back-btn"
            @click="goBack"
          >
            <Icon type="ios-arrow-back" />
            返回
          </Button>
          
          <div class="header-content">
            <h1 class="page-title">
              <Icon type="ios-document-outline" />
              {{ script.title || '脚本详情' }}
              <Button 
                type="text" 
                size="small"
                class="copy-btn"
                @click="copyTitle"
                :title="'复制标题'"
              >
                <Icon type="ios-copy" />
              </Button>
            </h1>
            <div class="page-meta">
              <Tag :color="getStatusColor(script.status)">
                {{ script.status && script.status.label }}
              </Tag>
              <span class="meta-item">
                <Icon type="ios-text" />
                {{ script.word_count || 0 }} 字
              </span>
              <span class="meta-item">
                <Icon type="ios-pricetag" />
                {{ script.format_type || '未指定' }}
              </span>
              <span class="meta-item">
                <Icon type="ios-time" />
                {{ formatDate(script.created_at) }}
              </span>
            </div>
          </div>
        </div>
        
        <div class="header-actions">
          <template v-if="!isEditMode">
            <Button 
              type="warning" 
              size="large"
              class="research-btn"
              @click="startResearch"
            >
              <Icon type="ios-bulb" />
              研究此脚本
            </Button>
            <Button 
              type="primary" 
              size="large"
              @click="enterEditMode"
            >
              <Icon type="ios-create" />
              编辑
            </Button>
          </template>
          <template v-else>
            <Button 
              size="large"
              @click="cancelEdit"
            >
              取消
            </Button>
            <Button 
              type="primary" 
              size="large"
              @click="saveScript"
              :loading="saving"
            >
              <Icon type="ios-checkmark" />
              保存
            </Button>
          </template>
        </div>
      </div>

      <!-- 脚本内容区域 -->
      <div class="script-content-area">
        <!-- 编辑模式 -->
        <div v-if="isEditMode" class="edit-mode">
          <div class="edit-section">
            <label class="edit-label">脚本标题</label>
            <Input 
              v-model="editForm.title" 
              placeholder="请输入脚本标题"
              size="large"
              class="title-input"
            />
          </div>
          
          <div class="edit-section">
            <div class="edit-label-row">
              <label class="edit-label">脚本内容</label>
              <div class="view-mode-toggle">
                <Button 
                  :type="viewMode === 'edit' ? 'primary' : 'default'"
                  size="small"
                  @click="viewMode = 'edit'"
                >
                  编辑
                </Button>
                <Button 
                  :type="viewMode === 'preview' ? 'primary' : 'default'"
                  size="small"
                  @click="viewMode = 'preview'"
                >
                  预览
                </Button>
              </div>
            </div>
            
            <!-- 编辑视图 -->
            <div v-if="viewMode === 'edit'" class="content-editor">
              <Input
                v-model="editForm.content"
                type="textarea"
                :autosize="{ minRows: 20, maxRows: 50 }"
                placeholder="请输入脚本内容（支持Markdown格式）"
                class="content-textarea"
              />
            </div>
            
            <!-- 预览视图 -->
            <div v-else class="content-preview">
              <div 
                class="markdown-content" 
                v-html="renderMarkdown(editForm.content)"
              ></div>
            </div>
          </div>
        </div>

        <!-- 查看模式 -->
        <div v-else class="view-mode">
          <div class="script-subtitle" v-if="script.subtitle">
            {{ script.subtitle }}
            <Button 
              type="text" 
              size="small"
              class="copy-btn"
              @click="copySubtitle"
              :title="'复制副标题'"
            >
              <Icon type="ios-copy" />
            </Button>
          </div>
          
          <div 
            class="markdown-content" 
            v-html="renderMarkdown(script.content)"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import moment from 'moment'
import marked from 'marked'

// 配置marked选项
marked.setOptions({
  breaks: true,        // 支持GitHub风格的换行
  gfm: true,          // 启用GitHub风格的Markdown
  tables: true,       // 支持表格
  smartLists: true,   // 智能列表
  highlight: null     // 代码高亮（可以后续添加）
})

export default {
  name: 'ScriptDetail',
  
  data() {
    return {
      // 脚本数据
      script: {
        id: null,
        title: '',
        subtitle: '',
        content: '',
        status: {},
        word_count: 0,
        format_type: '',
        created_at: ''
      },
      
      // 编辑模式
      isEditMode: false,
      viewMode: 'edit', // 'edit' | 'preview'
      
      // 编辑表单
      editForm: {
        title: '',
        content: ''
      },
      
      // 加载状态
      loading: false,
      saving: false
    }
  },

  methods: {
    // 加载脚本详情
    async loadScript() {
      const scriptId = this.$route.params.id
      if (!scriptId) {
        this.$Message.error('脚本ID不存在')
        this.goBack()
        return
      }

      this.loading = true
      try {
        const response = await this.$http.get(`/web/scripts/${scriptId}`)

        if (response && response.success) {
          this.script = response.data || {}
          // 初始化编辑表单
          this.editForm = {
            title: this.script.title || '',
            content: this.script.content || ''
          }
          
          // 如果URL中有edit参数，自动进入编辑模式
          if (this.$route.query.edit === 'true') {
            this.isEditMode = true
            this.viewMode = 'edit'
          }
        } else {
          this.$Message.error('加载脚本失败')
          this.goBack()
        }
      } catch (error) {
        console.error('加载脚本详情失败:', error)
        this.$Message.error('加载失败，请重试')
        this.goBack()
      } finally {
        this.loading = false
      }
    },

    // 进入编辑模式
    enterEditMode() {
      this.isEditMode = true
      this.viewMode = 'edit'
      // 确保编辑表单数据是最新的
      this.editForm = {
        title: this.script.title || '',
        content: this.script.content || ''
      }
    },

    // 取消编辑
    cancelEdit() {
      this.isEditMode = false
      this.viewMode = 'edit'
      // 恢复原始数据
      this.editForm = {
        title: this.script.title || '',
        content: this.script.content || ''
      }
    },

    // 保存脚本
    async saveScript() {
      if (!this.editForm.title || !this.editForm.title.trim()) {
        this.$Message.warning('请输入脚本标题')
        return
      }

      if (!this.editForm.content || !this.editForm.content.trim()) {
        this.$Message.warning('请输入脚本内容')
        return
      }

      this.saving = true
      try {
        const response = await this.$http.put(
          `/web/scripts/${this.script.id}`,
          {
            title: this.editForm.title.trim(),
            content: this.editForm.content.trim()
          }
        )

        if (response && response.success) {
          this.$Message.success('保存成功')
          this.isEditMode = false
          this.viewMode = 'edit'
          // 重新加载脚本数据
          await this.loadScript()
        }
      } catch (error) {
        console.error('保存脚本失败:', error)
        this.$Message.error('保存失败，请重试')
      } finally {
        this.saving = false
      }
    },

    // 渲染Markdown
    renderMarkdown(content) {
      if (!content) return ''
      try {
        return marked(content)
      } catch (error) {
        console.error('Markdown渲染失败:', error)
        return content
      }
    },

    // 返回
    goBack() {
      this.$router.push({ name: 'scripts' })
    },

    // 获取状态颜色
    getStatusColor(status) {
      if (!status || !status.name) return 'default'
      const colorMap = {
        DRAFT: 'default',
        COMPLETED: 'success',
        ARCHIVED: 'warning'
      }
      return colorMap[status.name] || 'default'
    },

    // 格式化日期
    formatDate(date) {
      if (!date) return ''
      return moment(date).format('YYYY-MM-DD HH:mm')
    },

    // 开始研究脚本
    startResearch() {
      this.$router.push({ 
        name: 'research-chat', 
        query: { scriptId: this.script.id } 
      })
    },

    // 复制标题
    copyTitle() {
      const title = this.script.title || ''
      if (!title) {
        this.$Message.warning('标题为空，无法复制')
        return
      }
      this.copyToClipboard(title, '标题')
    },

    // 复制副标题
    copySubtitle() {
      const subtitle = this.script.subtitle || ''
      if (!subtitle) {
        this.$Message.warning('副标题为空，无法复制')
        return
      }
      this.copyToClipboard(subtitle, '副标题')
    },

    // 复制到剪贴板
    copyToClipboard(text, label) {
      // 使用现代 Clipboard API
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
          this.$Message.success(`${label}已复制到剪贴板`)
        }).catch(() => {
          // 降级方案：使用传统方法
          this.fallbackCopyToClipboard(text, label)
        })
      } else {
        // 降级方案：使用传统方法
        this.fallbackCopyToClipboard(text, label)
      }
    },

    // 降级复制方法（兼容旧浏览器）
    fallbackCopyToClipboard(text, label) {
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      
      try {
        const successful = document.execCommand('copy')
        if (successful) {
          this.$Message.success(`${label}已复制到剪贴板`)
        } else {
          this.$Message.error('复制失败，请手动复制')
        }
      } catch (err) {
        console.error('复制失败:', err)
        this.$Message.error('复制失败，请手动复制')
      } finally {
        document.body.removeChild(textArea)
      }
    }
  },

  mounted() {
    this.loadScript()
  }
}
</script>

<style lang="less" scoped>
@import '../styles/variables.less';

.script-detail-page {
  height: ~"calc(100vh - 64px)";
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 30%, #312e81 70%, #1e1b4b 100%);
  position: relative;
  overflow: hidden;
}

// 背景特效（与创意页面一致）
.bg-effects {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.mind-grid {
  position: absolute;
  width: 100%;
  height: 100%;
  background-image: 
    radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 50% 50%, rgba(6, 182, 212, 0.06) 0%, transparent 70%),
    linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px),
    linear-gradient(0deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
  background-size: 
    100% 100%,
    100% 100%,
    100% 100%,
    6.25rem 6.25rem,
    6.25rem 6.25rem;
  animation: gridPulse 8s ease-in-out infinite;
}

@keyframes gridPulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.floating-shapes {
  position: absolute;
  width: 100%;
  height: 100%;

  .shape {
    position: absolute;
    border-radius: 50%;
    opacity: 0.12;
    animation: float 20s infinite ease-in-out;
    filter: blur(1px);

    &.shape-1 {
      width: 8rem;
      height: 8rem;
      background: linear-gradient(135deg, @primary-color 0%, @accent-color 100%);
      top: 10%;
      left: 15%;
      animation-duration: 28s;
    }

    &.shape-2 {
      width: 6rem;
      height: 6rem;
      background: linear-gradient(135deg, @secondary-color 0%, @primary-color 100%);
      top: 60%;
      right: 10%;
      animation-delay: -6s;
      animation-duration: 32s;
    }

    &.shape-3 {
      width: 10rem;
      height: 10rem;
      background: linear-gradient(135deg, @primary-light 0%, @primary-color 100%);
      bottom: 15%;
      left: 20%;
      animation-delay: -12s;
      animation-duration: 38s;
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) rotate(0deg);
  }
  33% {
    transform: translate(1.875rem, -1.875rem) rotate(120deg);
  }
  66% {
    transform: translate(-1.25rem, 1.25rem) rotate(240deg);
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
    background: radial-gradient(circle, rgba(255, 255, 255, 0.8) 0%, transparent 70%);
    border-radius: 50%;
    animation: particleFloat 15s infinite ease-in-out;

    &.particle-1 {
      top: 20%;
      left: 30%;
      animation-delay: 0s;
    }

    &.particle-2 {
      top: 50%;
      left: 70%;
      animation-delay: -3s;
    }

    &.particle-3 {
      top: 80%;
      left: 50%;
      animation-delay: -6s;
    }
  }
}

@keyframes particleFloat {
  0%, 100% {
    transform: translateY(0) scale(1);
    opacity: 0.3;
  }
  50% {
    transform: translateY(-3.125rem) scale(1.2);
    opacity: 0.8;
  }
}

// 内容容器
.content-wrapper {
  position: relative;
  z-index: 1;
  height: 100%;
  overflow-y: auto;
  padding: 2rem;
}

// 页面头部
.page-header {
  max-width: 1200px;
  margin: 0 auto 2rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 2rem;

  .header-left {
    flex: 1;
    display: flex;
    align-items: flex-start;
    gap: 1rem;

    .back-btn {
      color: rgba(255, 255, 255, 0.8);
      padding: 0.5rem;
      margin-top: 0.25rem;

      &:hover {
        color: @primary-light;
        background: rgba(59, 130, 246, 0.1);
      }

      .ivu-icon {
        font-size: 1.25rem;
      }
    }

    .header-content {
      flex: 1;

      .page-title {
        font-size: 2rem;
        font-weight: @font-weight-bold;
        color: #FFFFFF;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;

        .ivu-icon {
          font-size: 2rem;
        }

        .copy-btn {
          color: rgba(255, 255, 255, 0.6);
          padding: 0.25rem 0.5rem;
          margin-left: 0.5rem;
          transition: all @transition-fast;

          &:hover {
            color: @primary-light;
            background: rgba(59, 130, 246, 0.1);
          }

          .ivu-icon {
            font-size: 1.65rem;
          }
        }
      }

      .page-meta {
        display: flex;
        align-items: center;
        gap: 1rem;
        flex-wrap: wrap;

        .meta-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.875rem;
          color: rgba(255, 255, 255, 0.6);

          .ivu-icon {
            font-size: 1rem;
          }
        }
      }
    }
  }

  .header-actions {
    display: flex;
    gap: 0.75rem;

    .research-btn {
      background: linear-gradient(135deg, @accent-color, #FFB84D);
      border: none;
      color: #FFFFFF;
      box-shadow: 0 0.25rem 1rem rgba(255, 149, 0, 0.3);

      &:hover {
        box-shadow: 0 0.5rem 1.5rem rgba(255, 149, 0, 0.5);
        transform: translateY(-2px);
      }
    }
  }
}

// 脚本内容区域
.script-content-area {
  max-width: 1200px;
  margin: 0 auto;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: @border-radius-lg;
  padding: 2rem;
  min-height: 400px;
}

// 查看模式
.view-mode {
  .script-subtitle {
    font-size: 1.25rem;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
    font-weight: @font-weight-medium;
    display: flex;
    align-items: center;
    gap: 0.75rem;

    .copy-btn {
      color: rgba(255, 255, 255, 0.6);
      padding: 0.25rem 0.5rem;
      transition: all @transition-fast;

      &:hover {
        color: @primary-light;
        background: rgba(59, 130, 246, 0.1);
      }

      .ivu-icon {
        font-size: 1.25rem;
      }
    }
  }
}

// 编辑模式
.edit-mode {
  .edit-section {
    margin-bottom: 2rem;

    &:last-child {
      margin-bottom: 0;
    }

    .edit-label {
      display: block;
      font-size: 0.9375rem;
      font-weight: @font-weight-medium;
      color: rgba(255, 255, 255, 0.9);
      margin-bottom: 0.75rem;
    }

    .edit-label-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.75rem;

      .view-mode-toggle {
        display: flex;
        gap: 0.5rem;
      }
    }

    .title-input {
      /deep/ .ivu-input {
        font-size: 1.125rem;
        font-weight: @font-weight-semibold;
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(255, 255, 255, 0.2);
        color: #FFFFFF;

        &:focus {
          background: rgba(255, 255, 255, 0.15);
          border-color: @primary-color;
        }

        &::placeholder {
          color: rgba(255, 255, 255, 0.5);
        }
      }
    }

    .content-editor {
      .content-textarea {
        /deep/ .ivu-input {
          font-size: 1rem;
          line-height: 1.8;
          background: rgba(255, 255, 255, 0.1);
          border-color: rgba(255, 255, 255, 0.2);
          color: #FFFFFF;
          font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;

        &:focus {
          background: rgba(255, 255, 255, 0.15);
          border-color: @primary-color;
        }

        &::placeholder {
          color: rgba(255, 255, 255, 0.5);
        }
      }
      }
    }

    .content-preview {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: @border-radius-md;
      padding: 1.5rem;
      min-height: 300px;
    }
  }
}

// Markdown样式
.markdown-content {
  color: rgba(255, 255, 255, 0.95);
  line-height: 1.8;
  font-size: 1.125rem;
  
  /deep/ * {
    margin: 0;
    padding: 0;
  }
  
  /deep/ p {
    margin-bottom: 1rem;
    line-height: 1.8;
    font-size: 1.125rem;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  /deep/ h1, /deep/ h2, /deep/ h3, /deep/ h4, /deep/ h5, /deep/ h6 {
    font-weight: @font-weight-semibold;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    color: rgba(255, 255, 255, 0.95);
    
    &:first-child {
      margin-top: 0;
    }
  }
  
  /deep/ h1 { font-size: 2rem; }
  /deep/ h2 { font-size: 1.75rem; }
  /deep/ h3 { font-size: 1.5rem; }
  /deep/ h4 { font-size: 1.25rem; }
  /deep/ h5 { font-size: 1.125rem; }
  /deep/ h6 { font-size: 1rem; }
  
  /deep/ ul, /deep/ ol {
    margin-bottom: 1rem;
    padding-left: 2rem;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  /deep/ li {
    margin-bottom: 0.5rem;
    line-height: 1.8;
    font-size: 1.125rem;
  }
  
  /deep/ blockquote {
    border-left: 4px solid @primary-color;
    padding-left: 1rem;
    margin: 1rem 0;
    color: rgba(255, 255, 255, 0.85);
    font-style: italic;
    background: rgba(59, 130, 246, 0.1);
    padding: 1rem;
    border-radius: @border-radius-sm;
    font-size: 1.125rem;
  }
  
  /deep/ code {
    background: rgba(0, 0, 0, 0.3);
    padding: 0.125rem 0.375rem;
    border-radius: @border-radius-sm;
    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
    font-size: 0.875rem;
    color: @primary-light;
  }
  
  /deep/ pre {
    background: rgba(0, 0, 0, 0.3);
    padding: 1rem;
    border-radius: @border-radius-md;
    overflow-x: auto;
    margin: 1rem 0;
    
    code {
      background: transparent;
      padding: 0;
      color: rgba(255, 255, 255, 0.9);
    }
  }
  
  /deep/ table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
    
    th, td {
      border: 1px solid rgba(255, 255, 255, 0.2);
      padding: 0.75rem;
      text-align: left;
    }
    
    th {
      background: rgba(59, 130, 246, 0.1);
      font-weight: @font-weight-semibold;
      color: rgba(255, 255, 255, 0.95);
    }
    
    td {
      color: rgba(255, 255, 255, 0.9);
      font-size: 1.125rem;
    }
  }
  
  /deep/ a {
    color: @primary-light;
    text-decoration: none;
    transition: color @transition-fast;
    
    &:hover {
      color: @primary-color;
      text-decoration: underline;
    }
  }
  
  /deep/ strong {
    font-weight: @font-weight-bold;
    color: rgba(255, 255, 255, 0.95);
  }
  
  /deep/ em {
    font-style: italic;
    color: rgba(255, 255, 255, 0.85);
  }
  
  /deep/ hr {
    border: none;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    margin: 2rem 0;
  }
  
  /deep/ img {
    max-width: 100%;
    height: auto;
    border-radius: @border-radius-md;
    margin: 1rem 0;
  }
}

// 响应式
@media (max-width: @screen-md) {
  .content-wrapper {
    padding: 1rem;
  }

  .page-header {
    flex-direction: column;
    gap: 1rem;

    .header-left {
      flex-direction: column;
      gap: 1rem;

      .back-btn {
        align-self: flex-start;
      }
    }

    .header-actions {
      width: 100%;
      justify-content: flex-end;
    }
  }

  .script-content-area {
    padding: 1.5rem;
  }
}
</style>

