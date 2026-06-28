<template>
  <div class="counseling-container">
    <!-- 动态背景效果 -->
    <div class="bg-effects">
      <!-- 心理主题网格 - 象征思维网络 -->
      <div class="mind-grid"></div>
      
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
        <div class="shape shape-5"></div>
        <div class="shape shape-6"></div>
      </div>

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
    </div>

    <div class="content-wrapper">
      <!-- 左侧：历史会话列表（固定宽度） -->
      <div class="sidebar">
        <div class="sidebar-header">
          <Button 
            type="primary" 
            long 
            size="large"
            @click="createNewSession"
            class="new-chat-btn"
          >
            <Icon type="md-add" />
            新建会话
          </Button>
        </div>

        <div class="session-list">
          <div
            v-for="session in sessionHistory"
            :key="session.id"
            class="session-item"
            :class="{ active: currentSession && currentSession.id === session.id }"
            @click="selectSession(session)"
          >
            <div class="session-icon">
              <Icon type="md-chatbubbles" />
            </div>
            <div class="session-info">
              <div class="session-title">{{ session.title }}</div>
              <div class="session-meta">
                {{ session.total_dialogues }} 条对话 · {{ formatDate(session.created_at) }}
              </div>
            </div>
            <div class="session-actions">
              <Dropdown trigger="click" @on-click="handleSessionAction($event, session)">
                <Icon type="md-more" class="more-icon" />
                <DropdownMenu slot="list">
                  <DropdownItem name="rename">
                    <Icon type="md-create" />
                    重命名
                  </DropdownItem>
                  <DropdownItem name="delete" style="color: #ed4014;">
                    <Icon type="md-trash" />
                    删除
                  </DropdownItem>
                </DropdownMenu>
              </Dropdown>
            </div>
          </div>

          <div v-if="sessionHistory.length === 0" class="empty-state">
            <Icon type="md-filing" size="48" />
            <p>暂无历史会话</p>
            <p class="empty-hint">点击上方按钮创建新会话</p>
          </div>
        </div>
      </div>

      <!-- 中间：对话区域（弹性宽度） -->
      <div 
        class="chat-area"
        :class="{ 'dragging': isDragging }"
        @dragenter="handleDragEnter"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
        @drop="handleDrop"
      >
        

        <!-- 对话消息区域 -->
        <div class="chat-messages" ref="messageContainer">
          <!-- 欢迎提示 -->
          <div v-if="dialogues.length === 0" class="welcome-screen">
            <div class="welcome-icon">💭</div>
            <h3>欢迎使用明术AI心理咨询</h3>
            <p>在下方选择配置并输入您的问题开始咨询</p>
            
            <div class="feature-cards">
              <div class="feature-card">
                <Icon type="md-heart" />
                <span>专业心理疏导</span>
              </div>
              <div class="feature-card">
                <Icon type="ios-star" />
                <span>术数智慧指引</span>
              </div>
              <div class="feature-card">
                <Icon type="md-lock" />
                <span>隐私安全保护</span>
              </div>
            </div>
          </div>

          <!-- 对话列表 -->
          <div v-for="dialogue in dialogues" :key="dialogue.id" class="dialogue-item">
            <!-- 用户消息 -->
            <div class="message user-message">
              <div class="message-avatar user-avatar">
                <img v-if="currentUser && currentUser.avatar" :src="currentUser.avatar" alt="用户头像" class="avatar-image" />
                <Icon v-else type="md-person" />
              </div>
              <div class="message-bubble">
                <!-- 用户上传的图片 -->
                <div v-if="dialogue.attachment" class="message-image">
                  <img :src="dialogue.attachment.url" alt="用户上传的图片" @click="viewDialogueImage(dialogue.attachment)" />
                </div>
                <div class="message-content">{{ dialogue.user_question }}</div>
                <div class="message-footer">
                  <span class="message-time">{{ formatTime(dialogue.created_at) }}</span>
                </div>
              </div>
            </div>

            <!-- AI回复 -->
            <div class="message ai-message">
              <div class="message-avatar ai-avatar">
                <span class="ai-text">AI</span>
              </div>
              <div class="message-bubble">
                <div class="message-header">
                  <span class="ai-label">AI咨询师</span>
                  <div class="config-tags" v-if="(dialogue.scene || dialogue.strategy || dialogue.action || dialogue.emotion_strategy_label || dialogue.event_conflict_strategy_label || dialogue.question_focus_strategy_label || dialogue.open_questions) && !dialogue.regenerating">
                    <Tag v-if="dialogue.emotion_strategy_label" size="small" color="blue">{{ dialogue.emotion_strategy_label }}</Tag>
                    <Tag v-if="dialogue.event_conflict_strategy_label" size="small" color="green">{{ dialogue.event_conflict_strategy_label }}</Tag>
                    <Tag v-if="dialogue.question_focus_strategy_label" size="small" color="purple">{{ dialogue.question_focus_strategy_label }}</Tag>
                    <Tag v-if="dialogue.open_questions" size="small" color="red">开放式引导</Tag>
                  </div>
                </div>
                
                <!-- AI思考过程（可折叠） -->
                <div v-if="dialogue.reasoning_content || dialogue.thinking_content" class="thinking-section">
                  <div class="thinking-header" @click="toggleThinking(dialogue)">
                    <Icon :type="dialogue.thinkingExpanded ? 'md-arrow-dropdown' : 'md-arrow-dropright'" />
                    <span class="thinking-label">
                      <Icon type="ios-bulb" style="margin-right: 0.25rem;" />
                      深度思考过程
                    </span>
                    <span v-if="dialogue.loading || dialogue.regenerating" class="thinking-status">
                      <Spin size="small"></Spin>
                      <span style="margin-left: 0.25rem;">思考中...</span>
                    </span>
                  </div>
                  <div v-show="dialogue.thinkingExpanded" class="thinking-content">
                    <div class="thinking-text">
                      {{ dialogue.thinking_content || dialogue.reasoning_content }}
                      <span v-if="(dialogue.loading || dialogue.regenerating) && dialogue.thinking_content" class="typing-cursor">|</span>
                    </div>
                  </div>
                </div>
                
                <!-- AI回复内容（包括流式生成中的内容） -->
                <div class="message-content" :class="{ 'thinking-only': !dialogue.ai_response && (dialogue.loading || dialogue.regenerating) }">
                  <span v-if="!dialogue.ai_response && (dialogue.loading || dialogue.regenerating)" class="thinking-hint">
                    <Spin size="small"></Spin>
                    <span>{{ dialogue.regenerating ? 'AI正在重新生成回复...' : 'AI正在生成回复...' }}</span>
                  </span>
                  <span v-else>{{ dialogue.ai_response }}</span>
                  <!-- 流式生成中显示光标 -->
                  <span v-if="(dialogue.loading || dialogue.regenerating) && dialogue.ai_response" class="typing-cursor">|</span>
                </div>
                <div class="message-footer">
                  <span class="message-time">
                    {{ formatTime(dialogue.created_at) }}
                    <span v-if="!dialogue.loading && !dialogue.regenerating && dialogue.ai_response" class="word-count">
                      · {{ getWordCount(dialogue.ai_response) }}字
                    </span>
                  </span>
                  <div v-if="!dialogue.loading && !dialogue.regenerating" class="message-actions">
                    <Button type="text" size="small" icon="md-copy" @click="copyMessage(dialogue.ai_response)">复制</Button>
                    <Button v-if="isLastDialogue(dialogue)" type="text" size="small" icon="md-refresh" @click="openRegenerateModal(dialogue)">重新生成</Button>
                    <Button type="text" size="small" icon="md-thumbs-up">有用</Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input-section">
          <!-- 图片预览区域 -->
          <div v-if="uploadedImage" class="image-preview-container">
            <div class="image-preview-wrapper">
              <div class="image-preview" :class="{ 'has-error': uploadedImage.status === 'failed' }">
                <img v-if="uploadedImage.url" :src="uploadedImage.url" alt="上传的图片" />
                <div v-else class="image-placeholder">
                  <Icon type="md-image" />
                </div>
                
                <!-- 状态遮罩 -->
                <div v-if="uploadedImage.status === 'uploading' || uploadedImage.status === 'recognizing'" class="status-overlay">
                  <Spin size="large"></Spin>
                  <span class="status-text">
                    {{ uploadedImage.status === 'uploading' ? '上传中...' : '识别中...' }}
                  </span>
                </div>
                
                <!-- 失败状态 -->
                <div v-if="uploadedImage.status === 'failed'" class="error-overlay">
                  <Icon type="md-close-circle" />
                  <span class="error-text">{{ uploadedImage.error || '识别失败' }}</span>
                </div>
                
                <!-- 成功状态标记 -->
                <div v-if="uploadedImage.status === 'success'" class="success-badge">
                  <Icon type="md-checkmark-circle" />
                </div>
                
                <!-- 操作按钮（悬浮显示） -->
                <div class="image-actions">
                  <Button 
                    type="error" 
                    size="small" 
                    icon="md-trash"
                    @click="removeUploadedImage"
                    title="删除图片"
                  >
                    删除
                  </Button>
                  <Button 
                    type="primary" 
                    size="small" 
                    icon="md-eye"
                    @click="viewImageFullScreen"
                    title="查看大图"
                    :disabled="!uploadedImage.url"
                  >
                    查看
                  </Button>
                </div>
              </div>
              
              <!-- 识别的文字提示 -->
              <!-- <div v-if="uploadedImage.text" class="recognized-text-hint">
                <Icon type="md-checkmark-circle" style="color: #19be6b;" />
                <span>已识别文字并填入输入框</span>
              </div> -->
            </div>
          </div>
          
          <div class="input-wrapper">
            <Input
              ref="chatInput"
              v-model="userInput"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 6 }"
              :placeholder="inputPlaceholder"
              :disabled="isGenerating"
              @keydown.native="handleKeyDown"
              @paste.native="handlePaste"
              class="chat-input"
            />
            
            <Button
              type="primary"
              size="large"
              class="send-btn"
              :loading="isGenerating"
              :disabled="!canSendMessage"
              @click="sendMessage"
            >
              <Icon type="md-send" />
            </Button>
          </div>
        </div>
        
        <!-- 查看大图弹窗 -->
        <Modal
          v-model="imagePreviewModal"
          title="查看图片"
          width="80%"
          :footer-hide="true"
          class-name="image-preview-modal"
        >
          <div class="full-image-container">
            <img v-if="uploadedImage && uploadedImage.url" :src="uploadedImage.url" alt="查看大图" />
          </div>
        </Modal>

        <!-- 重生成配置弹窗 -->
        <Modal
          v-model="regenerateModalVisible"
          title="重新生成配置"
          width="520"
          @on-ok="confirmRegenerate"
          @on-cancel="cancelRegenerate"
          class-name="regenerate-config-modal"
        >
          <div class="config-panel-content">
            <div class="config-item" style="margin-bottom: 0.8rem;">  
              <label>情绪矛盾策略</label>
              <Select v-model="selectedEmotionRuleId" placeholder="自动选择（推荐）" size="default" :disabled="isLoadingConfig">
                <Option :value="null">自动选择</Option>
                <Option v-for="opt in emotionStrategyRuleOptions" :key="opt.id" :value="opt.id">{{ opt.rule }}</Option>
              </Select>
            </div>

            <div class="config-item" style="margin-bottom: 0.8rem;">
              <label>事体冲突策略</label>
              <Select v-model="selectedConflictRuleId" placeholder="自动选择（推荐）" size="default" :disabled="isLoadingConfig">
                <Option :value="null">自动选择</Option>
                <Option v-for="opt in conflictStrategyRuleOptions" :key="opt.id" :value="opt.id">{{ opt.rule }}</Option>
              </Select>
            </div>

            <div class="config-item" style="margin-bottom: 0.8rem;">
              <label>提问核心策略</label>
              <Select v-model="selectedQuestionFocusRuleId" placeholder="自动选择（推荐）" size="default" :disabled="isLoadingConfig">
                <Option :value="null">自动选择</Option>
                <Option v-for="opt in questionFocusStrategyRuleOptions" :key="opt.id" :value="opt.id">{{ opt.rule }}</Option>
              </Select>
            </div>

            <div class="config-item" style="margin-bottom: 0.8rem;">
              <label>字数限制</label>
              <Select v-model="selectedWordLimit" placeholder="选择字数" size="default" :disabled="isLoadingConfig">
                <Option v-for="limit in wordLimits" :key="limit.id" :value="limit.id">{{ limit.label || (limit.word_count + '字') }}</Option>
              </Select>
            </div>

            <div class="config-item">
              <label style="margin-right: 0.5rem;">开放式引导问句</label>
              <i-switch v-model="openQuestions" :true-value="true" :false-value="false" />
            </div>
          </div>
        </Modal>
      </div>

      
    </div>
  </div>
</template>

<script>
import moment from 'moment'
import { SSE } from '../libs/sse'
import { getCookie } from '../libs/util'
import Compressor from 'compressorjs'

export default {
  name: 'Counseling',
  
  data () {
    return {
      // 重生成配置弹窗
      regenerateModalVisible: false,
      
      // 配置选项数据（从API加载）
      scenes: [],
      strategies: [],
      actions: [],
      strategyOptions: { emotion: [], conflict: [], question_focus: [] },
      selectedEmotionRuleId: null,
      selectedConflictRuleId: null,
      selectedQuestionFocusRuleId: null,
      wordLimits: [],
      
      // 选中的配置
      selectedEmotionStrategy: '',
      selectedEventConflictStrategy: '',
      selectedQuestionFocusStrategy: '',
      openQuestions: false,
      selectedWordLimit: null,
      
      // 会话和对话
      currentSession: null,
      sessionHistory: [],
      dialogues: [],
      currentRound: 1,
      
      // 输入状态
      userInput: '',
      isGenerating: false,
      
      // 图片上传相关
      uploadedImage: null, // { media_id, url, status: 'uploading'|'recognizing'|'success'|'failed', text, error }
      imagePreviewModal: false, // 查看大图弹窗
      isDragging: false, // 拖拽状态
      
      // 加载状态
      isLoadingConfig: false,
      isLoadingSessions: false,
      
      // SSE相关
      sse: null,
      currentStatus: '',
      hasError: false,
      aiContent: '',
      targetDialogue: null
    }
  },
  
  computed: {
    // 当前登录用户 - 从 store 获取，确保数据一致性
    currentUser() {
      return this.$store.getters.user || {}
    },
    
    // 固定策略枚举（中文标签）
    emotionStrategyRuleOptions () {
      return this.strategyOptions && this.strategyOptions.emotion || []
    },
    conflictStrategyRuleOptions () {
      return this.strategyOptions && this.strategyOptions.conflict || []
    },
    questionFocusStrategyRuleOptions () {
      return this.strategyOptions && this.strategyOptions.question_focus || []
    },
    
    // 是否有对话正在重新生成
    isRegenerating() {
      return this.dialogues.some(d => d.regenerating)
    },
    
    // 是否可以发送消息（不再要求字数限制必选）
    canSendMessage() {
      return (
        this.userInput.trim() &&
        !this.isGenerating &&
        !this.isRegenerating
      )
    },
    
    // 输入框提示文本
    inputPlaceholder() {
      if (this.isRegenerating) {
        return 'AI正在重新生成回复，请稍候...'
      }
      return '输入您的问题或困扰... (Enter发送 / Shift+Enter换行 / 拖拽或粘贴图片识别 / 默认30-99字)'
    },
    
    // 会话状态
    sessionStatusText() {
      if (!this.currentSession) return ''
      return this.currentSession.status === 20 ? '进行中' : '已完成'
    },
    sessionStatusColor() {
      if (!this.currentSession) return 'default'
      return this.currentSession.status === 20 ? 'success' : 'default'
    }
  },
  
  watch: {
  },
  
  methods: {
    // 判断是否为最后一条对话（用于仅对最后一条AI消息显示“重新生成”）
    isLastDialogue(dialogue) {
      if (!dialogue) return false
      const len = this.dialogues && this.dialogues.length || 0
      if (!len) return false
      const last = this.dialogues[len - 1]
      return last && last.id === dialogue.id
    },
    // 切换配置面板
    toggleConfigPanel() {
      this.showConfigPanel = !this.showConfigPanel
    },
    
    // ==================== 图片上传相关 ====================
    
    // 监听拖拽进入
    handleDragEnter(e) {
      e.preventDefault()
      e.stopPropagation()
      this.isDragging = true
    },
    
    // 监听拖拽经过
    handleDragOver(e) {
      e.preventDefault()
      e.stopPropagation()
    },
    
    // 监听拖拽离开
    handleDragLeave(e) {
      e.preventDefault()
      e.stopPropagation()
      // 只有当离开整个拖拽区域时才重置状态
      if (e.target === e.currentTarget) {
        this.isDragging = false
      }
    },
    
    // 监听拖拽放下
    async handleDrop(e) {
      e.preventDefault()
      e.stopPropagation()
      this.isDragging = false
      
      const files = e.dataTransfer.files
      if (files.length > 0) {
        await this.handleImageUpload(files[0])
      }
    },
    
    // 处理图片上传
    async handleImageUpload(file) {
      // 验证文件类型
      if (!file.type.startsWith('image/')) {
        this.$Message.error('请上传图片文件')
        return
      }
      
      // 如果已有图片，先清除
      if (this.uploadedImage) {
        this.uploadedImage = null
      }
      
      // 设置上传中状态
      this.uploadedImage = {
        media_id: null,
        url: null,
        status: 'uploading',
        text: null,
        error: null
      }
      
      try {
        // 仅当文件大于 500KB 时进行压缩
        let uploadFile = file
        if (file && file.size && file.size > 500 * 1024) {
          try {
            uploadFile = await new Promise((resolve, reject) => {
              new Compressor(file, {
                quality: 0.6,
                maxHeight: 800,
                maxWidth: 800,
                success (result) {
                  resolve(new File([result], file.name || 'image.jpg', { type: result.type }))
                },
                error: reject
              })
            })
          } catch (compressError) {
            console.warn('图片压缩失败，使用原图:', compressError)
            // 压缩失败时使用原图继续上传
          }
        }
        
        // 上传到 media 接口
        const formData = new FormData()
        formData.append('image', uploadFile)  // 注意：后端字段名是 image 不是 file
        
        const response = await this.$http.post('/media', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        if (response && response.success && response.data) {
          // 上传成功，更新状态
          this.uploadedImage.media_id = response.data.id
          this.uploadedImage.url = response.data.url
          this.uploadedImage.status = 'recognizing'
          
          // 调用 OCR 识别
          await this.recognizeImageText(response.data.id)
        } else {
          this.uploadedImage.status = 'failed'
          this.uploadedImage.error = response.message || '上传失败'
          this.$Message.error('图片上传失败')
        }
      } catch (error) {
        console.error('图片上传失败:', error)
        this.uploadedImage.status = 'failed'
        this.uploadedImage.error = '上传失败，请重试'
        this.$Message.error('图片上传失败，请重试')
      }
    },
    
    // OCR 识别图片文字
    async recognizeImageText(mediaId) {
      try {
        const response = await this.$http.post('/web/counseling/ocr', {
          media_id: mediaId
        })
        
        if (response && response.success && response.data) {
          // 识别成功
          this.uploadedImage.status = 'success'
          this.uploadedImage.text = response.data.text
          
          // 清空输入框，填入识别的文字
          this.userInput = response.data.text
          
          this.$Message.success('图片识别成功')
        } else {
          this.uploadedImage.status = 'failed'
          this.uploadedImage.error = response.message || '识别失败'
          this.$Message.error('图片识别失败')
        }
      } catch (error) {
        console.error('OCR识别失败:', error)
        this.uploadedImage.status = 'failed'
        this.uploadedImage.error = '识别失败，请重试'
        this.$Message.error('图片识别失败，请重试')
      }
    },
    
    // 删除已上传的图片
    removeUploadedImage() {
      this.uploadedImage = null
      // 不清空输入框内容
    },
    
    // 查看大图
    viewImageFullScreen() {
      if (this.uploadedImage && this.uploadedImage.url) {
        this.imagePreviewModal = true
      }
    },
    
    // 查看对话中的图片
    viewDialogueImage(attachment) {
      if (!attachment || !attachment.url) return
      // 临时设置到 uploadedImage 用于弹窗显示
      const tempImage = this.uploadedImage
      this.uploadedImage = {
        media_id: attachment.id,
        url: attachment.url,
        status: 'success',
        text: null,
        error: null
      }
      this.imagePreviewModal = true
      
      // 关闭弹窗后恢复原来的图片状态
      const unwatch = this.$watch('imagePreviewModal', (newVal) => {
        if (!newVal) {
          this.uploadedImage = tempImage
          unwatch()
        }
      })
    },
    
    // ==================== 配置加载 ====================
    
    // 加载配置选项
    async loadConfigs() {
      this.isLoadingConfig = true
      try {
        // 仅加载字数限制
        const wordLimitsRes = await this.$http.get('/web/counseling/word-limits')
        
        if (wordLimitsRes && wordLimitsRes.success) {
          this.wordLimits = wordLimitsRes.data
          // 默认选中第二个字数限制（通常是标准字数）
          if (this.wordLimits.length > 1) {
            this.selectedWordLimit = this.wordLimits[1].id
          } else if (this.wordLimits.length > 0) {
            this.selectedWordLimit = this.wordLimits[0].id
          }
        }

        // 加载三类策略规则
        this.strategyOptions = { emotion: [], conflict: [], question_focus: [] }
        const [emoRes, confRes, qfRes] = await Promise.all([
          this.$http.get('/web/counseling/strategy-rules', { params: { type: 10, page: 1, per_page: 1000 } }),
          this.$http.get('/web/counseling/strategy-rules', { params: { type: 20, page: 1, per_page: 1000 } }),
          this.$http.get('/web/counseling/strategy-rules', { params: { type: 30, page: 1, per_page: 1000 } })
        ])
        if (emoRes && emoRes.success) this.strategyOptions.emotion = emoRes.rows || []
        if (confRes && confRes.success) this.strategyOptions.conflict = confRes.rows || []
        if (qfRes && qfRes.success) this.strategyOptions.question_focus = qfRes.rows || []
      } catch (error) {
        console.error('加载配置失败:', error)
        this.$Message.error('加载配置失败，请刷新重试')
      } finally {
        this.isLoadingConfig = false
      }
    },
    
    // 加载会话历史
    async loadSessionHistory() {
      this.isLoadingSessions = true
      try {
        const response = await this.$http.get('/web/counseling/sessions', {
          params: {
            page: 1,
            per_page: 50
          }
        })
        
        console.log('会话历史响应:', response)
        
        if (response && response.success) {
          // 分页接口返回格式：{success: true, rows: [...], pagination: {...}}
          // axios拦截器已经处理，直接访问response.rows
          this.sessionHistory = response.rows || []
          console.log('加载的会话历史:', this.sessionHistory)
        }
      } catch (error) {
        console.error('加载会话历史失败:', error)
        this.$Message.error('加载会话历史失败')
      } finally {
        this.isLoadingSessions = false
      }
    },
    
    // 准备新会话（不立即创建，等用户发送第一条消息时再创建）
    createNewSession() {
      // 重置当前会话状态
      this.currentSession = null
      this.dialogues = []
      this.currentRound = 1
      this.userInput = ''
      
          this.$Message.success('请输入您的问题开始咨询')
      
      // 聚焦输入框
      this.$nextTick(() => {
        if (this.$refs.chatInput) {
          this.$refs.chatInput.focus()
        }
      })
    },
    
    // 实际创建会话（在发送第一条消息时调用）
    async createSessionOnFirstMessage() {
      try {
        const response = await this.$http.post('/web/counseling/sessions', {
          title: `咨询会话 ${moment().format('MM-DD HH:mm')}`
        })
        
        if (response && response.success && response.data) {
          const newSession = response.data
          this.sessionHistory.unshift(newSession)
          this.currentSession = newSession
          return newSession
        } else {
          this.$Message.error(response.message || '创建会话失败')
          return null
        }
      } catch (error) {
        console.error('创建会话失败:', error)
        this.$Message.error('创建会话失败，请重试')
        return null
      }
    },
    
    // 选择会话
    async selectSession(session) {
      try {
        const response = await this.$http.get(`/web/counseling/sessions/${session.id}`)
        
        if (response && response.success && response.data) {
          this.currentSession = response.data
          // 为每个对话初始化 thinkingExpanded 属性（历史对话默认折叠）
          this.dialogues = (response.data.dialogues || []).map(dialogue => ({
            ...dialogue,
            thinkingExpanded: false  // 历史对话的思考过程默认折叠
          }))
          this.currentRound = this.dialogues.length + 1
          this.$Message.info(`已切换到：${session.title}`)
          
          // 滚动到底部并聚焦输入框
          this.$nextTick(() => {
            this.scrollToBottom()
            // 聚焦输入框，方便用户继续对话
            if (this.$refs.chatInput) {
              this.$refs.chatInput.focus()
            }
          })
        } else {
          this.$Message.error(response.message || '加载会话详情失败')
        }
      } catch (error) {
        console.error('加载会话详情失败:', error)
        this.$Message.error('加载会话详情失败')
      }
    },
    
    // 刷新当前会话的对话记录
    async refreshCurrentSession() {
      if (!this.currentSession) return
      
      try {
        const response = await this.$http.get(`/web/counseling/sessions/${this.currentSession.id}`)
        
        if (response && response.success && response.data) {
          this.currentSession = response.data
          // 保持现有对话的 thinkingExpanded 状态，新对话默认折叠
          const oldDialogues = this.dialogues
          this.dialogues = (response.data.dialogues || []).map(dialogue => {
            const oldDialogue = oldDialogues.find(d => d.id === dialogue.id)
            return {
              ...dialogue,
              thinkingExpanded: oldDialogue ? oldDialogue.thinkingExpanded : false
            }
          })
          this.currentRound = this.dialogues.length + 1
          console.log('会话对话记录已刷新')
        }
      } catch (error) {
        console.error('刷新会话对话记录失败:', error)
      }
    },
    
    // 会话操作
    handleSessionAction(action, session) {
      if (action === 'rename') {
        let newTitle = session.title
        this.$Modal.confirm({
          title: '重命名会话',
          render: (h) => {
            return h('Input', {
              props: {
                value: session.title,
                autofocus: true,
                placeholder: '输入新标题'
              },
              on: {
                input: (val) => {
                  newTitle = val
                }
              }
            })
          },
          onOk: async () => {
            try {
              const response = await this.$http.put(`/web/counseling/sessions/${session.id}`, {
                title: newTitle
              })
              
              if (response && response.success) {
                session.title = newTitle
                if (this.currentSession && this.currentSession.id === session.id) {
                  this.currentSession.title = newTitle
                }
                this.$Message.success('重命名成功')
              } else {
                this.$Message.error(response.message || '重命名失败')
              }
            } catch (error) {
              console.error('重命名失败:', error)
              this.$Message.error('重命名失败，请重试')
            }
          }
        })
      } else if (action === 'delete') {
        this.$Modal.confirm({
          title: '确认删除',
          content: `确定要删除会话"${session.title}"吗？删除后无法恢复。`,
          okText: '删除',
          okType: 'error',
          onOk: async () => {
            try {
              const response = await this.$http.delete(`/web/counseling/sessions/${session.id}`)
              
              if (response && response.success) {
                const index = this.sessionHistory.indexOf(session)
                if (index > -1) {
                  this.sessionHistory.splice(index, 1)
                }
                if (this.currentSession && this.currentSession.id === session.id) {
                  this.currentSession = null
                  this.dialogues = []
                }
                this.$Message.success('删除成功')
              } else {
                this.$Message.error(response.message || '删除失败')
              }
            } catch (error) {
              console.error('删除失败:', error)
              this.$Message.error('删除失败，请重试')
            }
          }
        })
      }
    },
    
    // 发送消息（使用SSE流式响应）
    async sendMessage() {
      if (!this.canSendMessage) {
        return
      }
      
      const userQuestion = this.userInput.trim()
      const attachmentSnapshot = this.uploadedImage ? { ...this.uploadedImage } : null
      
      this.userInput = ''
      this.isGenerating = true
      
      // 立即添加临时对话记录（用于显示用户问题和加载状态）
      const tempDialogue = {
        id: `temp_${Date.now()}`,
        user_question: userQuestion,
        attachment: attachmentSnapshot ? { url: attachmentSnapshot.url } : null,
        ai_response: '',  // 初始为空，SSE会逐步填充
        thinking_content: '',  // 思考过程（流式累积）
        thinkingExpanded: true,  // 思考过程默认展开
        loading: true,
        created_at: new Date().toISOString()
      }
      
      this.dialogues.push(tempDialogue)
      
      // 滚动到底部
      this.$nextTick(() => {
        this.scrollToBottom()
      })
      
      try {
        // 如果没有当前会话，先创建一个新会话
        if (!this.currentSession) {
          const newSession = await this.createSessionOnFirstMessage()
          if (!newSession) {
            this.dialogues.pop()
            this.userInput = userQuestion
            this.isGenerating = false
            return
          }
        }
        
        // 开始SSE流式响应
        this.startSSE(userQuestion, attachmentSnapshot, tempDialogue)
        
      } catch (error) {
        console.error('发送消息失败:', error)
        
        const tempIndex = this.dialogues.findIndex(d => d.id === tempDialogue.id)
        if (tempIndex !== -1) {
          this.dialogues.splice(tempIndex, 1)
        }
        
        this.$Message.error('AI生成失败，请重试')
        this.userInput = userQuestion
        this.isGenerating = false
      }
    },
    
    // 启动SSE连接
    startSSE(userQuestion, attachmentSnapshot, tempDialogue) {
      // 重置状态
      this.hasError = false
      this.aiContent = ''
      
      // 关闭之前的SSE连接
      if (this.sse) {
        this.sse.close()
      }
      
      // 构建请求参数（不传字数限制，使用后端默认30-99字）
      const params = {
        session_id: this.currentSession.id,
        user_question: userQuestion,
        attachment_media_id: this.uploadedImage && this.uploadedImage.media_id ? this.uploadedImage.media_id : null,
        round_number: this.currentRound,
        emotion_rule_id: this.selectedEmotionRuleId || null,
        conflict_rule_id: this.selectedConflictRuleId || null,
        question_focus_rule_id: this.selectedQuestionFocusRuleId || null
      }
      
      // 创建SSE连接
      this.sse = new SSE('/v1/web/counseling/dialogues', {
        headers: {
          'Content-Type': 'application/json',
          'source': 'web',
          'X-CSRF-TOKEN': getCookie('mingshu_auth_csrf_cookie')
        },
        method: 'POST',
        payload: JSON.stringify(params)
      })
      
      // 处理SSE消息
      this.sse.onmessage = (e) => {
        if (this.hasError) {
          return
        }
        
        let data = JSON.parse(e.data)
        console.log('SSE消息:', data)
        
        if (!data.status) {
          this.sse.close()
          this.isGenerating = false
          return
        }
        
        this.currentStatus = data.status
        
        // 处理不同的状态
        if (data.status === 'error') {
          // 错误处理
          this.hasError = true
          this.$Message.error(data.message || '生成失败，请重试')
          this.sse.close()
          this.isGenerating = false
          
          // 移除临时对话
          const tempIndex = this.dialogues.findIndex(d => d.id === tempDialogue.id)
          if (tempIndex !== -1) {
            this.dialogues.splice(tempIndex, 1)
          }
          
          // 恢复用户输入
          this.userInput = userQuestion
          return
        }
        
        if (data.status === 'start') {
          // 开始生成
          console.log('开始生成AI回复')
        } else if (data.status === 'ai_thinking') {
          // AI思考过程（豆包1.6深度思考特性）
          if (data.type === 'thinking' && data.content) {
            const tempIndex = this.dialogues.findIndex(d => d.id === tempDialogue.id)
            if (tempIndex !== -1) {
              const currentThinking = this.dialogues[tempIndex].thinking_content || ''
              this.$set(this.dialogues[tempIndex], 'thinking_content', currentThinking + data.content)
              // 确保思考过程显示时是展开的
              this.$set(this.dialogues[tempIndex], 'thinkingExpanded', true)
            }
            
            // 滚动到底部
            this.$nextTick(() => {
              this.scrollToBottom()
            })
          }
        } else if (data.status === 'ai_response') {
          // AI流式响应
          if (data.type === 'input' && data.content) {
            this.aiContent += data.content
            
            // 更新临时对话中的AI回复（使用$set确保响应式更新）
            const tempIndex = this.dialogues.findIndex(d => d.id === tempDialogue.id)
            if (tempIndex !== -1) {
              this.$set(this.dialogues[tempIndex], 'ai_response', this.aiContent)
              // 开始生成回复时，自动折叠思考过程
              if (this.dialogues[tempIndex].thinking_content && this.dialogues[tempIndex].thinkingExpanded) {
                this.$set(this.dialogues[tempIndex], 'thinkingExpanded', false)
              }
            }
            
            // 滚动到底部
            this.$nextTick(() => {
              this.scrollToBottom()
            })
          }
        } else if (data.status === 'saving') {
          // 保存中
          console.log('保存对话记录中...')
        } else if (data.status === 'done') {
          // 完成
          this.isGenerating = false
          this.sse.close()
          
          // 更新临时对话为完成状态（使用$set确保响应式更新）
          const tempIndex = this.dialogues.findIndex(d => d.id === tempDialogue.id)
          if (tempIndex !== -1) {
            this.$set(this.dialogues[tempIndex], 'id', data.id)  // 使用真实ID
            this.$set(this.dialogues[tempIndex], 'loading', false)
          }
          
          this.currentRound++
          
          // 更新会话对话数
          if (this.currentSession) {
            this.currentSession.total_dialogues = (this.currentSession.total_dialogues || 0) + 1
          }
          
          // 清空图片
          this.uploadedImage = null
          
          // 重置策略选择与开关
          this.selectedEmotionStrategy = ''
          this.selectedEventConflictStrategy = ''
          this.selectedQuestionFocusStrategy = ''
          this.openQuestions = false
          
          // 刷新当前会话的对话记录
          this.refreshCurrentSession()
          
          // 滚动到底部并聚焦输入框
          this.$nextTick(() => {
            this.scrollToBottom()
            // 聚焦输入框，方便用户继续输入
            if (this.$refs.chatInput) {
              this.$refs.chatInput.focus()
            }
          })
          
        }
      }
      
      // 错误处理
      this.sse.onerror = (e) => {
        console.error('SSE错误:', e)
        this.hasError = true
        this.$Message.error('连接服务器出错')
        this.sse.close()
        this.isGenerating = false
        
        // 移除临时对话
        const tempIndex = this.dialogues.findIndex(d => d.id === tempDialogue.id)
        if (tempIndex !== -1) {
          this.dialogues.splice(tempIndex, 1)
        }
        
        // 恢复用户输入
        this.userInput = userQuestion
      }
      
      // 开始流式传输
      this.sse.stream()
    },
    
    // 快捷键处理
    handleKeyDown(e) {
      // Enter 直接发送，Shift+Enter 换行
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        if (this.canSendMessage) {
          this.sendMessage()
        }
      }
      // Shift+Enter 允许换行（textarea默认行为，不需要处理）
    },
    
    // 处理粘贴事件（支持粘贴图片）
    async handlePaste(e) {
      // 检查剪贴板中是否有文件
      const clipboardData = e.clipboardData || window.clipboardData
      if (!clipboardData) return
      
      const items = clipboardData.items
      if (!items) return
      
      // 遍历剪贴板项，查找图片
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        
        // 如果是图片类型
        if (item.type.indexOf('image') !== -1) {
          // 阻止默认粘贴行为
          e.preventDefault()
          
          // 获取图片文件
          const file = item.getAsFile()
          if (file) {
            this.$Message.info('检测到图片，开始上传...')
            // 调用现有的图片上传方法
            await this.handleImageUpload(file)
          }
          
          // 找到图片后就跳出循环
          break
        }
      }
    },
    
    // 滚动到底部
    scrollToBottom() {
      const container = this.$refs.messageContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },
    
    // 时间格式化
    formatTime(time) {
      return moment(time).format('HH:mm')
    },
    
    formatDate(time) {
      return moment(time).format('MM-DD HH:mm')
    },
    
    // 复制消息到剪贴板
    async copyMessage(text) {
      if (!text) {
        this.$Message.warning('没有内容可复制')
        return
      }
      
      try {
        // 使用现代剪贴板 API
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(text)
          this.$Message.success('已复制到剪贴板')
        } else {
          // 降级方案：使用传统方法
          const textarea = document.createElement('textarea')
          textarea.value = text
          textarea.style.position = 'fixed'
          textarea.style.opacity = '0'
          document.body.appendChild(textarea)
          textarea.select()
          
          try {
            document.execCommand('copy')
            this.$Message.success('已复制到剪贴板')
          } catch (err) {
            this.$Message.error('复制失败，请手动复制')
          } finally {
            document.body.removeChild(textarea)
          }
        }
      } catch (error) {
        console.error('复制失败:', error)
        this.$Message.error('复制失败，请手动复制')
      }
    },
    
    // 统计字数
    getWordCount(text) {
      if (!text) return 0
      // 去除所有空白字符后计算字数
      return text.replace(/\s/g, '').length
    },
    
    // 切换思考过程的展开/折叠
    toggleThinking(dialogue) {
      this.$set(dialogue, 'thinkingExpanded', !dialogue.thinkingExpanded)
    },
    
    // 打开重生成配置弹窗
    openRegenerateModal(dialogue) {
      if (dialogue.regenerating) return
      // 预填充为上次该对话使用过的策略与开关状态
      this.selectedEmotionRuleId = (dialogue && dialogue.emotion_rule && dialogue.emotion_rule.id) || null
      this.selectedConflictRuleId = (dialogue && dialogue.conflict_rule && dialogue.conflict_rule.id) || null
      this.selectedQuestionFocusRuleId = (dialogue && dialogue.question_focus_rule && dialogue.question_focus_rule.id) || null
      this.openQuestions = !!(dialogue && dialogue.open_questions)
      // 同步字数限制为该对话的字数设置
      if (dialogue && dialogue.word_limit && dialogue.word_limit.id) {
        this.selectedWordLimit = dialogue.word_limit.id
      }
      this.targetDialogue = dialogue
      this.regenerateModalVisible = true
    },

    // 确认重生成
    confirmRegenerate() {
      const dlg = this.targetDialogue
      this.regenerateModalVisible = false
      if (!dlg) return
      this.startRegenerateSSE(dlg)
      this.targetDialogue = null
    },

    // 取消重生成
    cancelRegenerate() {
      this.regenerateModalVisible = false
      this.targetDialogue = null
    },
    
    // 启动重新生成的SSE连接
    startRegenerateSSE(dialogue) {
      // 重置状态
      this.hasError = false
      this.aiContent = ''
      
      // 设置重新生成状态（使用$set确保响应式）
      this.$set(dialogue, 'regenerating', true)
      
      // 重置AI回复内容和思考内容（同时清空 reasoning_content 和 thinking_content）
      this.$set(dialogue, 'ai_response', '')
      this.$set(dialogue, 'reasoning_content', '')  // 清空推理内容
      this.$set(dialogue, 'thinking_content', '')  // 清空思考内容
      this.$set(dialogue, 'thinkingExpanded', true)  // 默认展开思考过程
      this.$set(dialogue, 'scene', null)
      this.$set(dialogue, 'strategy', null)
      this.$set(dialogue, 'action', null)
      
      // 关闭之前的SSE连接（如果有）
      if (this.sse) {
        this.sse.close()
      }
      
      // 构建请求参数（使用当前选择的配置，允许用户调整配置后重新生成）
      const params = {
        word_limit_id: this.selectedWordLimit,
        emotion_rule_id: this.selectedEmotionRuleId || null,
        conflict_rule_id: this.selectedConflictRuleId || null,
        question_focus_rule_id: this.selectedQuestionFocusRuleId || null,
        open_questions: !!this.openQuestions
      }
      
      // 创建SSE连接（与原始SSE保持一致的配置）
      this.sse = new SSE(`/v1/web/counseling/dialogues/${dialogue.id}/regenerate`, {
        headers: {
          'Content-Type': 'application/json',
          'source': 'web',
          'X-CSRF-TOKEN': getCookie('mingshu_auth_csrf_cookie')
        },
        method: 'POST',
        payload: JSON.stringify(params)
      })
      
      // 处理SSE消息（与原始SSE保持一致的处理逻辑）
      this.sse.onmessage = (e) => {
        if (this.hasError) {
          return
        }
        
        let data = JSON.parse(e.data)
        console.log('重新生成SSE消息:', data)
        
        if (!data.status) {
          this.sse.close()
          this.$set(dialogue, 'regenerating', false)
          return
        }
        
        this.currentStatus = data.status
        
        // 处理不同的状态
        if (data.status === 'error') {
          // 错误处理
          this.hasError = true
          this.$Message.error(data.message || '重新生成失败，请重试')
          this.sse.close()
          this.$set(dialogue, 'regenerating', false)
          return
        }
        
        if (data.status === 'start') {
          // 开始生成
          console.log('开始重新生成AI回复')
        } else if (data.status === 'ai_thinking') {
          // AI思考过程（豆包1.6深度思考特性）
          if (data.type === 'thinking' && data.content) {
            const currentThinking = dialogue.thinking_content || ''
            this.$set(dialogue, 'thinking_content', currentThinking + data.content)
            // 确保思考过程显示时是展开的
            this.$set(dialogue, 'thinkingExpanded', true)
            
            // 滚动到底部
            this.$nextTick(() => {
              this.scrollToBottom()
            })
          }
        } else if (data.status === 'ai_response') {
          // AI流式响应
          if (data.type === 'input' && data.content) {
            this.aiContent += data.content
            
            // 更新对话中的AI回复（使用$set确保响应式更新）
            this.$set(dialogue, 'ai_response', this.aiContent)
            // 开始生成回复时，自动折叠思考过程
            if (dialogue.thinking_content && dialogue.thinkingExpanded) {
              this.$set(dialogue, 'thinkingExpanded', false)
            }
            
            // 滚动到底部
            this.$nextTick(() => {
              this.scrollToBottom()
            })
          }
        } else if (data.status === 'saving') {
          // 保存中
          console.log('保存更新的回复中...')
        } else if (data.status === 'done') {
          // 完成
          this.$set(dialogue, 'regenerating', false)
          this.sse.close()
          this.$Message.success('重新生成完成')
          
          // 重置策略选择与开关
          this.selectedEmotionRuleId = null
          this.selectedConflictRuleId = null
          this.selectedQuestionFocusRuleId = null
          this.openQuestions = false
          
          // 刷新当前会话的对话记录
          this.refreshCurrentSession()
          
          // 滚动到底部
          this.$nextTick(() => {
            this.scrollToBottom()
          })
        }
      }
      
      // 错误处理（与原始SSE保持一致）
      this.sse.onerror = (e) => {
        console.error('重新生成SSE错误:', e)
        this.hasError = true
        this.$Message.error('连接服务器出错')
        this.sse.close()
        this.$set(dialogue, 'regenerating', false)
      }
      
      // 开始流式传输
      this.sse.stream()
    }
  },
  
  async mounted() {
    // 确保认证状态和用户信息已加载
    await this.$auth.ready()
    
    // 刷新用户信息（确保头像等信息最新）
    if (this.$auth.check()) {
      await this.$store.dispatch('refreshUser')
    }
    
    // 初始化：加载配置选项
    await this.loadConfigs()
    
    // 加载会话历史
    await this.loadSessionHistory()
    
    // 不自动创建会话，等用户发送第一条消息时再创建
    
    // 页面加载完成后自动聚焦输入框
    this.$nextTick(() => {
      if (this.$refs.chatInput) {
        this.$refs.chatInput.focus()
      }
    })
  },
  
  beforeDestroy() {
    // 组件销毁前关闭SSE连接，防止内存泄漏
    if (this.sse) {
      this.sse.close()
      this.sse = null
    }
  }
}
</script>

<style lang="less" scoped>
// 导入设计系统变量
@import '../styles/variables.less';

.counseling-container {
  height: ~"calc(100vh - 64px)";
  // 心理咨询主题：深紫蓝渐变，温暖而专业
  background: linear-gradient(135deg, #1a1033 0%, #2d1b4e 30%, #1e3a5f 70%, #1a2332 100%);
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

// 心理主题网格 - 象征思维连接
.mind-grid {
  position: absolute;
  width: 100%;
  height: 100%;
  background-image: 
    radial-gradient(circle at 20% 30%, rgba(138, 101, 255, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(236, 72, 153, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 50% 50%, rgba(6, 182, 212, 0.06) 0%, transparent 70%),
    linear-gradient(90deg, rgba(138, 101, 255, 0.03) 1px, transparent 1px),
    linear-gradient(0deg, rgba(138, 101, 255, 0.03) 1px, transparent 1px);
  background-size: 
    100% 100%,
    100% 100%,
    100% 100%,
    6.25rem 6.25rem,
    6.25rem 6.25rem;
  animation: mindPulse 8s ease-in-out infinite;
}

@keyframes mindPulse {
  0%, 100% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
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
    box-shadow: 0 0 2.5rem rgba(138, 101, 255, 0.3),
                inset 0 0 2rem rgba(255, 255, 255, 0.08);

    &.shape-1 {
      width: 8rem;
      height: 8rem;
      // 温暖的紫粉渐变 - 象征心理温暖
      background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
      top: 8%;
      left: 12%;
      animation-duration: 28s;
    }

    &.shape-2 {
      width: 6rem;
      height: 6rem;
      // 青紫渐变 - 象征冷静思考
      background: linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%);
      top: 55%;
      left: 85%;
      animation-delay: -6s;
      animation-duration: 32s;
    }

    &.shape-3 {
      width: 10rem;
      height: 10rem;
      // 深紫蓝渐变 - 象征专业深度
      background: linear-gradient(135deg, #6366f1 0%, #3b82f6 100%);
      top: 75%;
      left: 18%;
      animation-delay: -12s;
      animation-duration: 38s;
    }

    &.shape-4 {
      width: 4.5rem;
      height: 4.5rem;
      // 柔和粉紫 - 象征关怀
      background: linear-gradient(135deg, #f472b6 0%, #c084fc 100%);
      top: 22%;
      left: 68%;
      animation-delay: -18s;
      animation-duration: 24s;
    }

    &.shape-5 {
      width: 7rem;
      height: 7rem;
      // 青绿渐变 - 象征成长治愈
      background: linear-gradient(135deg, #14b8a6 0%, #06b6d4 100%);
      top: 48%;
      left: 8%;
      animation-delay: -24s;
      animation-duration: 30s;
    }

    &.shape-6 {
      width: 5.5rem;
      height: 5.5rem;
      // 紫蓝渐变 - 象征智慧引导
      background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
      top: 35%;
      left: 88%;
      animation-delay: -30s;
      animation-duration: 35s;
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

.light-particles {
  position: absolute;
  width: 100%;
  height: 100%;

  .particle {
    position: absolute;
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    opacity: 0;
    animation: sparkle 4s infinite ease-in-out;
    
    // 不同粒子使用心理咨询主题的温暖色彩
    &.particle-1 { 
      top: 12%; 
      left: 28%; 
      animation-delay: 0s;
      background: #a78bfa;
      box-shadow: 0 0 1rem #a78bfa, 0 0 2rem #a78bfa;
    }
    &.particle-2 { 
      top: 38%; 
      left: 72%; 
      animation-delay: 0.6s;
      background: #ec4899;
      box-shadow: 0 0 1rem #ec4899, 0 0 2rem #ec4899;
    }
    &.particle-3 { 
      top: 62%; 
      left: 42%; 
      animation-delay: 1.2s;
      background: #06b6d4;
      box-shadow: 0 0 1rem #06b6d4, 0 0 2rem #06b6d4;
    }
    &.particle-4 { 
      top: 82%; 
      left: 18%; 
      animation-delay: 1.8s;
      background: #8b5cf6;
      box-shadow: 0 0 1rem #8b5cf6, 0 0 2rem #8b5cf6;
    }
    &.particle-5 { 
      top: 28%; 
      left: 82%; 
      animation-delay: 2.4s;
      background: #f472b6;
      box-shadow: 0 0 1rem #f472b6, 0 0 2rem #f472b6;
    }
    &.particle-6 { 
      top: 72%; 
      left: 62%; 
      animation-delay: 3s;
      background: #14b8a6;
      box-shadow: 0 0 1rem #14b8a6, 0 0 2rem #14b8a6;
    }
    &.particle-7 { 
      top: 48%; 
      left: 22%; 
      animation-delay: 1.5s;
      background: #c084fc;
      box-shadow: 0 0 1rem #c084fc, 0 0 2rem #c084fc;
    }
    &.particle-8 { 
      top: 52%; 
      left: 88%; 
      animation-delay: 2.1s;
      background: #6366f1;
      box-shadow: 0 0 1rem #6366f1, 0 0 2rem #6366f1;
    }
  }
}

@keyframes sparkle {
  0%, 100% {
    opacity: 0;
    transform: scale(0.3) translateY(0);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.2) translateY(-0.625rem);
  }
}

// 主内容区域（三栏布局）
.content-wrapper {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

// 左侧边栏（固定宽度）
.sidebar {
  width: 16rem;
  flex-shrink: 0;
  background: rgba(26, 26, 46, 0.5);
  backdrop-filter: blur(1.25rem);
  display: flex;
  flex-direction: column;
  
  .sidebar-header {
    padding: 1rem;
    
    .new-chat-btn {
      background: linear-gradient(45deg, @primary-color, @accent-color);
      border: none;
      font-weight: @font-weight-medium;
      border-radius: @border-radius-lg;
      
      &:hover {
        background: linear-gradient(45deg, @primary-dark, @primary-light);
        box-shadow: 0 0.25rem 0.75rem rgba(59, 130, 246, 0.3);
        transform: translateY(-1px);
      }
    }
  }
  
  .session-list {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
    
    .session-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem;
      margin-bottom: 0.5rem;
      border-radius: @border-radius-md;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid transparent;
      cursor: pointer;
      transition: all @transition-base;
      
      &:hover {
        background: rgba(59, 130, 246, 0.1);
        border-color: rgba(59, 130, 246, 0.3);
        
        .session-actions {
          opacity: 1;
        }
      }
      
      &.active {
        background: rgba(59, 130, 246, 0.15);
        border-color: @primary-color;
      }
      
      .session-icon {
        width: 2rem;
        height: 2rem;
        border-radius: 0.5rem;
        background: linear-gradient(45deg, @primary-color, @accent-color);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        
        .ivu-icon {
          font-size: 1rem;
          color: #FFFFFF;
        }
      }
      
      .session-info {
        flex: 1;
        min-width: 0;
        
        .session-title {
          font-size: 0.875rem;
          font-weight: @font-weight-medium;
          color: rgba(255, 255, 255, 0.9);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          margin-bottom: 0.125rem;
        }
        
        .session-meta {
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.5);
        }
      }
      
      .session-actions {
        opacity: 0;
        transition: opacity @transition-base;
        
        .more-icon {
          font-size: 1.25rem;
          color: rgba(255, 255, 255, 0.6);
          cursor: pointer;
          
          &:hover {
            color: #FFFFFF;
          }
        }
      }
    }
    
    .empty-state {
      text-align: center;
      padding: 3rem 1rem;
      color: rgba(255, 255, 255, 0.4);
      
      .ivu-icon {
        margin-bottom: 1rem;
        opacity: 0.5;
      }
      
      p {
        margin-bottom: 0.25rem;
      }
      
      .empty-hint {
        font-size: 0.75rem;
      }
    }
  }
}

// 中间对话区域（弹性宽度）
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(10, 10, 26, 0.2);
  position: relative;
  min-width: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  // 拖拽状态
  &.dragging {
    background: rgba(59, 130, 246, 0.1);
    border: 2px dashed @primary-color;
    
    &::after {
      content: '释放以上传图片';
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 1.5rem;
      font-weight: @font-weight-semibold;
      color: @primary-color;
      pointer-events: none;
      z-index: 1000;
      background: rgba(26, 26, 46, 0.95);
      padding: 1.5rem 3rem;
      border-radius: @border-radius-lg;
      box-shadow: 0 0.5rem 2rem rgba(59, 130, 246, 0.5);
    }
  }
  
  // 配置切换按钮（垂直居中）
  .config-toggle-btn {
    position: absolute;
    top: 50%;
    right: 0;
    transform: translateY(-50%);
    width: 3rem;
    height: 4rem;
    background: linear-gradient(135deg, @primary-color, @accent-color);
    border-radius: @border-radius-lg 0 0 @border-radius-lg;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 10;
    box-shadow: -0.25rem 0 0.75rem rgba(59, 130, 246, 0.3);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    
    .ivu-icon {
      font-size: 1.5rem;
      color: #FFFFFF;
      animation: rotate-pulse 2s ease-in-out infinite;
    }
    
    &:hover {
      right: -0.125rem;
      background: linear-gradient(135deg, @primary-light, @accent-color);
      box-shadow: -0.375rem 0 1rem rgba(59, 130, 246, 0.5);
      
      .ivu-icon {
        transform: scale(1.1);
      }
    }
    
    // 隐藏状态
    &.hidden {
      opacity: 0;
      pointer-events: none;
      transform: translateY(-50%) translateX(3rem);
    }
  }
  
  @keyframes rotate-pulse {
    0%, 100% {
      transform: rotate(0deg);
    }
    50% {
      transform: rotate(90deg);
    }
  }
  
  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 2rem 1.5rem 1.5rem;
    
    .welcome-screen {
      text-align: center;
      padding: 3rem 2rem;
      max-width: 40rem;
      margin: 0 auto;
      
      .welcome-icon {
        font-size: 4rem;
        margin-bottom: 1.5rem;
        filter: drop-shadow(0 0 1rem rgba(255, 255, 255, 0.3));
      }
      
      h3 {
        font-size: 1.5rem;
        font-weight: @font-weight-bold;
        color: #FFFFFF;
        margin-bottom: 0.75rem;
      }
      
      p {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.6);
        margin-bottom: 2rem;
      }
      
      .feature-cards {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        
        .feature-card {
          padding: 1.25rem;
          background: rgba(26, 26, 46, 0.6);
          border: 1px solid rgba(59, 130, 246, 0.2);
          border-radius: @border-radius-md;
          backdrop-filter: blur(1.25rem);
          
          .ivu-icon {
            font-size: 1.5rem;
            color: @primary-color;
            margin-bottom: 0.5rem;
          }
          
          span {
            display: block;
            font-size: 0.875rem;
            color: rgba(255, 255, 255, 0.8);
          }
        }
      }
    }
    
    .dialogue-item {
      max-width: 54rem;  // 比输入框(50rem)宽一点
      margin: 0 auto 2rem;
      padding: 0 1rem;
    }
    
    .message {
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1.5rem;
      max-width: 85%;  // 消息最大宽度85%
      width: fit-content;  // 宽度自适应内容
      
      .message-avatar {
        width: 2rem;
        height: 2rem;
        border-radius: 50%;
        background: rgba(59, 130, 246, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        overflow: hidden;  // 确保图片不溢出圆形
        
        .ivu-icon {
          font-size: 1rem;
          color: #FFFFFF;
        }
        
        .avatar-image {
          width: 100%;
          height: 100%;
          object-fit: cover;  // 图片填充整个容器
          border-radius: 50%;
        }
        
        &.user-avatar {
          background: rgba(59, 130, 246, 0.8);
        }
        
        &.ai-avatar {
          background: linear-gradient(45deg, @secondary-color, @primary-color);
          
          .ai-text {
            font-size: 1rem;
            font-weight: 600;
            color: #FFFFFF;
          }
        }
      }
      
      .message-bubble {
        flex: 0 1 auto;  // 自适应内容，不强制填充剩余空间
        max-width: 100%;  // 不超过父元素宽度
        
        // 消息中的图片
        .message-image {
          margin-bottom: 0.75rem;
          
          img {
            max-width: 12rem;
            max-height: 12rem;
            border-radius: @border-radius-md;
            cursor: pointer;
            transition: all @transition-base;
            box-shadow: 0 0.125rem 0.5rem rgba(0, 0, 0, 0.2);
            
            &:hover {
              transform: scale(1.05);
              box-shadow: 0 0.25rem 1rem rgba(0, 0, 0, 0.3);
            }
          }
        }
        
        .message-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.5rem;
          
          .ai-label {
            font-size: 0.75rem;
            font-weight: @font-weight-medium;
            color: rgba(255, 255, 255, 0.8);
            flex-shrink: 0;  // 防止被压缩
          }
          
          .config-tags {
            display: flex;
            gap: 0.25rem;
            flex-shrink: 1;  // 允许压缩
            min-width: 0;  // 允许flex子项缩小到内容以下
            
            // 为Tag设置最大宽度，防止挤压AI标签
            /deep/ .ivu-tag {
              max-width: 12rem;  // 最大宽度约96px
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }
          }
        }
        
        // 思考过程区域
        .thinking-section {
          margin-bottom: 0.75rem;
          background: rgba(138, 101, 255, 0.08);
          border: 1px solid rgba(138, 101, 255, 0.25);
          border-radius: @border-radius-md;
          overflow: hidden;
          transition: all @transition-base;
          
          .thinking-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.625rem 0.875rem;
            cursor: pointer;
            background: rgba(138, 101, 255, 0.05);
            transition: all @transition-base;
            user-select: none;
            
            &:hover {
              background: rgba(138, 101, 255, 0.12);
            }
            
            .ivu-icon:first-child {
              font-size: 1rem;
              color: rgba(138, 101, 255, 0.8);
              transition: transform @transition-base;
            }
            
            .thinking-label {
              display: flex;
              align-items: center;
              font-size: 0.8125rem;
              font-weight: @font-weight-medium;
              color: rgba(138, 101, 255, 0.9);
              flex: 1;
              
              .ivu-icon {
                color: rgba(255, 204, 0, 0.8);
              }
            }
            
            .thinking-status {
              display: flex;
              align-items: center;
              font-size: 0.75rem;
              color: rgba(138, 101, 255, 0.7);
            }
          }
          
          .thinking-content {
            padding: 0.5rem 0.875rem;
            background: rgba(26, 26, 46, 0.4);
            max-height: 20rem;
            overflow-y: auto;
            
            .thinking-text {
              font-size: 0.875rem;
              line-height: 1.6;
              color: rgba(255, 255, 255, 0.75);
              white-space: pre-wrap;
              word-break: break-word;
              font-family: @font-family-base;
              
              .typing-cursor {
                display: inline-block;
                width: 2px;
                height: 1em;
                background: rgba(138, 101, 255, 0.8);
                margin-left: 2px;
                vertical-align: text-bottom;
                animation: blink 1s infinite;
              }
            }
            
            // 自定义滚动条
            &::-webkit-scrollbar {
              width: 0.25rem;
            }
            
            &::-webkit-scrollbar-track {
              background: rgba(0, 0, 0, 0.1);
              border-radius: 0.125rem;
            }
            
            &::-webkit-scrollbar-thumb {
              background: rgba(138, 101, 255, 0.3);
              border-radius: 0.125rem;
              
              &:hover {
                background: rgba(138, 101, 255, 0.5);
              }
            }
          }
        }
        
        .message-content {
          background: rgba(26, 26, 46, 0.6);
          border: 1px solid rgba(59, 130, 246, 0.2);
          border-radius: @border-radius-md;
          padding: 0.875rem 1rem;
          color: rgba(255, 255, 255, 0.9);
          line-height: 1.6;
          font-size: 0.9375rem;
          backdrop-filter: blur(1.25rem);
          white-space: pre-wrap;
          word-break: break-word;
          
          // 只显示思考提示时，使用更紧凑的padding
          &.thinking-only {
            padding: 0.625rem 0.875rem;
            min-height: auto;
          }
          
          .thinking-hint {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: @primary-color;
            font-size: 0.875rem;
            line-height: 1.2;
            vertical-align: middle;
          }
          
          .typing-cursor {
            display: inline-block;
            width: 2px;
            height: 1em;
            background: @primary-color;
            margin-left: 2px;
            vertical-align: text-bottom;
            animation: blink 1s infinite;
          }
        }
        
        @keyframes blink {
          0%, 49% {
            opacity: 1;
          }
          50%, 100% {
            opacity: 0;
          }
        }
        
        .message-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 0.5rem;
          
          .message-time {
            font-size: 0.75rem;
            color: rgba(255, 255, 255, 0.4);
            
            .word-count {
              color: rgba(255, 255, 255, 0.5);
              font-weight: @font-weight-medium;
            }
          }
          
          .message-actions {
            display: flex;
            gap: 0.25rem;
          }
        }
      }
      
      &.user-message {
        flex-direction: row-reverse;  // 用户消息右对齐
        margin-left: auto;  // 推到右边
        
        .message-bubble {
          .message-content {
            background: rgba(59, 130, 246, 0.15);
            border-color: rgba(59, 130, 246, 0.3);
          }
        }
      }
      
      &.ai-message {
        margin-right: auto;  // AI消息左对齐
      }
    }
  }
  
  .chat-input-section {
    background: transparent;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    
    // 图片预览容器
    .image-preview-container {
      max-width: 50rem;
      width: 100%;
      
      .image-preview-wrapper {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      }
      
      .image-preview {
        position: relative;
        width: 10rem;
        height: 10rem;
        border-radius: @border-radius-lg;
        overflow: hidden;
        background: rgba(26, 26, 46, 0.8);
        border: 2px solid rgba(59, 130, 246, 0.3);
        transition: all @transition-base;
        
        &:hover {
          border-color: @primary-color;
          
          .image-actions {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        &.has-error {
          border-color: @error-color;
        }
        
        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        
        .image-placeholder {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          
          .ivu-icon {
            font-size: 3rem;
            color: rgba(255, 255, 255, 0.3);
          }
        }
        
        // 状态遮罩
        .status-overlay {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(26, 26, 46, 0.95);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          
          .status-text {
            font-size: 0.875rem;
            color: @primary-color;
            font-weight: @font-weight-medium;
          }
        }
        
        // 错误遮罩
        .error-overlay {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(255, 59, 48, 0.1);
          backdrop-filter: blur(0.25rem);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          
          .ivu-icon {
            font-size: 2rem;
            color: @error-color;
          }
          
          .error-text {
            font-size: 0.75rem;
            color: @error-color;
            text-align: center;
            padding: 0 0.5rem;
          }
        }
        
        // 成功标记
        .success-badge {
          position: absolute;
          top: 0.5rem;
          right: 0.5rem;
          
          .ivu-icon {
            font-size: 1.5rem;
            color: @success-color;
            filter: drop-shadow(0 0 0.25rem rgba(52, 199, 89, 0.5));
          }
        }
        
        // 操作按钮
        .image-actions {
          position: absolute;
          bottom: 0;
          left: 0;
          width: 100%;
          padding: 0.75rem;
          background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
          display: flex;
          gap: 0.5rem;
          justify-content: center;
          opacity: 0;
          transform: translateY(0.5rem);
          transition: all @transition-base;
        }
      }
      
      // 识别文字提示
      .recognized-text-hint {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.7);
        padding: 0.5rem 0.75rem;
        background: rgba(52, 199, 89, 0.1);
        border-radius: @border-radius-md;
        border: 1px solid rgba(52, 199, 89, 0.3);
        
        .ivu-icon {
          font-size: 1rem;
        }
      }
    }
    
    .input-wrapper {
      display: flex;
      gap: 0.875rem;
      align-items: flex-end;
      max-width: 50rem;
      width: 100%;
      
      /deep/ .chat-input {
        flex: 1;
        
        .ivu-input {
          background: rgba(26, 26, 46, 0.8);
          border: 1px solid rgba(59, 130, 246, 0.25);
          color: rgba(255, 255, 255, 0.9);
          resize: none;
          border-radius: @border-radius-lg;
          padding: 0.75rem 1rem;
          font-size: 0.9375rem;
          line-height: 1.5;
          transition: all @transition-base;
          min-height: 3.25rem;
          max-height: 12rem;
          
          &:focus {
            border-color: @primary-color;
            background: rgba(26, 26, 46, 0.95);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
          }
          
          &::placeholder {
            color: rgba(255, 255, 255, 0.4);
          }
          
          // 隐藏滚动条但保持滚动功能
          &::-webkit-scrollbar {
            width: 0.25rem;
          }
          
          &::-webkit-scrollbar-track {
            background: transparent;
          }
          
          &::-webkit-scrollbar-thumb {
            background: rgba(59, 130, 246, 0.3);
            border-radius: 0.125rem;
            
            &:hover {
              background: rgba(59, 130, 246, 0.5);
            }
          }
        }
      }
      
      .send-btn {
        width: 3.25rem;
        height: 3.25rem;
        padding: 0;
        background: linear-gradient(135deg, @primary-color, @accent-color);
        border: none;
        border-radius: 50%;
        transition: all @transition-base;
        flex-shrink: 0;
        
        .ivu-icon {
          font-size: 1.375rem;
        }
        
        &:hover:not(:disabled) {
          background: linear-gradient(135deg, @primary-light, @accent-color);
          box-shadow: 0 0.375rem 1rem rgba(59, 130, 246, 0.4);
          transform: scale(1.08);
        }
        
        &:active:not(:disabled) {
          transform: scale(1.02);
        }
        
        &:disabled {
          background: rgba(255, 255, 255, 0.1);
          opacity: 0.4;
          cursor: not-allowed;
        }
      }
    }
  }
}

// 右侧配置面板（固定宽度，flex布局）
.config-panel {
  width: 22rem;
  flex-shrink: 0;
  background: rgba(26, 26, 46, 0.95);
  backdrop-filter: blur(1.25rem);
  display: flex;
  flex-direction: column;
  
  .config-panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.5rem;
    border-bottom: 1px solid rgba(59, 130, 246, 0.2);
    
    h3 {
      font-size: 1.125rem;
      font-weight: @font-weight-semibold;
      color: #FFFFFF;
      margin: 0;
    }
    
    .close-btn {
      padding: 0.375rem;
      
      .ivu-icon {
        font-size: 1.5rem;
        color: rgba(255, 255, 255, 0.7);
        transition: all @transition-base;
      }
      
      &:hover .ivu-icon {
        color: rgba(100, 100, 120, 0.9);
        transform: rotate(90deg);
      }
    }
  }
  
  .config-panel-content {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    
    .config-item {
      display: flex;
      flex-direction: column;
      gap: 0.625rem;
      margin-bottom: 1.5rem;
      
      label {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.8);
        font-weight: @font-weight-medium;
      }
      
      /deep/ .ivu-select {
        width: 100%;
        
        .ivu-select-selection {
          background: rgba(26, 26, 46, 0.8);
          border: 1px solid rgba(59, 130, 246, 0.3);
          color: rgba(255, 255, 255, 0.9);
          border-radius: @border-radius-md;
          transition: all @transition-base;
          height: 2.5rem;
          
          &:hover {
            border-color: @primary-color;
            background: rgba(26, 26, 46, 0.95);
          }
          
          .ivu-select-placeholder {
            color: rgba(255, 255, 255, 0.4);
          }
          
          .ivu-select-selected-value {
            color: rgba(255, 255, 255, 0.9);
            line-height: 2.5rem;
          }
          
          .ivu-icon {
            color: rgba(255, 255, 255, 0.6);
          }
        }
      }
    }
    
    // 自定义滚动条
    &::-webkit-scrollbar {
      width: 0.375rem;
    }
    
    &::-webkit-scrollbar-track {
      background: transparent;
    }
    
    &::-webkit-scrollbar-thumb {
      background: rgba(59, 130, 246, 0.3);
      border-radius: 0.1875rem;
      
      &:hover {
        background: rgba(59, 130, 246, 0.5);
      }
    }
  }
}

// 配置面板滑入滑出动画
.config-panel-slide-enter-active,
.config-panel-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.config-panel-slide-enter,
.config-panel-slide-leave-to {
  width: 0;
  opacity: 0;
}

// Select下拉菜单样式
/deep/ .ivu-select-dropdown {
  background: rgba(26, 26, 46, 0.95);
  border: 1px solid rgba(59, 130, 246, 0.3);
  backdrop-filter: blur(1.25rem);
  
  .ivu-select-dropdown-list {
    .ivu-select-item {
      color: rgba(255, 255, 255, 0.8);
      
      &:hover {
        background: rgba(59, 130, 246, 0.2);
        color: #FFFFFF;
      }
      
      &.ivu-select-item-selected {
        background: rgba(59, 130, 246, 0.3);
        color: #FFFFFF;
      }
      
      &.ivu-select-item-focus {
        background: rgba(59, 130, 246, 0.2) !important;
        color: #FFFFFF !important;
      }
    }
  }
}

// 响应式设计
@media (max-width: @screen-md) {
  .sidebar {
    width: 14rem;
  }
  
  .chat-area {
    .config-toggle-btn {
      width: 2.5rem;
      height: 3.5rem;
      
      .ivu-icon {
        font-size: 1.375rem;
      }
    }
  }
  
  .config-panel {
    width: 20rem;
    
    .config-panel-header {
      padding: 1.25rem;
      
      h3 {
        font-size: 1rem;
      }
    }
    
    .config-panel-content {
      padding: 1.25rem;
      gap: 1.25rem;
    }
  }
  
  .chat-input-section {
    padding: 1rem;
    
    .input-wrapper {
      max-width: 45rem;
    }
  }
  
  // 简化背景
  .floating-shapes .shape {
    opacity: 0.08;
  }
  
  .light-particles .particle {
    opacity: 0.6;
  }
}

@media (max-width: @screen-sm) {
  .sidebar {
    position: absolute;
    left: -16rem;
    z-index: 100;
    transition: left @transition-slow;
    
    &.show {
      left: 0;
    }
  }
  
  .chat-area {
    .config-toggle-btn {
      width: 2.25rem;
      height: 3rem;
      
      .ivu-icon {
        font-size: 1.25rem;
      }
    }
  }
  
  .config-panel {
    width: 18rem;
    
    .config-panel-header {
      padding: 1rem;
    }
    
    .config-panel-content {
      padding: 1rem;
      gap: 1rem;
      
      .config-item {
        margin-bottom: 1rem;
        label {
          font-size: 0.8125rem;
        }
      }
    }
  }
  
  .chat-messages {
    .welcome-screen {
      padding: 2rem 1rem;
      
      .feature-cards {
        grid-template-columns: 1fr;
      }
    }
  }
  
  .chat-input-section {
    padding: 0.875rem;
    
    .input-wrapper {
      gap: 0.625rem;
      
      /deep/ .chat-input .ivu-input {
        padding: 0.625rem 0.875rem;
        font-size: 0.875rem;
      }
      
      .send-btn {
        width: 2.75rem;
        height: 2.75rem;
        
        .ivu-icon {
          font-size: 1.125rem;
        }
      }
    }
  }
}

// 查看大图弹窗样式
/deep/ .image-preview-modal {
  .ivu-modal {
    .ivu-modal-content {
      background: rgba(26, 26, 46, 0.98);
      backdrop-filter: blur(1.25rem);
      
      .ivu-modal-header {
        background: transparent;
        border-bottom: 1px solid rgba(59, 130, 246, 0.2);
        
        .ivu-modal-header-inner {
          color: #FFFFFF;
        }
      }
      
      .ivu-modal-body {
        padding: 1.5rem;
        
        .full-image-container {
          display: flex;
          align-items: center;
          justify-content: center;
          max-height: 70vh;
          
          img {
            max-width: 100%;
            max-height: 70vh;
            object-fit: contain;
            border-radius: @border-radius-lg;
            box-shadow: 0 0.5rem 2rem rgba(0, 0, 0, 0.5);
          }
        }
      }
    }
  }
}

// 重生成配置弹窗样式（沿用整体主题色）
/deep/ .regenerate-config-modal {
  .ivu-modal {
    .ivu-modal-content {
      background: rgba(26, 26, 46, 0.98);
      backdrop-filter: blur(1.25rem);

      .ivu-modal-header {
        background: transparent;
        border-bottom: 1px solid rgba(59, 130, 246, 0.2);
        .ivu-modal-header-inner {
          color: #FFFFFF;
          font-weight: @font-weight-semibold;
        }
      }

      .ivu-modal-body {
        padding-top: 1rem;
        .config-panel-content {
          padding: 0;
        }
        .config-item label {
          color: rgba(255, 255, 255, 0.85);
          margin-bottom: 0.5rem;
        }
        /deep/ .ivu-select-selection {
          background: rgba(26, 26, 46, 0.95); // 与主题一致
          border: 1px solid rgba(59, 130, 246, 0.3);
          color: rgba(255, 255, 255, 0.9);
          backdrop-filter: blur(1.25rem);
        }
        /deep/ .ivu-select-selection .ivu-select-placeholder,
        /deep/ .ivu-select-selection .ivu-select-selected-value {
          color: rgba(255, 255, 255, 0.85);
        }
        /deep/ .ivu-select-input {
          background: transparent;
          color: rgba(255, 255, 255, 0.9);
        }
        /deep/ .ivu-select-arrow {
          color: rgba(255, 255, 255, 0.65);
        }
        /deep/ .ivu-select-visible .ivu-select-selection,
        /deep/ .ivu-select-selection:hover {
          border-color: @primary-color;
        }
        /deep/ .ivu-switch {
          background-color: rgba(255, 255, 255, 0.12);
          &.ivu-switch-checked {
            background-color: @primary-color;
          }
        }
      }

      .ivu-modal-footer {
        background: transparent;
        border-top: 1px solid rgba(59, 130, 246, 0.2);
        .ivu-btn-primary {
          background: linear-gradient(135deg, @primary-color, @accent-color);
          border: none;
        }
      }
    }
  }
}
</style>

<style lang="less">
 @import '../styles/variables.less';
// 全局覆盖：iView Modal 渲染在 body 下，需非 scoped 才能生效
.regenerate-config-modal {
  .ivu-modal-body {
    // 选择框（非下拉层）的深色主题
    .ivu-select {
      .ivu-select-selection {
        background: rgba(26, 26, 46, 0.95) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 8px;
        backdrop-filter: blur(1.25rem);
      }
      .ivu-select-selection .ivu-select-placeholder,
      .ivu-select-selection .ivu-select-selected-value {
        color: rgba(255, 255, 255, 0.85) !important;
      }
      .ivu-select-input {
        background: transparent !important;
        color: rgba(255, 255, 255, 0.9) !important;
      }
      .ivu-select-arrow {
        color: rgba(255, 255, 255, 0.65) !important;
      }
      &.ivu-select-visible .ivu-select-selection,
      .ivu-select-selection:hover {
        border-color: @primary-color !important;
      }
    }
  }
}
</style>

