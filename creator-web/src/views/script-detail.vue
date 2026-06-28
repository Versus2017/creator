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
      <div class="script-content-area" :class="{ 'with-media-panel': showMediaPanel }">
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
          <div class="script-subtitle-row">
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
            <Button 
              size="small"
              class="copy-full-btn"
              @click="copyFullContent"
            >
              <Icon type="ios-copy" />
              复制全文
            </Button>
          </div>
          
          <div 
            class="markdown-content" 
            v-html="renderMarkdown(script.content)"
          ></div>
        </div>
      </div>
    </div>

    <!-- ✦ 左下角悬浮分享按钮 ✦ -->
    <div
      class="share-fab"
      :class="{ loading: isSharing }"
      @click="shareScript"
    >
      <Icon type="md-share" class="fab-icon" v-if="!isSharing" />
      <Icon type="md-refresh" class="fab-icon spin-icon" v-else />
      <span class="fab-label">{{ isSharing ? '导出中…' : '分享脚本' }}</span>
    </div>

    <!-- ✦ 右下角悬浮 AI 生图触发按钮 ✦ -->
    <div class="ai-fab" @click="toggleMediaPanel" :class="{ active: showMediaPanel }">
      <Icon type="md-color-wand" class="fab-icon" />
      <span class="fab-label">AI 生图</span>
    </div>

    <!-- ✦ AI 生图侧边面板 ✦ -->
    <transition name="panel-slide">
      <div v-if="showMediaPanel" class="ai-media-panel">
        <!-- 面板头部 -->
        <div class="panel-header">
          <div class="panel-title">
            <Icon type="md-color-wand" />
            AI 生图
          </div>
          <Icon type="md-close" class="panel-close" @click="showMediaPanel = false" />
        </div>

        <!-- 类型选择 -->
        <div class="panel-section">
          <div class="section-label">选择素材类型</div>
          <div class="media-type-grid">
            <div
              v-for="t in mediaTypeOptions"
              :key="t.value"
              class="type-card"
              :class="{ selected: selectedMediaType === t.value }"
              @click="selectedMediaType = t.value"
            >
              <div class="type-icon">{{ t.icon }}</div>
              <div class="type-name">{{ t.label }}</div>
              <div class="type-ratio">{{ t.ratio }}</div>
              <div class="type-desc">{{ t.desc }}</div>
            </div>
          </div>
        </div>

        <!-- 生成按钮 -->
        <div class="panel-section">
          <Button
            type="primary"
            long
            :loading="generating"
            @click="generateMedia"
            class="generate-btn"
          >
            <Icon type="md-color-wand" v-if="!generating" />
            {{ generating ? '生成中…' : '开始生成' }}
          </Button>
        </div>

        <!-- 历史生成记录 -->
        <div class="panel-section panel-history" v-if="scriptMediaList.length > 0">
          <div class="section-label">生成记录</div>
          <div class="history-list">
            <div
              v-for="item in scriptMediaList"
              :key="item.id"
              class="history-item"
            >
              <!-- 生成中/等待（无部分结果） -->
              <div
                v-if="(item.status.name === 'PENDING' || item.status.name === 'PROCESSING') && !hasPartialSegments(item)"
                class="history-img loading-placeholder"
              >
                <div class="loading-spinner">
                  <Icon type="md-refresh" class="spin-icon" />
                </div>
                <div class="loading-text">{{ getMediaProgressText(item) }}</div>
              </div>

              <!-- 生成中：素材已有部分段落 -->
              <div
                v-else-if="item.status.name === 'PROCESSING' && hasPartialSegments(item)"
                class="history-segments processing-segments"
              >
                <div
                  v-for="seg in item.generated_items"
                  :key="item.id + '-proc-' + seg.segment_index"
                  class="segment-card"
                >
                  <div v-if="seg.status === 'completed' && seg.media_url" class="history-img-wrap">
                    <img
                      :src="seg.media_url"
                      :alt="seg.segment_title"
                      class="history-img-thumb segment-thumb"
                      @click="previewImage(seg.media_url)"
                    />
                  </div>
                  <div v-else-if="seg.status === 'failed'" class="history-img failed-placeholder segment-failed">
                    <Icon type="md-close-circle" />
                  </div>
                  <div v-else class="history-img loading-placeholder segment-loading">
                    <Icon type="md-refresh" class="spin-icon" />
                  </div>
                  <div class="segment-title">{{ seg.segment_title }}</div>
                </div>
                <div class="segment-progress-tip">{{ getMediaProgressText(item) }}</div>
              </div>

              <!-- 失败 -->
              <div v-else-if="item.status.name === 'FAILED'" class="history-img failed-placeholder">
                <Icon type="md-close-circle" />
                <div class="failed-text">生成失败</div>
                <div class="failed-err" :title="item.error_message">{{ item.error_message }}</div>
              </div>

              <!-- 封面 / 素材：多图批次 -->
              <div v-else-if="isMultiImageBatch(item)" class="history-segments">
                <div
                  v-for="seg in item.generated_items"
                  :key="item.id + '-' + seg.segment_index"
                  class="segment-card"
                >
                  <div v-if="seg.status === 'completed' && seg.media_url" class="history-img-wrap">
                    <img
                      :src="seg.media_url"
                      :alt="seg.segment_title"
                      class="history-img-thumb segment-thumb"
                      :class="{ 'cover-portrait': isCoverBatch(item) && seg.segment_index === 1, 'cover-landscape': isCoverBatch(item) && seg.segment_index === 2 }"
                      @click="previewImage(seg.media_url)"
                    />
                    <div class="img-overlay">
                      <Icon type="md-expand" @click.stop="previewImage(seg.media_url)" title="预览" />
                      <Icon type="md-download" @click.stop="downloadImage(seg.media_url, seg.segment_title)" title="下载" />
                    </div>
                  </div>
                  <div v-else class="history-img failed-placeholder segment-failed">
                    <Icon type="md-close-circle" />
                    <div class="failed-text">生成失败</div>
                  </div>
                  <div class="segment-title">{{ seg.segment_title }}</div>
                </div>
              </div>

              <!-- 封面：旧版单图兼容 -->
              <div v-else-if="item.media_url" class="history-img-wrap">
                <img
                  :src="item.media_url"
                  :alt="item.media_type.label"
                  class="history-img-thumb"
                  @click="previewImage(item.media_url)"
                />
                <div class="img-overlay">
                  <Icon type="md-expand" @click.stop="previewImage(item.media_url)" title="预览" />
                  <Icon type="md-download" @click.stop="downloadImage(item.media_url, item.media_type.label)" title="下载" />
                </div>
              </div>

              <div class="history-meta">
                <Tag :color="getMediaTypeColor(item.media_type.name)" size="small">{{ item.media_type.label }}</Tag>
                <span v-if="isMultiImageBatch(item) && item.total_segment_count" class="history-progress">
                  {{ item.completed_segment_count || 0 }}/{{ item.total_segment_count }} {{ isCoverBatch(item) ? '张' : '段' }}
                </span>
                <span class="history-time">{{ item.created_at }}</span>
              </div>
              <div v-if="item.error_message && item.status.name === 'COMPLETED'" class="history-warn">
                {{ item.error_message }}
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div class="panel-empty" v-else>
          <Icon type="md-images" />
          <p>还没有生成过素材<br>选择类型后点击开始生成</p>
        </div>
      </div>
    </transition>

    <!-- 图片预览遮罩 -->
    <transition name="fade">
      <div v-if="previewUrl" class="image-preview-mask" @click="previewUrl = null">
        <div class="preview-container" @click.stop>
          <img :src="previewUrl" class="preview-image" />
          <Icon type="md-close" class="preview-close" @click="previewUrl = null" />
        </div>
      </div>
    </transition>

  </div>
</template>

<script>
import moment from 'moment'
import marked from 'marked'
import { api } from '@/libs/api'

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
      saving: false,

      // AI 生图面板
      showMediaPanel: false,
      selectedMediaType: 10,
      generating: false,
      scriptMediaList: [],
      mediaPollingTimer: null,
      previewUrl: null,
      isSharing: false,

      // 素材类型选项（与后端 ScriptMediaType 对应）
      mediaTypeOptions: [
        { value: 10, label: '封面', ratio: '4K · 3:4 + 4:3', icon: '📱', desc: '竖版 2480×3312 + 横版 3312×2480' },
        { value: 20, label: '素材', ratio: '4K · 4:3', icon: '🖼️', desc: '3312×2480 · 横版配图' }
      ]
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
          await this.loadScriptMedia()
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

    // 复制全文
    copyFullContent() {
      const content = this.script.content || ''
      if (!content.trim()) {
        this.$Message.warning('脚本内容为空，无法复制')
        return
      }
      this.copyToClipboard(content, '全文')
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
    },

    // ── AI 生图面板 ──────────────────────────────

    toggleMediaPanel() {
      this.showMediaPanel = !this.showMediaPanel
      if (this.showMediaPanel && this.script.id) {
        this.loadScriptMedia()
      }
    },

    async loadScriptMedia() {
      if (!this.script.id) return
      try {
        const response = await this.$http.get('/web/scripts/' + this.script.id + '/media')
        if (response && response.success) {
          this.scriptMediaList = (response.data && response.data.rows) || []
          this.startMediaPolling()
        }
      } catch (err) {
        console.error('加载素材列表失败:', err)
      }
    },

    async generateMedia() {
      if (!this.script.id) return
      this.generating = true
      try {
        const response = await this.$http.post('/web/scripts/' + this.script.id + '/media', {
          media_type: this.selectedMediaType
        })
        if (response && response.success) {
          var successHint = this.selectedMediaType === 10
            ? '已提交封面生成任务，将生成竖版+横版两张'
            : '已提交素材生成任务，AI 会先分析脚本再逐段生图'
          this.$Message.success(successHint)
          await this.loadScriptMedia()
        } else {
          this.$Message.error('提交失败，请重试')
        }
      } catch (err) {
        console.error('提交生图任务失败:', err)
        this.$Message.error('提交失败，请重试')
      } finally {
        this.generating = false
      }
    },

    startMediaPolling() {
      this.stopMediaPolling()
      var self = this
      function hasPending() {
        return self.scriptMediaList.some(function(item) {
          return item.status && (item.status.name === 'PENDING' || item.status.name === 'PROCESSING')
        })
      }
      if (!hasPending()) return
      this.mediaPollingTimer = setInterval(function() {
        if (!self.showMediaPanel) {
          self.stopMediaPolling()
          return
        }
        self.$http.get('/web/scripts/' + self.script.id + '/media').then(function(res) {
          if (res && res.success) {
            self.scriptMediaList = (res.data && res.data.rows) || []
            if (!hasPending()) {
              self.stopMediaPolling()
            }
          }
        }).catch(function(err) {
          console.error('轮询素材列表失败:', err)
        })
      }, 4000)
    },

    stopMediaPolling() {
      if (this.mediaPollingTimer) {
        clearInterval(this.mediaPollingTimer)
        this.mediaPollingTimer = null
      }
    },

    previewImage(url) {
      this.previewUrl = url
    },

    downloadImage(url, label) {
      var a = document.createElement('a')
      a.href = url
      a.download = (label || 'image') + '.png'
      a.target = '_blank'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    },

    isMaterialBatch(item) {
      return item
        && item.media_type
        && item.media_type.name === 'MATERIAL'
        && item.generated_items
        && item.generated_items.length > 0
    },

    isCoverBatch(item) {
      return item
        && item.media_type
        && item.media_type.name === 'COVER'
        && item.generated_items
        && item.generated_items.length > 0
    },

    isMultiImageBatch(item) {
      return this.isMaterialBatch(item) || this.isCoverBatch(item)
    },

    hasPartialSegments(item) {
      return this.isMultiImageBatch(item) && item.status && item.status.name === 'PROCESSING'
    },

    getMediaProgressText(item) {
      if (!item) return '处理中…'
      if (item.media_type && item.media_type.name === 'MATERIAL') {
        var total = item.total_segment_count || 0
        var done = item.completed_segment_count || 0
        if (total > 0) {
          return '生成中 ' + done + '/' + total + ' 段…'
        }
        return 'AI 分析脚本规划中…'
      }
      if (item.media_type && item.media_type.name === 'COVER') {
        var coverTotal = item.total_segment_count || 2
        var coverDone = item.completed_segment_count || 0
        if (coverDone > 0) {
          return '生成中 ' + coverDone + '/' + coverTotal + ' 张…'
        }
        return 'AI 分析封面规划中…'
      }
      return (item.status && item.status.label ? item.status.label : '处理中') + '…'
    },

    getMediaTypeColor(name) {
      var colorMap = {
        COVER:    'purple',
        MATERIAL: 'blue'
      }
      return colorMap[name] || 'default'
    },

    // ── 分享/导出脚本（后端打包：index.html + 本地图片） ──

    async shareScript() {
      if (!this.script || !this.script.id) {
        this.$Message.warning('脚本尚未加载')
        return
      }
      if (!this.script.content || !String(this.script.content).trim()) {
        this.$Message.warning('暂无脚本内容可分享')
        return
      }
      if (this.isSharing) {
        return
      }

      this.isSharing = true
      try {
        var title = (this.script.title || '未命名脚本').trim()
        var exportedAt = moment().format('YYYY-MM-DD HH:mm')
        var zipBlob = await api.get('/web/scripts/' + this.script.id + '/share', {
          responseType: 'blob',
          hideError: true
        })
        if (!zipBlob || zipBlob.size === 0) {
          throw new Error('压缩包为空')
        }
        if (zipBlob.type && zipBlob.type.indexOf('json') >= 0) {
          var errText = await zipBlob.text()
          var errJson = {}
          try {
            errJson = JSON.parse(errText)
          } catch (parseErr) {
            errJson = {}
          }
          throw new Error((errJson && errJson.message) || '分享失败')
        }
        this.downloadZipFile(this.buildShareFileName(title, exportedAt), zipBlob)
        this.$Message.success('已导出压缩包，解压后打开 index.html 即可查看')
      } catch (error) {
        console.error('分享脚本失败:', error)
        this.$Message.error((error && error.message) || '分享失败，请稍后重试')
      } finally {
        this.isSharing = false
      }
    },

    buildShareFileName(title, exportedAt) {
      var safeTitle = String(title || '脚本')
        .replace(/[\\/:*?"<>|]/g, '_')
        .replace(/\s+/g, '_')
        .slice(0, 40)
      return safeTitle + '_' + exportedAt.replace(/[:\s]/g, '-') + '.zip'
    },

    downloadZipFile(fileName, zipBlob) {
      var url = URL.createObjectURL(zipBlob)
      var link = document.createElement('a')
      link.href = url
      link.download = fileName
      link.style.display = 'none'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    }
  },

  beforeDestroy() {
    this.stopMediaPolling()
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
  .script-subtitle-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  }

  .script-subtitle {
    flex: 1;
    font-size: 1.25rem;
    color: rgba(255, 255, 255, 0.9);
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

  .copy-full-btn {
    flex-shrink: 0;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.25);
    color: rgba(255, 255, 255, 0.9);

    &:hover {
      background: rgba(59, 130, 246, 0.2);
      border-color: @primary-color;
      color: #FFFFFF;
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

// ── 左下角分享悬浮按钮 ──────────────────────────
.share-fab {
  position: fixed;
  bottom: 2rem;
  left: 2rem;
  z-index: 200;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: linear-gradient(135deg, @primary-color 0%, @accent-color 100%);
  border-radius: 2rem;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.45);
  transition: all 0.25s ease;
  user-select: none;

  .fab-icon {
    font-size: 1.2rem;
    color: #fff;
  }

  .fab-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: #fff;
    letter-spacing: 0.02em;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 28px rgba(59, 130, 246, 0.6);
  }

  &.loading {
    cursor: wait;
    opacity: 0.85;
  }

  .spin-icon {
    animation: spin 1.2s linear infinite;
  }
}

// ── AI 生图悬浮按钮 ──────────────────────────
.ai-fab {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 200;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 2rem;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.45);
  transition: all 0.25s ease;
  user-select: none;

  .fab-icon {
    font-size: 1.2rem;
    color: #fff;
  }

  .fab-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: #fff;
    letter-spacing: 0.02em;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 28px rgba(99, 102, 241, 0.6);
  }

  &.active {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
  }
}

// ── AI 生图侧边面板 ──────────────────────────
.ai-media-panel {
  position: fixed;
  top: 64px;
  right: 0;
  bottom: 0;
  width: 22rem;
  z-index: 190;
  background: rgba(15, 23, 42, 0.96);
  backdrop-filter: blur(16px);
  border-left: 1px solid rgba(99, 102, 241, 0.2);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid rgba(99, 102, 241, 0.15);
    position: sticky;
    top: 0;
    background: rgba(15, 23, 42, 0.98);
    z-index: 10;

    .panel-title {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 1rem;
      font-weight: 600;
      color: #e2e8f0;

      .ivu-icon {
        color: #818cf8;
        font-size: 1.15rem;
      }
    }

    .panel-close {
      font-size: 1.25rem;
      color: #64748b;
      cursor: pointer;
      transition: color 0.2s;

      &:hover { color: #e2e8f0; }
    }
  }

  .panel-section {
    padding: 1rem 1.25rem;

    & + .panel-section {
      border-top: 1px solid rgba(99, 102, 241, 0.08);
    }
  }

  .section-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.75rem;
  }

  // 类型卡片网格
  .media-type-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.625rem;
  }

  .type-card {
    padding: 1rem 0.75rem;
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 0.75rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
    background: rgba(30, 41, 59, 0.5);

    &:hover {
      border-color: rgba(99, 102, 241, 0.4);
      background: rgba(99, 102, 241, 0.08);
    }

    &.selected {
      border-color: #818cf8;
      background: rgba(99, 102, 241, 0.15);
      box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.3);
    }

    .type-icon {
      font-size: 1.75rem;
      line-height: 1;
      margin-bottom: 0.4rem;
    }

    .type-name {
      font-size: 0.9rem;
      font-weight: 700;
      color: #e2e8f0;
    }

    .type-ratio {
      display: inline-block;
      font-size: 0.7rem;
      font-weight: 600;
      color: #818cf8;
      background: rgba(99, 102, 241, 0.12);
      border-radius: 0.25rem;
      padding: 0.1rem 0.35rem;
      margin-top: 0.3rem;
    }

    .type-desc {
      font-size: 0.68rem;
      color: #64748b;
      margin-top: 0.35rem;
      line-height: 1.3;
    }
  }

  // 生成按钮
  .generate-btn {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    font-weight: 600;
    letter-spacing: 0.02em;
    height: 2.5rem;
    border-radius: 0.625rem !important;
    box-shadow: 0 2px 12px rgba(99, 102, 241, 0.35);
    transition: all 0.2s ease !important;

    &:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 4px 18px rgba(99, 102, 241, 0.5) !important;
    }
  }

  // 历史记录
  .panel-history { flex: 1; }

  .history-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .history-item {
    border-radius: 0.75rem;
    overflow: hidden;
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid rgba(99, 102, 241, 0.1);
  }

  .loading-placeholder,
  .failed-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 7rem;
    gap: 0.4rem;
    color: #64748b;
    font-size: 0.8rem;
  }

  .loading-spinner {
    .spin-icon {
      font-size: 1.5rem;
      color: #818cf8;
      animation: spin 1.2s linear infinite;
    }
  }

  .loading-text { color: #94a3b8; font-size: 0.75rem; }

  .failed-placeholder {
    .ivu-icon { font-size: 1.5rem; color: #f87171; }
    .failed-text { color: #f87171; font-size: 0.75rem; }
    .failed-err {
      color: #64748b;
      font-size: 0.7rem;
      max-width: 90%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .history-img-wrap {
    position: relative;
    overflow: hidden;
    cursor: pointer;

    &:hover .img-overlay { opacity: 1; }

    .history-img-thumb {
      width: 100%;
      display: block;
      object-fit: cover;
      max-height: 10rem;
    }

    .img-overlay {
      position: absolute;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 1.25rem;
      opacity: 0;
      transition: opacity 0.2s;

      .ivu-icon {
        font-size: 1.5rem;
        color: #fff;
        cursor: pointer;
        transition: transform 0.15s;

        &:hover { transform: scale(1.15); }
      }
    }
  }

  .history-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0.75rem;
    flex-wrap: wrap;
    gap: 0.25rem;

    .history-progress {
      font-size: 0.7rem;
      color: #818cf8;
    }

    .history-time {
      font-size: 0.7rem;
      color: #475569;
    }
  }

  .history-warn {
    padding: 0 0.75rem 0.5rem;
    font-size: 0.68rem;
    color: #fbbf24;
  }

  .history-segments {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0.75rem;
  }

  .segment-card {
    border-radius: 0.5rem;
    overflow: hidden;
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid rgba(99, 102, 241, 0.12);
  }

  .segment-thumb {
    max-height: 8rem;
    object-fit: cover;
  }

  .cover-portrait {
    max-height: 10rem;
    aspect-ratio: 3 / 4;
    width: auto;
    margin: 0 auto;
    display: block;
  }

  .cover-landscape {
    max-height: 7rem;
    aspect-ratio: 4 / 3;
    width: 100%;
    display: block;
  }

  .segment-title {
    padding: 0.4rem 0.6rem;
    font-size: 0.72rem;
    color: #94a3b8;
    line-height: 1.35;
    border-top: 1px solid rgba(99, 102, 241, 0.08);
  }

  .segment-failed,
  .segment-loading {
    height: 5rem;
  }

  .segment-progress-tip {
    text-align: center;
    font-size: 0.75rem;
    color: #818cf8;
    padding-bottom: 0.25rem;
  }

  .processing-segments {
    opacity: 0.95;
  }

  // 空状态
  .panel-empty {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    text-align: center;
    color: #475569;

    .ivu-icon {
      font-size: 3rem;
      color: #334155;
      margin-bottom: 1rem;
    }

    p {
      font-size: 0.8rem;
      line-height: 1.6;
      color: #64748b;
    }
  }
}

// 面板滑入动画
.panel-slide-enter-active,
.panel-slide-leave-active {
  transition: transform 0.28s cubic-bezier(0.25, 1, 0.5, 1), opacity 0.28s ease;
}
.panel-slide-enter,
.panel-slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

// 图片预览遮罩
.image-preview-mask {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-out;

  .preview-container {
    position: relative;
    max-width: 90vw;
    max-height: 90vh;
    cursor: default;
  }

  .preview-image {
    max-width: 100%;
    max-height: 90vh;
    border-radius: 0.5rem;
    object-fit: contain;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.6);
  }

  .preview-close {
    position: absolute;
    top: -1.5rem;
    right: -1.5rem;
    font-size: 1.5rem;
    color: #94a3b8;
    cursor: pointer;
    background: rgba(15, 23, 42, 0.8);
    border-radius: 50%;
    padding: 0.25rem;
    transition: color 0.2s;

    &:hover { color: #fff; }
  }
}

// 淡入淡出过渡
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter, .fade-leave-to { opacity: 0; }

// 旋转动画
@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
</style>

