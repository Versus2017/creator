<template>
  <div class="scripts-container">
    <!-- 科技感背景效果 -->
    <div class="bg-effects">
      <div class="mind-grid"></div>
      
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
      </div>

      <div class="light-particles">
        <div class="particle particle-1"></div>
        <div class="particle particle-2"></div>
        <div class="particle particle-3"></div>
        <div class="particle particle-4"></div>
        <div class="particle particle-5"></div>
        <div class="particle particle-6"></div>
      </div>
    </div>

    <div class="content-wrapper">
      <!-- 左侧边栏 -->
      <div class="sidebar">
        <div class="sidebar-header">
          <Button 
            type="primary" 
            long 
            size="large"
            @click="startNewCreativity"
            class="new-chat-btn"
          >
            <Icon type="md-add" />
            新创意
          </Button>
        </div>
        
        <div class="conversation-list">
          <div 
            v-for="conv in conversations" 
            :key="conv.id"
            class="conversation-item"
            :class="{ active: currentConversation && currentConversation.id === conv.id }"
            @click="selectConversation(conv)"
          >
            <div class="conversation-icon">
              <Icon type="md-document" />
            </div>
            <div class="conversation-info">
              <div class="conversation-title">{{ conv.title || '未命名脚本' }}</div>
              <div class="conversation-meta">{{ formatDate(conv.updated_at) }}</div>
            </div>
            <div class="conversation-actions">
              <Icon type="md-trash" @click.stop="deleteConversation(conv.id)" class="delete-icon" />
            </div>
          </div>
          
          <!-- 空状态 -->
          <div v-if="conversations.length === 0" class="empty-state">
            <Icon type="md-filing" size="48" />
            <p>暂无创作记录</p>
            <p class="empty-hint">点击上方按钮开始创作</p>
          </div>
        </div>
      </div>

      <!-- 对话区域 -->
      <div class="chat-area">
        <!-- 对话消息区域 -->
        <div class="chat-messages" ref="messagesContainer">
          <!-- 欢迎提示 -->
          <div v-if="!currentConversation || messages.length === 0" class="welcome-screen">
            <div class="welcome-icon">✨</div>
            <h3>开始创作您的视频脚本</h3>
            <p>告诉我您的创意想法，我会帮助您创作专业的视频脚本</p>
            
            <div class="suggestion-cards">
              <div class="suggestion-card" @click="useSuggestion('我想创作一个关于健康饮食的科普视频脚本')">
                <Icon type="ios-restaurant" />
                <span>健康饮食科普</span>
              </div>
              <div class="suggestion-card" @click="useSuggestion('帮我写一个产品介绍视频的脚本')">
                <Icon type="ios-cart" />
                <span>产品介绍视频</span>
              </div>
              <div class="suggestion-card" @click="useSuggestion('我需要一个教程类视频的脚本')">
                <Icon type="ios-school" />
                <span>教程类视频</span>
              </div>
              <div class="suggestion-card" @click="useSuggestion('创作一个Vlog视频脚本')">
                <Icon type="ios-videocam" />
                <span>Vlog脚本</span>
              </div>
            </div>
          </div>

          <!-- 消息列表 -->
          <div v-else class="messages-list">
            <div 
              v-for="(message, index) in messages" 
              :key="index"
              class="message-item"
            >
              <!-- 用户消息 -->
              <div v-if="message.role === 'user'" class="message user-message">
                <div class="message-avatar user-avatar">
                  <img v-if="currentUser && currentUser.avatar" :src="currentUser.avatar" alt="用户头像" class="avatar-image" />
                  <Icon v-else type="md-person" />
                </div>
                <div class="message-bubble">
                  <div
                    v-if="message.referenced_scripts_meta && message.referenced_scripts_meta.length"
                    class="referenced-scripts-meta"
                  >
                    <Icon type="ios-link" size="14" />
                    <span class="referenced-label">引用了</span>
                    <span
                      v-for="(refScript, refIndex) in message.referenced_scripts_meta"
                      :key="refScript.id || refIndex"
                      class="referenced-script-link"
                      @click.stop="goScriptDetail(refScript.id)"
                    >《{{ refScript.title }}》</span>
                  </div>
                  <div class="message-content">{{ message.content }}</div>
                  <div class="message-footer">
                    <span class="message-time">{{ formatTime(message.created_at) }}</span>
                  </div>
                </div>
              </div>

              <!-- AI回复 -->
              <div v-else class="message ai-message">
                <div class="message-avatar ai-avatar">
                  <span class="ai-text">AI</span>
                </div>
                <div class="message-bubble">
                  <div class="message-header">
                    <span class="ai-label">AI助手</span>
                  </div>
                  <div
                    class="message-content markdown-content"
                    :class="{ 'is-waiting': isAiMessageWaiting(message, index) }"
                  >
                    <span
                      v-if="isAiMessageWaiting(message, index)"
                      class="ai-typing-cursor"
                      aria-label="AI 正在思考"
                    ></span>
                    <template v-else>
                      <span class="markdown-body" v-html="renderMarkdown(message.content)"></span>
                      <span
                        v-if="isAiMessageStreaming(message, index)"
                        class="ai-typing-cursor ai-typing-cursor--inline"
                        aria-hidden="true"
                      ></span>
                    </template>
                  </div>
                  <div class="message-footer">
                    <span class="message-time">{{ formatTime(message.created_at) }}</span>
                    <div class="message-actions">
                      <Button type="text" size="small" icon="md-copy" @click="copyMessage(message.content)">复制</Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input-section">
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

          <!-- 已引用脚本（显示在输入框上方） -->
          <div
            v-if="referencedScripts.length > 0"
            class="referenced-scripts-summary"
          >
            <Icon type="ios-link" size="14" class="summary-icon" />
            <span class="summary-label">已引用：</span>
            <div class="summary-titles">
              <span
                v-for="script in referencedScripts"
                :key="script.id"
                class="summary-title-item"
              >
                <span
                  class="summary-title-text"
                  @click="goScriptDetail(script.id)"
                >《{{ script.title }}》</span>
                <Icon
                  type="md-close"
                  class="summary-title-remove"
                  @click.stop="removeReferencedScript(script.id)"
                />
              </span>
            </div>
          </div>

          <!-- 文字输入模式 -->
          <div v-if="inputMode === 'text'" class="text-input-column">
            <div class="script-reference-bar">
              <Button
                type="default"
                size="small"
                class="reference-script-btn"
                :disabled="isLoading"
                @click="openScriptPicker"
              >
                <Icon type="ios-link" />
                引用脚本
              </Button>
              <span v-if="referencedScripts.length === 0" class="reference-hint">可选：引用历史脚本作为分析上下文（最多{{ maxReferencedScripts }}个）</span>
            </div>
            <div class="input-wrapper">
            <Input
              ref="chatInput"
              v-model="userInput"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 6 }"
              placeholder="描述您的创意和需求... (Enter发送 / Shift+Enter换行)"
              :disabled="isLoading"
              @keydown.native="handleKeyDown"
              class="chat-input"
            />
            
            <Button
              type="primary"
              size="large"
              class="send-btn"
              :loading="isLoading"
              :disabled="!userInput.trim()"
              @click="sendMessage"
            >
              <Icon type="md-send" />
            </Button>
            </div>
          </div>

          <!-- 语音录音模式 -->
          <div v-else class="voice-input-wrapper">
            <!-- 录音未开始（仅在没有任何处理状态时显示） -->
            <div v-if="!isRecording && !recordedAudio && !currentVoiceMessageId && !isUploadingAudio && !voiceStatus.transcription.isActive && !voiceStatus.refinement.isActive && !voiceProcessingComplete" class="voice-idle">
              <div v-if="audioInputDevices.length > 0" class="mic-device-select">
                <span class="mic-device-label">麦克风</span>
                <Select
                  v-model="selectedAudioDeviceId"
                  placeholder="系统默认"
                  size="small"
                  style="width: 100%"
                >
                  <Option
                    v-for="dev in audioInputDevices"
                    :key="dev.deviceId"
                    :value="dev.deviceId"
                    :label="dev.label || ('麦克风 ' + dev.deviceId.slice(0, 8))"
                  />
                </Select>
              </div>
              <Button
                type="primary"
                size="large"
                class="start-record-btn"
                @click="startRecording"
              >
                <Icon type="md-mic" size="24" />
                <span>点击开始录音</span>
              </Button>
              <p class="voice-hint">最长支持 15 分钟；不足 15 秒的录音将在完成后一次性识别，长录音约每 12 秒增量识别。若录出来全是杂音，请换用「内建麦克风」。</p>
            </div>

            <!-- 录音中 -->
            <div v-if="isRecording" class="voice-recording">
              <div class="recording-visualizer">
                <!-- 实时麦克风音量（说话时应明显跳动） -->
                <div class="mic-level-wrap">
                  <div class="mic-level-bar">
                    <div class="mic-level-fill" :style="{ width: micLevel + '%' }"></div>
                  </div>
                  <span class="mic-level-label">输入音量 {{ micLevel }}%</span>
                </div>
                
                <!-- 录音时长 -->
                <div class="recording-duration">{{ formattedRecordingDuration }}</div>
                
                <!-- 录音提示 -->
                <div class="recording-hint">
                  <div class="recording-indicator">
                    <span class="pulse-dot"></span>
                    <span>录音中...</span>
                  </div>
                  <div v-if="currentVoiceMessageId" class="recording-stream-hint">
                    <Spin v-if="voiceStatus.transcription.isActive" size="small"></Spin>
                    <span v-if="voiceStatus.transcription.processedChunks > 0">
                      已识别 {{ voiceStatus.transcription.processedChunks }} 段
                    </span>
                    <span v-else-if="isProcessingChunkQueue || isUploadingAudio">正在上传并识别...</span>
                  </div>
                  <div
                    v-if="currentVoiceMessageId && voiceStatus.transcription.partialText"
                    class="recording-partial-text"
                  >
                    {{ voiceStatus.transcription.partialText }}
                  </div>
                </div>
              </div>

              <!-- 控制按钮 -->
              <div class="recording-controls">
                <Button
                  size="large"
                  class="control-btn cancel-btn"
                  @click="cancelRecording"
                >
                  <Icon type="md-close" size="20" />
                  <span>取消</span>
                </Button>
                
                <Button
                  v-if="!isPaused"
                  size="large"
                  class="control-btn pause-btn"
                  @click="pauseRecording"
                >
                  <Icon type="md-pause" size="20" />
                  <span>暂停</span>
                </Button>
                
                <Button
                  v-else
                  size="large"
                  class="control-btn resume-btn"
                  @click="resumeRecording"
                >
                  <Icon type="md-play" size="20" />
                  <span>继续</span>
                </Button>
                
                <Button
                  type="primary"
                  size="large"
                  class="control-btn finish-btn"
                  @click="finishRecording"
                >
                  <Icon type="md-checkmark" size="20" />
                  <span>完成</span>
                </Button>
              </div>
            </div>

            <!-- 录音完成，处理中（包括上传、转写、校对） -->
            <div v-if="!isRecording && currentVoiceMessageId && (isUploadingAudio || voiceStatus.transcription.isActive || voiceStatus.refinement.isActive || voiceProcessingComplete || voiceStatus.transcription.error)" class="voice-processing">
              <div class="processing-status">
                <!-- 上传中 -->
                <div v-if="isUploadingAudio" class="status-item">
                  <Spin size="small"></Spin>
                  <span>正在上传音频...</span>
                </div>
                
                <!-- 转写中 -->
                <div v-if="!isUploadingAudio && voiceStatus.transcription.isActive && !voiceStatus.transcription.isCompleted" class="status-item">
                  <Spin size="small"></Spin>
                  <span v-if="voiceStatus.transcription.processedChunks > 0">
                    已识别 {{ voiceStatus.transcription.processedChunks }} 段，继续转写中...
                  </span>
                  <span v-else>正在转写语音...</span>
                </div>
                
                <!-- 流式转写：实时显示已识别的部分文本 -->
                <div v-if="!isUploadingAudio && voiceStatus.transcription.isActive && voiceStatus.transcription.partialText" class="partial-transcription">
                  <div class="result-label">
                    <Icon type="md-pulse" size="14" />
                    <span>实时识别（转写中）：</span>
                  </div>
                  <div class="result-text readonly partial">{{ voiceStatus.transcription.partialText }}</div>
                </div>
                
                <!-- 转写完成，显示可编辑文本 -->
                <div v-if="voiceStatus.transcription.isCompleted && voiceStatus.transcription.text" class="transcription-result">
                  <div class="result-label">
                    <Icon type="md-mic" size="14" />
                    <span>语音识别内容（可编辑后发送）：</span>
                  </div>
                  <Input
                    v-model="voiceConfirmedContent"
                    type="textarea"
                    :autosize="{ minRows: 3, maxRows: 8 }"
                    class="result-text-editable"
                    placeholder="您可以在此编辑文本..."
                  />
                </div>
                
                <!-- 转写失败但有部分结果 -->
                <div v-if="voiceStatus.transcription.error && voiceStatus.transcription.partialText && !voiceStatus.transcription.isCompleted" class="partial-transcription">
                  <div class="result-label">
                    <Icon type="md-pulse" size="14" />
                    <span>已识别部分内容（可编辑后发送）：</span>
                  </div>
                  <Input
                    v-model="voiceConfirmedContent"
                    type="textarea"
                    :autosize="{ minRows: 3, maxRows: 8 }"
                    class="result-text-editable"
                    placeholder="您可以在此编辑文本..."
                  />
                </div>

                <!-- 错误提示 -->
                <div v-if="voiceStatus.transcription.error || voiceStatus.refinement.error" class="error-message">
                  <Icon type="md-alert" />
                  <span>{{ voiceStatus.transcription.error || voiceStatus.refinement.error }}</span>
                </div>
              </div>

              <!-- 转写失败后的操作 -->
              <div v-if="voiceStatus.transcription.error && !voiceProcessingComplete" class="recorded-controls">
                <Button
                  size="large"
                  class="control-btn"
                  @click="reRecord"
                >
                  <Icon type="md-refresh" size="20" />
                  <span>重录</span>
                </Button>
                <Button
                  v-if="voiceStatus.transcription.partialText"
                  size="large"
                  class="control-btn"
                  @click="retryVoiceFinalize"
                >
                  <Icon type="md-sync" size="20" />
                  <span>合并已识别内容</span>
                </Button>
                <Button
                  v-if="voiceConfirmedContent && voiceConfirmedContent.trim()"
                  type="primary"
                  size="large"
                  class="control-btn send-audio-btn"
                  :loading="isConfirmingVoice"
                  @click="confirmVoiceContent"
                >
                  <Icon type="md-checkmark" size="20" />
                  <span>使用当前内容发送</span>
                </Button>
              </div>

              <!-- 处理完成后的操作按钮 -->
              <div v-if="voiceProcessingComplete" class="recorded-controls">
                <Button
                  size="large"
                  class="control-btn"
                  @click="reRecord"
                >
                  <Icon type="md-refresh" size="20" />
                  <span>重录</span>
                </Button>
                
                <Button
                  type="primary"
                  size="large"
                  class="control-btn send-audio-btn"
                  :loading="isConfirmingVoice"
                  :disabled="isConfirmingVoice || autoConfirmTriggered"
                  @click="confirmVoiceContent"
                >
                  <Icon type="md-checkmark" size="20" />
                  <span>确认发送</span>
                </Button>
              </div>
            </div>

            <!-- 录音完成，待发送（如果用户取消了自动上传或出错，保留手动发送选项） -->
            <div v-if="!isRecording && recordedAudio && !isUploadingAudio && !voiceStatus.transcription.isActive && !voiceStatus.refinement.isActive && !voiceProcessingComplete" class="voice-recorded">
              <div class="recorded-info">
                <Icon type="ios-musical-notes" size="32" class="audio-icon" />
                <div class="audio-info">
                  <div class="audio-duration">录音时长: {{ formattedRecordedDuration }}</div>
                  <div class="audio-hint">准备重新上传</div>
                </div>
              </div>

              <div class="recorded-controls">
                <Button
                  size="large"
                  class="control-btn"
                  @click="reRecord"
                >
                  <Icon type="md-refresh" size="20" />
                  <span>重录</span>
                </Button>
                
                <Button
                  type="primary"
                  size="large"
                  class="control-btn send-audio-btn"
                  @click="sendVoiceMessage"
                >
                  <Icon type="md-send" size="20" />
                  <span>重新发送</span>
                </Button>
              </div>
            </div>
          </div>

          <!-- 导出对话（左下角） -->
          <div
            v-if="currentConversation && messages.length > 0"
            class="chat-export-bar"
          >
            <Button
              type="text"
              size="small"
              icon="md-download"
              :loading="isExporting"
              :disabled="isLoading"
              class="export-chat-btn"
              @click="exportConversation"
            >
              导出对话
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- 悬浮生成脚本按钮 -->
    <div 
      v-if="currentConversation && messages.length > 0"
      class="floating-generate-btn"
      :style="{ left: floatBtnPosition.x + 'px', top: floatBtnPosition.y + 'px' }"
      @mousedown="startDrag"
    >
      <Tooltip content="提取视频脚本" placement="left">
        <Button 
          type="primary" 
          shape="circle" 
          size="large"
          class="generate-btn"
          :loading="isExtractingScript"
          @click="showGenerateModal"
        >
          <Icon v-if="!isExtractingScript" type="ios-paper" size="24" />
        </Button>
      </Tooltip>
    </div>

    <!-- 全屏提取动画 -->
    <transition name="fade">
      <div v-if="isExtractingScript" class="fullscreen-extracting">
        <div class="extracting-overlay"></div>
        <div class="extracting-content">
          <!-- 科技感加载动画 -->
          <div class="tech-loader">
            <!-- 旋转的圆环 -->
            <div class="loader-ring ring-1"></div>
            <div class="loader-ring ring-2"></div>
            <div class="loader-ring ring-3"></div>
            
            <!-- 中心图标 -->
            <Icon type="ios-paper" class="loader-icon" />
          </div>
          
          <!-- 文案 -->
          <div class="extracting-text">
            <h3>脚本整理中...</h3>
            <p>正在从对话中提取脚本内容</p>
          </div>
          
          <!-- 粒子效果 -->
          <div class="tech-particles">
            <div class="particle" v-for="i in 20" :key="i"></div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 脚本编辑弹窗 -->
    <Modal
      v-model="showScriptEditModal"
      title="生成的视频脚本"
      width="800"
      :mask-closable="false"
      class-name="script-edit-modal"
    >
      <div class="script-edit-form">
        <!-- 主标题 -->
        <div class="form-item">
          <label>主标题（可选）</label>
          <Input 
            v-model="extractedScript.title" 
            placeholder="请输入主标题"
            size="large"
          />
        </div>
        
        <!-- 副标题 -->
        <div class="form-item">
          <label>副标题（可选）</label>
          <Input 
            v-model="extractedScript.subtitle" 
            placeholder="请输入副标题"
            size="large"
          />
        </div>
        
        <!-- 脚本内容 -->
        <div class="form-item">
          <label class="label-with-count">
            <span>脚本内容（必填）</span>
            <span class="word-count">{{ extractedScript.word_count }}字</span>
          </label>
          <Input
            v-model="extractedScript.content"
            type="textarea"
            :autosize="{ minRows: 15, maxRows: 30 }"
            placeholder="脚本内容"
            @on-change="updateWordCount"
          />
        </div>
      </div>

      <div slot="footer">
        <Button @click="closeScriptEdit">取消</Button>
        <Button 
          type="primary" 
          @click="saveScript" 
          :loading="isSavingScript"
          :disabled="!extractedScript.content || !extractedScript.content.trim()"
        >
          <Icon type="md-checkmark" />
          保存
        </Button>
      </div>
    </Modal>

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

    <!-- 引用脚本选择弹窗 -->
    <Modal
      v-model="showScriptPickerModal"
      title="引用历史脚本"
      width="640"
      class-name="script-picker-modal"
      @on-visible-change="onScriptPickerVisibleChange"
    >
      <div class="script-picker-content">
        <Input
          v-model="scriptPickerKeyword"
          search
          placeholder="搜索脚本标题..."
          @on-search="loadScriptPickerList"
        />
        <div v-if="scriptPickerLoading" class="script-picker-loading">
          <Spin />
          <span>加载中...</span>
        </div>
        <div v-else-if="scriptPickerList.length === 0" class="script-picker-empty">
          暂无脚本，请先在对话中提取并保存脚本
        </div>
        <div v-else class="script-picker-list">
          <div
            v-for="script in scriptPickerList"
            :key="script.id"
            class="script-picker-item"
            :class="{ selected: isScriptSelected(script.id), disabled: isScriptPickerItemDisabled(script.id) }"
            @click="toggleScriptSelection(script)"
          >
            <Checkbox
              :value="isScriptSelected(script.id)"
              :disabled="isScriptPickerItemDisabled(script.id)"
              @click.native.stop
            />
            <div class="script-picker-item-body">
              <div class="script-picker-title">{{ script.title }}</div>
              <div class="script-picker-meta">
                <span>{{ script.word_count || 0 }} 字</span>
                <span v-if="script.updated_at">{{ formatScriptDate(script.updated_at) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="script-picker-footer-hint">
          已选 {{ referencedScripts.length }} / {{ maxReferencedScripts }} 个脚本
        </div>
      </div>
      <div slot="footer">
        <Button type="primary" @click="showScriptPickerModal = false">确定</Button>
      </div>
    </Modal>

  </div>
</template>

<script>
  import moment from 'moment'
  import { SSE } from '@/libs/sse'
  import { getCookie } from '@/libs/util'
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
    name: 'Creativity',

    data () {
      return {
        // 对话列表
        conversations: [],
        currentConversation: null,
        
        // 消息列表
        messages: [],
        
        // 用户输入
        userInput: '',
        
        // 加载状态
        isLoading: false,
        isExporting: false,
        
        // SSE 连接
        sseConnection: null,
        _streamChatFinishing: false,
        
        // 当前AI消息索引
        currentAiMessageIndex: -1,
        
        // 悬浮按钮位置
        floatBtnPosition: {
          x: 0,
          y: 0
        },
        isDragging: false,
        dragStartX: 0,
        dragStartY: 0,
        
        // 生成脚本相关（改为提取脚本）
        isExtractingScript: false,  // 全屏动画显示状态
        showScriptEditModal: false,  // 编辑弹窗
        extractedScript: {
          title: '',        // 主标题
          subtitle: '',     // 副标题（新增）
          content: '',      // 脚本内容
          word_count: 0
        },
        isSavingScript: false,  // 保存中状态
        
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
        
        // 流式分块录音状态
        streamChunkIndex: 0,
        streamChunkMinDurationSec: 15, // 低于此时长不切片，完成时一次性上传
        streamChunkIntervalMs: 12000,  // 长录音：首片后每 12 秒一片
        streamMidChunkStarted: false,  // 是否已触发过中途切片（区分短/长录音）
        recordMimeType: 'audio/webm',
        chunkUploadQueue: [],
        isProcessingChunkQueue: false,
        _streamChunkTimer: null,
        
        // 麦克风设备与电平监测
        audioInputDevices: [],
        selectedAudioDeviceId: '',
        micLevel: 0,
        recordingStream: null,
        
        // 上传状态
        isUploadingAudio: false,
        isFinishingRecording: false, // 防止重复调用完成录音
        voiceRecordingCancelled: false, // 取消录音后阻断分块上传与转写
        validFinalChunkUploaded: false, // 已成功上传有效最终块（避免 stop 空尾片重复收尾）
        _voiceFinalizeAttempted: false,
        
        // 语音处理状态
        voiceProcessingComplete: false,
        currentVoiceMessageId: null,
        voicePollingTimer: null,
        voiceEventSource: null,
        _voiceStatusWaitActive: false,
        voiceStatus: {
          transcription: {
            isActive: false,
            isCompleted: false,
            text: '',
            error: '',
            partialText: '',     // 流式模式：正在转写中的已识别文本
            processedChunks: 0  // 流式模式：已处理的块数
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

        // 引用历史脚本
        maxReferencedScripts: 3,
        referencedScripts: [],
        showScriptPickerModal: false,
        scriptPickerLoading: false,
        scriptPickerList: [],
        scriptPickerKeyword: '',
      }
    },

    computed: {
      // 当前登录用户 - 从 store 获取
      currentUser() {
        return this.$store.getters.user || {}
      },
      
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
      // 开始新创意（清空状态，不创建会话）
      startNewCreativity () {
        // 关闭SSE连接
        this.closeSseConnection()
        
        // 清空当前选中的会话
        this.currentConversation = null
        
        // 清空消息列表
        this.messages = []
        
        // 清空输入框与待发送的引用
        this.userInput = ''
        this.clearPendingScriptReferences()
      },
      
      // 创建新会话（在发送第一条消息时调用）
      async createNewConversation () {
        try {
          const response = await this.$http.post('/web/conversations', {
            title: '未命名脚本',
            topic: '视频脚本创作'
          })
          
          if (response && response.success) {
            this.conversations.unshift(response.data)
            this.currentConversation = response.data
            return true
          }
        } catch (error) {
          console.error('创建会话失败:', error)
          this.$Message.error('创建会话失败，请重试')
          return false
        }
      },
      
      // 选择对话
      async selectConversation (conv, skipLoadMessages = false) {
        // 先关闭之前的SSE连接（会自动重置索引）
        this.closeSseConnection()
        this.clearPendingScriptReferences()

        this.currentConversation = conv
        
        // 如果指定跳过加载消息（例如新创建的会话），则清空消息列表
        if (skipLoadMessages) {
          this.messages = []
        } else {
          await this.loadMessages(conv.id)
        }
      },
      
      // 加载消息
      async loadMessages (conversationId) {
        // 如果有活动的 SSE 连接，不要加载消息（避免覆盖正在流式更新的消息）
        if (this.sseConnection) {
          console.warn('SSE 连接活动中，跳过消息加载')
          return
        }
        
        try {
          const response = await this.$http.get(`/web/conversations/${conversationId}/messages`)
          
          if (response && response.success) {
            this.messages = this.filterDisplayMessages(response.data || [])
            this.$nextTick(() => {
              this.scrollToBottom()
            })
          }
        } catch (error) {
          console.error('加载消息失败:', error)
          this.messages = []
        }
      },
      
      // 删除对话
      deleteConversation (convId) {
        this.$Modal.confirm({
          title: '确认删除',
          content: '确定要删除这个脚本吗？删除后无法恢复。',
          onOk: async () => {
            try {
              // TODO: 调用API删除
              await this.$http.delete(`/web/conversations/${convId}`)
              
              this.conversations = this.conversations.filter(c => c.id !== convId)
              
              if (this.currentConversation && this.currentConversation.id === convId) {
                // 关闭SSE连接（会自动重置索引）
                this.closeSseConnection()
                this.currentConversation = null
                this.messages = []
              }
              
              this.$Message.success('删除成功')
            } catch (error) {
              console.error('删除失败:', error)
              this.$Message.error('删除失败，请重试')
            }
          }
        })
      },
      
      // 发送消息
      async sendMessage () {
        if (!this.userInput.trim()) return
        if (this.isLoading) {
          this.$Message.warning('请等待当前回复完成')
          return
        }
        
        // 如果没有当前对话，先创建一个新会话
        if (!this.currentConversation) {
          const created = await this.createNewConversation()
          if (!created) return
        }
        
        const messageContent = this.userInput.trim()
        const referencedScriptsMeta = this.buildReferencedScriptsMeta()
        const referencedScriptIds = this.getReferencedScriptIds()
        this.userInput = ''
        // 发送后清空输入区引用，下一条消息需重新选择
        this.clearPendingScriptReferences()
        
        // 判断是否为第一条用户消息（消息列表为空或只有系统消息）
        const isFirstUserMessage = this.messages.length === 0 || 
          this.messages.filter(m => m.role === 'user').length === 0
        
        // 添加用户消息到界面
        this.messages.push({
          role: 'user',
          content: messageContent,
          referenced_scripts_meta: referencedScriptsMeta,
          created_at: new Date().toISOString()
        })
        
        this.$nextTick(() => {
          this.scrollToBottom()
        })
        
        this.closeSseConnection()
        this.isLoading = true
        
        // 添加空的AI消息占位
        this.messages.push({
          role: 'assistant',
          content: '',
          created_at: new Date().toISOString()
        })
        this.currentAiMessageIndex = this.messages.length - 1
        
        try {
          // 使用 SSE 流式对话
          await this.streamChat(messageContent, null, referencedScriptIds)
          
          // 如果是第一条用户消息，自动生成标题
          if (isFirstUserMessage && this.currentConversation) {
            this.generateConversationTitle()
          }
        } catch (error) {
          console.error('发送消息失败:', error)
          if (!this.sseConnection) {
            this.$Message.error('发送失败，请重试')
          }
        } finally {
          this.isLoading = false
          this.currentAiMessageIndex = -1
          this.clearPendingScriptReferences()
        }
      },
      
      // SSE 流式对话
      streamChat(content, messageId = null, referencedScriptIds = null) {
        return new Promise((resolve, reject) => {
          // 构建 SSE 请求
          const url = `/v1/web/conversations/chat-stream`
          const payloadData = {
            conversation_id: this.currentConversation.id,
            content: content,
            model_type: 'deepseek'
          }
          if (messageId) {
            payloadData.message_id = messageId
          }
          const scriptIds = referencedScriptIds !== null && referencedScriptIds !== undefined
            ? referencedScriptIds
            : this.getReferencedScriptIds()
          if (scriptIds && scriptIds.length > 0) {
            payloadData.referenced_script_ids = scriptIds
          }
          const payload = JSON.stringify(payloadData)
          
          // 获取 CSRF Token
          const csrfToken = getCookie('creator_auth_csrf_cookie')
          
          this.sseConnection = new SSE(url, {
            headers: {
              'Content-Type': 'application/json',
              'source': 'web',
              'X-CSRF-TOKEN': csrfToken  // 添加 CSRF Token
            },
            payload: payload,
            method: 'POST',
            withCredentials: true
          })
          
          // 监听消息事件
          this.sseConnection.addEventListener('message', (e) => {
            if (e.data) {
              try {
                // 解析 JSON 消息
                const message = JSON.parse(e.data)

                console.log('SSE消息:', message, message.content)
                
                // 根据消息类型处理
                if (message.type === 'start') {
                  // 开始接收消息
                  console.log('开始接收AI回复')
                } else if (message.type === 'begin') {
                  // 开始接收内容（准备阶段）
                  console.log('AI准备回复中...')
                } else if (message.type === 'input') {
                  // 接收内容片段
                  if (this.currentAiMessageIndex >= 0 && message.content) {
                    const currentMessage = this.messages[this.currentAiMessageIndex]
                    
                    // 安全检查：确保消息对象存在
                    if (!currentMessage) {
                      console.error('当前AI消息不存在，索引:', this.currentAiMessageIndex)
                      return
                    }
                    
                    currentMessage.content += message.content
                    
                    // 强制更新视图
                    this.$set(this.messages, this.currentAiMessageIndex, currentMessage)
                    
                    this.$nextTick(() => {
                      this.scrollToBottom()
                    })
                  }
                } else if (message.type === 'stop') {
                  // 消息结束
                  console.log('AI回复完成')
                  // 如果 stop 消息带有 content，可能是特殊提示（如"内容不合法"）
                  if (message.content) {
                    this.$Message.warning(message.content)
                  }
                } else if (message.type === 'error') {
                  // 错误消息
                  console.error('AI回复错误:', message.content)
                  this.$Message.error(message.content || '对话出错，请重试')
                  this.finishStreamChat({ failed: true }).then(function () {
                    reject(new Error(message.content || '对话出错'))
                  })
                } else if (message.type === 'thinking') {
                  // 思考过程（豆包1.6深度思考模型）
                  console.log('AI思考中:', message.content)
                }
              } catch (error) {
                console.error('解析SSE消息失败:', error, 'raw data:', e.data)
              }
            }
          })
          
          const self = this
          let streamFailed = false

          // 监听错误事件
          this.sseConnection.addEventListener('error', (e) => {
            console.error('SSE错误:', e)
            streamFailed = true
            self.finishStreamChat({ failed: true, waitBackground: true }).then(function () {
              reject(new Error('流式对话失败'))
            })
          })
          
          // 监听结束事件（CLOSED = 2）
          this.sseConnection.addEventListener('readystatechange', (e) => {
            if (e.readyState !== 2) {
              return
            }
            if (self._streamChatFinishing) {
              return
            }
            self.finishStreamChat({
              failed: streamFailed,
              waitBackground: streamFailed
            }).then(resolve)
          })
          
          // 开始流式请求
          this.sseConnection.stream()
        })
      },
      
      // 关闭 SSE 连接（不清理 UI 状态）
      closeSseConnection() {
        if (this.sseConnection) {
          this.sseConnection.close()
          this.sseConnection = null
        }
      },

      // 流式结束：保留已显示片段，再与数据库同步
      async finishStreamChat(options) {
        if (this._streamChatFinishing) {
          return
        }
        this._streamChatFinishing = true

        const opts = options || {}
        const partialContent = this.currentAiMessageIndex >= 0 &&
          this.messages[this.currentAiMessageIndex] &&
          this.messages[this.currentAiMessageIndex].content
            ? this.messages[this.currentAiMessageIndex].content
            : ''

        this.closeSseConnection()
        this.currentAiMessageIndex = -1
        this.isLoading = false

        try {
          if (!this.currentConversation) {
            return
          }

          await this.loadMessages(this.currentConversation.id)
          this._mergePartialAssistant(partialContent, opts.failed)

          if (opts.waitBackground && !this._hasAssistantMessage()) {
            this.$Message.info('连接中断，正在后台继续生成，请稍候…')
            await this.pollUntilAssistantReply(90, 2000)
          }

          this.$nextTick(() => {
            this.scrollToBottom()
          })
        } finally {
          this._streamChatFinishing = false
        }
      },

      _hasAssistantMessage() {
        return this.messages.some(function (m) {
          return m.role === 'assistant' && m.content && String(m.content).trim()
        })
      },

      _mergePartialAssistant(partialContent, failed) {
        const hasAssistant = this._hasAssistantMessage()
        if (partialContent && !hasAssistant) {
          this.messages.push({
            role: 'assistant',
            content: partialContent,
            created_at: new Date().toISOString()
          })
        } else if (failed && partialContent && hasAssistant) {
          const assistants = this.messages.filter(function (m) {
            return m.role === 'assistant'
          })
          const lastAssistant = assistants[assistants.length - 1]
          if (lastAssistant && (!lastAssistant.content || !String(lastAssistant.content).trim())) {
            lastAssistant.content = partialContent
          }
        }
      },

      async pollUntilAssistantReply(maxAttempts, intervalMs) {
        const self = this
        for (let i = 0; i < maxAttempts; i++) {
          await new Promise(function (resolve) {
            setTimeout(resolve, intervalMs)
          })
          if (!self.currentConversation) {
            return false
          }
          await self.loadMessages(self.currentConversation.id)
          if (self._hasAssistantMessage()) {
            self.$Message.success('AI 回复已生成')
            return true
          }
        }
        return false
      },
      
      // 使用建议
      useSuggestion (text) {
        this.userInput = text
        this.sendMessage()
      },
      
      // 快捷键处理
      handleKeyDown(e) {
        // Enter 直接发送，Shift+Enter 换行
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault()
          if (this.userInput.trim() && !this.isLoading) {
            this.sendMessage()
          }
        }
        // Shift+Enter 允许换行（textarea默认行为，不需要处理）
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
      
      // 导出当前对话为 HTML（保持页面样式）
      exportConversation () {
        if (!this.currentConversation || !this.messages.length) {
          this.$Message.warning('当前没有可导出的对话')
          return
        }
        if (this.isExporting) {
          return
        }

        var exportMessages = this.getExportableMessages()
        if (!exportMessages.length) {
          this.$Message.warning('当前没有可导出的消息')
          return
        }

        this.isExporting = true
        try {
          var title = (this.currentConversation.title || '未命名对话').trim()
          var exportedAt = moment().format('YYYY-MM-DD HH:mm')
          var userAvatar = this.currentUser && this.currentUser.avatar
            ? this.escapeHtmlAttr(this.currentUser.avatar)
            : ''
          var messagesHtml = ''
          var i
          for (i = 0; i < exportMessages.length; i++) {
            messagesHtml += this.buildExportMessageHtml(exportMessages[i], userAvatar)
          }

          var html = this.buildExportHtmlDocument(title, exportedAt, messagesHtml)
          var fileName = this.buildExportFileName(title, exportedAt)
          this.downloadHtmlFile(fileName, html)
          this.$Message.success('对话已导出')
        } catch (error) {
          console.error('导出对话失败:', error)
          this.$Message.error('导出失败，请稍后重试')
        } finally {
          this.isExporting = false
        }
      },

      getExportableMessages () {
        var list = this.filterDisplayMessages(this.messages)
        return list.filter(function (m) {
          if (!m) {
            return false
          }
          var content = m.content ? String(m.content).trim() : ''
          return !!content
        })
      },

      buildExportMessageHtml (message, userAvatar) {
        if (message.role === 'user') {
          return this.buildExportUserMessageHtml(message, userAvatar)
        }
        return this.buildExportAiMessageHtml(message)
      },

      buildExportUserMessageHtml (message, userAvatar) {
        var refsHtml = ''
        if (message.referenced_scripts_meta && message.referenced_scripts_meta.length) {
          refsHtml = '<div class="referenced-scripts-meta">' +
            this.buildExportReferencedScriptsHtml(message.referenced_scripts_meta) +
            '</div>'
        }
        var avatarHtml = userAvatar
          ? '<img src="' + userAvatar + '" alt="用户头像" class="avatar-image" />'
          : '<span class="avatar-fallback">我</span>'

        return '<div class="message-item">' +
          '<div class="message user-message">' +
            '<div class="message-avatar user-avatar">' + avatarHtml + '</div>' +
            '<div class="message-bubble">' +
              refsHtml +
              '<div class="message-content">' + this.escapeHtml(message.content || '') + '</div>' +
              '<div class="message-footer"><span class="message-time">' +
                this.escapeHtml(this.formatTime(message.created_at)) +
              '</span></div>' +
            '</div>' +
          '</div>' +
        '</div>'
      },

      buildExportAiMessageHtml (message) {
        return '<div class="message-item">' +
          '<div class="message ai-message">' +
            '<div class="message-avatar ai-avatar"><span class="ai-text">AI</span></div>' +
            '<div class="message-bubble">' +
              '<div class="message-header"><span class="ai-label">AI助手</span></div>' +
              '<div class="message-content markdown-content">' +
                '<div class="markdown-body">' + this.renderMarkdown(message.content || '') + '</div>' +
              '</div>' +
              '<div class="message-footer"><span class="message-time">' +
                this.escapeHtml(this.formatTime(message.created_at)) +
              '</span></div>' +
            '</div>' +
          '</div>' +
        '</div>'
      },

      buildExportReferencedScriptsHtml (refs) {
        var html = '<span class="referenced-label">引用了</span>'
        var i
        for (i = 0; i < refs.length; i++) {
          var refScript = refs[i]
          var title = refScript && refScript.title ? refScript.title : '未命名脚本'
          html += '<span class="referenced-script-link">《' + this.escapeHtml(title) + '》</span>'
        }
        return html
      },

      buildExportHtmlDocument (title, exportedAt, messagesHtml) {
        return '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n' +
          '<meta charset="UTF-8" />\n' +
          '<meta name="viewport" content="width=device-width, initial-scale=1.0" />\n' +
          '<title>' + this.escapeHtml(title) + ' - 对话导出</title>\n' +
          '<style>' + this.getExportDocumentStyles() + '</style>\n' +
          '</head>\n<body>\n' +
          '<div class="export-page">\n' +
            '<header class="export-header">\n' +
              '<h1>' + this.escapeHtml(title) + '</h1>\n' +
              '<p class="export-meta">导出时间：' + this.escapeHtml(exportedAt) + '</p>\n' +
            '</header>\n' +
            '<main class="export-messages">' + messagesHtml + '</main>\n' +
          '</div>\n' +
          '</body>\n</html>'
      },

      getExportDocumentStyles () {
        return [
          '* { box-sizing: border-box; margin: 0; padding: 0; }',
          'body {',
          '  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;',
          '  background: #0a0a1a;',
          '  color: rgba(255, 255, 255, 0.9);',
          '  line-height: 1.6;',
          '}',
          '.export-page { max-width: 75rem; margin: 0 auto; padding: 2rem 1.5rem 3rem; }',
          '.export-header { margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(59, 130, 246, 0.3); }',
          '.export-header h1 { font-size: 1.5rem; font-weight: 600; color: #fff; margin-bottom: 0.5rem; }',
          '.export-meta { font-size: 0.875rem; color: rgba(255, 255, 255, 0.5); }',
          '.export-messages .message-item { margin: 0 auto 2rem; padding: 0 1rem; }',
          '.export-messages .message { display: flex; gap: 0.75rem; margin-bottom: 1.5rem; max-width: 92%; width: fit-content; }',
          '.export-messages .message-avatar { width: 2rem; height: 2rem; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; overflow: hidden; }',
          '.export-messages .user-avatar { background: rgba(59, 130, 246, 0.8); }',
          '.export-messages .ai-avatar { background: linear-gradient(45deg, #8B5CF6, #3B82F6); }',
          '.export-messages .avatar-image { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }',
          '.export-messages .avatar-fallback, .export-messages .ai-text { font-size: 0.875rem; font-weight: 600; color: #fff; }',
          '.export-messages .message-bubble { flex: 0 1 auto; max-width: 100%; }',
          '.export-messages .message-header { margin-bottom: 0.5rem; }',
          '.export-messages .ai-label { font-size: 0.75rem; font-weight: 500; color: rgba(255, 255, 255, 0.8); }',
          '.export-messages .message-content { background: rgba(26, 26, 46, 0.6); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 8px; padding: 0.875rem 1rem; color: rgba(255, 255, 255, 0.9); font-size: 0.9375rem; word-break: break-word; }',
          '.export-messages .user-message { flex-direction: row-reverse; margin-left: auto; }',
          '.export-messages .user-message .message-content { background: rgba(59, 130, 246, 0.15); border-color: rgba(59, 130, 246, 0.3); white-space: pre-wrap; }',
          '.export-messages .ai-message { margin-right: auto; }',
          '.export-messages .markdown-content { white-space: normal; }',
          '.export-messages .referenced-scripts-meta { display: flex; flex-wrap: wrap; gap: 0.25rem; margin-bottom: 0.375rem; font-size: 0.75rem; color: rgba(255, 255, 255, 0.65); }',
          '.export-messages .referenced-script-link { color: #60A5FA; }',
          '.export-messages .message-footer { margin-top: 0.5rem; }',
          '.export-messages .message-time { font-size: 0.75rem; color: rgba(255, 255, 255, 0.4); }',
          '.export-messages .markdown-content p { margin-bottom: 0.75rem; line-height: 1.7; }',
          '.export-messages .markdown-content p:last-child { margin-bottom: 0; }',
          '.export-messages .markdown-content h1, .export-messages .markdown-content h2, .export-messages .markdown-content h3, .export-messages .markdown-content h4, .export-messages .markdown-content h5, .export-messages .markdown-content h6 { font-weight: 600; margin-top: 1.25rem; margin-bottom: 0.75rem; color: rgba(255, 255, 255, 0.95); }',
          '.export-messages .markdown-content h1:first-child, .export-messages .markdown-content h2:first-child, .export-messages .markdown-content h3:first-child { margin-top: 0; }',
          '.export-messages .markdown-content h1 { font-size: 1.5rem; }',
          '.export-messages .markdown-content h2 { font-size: 1.3rem; }',
          '.export-messages .markdown-content h3 { font-size: 1.15rem; }',
          '.export-messages .markdown-content ul, .export-messages .markdown-content ol { margin-bottom: 0.75rem; padding-left: 1.5rem; }',
          '.export-messages .markdown-content li { margin-bottom: 0.25rem; }',
          '.export-messages .markdown-content code { background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 0.25rem; padding: 0.125rem 0.375rem; font-family: "SF Mono", Monaco, Consolas, monospace; font-size: 0.875em; }',
          '.export-messages .markdown-content pre { background: rgba(10, 10, 26, 0.6); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 8px; padding: 0.875rem; margin: 0.75rem 0; overflow-x: auto; }',
          '.export-messages .markdown-content pre code { background: none; border: none; padding: 0; display: block; }',
          '.export-messages .markdown-content blockquote { border-left: 0.25rem solid #3B82F6; padding-left: 1rem; margin: 0.75rem 0; color: rgba(255, 255, 255, 0.8); font-style: italic; }',
          '.export-messages .markdown-content table { width: 100%; border-collapse: collapse; margin: 0.75rem 0; }',
          '.export-messages .markdown-content th, .export-messages .markdown-content td { border: 1px solid rgba(59, 130, 246, 0.3); padding: 0.5rem 0.75rem; text-align: left; }',
          '.export-messages .markdown-content th { background: rgba(59, 130, 246, 0.15); font-weight: 600; }',
          '.export-messages .markdown-content tr:nth-child(even) { background: rgba(255, 255, 255, 0.02); }',
          '.export-messages .markdown-content a { color: #60A5FA; text-decoration: none; border-bottom: 1px solid rgba(90, 200, 250, 0.3); }',
          '.export-messages .markdown-content strong { font-weight: 600; color: rgba(255, 255, 255, 0.95); }',
          '.export-messages .markdown-content hr { border: none; border-top: 1px solid rgba(59, 130, 246, 0.3); margin: 1rem 0; }',
          '.export-messages .markdown-content img { max-width: 100%; height: auto; border-radius: 8px; margin: 0.5rem 0; }',
          '@media print { body { background: #fff; color: #111; } .export-messages .message-content { background: #f5f5f5; border-color: #ddd; color: #111; } }'
        ].join('\n')
      },

      buildExportFileName (title, exportedAt) {
        var safeTitle = String(title || '对话')
          .replace(/[\\/:*?"<>|]/g, '_')
          .replace(/\s+/g, '_')
          .slice(0, 40)
        return safeTitle + '_' + exportedAt.replace(/[:\s]/g, '-') + '.html'
      },

      downloadHtmlFile (fileName, html) {
        var blob = new Blob([html], { type: 'text/html;charset=utf-8' })
        var url = URL.createObjectURL(blob)
        var link = document.createElement('a')
        link.href = url
        link.download = fileName
        link.style.display = 'none'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
      },

      escapeHtml (text) {
        return String(text || '')
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#39;')
      },

      escapeHtmlAttr (text) {
        return this.escapeHtml(text).replace(/`/g, '&#96;')
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
      
      // 格式化消息
      formatMessage (content) {
        if (!content) return ''
        // 简单的换行处理
        return content.replace(/\n/g, '<br/>')
      },
      
      // 滚动到底部
      scrollToBottom () {
        const container = this.$refs.messagesContainer
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      },
      
      // 格式化日期
      formatDate (date) {
        if (!date) return ''
        return moment(date).format('MM-DD HH:mm')
      },
      
      // 格式化时间
      formatTime (time) {
        if (!time) return ''
        return moment(time).format('HH:mm')
      },

      isAiMessageWaiting (message, index) {
        return this.isLoading &&
          index === this.currentAiMessageIndex &&
          (!message.content || !String(message.content).trim())
      },

      isAiMessageStreaming (message, index) {
        return this.isLoading &&
          index === this.currentAiMessageIndex &&
          message.content &&
          String(message.content).trim()
      },
      
      // 加载对话列表
      async loadConversations () {
        try {
          const response = await this.$http.get('/web/conversations', {
            params: {
              page: 1,
              per_page: 50
            }
          })
          
          if (response && response.success) {
            // 使用分页返回的数据
            this.conversations = response.rows || []
          }
        } catch (error) {
          console.error('加载对话列表失败:', error)
          this.conversations = []
        }
      },

      async selectConversationFromRoute () {
        const rawId = this.$route && this.$route.query
          ? this.$route.query.conversation_id
          : null
        const conversationId = parseInt(rawId, 10)
        if (!conversationId) return

        let conv = this.conversations.find(function (item) {
          return Number(item.id) === conversationId
        })

        if (!conv) {
          try {
            const response = await this.$http.get('/web/conversations/' + conversationId)
            if (response && response.success && response.data) {
              conv = response.data
              this.conversations.unshift(conv)
            }
          } catch (error) {
            console.error('加载 Codex 对话失败:', error)
          }
        }

        if (conv) {
          await this.selectConversation(conv)
        }
      },
      
      // 自动生成对话标题
      async generateConversationTitle() {
        if (!this.currentConversation) return
        
        try {
          const response = await this.$http.post(
            `/web/conversations/${this.currentConversation.id}/generate-title`
          )
          
          if (response && response.success && response.data) {
            // 更新当前对话的标题
            this.currentConversation.title = response.data.title
            
            // 更新对话列表中的标题
            const convIndex = this.conversations.findIndex(
              c => c.id === this.currentConversation.id
            )
            if (convIndex !== -1) {
              this.$set(this.conversations[convIndex], 'title', response.data.title)
            }
            
            console.log('标题生成成功:', response.data.title)
          }
        } catch (error) {
          console.error('生成标题失败:', error)
          // 标题生成失败不影响主流程，只记录日志
        }
      },
      
      // ==================== 悬浮按钮拖拽功能 ====================
      
      // 初始化悬浮按钮位置
      initFloatBtnPosition() {
        // 默认位置：右下角，距离边缘 20px
        const containerWidth = window.innerWidth
        const containerHeight = window.innerHeight
        this.floatBtnPosition.x = containerWidth - 80
        this.floatBtnPosition.y = containerHeight - 150
      },
      
      // 开始拖拽
      startDrag(e) {
        // 如果点击的是按钮本身，不触发拖拽，让点击事件正常执行
        if (e.target.closest('.generate-btn')) {
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
        
        const newX = e.clientX - this.dragStartX
        const newY = e.clientY - this.dragStartY
        
        // 限制在窗口范围内
        const maxX = window.innerWidth - 60
        const maxY = window.innerHeight - 60
        
        this.floatBtnPosition.x = Math.max(0, Math.min(newX, maxX))
        this.floatBtnPosition.y = Math.max(0, Math.min(newY, maxY))
      },
      
      // 停止拖拽
      stopDrag() {
        this.isDragging = false
        document.removeEventListener('mousemove', this.onDrag)
        document.removeEventListener('mouseup', this.stopDrag)
      },
      
      // ==================== 引用脚本功能 ====================

      clearPendingScriptReferences () {
        this.referencedScripts = []
      },

      filterDisplayMessages (messages) {
        if (!messages || !messages.length) {
          return []
        }
        return messages.filter(function (m) {
          if (!m || m.role !== 'user') {
            return true
          }
          var content = m.content ? String(m.content).trim() : ''
          if (content) {
            return true
          }
          // 未确认且无正文的语音草稿不在气泡区展示
          if (!m.user_confirmed && m.audio_media_id) {
            return false
          }
          return true
        })
      },

      async discardDraftVoiceMessage () {
        var messageId = this.currentVoiceMessageId
        if (!messageId) {
          return
        }
        try {
          await this.$http.delete('/web/messages/' + messageId)
          this.messages = this.messages.filter(function (m) {
            return m.id !== messageId
          })
        } catch (error) {
          console.warn('删除语音草稿失败:', error)
        } finally {
          this.currentVoiceMessageId = null
        }
      },

      getReferencedScriptIds () {
        if (!this.referencedScripts || !this.referencedScripts.length) {
          return []
        }
        return this.referencedScripts.map(function (item) {
          return item.id
        })
      },

      buildReferencedScriptsMeta () {
        if (!this.referencedScripts || !this.referencedScripts.length) {
          return []
        }
        return this.referencedScripts.map(function (item) {
          return {
            id: item.id,
            title: item.title || '未命名脚本',
            word_count: item.word_count || 0
          }
        })
      },

      openScriptPicker () {
        this.showScriptPickerModal = true
      },

      onScriptPickerVisibleChange (visible) {
        if (visible) {
          this.loadScriptPickerList()
        }
      },

      async loadScriptPickerList () {
        this.scriptPickerLoading = true
        try {
          const params = {
            page: 1,
            per_page: 50
          }
          if (this.scriptPickerKeyword && this.scriptPickerKeyword.trim()) {
            params.keyword = this.scriptPickerKeyword.trim()
          }
          const response = await this.$http.get('/web/scripts', { params: params })
          if (response && response.success) {
            this.scriptPickerList = response.rows || []
          } else {
            this.scriptPickerList = []
          }
        } catch (error) {
          console.error('加载脚本列表失败:', error)
          this.$Message.error('加载脚本列表失败')
          this.scriptPickerList = []
        } finally {
          this.scriptPickerLoading = false
        }
      },

      isScriptSelected (scriptId) {
        if (!this.referencedScripts || !this.referencedScripts.length) {
          return false
        }
        return this.referencedScripts.some(function (item) {
          return item.id === scriptId
        })
      },

      isScriptPickerItemDisabled (scriptId) {
        if (this.isScriptSelected(scriptId)) {
          return false
        }
        return this.referencedScripts.length >= this.maxReferencedScripts
      },

      toggleScriptSelection (script) {
        if (!script || !script.id) {
          return
        }
        if (this.isScriptSelected(script.id)) {
          this.removeReferencedScript(script.id)
          return
        }
        if (this.referencedScripts.length >= this.maxReferencedScripts) {
          this.$Message.warning('最多引用 ' + this.maxReferencedScripts + ' 个脚本')
          return
        }
        this.referencedScripts.push({
          id: script.id,
          title: script.title || '未命名脚本',
          word_count: script.word_count || 0
        })
      },

      removeReferencedScript (scriptId) {
        this.referencedScripts = this.referencedScripts.filter(function (item) {
          return item.id !== scriptId
        })
      },

      goScriptDetail (scriptId) {
        if (!scriptId) {
          return
        }
        this.$router.push({ name: 'script-detail', params: { id: scriptId } })
      },

      formatScriptDate (dateStr) {
        if (!dateStr) {
          return ''
        }
        return moment(dateStr).format('MM-DD HH:mm')
      },

      // ==================== 提取脚本功能 ====================
      
      // 点击悬浮按钮：直接提取脚本
      async showGenerateModal() {
        // 1. 基础验证
        if (!this.currentConversation) {
          this.$Message.warning('请先创建对话')
          return
        }
        
        if (this.messages.length === 0) {
          this.$Message.warning('请先与AI讨论您的创意需求')
          return
        }
        
        // 2. 显示全屏动画
        this.isExtractingScript = true
        
        // 3. 延迟至少1秒以显示动画（提升体验）
        const startTime = Date.now()
        
        try {
          // 调用提取接口
          await this.extractScript()
          
          // 确保动画至少显示1秒
          const elapsed = Date.now() - startTime
          if (elapsed < 1000) {
            await new Promise(resolve => setTimeout(resolve, 1000 - elapsed))
          }
        } catch (error) {
          // 错误已在 extractScript 中处理
        }
      },
      
      // 从对话中提取脚本
      async extractScript() {
        try {
          const response = await this.$http.post(
            `/web/conversations/${this.currentConversation.id}/extract-script`
          )
          
          if (response && response.success) {
            // 提取成功
            this.extractedScript = {
              title: response.data.title || '',
              subtitle: response.data.subtitle || '',
              content: response.data.content || '',
              word_count: response.data.word_count || 0
            }
            
            // 关闭动画，显示编辑弹窗
            this.isExtractingScript = false
            this.showScriptEditModal = true
            
            console.log('脚本提取成功:', this.extractedScript)
          }
        } catch (error) {
          console.error('提取脚本失败:', error)
          this.isExtractingScript = false
          
          // 根据错误类型显示提示
          let errorMsg = '脚本提取失败，请重试'
          
          if (error.response && error.response.data) {
            errorMsg = error.response.data.detail || error.response.data.message || errorMsg
          } else if (error.message) {
            errorMsg = error.message
          }
          
          this.$Message.error(errorMsg)
        }
      },
      
      // 更新字数统计
      updateWordCount() {
        this.extractedScript.word_count = this.extractedScript.content ? this.extractedScript.content.length : 0
      },
      
      // 保存脚本
      async saveScript() {
        // 验证
        if (!this.extractedScript.content || !this.extractedScript.content.trim()) {
          this.$Message.warning('脚本内容不能为空')
          return
        }
        
        this.isSavingScript = true
        
        try {
          const response = await this.$http.post('/web/scripts', {
            conversation_id: this.currentConversation.id,
            title: this.extractedScript.title || '未命名脚本',
            subtitle: this.extractedScript.subtitle,
            content: this.extractedScript.content,
            format_type: 'vlog' // 默认格式
          })
          
          if (response && response.success) {
            this.$Message.success('脚本保存成功')
            this.closeScriptEdit()
            // 不跳转，保持在当前页
          }
        } catch (error) {
          console.error('保存失败:', error)
          this.$Message.error('保存失败，请重试')
        } finally {
          this.isSavingScript = false
        }
      },
      
      // 关闭编辑弹窗
      closeScriptEdit() {
        this.showScriptEditModal = false
        this.extractedScript = {
          title: '',
          subtitle: '',
          content: '',
          word_count: 0
        }
      },
      
      // ==================== 语音录音功能 ====================
      
      // 切换输入模式
      async switchInputMode(mode) {
        if (this.isLoading) {
          this.$Message.warning('请等待当前操作完成')
          return
        }
        
        if (this.isRecording) {
          this.$Message.warning('请先停止录音')
          return
        }

        if (mode !== 'voice' && this.inputMode === 'voice') {
          this.voiceRecordingCancelled = true
          this.stopVoiceStatusPolling()
          await this.discardDraftVoiceMessage()
          this.resetVoiceProcessingState()
        }
        
        this.inputMode = mode
        if (mode === 'voice') {
          this.primeAudioDevices()
        }
      },
      
      async primeAudioDevices() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          return
        }
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
          stream.getTracks().forEach(function (track) { track.stop() })
          await this.loadAudioInputDevices()
        } catch (e) {
          console.warn('获取麦克风设备列表失败:', e)
        }
      },
      
      async loadAudioInputDevices() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
          return
        }
        const devices = await navigator.mediaDevices.enumerateDevices()
        const inputs = devices.filter(function (d) { return d.kind === 'audioinput' })
        this.audioInputDevices = inputs
        if (!this.selectedAudioDeviceId && inputs.length > 0) {
          var preferred = inputs.find(function (d) {
            var label = (d.label || '').toLowerCase()
            return label.indexOf('built-in') >= 0 ||
              label.indexOf('internal') >= 0 ||
              label.indexOf('内建') >= 0 ||
              label.indexOf('macbook') >= 0
          })
          if (preferred) {
            this.selectedAudioDeviceId = preferred.deviceId
          }
        }
      },
      
      _getAudioConstraints() {
        var constraints = {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1
        }
        if (this.selectedAudioDeviceId) {
          constraints.deviceId = { exact: this.selectedAudioDeviceId }
        }
        return constraints
      },
      
      setupMicLevelMonitor(stream) {
        this.teardownMicLevelMonitor()
        this.recordingStream = stream
        try {
          var AudioCtx = window.AudioContext || window.webkitAudioContext
          if (!AudioCtx) {
            return
          }
          this._audioContext = new AudioCtx()
          var source = this._audioContext.createMediaStreamSource(stream)
          var analyser = this._audioContext.createAnalyser()
          analyser.fftSize = 256
          source.connect(analyser)
          this._audioAnalyser = analyser
          var dataArray = new Uint8Array(analyser.frequencyBinCount)
          var self = this
          var tick = function () {
            if (!self._audioAnalyser) {
              return
            }
            analyser.getByteFrequencyData(dataArray)
            var sum = 0
            for (var i = 0; i < dataArray.length; i++) {
              sum += dataArray[i]
            }
            var avg = sum / dataArray.length
            self.micLevel = Math.min(100, Math.round(avg * 100 / 80))
            self._micLevelRaf = requestAnimationFrame(tick)
          }
          tick()
        } catch (e) {
          console.warn('麦克风电平监测初始化失败:', e)
        }
      },
      
      teardownMicLevelMonitor() {
        if (this._micLevelRaf) {
          cancelAnimationFrame(this._micLevelRaf)
          this._micLevelRaf = null
        }
        if (this._audioContext) {
          this._audioContext.close()
          this._audioContext = null
        }
        this._audioAnalyser = null
        this.recordingStream = null
        this.micLevel = 0
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
          this.voiceRecordingCancelled = false
          // 检查浏览器支持
          if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.$Message.error('您的浏览器不支持录音功能')
            return
          }
          
          // 请求麦克风（可指定设备，开启降噪/回声消除）
          const stream = await navigator.mediaDevices.getUserMedia({
            audio: this._getAudioConstraints()
          })
          
          await this.loadAudioInputDevices()
          this.setupMicLevelMonitor(stream)
          
          this.recordMimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
            ? 'audio/webm;codecs=opus'
            : 'audio/webm'
          
          // 创建 MediaRecorder
          this.mediaRecorder = new MediaRecorder(stream, { mimeType: this.recordMimeType })
          this.audioChunks = []
          this.chunkUploadQueue = []
          
          // 监听数据可用：仅上传本段切片（非累积整段），服务端追加到主 WebM
          this.mediaRecorder.addEventListener('dataavailable', (event) => {
            if (this.voiceRecordingCancelled) {
              return
            }
            if (event.data && event.data.size > 0) {
              this.audioChunks.push(event.data)
              const isFinal = !this.isRecording
              console.log(
                '收到音频切片，本段:', event.data.size, '字节，序号:', this.streamChunkIndex,
                '是否最终块:', isFinal
              )
              this.enqueueChunkUpload(isFinal, event.data)
            }
          })
          
          // 监听录音停止事件（保留用于停止所有音轨）
          this.mediaRecorder.addEventListener('stop', () => {
            stream.getTracks().forEach(track => track.stop())
            this.teardownMicLevelMonitor()
            console.log('录音停止，总时长:', this.recordingDuration, '秒')
          })
          
          // 开始录音：长录音（≥15s）才启用中途切片；短录音仅在「完成」时一次性上传
          this.mediaRecorder.start()
          this._startStreamChunkTimer(this.streamChunkMinDurationSec * 1000)
          this.isRecording = true
          this.isPaused = false
          this.recordingDuration = 0
          this.streamChunkIndex = 0
          this.streamMidChunkStarted = false
          this.validFinalChunkUploaded = false
          this._voiceFinalizeAttempted = false
          
          // 启动计时器
          this.recordingTimer = setInterval(() => {
            this.recordingDuration++
            
            // 检查是否超过15分钟
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
      
      // 定时触发 MediaRecorder 分片（仅长录音：默认首片在 streamChunkMinDurationSec 触发）
      _startStreamChunkTimer(firstDelayMs) {
        this._clearStreamChunkTimer()
        const self = this
        const initialDelay = (firstDelayMs !== undefined && firstDelayMs !== null)
          ? firstDelayMs
          : (this.streamChunkMinDurationSec * 1000)
        const scheduleNext = function (delayMs) {
          self._streamChunkTimer = setTimeout(function () {
            if (self.mediaRecorder && self.mediaRecorder.state === 'recording') {
              self.streamMidChunkStarted = true
              self.mediaRecorder.requestData()
              scheduleNext(self.streamChunkIntervalMs)
            }
          }, delayMs)
        }
        scheduleNext(initialDelay)
      },

      _clearStreamChunkTimer() {
        if (this._streamChunkTimer) {
          clearTimeout(this._streamChunkTimer)
          this._streamChunkTimer = null
        }
      },

      // 暂停录音
      pauseRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
          this.mediaRecorder.pause()
          this.isPaused = true
          this._clearStreamChunkTimer()
          clearInterval(this.recordingTimer)
          this.$Message.info('录音已暂停')
        }
      },
      
      // 继续录音
      resumeRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
          this.mediaRecorder.resume()
          this.isPaused = false
          if (this.streamMidChunkStarted) {
            this._startStreamChunkTimer(this.streamChunkIntervalMs)
          } else {
            const remainingSec = this.streamChunkMinDurationSec - this.recordingDuration
            const delayMs = remainingSec > 0 ? remainingSec * 1000 : this.streamChunkIntervalMs
            this._startStreamChunkTimer(delayMs)
          }
          
          // 重新启动计时器
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
        // 防止重复调用
        if (this.isFinishingRecording) {
          return
        }
        
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
          this.isFinishingRecording = true
          // 先将 isRecording 置为 false，这样 dataavailable 触发时能识别为最终块
          this.isRecording = false
          this.isPaused = false
          this._clearStreamChunkTimer()
          clearInterval(this.recordingTimer)
          
          // 先 requestData() 再 stop()，确保最后一段音频写入 Blob（否则 WebM 可能不完整）
          if (this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.requestData()
          }
          this.mediaRecorder.stop()
          this.$Message.success('录音完成，正在上传...')
          
          setTimeout(() => {
            this.isFinishingRecording = false
          }, 500)
        } else {
          this.isFinishingRecording = false
        }
      },
      
      // 分块上传队列（避免并发锁导致最终块/中间块被跳过）
      enqueueChunkUpload(isFinal, sliceBlob) {
        if (this.voiceRecordingCancelled) {
          return
        }
        this.chunkUploadQueue.push({ isFinal: isFinal, sliceBlob: sliceBlob })
        this.processChunkUploadQueue()
      },
      
      async processChunkUploadQueue() {
        if (this.isProcessingChunkQueue || this.voiceRecordingCancelled) {
          return
        }
        this.isProcessingChunkQueue = true
        try {
          while (this.chunkUploadQueue.length > 0) {
            if (this.voiceRecordingCancelled) {
              this.chunkUploadQueue = []
              break
            }
            const item = this.chunkUploadQueue.shift()
            await this.uploadStreamChunk(item.isFinal, item.sliceBlob)
          }
          if (this.currentVoiceMessageId && !this.voicePollingTimer) {
            this.$set(this.voiceStatus.transcription, 'isActive', true)
            this.startVoiceStatusPolling()
          }
        } finally {
          this.isProcessingChunkQueue = false
        }
      },
      
      async finalizeVoiceRecording () {
        if (!this.currentVoiceMessageId || this.voiceRecordingCancelled) {
          return
        }
        try {
          await this.$http.post('/web/messages/' + this.currentVoiceMessageId + '/voice-finalize')
          if (!this.voicePollingTimer) {
            this.resetVoiceStatus()
            this.$set(this.voiceStatus.transcription, 'isActive', true)
            this.startVoiceStatusPolling()
          }
        } catch (error) {
          console.error('[语音收尾] 失败', {
            messageId: this.currentVoiceMessageId,
            cancelled: this.voiceRecordingCancelled,
            error: error
          })
          this.$Message.error('语音处理失败，请重试')
        }
      },

      async retryVoiceFinalize () {
        this._voiceFinalizeAttempted = false
        this.$set(this.voiceStatus.transcription, 'error', '')
        this.$set(this.voiceStatus.transcription, 'isActive', true)
        await this.finalizeVoiceRecording()
        this.$Message.info('正在合并已识别内容...')
      },

      // 等待已转写分块数达到 minCount（HTTP 上传完成 ≠ Whisper 转写完成）
      async waitUntilTranscribedCount(minCount, options) {
        if (!this.currentVoiceMessageId || !minCount || minCount <= 0) {
          return true
        }
        const opts = options || {}
        const deadline = Date.now() + (opts.timeoutMs || 120000)
        const label = opts.label || ('count>=' + minCount)
        this._voiceStatusWaitActive = true
        console.log('[语音上传] 等待转写计数', {
          messageId: this.currentVoiceMessageId,
          minCount: minCount,
          label: label
        })
        try {
          while (Date.now() < deadline) {
            if (this.voiceRecordingCancelled || !this.currentVoiceMessageId) {
              return false
            }
            try {
              const response = await this.$http.get(
                '/web/messages/' + this.currentVoiceMessageId + '/processing-status',
                { hideProgress: true }
              )
              if (response && response.success && response.data && response.data.transcription) {
                const trans = response.data.transcription
                const statusName = trans.status && trans.status.name ? trans.status.name : ''
                const processed = trans.processed_chunks || 0
                this.applyVoiceProcessingStatus(response.data)
                if (statusName === 'COMPLETED' || processed >= minCount) {
                  console.log('[语音上传] 转写计数达标', {
                    minCount: minCount,
                    processed: processed,
                    status: statusName,
                    label: label
                  })
                  return true
                }
                if (statusName === 'FAILED' && trans.partial_text) {
                  console.warn('[语音上传] FAILED 但有 partial，继续等待转写计数', {
                    minCount: minCount,
                    processed: processed,
                    label: label
                  })
                }
              }
            } catch (error) {
              console.warn('[语音上传] 轮询转写计数失败', error)
            }
            await new Promise(function (resolve) {
              setTimeout(resolve, 1000)
            })
          }
          console.warn('[语音上传] 等待转写计数超时', { minCount: minCount, label: label })
          return false
        } finally {
          this._voiceStatusWaitActive = false
        }
      },

      // 流式分块上传：仅上传本段切片，后端追加到主 WebM 后转写新增时段
      async uploadStreamChunk(isFinal, sliceBlob) {
        if (this.voiceRecordingCancelled) {
          return
        }
        const blob = sliceBlob
        if (!blob || blob.size === 0) {
          console.warn('没有音频切片，跳过上传')
          return
        }
        
        if (isFinal) {
          this.isUploadingAudio = true
        }
        
        const currentChunkIndex = this.streamChunkIndex
        // 方案 D：中途切片永远 is_final=false；仅收尾块（短录音首块 / 长录音最后一片）为 true
        const sendAsFinal = isFinal && (
          !this.streamMidChunkStarted || currentChunkIndex > 0
        )

        try {
          // 上传块 N 前：必须已有 N 个块转写完成（块 0..N-1）
          if (currentChunkIndex > 0) {
            const previousReady = await this.waitUntilTranscribedCount(currentChunkIndex, {
              label: 'before-upload-chunk-' + currentChunkIndex
            })
            if (!previousReady) {
              throw new Error('前序语音块尚未转写完成，请稍后重试')
            }
          }

          // 确保有会话
          if (!this.currentConversation) {
            const created = await this.createNewConversation()
            if (!created) {
              throw new Error('创建会话失败')
            }
          }
          
          if (blob.size < 256) {
            console.warn('[语音切片] 过小，跳过上传', {
              size: blob.size,
              isFinal: isFinal,
              sendAsFinal: sendAsFinal,
              chunkIndex: currentChunkIndex,
              messageId: this.currentVoiceMessageId,
              uploadedChunks: this.streamChunkIndex
            })
            if (isFinal) {
              this.isUploadingAudio = false
              // 已有有效最终块时，stop() 产生的空尾片直接忽略
              if (this.validFinalChunkUploaded) {
                console.log('[语音切片] 已有有效最终块，忽略空尾片', {
                  size: blob.size,
                  messageId: this.currentVoiceMessageId,
                  uploadedChunks: this.streamChunkIndex
                })
                return
              }
              // 前面分块已上传但从未标记 is_final 时，走收尾
              if (this.currentVoiceMessageId && this.streamChunkIndex > 0) {
                console.log('[语音切片] 尾片为空，走收尾流程', {
                  messageId: this.currentVoiceMessageId,
                  uploadedChunks: this.streamChunkIndex
                })
                await this.finalizeVoiceRecording()
                return
              }
              console.error('[语音切片] 无有效录音', {
                size: blob.size,
                isFinal: isFinal,
                messageId: this.currentVoiceMessageId,
                uploadedChunks: this.streamChunkIndex,
                cancelled: this.voiceRecordingCancelled
              })
              this.$Message.error('未采集到有效录音，请检查浏览器麦克风权限与系统输入设备')
            }
            return
          }
          
          const formData = new FormData()
          formData.append('file', blob, 'chunk_' + currentChunkIndex + '.webm')
          
          console.log('上传切片', currentChunkIndex, '大小:', blob.size, '字节，is_final:', sendAsFinal)
          
          const uploadResp = await this.$http.post('/media', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 90000
          })
          
          if (!uploadResp || !uploadResp.success) {
            throw new Error('音频块上传失败')
          }
          
          const mediaId = uploadResp.data.id

          if (this.voiceRecordingCancelled) {
            if (isFinal) {
              this.isUploadingAudio = false
            }
            return
          }
          
          // 调用 voice-stream 端点
          const streamBody = {
            audio_media_id: mediaId,
            chunk_index: currentChunkIndex,
            is_final: sendAsFinal
          }
          if (this.currentVoiceMessageId) {
            streamBody.message_id = this.currentVoiceMessageId
          }
          
          const streamResp = await this.$http.post(
            '/web/conversations/' + this.currentConversation.id + '/voice-stream',
            streamBody
          )
          
          if (!streamResp || !streamResp.success) {
            throw new Error('语音流接口调用失败')
          }
          
          // 首块返回 message_id，开始轮询
          if (!this.currentVoiceMessageId) {
            this.currentVoiceMessageId = streamResp.data.message_id
            this.resetVoiceStatus()
            console.log('流式录音：获得 message_id=' + this.currentVoiceMessageId)
          }
          
          // 成功后递增块序号
          this.streamChunkIndex++

          console.log('块', currentChunkIndex, '上传成功，message_id=' + this.currentVoiceMessageId)

          // 上传块 N 后：必须等块 N 转写完成，队列才处理下一块（避免 Huey 并发竞态）
          const currentReady = await this.waitUntilTranscribedCount(currentChunkIndex + 1, {
            label: 'after-upload-chunk-' + currentChunkIndex
          })
          if (!currentReady) {
            console.warn('[语音上传] 当前块转写未确认完成，暂停后续队列', {
              chunkIndex: currentChunkIndex,
              messageId: this.currentVoiceMessageId
            })
            throw new Error('语音块转写等待超时，请稍后重试')
          }

          if (sendAsFinal) {
            this.isUploadingAudio = false
            if (blob.size >= 256) {
              this.validFinalChunkUploaded = true
            }
          }
          
        } catch (error) {
          console.error('[语音上传] uploadStreamChunk 失败', {
            chunkIndex: currentChunkIndex,
            isFinal: isFinal,
            sendAsFinal: sendAsFinal,
            messageId: this.currentVoiceMessageId,
            uploadedChunks: this.streamChunkIndex,
            error: error
          })
          
          if (isFinal) {
            this.isUploadingAudio = false
            this.$Message.error('上传失败，请重试：' + (error.message || '未知错误'))
          }
        }
      },
      
      // 取消录音
      async cancelRecording() {
        this.voiceRecordingCancelled = true
        this._clearStreamChunkTimer()
        this.teardownMicLevelMonitor()
        clearInterval(this.recordingTimer)
        this.stopVoiceStatusPolling()

        this.isRecording = false
        this.isPaused = false
        this.isFinishingRecording = false
        this.recordedAudio = null
        this.recordedDuration = 0
        this.recordingDuration = 0
        this.audioChunks = []
        this.streamChunkIndex = 0
        this.chunkUploadQueue = []
        this.isProcessingChunkQueue = false
        this.isUploadingAudio = false

        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
          this.mediaRecorder.stop()
        }

        await this.discardDraftVoiceMessage()
        this.resetVoiceProcessingState()
        this.$Message.info('已取消录音')
      },
      
      // 重新录音
      async reRecord() {
        this.voiceRecordingCancelled = true
        this.stopVoiceStatusPolling()
        await this.discardDraftVoiceMessage()
        this.resetVoiceProcessingState()
      },
      
      // 发送语音消息
      async sendVoiceMessage() {
        // 防止重复调用
        if (this.isUploadingAudio) {
          console.log('已经在处理音频上传，跳过重复调用')
          return
        }
        
        if (!this.recordedAudio) {
          console.warn('[语音发送] 没有录音数据', {
            messageId: this.currentVoiceMessageId,
            isUploadingAudio: this.isUploadingAudio
          })
          this.$Message.warning('没有录音数据')
          return
        }
        
        // 如果没有当前对话，先创建
        if (!this.currentConversation) {
          this.isUploadingAudio = true
          const created = await this.createNewConversation()
          if (!created) {
            this.isUploadingAudio = false
            return
          }
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
            timeout: 60000 // 60秒超时
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
            `/web/conversations/${this.currentConversation.id}/messages/voice`,
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
          
          // 步骤4：开始轮询处理状态（在录音区域显示）
          this.$Message.destroy()
          this.resetVoiceStatus()
          this.startVoiceStatusPolling()
          
          this.$Message.success('开始语音识别...')
        } catch (error) {
          console.error('发送语音消息失败:', error)
          this.$Message.destroy()
          this.isUploadingAudio = false
          
          // 停止轮询（如果已经启动）
          this.stopVoiceStatusPolling()
          
          // 清理消息ID
          this.currentVoiceMessageId = null
          
          // 根据错误类型提供更详细的提示
          let errorMsg = '上传失败'
          if (error.message) {
            errorMsg = error.message
          } else if (error.code === 'ECONNABORTED') {
            errorMsg = '上传超时，请检查网络连接'
          } else if (error.response) {
            errorMsg = '服务器错误，请稍后重试'
          }
          
          console.error('[语音发送] 失败', {
            messageId: this.currentVoiceMessageId,
            hasRecordedAudio: !!this.recordedAudio,
            error: error,
            errorMsg: errorMsg
          })
          this.$Message.error(errorMsg)
          
          // 保留录音数据以便用户重试
          // this.recordedAudio 保持不变，用户可以点击"重新发送"
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
            error: '',
            partialText: '',
            processedChunks: 0
          },
          refinement: {
            isActive: false,
            isCompleted: false,
            result: null,
            error: ''
          }
        }
      },
      
      // 开始监听语音处理状态（直接轮询；SSE 需要自定义请求头，原生 EventSource 无法设置）
      startVoiceStatusPolling() {
        this.stopVoiceStatusPolling()
        this.startVoiceStatusPollFallback()
      },

      startVoiceStatusSSE() {
        const self = this
        const url = '/v1/web/messages/' + this.currentVoiceMessageId +
          '/processing-status/stream?nonce=' + Date.now()
        const es = new EventSource(url, { withCredentials: true })
        this.voiceEventSource = es

        es.onmessage = function (ev) {
          if (!ev.data) {
            return
          }
          try {
            const payload = JSON.parse(ev.data)
            if (payload.done) {
              self.stopVoiceStatusPolling()
              return
            }
            if (payload.success && payload.data) {
              self.applyVoiceProcessingStatus(payload.data)
            }
          } catch (e) {
            console.error('解析 SSE 状态失败:', e)
          }
        }

        es.onerror = function () {
          console.warn('SSE 连接异常，降级为轮询')
          self.stopVoiceStatusSSE()
          self.startVoiceStatusPollFallback()
        }
      },

      stopVoiceStatusSSE() {
        if (this.voiceEventSource) {
          this.voiceEventSource.close()
          this.voiceEventSource = null
        }
      },

      startVoiceStatusPollFallback() {
        const self = this
        this.pollVoiceStatus()
        this.voicePollingTimer = setInterval(function () {
          self.pollVoiceStatus()
        }, 1000)
      },
      
      // 轮询语音处理状态（SSE 降级）
      async pollVoiceStatus() {
        if (!this.currentVoiceMessageId) {
          this.stopVoiceStatusPolling()
          return
        }
        if (this._voiceStatusWaitActive) {
          return
        }
        
        try {
          const response = await this.$http.get(
            '/web/messages/' + this.currentVoiceMessageId + '/processing-status',
            { hideProgress: true }
          )
          
          if (!response || !response.success) {
            console.error('获取状态失败')
            this.stopVoiceStatusPolling()
            return
          }
          
          this.applyVoiceProcessingStatus(response.data)
        } catch (error) {
          console.error('轮询状态失败:', error)
        }
      },

      applyVoiceProcessingStatus(status) {
        // 若消息已被确认/重置，忽略迟到的轮询响应，防止竞态导致状态错乱
        if (!this.currentVoiceMessageId) {
          return
        }
        if (!status || !status.transcription || !status.transcription.status) {
          return
        }
        const transStatus = status.transcription.status.name
        console.log('[语音轮询] 状态', transStatus, {
          messageId: this.currentVoiceMessageId,
          rawTextLen: status.transcription.raw_text ? status.transcription.raw_text.length : 0,
          processedChunks: status.transcription.processed_chunks,
          partialLen: status.transcription.partial_text ? status.transcription.partial_text.length : 0
        })

        if (status.transcription.partial_text) {
          this.$set(this.voiceStatus.transcription, 'partialText', status.transcription.partial_text)
        }
        if (status.transcription.processed_chunks !== undefined) {
          this.$set(this.voiceStatus.transcription, 'processedChunks', status.transcription.processed_chunks)
        }

        if (transStatus === 'PROCESSING') {
          this.$set(this.voiceStatus.transcription, 'isActive', true)
          this.$set(this.voiceStatus.transcription, 'isCompleted', false)
          this.$set(this.voiceStatus.transcription, 'error', '')
        } else if (transStatus === 'COMPLETED') {
          this.$set(this.voiceStatus.transcription, 'isActive', false)
          this.$set(this.voiceStatus.transcription, 'isCompleted', true)
          this.$set(this.voiceStatus.transcription, 'partialText', '')
          this.$set(this.voiceStatus.transcription, 'error', '')

          const rawText = status.transcription.raw_text || ''
          this.$set(this.voiceStatus.transcription, 'text', rawText)

          if (!this.voiceProcessingComplete) {
            this.voiceConfirmedContent = rawText
            this.voiceProcessingComplete = true
            this.stopVoiceStatusPolling()
            this.scheduleAutoConfirmVoiceContent()
          }
        } else if (transStatus === 'FAILED') {
          const partial = status.transcription.partial_text || ''
          const errorText = status.transcription.error || ''
          if (errorText.indexOf('Whisper 服务未正确初始化') !== -1) {
            this.$set(this.voiceStatus.transcription, 'isActive', true)
            this.$set(this.voiceStatus.transcription, 'isCompleted', false)
            this.$set(this.voiceStatus.transcription, 'error', '')
            if (partial) {
              this.$set(this.voiceStatus.transcription, 'partialText', partial)
            }
            console.warn('[语音轮询] Whisper 暂未就绪，继续等待重试')
            return
          }
          const stillUploading = this.isProcessingChunkQueue ||
            this.chunkUploadQueue.length > 0 ||
            this.isUploadingAudio

          if (partial && stillUploading) {
            // 上传队列仍在跑时，FAILED 多为并发误报，不展示错误
            this.$set(this.voiceStatus.transcription, 'isActive', true)
            this.$set(this.voiceStatus.transcription, 'isCompleted', false)
            this.$set(this.voiceStatus.transcription, 'error', '')
            this.$set(this.voiceStatus.transcription, 'partialText', partial)
            return
          }

          this.$set(this.voiceStatus.transcription, 'isActive', false)
          this.$set(this.voiceStatus.transcription, 'isCompleted', false)

          if (partial) {
            this.$set(this.voiceStatus.transcription, 'partialText', partial)
            this.$set(this.voiceStatus.transcription, 'error', '')
            if (!this.voiceConfirmedContent) {
              this.voiceConfirmedContent = partial
            }
            if (!this._voiceFinalizeAttempted) {
              this._voiceFinalizeAttempted = true
              this.finalizeVoiceRecording()
              this.$set(this.voiceStatus.transcription, 'isActive', true)
            }
          } else {
            this.$set(this.voiceStatus.transcription, 'error', status.transcription.error || '转写失败')
            this.$set(this.voiceStatus.transcription, 'partialText', '')
            // 无 partial 的 FAILED 可能是并发误报（后续块抢跑），继续轮询
            console.warn('[语音轮询] FAILED 但无 partial，继续轮询等待前序块完成')
            this.$set(this.voiceStatus.transcription, 'isActive', true)
          }
        }
      },
      
      // 停止 SSE / 轮询
      stopVoiceStatusPolling() {
        this.stopVoiceStatusSSE()
        if (this.voicePollingTimer) {
          clearInterval(this.voicePollingTimer)
          this.voicePollingTimer = null
        }
      },
      
      // 校对完成后自动发送（延迟 1.5s 让用户能看到转写文本）
      scheduleAutoConfirmVoiceContent() {
        if (this.autoConfirmTriggered) {
          return
        }
        if (!this.currentVoiceMessageId) {
          return
        }
        this.autoConfirmTriggered = true
        this.$Message.info('语音识别完成，1.5 秒后自动发送，可手动编辑...')
        setTimeout(() => {
          // 二次检查：若用户已重录或取消则放弃
          if (!this.currentVoiceMessageId || !this.voiceProcessingComplete) {
            return
          }
          this.confirmVoiceContent()
        }, 1500)
      },
      
      // 确认语音内容
      async confirmVoiceContent() {
        // 如果没有校对后的文本，使用转写文本
        let contentToSend = this.voiceConfirmedContent && this.voiceConfirmedContent.trim()
          ? this.voiceConfirmedContent.trim()
          : (this.voiceStatus.transcription.text || '')
        contentToSend = contentToSend.trim()
        
        if (!contentToSend) {
          console.warn('[语音确认] 内容为空', {
            messageId: this.currentVoiceMessageId,
            voiceConfirmedContent: this.voiceConfirmedContent,
            transcriptionText: this.voiceStatus.transcription.text
          })
          this.$Message.warning('内容不能为空')
          this.autoConfirmTriggered = false
          return
        }
        
        if (!this.currentVoiceMessageId) {
          console.error('[语音确认] 消息ID丢失', {
            voiceProcessingComplete: this.voiceProcessingComplete,
            voiceConfirmedContent: this.voiceConfirmedContent
          })
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
              send_to_ai: true  // 默认发送给AI
            }
          )
          
          if (!response || !response.success) {
            throw new Error('确认内容失败')
          }
          
          // 保存消息ID用于后续轮询
          const confirmedMessageId = this.currentVoiceMessageId
          
          // 重置语音处理状态
          this.resetVoiceProcessingState()
          
          // 重新加载消息列表以获取最新的用户消息
          if (this.currentConversation) {
            await this.loadMessages(this.currentConversation.id)
          }
          
          // 判断是否为第一条用户消息（重新加载后，如果只有1条用户消息，说明是第一条）
          const userMessages = this.messages.filter(m => m.role === 'user')
          const isFirstUserMessage = userMessages.length === 1
          
          // 启动AI回复的流式显示（使用已存在的消息ID，避免创建重复消息）
          this.closeSseConnection()
          this.isLoading = true
          this.$Message.info('AI正在处理您的消息...')
          
          // 添加空的AI消息占位
          this.messages.push({
            role: 'assistant',
            content: '',
            created_at: new Date().toISOString()
          })
          this.currentAiMessageIndex = this.messages.length - 1
          
          try {
            // 使用 SSE 流式对话来接收AI回复，传入已存在的消息ID
            const voiceReferencedScriptIds = this.getReferencedScriptIds()
            this.clearPendingScriptReferences()
            await this.streamChat(contentToSend, confirmedMessageId, voiceReferencedScriptIds)
            
            // 如果是第一条用户消息，自动生成标题
            if (isFirstUserMessage && this.currentConversation) {
              this.generateConversationTitle()
            }
          } catch (error) {
            console.error('AI回复失败:', error)
            this.$Message.error('AI回复失败，请重试')
            
            // 尝试从数据库重新加载消息
            if (this.currentConversation) {
              await this.loadMessages(this.currentConversation.id)
            }
          } finally {
            this.isLoading = false
            this.currentAiMessageIndex = -1
            this.clearPendingScriptReferences()
          }
          
        } catch (error) {
          console.error('[语音确认] 失败', {
            messageId: this.currentVoiceMessageId,
            contentToSend: contentToSend,
            error: error
          })
          this.autoConfirmTriggered = false
          this.$Message.error('确认失败: ' + (error.message || '未知错误'))
        } finally {
          this.isConfirmingVoice = false
          this.isLoading = false
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
        this.validFinalChunkUploaded = false
        this._voiceFinalizeAttempted = false
        this.streamMidChunkStarted = false
        this.streamChunkIndex = 0
        this.audioChunks = []
        this.chunkUploadQueue = []
        this.isProcessingChunkQueue = false
        this._clearStreamChunkTimer()
        this.teardownMicLevelMonitor()
        this.resetVoiceStatus()
      }
    },

    mounted () {
      this.loadConversations().then(() => {
        this.selectConversationFromRoute()
      })
      this.initFloatBtnPosition()
      
      // 监听窗口大小变化
      window.addEventListener('resize', this.initFloatBtnPosition)
    },
    
    beforeDestroy () {
      // 清理SSE连接
      this.closeSseConnection()
      
      // 清理拖拽事件监听
      document.removeEventListener('mousemove', this.onDrag)
      document.removeEventListener('mouseup', this.stopDrag)
      
      // 清理窗口resize监听
      window.removeEventListener('resize', this.initFloatBtnPosition)
      
      // 清理录音相关
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
        this.mediaRecorder.stop()
      }
      clearInterval(this.recordingTimer)
      this._clearStreamChunkTimer()
      this.teardownMicLevelMonitor()
      
      // 清理语音状态轮询
      this.stopVoiceStatusPolling()
    }
  }
</script>

<style lang="less" scoped>
// 导入设计系统变量
@import '../styles/variables.less';

.scripts-container {
  height: ~"calc(100vh - 64px)";
  // 脚本创作主题：蓝紫渐变，专业而富有创意
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

// 网格背景
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
    box-shadow: 0 0 2.5rem rgba(59, 130, 246, 0.3),
                inset 0 0 2rem rgba(255, 255, 255, 0.08);

    &.shape-1 {
      width: 8rem;
      height: 8rem;
      background: linear-gradient(135deg, @primary-color 0%, @accent-color 100%);
      top: 8%;
      left: 12%;
      animation-duration: 28s;
    }

    &.shape-2 {
      width: 6rem;
      height: 6rem;
      background: linear-gradient(135deg, @secondary-color 0%, @primary-color 100%);
      top: 55%;
      left: 85%;
      animation-delay: -6s;
      animation-duration: 32s;
    }

    &.shape-3 {
      width: 10rem;
      height: 10rem;
      background: linear-gradient(135deg, @primary-light 0%, @primary-color 100%);
      top: 75%;
      left: 18%;
      animation-delay: -12s;
      animation-duration: 38s;
    }

    &.shape-4 {
      width: 4.5rem;
      height: 4.5rem;
      background: linear-gradient(135deg, @accent-color 0%, @secondary-color 100%);
      top: 22%;
      left: 68%;
      animation-delay: -18s;
      animation-duration: 24s;
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
    
    &.particle-1 { 
      top: 12%; 
      left: 28%; 
      animation-delay: 0s;
      background: @primary-light;
      box-shadow: 0 0 1rem @primary-light, 0 0 2rem @primary-light;
    }
    &.particle-2 { 
      top: 38%; 
      left: 72%; 
      animation-delay: 0.6s;
      background: @accent-color;
      box-shadow: 0 0 1rem @accent-color, 0 0 2rem @accent-color;
    }
    &.particle-3 { 
      top: 62%; 
      left: 42%; 
      animation-delay: 1.2s;
      background: @primary-color;
      box-shadow: 0 0 1rem @primary-color, 0 0 2rem @primary-color;
    }
    &.particle-4 { 
      top: 82%; 
      left: 18%; 
      animation-delay: 1.8s;
      background: @secondary-color;
      box-shadow: 0 0 1rem @secondary-color, 0 0 2rem @secondary-color;
    }
    &.particle-5 { 
      top: 28%; 
      left: 82%; 
      animation-delay: 2.4s;
      background: @primary-light;
      box-shadow: 0 0 1rem @primary-light, 0 0 2rem @primary-light;
    }
    &.particle-6 { 
      top: 52%; 
      left: 88%; 
      animation-delay: 2.1s;
      background: @accent-color;
      box-shadow: 0 0 1rem @accent-color, 0 0 2rem @accent-color;
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

// 主内容区域
.content-wrapper {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

// 左侧边栏
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
  
  .conversation-list {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
    
    .conversation-item {
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
        
        .conversation-actions {
          opacity: 1;
        }
      }
      
      &.active {
        background: rgba(59, 130, 246, 0.15);
        border-color: @primary-color;
      }
      
      .conversation-icon {
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
      
      .conversation-info {
        flex: 1;
        min-width: 0;
        
        .conversation-title {
          font-size: 0.875rem;
          font-weight: @font-weight-medium;
          color: rgba(255, 255, 255, 0.9);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          margin-bottom: 0.125rem;
        }
        
        .conversation-meta {
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.5);
        }
      }
      
      .conversation-actions {
        opacity: 0;
        transition: opacity @transition-base;
        
        .delete-icon {
          font-size: 1.25rem;
          color: rgba(255, 255, 255, 0.6);
          cursor: pointer;
          
          &:hover {
            color: @error-color;
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

// 对话区域
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(10, 10, 26, 0.2);
  position: relative;
  min-width: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 2rem 1.5rem 1.5rem;
    
    .welcome-screen {
      text-align: center;
      padding: 3rem 2rem;
      max-width: 60rem;
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
      
      .suggestion-cards {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        
        .suggestion-card {
          padding: 1.25rem;
          background: rgba(26, 26, 46, 0.6);
          border: 1px solid rgba(59, 130, 246, 0.2);
          border-radius: @border-radius-md;
          backdrop-filter: blur(1.25rem);
          cursor: pointer;
          transition: all @transition-base;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.75rem;
          
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
          
          &:hover {
            background: rgba(59, 130, 246, 0.15);
            border-color: @primary-color;
            transform: translateY(-0.125rem);
          }
        }
      }
    }

    .messages-list {
      .message-item {
        max-width: 75rem;
        margin: 0 auto 2rem;
        padding: 0 1rem;
      }
      
      .message {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
        max-width: 92%;
        width: fit-content;
        
        .message-avatar {
          width: 2rem;
          height: 2rem;
          border-radius: 50%;
          background: rgba(59, 130, 246, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          overflow: hidden;
          
          .ivu-icon {
            font-size: 1rem;
            color: #FFFFFF;
          }
          
          .avatar-image {
            width: 100%;
            height: 100%;
            object-fit: cover;
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
          flex: 0 1 auto;
          max-width: 100%;
          
          .message-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
            
            .ai-label {
              font-size: 0.75rem;
              font-weight: @font-weight-medium;
              color: rgba(255, 255, 255, 0.8);
              flex-shrink: 0;
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

            &.is-waiting {
              display: flex;
              align-items: center;
              min-height: 1.75rem;
              padding: 0.75rem 1rem;
            }

            .ai-typing-cursor {
              display: inline-block;
              width: 0.5625rem;
              height: 0.5625rem;
              border-radius: 50%;
              background: @primary-light;
              box-shadow: 0 0 0.5rem rgba(90, 200, 250, 0.55);
              animation: ai-cursor-blink 1s ease-in-out infinite;
              flex-shrink: 0;
            }

            .ai-typing-cursor--inline {
              margin-left: 0.125rem;
              vertical-align: middle;
            }

            .markdown-body {
              display: inline;
            }
            
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
              
              /deep/ h1 { font-size: 1.5rem; }
              /deep/ h2 { font-size: 1.3rem; }
              /deep/ h3 { font-size: 1.15rem; }
              /deep/ h4 { font-size: 1.05rem; }
              /deep/ h5 { font-size: 1rem; }
              /deep/ h6 { font-size: 0.95rem; }
              
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
              }
              
              /deep/ code {
                background: rgba(139, 92, 246, 0.15);
                border: 1px solid rgba(139, 92, 246, 0.3);
                border-radius: 0.25rem;
                padding: 0.125rem 0.375rem;
                font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
                font-size: 0.875em;
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
          
          .message-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 0.5rem;
            
            .message-time {
              font-size: 0.75rem;
              color: rgba(255, 255, 255, 0.4);
            }
            
            .message-actions {
              display: flex;
              gap: 0.25rem;
            }
          }
        }
        
        &.user-message {
          flex-direction: row-reverse;
          margin-left: auto;
          
          .message-bubble {
            .referenced-scripts-meta {
              display: flex;
              flex-wrap: wrap;
              align-items: center;
              gap: 0.25rem;
              margin-bottom: 0.375rem;
              font-size: 0.75rem;
              color: rgba(255, 255, 255, 0.65);

              .referenced-label {
                margin-right: 0.125rem;
              }

              .referenced-script-link {
                color: @primary-light;
                cursor: pointer;

                &:hover {
                  text-decoration: underline;
                }
              }
            }

            .message-content {
              background: rgba(59, 130, 246, 0.15);
              border-color: rgba(59, 130, 246, 0.3);
            }
          }
        }
        
        &.ai-message {
          margin-right: auto;
        }
      }
    }
  }

  @keyframes ai-cursor-blink {
    0%, 100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.2;
      transform: scale(0.82);
    }
  }

  .chat-input-section {
    background: transparent;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;

    .chat-export-bar {
      align-self: flex-start;
      width: 100%;
      max-width: 75rem;
      display: flex;
      justify-content: flex-start;
      margin-top: -0.25rem;

      .export-chat-btn {
        color: rgba(255, 255, 255, 0.55);
        padding-left: 0;

        &:hover {
          color: @primary-light;
        }

        &[disabled] {
          color: rgba(255, 255, 255, 0.25);
        }
      }
    }
    
    // 输入模式切换
    .input-mode-switch {
      display: flex;
      background: rgba(26, 26, 46, 0.6);
      border-radius: @border-radius-lg;
      padding: 0.25rem;
      gap: 0.25rem;
      backdrop-filter: blur(1.25rem);
      border: 1px solid rgba(59, 130, 246, 0.2);
      
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
    
    .referenced-scripts-summary {
      display: flex;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 0.375rem 0.5rem;
      max-width: 75rem;
      width: 100%;
      padding: 0.625rem 0.875rem;
      border-radius: @border-radius-lg;
      background: rgba(59, 130, 246, 0.12);
      border: 1px solid rgba(59, 130, 246, 0.28);

      .summary-icon {
        color: @primary-light;
        margin-top: 0.125rem;
        flex-shrink: 0;
      }

      .summary-label {
        font-size: 0.8125rem;
        color: rgba(255, 255, 255, 0.65);
        flex-shrink: 0;
        line-height: 1.5;
      }

      .summary-titles {
        display: flex;
        flex-wrap: wrap;
        gap: 0.375rem 0.625rem;
        flex: 1;
        min-width: 0;
      }

      .summary-title-item {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        max-width: 100%;
      }

      .summary-title-text {
        font-size: 0.875rem;
        font-weight: @font-weight-medium;
        color: @primary-light;
        cursor: pointer;
        line-height: 1.5;
        word-break: break-all;

        &:hover {
          text-decoration: underline;
        }
      }

      .summary-title-remove {
        cursor: pointer;
        color: rgba(255, 255, 255, 0.5);
        flex-shrink: 0;

        &:hover {
          color: #fff;
        }
      }
    }

    .text-input-column {
      display: flex;
      flex-direction: column;
      gap: 0.625rem;
      max-width: 75rem;
      width: 100%;
    }

    .script-reference-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.5rem;
      width: 100%;

      .reference-script-btn {
        border-color: rgba(59, 130, 246, 0.35);
        background: rgba(26, 26, 46, 0.6);
        color: rgba(255, 255, 255, 0.85);
      }

      .reference-hint {
        font-size: 0.8125rem;
        color: rgba(255, 255, 255, 0.45);
      }
    }

    .input-wrapper {
      display: flex;
      gap: 0.875rem;
      align-items: flex-end;
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
    
    // ==================== 语音录音界面 ====================
    .voice-input-wrapper {
      max-width: 75rem;
      width: 100%;
      
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
        
        .mic-device-select {
          max-width: 20rem;
          margin: 0 auto 1rem;
          text-align: left;
          
          .mic-device-label {
            display: block;
            margin-bottom: 0.375rem;
            font-size: 0.8125rem;
            color: rgba(255, 255, 255, 0.6);
          }
        }
        
        .voice-hint {
          margin-top: 1rem;
          color: rgba(255, 255, 255, 0.5);
          font-size: 0.875rem;
          line-height: 1.5;
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
          
          .mic-level-wrap {
            max-width: 16rem;
            margin: 0 auto 1rem;
            
            .mic-level-bar {
              height: 0.5rem;
              background: rgba(255, 255, 255, 0.1);
              border-radius: 0.25rem;
              overflow: hidden;
              
              .mic-level-fill {
                height: 100%;
                background: linear-gradient(90deg, @primary-color, #34d399);
                border-radius: 0.25rem;
                transition: width 0.08s ease-out;
              }
            }
            
            .mic-level-label {
              display: block;
              margin-top: 0.375rem;
              font-size: 0.8125rem;
              color: rgba(255, 255, 255, 0.55);
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
            
            .recording-stream-hint {
              display: flex;
              align-items: center;
              justify-content: center;
              gap: 0.5rem;
              margin-top: 0.5rem;
              font-size: 0.8125rem;
              color: rgba(16, 185, 129, 0.9);
            }
            
            .recording-partial-text {
              margin-top: 0.5rem;
              padding: 0.5rem 0.75rem;
              max-height: 4rem;
              overflow: hidden;
              text-align: left;
              font-size: 0.8125rem;
              line-height: 1.5;
              color: rgba(255, 255, 255, 0.65);
              background: rgba(16, 185, 129, 0.08);
              border-radius: @border-radius-sm;
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
          
          .partial-transcription {
            margin-top: 0.75rem;
            padding: 0.875rem;
            background: rgba(16, 185, 129, 0.06);
            border-radius: @border-radius-md;
            border: 1px solid rgba(16, 185, 129, 0.2);
            
            .result-label {
              display: flex;
              align-items: center;
              gap: 0.5rem;
              font-size: 0.8125rem;
              color: rgba(16, 185, 129, 0.8);
              margin-bottom: 0.5rem;
            }
            
            .result-text.partial {
              font-size: 0.875rem;
              color: rgba(255, 255, 255, 0.6);
              line-height: 1.6;
              max-height: 6rem;
              overflow: hidden;
              text-overflow: ellipsis;
              display: -webkit-box;
              -webkit-line-clamp: 4;
              line-clamp: 4;
              -webkit-box-orient: vertical;
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
          
          .corrections-list {
            margin-top: 1rem;
            padding: 0.875rem;
            background: rgba(139, 92, 246, 0.08);
            border-radius: @border-radius-md;
            border: 1px solid rgba(139, 92, 246, 0.2);
            
            .corrections-label {
              font-size: 0.8125rem;
              font-weight: @font-weight-medium;
              color: rgba(255, 255, 255, 0.7);
              margin-bottom: 0.625rem;
            }
            
            .correction-item {
              display: flex;
              align-items: center;
              gap: 0.5rem;
              padding: 0.5rem 0;
              font-size: 0.875rem;
              
              .original {
                color: rgba(255, 59, 48, 0.9);
                text-decoration: line-through;
              }
              
              .ivu-icon {
                color: rgba(255, 255, 255, 0.5);
              }
              
              .corrected {
                color: @success-color;
                font-weight: @font-weight-medium;
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
}

// 响应式设计
@media (max-width: @screen-md) {
  .sidebar {
    width: 14rem;
  }
  
  .chat-area {
    .chat-messages {
      padding: 1.5rem;
      
      .messages-list .message-item .message {
        max-width: 95%;
      }
    }
    
    .chat-input-section {
      padding: 1rem;
      
      .input-wrapper {
        max-width: 65rem;
      }
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
    .chat-messages {
      padding: 1rem;
      
      .welcome-screen {
        padding: 2rem 1rem;
        
        .suggestion-cards {
          grid-template-columns: 1fr;
        }
      }
      
      .messages-list .message-item .message {
        max-width: 98%;
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
}

// 悬浮生成脚本按钮
.floating-generate-btn {
  position: fixed;
  z-index: 999;
  cursor: move;
  transition: box-shadow @transition-base;
  
  .generate-btn {
    width: 3.75rem;
    height: 3.75rem;
    background: linear-gradient(135deg, @primary-color, @accent-color);
    border: none;
    box-shadow: 0 0.5rem 1.5rem rgba(59, 130, 246, 0.4);
    transition: all @transition-base;
    
    &:hover:not(:disabled) {
      background: linear-gradient(135deg, @primary-light, @accent-color);
      box-shadow: 0 0.75rem 2rem rgba(59, 130, 246, 0.6);
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

// ==================== 全屏提取动画 ====================
.fullscreen-extracting {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .extracting-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(10, 10, 26, 0.95);
    backdrop-filter: blur(1.25rem);
  }
  
  .extracting-content {
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
        border-top-color: @primary-color;
        border-right-color: @primary-color;
        animation-duration: 3s;
      }
      
      &.ring-2 {
        width: 7.5rem;
        height: 7.5rem;
        border-top-color: @accent-color;
        border-left-color: @accent-color;
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
      color: @primary-light;
      animation: pulse 2s ease-in-out infinite;
    }
  }
  
  // 文案
  .extracting-text {
    text-align: center;
    
    h3 {
      font-size: 1.75rem;
      font-weight: @font-weight-semibold;
      color: #FFFFFF;
      margin-bottom: 0.75rem;
      background: linear-gradient(135deg, @primary-light, @accent-color);
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
      background: @primary-color;
      border-radius: 50%;
      opacity: 0;
      animation: particle-float 3s ease-in-out infinite;
      box-shadow: 0 0 0.5rem @primary-color;
      
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

// ==================== 脚本编辑弹窗 ====================
/deep/ .script-edit-modal {
  .ivu-modal {
    // 弹窗整体背景 - 深色科技感
    .ivu-modal-content {
      background: rgba(26, 26, 46, 0.98) !important;
      backdrop-filter: blur(1.25rem);
      border: 1px solid rgba(59, 130, 246, 0.3);
      box-shadow: 0 1.25rem 3.75rem rgba(0, 0, 0, 0.5);
    }
    
    // 弹窗标题
    .ivu-modal-header {
      background: transparent !important;
      border-bottom: 1px solid rgba(59, 130, 246, 0.2);
      padding: 1.25rem 2rem;
      
      .ivu-modal-header-inner {
        color: #FFFFFF !important;
        font-size: 1.125rem;
        font-weight: @font-weight-semibold;
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
      border-top: 1px solid rgba(59, 130, 246, 0.2);
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
          background: linear-gradient(135deg, @primary-color, @accent-color);
          border: none;
          
          &:hover:not(:disabled) {
            background: linear-gradient(135deg, @primary-light, @accent-color);
            box-shadow: 0 0.25rem 0.75rem rgba(59, 130, 246, 0.4);
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

.script-edit-form {
  .form-item {
    margin-bottom: 1.5rem;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    label {
      display: block;
      margin-bottom: 0.625rem;
      font-size: 0.9375rem;
      font-weight: @font-weight-medium;
      color: rgba(255, 255, 255, 0.9);
      
      &.label-with-count {
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .word-count {
          font-size: 0.875rem;
          color: @primary-light;
          font-weight: @font-weight-normal;
        }
      }
    }
    
    /deep/ .ivu-input {
      background: rgba(10, 10, 26, 0.6);
      border: 1px solid rgba(59, 130, 246, 0.3);
      color: rgba(255, 255, 255, 0.95);
      font-size: 0.9375rem;
      transition: all @transition-base;
      
      &:focus {
        background: rgba(10, 10, 26, 0.8);
        border-color: @primary-color;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
        color: #FFFFFF;
      }
      
      &::placeholder {
        color: rgba(255, 255, 255, 0.3);
      }
      
      &[type="textarea"] {
        line-height: 1.8;
        font-size: 1rem;
        padding: 0.875rem;
        min-height: 20rem;
        
        // 滚动条样式
        &::-webkit-scrollbar {
          width: 0.375rem;
        }
        
        &::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.2);
          border-radius: 0.1875rem;
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

// 引用脚本弹窗（Modal 挂到 body，需 /deep/ + 深色底，避免白字白底）
/deep/ .script-picker-modal {
  .ivu-modal-content {
    background: rgba(26, 26, 46, 0.98) !important;
    backdrop-filter: blur(1.25rem);
    border: 1px solid rgba(59, 130, 246, 0.3);
    box-shadow: 0 1.25rem 3.75rem rgba(0, 0, 0, 0.5);
  }

  .ivu-modal-header {
    background: transparent !important;
    border-bottom: 1px solid rgba(59, 130, 246, 0.2);
    padding: 1.25rem 1.5rem;

    .ivu-modal-header-inner {
      color: #FFFFFF !important;
      font-size: 1.0625rem;
      font-weight: @font-weight-semibold;
    }

    .ivu-icon-ios-close {
      color: rgba(255, 255, 255, 0.65);

      &:hover {
        color: #FFFFFF;
      }
    }
  }

  .ivu-modal-body {
    padding: 1rem 1.5rem 0.5rem;
    background: transparent !important;
    color: rgba(255, 255, 255, 0.9);
  }

    .ivu-modal-footer {
    background: transparent !important;
    border-top: 1px solid rgba(59, 130, 246, 0.2);
    padding: 0.875rem 1.5rem;

    .ivu-btn-primary {
      background: linear-gradient(135deg, @primary-color, @accent-color);
      border: none;

      &:hover {
        background: linear-gradient(135deg, @primary-light, @accent-color);
      }
    }
  }

  .script-picker-content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    min-height: 16rem;
  }

  .script-picker-content .ivu-input {
    background: rgba(15, 15, 30, 0.9);
    border: 1px solid rgba(59, 130, 246, 0.35);
    color: rgba(255, 255, 255, 0.95);

    &::placeholder {
      color: rgba(255, 255, 255, 0.4);
    }

    &:focus {
      border-color: @primary-color;
      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    }
  }

  .script-picker-content .ivu-input-icon {
    color: rgba(255, 255, 255, 0.55);
  }

  .script-picker-loading,
  .script-picker-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 2rem 0;
    color: rgba(255, 255, 255, 0.65);
    font-size: 0.875rem;
  }

  .script-picker-list {
    max-height: 20rem;
    overflow-y: auto;
    border: 1px solid rgba(59, 130, 246, 0.25);
    border-radius: @border-radius-md;
    background: rgba(15, 15, 30, 0.6);
  }

  .script-picker-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    cursor: pointer;
    border-bottom: 1px solid rgba(59, 130, 246, 0.12);
    transition: background @transition-fast;

    &:last-child {
      border-bottom: none;
    }

    &:hover:not(.disabled) {
      background: rgba(59, 130, 246, 0.12);
    }

    &.selected {
      background: rgba(59, 130, 246, 0.2);
    }

    &.disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }

    .ivu-checkbox-inner {
      border-color: rgba(255, 255, 255, 0.45);
      background: transparent;
    }

    .ivu-checkbox-checked .ivu-checkbox-inner {
      border-color: @primary-color;
      background-color: @primary-color;
    }
  }

  .script-picker-item-body {
    flex: 1;
    min-width: 0;
  }

  .script-picker-title {
    font-weight: @font-weight-medium;
    font-size: 0.9375rem;
    color: #FFFFFF;
    margin-bottom: 0.25rem;
    line-height: 1.4;
    word-break: break-word;
  }

  .script-picker-meta {
    font-size: 0.8125rem;
    color: rgba(255, 255, 255, 0.55);
    display: flex;
    gap: 0.75rem;
  }

  .script-picker-footer-hint {
    font-size: 0.8125rem;
    color: rgba(255, 255, 255, 0.5);
    padding-bottom: 0.25rem;
  }
}

</style>

