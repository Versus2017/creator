<style lang="less">
  @import '../../styles/common.less';

  .table-importer {
    margin-left: 8px;

    .title-wrapper {
      span {
        margin-left: 4px;
      }
    }

    .spin-icon-load {
      animation: load-spin 1s linear infinite;
    }

    @keyframes load-spin {
      from {
        transform: rotate(0deg);
      }
      50% {
        transform: rotate(180deg);
      }
      to {
        transform: rotate(360deg);
      }
    }

    &.ivu-upload-drag {
      height: calc(~"100vh - 122px");
      display: flex;
      align-items: center;
      justify-content: center;

      .ivu-icon {
        font-size: 60px;
        display: block;
      }

      .title-wrapper {
        display: block;
      }
    }
  }
</style>

<template>
  <label class="table-importer"
         for="table-importer"
         :class="{
           'ivu-btn-loading': loading,
           'ivu-btn': type === 'button',
           'ivu-btn-primary': type === 'button',
           'ivu-upload-drag': type === 'drag'
         }"
         @change="importTable"
         @drop.prevent="onDrop"
         @dragover.prevent="dragOver = true"
         @dragleave.prevent="dragOver = false">
    <div class="title-wrapper">
      <template v-if="loading">
        <Icon type="load-c" class="spin-icon-load"/>
        <span>导入中...</span>
      </template>
      <template v-else>
        <Icon type="android-upload"/>
        <span>{{ title }}</span>
      </template>
    </div>
    <input
      id="table-importer"
      type="file"
      style="display: none"
      ref="file"
      :disabled="loading"
      accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel">
  </label>
</template>

<script>
  import XLSX from 'xlsx'

  export default {
    props: {
      columns: {
        type: Array,
        default: () => {
          return []
        },
      },
      title: {
        type: String,
        default: '批量导入',
      },
      type: {
        type: String,
        default: 'button',
      },
      importing: {
        type: Boolean,
        default: false,
      }
    },

    data () {
      return {
        loading: false,
        dragOver: false,
      }
    },

    watch: {
      importing (val) {
        this.loading = val
      }
    },

    methods: {
      async onDrop (e) {
        if (this.type === 'drag') {
          this.dragOver = false
          let files = e.dataTransfer.files
          this.$emit('load', await this.getSheet(files[0]))
        }
      },

      async importTable (e) {
        let files = e.target.files
        if (files.length > 0) {
          this.$emit('load', await this.getSheet(files[0]))
        }
      },

      getSheet (f) {
        this.$emit('start')
        return new Promise(resolve => {
          this.$nextTick(() => {
            if (FileReader.prototype.readAsBinaryString === undefined) {
              FileReader.prototype.readAsBinaryString = function (fileData) {
                let binary = ''
                let pt = this
                let reader = new FileReader()
                reader.onload = function () {
                  let bytes = new Uint8Array(reader.result)
                  let length = bytes.byteLength
                  for (let i = 0; i < length; i++) {
                    binary += String.fromCharCode(bytes[i])
                  }
                  //pt.result  - readonly so assign content to another property
                  pt.content = binary
                  pt.onload()
                }
                reader.readAsArrayBuffer(fileData)
              }
            }

            let reader = new FileReader()
            reader.onload = e => {
              try {
                let workbook = XLSX.read(e ? e.target.result : reader.content, {type: 'binary'})
                let sheet = workbook.Sheets[workbook.SheetNames[0]]
                let data = XLSX.utils.sheet_to_json(sheet)
                resolve(data.map(row => {
                  let rv = {}
                  this.columns.map(col => {
                    rv[col.name] = row[col.label]
                  })
                  return rv
                }))
              } catch (e) {
                this.$Notice.warning({
                  title: '无法导入',
                  desc: 'Excel 文件格式不正确'
                })
              } finally {
                this.$refs.file.value = ''
              }
            }
            reader.readAsBinaryString(f)
          })
        })
      }
    }
  }
</script>
