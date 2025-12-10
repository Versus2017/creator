<template>
  <div class="research-list-page">
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
        <div class="header-content">
          <h1 class="page-title">
            <Icon type="ios-flask" />
            研究记录
          </h1>
          <p class="page-description">查看您的脚本研究历史和成功经验</p>
        </div>
      </div>

      <!-- 研究列表 -->
      <div class="research-container">
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <Spin size="large">
            <Icon type="ios-loading" size="48" class="spin-icon-load"></Icon>
            <div class="loading-text">加载中...</div>
          </Spin>
        </div>

        <!-- 空状态 -->
        <div v-else-if="researches.length === 0" class="empty-state">
          <div class="empty-icon">🔬</div>
          <h3>暂无研究记录</h3>
          <p>前往"脚本"页面，选择效果好的脚本进行研究分析</p>
          <Button type="primary" size="large" @click="goToScripts">
            <Icon type="ios-document" />
            查看脚本
          </Button>
        </div>

        <!-- 研究卡片列表 -->
        <div v-else class="research-list">
          <div 
            v-for="research in researches" 
            :key="research.id"
            class="research-card"
            @click="viewResearch(research)"
          >
            <div class="card-header">
              <div class="header-left">
                <h3 class="research-title">
                  {{ research.script ? research.script.title : '未知脚本' }}
                </h3>
                <Tag :color="getStatusColor(research.status)">
                  {{ research.status.label }}
                </Tag>
              </div>
            </div>

            <!-- 关键发现 -->
            <div v-if="research.key_findings && research.key_findings.length" class="findings-section">
              <h4>关键发现：</h4>
              <div class="findings-list">
                <div 
                  v-for="(finding, index) in research.key_findings.slice(0, 3)" 
                  :key="index"
                  class="finding-item"
                >
                  <Icon type="ios-checkmark-circle" />
                  <span>{{ finding }}</span>
                </div>
                <div v-if="research.key_findings.length > 3" class="more-findings">
                  还有 {{ research.key_findings.length - 3 }} 个发现...
                </div>
              </div>
            </div>

            <!-- 研究总结 -->
            <div v-if="research.summary" class="summary-section">
              <p class="summary-text">{{ research.summary }}</p>
            </div>

            <!-- 卡片底部 -->
            <div class="card-footer">
              <div class="footer-meta">
                <Icon type="ios-time" />
                <span>{{ formatDate(research.created_at) }}</span>
              </div>
              <div class="footer-actions">
                <Button 
                  type="text" 
                  size="small"
                  @click.stop="viewScript(research.script)"
                >
                  <Icon type="ios-document" />
                  查看脚本
                </Button>
                <Button 
                  type="text" 
                  size="small"
                  class="delete-btn"
                  @click.stop="deleteResearch(research)"
                >
                  <Icon type="ios-trash" />
                  删除
                </Button>
              </div>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="total > 0" class="pagination-wrapper">
          <Page 
            :total="total" 
            :current="currentPage"
            :page-size="pageSize"
            show-total
            @on-change="handlePageChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import moment from 'moment'

export default {
  name: 'ResearchList',
  
  data() {
    return {
      // 研究列表
      researches: [],
      total: 0,
      currentPage: 1,
      pageSize: 10,
      
      // 加载状态
      loading: false
    }
  },

  methods: {
    // 加载研究列表
    async loadResearches() {
      this.loading = true
      try {
        const params = {
          page: this.currentPage,
          per_page: this.pageSize
        }
        
        const response = await this.$http.get('/web/researches', { params })

        if (response && response.success) {
          // ✅ 后端已按脚本去重，每个脚本只返回最新的一条研究
          this.researches = response.rows || []
          this.total = response.pagination && response.pagination.total ? response.pagination.total : 0
        }
      } catch (error) {
        console.error('加载研究列表失败:', error)
        this.$Message.error('加载失败，请重试')
      } finally {
        this.loading = false
      }
    },

    // 翻页
    handlePageChange(page) {
      this.currentPage = page
      this.loadResearches()
    },

    // 查看研究详情
    viewResearch(research) {
      this.$router.push({ 
        name: 'research-chat', 
        query: { researchId: research.id } 
      })
    },

    // 查看脚本
    viewScript(script) {
      if (!script) return
      this.$router.push({ 
        name: 'script-detail', 
        params: { id: script.id } 
      })
    },

    // 删除研究
    deleteResearch(research) {
      this.$Modal.confirm({
        title: '确认删除',
        content: '确定要删除这条研究记录吗？删除后无法恢复。',
        onOk: async () => {
          try {
            await this.$http.delete(`/web/researches/${research.id}`)
            this.$Message.success('删除成功')
            this.loadResearches()
          } catch (error) {
            console.error('删除失败:', error)
            this.$Message.error('删除失败，请重试')
          }
        }
      })
    },

    // 前往脚本页面
    goToScripts() {
      this.$router.push({ name: 'scripts' })
    },

    // 获取状态颜色
    getStatusColor(status) {
      if (!status || !status.name) return 'default'
      const colorMap = {
        IN_PROGRESS: 'warning',
        COMPLETED: 'success',
        ARCHIVED: 'default'
      }
      return colorMap[status.name] || 'default'
    },

    // 格式化日期
    formatDate(date) {
      if (!date) return ''
      return moment(date).format('YYYY-MM-DD HH:mm')
    }
  },

  mounted() {
    this.loadResearches()
  }
}
</script>

<style lang="less" scoped>
@import '../styles/variables.less';

.research-list-page {
  height: ~"calc(100vh - 64px)";
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 30%, #312e81 70%, #1e1b4b 100%);
  position: relative;
  overflow: hidden;
}

// 背景特效（与其他页面一致）
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
  overflow-y: auto;
  padding: 2rem;
}

// 页面头部
.page-header {
  max-width: 1000px;
  margin: 0 auto 2rem;

  .header-content {
    .page-title {
      font-size: 2rem;
      font-weight: @font-weight-bold;
      color: #FFFFFF;
      margin-bottom: 0.5rem;
      display: flex;
      align-items: center;
      gap: 0.75rem;

      .ivu-icon {
        font-size: 2rem;
      }
    }

    .page-description {
      font-size: 1rem;
      color: rgba(255, 255, 255, 0.8);
    }
  }
}

// 研究容器
.research-container {
  max-width: 1000px;
  margin: 0 auto;
  min-height: 400px;
}

// 加载和空状态（与scripts.vue一致）
.loading-state,
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #FFFFFF;

  .empty-icon {
    font-size: 4rem;
    margin-bottom: 1.5rem;
  }

  h3 {
    font-size: 1.5rem;
    font-weight: @font-weight-semibold;
    margin-bottom: 0.75rem;
  }

  p {
    font-size: 1rem;
    opacity: 0.8;
    margin-bottom: 2rem;
  }
}

// 研究列表
.research-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

// 研究卡片
.research-card {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: @border-radius-lg;
  padding: 1.5rem;
  cursor: pointer;
  transition: all @transition-base;

  &:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(59, 130, 246, 0.5);
    box-shadow: 0 0.5rem 2rem rgba(59, 130, 246, 0.3);
    transform: translateY(-4px);
  }

  .card-header {
    margin-bottom: 1rem;

    .header-left {
      display: flex;
      align-items: center;
      gap: 1rem;

      .research-title {
        font-size: 1.25rem;
        font-weight: @font-weight-semibold;
        color: #FFFFFF;
        margin: 0;
      }
    }
  }

  .findings-section {
    margin-bottom: 1rem;

    h4 {
      font-size: 0.875rem;
      color: rgba(255, 255, 255, 0.8);
      margin-bottom: 0.75rem;
    }

    .findings-list {
      .finding-item {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.875rem;
        line-height: 1.5;

        .ivu-icon {
          color: @success-color;
          flex-shrink: 0;
          margin-top: 0.125rem;
        }
      }

      .more-findings {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.5);
        margin-top: 0.5rem;
        font-style: italic;
      }
    }
  }

  .summary-section {
    margin-bottom: 1rem;

    .summary-text {
      color: rgba(255, 255, 255, 0.8);
      font-size: 0.875rem;
      line-height: 1.6;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
  }

  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);

    .footer-meta {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.875rem;
      color: rgba(255, 255, 255, 0.6);
    }

    .footer-actions {
      display: flex;
      gap: 0.75rem;

      /deep/ .ivu-btn-text {
        color: rgba(255, 255, 255, 0.6);
        transition: all @transition-fast;

        &:hover {
          color: @primary-light;
        }

        &.delete-btn:hover {
          color: @error-color;
        }
      }
    }
  }
}

// 分页（与scripts.vue一致）
.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 2rem 0;

  /deep/ .ivu-page {
    .ivu-page-item {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.2);

      a {
        color: rgba(255, 255, 255, 0.8);
      }

      &:hover {
        background: rgba(255, 255, 255, 0.15);
        border-color: @primary-color;
      }

      &.ivu-page-item-active {
        background: @primary-color;
        border-color: @primary-color;

        a {
          color: #FFFFFF;
        }
      }
    }

    .ivu-page-prev, .ivu-page-next {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.2);

      a {
        color: rgba(255, 255, 255, 0.8);
      }

      &:hover {
        background: rgba(255, 255, 255, 0.15);
        border-color: @primary-color;
      }
    }
  }
}
</style>

