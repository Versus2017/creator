<template>
  <div>
    <base-table ref="list"
           :columns="columns"
           :resourcePath="path"
           exporterPrefix="BORoles">
      <Button v-if="hasPermission('bo_roles_manage')" class="create-btn" type="primary" slot="header-buttons" @click="createRole">创建角色</Button>
    </base-table>
  </div>
</template>

<script>
  import BaseTable from '../../components/tables/base-table'
  import StatusCol from '../../components/tables/status-col'
  export default {
    name: 'RoleList',

    components: {
      StatusCol,
      BaseTable
    },

    data () {
      return {
        path: '/admin/roles'
      }
    },

    computed: {
      columns () {
        return [
          {
            title: '操作',
            key: 'actions',
            width: 96,
            toExport: false,
            requiredPerms: ['bo_roles_manage'],
            render: (h, {row}) => {
              return h('Button', {
                props: {type: 'primary'},
                on: {click: ()=> this.$router.push(`/user/roles/${row.id}/edit`)}
              }, '编辑')
            }
          }, {
            title: '角色名称',
            key: 'name'
          }, {
            title: '角色描述',
            key: 'description'
          }, {
            title: '状态',
            key: 'disabled_at',
            requiredPerms: ['bo_roles_manage'],
            width: 114,
            render: (h, {row}) => {
              return h(StatusCol, {
                props: {
                  status: !row.disabled_at,
                  deactivateText: '如果禁用，该角色对应用户将被禁用',
                  activateText: '如果启用，该角色对应的被禁用的用户需手动启用',
                  changing: row.changing
                },
                on: {
                  'on-ok': () => {
                    this.updateRoleStatus(row)
                  }
                }
              })
            }
          }
        ]
      }
    },

    methods: {
      createRole () {
        this.$router.push('/user/roles/create')
      },

      async updateRoleStatus (role) {
        if (role.changing) {
          return
        }
        role.changing = true
        try {
          let mode = role.disabled_at ? 'enable' : 'disable'
          await this.$http.post(`${this.path}/${role.id}/${mode}`)
          this.$refs.list.loadData()
        } finally {
          role.changing = false
        }
      },
    },

    mounted () {
    }
  }
</script>

<style lang="less" scoped>
  .create-btn {
    margin-left: 3px;
  }
</style>