<template>
  <div>
    <base-table
      ref="list"
      :columns="columns"
      :resourcePath="path"
      :showTableTop="false"
      :afterLoadData="afterLoadData"
      :enablePagination="false"
      dataFieldName="configs"
    ></base-table>
  </div>
</template>

<script>
  import BaseTable from '../../components/tables/base-table'
  import EditableCol from '../../components/tables/editable-col'

  export default {
    name: 'Config',

    components: {
      EditableCol,
      BaseTable
    },

    data () {
      return {
        path: '/admin/configs'
      }
    },

    computed: {
      columns () {
        let rv = [
          {
            key: 'actions',
            title: '操作',
            width: 92,
            render: (h, params) => {
              return h('Button', {
                props: {
                  type: params.row.isEditing ? 'success' : 'primary',
                  loading: params.row.editLoading
                },
                on: {
                  click: () => {
                    this.confirm(params.row)
                  }
                }
              }, params.row.isEditing ? '保存' : '编辑')
            }
          },
          {
            key: 'name',
            title: '名称',
            width: 150
          },
          {
            key: 'value',
            title: '值',
            width: 100,
            render: (h, {row}) => {
              return h(EditableCol, {
                props: {
                  value: row.value,
                  editing: row.isEditing,
                  inputType: row.type,
                  switchOn: '开',
                  switchOff: '关',
                  width: '60px'
                },
                on: {
                  switchChanged: (value) => {
                    row.newValue = `${value}`
                  },
                  input: (value) => {
                    row.newValue = value
                  }
                }
              })
            }
          },
          {
            key: 'key',
            title: 'Key',
            width: 220
          },
          {
            key: 'desc',
            title: '描述'
          }
        ]
        return rv
      }
    },

    methods: {
      afterLoadData (resp) {
        let data = resp.configs.map((row) => {
          row.isEditing = false
          row.editLoading = false
          row.newValue = null
          return row
        })
        resp.configs = data
      },

      async confirm (row) {
        if (!row.isEditing) {
          row.isEditing = true
          return
        }
        if (row.newValue === null) {
          row.isEditing = false
          return
        }
        row.editLoading = true
        try {
          await this.$http.put(this.path, {
            key: row.key,
            value: row.newValue
          })
          this.$Message.success('修改成功')
          this.$refs.list.loadData()
        } finally {
          row.editLoading = false
        }
      }
    }
  }
</script>

<style scoped>

</style>