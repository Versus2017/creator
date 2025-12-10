<template>
  <div>
    <base-table ref="list"
           :columns="columns"
           :resourcePath="path"
           exporterPrefix="BOUsers">
      <Button v-if="hasPermission('bo_users_manage')" class="create-btn" type="primary" slot="header-buttons" @click="createUser">创建用户</Button>
    </base-table>
    <bo-user-editor v-model="visible" :user="currentUser" :role-options="roleOptions" @input="val => visible = val" @success="onSuccess"></bo-user-editor>
  </div>
</template>

<script>
  import ActionsCol from '../../components/tables/actions-col'
  import BaseTable from '../../components/tables/base-table'
  import StatusCol from '../../components/tables/status-col'
  import QRCodeCol from '../../components/tables/qr-code-col'
  import BoUserEditor from './bo-user-editor'
  import { getFilterValue } from '../../libs/util'

  export default {
    name: 'BOUserList',

    components: {
      BoUserEditor,
      StatusCol,
      BaseTable
    },

    data () {
      return {
        path: '/admin/users',
        visible: false,
        currentUser: null,
        roleOptions: [],
        actionColWidth: 0
      }
    },

    computed: {

      columns () {
        return [
          {
            title: '操作',
            key: 'actions',
            width: this.actionColWidth,
            toExport: false,
            requiredPerms: ['bo_users_manage', 'bo_users_wechat_bind_manage'],
            render: (h, {row}) => {
              let actions = []
              if (this.hasPermission('bo_users_manage')) {
                actions.push(h('Button', {
                  props: {type: 'primary'},
                  on: {click: ()=> this.editUser(row)}
                }, '编辑'))
              }
              if (this.hasPermission('bo_users_wechat_bind_manage') && row.bound_wechat) {
                actions.push(h('Button', {
                  props: {type: 'warning'},
                  on: {click: ()=> this.unbindWechat(row)}
                }, '解绑'))
              }
              return h(ActionsCol, {
                on: {
                  actionWidthChanged: (width) => {
                    if (width > this.actionWidth) {
                      this.actionWidth = width
                    }
                  }
                }
              }, actions)
            }
          }, {
            title: '用户二维码',
            key: 'qr_code',
            width: 100,
            toExport: false,
            show: this.hasPermission('bo_users_wechat_bind_manage'),
            render: (h, { row }) => {
              return h(QRCodeCol, {
                props: {
                  value: row.bind_url,
                  remoteUrl: `/admin/users/${row.id}/bind_wechat_url`,
                  title: '用户二维码（有效期 5 分钟）'
                }
              })
            }
          }, {
            title: '账户',
            key: 'username',
            minWidth: 130
          }, {
            title: '用户昵称',
            key: 'nickname',
            minWidth: 130
          }, {
            title: '手机号码',
            key: 'mobile',
            minWidth: 130
          }, {
            title: '角色',
            key: 'role',
            minWidth: 130,
            filters: this.roleOptions,
            filterMultiple: false,
            filterRemote: (values) => {
              this.$refs.list.setParams({role_id: getFilterValue(values)})
            },
            format: (row) => row.role ? row.role.name : '-'
          }, {
            title: '微信账户',
            key: 'bound_wechat',
            format: (row) => row.bound_wechat ? '已绑定' : '未绑定',
            width: 120,
            filters: [
              {
                label: '已绑定',
                value: 1
              }, {
                label: '未绑定',
                value: 0
              }
            ],
            filterMultiple: false,
            filterRemote: (values) => {
              this.$refs.list.setParams({'bound_wechat': getFilterValue(values)})
            }
          }, {
            title: '状态',
            key: 'disabled_at',
            requiredPerms: ['bo_users_manage'],
            filterParam: 'active',
            width: 114,
            filters: [
              {
                label: '启用',
                value: 1
              }, {
                label: '禁用',
                value: 0
              }
            ],
            filterMultiple: false,
            filterRemote: (values) => {
              this.$refs.list.setParams({active: getFilterValue(values)})
            },
            render: (h, {row}) => {
              return h(StatusCol, {
                props: {
                  status: row.active,
                  deactivateText: '确定要禁用这个用户吗?',
                  activateText: '确定要启用这个用户吗?',
                  changing: row.changing
                },
                on: {
                  'on-ok': () => {
                    this.updateUserStatus(row)
                  }
                }
              })
            }
          }
        ]
      }
    },

    methods: {
      createUser () {
        this.currentUser = null
        this.visible = true
      },

      editUser (user) {
        this.currentUser = user
        this.visible = true
      },

      unbindWechat (user) {
        this.$Modal.confirm({
          title: '解绑微信',
          content: `您确定要解除用户${user.nickname || user.username}的微信绑定关系吗？`,
          onOk: async () => {
            await this.$http.delete(`/admin/users/${user.id}/wechat_user`)
            this.$refs.list.loadData()
          }
        })
      },

      async updateUserStatus (user) {
        if (user.changing) {
          return
        }
        user.changing = true
        try {
          let mode = user.active ? 'disable' : 'enable'
          await this.$http.post(`${this.path}/${user.id}/${mode}`)
          this.$refs.list.loadData()
        } finally {
          user.changing = false
        }
      },

      async loadRoleOptions () {
        let resp = await this.$http.get('/admin/roles')
        this.roleOptions = resp.rows.map(option => {
          return {
            label: option.name,
            value: option.id
          }
        })
      },

      onSuccess () {
        this.visible = false
        this.$refs.list.loadData()
      }
    },

    mounted() {
      if (this.hasPermission('bo_users_manage')) {
        this.loadRoleOptions()
      }
    }
  }
</script>

<style lang="less" scoped>
  .create-btn {
    margin-left: 3px;
  }
</style>