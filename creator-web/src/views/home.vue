<template>
  <div class="home-container">
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
        <div class="particle particle-4"></div>
            </div>
          </div>
          
    <!-- 英雄区 -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-badge">
          <Icon type="ios-flash" />
          <span>AI驱动的智能创作平台</span>
        </div>
        
        <h1 class="hero-title">
          让视频脚本创作<br/>
          <span class="gradient-text">更高效、更专业</span>
        </h1>
        
        <p class="hero-description">
          基于先进AI大模型，通过智能对话和个性化学习，<br/>
          助您快速创作专业、优质的视频脚本
        </p>
        
        <div class="hero-actions">
          <Button type="primary" size="large" @click="startCreating" class="primary-btn">
            <Icon type="ios-create" />
            开始创作
          </Button>
          <Button size="large" @click="viewDemo" class="secondary-btn">
            <Icon type="ios-play" />
            观看演示
          </Button>
        </div>
        
        <div class="hero-stats">
          <div class="stat-item">
            <div class="stat-number">50%+</div>
            <div class="stat-label">效率提升</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-number">10,000+</div>
            <div class="stat-label">创作脚本</div>
            </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-number">98%</div>
            <div class="stat-label">用户满意度</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 功能特性区 -->
    <section class="features-section">
      <div class="section-header">
        <h2 class="section-title">核心功能</h2>
        <p class="section-subtitle">三大智能功能，让脚本创作更轻松</p>
      </div>
      
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon feature-icon-1">
            <Icon type="ios-chatbubbles" size="40" />
          </div>
          <h3>AI智能对话创作</h3>
          <p>通过多轮对话深入理解您的创作需求，提供专业的脚本建议和结构优化方案</p>
          <ul class="feature-list">
            <li><Icon type="ios-checkmark-circle" /> 支持文字和语音输入</li>
            <li><Icon type="ios-checkmark-circle" /> 智能理解创作意图</li>
            <li><Icon type="ios-checkmark-circle" /> 实时创意建议</li>
          </ul>
            </div>
            
        <div class="feature-card">
          <div class="feature-icon feature-icon-2">
            <Icon type="ios-analytics" size="40" />
          </div>
          <h3>个性化风格学习</h3>
          <p>AI自动分析您的历史脚本，学习您的写作风格和格式偏好，提供定制化建议</p>
          <ul class="feature-list">
            <li><Icon type="ios-checkmark-circle" /> 智能分析写作风格</li>
            <li><Icon type="ios-checkmark-circle" /> 提取常用表达模式</li>
            <li><Icon type="ios-checkmark-circle" /> 建立个人知识库</li>
          </ul>
          </div>
          
        <div class="feature-card">
          <div class="feature-icon feature-icon-3">
            <Icon type="ios-document" size="40" />
          </div>
          <h3>规范化脚本输出</h3>
          <p>按照专业脚本规范，输出结构完整、格式标准的视频脚本，支持多种格式导出</p>
          <ul class="feature-list">
            <li><Icon type="ios-checkmark-circle" /> 标准化脚本格式</li>
            <li><Icon type="ios-checkmark-circle" /> 结构完整性检查</li>
            <li><Icon type="ios-checkmark-circle" /> 多格式导出支持</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- 使用流程区 -->
    <section class="process-section">
      <div class="section-header">
        <h2 class="section-title">创作流程</h2>
        <p class="section-subtitle">三步完成专业脚本创作</p>
          </div>
          
      <div class="process-steps">
        <div class="step-item">
          <div class="step-number">01</div>
          <div class="step-content">
            <div class="step-icon">
              <Icon type="ios-bulb" size="36" />
            </div>
            <h3>描述创意</h3>
            <p>简单描述您的视频创意和内容方向，AI将快速理解您的需求</p>
          </div>
          <div class="step-arrow">
            <Icon type="ios-arrow-forward" />
          </div>
            </div>
            
        <div class="step-item">
          <div class="step-number">02</div>
          <div class="step-content">
            <div class="step-icon">
              <Icon type="ios-chatboxes" size="36" />
            </div>
            <h3>智能对话</h3>
            <p>AI通过多轮对话深入挖掘细节，引导您完善脚本结构和内容</p>
          </div>
          <div class="step-arrow">
            <Icon type="ios-arrow-forward" />
          </div>
            </div>
            
        <div class="step-item">
          <div class="step-number">03</div>
          <div class="step-content">
            <div class="step-icon">
              <Icon type="ios-checkmark-circle" size="36" />
            </div>
            <h3>生成脚本</h3>
            <p>获得专业、规范的视频脚本，可直接用于视频制作或进一步优化</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 价值亮点区 -->
    <section class="benefits-section">
      <div class="section-header">
        <h2 class="section-title">为什么选择创思</h2>
        <p class="section-subtitle">四大核心优势，让创作更出色</p>
      </div>
      
      <div class="benefits-grid">
        <div class="benefit-card">
          <div class="benefit-icon">
            <Icon type="ios-speedometer" size="32" />
          </div>
          <h3>效率提升50%+</h3>
          <p>通过AI辅助，将脚本创作时间大幅缩短，让您有更多时间专注于创意本身</p>
        </div>
        
        <div class="benefit-card">
          <div class="benefit-icon">
            <Icon type="ios-ribbon" size="32" />
          </div>
          <h3>专业质量保证</h3>
          <p>基于专业脚本规范，确保输出内容的专业性和可执行性，提升作品品质</p>
        </div>
        
        <div class="benefit-card">
          <div class="benefit-icon">
            <Icon type="ios-person" size="32" />
          </div>
          <h3>个性化体验</h3>
          <p>AI学习您的创作风格和习惯，提供更贴合您需求的定制化建议和方案</p>
        </div>
        
        <div class="benefit-card">
          <div class="benefit-icon">
            <Icon type="ios-school" size="32" />
            </div>
          <h3>降低创作门槛</h3>
          <p>即使是新手创作者，也能在AI引导下快速掌握专业脚本创作方法</p>
        </div>
      </div>
    </section>

    <!-- CTA区域 -->
    <section class="cta-section">
      <div class="cta-content">
        <h2>准备好创作精彩脚本了吗？</h2>
        <p>立即开始，让AI助力您的视频内容创作</p>
        <div class="cta-actions">
          <Button type="primary" size="large" @click="startCreating" class="cta-primary-btn">
            <Icon type="ios-rocket" />
            立即开始创作
          </Button>
      </div>
    </div>
    </section>
  </div>
</template>

<script>
  export default {
    name: 'Home',

    data () {
      return {
        // 页面状态控制
      }
    },

    methods: {
      // 开始创作
      startCreating () {
        // TODO: 跳转到创作页面
        this.$router.push({ name: 'conversations' })
      },
      
      // 观看演示
      viewDemo () {
        // TODO: 打开演示弹窗或跳转到演示页面
        this.$Message.info('演示功能即将上线')
      }
    },

    mounted () {
      // 页面初始化
    }
  }
</script>

<style lang="less" scoped>
  // 导入设计系统变量
  @import '../styles/variables.less';

  .home-container {
    min-height: 100vh;
    background: @bg-primary;
    position: relative;
    overflow-x: hidden;
  }

  // 背景特效（简化版）
  .bg-effects {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
  }

  // 浮动几何图形（简化版）
  .floating-shapes {
    position: absolute;
    width: 100%;
    height: 100%;

    .shape {
      position: absolute;
      border-radius: 50%;
      opacity: 0.08;
      animation: float 30s infinite linear;
      filter: blur(0.75rem);

      &.shape-1 {
        width: 15rem;
        height: 15rem;
        background: linear-gradient(45deg, @primary-color, @accent-color);
        top: 10%;
        left: 5%;
        animation-duration: 40s;
      }

      &.shape-2 {
        width: 12rem;
        height: 12rem;
        background: linear-gradient(45deg, @secondary-color, @primary-color);
        top: 60%;
        left: 85%;
        animation-duration: 35s;
        animation-delay: -10s;
      }

      &.shape-3 {
        width: 10rem;
        height: 10rem;
        background: linear-gradient(45deg, @accent-color, @primary-light);
        top: 85%;
        left: 15%;
        animation-duration: 45s;
        animation-delay: -20s;
      }
    }
  }

  @keyframes float {
    0% {
      transform: translateY(0) translateX(0) rotate(0deg);
    }
    50% {
      transform: translateY(-2rem) translateX(2rem) rotate(180deg);
    }
    100% {
      transform: translateY(0) translateX(0) rotate(360deg);
    }
  }

  // 光点粒子效果（简化版）
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
      opacity: 0;
      animation: sparkle 4s infinite;
      box-shadow: 0 0 0.5rem @accent-color;

      &.particle-1 {
        top: 20%;
        left: 30%;
        animation-delay: 0s;
      }

      &.particle-2 {
        top: 40%;
        left: 70%;
        animation-delay: 1s;
      }

      &.particle-3 {
        top: 70%;
        left: 50%;
        animation-delay: 2s;
      }

      &.particle-4 {
        top: 90%;
        left: 20%;
        animation-delay: 3s;
      }
    }
  }

  @keyframes sparkle {
    0%, 100% {
      opacity: 0;
      transform: scale(0.5);
    }
    50% {
      opacity: 0.8;
      transform: scale(1.2);
    }
  }

  // 英雄区
  .hero-section {
    position: relative;
    z-index: 1;
    padding: 6.25rem 1.25rem;
    text-align: center;
    max-width: 75rem;
    margin: 0 auto;

    .hero-content {
      .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 6.25rem;
        color: @primary-light;
        font-size: @font-size-small;
        font-weight: @font-weight-medium;
        margin-bottom: 2rem;

        .ivu-icon {
          color: @accent-color;
        }
      }

      .hero-title {
        font-size: 3.5rem;
        font-weight: @font-weight-bold;
        color: @text-primary;
        line-height: @line-height-tight;
        margin-bottom: 1.5rem;

        .gradient-text {
          background: linear-gradient(135deg, @primary-color, @accent-color);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
      }

      .hero-description {
        font-size: @font-size-large;
        color: @text-secondary;
        line-height: @line-height-relaxed;
        margin-bottom: 2.5rem;
        max-width: 50rem;
        margin-left: auto;
        margin-right: auto;
      }

      .hero-actions {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin-bottom: 4rem;

        .primary-btn {
          background: linear-gradient(135deg, @primary-color, @accent-color);
          border: none;
          height: 3rem;
          padding: 0 2rem;
          font-size: @font-size-base;
          font-weight: @font-weight-medium;
          box-shadow: @shadow-primary;
          transition: all @transition-slow;

          &:hover {
            background: linear-gradient(135deg, @primary-dark, @primary-color);
            box-shadow: 0 0.625rem 1.875rem rgba(59, 130, 246, 0.4);
            transform: translateY(-0.125rem);
          }
        }

        .secondary-btn {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(75, 85, 99, 0.5);
          color: @text-primary;
          height: 3rem;
          padding: 0 2rem;
          font-size: @font-size-base;
          font-weight: @font-weight-medium;
          transition: all @transition-slow;

          &:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: @primary-color;
            transform: translateY(-0.125rem);
          }
        }
      }

      .hero-stats {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 3rem;

        .stat-item {
          .stat-number {
            font-size: 2.5rem;
            font-weight: @font-weight-bold;
            background: linear-gradient(135deg, @primary-light, @accent-color);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.2;
          }

          .stat-label {
            font-size: @font-size-small;
            color: @text-tertiary;
            margin-top: 0.5rem;
          }
        }

        .stat-divider {
          width: 1px;
          height: 3rem;
          background: @separator-color;
        }
      }
    }
  }

  // 区块通用样式
  section {
    position: relative;
    z-index: 1;
    padding: 5rem 1.25rem;
    max-width: 75rem;
    margin: 0 auto;

    .section-header {
      text-align: center;
      margin-bottom: 3.75rem;

      .section-title {
        font-size: 2.5rem;
        font-weight: @font-weight-bold;
        color: @text-primary;
        margin-bottom: 1rem;
      }

      .section-subtitle {
        font-size: @font-size-large;
        color: @text-secondary;
      }
    }
  }

  // 功能特性区
  .features-section {
    .features-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 2rem;

      .feature-card {
        background: rgba(26, 26, 26, 0.8);
        border: 1px solid rgba(75, 85, 99, 0.3);
        border-radius: @border-radius-lg;
        padding: 2rem;
        backdrop-filter: blur(0.625rem);
        transition: all @transition-slow;

        &:hover {
          border-color: rgba(59, 130, 246, 0.5);
          transform: translateY(-0.25rem);
          box-shadow: @shadow-md;
        }

        .feature-icon {
          width: 4.5rem;
          height: 4.5rem;
          border-radius: @border-radius-lg;
    display: flex;
    align-items: center;
          justify-content: center;
          margin-bottom: 1.5rem;

          &.feature-icon-1 {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(6, 182, 212, 0.2));
            color: @primary-light;
          }

          &.feature-icon-2 {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(59, 130, 246, 0.2));
            color: @secondary-color;
          }

          &.feature-icon-3 {
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(16, 185, 129, 0.2));
            color: @accent-color;
          }
        }

        h3 {
          font-size: @font-size-h5;
          font-weight: @font-weight-semibold;
          color: @text-primary;
          margin-bottom: 0.75rem;
        }

        p {
          font-size: @font-size-base;
          color: @text-secondary;
          line-height: @line-height-base;
          margin-bottom: 1.25rem;
        }

        .feature-list {
          list-style: none;
          padding: 0;
          margin: 0;

          li {
      display: flex;
      align-items: center;
            gap: 0.5rem;
            font-size: @font-size-small;
            color: @text-tertiary;
            margin-bottom: 0.5rem;

            .ivu-icon {
              color: @accent-color;
              flex-shrink: 0;
            }

            &:last-child {
              margin-bottom: 0;
            }
          }
        }
      }
    }
  }

  // 使用流程区
  .process-section {
    background: rgba(15, 15, 15, 0.5);
    border-radius: @border-radius-xl;
    padding: 5rem 2.5rem;

    .process-steps {
      display: flex;
      align-items: center;
      justify-content: space-between;
      max-width: 62.5rem;
      margin: 0 auto;
      
      .step-item {
        flex: 1;
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;

        .step-number {
          font-size: 1.5rem;
          font-weight: @font-weight-bold;
          background: linear-gradient(135deg, @primary-color, @accent-color);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin-bottom: 1rem;
        }

        .step-content {
        text-align: center;

          .step-icon {
            width: 4.5rem;
            height: 4.5rem;
            border-radius: 50%;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(6, 182, 212, 0.2));
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.25rem;
            color: @primary-light;
          }

          h3 {
            font-size: @font-size-h6;
            font-weight: @font-weight-semibold;
            color: @text-primary;
            margin-bottom: 0.75rem;
          }

          p {
            font-size: @font-size-small;
            color: @text-secondary;
            line-height: @line-height-base;
          }
        }

        .step-arrow {
          position: absolute;
          right: -2rem;
          top: 50%;
          transform: translateY(-50%);
          color: @text-tertiary;
          font-size: 1.5rem;
        }

        &:last-child .step-arrow {
          display: none;
        }
      }
    }
  }

  // 价值亮点区
  .benefits-section {
    .benefits-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1.5rem;

      .benefit-card {
        background: rgba(26, 26, 26, 0.6);
        border: 1px solid rgba(75, 85, 99, 0.3);
        border-radius: @border-radius-lg;
        padding: 1.875rem;
        text-align: center;
        transition: all @transition-slow;

        &:hover {
          border-color: rgba(59, 130, 246, 0.4);
          transform: translateY(-0.25rem);
        }

        .benefit-icon {
          width: 3.75rem;
          height: 3.75rem;
          border-radius: 50%;
          background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(6, 182, 212, 0.15));
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 1.25rem;
          color: @primary-light;
        }

        h3 {
          font-size: @font-size-base;
          font-weight: @font-weight-semibold;
          color: @text-primary;
          margin-bottom: 0.625rem;
        }

        p {
          font-size: @font-size-small;
          color: @text-secondary;
          line-height: @line-height-base;
        }
      }
    }
  }

  // CTA区域
  .cta-section {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(6, 182, 212, 0.1));
    border-radius: @border-radius-xl;
    padding: 5rem 2.5rem;
    text-align: center;

    .cta-content {
      h2 {
        font-size: 2.5rem;
        font-weight: @font-weight-bold;
        color: @text-primary;
        margin-bottom: 1rem;
      }

      p {
        font-size: @font-size-large;
        color: @text-secondary;
        margin-bottom: 2.5rem;
      }

      .cta-actions {
        .cta-primary-btn {
          background: linear-gradient(135deg, @primary-color, @accent-color);
          border: none;
          height: 3.5rem;
          padding: 0 2.5rem;
          font-size: @font-size-large;
          font-weight: @font-weight-medium;
          box-shadow: @shadow-primary;
          transition: all @transition-slow;

          &:hover {
            background: linear-gradient(135deg, @primary-dark, @primary-color);
            box-shadow: 0 0.75rem 2.25rem rgba(59, 130, 246, 0.5);
            transform: translateY(-0.125rem);
          }
        }
      }
    }
  }
  
  // 响应式设计
  @media (max-width: @screen-lg) {
    .hero-section {
      padding: 5rem 1.25rem;

      .hero-content {
        .hero-title {
          font-size: 3rem;
        }
      }
    }

    .features-section .features-grid {
      grid-template-columns: 1fr;
      gap: 1.5rem;
    }

    .process-section .process-steps {
      flex-direction: column;
      gap: 2.5rem;

      .step-item {
        .step-arrow {
          display: none;
        }
      }
    }

    .benefits-section .benefits-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: @screen-md) {
    .hero-section {
      padding: 4rem 1.25rem;

      .hero-content {
        .hero-title {
          font-size: 2.5rem;
        }

        .hero-description {
          font-size: @font-size-base;
        }

        .hero-stats {
          gap: 1.5rem;

          .stat-item .stat-number {
            font-size: 2rem;
          }
        }
      }
    }

    section {
      padding: 3.75rem 1.25rem;

      .section-header {
        margin-bottom: 2.5rem;

        .section-title {
          font-size: 2rem;
        }
      }
    }

    .benefits-section .benefits-grid {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: @screen-sm) {
    .hero-section {
      padding: 3rem 1rem;

      .hero-content {
        .hero-title {
          font-size: 2rem;

          br {
            display: none;
          }
        }

        .hero-description br {
          display: none;
        }

        .hero-actions {
          flex-direction: column;
          align-items: stretch;
        }

        .hero-stats {
          flex-direction: column;
          gap: 1.5rem;

          .stat-divider {
            display: none;
          }
        }
      }
    }

    section {
      padding: 3rem 1rem;
    }

    .process-section,
    .cta-section {
      padding: 3rem 1.5rem;
    }

    // 移动端隐藏背景效果
    .floating-shapes,
    .light-particles {
      display: none;
    }
  }
</style>