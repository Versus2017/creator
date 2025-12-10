<template>
  <div class="research-chat-page">
    <!-- 科技感背景效果 -->
    <div class="bg-effects">
      <div class="mind-grid"></div>
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
      </div>
    </div>

    <div class="content-wrapper">
      <!-- 页面头部 -->
      <div class="page-header">
          <Button 
            type="text" 
            icon="ios-arrow-back"
            class="back-btn"
            @click="goBack"
          >
            返回
          </Button>
          <h1 class="page-title">
            <Icon type="ios-bulb" />
            脚本研究
          </h1>
          <p class="page-description">与AI一起分析成功经验，提炼创作秘诀</p>
      </div>

      <!-- 主内容区：左右两栏布局 -->
      <div class="main-content">
        <!-- 左侧：脚本信息 -->
        <div class="left-panel">
          <div v-if="scriptInfo" class="script-panel">
            <div class="panel-header">
          <h3>{{ scriptInfo.title }}</h3>
          <Tag color="success">研究中</Tag>
        </div>
            
            <div class="script-meta">
              <div class="meta-item">
                <Icon type="ios-document" />
          <span>{{ scriptInfo.word_count || 0 }} 字</span>
              </div>
              <div class="meta-item">
                <Icon type="ios-pricetag" />
          <span>{{ scriptInfo.format_type }}</span>
        </div>
      </div>

            <div class="script-content">
              <div class="content-label">脚本内容</div>
              <div class="content-text markdown-content" v-html="renderMarkdown(scriptInfo.content || '暂无内容')"></div>
            </div>
          </div>
          
          <div v-else class="script-panel loading">
            <Spin size="large">
              <Icon type="ios-loading" size="32" class="spin-icon"></Icon>
              <div>加载脚本信息...</div>
            </Spin>
          </div>
        </div>

        <!-- 右侧：对话区域 -->
        <div class="right-panel">
      <div class="chat-container">
        <!-- 加载已有研究的提示 -->
        <div v-if="isLoadingExisting" class="loading-overlay">
          <Spin size="large">
            <Icon type="ios-loading" size="48" class="spin-icon-load"></Icon>
            <div class="loading-text">加载研究记录中...</div>
          </Spin>
        </div>
        
        <div class="messages-area" ref="messagesArea">
          <div 
            v-for="(message, index) in messages" 
            :key="index"
            v-if="message.content || message.role === 'user'"
            :class="['message-item', message.role]"
          >
            <div class="message-avatar">
              <Icon :type="message.role === 'user' ? 'ios-person' : 'ios-bulb'" />
            </div>
            <div class="message-content">
              <!-- 用户消息：普通文本 -->
              <div v-if="message.role === 'user'" class="message-text">{{ message.content }}</div>
              <!-- AI消息：Markdown渲染 -->
              <div v-else class="message-text markdown-content" v-html="renderMarkdown(message.content)"></div>
              <div class="message-time">{{ formatTime(message.created_at) }}</div>
            </div>
          </div>

          <!-- 思考指示器（AI未开始回复时显示） -->
          <div v-if="isAIThinking" class="message-item assistant">
            <div class="message-avatar">
              <Icon type="ios-bulb" />
            </div>
            <div class="message-content">
              <div class="thinking-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <!-- 输入模式切换 -->
        <div class="input-mode-switch">
          <div 
            class="mode-tab"
            :class="{ active: inputMode === 'text' }"
            @click="switchInputMode('text')"
          >
            <Icon type="md-create" />
            <span>文字</span>
          </div>
          <div 
            class="mode-tab"
            :class="{ active: inputMode === 'voice' }"
            @click="switchInputMode('voice')"
          >
            <Icon type="md-mic" />
            <span>语音</span>
          </div>
        </div>

        <!-- 文字输入模式 -->
        <div v-if="inputMode === 'text'" class="text-input-wrapper">
          <!-- 已完成研究的提示 -->
          <div v-if="researchStatus && researchStatus.name === 'COMPLETED'" class="completed-notice">
            <Icon type="ios-checkmark-circle" />
            <span>此研究已完成，您可以查看对话记录，但无法继续对话</span>
          </div>
          
          <!-- 输入框和发送按钮 -->
          <div v-else class="input-box">
            <Input 
              v-model="userInput"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 6 }"
              placeholder="分享你的想法和观察..."
              class="chat-input"
              @keydown.native="handleKeyDown"
            />
            <Button 
              type="primary" 
              :loading="isSending"
              :disabled="!userInput.trim()"
              class="send-btn"
              @click="handleSend"
            >
              <Icon type="ios-send" />
            </Button>
          </div>
        </div>

        <!-- 语音输入模式 -->
        <div v-else class="voice-input-wrapper">
          <!-- 已完成研究的提示 -->
          <div v-if="researchStatus && researchStatus.name === 'COMPLETED'" class="completed-notice">
            <Icon type="ios-checkmark-circle" />
            <span>此研究已完成，您可以查看对话记录，但无法继续对话</span>
          </div>
          
          <!-- 录音未开始 -->
          <div v-else-if="!isRecording && !recordedAudio && !currentVoiceMessageId && !isUploadingAudio && !voiceStatus.transcription.isActive && !voiceStatus.refinement.isActive && !voiceProcessingComplete" class="voice-idle">
            <Button
              type="primary"
              size="large"
              class="start-record-btn"
              @click="startRecording"
            >
              <Icon type="md-mic" size="24" />
              <span>点击开始录音</span>
            </Button>
            <p class="voice-hint">最长支持 15 分钟录音</p>
          </div>

          <!-- 录音中 -->
          <div v-if="isRecording" class="voice-recording">
            <div class="recording-visualizer">
              <div class="wave-bars">
                <div class="wave-bar" v-for="i in 20" :key="i" :style="{ animationDelay: (i * 0.05) + 's' }"></div>
              </div>
              <div class="recording-duration">{{ formattedRecordingDuration }}</div>
              <div class="recording-hint">
                <div class="recording-indicator">
                  <span class="pulse-dot"></span>
                  <span>录音中...</span>
                </div>
              </div>
            </div>

            <div class="recording-controls">
              <Button size="large" class="control-btn cancel-btn" @click="cancelRecording">
                <Icon type="md-close" size="20" />
                <span>取消</span>
              </Button>
              <Button v-if="!isPaused" size="large" class="control-btn pause-btn" @click="pauseRecording">
                <Icon type="md-pause" size="20" />
                <span>暂停</span>
              </Button>
              <Button v-else size="large" class="control-btn resume-btn" @click="resumeRecording">
                <Icon type="md-play" size="20" />
                <span>继续</span>
              </Button>
              <Button type="primary" size="large" class="control-btn finish-btn" @click="finishRecording">
                <Icon type="md-checkmark" size="20" />
                <span>完成</span>
              </Button>
            </div>
          </div>

          <!-- 处理中（上传、转写、校对） -->
          <div v-if="!isRecording && (recordedAudio || currentVoiceMessageId) && (isUploadingAudio || voiceStatus.transcription.isActive || voiceStatus.refinement.isActive || voiceProcessingComplete)" class="voice-processing">
            <div class="processing-status">
              <div v-if="isUploadingAudio" class="status-item">
                <Spin size="small"></Spin>
                <span>正在上传音频...</span>
              </div>
              
              <div v-if="!isUploadingAudio && voiceStatus.transcription.isActive && !voiceStatus.transcription.isCompleted" class="status-item">
                <Spin size="small"></Spin>
                <span>正在转写语音...</span>
              </div>
              
              <div v-if="voiceStatus.transcription.isCompleted && voiceStatus.transcription.text" class="transcription-result">
                <div class="result-label">
                  <Icon type="md-lock" size="14" />
                  <span>原始转写：</span>
                </div>
                <div class="result-text readonly">{{ voiceStatus.transcription.text }}</div>
              </div>
              
              <div v-if="voiceStatus.transcription.isCompleted && voiceStatus.refinement.isActive && !voiceStatus.refinement.isCompleted" class="status-item">
                <Spin size="small"></Spin>
                <span>正在校对修正...</span>
              </div>
              
              <div v-if="voiceStatus.refinement.isCompleted && voiceStatus.refinement.result && voiceStatus.refinement.result.final_text" class="refinement-result">
                <div class="result-label">
                  <Icon type="md-create" size="14" />
                  <span>校对后文本（可编辑）：</span>
                  <Button
                    v-if="voiceStatus.refinement.result.corrections && voiceStatus.refinement.result.corrections.length > 0"
                    type="text"
                    size="small"
                    class="corrections-trigger-btn"
                    @click="showCorrectionsModal = true"
                  >
                    <Icon type="md-list" size="16" />
                    <span>{{ voiceStatus.refinement.result.corrections.length }} 处修正</span>
                  </Button>
                </div>
                <Input
                  v-model="voiceConfirmedContent"
                  type="textarea"
                  :autosize="{ minRows: 3, maxRows: 8 }"
                  class="result-text-editable"
                  placeholder="您可以在此编辑文本..."
                />
              </div>
              
              <div v-if="voiceStatus.transcription.error || voiceStatus.refinement.error" class="error-message">
                <Icon type="md-alert" />
                <span>{{ voiceStatus.transcription.error || voiceStatus.refinement.error }}</span>
              </div>
            </div>

            <div v-if="voiceProcessingComplete" class="recorded-controls">
              <Button size="large" class="control-btn" @click="reRecord">
                <Icon type="md-refresh" size="20" />
                <span>重录</span>
              </Button>
              <Button type="primary" size="large" class="control-btn send-audio-btn" :loading="isConfirmingVoice" :disabled="isConfirmingVoice || autoConfirmTriggered" @click="confirmVoiceContent">
                <Icon type="md-checkmark" size="20" />
                <span>确认发送</span>
              </Button>
            </div>
          </div>

          <!-- 待发送（出错后保留） -->
          <div v-if="!isRecording && recordedAudio && !isUploadingAudio && !voiceStatus.transcription.isActive && !voiceStatus.refinement.isActive && !voiceProcessingComplete" class="voice-recorded">
            <div class="recorded-info">
              <Icon type="ios-musical-notes" size="32" class="audio-icon" />
              <div class="audio-info">
                <div class="audio-duration">录音时长: {{ formattedRecordedDuration }}</div>
                <div class="audio-hint">准备重新上传</div>
              </div>
            </div>
            <div class="recorded-controls">
              <Button size="large" class="control-btn" @click="reRecord">
                <Icon type="md-refresh" size="20" />
                <span>重录</span>
              </Button>
              <Button type="primary" size="large" class="control-btn send-audio-btn" @click="sendVoiceMessage">
                <Icon type="md-send" size="20" />
                <span>重新发送</span>
              </Button>
            </div>
          </div>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- 悬浮生成报告按钮 -->
    <div 
      v-if="canComplete && (!researchStatus || researchStatus.name !== 'COMPLETED')"
      class="floating-report-btn"
      :style="{ left: floatBtnPosition.x + 'px', top: floatBtnPosition.y + 'px' }"
      @mousedown="startDrag"
    >
      <Tooltip content="生成研究报告" placement="left">
        <Button 
          type="primary" 
          shape="circle" 
          size="large"
          class="report-btn"
          @click="showCompleteModal"
        >
          <Icon type="ios-document" size="24" />
        </Button>
      </Tooltip>
    </div>

    <!-- 全屏分析动画 -->
    <transition name="fade">
      <div v-if="isAnalyzing" class="fullscreen-analyzing">
        <div class="analyzing-overlay"></div>
        <div class="analyzing-content">
          <!-- 科技感加载动画 -->
          <div class="tech-loader">
            <!-- 旋转的圆环 -->
            <div class="loader-ring ring-1"></div>
            <div class="loader-ring ring-2"></div>
            <div class="loader-ring ring-3"></div>
            
            <!-- 中心图标 -->
            <Icon type="ios-analytics" class="loader-icon" />
          </div>
          
          <!-- 文案 -->
          <div class="analyzing-text">
            <h3>深度分析中...</h3>
            <p>AI正在分析对话内容和脚本，提炼成功要素</p>
          </div>
          
          <!-- 粒子效果 -->
          <div class="tech-particles">
            <div class="particle" v-for="i in 20" :key="i"></div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 修正记录弹窗 -->
    <Modal
      v-model="showCorrectionsModal"
      title="修正记录"
      width="600"
      :mask-closable="true"
    >
      <div class="corrections-modal-content">
        <div class="corrections-summary">
          <Icon type="md-checkmark-circle" size="20" color="#52c41a" />
          <span>共修正了 {{ voiceStatus.refinement.result && voiceStatus.refinement.result.corrections ? voiceStatus.refinement.result.corrections.length : 0 }} 处错误</span>
        </div>
        
        <div class="corrections-list-modal">
          <div 
            v-for="(correction, index) in (voiceStatus.refinement.result && voiceStatus.refinement.result.corrections ? voiceStatus.refinement.result.corrections : [])" 
            :key="index" 
            class="correction-item-modal"
          >
            <div class="correction-number">#{{ index + 1 }}</div>
            <div class="correction-content">
              <div class="correction-row">
                <span class="correction-label">原文：</span>
                <span class="original-text">{{ correction.original }}</span>
              </div>
              <div class="correction-row">
                <span class="correction-label">修正：</span>
                <span class="corrected-text">{{ correction.corrected }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div slot="footer">
        <Button type="primary" @click="showCorrectionsModal = false">关闭</Button>
      </div>
    </Modal>

    <!-- 完成研究弹窗 -->
    <Modal
      v-model="completeModalVisible"
      title="生成研究报告"
      width="700"
      :mask-closable="false"
      class-name="research-complete-modal"
      @on-ok="handleComplete"
    >
      <div class="complete-form">
        <div class="ai-generated-notice">
          <Icon type="ios-bulb" />
          <span>以下内容由AI基于对话和脚本自动生成，您可以编辑调整</span>
        </div>
        
        <h4>关键成功要素（3-5个）：</h4>
        <div class="findings-list">
          <div 
            v-for="(finding, index) in keyFindings" 
            :key="index"
            class="finding-item"
          >
            <Input 
              v-model="keyFindings[index]"
              placeholder="输入关键要素..."
            />
            <Button 
              type="text" 
              icon="ios-close-circle"
              @click="removeFinding(index)"
            />
          </div>
        </div>
        <Button 
          type="dashed" 
          icon="ios-add"
          long
          @click="addFinding"
        >
          添加要素
        </Button>

        <h4 style="margin-top: 20px;">研究总结：</h4>
        <Input 
          v-model="summary"
          type="textarea"
          :autosize="{ minRows: 4, maxRows: 8 }"
          placeholder="简要总结这次研究的核心发现..."
        />

        <Checkbox v-model="applyToProfile" style="margin-top: 15px;">
          应用到我的创作风格档案
        </Checkbox>
      </div>
    </Modal>
  </div>
</template>

<script>
import moment from 'moment'
import marked from 'marked'
import { SSE } from '@/libs/sse'
import { getCookie } from '@/libs/util'

// 配置marked选项
marked.setOptions({
  breaks: true,        // 支持GitHub风格的换行
  gfm: true,          // 启用GitHub风格的Markdown
  tables: true,       // 支持表格
  smartLists: true,   // 智能列表
  highlight: null     // 代码高亮（可以后续添加）
})

export default {
  name: 'ResearchChat',
  
  data() {
    return {
      // 脚本信息
      scriptInfo: null,
      
      // 研究记录
      researchId: null,
      conversationId: null,
      researchStatus: null, // 研究状态
      isLoadingExisting: false, // 是否在加载已有研究
      
      // 对话消息
      messages: [],
      
      // 用户输入
      userInput: '',
      
      // 状态
      isSending: false,
      isAIThinking: false,
      canComplete: false,
      
      // 完成研究
      isAnalyzing: false,  // 全屏分析动画
      completeModalVisible: false,
      keyFindings: ['', '', ''],
      summary: '',
      applyToProfile: true,

      // ==================== 语音录音相关 ====================
      inputMode: 'text', // 'text' 或 'voice'
      
      // 录音状态
      isRecording: false,
      isPaused: false,
      recordedAudio: null,
      recordedDuration: 0,
      recordingDuration: 0,
      recordingTimer: null,
      mediaRecorder: null,
      audioChunks: [],
      
      // 上传状态
      isUploadingAudio: false,
      isFinishingRecording: false,
      
      // 语音处理状态
      voiceProcessingComplete: false,
      currentVoiceMessageId: null,
      voicePollingTimer: null,
      voiceStatus: {
        transcription: {
          isActive: false,
          isCompleted: false,
          text: '',
          error: ''
        },
        refinement: {
          isActive: false,
          isCompleted: false,
          result: null,
          error: ''
        }
      },
      
      // 确认内容
      voiceConfirmedContent: '',
      isConfirmingVoice: false,
      autoConfirmTriggered: false,
      
      // 修正记录弹窗
      showCorrectionsModal: false,
      
      // ==================== 浮动按钮 ====================
      floatBtnPosition: {
        x: 0,
        y: 0
      },
      isDragging: false,
      dragStartX: 0,
      dragStartY: 0
    }
  },

  computed: {
    // 格式化录音时长（录音中）
    formattedRecordingDuration() {
      return this.formatDuration(this.recordingDuration)
    },
    
    // 格式化录音时长（已录制）
    formattedRecordedDuration() {
      return this.formatDuration(this.recordedDuration)
    }
  },

  methods: {
    // 初始化研究
    async initResearch() {
      const scriptId = this.$route.query.scriptId
      const researchId = this.$route.query.researchId
      
      // 模式1: 查看已有研究（从研究列表进入）
      if (researchId) {
        await this.loadExistingResearch(researchId)
        return
      }
      
      // 模式2: 创建新研究（从脚本详情进入）
      if (!scriptId) {
        this.$Message.error('缺少脚本ID或研究ID')
        this.goBack()
        return
      }

      try {
        // 1. 获取脚本信息
        const scriptRes = await this.$http.get(`/web/scripts/${scriptId}`)
        if (scriptRes && scriptRes.success) {
          this.scriptInfo = scriptRes.data
        }

        // 2. 开始新研究
        const researchRes = await this.$http.post('/web/researches', {
          script_id: parseInt(scriptId)
        })

        if (researchRes && researchRes.success) {
          this.researchId = researchRes.data.research.id
          this.conversationId = researchRes.data.conversation.id
          
          // 添加AI开场白
          this.messages.push(researchRes.data.initial_message)
        }
      } catch (error) {
        console.error('初始化研究失败:', error)
        this.$Message.error('初始化失败，请重试')
        this.goBack()
      }
    },
    
    // 加载已有研究
    async loadExistingResearch(researchId) {
      this.isLoadingExisting = true
      try {
        // 获取研究详情（包含脚本、消息历史）
        const response = await this.$http.get(`/web/researches/${researchId}`)
        
        if (response && response.success) {
          const data = response.data
          
          // 设置研究信息
          this.researchId = data.research.id
          this.conversationId = data.research.conversation_id
          this.researchStatus = data.research.status
          
          // 设置脚本信息
          if (data.script) {
            this.scriptInfo = data.script
          }
          
          // 加载历史消息
          if (data.messages && data.messages.length > 0) {
            this.messages = data.messages
            this.scrollToBottom()
          }
          
          // 检查研究状态
          if (this.researchStatus && this.researchStatus.name === 'COMPLETED') {
            // 已完成的研究不能再继续对话，但可以查看
            this.canComplete = false
          } else if (this.messages.length >= 5) {
            // 进行中的研究，消息数量超过10条可以完成
            this.canComplete = true
          }
        }
      } catch (error) {
        console.error('加载研究失败:', error)
        this.$Message.error('加载失败，请重试')
        this.goBack()
      } finally {
        this.isLoadingExisting = false
      }
    },

    // 发送消息
    async handleSend() {
      if (!this.userInput.trim() || this.isSending) return

      const content = this.userInput.trim()
      this.userInput = ''
      
      // 添加用户消息到界面
      this.messages.push({
        role: 'user',
        content: content,
        created_at: new Date().toISOString()
      })

      this.scrollToBottom()
      this.isSending = true
      this.isAIThinking = true
      
      // 添加空的AI消息占位
      this.messages.push({
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString()
      })
      const currentAiMessageIndex = this.messages.length - 1

      try {
        // 使用 SSE 流式对话
        await this.streamResearchChat(content, currentAiMessageIndex)
        
        // 检查是否可以完成研究（例如：对话超过5轮）
        if (this.messages.length >= 10) {
          this.canComplete = true
        }
      } catch (error) {
        console.error('发送消息失败:', error)
        this.$Message.error('发送失败，请重试')
        
        // 删除空的AI消息占位
        if (this.messages[currentAiMessageIndex] && !this.messages[currentAiMessageIndex].content) {
          this.messages.splice(currentAiMessageIndex, 1)
        }
      } finally {
        this.isSending = false
        this.isAIThinking = false
        this.scrollToBottom()
      }
    },
    
    // SSE 流式研究对话
    streamResearchChat(content, aiMessageIndex) {
      return new Promise((resolve, reject) => {
        // 构建 SSE 请求
        const url = `/v1/web/researches/${this.researchId}/chat`
        const payload = JSON.stringify({
          research_id: this.researchId,
          content: content
        })
        
        // 获取 CSRF Token
        const csrfToken = getCookie('creator_auth_csrf_cookie')
        
        const sseConnection = new SSE(url, {
          headers: {
            'Content-Type': 'application/json',
            'source': 'web',
            'X-CSRF-TOKEN': csrfToken
          },
          payload: payload,
          method: 'POST',
          withCredentials: true
        })
        
        // 监听消息事件
        sseConnection.addEventListener('message', (e) => {
          if (e.data) {
            try {
              const message = JSON.parse(e.data)
              
              console.log('SSE消息:', message)
              
              if (message.type === 'start') {
                console.log('开始接收AI回复')
              } else if (message.type === 'begin') {
                console.log('AI准备回复中...')
                // AI开始回复，隐藏思考指示器
                this.isAIThinking = false
              } else if (message.type === 'input') {
                // AI开始输出内容，确保思考指示器已隐藏
                if (this.isAIThinking) {
                  this.isAIThinking = false
                }
                
                // 接收内容片段
                if (aiMessageIndex >= 0 && message.content) {
                  const currentMessage = this.messages[aiMessageIndex]
                  
                  if (currentMessage) {
                    currentMessage.content += message.content
                    this.$set(this.messages, aiMessageIndex, currentMessage)
                    
                    this.$nextTick(() => {
                      this.scrollToBottom()
                    })
                  }
                }
              } else if (message.type === 'stop') {
                console.log('AI回复完成')
                if (message.content) {
                  this.$Message.warning(message.content)
                }
              } else if (message.type === 'error') {
                console.error('AI回复错误:', message.content)
                this.$Message.error(message.content || '对话出错，请重试')
                sseConnection.close()
                reject(new Error(message.content || '对话出错'))
              }
            } catch (error) {
              console.error('解析SSE消息失败:', error, 'raw data:', e.data)
            }
          }
        })
        
        // 监听错误事件
        sseConnection.addEventListener('error', (e) => {
          console.error('SSE错误:', e)
          sseConnection.close()
          reject(new Error('流式对话失败'))
        })
        
        // 监听结束事件
        sseConnection.addEventListener('readystatechange', (e) => {
          if (e.readyState === sseConnection.CLOSED) {
            sseConnection.close()
            resolve()
          }
        })
        
        // 开始流式请求
        sseConnection.stream()
      })
    },

    // 显示完成弹窗
    async showCompleteModal() {
      // 先显示分析动画
      this.isAnalyzing = true
      
      try {
        // 调用后端API，让AI分析生成关键要素和总结
        const response = await this.$http.post(
          `/web/researches/${this.researchId}/analyze`
        )
        
        if (response && response.success) {
          // 将AI生成的内容填充到表单
          const data = response.data
          this.keyFindings = data.key_findings || ['', '', '']
          this.summary = data.summary || ''
          
          // 确保至少有3个要素输入框
          while (this.keyFindings.length < 3) {
            this.keyFindings.push('')
          }
          
          this.$Message.success('AI分析完成')
        } else {
          this.$Message.warning('AI分析失败，请手动填写')
          // 重置为空值，让用户手动填写
          this.keyFindings = ['', '', '']
          this.summary = ''
        }
      } catch (error) {
        console.error('AI分析失败:', error)
        this.$Message.error('AI分析失败，请手动填写')
        // 重置为空值，让用户手动填写
        this.keyFindings = ['', '', '']
        this.summary = ''
      } finally {
        // 关闭分析动画，显示弹窗
        this.isAnalyzing = false
        this.$nextTick(() => {
          this.completeModalVisible = true
        })
      }
    },

    // 完成研究
    async handleComplete() {
      // 过滤空值
      const validFindings = this.keyFindings.filter(f => f.trim())
      
      if (validFindings.length === 0) {
        this.$Message.warning('请至少填写一个关键成功要素')
        return false
      }

      if (!this.summary.trim()) {
        this.$Message.warning('请填写研究总结')
        return false
      }

      try {
        const response = await this.$http.post(
          `/web/researches/${this.researchId}/complete`,
          {
            key_findings: validFindings,
            summary: this.summary.trim(),
            apply_to_profile: this.applyToProfile
          }
        )

        if (response && response.success) {
          this.$Message.success('研究完成！成功经验已记录')
          // 跳转到研究列表或脚本列表
          this.$router.push({ name: 'research-list' })
        }
      } catch (error) {
        console.error('完成研究失败:', error)
        this.$Message.error('操作失败，请重试')
        return false
      }
    },

    // 添加要素
    addFinding() {
      this.keyFindings.push('')
    },

    // 删除要素
    removeFinding(index) {
      this.keyFindings.splice(index, 1)
    },

    // 滚动到底部
    scrollToBottom() {
      this.$nextTick(() => {
        const messagesArea = this.$refs.messagesArea
        if (messagesArea) {
          messagesArea.scrollTop = messagesArea.scrollHeight
        }
      })
    },

    // 格式化时间
    formatTime(time) {
      if (!time) return ''
      return moment(time).format('HH:mm')
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
      this.$router.go(-1)
    },

    // ==================== 语音录音功能 ====================
    
    // 切换输入模式
    switchInputMode(mode) {
      if (this.isSending) {
        this.$Message.warning('请等待当前操作完成')
        return
      }
      
      if (this.isRecording) {
        this.$Message.warning('请先停止录音')
        return
      }
      
      this.inputMode = mode
    },
    
    // 快捷键处理
    handleKeyDown(e) {
      // Enter 直接发送，Shift+Enter 换行
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        if (this.userInput.trim() && !this.isSending) {
          this.handleSend()
        }
      }
    },
    
    // 格式化时长 (秒 -> MM:SS)
    formatDuration(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    },
    
    // 开始录音
    async startRecording() {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          this.$Message.error('您的浏览器不支持录音功能')
          return
        }
        
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        
        this.mediaRecorder = new MediaRecorder(stream)
        this.audioChunks = []
        
        this.mediaRecorder.addEventListener('dataavailable', (event) => {
          this.audioChunks.push(event.data)
        })
        
        this.mediaRecorder.addEventListener('stop', () => {
          const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' })
          this.recordedAudio = audioBlob
          this.recordedDuration = this.recordingDuration
          
          stream.getTracks().forEach(track => track.stop())
          
          console.log('录音完成，时长:', this.recordedDuration, '秒')
        })
        
        this.mediaRecorder.start()
        this.isRecording = true
        this.isPaused = false
        this.recordingDuration = 0
        
        this.recordingTimer = setInterval(() => {
          this.recordingDuration++
          
          if (this.recordingDuration >= 900) {
            this.$Message.warning('已达到最大录音时长（15分钟），自动停止')
            this.finishRecording()
          }
        }, 1000)
        
        this.$Message.success('开始录音')
      } catch (error) {
        console.error('开始录音失败:', error)
        if (error.name === 'NotAllowedError') {
          this.$Message.error('您拒绝了麦克风权限，无法录音')
        } else {
          this.$Message.error('开始录音失败: ' + error.message)
        }
      }
    },
    
    // 暂停录音
    pauseRecording() {
      if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
        this.mediaRecorder.pause()
        this.isPaused = true
        clearInterval(this.recordingTimer)
        this.$Message.info('录音已暂停')
      }
    },
    
    // 继续录音
    resumeRecording() {
      if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
        this.mediaRecorder.resume()
        this.isPaused = false
        
        this.recordingTimer = setInterval(() => {
          this.recordingDuration++
          
          if (this.recordingDuration >= 900) {
            this.$Message.warning('已达到最大录音时长（15分钟），自动停止')
            this.finishRecording()
          }
        }, 1000)
        
        this.$Message.info('继续录音')
      }
    },
    
    // 完成录音
    finishRecording() {
      if (this.isFinishingRecording) {
        return
      }
      
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
        this.isFinishingRecording = true
        this.mediaRecorder.stop()
        this.isRecording = false
        this.isPaused = false
        clearInterval(this.recordingTimer)
        
        this.$Message.success('录音完成')
        
        setTimeout(() => {
          this.isFinishingRecording = false
          if (this.recordedAudio && !this.isUploadingAudio) {
            this.sendVoiceMessage()
          } else if (!this.recordedAudio) {
            console.error('录音数据未就绪')
            this.$Message.error('录音数据未就绪，请重试')
          }
        }, 300)
      } else {
        this.isFinishingRecording = false
      }
    },
    
    // 取消录音
    cancelRecording() {
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
        this.mediaRecorder.stop()
      }
      
      this.isRecording = false
      this.isPaused = false
      this.isFinishingRecording = false
      this.recordedAudio = null
      this.recordedDuration = 0
      this.recordingDuration = 0
      this.audioChunks = []
      
      clearInterval(this.recordingTimer)
      this.$Message.info('已取消录音')
    },
    
    // 重新录音
    reRecord() {
      this.resetVoiceProcessingState()
    },
    
    // 发送语音消息
    async sendVoiceMessage() {
      if (this.isUploadingAudio) {
        console.log('已经在处理音频上传，跳过重复调用')
        return
      }
      
      if (!this.recordedAudio) {
        this.$Message.warning('没有录音数据')
        return
      }
      
      this.isUploadingAudio = true
      this.$Message.loading('正在上传音频...', 0)
      
      try {
        // 步骤1：上传音频文件到 /media
        console.log('开始上传音频文件...')
        const formData = new FormData()
        formData.append('file', this.recordedAudio, 'recording.webm')
        
        const uploadResponse = await this.$http.post('/media', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 60000
        })
        
        if (!uploadResponse || !uploadResponse.success) {
          throw new Error('音频上传失败')
        }
        
        const mediaId = uploadResponse.data.id
        console.log('音频上传成功，media_id:', mediaId)
        this.$Message.destroy()
        this.$Message.success('音频上传成功')
        
        // 步骤2：创建语音消息并开始识别
        this.$Message.loading('正在创建语音消息...', 0)
        const voiceResponse = await this.$http.post(
          `/web/conversations/${this.conversationId}/messages/voice`,
          { audio_media_id: mediaId }
        )
        
        if (!voiceResponse || !voiceResponse.success) {
          throw new Error('创建语音消息失败')
        }
        
        this.currentVoiceMessageId = voiceResponse.data.id
        console.log('语音消息创建成功，message_id:', this.currentVoiceMessageId)
        
        // 步骤3：清空录音状态
        this.recordedAudio = null
        this.recordedDuration = 0
        this.isUploadingAudio = false
        
        // 步骤4：开始轮询处理状态
        this.$Message.destroy()
        this.resetVoiceStatus()
        this.startVoiceStatusPolling()
        
        this.$Message.success('开始语音识别...')
      } catch (error) {
        console.error('发送语音消息失败:', error)
        this.$Message.destroy()
        this.isUploadingAudio = false
        
        this.stopVoiceStatusPolling()
        this.currentVoiceMessageId = null
        
        let errorMsg = '上传失败'
        if (error.message) {
          errorMsg = error.message
        } else if (error.code === 'ECONNABORTED') {
          errorMsg = '上传超时，请检查网络连接'
        } else if (error.response) {
          errorMsg = '服务器错误，请稍后重试'
        }
        
        this.$Message.error(errorMsg)
      }
    },
    
    // 重置语音状态
    resetVoiceStatus() {
      this.voiceProcessingComplete = false
      this.voiceStatus = {
        transcription: {
          isActive: false,
          isCompleted: false,
          text: '',
          error: ''
        },
        refinement: {
          isActive: false,
          isCompleted: false,
          result: null,
          error: ''
        }
      }
    },
    
    // 开始轮询语音处理状态
    startVoiceStatusPolling() {
      if (this.voicePollingTimer) {
        clearInterval(this.voicePollingTimer)
      }
      
      this.pollVoiceStatus()
      
      this.voicePollingTimer = setInterval(() => {
        this.pollVoiceStatus()
      }, 2000)
    },
    
    // 轮询语音处理状态
    async pollVoiceStatus() {
      if (!this.currentVoiceMessageId) {
        this.stopVoiceStatusPolling()
        return
      }
      
      try {
        const response = await this.$http.get(
          `/web/messages/${this.currentVoiceMessageId}/processing-status`
        )
        
        if (!response || !response.success) {
          console.error('获取状态失败')
          this.stopVoiceStatusPolling()
          return
        }
        
        const status = response.data
        console.log('语音处理状态:', status)
        
        // 更新转写状态
        if (status.transcription && status.transcription.status) {
          const transStatus = status.transcription.status.name
          
          if (transStatus === 'PROCESSING') {
            this.$set(this.voiceStatus.transcription, 'isActive', true)
            this.$set(this.voiceStatus.transcription, 'isCompleted', false)
            this.$set(this.voiceStatus.transcription, 'error', '')
          } else if (transStatus === 'COMPLETED') {
            this.$set(this.voiceStatus.transcription, 'isActive', false)
            this.$set(this.voiceStatus.transcription, 'isCompleted', true)
            this.$set(this.voiceStatus.transcription, 'text', status.transcription.raw_text || '')
            this.$set(this.voiceStatus.transcription, 'error', '')
          } else if (transStatus === 'FAILED') {
            this.$set(this.voiceStatus.transcription, 'isActive', false)
            this.$set(this.voiceStatus.transcription, 'isCompleted', false)
            this.$set(this.voiceStatus.transcription, 'error', status.transcription.error || '转写失败')
            this.stopVoiceStatusPolling()
          }
        }
        
        // 更新整理状态
        if (status.refinement && status.refinement.status) {
          const refineStatus = status.refinement.status.name
          
          if (refineStatus === 'PROCESSING') {
            this.$set(this.voiceStatus.refinement, 'isActive', true)
            this.$set(this.voiceStatus.refinement, 'isCompleted', false)
            this.$set(this.voiceStatus.refinement, 'error', '')
          } else if (refineStatus === 'COMPLETED') {
            this.$set(this.voiceStatus.refinement, 'isActive', false)
            this.$set(this.voiceStatus.refinement, 'isCompleted', true)
            this.$set(this.voiceStatus.refinement, 'result', status.refinement.result)
            
            this.voiceProcessingComplete = true
            const refinedText = status.refinement.result && status.refinement.result.final_text
              ? status.refinement.result.final_text
              : (status.refinement.refined_content || this.voiceStatus.transcription.text || '')
            this.voiceConfirmedContent = refinedText
            this.stopVoiceStatusPolling()
            this.scheduleAutoConfirmVoiceContent()
          } else if (refineStatus === 'FAILED') {
            this.$set(this.voiceStatus.refinement, 'isActive', false)
            this.$set(this.voiceStatus.refinement, 'isCompleted', false)
            this.$set(this.voiceStatus.refinement, 'error', status.refinement.error || '整理失败')
            this.stopVoiceStatusPolling()
          }
        }
      } catch (error) {
        console.error('轮询状态失败:', error)
      }
    },
    
    // 停止轮询
    stopVoiceStatusPolling() {
      if (this.voicePollingTimer) {
        clearInterval(this.voicePollingTimer)
        this.voicePollingTimer = null
      }
    },
    
    // 校对完成后自动发送
    scheduleAutoConfirmVoiceContent() {
      if (this.autoConfirmTriggered) {
        return
      }
      if (!this.currentVoiceMessageId) {
        return
      }
      this.autoConfirmTriggered = true
      this.$Message.info('语音内容校对完成，正在自动发送...')
      this.$nextTick(() => {
        this.confirmVoiceContent()
      })
    },
    
    // 确认语音内容
    async confirmVoiceContent() {
      const contentToSend = this.voiceConfirmedContent && this.voiceConfirmedContent.trim()
        ? this.voiceConfirmedContent.trim()
        : (this.voiceStatus.transcription.text || '')
      
      if (!contentToSend) {
        this.$Message.warning('内容不能为空')
        this.autoConfirmTriggered = false
        return
      }
      
      if (!this.currentVoiceMessageId) {
        this.$Message.error('消息ID丢失')
        this.autoConfirmTriggered = false
        return
      }
      
      this.isConfirmingVoice = true
      
      try {
        const response = await this.$http.post(
          `/web/messages/${this.currentVoiceMessageId}/confirm`,
          {
            content: contentToSend,
            send_to_ai: false  // 研究对话不自动发送给AI，由用户确认后再发送
          }
        )
        
        if (!response || !response.success) {
          throw new Error('确认内容失败')
        }
        
        // 重置语音处理状态
        this.resetVoiceProcessingState()
        
        // 将确认的内容作为用户输入
        this.userInput = contentToSend
        
        // 自动发送给AI
        this.$nextTick(() => {
          this.handleSend()
        })
        
      } catch (error) {
        console.error('确认内容失败:', error)
        this.autoConfirmTriggered = false
        this.$Message.error('确认失败: ' + (error.message || '未知错误'))
      } finally {
        this.isConfirmingVoice = false
      }
    },
    
    // 重置语音处理状态
    resetVoiceProcessingState() {
      this.currentVoiceMessageId = null
      this.voiceConfirmedContent = ''
      this.recordedAudio = null
      this.recordedDuration = 0
      this.voiceProcessingComplete = false
      this.isFinishingRecording = false
      this.isUploadingAudio = false
      this.autoConfirmTriggered = false
      this.resetVoiceStatus()
    },
    
    // ==================== 浮动按钮拖拽 ====================
    
    // 初始化浮动按钮位置
    initFloatBtnPosition() {
      // 默认位置：右下角，距离边缘 20px
      this.floatBtnPosition.x = window.innerWidth - 90
      this.floatBtnPosition.y = window.innerHeight - 150
    },
    
    // 开始拖拽
    startDrag(e) {
      // 防止点击按钮时触发拖拽
      if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
        return
      }
      
      this.isDragging = true
      this.dragStartX = e.clientX - this.floatBtnPosition.x
      this.dragStartY = e.clientY - this.floatBtnPosition.y
      
      document.addEventListener('mousemove', this.onDrag)
      document.addEventListener('mouseup', this.stopDrag)
      
      e.preventDefault()
    },
    
    // 拖拽中
    onDrag(e) {
      if (!this.isDragging) return
      
      let newX = e.clientX - this.dragStartX
      let newY = e.clientY - this.dragStartY
      
      // 限制在窗口范围内
      const btnSize = 60
      newX = Math.max(0, Math.min(newX, window.innerWidth - btnSize))
      newY = Math.max(0, Math.min(newY, window.innerHeight - btnSize))
      
      this.floatBtnPosition.x = newX
      this.floatBtnPosition.y = newY
    },
    
    // 停止拖拽
    stopDrag() {
      this.isDragging = false
      document.removeEventListener('mousemove', this.onDrag)
      document.removeEventListener('mouseup', this.stopDrag)
    }
  },

  mounted() {
    this.initResearch()
    this.initFloatBtnPosition()
  },

  beforeDestroy() {
    // 清理录音相关
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop()
    }
    clearInterval(this.recordingTimer)
    
    // 清理语音状态轮询
    this.stopVoiceStatusPolling()
    
    // 清理拖拽事件
    document.removeEventListener('mousemove', this.onDrag)
    document.removeEventListener('mouseup', this.stopDrag)
  }
}
</script>

<style lang="less" scoped>
@import '../styles/variables.less';

.research-chat-page {
  height: ~"calc(100vh - 64px)";
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 30%, #312e81 70%, #1e1b4b 100%);
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

.mind-grid {
  position: absolute;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px),
    linear-gradient(0deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
  background-size: 6.25rem 6.25rem;
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
  }
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(1.875rem, -1.875rem); }
}

// 内容容器
.content-wrapper {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 1.5rem 2rem;
  max-width: 1600px;
  margin: 0 auto;
}

// 页面头部
.page-header {
  margin-bottom: 1.5rem;

  .back-btn {
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 0.5rem;

    &:hover {
      color: @primary-light;
    }
  }

  .page-title {
    font-size: 1.5rem;
    font-weight: @font-weight-bold;
    color: #FFFFFF;
    margin-bottom: 0.375rem;
    display: flex;
    align-items: center;
    gap: 0.625rem;
  }

  .page-description {
    font-size: 0.9375rem;
    color: rgba(255, 255, 255, 0.7);
  }
}

// 主内容区：左右两栏
.main-content {
  flex: 1;
  display: flex;
  gap: 1.5rem;
  min-height: 0;
  overflow: hidden;
}

// 左侧面板：脚本信息
.left-panel {
  width: 400px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  
  .script-panel {
    flex: 1;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: @border-radius-lg;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    
    &.loading {
      align-items: center;
      justify-content: center;
      
      .spin-icon {
        color: @primary-color;
        margin-bottom: 0.75rem;
      }
    }
    
    .panel-header {
    display: flex;
    justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 1rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);

    h3 {
      color: #FFFFFF;
      font-size: 1.125rem;
      font-weight: @font-weight-semibold;
      margin: 0;
        line-height: 1.4;
        flex: 1;
    }
  }

    .script-meta {
    display: flex;
      flex-direction: column;
      gap: 0.625rem;
      margin-bottom: 1.25rem;
      
      .meta-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.7);
        
        .ivu-icon {
          color: @primary-light;
          font-size: 1rem;
        }
      }
    }
    
    .script-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-height: 0;
      
      .content-label {
        font-size: 0.875rem;
        font-weight: @font-weight-medium;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        
        &:before {
          content: '';
          width: 3px;
          height: 14px;
          background: linear-gradient(180deg, @primary-color, @primary-light);
          border-radius: 2px;
        }
      }
      
      .content-text {
        flex: 1;
        background: rgba(10, 10, 26, 0.5);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: @border-radius-md;
        padding: 1rem;
        color: rgba(255, 255, 255, 0.85);
        font-size: 0.875rem;
        line-height: 1.8;
        overflow-y: auto;
        word-break: break-word;
        
        // Markdown 样式
        &.markdown-content {
          white-space: normal;
          
          /deep/ * {
            margin: 0;
            padding: 0;
          }
          
          /deep/ p {
            margin-bottom: 0.75rem;
            line-height: 1.8;
            font-size: 0.875rem;
            color: rgba(255, 255, 255, 0.85);
            
            &:last-child {
              margin-bottom: 0;
            }
          }
          
          /deep/ h1, /deep/ h2, /deep/ h3, /deep/ h4, /deep/ h5, /deep/ h6 {
            font-weight: @font-weight-semibold;
            margin-top: 1.25rem;
            margin-bottom: 0.75rem;
            color: rgba(255, 255, 255, 0.95);
            
            &:first-child {
              margin-top: 0;
            }
          }
          
          /deep/ h1 { font-size: 1.375rem; }
          /deep/ h2 { font-size: 1.1875rem; }
          /deep/ h3 { font-size: 1.0625rem; }
          /deep/ h4 { font-size: 0.9375rem; }
          /deep/ h5 { font-size: 0.875rem; }
          /deep/ h6 { font-size: 0.8125rem; }
          
          /deep/ ul, /deep/ ol {
            margin-bottom: 0.75rem;
            padding-left: 1.5rem;
            
            &:last-child {
              margin-bottom: 0;
            }
          }
          
          /deep/ li {
            margin-bottom: 0.25rem;
            line-height: 1.7;
            font-size: 0.875rem;
            color: rgba(255, 255, 255, 0.85);
          }
          
          /deep/ code {
            background: rgba(139, 92, 246, 0.15);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 0.25rem;
            padding: 0.125rem 0.375rem;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
            font-size: 0.8125rem;
            color: rgba(255, 255, 255, 0.95);
          }
          
          /deep/ pre {
            background: rgba(10, 10, 26, 0.8);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: @border-radius-md;
            padding: 0.875rem;
            margin: 0.75rem 0;
            overflow-x: auto;
            
            code {
              background: none;
              border: none;
              padding: 0;
              font-size: 0.8125rem;
              line-height: 1.5;
              display: block;
            }
          }
          
          /deep/ blockquote {
            border-left: 0.25rem solid @primary-color;
            padding-left: 1rem;
            margin: 0.75rem 0;
            color: rgba(255, 255, 255, 0.75);
            font-style: italic;
          }
          
          /deep/ table {
            width: 100%;
            border-collapse: collapse;
            margin: 0.75rem 0;
            font-size: 0.875rem;
            
            th, td {
              border: 1px solid rgba(59, 130, 246, 0.3);
              padding: 0.5rem 0.75rem;
              text-align: left;
            }
            
            th {
              background: rgba(59, 130, 246, 0.15);
              font-weight: @font-weight-semibold;
              color: rgba(255, 255, 255, 0.95);
            }
            
            tr:nth-child(even) {
              background: rgba(255, 255, 255, 0.02);
            }
          }
          
          /deep/ a {
            color: @primary-light;
            text-decoration: none;
            border-bottom: 1px solid rgba(90, 200, 250, 0.3);
            transition: all @transition-base;
            
            &:hover {
              color: #FFFFFF;
              border-bottom-color: @primary-light;
            }
          }
          
          /deep/ strong {
            font-weight: @font-weight-semibold;
            color: rgba(255, 255, 255, 0.95);
          }
          
          /deep/ em {
            font-style: italic;
            color: rgba(255, 255, 255, 0.9);
          }
          
          /deep/ hr {
            border: none;
            border-top: 1px solid rgba(59, 130, 246, 0.3);
            margin: 1rem 0;
          }
          
          /deep/ img {
            max-width: 100%;
            height: auto;
            border-radius: @border-radius-md;
            margin: 0.5rem 0;
          }
        }
        
        // 滚动条样式
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
  }
}

// 右侧面板：对话区域
.right-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

// 对话容器
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: @border-radius-lg;
  overflow: hidden;
  position: relative;
  min-height: 0;
}

// 加载覆盖层
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  
  .loading-text {
    margin-top: 1rem;
    color: rgba(255, 255, 255, 0.9);
    font-size: 1rem;
  }
  
  .spin-icon-load {
    color: @primary-color;
  }
}

// 消息区域
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.message-item {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;

  &.user {
    flex-direction: row-reverse;

    .message-content {
      align-items: flex-end;
    }

    .message-text {
      background: linear-gradient(135deg, @primary-color, @primary-light);
      color: #FFFFFF;
    }
  }

  &.assistant {
    .message-avatar {
      background: linear-gradient(135deg, @accent-color, #FFB84D);
    }
  }

  .message-avatar {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    background: linear-gradient(135deg, @primary-light, @primary-color);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #FFFFFF;
    flex-shrink: 0;

    .ivu-icon {
      font-size: 1.25rem;
    }
  }

  .message-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .message-text {
    background: rgba(255, 255, 255, 0.1);
    padding: 0.875rem 1.125rem;
    border-radius: @border-radius-md;
    color: #FFFFFF;
    font-size: 0.9375rem;
    line-height: 1.65;
    max-width: 80%;
    white-space: pre-wrap;
    word-break: break-word;
    
    // Markdown样式
    &.markdown-content {
      white-space: normal;
      
      /deep/ * {
        margin: 0;
        padding: 0;
      }
      
      /deep/ p {
        margin-bottom: 0.75rem;
        line-height: 1.7;
        font-size: 0.9375rem;
        
        &:last-child {
          margin-bottom: 0;
        }
      }
      
      /deep/ h1, /deep/ h2, /deep/ h3, /deep/ h4, /deep/ h5, /deep/ h6 {
        font-weight: @font-weight-semibold;
        margin-top: 1.25rem;
        margin-bottom: 0.75rem;
        color: rgba(255, 255, 255, 0.95);
        
        &:first-child {
          margin-top: 0;
        }
      }
      
      /deep/ h1 { font-size: 1.625rem; }
      /deep/ h2 { font-size: 1.375rem; }
      /deep/ h3 { font-size: 1.1875rem; }
      /deep/ h4 { font-size: 1.0625rem; }
      /deep/ h5 { font-size: 1rem; }
      /deep/ h6 { font-size: 0.9375rem; }
      
      /deep/ ul, /deep/ ol {
        margin-bottom: 0.75rem;
        padding-left: 1.5rem;
        
        &:last-child {
          margin-bottom: 0;
        }
      }
      
      /deep/ li {
        margin-bottom: 0.25rem;
        line-height: 1.6;
        font-size: 0.9375rem;
      }
      
      /deep/ code {
        background: rgba(139, 92, 246, 0.15);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 0.25rem;
        padding: 0.125rem 0.375rem;
        font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.95);
      }
      
      /deep/ pre {
        background: rgba(10, 10, 26, 0.6);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: @border-radius-md;
        padding: 0.875rem;
        margin: 0.75rem 0;
        overflow-x: auto;
        
        code {
          background: none;
          border: none;
          padding: 0;
          font-size: 0.875rem;
          line-height: 1.5;
          display: block;
        }
      }
      
      /deep/ blockquote {
        border-left: 0.25rem solid @primary-color;
        padding-left: 1rem;
        margin: 0.75rem 0;
        color: rgba(255, 255, 255, 0.8);
        font-style: italic;
      }
      
      /deep/ table {
        width: 100%;
        border-collapse: collapse;
        margin: 0.75rem 0;
        font-size: 0.9375rem;
        
        th, td {
          border: 1px solid rgba(59, 130, 246, 0.3);
          padding: 0.5rem 0.75rem;
          text-align: left;
        }
        
        th {
          background: rgba(59, 130, 246, 0.15);
          font-weight: @font-weight-semibold;
        }
        
        tr:nth-child(even) {
          background: rgba(255, 255, 255, 0.02);
        }
      }
      
      /deep/ a {
        color: @primary-light;
        text-decoration: none;
        border-bottom: 1px solid rgba(90, 200, 250, 0.3);
        transition: all @transition-base;
        
        &:hover {
          color: #FFFFFF;
          border-bottom-color: @primary-light;
        }
      }
      
      /deep/ strong {
        font-weight: @font-weight-semibold;
        color: rgba(255, 255, 255, 0.95);
      }
      
      /deep/ em {
        font-style: italic;
        color: rgba(255, 255, 255, 0.9);
      }
      
      /deep/ hr {
        border: none;
        border-top: 1px solid rgba(59, 130, 246, 0.3);
        margin: 1rem 0;
      }
      
      /deep/ img {
        max-width: 100%;
        height: auto;
        border-radius: @border-radius-md;
        margin: 0.5rem 0;
      }
    }
  }

  .message-time {
    font-size: 0.8125rem;
    color: rgba(255, 255, 255, 0.5);
  }
}

// AI思考指示器
.thinking-indicator {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;

  span {
    width: 0.5rem;
    height: 0.5rem;
    background: rgba(255, 255, 255, 0.6);
    border-radius: 50%;
    animation: thinking 1.4s infinite ease-in-out;

    &:nth-child(1) {
      animation-delay: 0s;
    }

    &:nth-child(2) {
      animation-delay: 0.2s;
    }

    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}

@keyframes thinking {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: scale(1);
  }
  30% {
    opacity: 1;
    transform: scale(1.2);
  }
}

// 输入区域
.input-area {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1rem 1.5rem;
  
  // 输入模式切换
  .input-mode-switch {
    display: flex;
    background: rgba(26, 26, 46, 0.6);
    border-radius: @border-radius-lg;
    padding: 0.25rem;
    gap: 0.25rem;
    backdrop-filter: blur(1.25rem);
    border: 1px solid rgba(59, 130, 246, 0.2);
    margin-bottom: 1rem;
    
    .mode-tab {
      flex: 1;
      padding: 0.5rem 1rem;
      border-radius: @border-radius-md;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      cursor: pointer;
      transition: all @transition-base;
      color: rgba(255, 255, 255, 0.6);
      
      &:hover {
        color: rgba(255, 255, 255, 0.9);
        background: rgba(59, 130, 246, 0.1);
      }
      
      &.active {
        background: @primary-color;
        color: #FFFFFF;
      }
      
      .ivu-icon {
        font-size: 1rem;
      }
      
      span {
        font-size: 0.875rem;
        font-weight: @font-weight-medium;
      }
    }
  }
  
  // 文字输入
  .text-input-wrapper {
    .completed-notice {
      padding: 1rem 1.5rem;
      background: rgba(52, 199, 89, 0.1);
      border: 1px solid rgba(52, 199, 89, 0.3);
      border-radius: @border-radius-md;
      display: flex;
      align-items: center;
      gap: 0.75rem;
      color: @success-color;
      font-size: 0.9375rem;
      
      .ivu-icon {
        font-size: 1.25rem;
        flex-shrink: 0;
      }
    }
    
    .input-box {
      display: flex;
      gap: 0.875rem;
      align-items: flex-start;
      
      .chat-input {
        flex: 1;

        /deep/ .ivu-input {
          background: rgba(26, 26, 46, 0.8);
          border: 1px solid rgba(59, 130, 246, 0.25);
          color: rgba(255, 255, 255, 0.9);
          resize: none;
          border-radius: @border-radius-lg;
          padding: 0.625rem 0.875rem;
          font-size: 0.9375rem;
          line-height: 1.4;
          transition: all @transition-base;
          min-height: auto;
          height: auto;

          &::placeholder {
            color: rgba(255, 255, 255, 0.4);
          }

          &:focus {
            border-color: @primary-color;
            background: rgba(26, 26, 46, 0.95);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
          }
          
          // 滚动条样式
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
        width: 2.75rem;
        height: 2.75rem;
        padding: 0;
        background: linear-gradient(135deg, @primary-color, @accent-color);
        border: none;
        border-radius: 50%;
        transition: all @transition-base;
        flex-shrink: 0;
        
        .ivu-icon {
          font-size: 1.25rem;
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
  
  // ==================== 语音录音界面 ====================
  .voice-input-wrapper {
    width: 100%;
    
    .completed-notice {
      padding: 1.5rem 2rem;
      background: rgba(52, 199, 89, 0.1);
      border: 1px solid rgba(52, 199, 89, 0.3);
      border-radius: @border-radius-lg;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.75rem;
      color: @success-color;
      font-size: 0.9375rem;
      
      .ivu-icon {
        font-size: 1.5rem;
        flex-shrink: 0;
      }
    }
    
    // 录音未开始状态
    .voice-idle {
      text-align: center;
      padding: 2rem;
      background: rgba(26, 26, 46, 0.6);
      border-radius: @border-radius-lg;
      backdrop-filter: blur(1.25rem);
      border: 1px solid rgba(59, 130, 246, 0.2);
      
      .start-record-btn {
        width: 100%;
        max-width: 20rem;
        height: 4rem;
        background: linear-gradient(135deg, @primary-color, @accent-color);
        border: none;
        border-radius: @border-radius-lg;
        font-size: 1.125rem;
        font-weight: @font-weight-medium;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.75rem;
        margin: 0 auto;
        transition: all @transition-base;
        
        &:hover {
          background: linear-gradient(135deg, @primary-light, @accent-color);
          box-shadow: 0 0.5rem 1.5rem rgba(59, 130, 246, 0.4);
          transform: translateY(-0.125rem);
        }
      }
      
      .voice-hint {
        margin-top: 1rem;
        color: rgba(255, 255, 255, 0.5);
        font-size: 0.875rem;
      }
    }
    
    // 录音中状态
    .voice-recording {
      padding: 2rem;
      background: rgba(26, 26, 46, 0.6);
      border-radius: @border-radius-lg;
      backdrop-filter: blur(1.25rem);
      border: 1px solid rgba(59, 130, 246, 0.3);
      
      .recording-visualizer {
        text-align: center;
        margin-bottom: 2rem;
        
        .wave-bars {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 0.375rem;
          height: 5rem;
          margin-bottom: 1.5rem;
          
          .wave-bar {
            width: 0.25rem;
            height: 1rem;
            background: linear-gradient(180deg, @primary-light, @primary-color);
            border-radius: 0.125rem;
            animation: wave 1.2s ease-in-out infinite;
          }
          
          @keyframes wave {
            0%, 100% {
              transform: scaleY(0.5);
              opacity: 0.5;
            }
            50% {
              transform: scaleY(2);
              opacity: 1;
            }
          }
        }
        
        .recording-duration {
          font-size: 2.5rem;
          font-weight: @font-weight-bold;
          color: @primary-light;
          font-variant-numeric: tabular-nums;
          margin-bottom: 1rem;
        }
        
        .recording-hint {
          .recording-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.875rem;
            
            .pulse-dot {
              width: 0.5rem;
              height: 0.5rem;
              background: @error-color;
              border-radius: 50%;
              animation: pulse 1.5s ease-in-out infinite;
            }
            
            @keyframes pulse {
              0%, 100% {
                opacity: 1;
                transform: scale(1);
              }
              50% {
                opacity: 0.5;
                transform: scale(0.8);
              }
            }
          }
        }
      }
      
      .recording-controls {
        display: flex;
        justify-content: center;
        gap: 1rem;
        
        .control-btn {
          min-width: 7rem;
          height: 3rem;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          border-radius: @border-radius-md;
          font-weight: @font-weight-medium;
          transition: all @transition-base;
          
          &.cancel-btn {
            background: rgba(255, 59, 48, 0.15);
            border-color: rgba(255, 59, 48, 0.3);
            color: @error-color;
            
            &:hover {
              background: rgba(255, 59, 48, 0.25);
              border-color: @error-color;
            }
          }
          
          &.pause-btn, &.resume-btn {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.2);
            color: rgba(255, 255, 255, 0.9);
            
            &:hover {
              background: rgba(255, 255, 255, 0.1);
              border-color: rgba(255, 255, 255, 0.3);
            }
          }
          
          &.finish-btn {
            background: linear-gradient(135deg, @primary-color, @accent-color);
            border: none;
            
            &:hover {
              background: linear-gradient(135deg, @primary-light, @accent-color);
              box-shadow: 0 0.25rem 0.75rem rgba(59, 130, 246, 0.4);
            }
          }
        }
      }
    }
    
    // 处理中状态（上传、转写、校对）
    .voice-processing {
      padding: 2rem;
      background: rgba(26, 26, 46, 0.6);
      border-radius: @border-radius-lg;
      backdrop-filter: blur(1.25rem);
      border: 1px solid rgba(59, 130, 246, 0.3);
      
      .processing-status {
        margin-bottom: 1.5rem;
        
        .status-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.875rem;
          color: rgba(255, 255, 255, 0.8);
          font-size: 0.9375rem;
          
          .ivu-spin {
            color: @primary-color;
          }
        }
        
        .transcription-result, .refinement-result {
          margin-top: 1rem;
          padding: 1rem;
          background: rgba(59, 130, 246, 0.08);
          border-radius: @border-radius-md;
          border: 1px solid rgba(59, 130, 246, 0.2);
          
          .result-label {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
            font-size: 0.875rem;
            font-weight: @font-weight-medium;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 0.75rem;
            
            .ivu-icon {
              opacity: 0.7;
            }
            
            .corrections-trigger-btn {
              color: rgba(255, 255, 255, 0.6);
              padding: 0.25rem 0.625rem;
              border-radius: @border-radius-sm;
              transition: all @transition-base;
              display: flex;
              align-items: center;
              gap: 0.375rem;
              
              &:hover {
                color: @primary-color;
                background: rgba(59, 130, 246, 0.1);
              }
              
              .ivu-icon {
                opacity: 1;
              }
              
              span {
                font-size: 0.8125rem;
              }
            }
          }
          
          .result-text {
            font-size: 0.9375rem;
            color: rgba(255, 255, 255, 0.9);
            line-height: 1.6;
            padding: 0.75rem;
            background: rgba(10, 10, 26, 0.4);
            border-radius: @border-radius-sm;
            
            &.readonly {
              color: rgba(255, 255, 255, 0.6);
              background: rgba(10, 10, 26, 0.3);
              border: 1px solid rgba(59, 130, 246, 0.1);
            }
          }
          
          .result-text-editable {
            /deep/ .ivu-input {
              background: rgba(10, 10, 26, 0.6);
              border: 1px solid rgba(59, 130, 246, 0.3);
              color: rgba(255, 255, 255, 0.95);
              border-radius: @border-radius-md;
              padding: 0.875rem;
              font-size: 0.9375rem;
              line-height: 1.6;
              transition: all @transition-base;
              
              &:focus {
                border-color: @primary-color;
                background: rgba(10, 10, 26, 0.8);
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
              }
              
              &::placeholder {
                color: rgba(255, 255, 255, 0.4);
              }
            }
          }
        }
        
        .error-message {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.875rem;
          background: rgba(255, 59, 48, 0.1);
          border-radius: @border-radius-md;
          border: 1px solid rgba(255, 59, 48, 0.3);
          color: @error-color;
          font-size: 0.875rem;
          margin-top: 1rem;
        }
      }
      
      // 处理完成后的操作按钮
      .recorded-controls {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 1px solid rgba(59, 130, 246, 0.2);
        
        .control-btn {
          min-width: 9rem;
          height: 3.25rem;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.625rem;
          border-radius: @border-radius-lg;
          font-weight: @font-weight-medium;
          font-size: 0.9375rem;
          transition: all @transition-base;
          border: none;
          
          &:not(.send-audio-btn) {
            background: rgba(255, 255, 255, 0.08);
            color: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(0.625rem);
            
            &:hover {
              background: rgba(255, 255, 255, 0.15);
              transform: translateY(-1px);
              box-shadow: 0 0.25rem 0.75rem rgba(0, 0, 0, 0.2);
            }
            
            &:active {
              transform: translateY(0);
            }
          }
          
          &.send-audio-btn {
            background: linear-gradient(135deg, @primary-color, @accent-color);
            color: #FFFFFF;
            box-shadow: 0 0.25rem 0.75rem rgba(59, 130, 246, 0.3);
            
            &:hover:not(:disabled) {
              background: linear-gradient(135deg, @primary-light, @accent-color);
              box-shadow: 0 0.375rem 1rem rgba(59, 130, 246, 0.5);
              transform: translateY(-2px);
            }
            
            &:active:not(:disabled) {
              transform: translateY(0);
            }
            
            &:disabled {
              opacity: 0.6;
              cursor: not-allowed;
            }
          }
          
          .ivu-icon {
            font-size: 1.125rem;
          }
        }
      }
    }
    
    // 录音完成待发送状态
    .voice-recorded {
      padding: 2rem;
      background: rgba(26, 26, 46, 0.6);
      border-radius: @border-radius-lg;
      backdrop-filter: blur(1.25rem);
      border: 1px solid rgba(59, 130, 246, 0.2);
      
      .recorded-info {
        display: flex;
        align-items: center;
        gap: 1.5rem;
        margin-bottom: 1.5rem;
        padding: 1.5rem;
        background: rgba(59, 130, 246, 0.08);
        border-radius: @border-radius-md;
        border: 1px solid rgba(59, 130, 246, 0.2);
        
        .audio-icon {
          color: @primary-color;
          flex-shrink: 0;
        }
        
        .audio-info {
          flex: 1;
          
          .audio-duration {
            font-size: 1.125rem;
            font-weight: @font-weight-semibold;
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 0.25rem;
          }
          
          .audio-hint {
            font-size: 0.875rem;
            color: rgba(255, 255, 255, 0.6);
          }
        }
      }
      
      .recorded-controls {
        display: flex;
        justify-content: center;
        gap: 1rem;
        
        .control-btn {
          min-width: 8rem;
          height: 3rem;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          border-radius: @border-radius-md;
          font-weight: @font-weight-medium;
          transition: all @transition-base;
          
          &.send-audio-btn {
            background: linear-gradient(135deg, @primary-color, @accent-color);
            border: none;
            
            &:hover:not(:disabled) {
              background: linear-gradient(135deg, @primary-light, @accent-color);
              box-shadow: 0 0.375rem 1rem rgba(59, 130, 246, 0.4);
            }
          }
        }
      }
    }
  }
}

// ==================== 完成研究弹窗样式 ====================
/deep/ .research-complete-modal {
  .ivu-modal {
    // 弹窗整体背景 - 深色科技感
    .ivu-modal-content {
      background: rgba(26, 26, 46, 0.98) !important;
      backdrop-filter: blur(1.25rem);
      border: 1px solid rgba(52, 199, 89, 0.3);
      box-shadow: 0 1.25rem 3.75rem rgba(0, 0, 0, 0.5);
    }
    
    // 弹窗标题
    .ivu-modal-header {
      background: transparent !important;
      border-bottom: 1px solid rgba(52, 199, 89, 0.2);
      padding: 1.25rem 2rem;
      
      .ivu-modal-header-inner {
        color: #FFFFFF !important;
        font-size: 1.125rem;
        font-weight: @font-weight-semibold;
        background: linear-gradient(135deg, @success-color, @primary-light);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
      
      .ivu-icon-ios-close {
        color: rgba(255, 255, 255, 0.6);
        font-size: 1.875rem;
        
        &:hover {
          color: #FFFFFF;
        }
      }
    }
    
    // 弹窗内容区
    .ivu-modal-body {
      padding: 1.5rem 2rem;
      background: transparent !important;
      color: rgba(255, 255, 255, 0.9);
    }
    
    // 弹窗底部
    .ivu-modal-footer {
      background: transparent !important;
      border-top: 1px solid rgba(52, 199, 89, 0.2);
      padding: 1rem 2rem;
      
      .ivu-btn {
        &:not(.ivu-btn-primary) {
          background: rgba(255, 255, 255, 0.05);
          border-color: rgba(255, 255, 255, 0.2);
          color: rgba(255, 255, 255, 0.8);
          
          &:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.3);
            color: #FFFFFF;
          }
        }
        
        &.ivu-btn-primary {
          background: linear-gradient(135deg, @success-color, @primary-light);
          border: none;
          
          &:hover:not(:disabled) {
            background: linear-gradient(135deg, #5ad879, @primary-color);
            box-shadow: 0 0.25rem 0.75rem rgba(52, 199, 89, 0.4);
          }
          
          &:disabled {
            background: rgba(255, 255, 255, 0.1);
            opacity: 0.5;
          }
        }
      }
    }
  }
}

.complete-form {
  .ai-generated-notice {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    padding: 0.875rem 1rem;
    background: rgba(52, 199, 89, 0.08);
    border: 1px solid rgba(52, 199, 89, 0.2);
    border-radius: @border-radius-md;
    margin-bottom: 1.5rem;
    color: rgba(255, 255, 255, 0.85);
    font-size: 0.875rem;
    
    .ivu-icon {
      color: @success-color;
      font-size: 1.125rem;
      flex-shrink: 0;
    }
  }
  
  h4 {
    color: #FFFFFF;
    margin-bottom: 1rem;
    font-size: 1rem;
    font-weight: @font-weight-semibold;
  }

  .findings-list {
    margin-bottom: 1.5rem;
  }

  .finding-item {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    align-items: center;
    
    /deep/ .ivu-input {
      background: rgba(10, 10, 26, 0.6);
      border: 1px solid rgba(52, 199, 89, 0.3);
      color: rgba(255, 255, 255, 0.95);
      font-size: 0.9375rem;
      transition: all @transition-base;
      
      &:focus {
        background: rgba(10, 10, 26, 0.8);
        border-color: @success-color;
        box-shadow: 0 0 0 3px rgba(52, 199, 89, 0.15);
        color: #FFFFFF;
      }
      
      &::placeholder {
        color: rgba(255, 255, 255, 0.4);
      }
    }
    
    .ivu-btn {
      color: rgba(255, 255, 255, 0.6);
      
      &:hover {
        color: @error-color;
      }
    }
  }
  
  /deep/ .ivu-btn-dashed {
    background: rgba(52, 199, 89, 0.05);
    border: 1px dashed rgba(52, 199, 89, 0.3);
    color: @success-color;
    
    &:hover {
      background: rgba(52, 199, 89, 0.1);
      border-color: @success-color;
      color: @success-color;
    }
  }
  
  /deep/ .ivu-input[type="textarea"] {
    background: rgba(10, 10, 26, 0.6);
    border: 1px solid rgba(52, 199, 89, 0.3);
    color: rgba(255, 255, 255, 0.95);
    font-size: 0.9375rem;
    line-height: 1.6;
    transition: all @transition-base;
    
    &:focus {
      background: rgba(10, 10, 26, 0.8);
      border-color: @success-color;
      box-shadow: 0 0 0 3px rgba(52, 199, 89, 0.15);
      color: #FFFFFF;
    }
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.4);
    }
  }
  
  /deep/ .ivu-checkbox-wrapper {
    color: rgba(255, 255, 255, 0.9);
    
    .ivu-checkbox-inner {
      background: rgba(10, 10, 26, 0.6);
      border-color: rgba(52, 199, 89, 0.3);
    }
    
    .ivu-checkbox-checked .ivu-checkbox-inner {
      background: @success-color;
      border-color: @success-color;
    }
    
    &:hover .ivu-checkbox-inner {
      border-color: @success-color;
    }
  }
}

// ==================== 全屏分析动画 ====================
.fullscreen-analyzing {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .analyzing-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(10, 10, 26, 0.95);
    backdrop-filter: blur(1.25rem);
  }
  
  .analyzing-content {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  
  // 科技感加载器
  .tech-loader {
    position: relative;
    width: 10rem;
    height: 10rem;
    margin-bottom: 2rem;
    
    .loader-ring {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      border-radius: 50%;
      border: 2px solid transparent;
      animation: rotate 3s linear infinite;
      
      &.ring-1 {
        width: 10rem;
        height: 10rem;
        border-top-color: @success-color;
        border-right-color: @success-color;
        animation-duration: 3s;
      }
      
      &.ring-2 {
        width: 7.5rem;
        height: 7.5rem;
        border-top-color: @primary-color;
        border-left-color: @primary-color;
        animation-duration: 2s;
        animation-direction: reverse;
      }
      
      &.ring-3 {
        width: 5rem;
        height: 5rem;
        border-top-color: @primary-light;
        border-bottom-color: @primary-light;
        animation-duration: 1.5s;
      }
    }
    
    .loader-icon {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 3rem;
      color: @success-color;
      animation: pulse 2s ease-in-out infinite;
    }
  }
  
  // 文案
  .analyzing-text {
    text-align: center;
    
    h3 {
      font-size: 1.75rem;
      font-weight: @font-weight-semibold;
      color: #FFFFFF;
      margin-bottom: 0.75rem;
      background: linear-gradient(135deg, @success-color, @primary-light);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    p {
      font-size: 1rem;
      color: rgba(255, 255, 255, 0.7);
    }
  }
  
  // 粒子效果
  .tech-particles {
    position: absolute;
    width: 100%;
    height: 100%;
    pointer-events: none;
    
    .particle {
      position: absolute;
      width: 0.25rem;
      height: 0.25rem;
      background: @success-color;
      border-radius: 50%;
      opacity: 0;
      animation: particle-float 3s ease-in-out infinite;
      box-shadow: 0 0 0.5rem @success-color;
      
      &:nth-child(1) { left: 15%; top: 20%; animation-delay: 0s; animation-duration: 2.5s; }
      &:nth-child(2) { left: 85%; top: 15%; animation-delay: 0.5s; animation-duration: 3s; }
      &:nth-child(3) { left: 25%; top: 75%; animation-delay: 1s; animation-duration: 2.8s; }
      &:nth-child(4) { left: 70%; top: 80%; animation-delay: 1.5s; animation-duration: 3.2s; }
      &:nth-child(5) { left: 50%; top: 10%; animation-delay: 0.3s; animation-duration: 2.6s; }
      &:nth-child(6) { left: 90%; top: 50%; animation-delay: 2s; animation-duration: 3.5s; }
      &:nth-child(7) { left: 10%; top: 60%; animation-delay: 0.8s; animation-duration: 2.9s; }
      &:nth-child(8) { left: 40%; top: 30%; animation-delay: 1.2s; animation-duration: 3.1s; }
      &:nth-child(9) { left: 60%; top: 65%; animation-delay: 0.6s; animation-duration: 2.7s; }
      &:nth-child(10) { left: 30%; top: 45%; animation-delay: 1.8s; animation-duration: 3.3s; }
      &:nth-child(11) { left: 80%; top: 25%; animation-delay: 0.4s; animation-duration: 2.4s; }
      &:nth-child(12) { left: 20%; top: 85%; animation-delay: 1.4s; animation-duration: 3.4s; }
      &:nth-child(13) { left: 65%; top: 40%; animation-delay: 0.9s; animation-duration: 2.8s; }
      &:nth-child(14) { left: 45%; top: 70%; animation-delay: 1.6s; animation-duration: 3s; }
      &:nth-child(15) { left: 75%; top: 55%; animation-delay: 0.7s; animation-duration: 2.9s; }
      &:nth-child(16) { left: 35%; top: 20%; animation-delay: 1.1s; animation-duration: 3.2s; }
      &:nth-child(17) { left: 55%; top: 90%; animation-delay: 0.2s; animation-duration: 2.6s; }
      &:nth-child(18) { left: 95%; top: 35%; animation-delay: 1.9s; animation-duration: 3.1s; }
      &:nth-child(19) { left: 5%; top: 50%; animation-delay: 1.3s; animation-duration: 2.7s; }
      &:nth-child(20) { left: 50%; top: 95%; animation-delay: 0.1s; animation-duration: 3.3s; }
    }
  }
}

@keyframes rotate {
  0% { transform: translate(-50%, -50%) rotate(0deg); }
  100% { transform: translate(-50%, -50%) rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { 
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
  50% { 
    opacity: 0.7;
    transform: translate(-50%, -50%) scale(1.1);
  }
}

@keyframes particle-float {
  0%, 100% {
    opacity: 0;
    transform: translateY(0) translateX(0);
  }
  50% {
    opacity: 0.7;
    transform: translateY(-1.875rem) translateX(0.625rem);
  }
}

// 淡入淡出过渡
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter, .fade-leave-to {
  opacity: 0;
}

// ==================== 浮动生成报告按钮 ====================
.floating-report-btn {
  position: fixed;
  z-index: 999;
  cursor: move;
  transition: box-shadow @transition-base;
  
  .report-btn {
    width: 3.75rem;
    height: 3.75rem;
    background: linear-gradient(135deg, @success-color, #5ad879);
    border: none;
    box-shadow: 0 0.5rem 1.5rem rgba(52, 199, 89, 0.4);
    transition: all @transition-base;
    
    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #5ad879, @success-color);
      box-shadow: 0 0.75rem 2rem rgba(52, 199, 89, 0.6);
      transform: scale(1.1);
    }
    
    &:active:not(:disabled) {
      transform: scale(1.05);
    }
    
    .ivu-icon {
      color: #FFFFFF;
    }
  }
}

// 修正记录弹窗样式
.corrections-modal-content {
  .corrections-summary {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    padding: 1rem;
    background: rgba(82, 196, 26, 0.08);
    border-radius: @border-radius-md;
    border: 1px solid rgba(82, 196, 26, 0.2);
    margin-bottom: 1.5rem;
    color: @text-primary;
    font-size: 0.9375rem;
    font-weight: @font-weight-medium;
    
    .ivu-icon {
      color: @success-color;
    }
  }
  
  .corrections-list-modal {
    max-height: 25rem;
    overflow-y: auto;
    
    .correction-item-modal {
      display: flex;
      gap: 1rem;
      padding: 1rem;
      margin-bottom: 0.75rem;
      background: rgba(26, 26, 46, 0.05);
      border-radius: @border-radius-md;
      border: 1px solid rgba(59, 130, 246, 0.1);
      transition: all @transition-base;
      
      &:hover {
        background: rgba(59, 130, 246, 0.05);
        border-color: rgba(59, 130, 246, 0.2);
      }
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .correction-number {
        flex-shrink: 0;
        width: 2rem;
        height: 2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, @primary-color, @accent-color);
        color: #FFFFFF;
        border-radius: 50%;
        font-size: 0.875rem;
        font-weight: @font-weight-semibold;
      }
      
      .correction-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 0.625rem;
        
        .correction-row {
          display: flex;
          align-items: flex-start;
          gap: 0.5rem;
          
          .correction-label {
            flex-shrink: 0;
            font-size: 0.875rem;
            font-weight: @font-weight-medium;
            color: @text-secondary;
            min-width: 3rem;
          }
          
          .original-text {
            flex: 1;
            font-size: 0.875rem;
            color: @error-color;
            text-decoration: line-through;
            word-break: break-word;
          }
          
          .corrected-text {
            flex: 1;
            font-size: 0.875rem;
            color: @success-color;
            font-weight: @font-weight-medium;
            word-break: break-word;
          }
        }
      }
    }
  }
  
  // 滚动条样式
  .corrections-list-modal::-webkit-scrollbar {
    width: 0.375rem;
  }
  
  .corrections-list-modal::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.05);
    border-radius: 0.1875rem;
  }
  
  .corrections-list-modal::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.3);
    border-radius: 0.1875rem;
    
    &:hover {
      background: rgba(59, 130, 246, 0.5);
    }
  }
}

// ==================== 响应式适配 ====================
@media (max-width: 1200px) {
  .left-panel {
    width: 350px;
  }
}

@media (max-width: 992px) {
  .content-wrapper {
    padding: 1rem;
  }
  
  .page-header {
    margin-bottom: 1rem;
    
    .page-title {
      font-size: 1.25rem;
    }
    
    .page-description {
      font-size: 0.875rem;
    }
  }
  
  .main-content {
    flex-direction: column;
    gap: 1rem;
  }
  
  .left-panel {
    width: 100%;
    max-height: 300px;
    
    .script-panel {
      .script-content {
        .content-text {
          max-height: 150px;
        }
      }
    }
  }
  
  .right-panel {
    flex: 1;
  }
}

@media (max-width: 768px) {
  .content-wrapper {
    padding: 0.75rem;
  }
  
  .left-panel {
    max-height: 250px;
    
    .script-panel {
      padding: 1rem;
    }
  }
}
</style>

