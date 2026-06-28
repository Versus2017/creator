<template>
  <div class="scripts-page">
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
        <div class="header-content">
          <h1 class="page-title">
            <Icon type="ios-document-outline" />
            脚本管理
          </h1>
          <p class="page-description">查看和管理您的视频脚本</p>
        </div>
        
        <Button 
          type="primary" 
          size="large"
          class="create-btn"
          @click="goToCreativity"
        >
          <Icon type="md-add" />
          创建新脚本
        </Button>
      </div>

      <!-- 搜索和筛选栏 -->
      <div class="filter-section">
        <Input 
          v-model="searchKeyword" 
          search 
          placeholder="搜索脚本标题..."
          class="search-input"
          size="large"
          @on-search="handleSearch"
        >
          <Icon type="ios-search" slot="prefix" />
        </Input>
        
        <Select 
          v-model="filterStatus" 
          placeholder="全部状态" 
          class="filter-select"
          size="large"
          @on-change="loadScripts"
        >
          <Option value="">全部状态</Option>
          <Option value="10">草稿</Option>
          <Option value="30">已完成</Option>
        </Select>
      </div>

      <!-- 脚本列表 -->
      <div class="scripts-container">
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <Spin size="large">
            <Icon type="ios-loading" size="48" class="spin-icon-load"></Icon>
            <div class="loading-text">加载中...</div>
          </Spin>
        </div>

        <!-- 空状态 -->
        <div v-else-if="scripts.length === 0" class="empty-state">
          <div class="empty-icon">📝</div>
          <h3>暂无脚本</h3>
          <p>前往"创意"页面开始创作您的第一个视频脚本</p>
          <Button type="primary" size="large" @click="goToCreativity">
            <Icon type="ios-bulb" />
            开始创作
          </Button>
        </div>

        <!-- 脚本卡片列表 -->
        <div v-else class="scripts-list">
          <div 
            v-for="script in scripts" 
            :key="script.id"
            class="script-card"
            @click="viewScript(script)"
          >
            <div class="card-header">
              <div class="header-left">
                <h3 class="script-title">{{ script.title }}</h3>
                <Tag :color="getStatusColor(script.status)">
                  {{ script.status.label }}
                </Tag>
              </div>
              <div class="header-right">
                <Button 
                  type="text" 
                  size="small" 
                  class="action-btn"
                  @click.stop="editScript(script)"
                >
                  <Icon type="ios-create" />
                </Button>
                <Button 
                  type="text" 
                  size="small" 
                  class="action-btn delete-btn"
                  @click.stop="deleteScript(script)"
                >
                  <Icon type="ios-trash" />
                </Button>
              </div>
            </div>
            
            <div class="card-meta">
              <div class="meta-item">
                <Icon type="ios-text" />
                <span>{{ script.word_count || 0 }} 字</span>
              </div>
              <div class="meta-item">
                <Icon type="ios-pricetag" />
                <span>{{ script.format_type || '未指定' }}</span>
              </div>
              <div class="meta-item">
                <Icon type="ios-time" />
                <span>{{ formatDate(script.created_at) }}</span>
              </div>
            </div>

            <div class="card-preview">
              {{ getPreview(script.content) }}
            </div>

            <div class="card-footer">
              <Button type="text" size="small" @click.stop="editScript(script)">
                <Icon type="ios-create" />
                编辑
              </Button>
              <Button 
                type="text" 
                size="small" 
                class="research-btn"
                @click.stop="startResearch(script)"
              >
                <Icon type="ios-bulb" />
                研究
              </Button>
              <Button type="text" size="small">
                <Icon type="ios-copy" />
                复制
              </Button>
              <Button type="text" size="small">
                <Icon type="ios-share" />
                导出
              </Button>
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
  name: 'Scripts',
  
  data() {
    return {
      // 脚本列表
      scripts: [],
      total: 0,
      currentPage: 1,
      pageSize: 12,
      
      // 搜索和筛选
      searchKeyword: '',
      filterStatus: '',
      
      // 加载状态
      loading: false
    }
  },

  methods: {
    // 加载脚本列表
    async loadScripts() {
      this.loading = true
      try {
        // 构建请求参数，过滤空值
        const params = {
          page: this.currentPage,
          per_page: this.pageSize
        }
        
        // 只有当keyword有值时才添加
        if (this.searchKeyword && this.searchKeyword.trim()) {
          params.keyword = this.searchKeyword.trim()
        }
        
        // 只有当status有值时才添加（必须是数字）
        if (this.filterStatus) {
          params.status = parseInt(this.filterStatus)
        }
        
        const response = await this.$http.get('/web/scripts', { params })

        if (response && response.success) {
          this.scripts = response.rows || []
          this.total = response.pagination && response.pagination.total ? response.pagination.total : 0
        }
      } catch (error) {
        console.error('加载脚本列表失败:', error)
        this.$Message.error('加载失败，请重试')
      } finally {
        this.loading = false
      }
    },

    // 搜索
    handleSearch() {
      this.currentPage = 1
      this.loadScripts()
    },

    // 翻页
    handlePageChange(page) {
      this.currentPage = page
      this.loadScripts()
    },

    // 查看脚本
    viewScript(script) {
      this.$router.push({ name: 'script-detail', params: { id: script.id } })
    },

    // 编辑脚本
    editScript(script) {
      this.$router.push({ name: 'script-detail', params: { id: script.id }, query: { edit: 'true' } })
    },

    // 删除脚本
    deleteScript(script) {
      this.$Modal.confirm({
        title: '确认删除',
        content: `确定要删除脚本"${script.title}"吗？删除后无法恢复。`,
        onOk: async () => {
          try {
            await this.$http.delete(`/web/scripts/${script.id}`)
            this.$Message.success('删除成功')
            this.loadScripts()
          } catch (error) {
            console.error('删除失败:', error)
            this.$Message.error('删除失败，请重试')
          }
        }
      })
    },

    // 前往创意页面
    goToCreativity() {
      this.$router.push({ name: 'creativity' })
    },

    // 开始研究脚本
    startResearch(script) {
      this.$router.push({ 
        name: 'research-chat', 
        query: { scriptId: script.id } 
      })
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

    // 获取预览文本
    getPreview(content) {
      if (!content) return '暂无内容'
      return content.length > 120 ? content.substring(0, 120) + '...' : content
    },

    // 格式化日期
    formatDate(date) {
      if (!date) return ''
      return moment(date).format('YYYY-MM-DD HH:mm')
    }
  },

  mounted() {
    this.loadScripts()
  }
}
</script>

<style lang="less" scoped>
@import '../styles/variables.less';

.scripts-page {
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
  align-items: center;

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

  .create-btn {
    background: linear-gradient(135deg, @primary-color, @primary-light);
    border: none;
    box-shadow: 0 0.25rem 1rem rgba(59, 130, 246, 0.3);
    transition: all @transition-base;

    &:hover {
      box-shadow: 0 0.5rem 1.5rem rgba(59, 130, 246, 0.5);
      transform: translateY(-2px);
    }
  }
}

// 筛选栏
.filter-section {
  max-width: 1200px;
  margin: 0 auto 2rem;
  display: flex;
  gap: 1rem;

  .search-input {
    flex: 1;
    max-width: 500px;

    /deep/ .ivu-input {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: #FFFFFF;
      backdrop-filter: blur(10px);

      &::placeholder {
        color: rgba(255, 255, 255, 0.5);
      }

      &:focus {
        background: rgba(255, 255, 255, 0.15);
        border-color: @primary-color;
      }
    }

    /deep/ .ivu-input-prefix {
      color: rgba(255, 255, 255, 0.6);
    }
  }

  .filter-select {
    width: 200px;

    /deep/ .ivu-select-selection {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: #FFFFFF;
      backdrop-filter: blur(10px);

      &:hover, &:focus {
        background: rgba(255, 255, 255, 0.15);
        border-color: @primary-color;
      }
    }

    /deep/ .ivu-select-placeholder {
      color: rgba(255, 255, 255, 0.5);
    }

    /deep/ .ivu-select-selected-value {
      color: #FFFFFF;
    }
  }
}

// 脚本容器
.scripts-container {
  max-width: 1200px;
  margin: 0 auto;
  min-height: 400px;
}

// 加载状态
.loading-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #FFFFFF;

  .loading-text {
    margin-top: 1rem;
    font-size: 1rem;
  }
}

// 空状态
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

// 脚本列表
.scripts-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

// 脚本卡片
.script-card {
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
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;

    .header-left {
      flex: 1;
      display: flex;
      align-items: center;
      gap: 1rem;

      .script-title {
        font-size: 1.25rem;
        font-weight: @font-weight-semibold;
        color: #FFFFFF;
        margin: 0;
      }
    }

    .header-right {
      display: flex;
      gap: 0.5rem;

      .action-btn {
        color: rgba(255, 255, 255, 0.6);
        transition: all @transition-fast;

        &:hover {
          color: @primary-light;
          background: rgba(59, 130, 246, 0.1);
        }

        &.delete-btn:hover {
          color: @error-color;
          background: rgba(255, 59, 48, 0.1);
        }
      }
    }
  }

  .card-meta {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 1rem;

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

  .card-preview {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.875rem;
    line-height: 1.6;
    margin-bottom: 1rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .card-footer {
    display: flex;
    gap: 1rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);

    /deep/ .ivu-btn-text {
      color: rgba(255, 255, 255, 0.6);
      transition: all @transition-fast;

      &:hover {
        color: @primary-light;
      }
    }

    .research-btn {
      /deep/ .ivu-icon {
        color: @accent-color;
      }

      &:hover {
        /deep/ .ivu-icon {
          color: @accent-color;
        }
        background: rgba(255, 149, 0, 0.1);
      }
    }
  }
}

// 分页
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

// 响应式
@media (max-width: @screen-md) {
  .content-wrapper {
    padding: 1rem;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;

    .create-btn {
      width: 100%;
    }
  }

  .filter-section {
    flex-direction: column;

    .search-input {
      max-width: 100%;
    }

    .filter-select {
      width: 100%;
    }
  }

  .script-card {
    .card-meta {
      flex-wrap: wrap;
      gap: 1rem;
    }

    .card-footer {
      flex-wrap: wrap;
    }
  }
}
</style>
