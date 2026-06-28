<template>
  <div>
    <Row v-if="showTableTop" ref="tableTop" class="top-container">
      <search-input v-if="canSearch" v-model="keyword"
                    :width="searchInputWidth"
                    :placeholder="searchInputPlaceholder"
                    @on-search="onSearch"></search-input>
      <slot name="filters"></slot>
      <div class="top-container-right">
        <table-exporter v-if="showExporter"
                        :url="resourcePath"
                        :prefix="exporterPrefix"
                        :columns="exporterColumns"
                        :subColumns="exporterSubColumns"
                        :params="params"
                        :title="exporterTitle"/>
        <slot name="header-buttons"></slot>
      </div>
      <slot name="extra-content"></slot>
    </Row>
    <Row :class="defaultMarginClass">
      <Table
        :data="rows"
        :columns="_columns"
        border
        :height="tableHeight"
        :loading="loading"
        no-data-text="暂无数据"
        @on-sort-change="onSortChange">
      </Table>
    </Row>
    <Row :class="defaultMarginClass" v-if="enablePagination">
      <Page :current="pagination.page"
            :total="pagination.total"
            :page-size="pagination.per_page"
            show-total
            show-sizer
            show-elevator
            :page-size-opts="[15, 20, 30]"
            @on-change="onPageChange"
            @on-page-size-change="onPageSizeChange"/>
    </Row>
  </div>
</template>

<script>
  import { TableMixin } from './table-mixin'
  import TableExporter from './table-exporter'
  import SearchInput from './search-input'
  import { find } from 'lodash'

  export default {
    name: 'BaseTable',

    mixins: [TableMixin],

    components: {
      TableExporter,
      SearchInput
    },

    props: {
      showTableTop: {
        type: Boolean,
        default: true
      },
      // SearchBar Config
      canSearch: {
        type: Boolean,
        default: true
      },
      searchInputWidth: {
        type: Number,
        default: 300
      },
      searchInputPlaceholder: {
        type: String,
        default: '请输入搜索关键字'
      },

      // Exporter Config
      canExport: {
        type: Boolean,
        default: true
      },
      exporterTitle: {
        type: String,
        default: '批量导出'
      },
      exporterUrl: {
        type: String,
        default: null
      },
      exporterPrefix: {
        type: String,
        default: 'List'
      },
      exporterSubColumns: {
        type: Object,
        default: () => null
      },

      // List Config
      columns: {
        type: Array,
        default: () => []
      },
      resourcePath: String,
      resourceParams: {
        type: Object,
        default: () => {}
      },
      enablePagination: {
        type: Boolean,
        default: true
      },
      afterLoadData: {
        type: Function,
        default: null
      },
      dataFieldName: {
        type: String,
        default: 'rows'
      },
    },

    data () {
      let params = {
        ...this.resourceParams,
        ...this.getStateQuery()
      }
      return {
        params: params,
        keyword: params.keyword,
        pagination: {
          page:  params.page || 1,
          per_page: params.per_page || 15,
          total: params.total
        },
        rows: [],
        loading: false
      }
    },

    computed: {
      showExporter () {
        return this.canExport && this.rows && this.rows.length > 0
      },

      exporterColumns () {
        if (this.showExporter) {
          return this.generateExportColumns(this.columns)
        }
        return []
      },

      _columns () {
        let cols = this.columns.map(column => {
          // set filter value for cache filters
          let filters = column.filters
          if (filters && filters.length && filters.length > 0 && !column.hideFilter) {
            let param = column.filterParam || column.key
            let value = this.params[param]
            let option = find(filters, filter => filter.value === value)
            // filteredValue 不能设置为null或undefined
            if (option) {
              column.filteredValue = [value]
            }
            if (!option && column.filteredValue) {
              delete column['filteredValue']
            }
          }
          // set sort columns for cache sort
          if (column.sortable && this.params.sort_by && column.key === this.params.sort_by) {
            column.sortType = this.params.is_desc ? 'desc' : 'asc'
          } else {
            // sortType 不能设置为null或undefined，否则排序会乱。
            column.sortType && delete column.sortType
          }

          return column
        })
        return this.completeTableColumns(cols)
      }
    },

    methods: {
      pageKey () {
        return `${this.$route.path}+${this.$route.query.nonce}`
      },

      getStateQuery () {
        let ret = this.$store.getters['listQuery'](this.pageKey()) || {}
        return ret
      },

      fetchParams () {
        var params = Object.assign({}, this.params)
        Object.keys(params).forEach(key => {
          let value = params[key]
          if (value == null) {
            delete params[key]
          } else if (typeof value === 'object') {
            if (value['value'] !== null) {
              params[key] = value['value']
            } else {
              delete params[key]
            }
          }
        })
        return params
      },

      reloadPage (page) {
        let query = Object.assign({}, this.params)
        if (page) {
          query.page = page
        }
        Object.keys(query).forEach(key => query[key] == null && delete query[key])
        this.$store.commit('clearPageQueryCache', `${this.$route.path}+`)
        this.$store.commit('setListQuery', {pageKey: this.pageKey(), params: query})
        if (this.loadData) {
          this.loadData(page)
        }
      },

      setParams (params, reload=true) {
        this.params = Object.assign(this.params, params)
        if (reload) {
          this.reloadPage(1)
        }
        this.$emit('on-params-change', this.params)
      },

      onSearch (keyword) {
        // 在 IE 下，input 的 value change 事件在页面初始化时会自动触发一次，
        // 导致多余的数据加载，这里判断一下若新旧 keyword 相同，则不重新加载数据
        let newKeyword = keyword ? keyword : ''
        let oldKeyword = this.params.keyword ? this.params.keyword : ''
        if (newKeyword === oldKeyword) {
          return
        }
        this.params.keyword = keyword
        this.reloadPage(1)
      },

      onPageChange (page) {
        if (page) {
          this.pagination.page = page
        }
        this.params.page = this.pagination.page
        this.reloadPage(page)
      },

      onPageSizeChange (perPage) {
        if (perPage) {
          this.pagination.per_page = perPage
        }
        this.params.per_page = this.pagination.per_page
        this.reloadPage(1)
      },

      onSortChange ({ key, order }) {
        this.params.sort_by = key
        this.params.is_desc = order === 'normal' ? null : order === 'desc'
        this.reloadPage(1)
      },

      async loadData (page, per_page) {
        let params = this.fetchParams()
        if (this.enablePagination) {
          if (page) {
            this.pagination.page = page
          }
          if (per_page) {
            this.pagination.per_page = per_page
          }
          params.page = this.pagination.page
          params.per_page = this.pagination.per_page
        }
        this.loading = true
        try {
          let resp = await this.$http.get(this.resourcePath, {params: params})
          if (this.afterLoadData) {
            this.afterLoadData(resp)
          }
          this.rows = resp[this.dataFieldName]
          if (this.enablePagination && resp.pagination) {
            resp.pagination.per_page = this.pagination.per_page
            this.pagination = resp.pagination
            this.params.total = this.pagination.total
          }
        } finally {
          this.loading = false
        }
      }
    },

    mounted () {
      this.loadData()
    }
  }
</script>

<style lang="less" scoped>
  @import '../../styles/common.less';

  .top-container {
    display: flex;
    align-items: center;
    justify-content: space-between;

    .top-container-right {
      display: flex;
      align-items: center;
      margin-left: auto;

      button {
        margin-left: 3px;
      }
    }

    .table-importer {
      margin-left: 3px;
    }
  }
</style>
