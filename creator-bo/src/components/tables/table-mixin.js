import { find } from 'lodash'
import { formatNull } from '../../libs/filters'

export const TableMixin = {
  data () {
    return {
      fullScreenHeight: null,
      tableTopHeight: 0,
      defaultMargin: 10,
    }
  },

  computed: {
    tableHeight () {
      let navHeight = 60
      let tableTopHeight = 32
      let pageHeight = this.enablePagination ? 33 : 0
      let rv = this.fullScreenHeight - navHeight - this.defaultMargin
      if (this.showTableTop) {
        rv = rv - tableTopHeight - this.defaultMargin
      }
      rv = rv - this.defaultMargin - pageHeight - this.defaultMargin
      return rv
    },

    defaultMarginClass () {
      return `margin-top-${this.defaultMargin}`
    }
  },

  mounted () {
    window.addEventListener('resize', this.handleResize)
    this.handleResize()
  },

  beforeDestroy () {
    window.removeEventListener('resize', this.handleResize)
  },

  methods: {
    handleResize () {
      this.fullScreenHeight = document.documentElement.clientHeight
      if (this.$refs.tableTop) {
        this.tableTopHeight = this.$refs.tableTop.offsetHeight
      }
    },

    filterColumn (item) {
      // To filter configuration enabled, with 'and' relationship
      if (item.requiredConfigs && item.requiredConfigs.length > 0) {
        let disabled = find(item.requiredConfigs, function (config) {
          return config && !this.$store.getters[config]
        })
        if (disabled) return false
      }
      // To filter permission item, with 'or' relationship
      if (item.requiredPerms && item.requiredPerms.length > 0) {
        return this.hasAnyPermission(item.requiredPerms)
      }
      return true
    },

    completeTableColumns (columns, defaultMinWidth = 100) {
      return columns.filter(item => {
        if (item.show === false) {
          return false
        }
        return this.filterColumn(item)
      }).map((item) => {
        if (!item.render) {
          item.render = this.defaultRowRender
        }
        if (defaultMinWidth && !item.width && !item.minWidth) {
          item.minWidth = defaultMinWidth
        }
        if (item.hideFilter) {
          item.filters = null
          item.filterRemote = null
        }
        return item
      })
    },

    generateExportColumns (columns) {
      return columns.filter(item => {
        if (item.toExport === false) {
          return false
        }
        return this.filterColumn(item)
      })
    },

    defaultRowRender (h, {column, row}) {
      let data = row
      if (column.format) {
        data = column.format(data)
      } else {
        column.key.split('.').forEach((key) => {
          data = data ? data[key] : null
        })
      }
      return h('span', formatNull(data))
    }
  }
}
