<style lang="less">
  @import '../../styles/common.less';

  .table-exporter {
    display: inline-block;
  }
</style>

<template>
  <div class="table-exporter">
    <Button @click="exportTable" :type="buttonType" :loading="loading"
            icon="android-download">
      {{ title }}
    </Button>
    <Modal v-model="loading"
           :closable="false"
           :mask-closable="false"
           class="progress-modal"
           class-name="vertical-modal"
           width="516">
      <div slot="header">
        正在导出，请稍后...
      </div>
      <Progress :percent="percent" status="active"/>
      <div slot="footer" class="footer">
        <Button @click.native="cancel">中止导出</Button>
      </div>
    </Modal>
  </div>
</template>

<script>
  import FileSaver from 'file-saver'
  import moment from 'moment'
  import XLSX from 'xlsx'
  import isCallable from 'is-callable'
  import { fill } from 'lodash'
  import { APP_NAME } from '../../libs/constants'

  // Default export time for a single piece of data, milliseconds
  const singleDataLoadingTime = 6

  export default {
    props: {
      prefix: String,
      columns: {
        type: Array,
        default: () => {
          return []
        }
      },
      subColumns: {
        // {key: 'column key', columns: [{key: '', title: '', }]}
        type: Object,
        default: () => null
      },
      params: {
        type: Object,
        default: () => {
          return {}
        }
      },
      url: String,
      step: {
        type: Number,
        default: 300,
      },
      title: {
        type: String,
        default: '批量导出',
      },
      buttonType: {
        type: String,
        default: 'primary'
      },
      formatLoadedData: {
        type: Function,
        default: null
      }
    },

    data () {
      return {
        loading: false,
        page: 1,
        rows: [],
        percent: 0,
        fakeLoadedPercent: 0,
        canceled: false,
        timer: null,
        showFakeLoading: false
      }
    },

    methods: {
      genFilename () {
        let prefix = APP_NAME
        if (this.prefix) {
          prefix = `${prefix} - ${this.prefix}`
        }
        return `${prefix} - ${moment().format('YYYY-MM-DD HH-mm-ss')}.xlsx`
      },

      async load () {
        let params = Object.assign({}, this.params, {
          page: this.page,
          per_page: this.step,
        })
        let resp = {}
        try {
          resp = await this.$http.get(this.url, {
            params: params
          })
        } catch (error) {
          this.canceled = true
          return
        }
        if (isCallable(this.formatLoadedData)) {
          resp.rows = this.formatLoadedData(resp.rows)
        }
        if (this.page === 1) {
          this.rows = resp.rows
        } else if (resp.rows) {
          this.rows.push(...resp.rows)
        }
        this.showFakeLoading = false
        if (resp.pagination) {
          this.setExportPercentage(resp.pagination)
          // 数据报表相关结果不返回pagination
          this.page = resp.pagination.next
          if (resp.pagination.has_next && !this.canceled) {
            await this.load()
          }
        } else {
          this.percent = 98
          this.finish()
        }
      },

      setExportPercentage (pagination) {
        let currentPage = pagination.page
        let lastPage = pagination.last
        let pageLoadingTime = this.step * singleDataLoadingTime
        if (currentPage === lastPage) {
          let lastPageData = pagination.total - (lastPage - 1) * this.step
          pageLoadingTime = lastPageData * singleDataLoadingTime
        }
        let progressUpdateTotalTime = 0
        this.setPercentProgress(progressUpdateTotalTime, pageLoadingTime, pagination)
      },

      setPercentProgress (progressUpdateTotalTime, pageLoadingTime, pagination) {
        let progressUpdateTime = this.step
        let totalPages = pagination.last
        let totalPercent = 100 - this.fakeLoadedPercent
        this.progressTimer = setTimeout(() => {
          progressUpdateTotalTime += progressUpdateTime
          let pageLoopCount = pageLoadingTime/progressUpdateTime
          let increase = Math.floor((totalPercent/totalPages)/pageLoopCount)
          if (progressUpdateTotalTime < pageLoadingTime) {
            this.percent += increase
            this.setPercentProgress(progressUpdateTotalTime, pageLoadingTime, pagination)
          } else if (pagination.last === pagination.page) {
            this.finish()
          }
        }, progressUpdateTime)
      },

      // default fake max percentage is 20 percent
      setFakePercentage () {
        if (!this.showFakeLoading) {
          return
        }
        this.fakeTimer = setTimeout(() => {
          if (this.showFakeLoading && this.percent < 20) {
            this.percent += 1
            this.fakeLoadedPercent = this.percent
            this.setFakePercentage()
          }
        }, 100)
      },

      mapRowData (row, cols) {
        return cols.map(col => {
          if (col.format) {
            return col.format(row)
          }
          let data = row
          col.key.split('.').forEach((key) => {
            data = data ? data[key] : null
          })
          return data
        })
      },

      async loadData () {
        await this.load()
        let columns = this.columns.map(col => {
          return col.title
        })
        let subColumns = this.subColumns && this.subColumns.columns
        let subColumnsKey = this.subColumns && this.subColumns.key
        let rows = []
        this.rows.forEach(row => {
          let rowData = this.mapRowData(row, this.columns)
          let subRows = null
          if (subColumns && subColumnsKey) {
            subRows = (row[this.subColumns.key] || []).map(
              subRow => this.mapRowData(subRow, this.subColumns.columns))
            let first = subRows.shift()
            if (first) {
              rowData.push(...first)
            }
          }
          rows.push(rowData)
          if (subRows && subRows.length > 0) {
            let placeholder = new Array(columns.length)
            fill(placeholder, '')
            subRows = subRows.map(subRow => {
              subRow.unshift(...placeholder)
              return subRow
            })
            rows.push(...subRows)
          }
        })

        if (subColumns) {
          columns.push(...subColumns.map(col => col.title))
        }

        rows.unshift(columns)
        return rows
      },

      s2ab (s) {
        let buf = new ArrayBuffer(s.length)
        let view = new Uint8Array(buf)
        for (let i = 0; i !== s.length; ++i) {
          view[i] = s.charCodeAt(i) & 0xFF
        }
        return buf
      },

      async exportTable () {
        this.start()
        let data = await this.loadData()
        if (!this.canceled) {
          let ws = XLSX.utils.aoa_to_sheet(data)
          let wb = XLSX.utils.book_new()
          XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')
          let wbout = XLSX.write(wb, {
            type: 'binary',
            bookType: 'xlsx'
          })
          FileSaver.saveAs(new Blob([this.s2ab(wbout)], {
            type: 'application/octet-stream'
          }), this.genFilename())
        }
      },

      start () {
        this.loading = true
        this.showFakeLoading = true
        this.setFakePercentage()
      },

      finish () {
        this.percent = 100
        // show complete clearly, then hide
        this.timer = setTimeout(() => {
          this.reset()
        }, 500)
      },

      cancel () {
        this.canceled = true
        this.loading = false
      },

      reset () {
        this.loading = false
        this.page = 1
        this.rows = []
        this.percent = 0
        this.canceled = false
        clearTimeout(this.timer)
        clearTimeout(this.progressTimer)
        clearTimeout(this.fakeTimer)
      },
    },
  }
</script>

