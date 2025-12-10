<template>
  <div>
    <div class="user-avator-dropdown">
      <Dropdown @on-click="handleClick" trigger="click">
        <a href="javascript:void(0)">
          <span>{{ name }}</span>
          <Icon :size="18" type="md-arrow-dropdown"></Icon>
          <Avatar :src="userAvatar" icon="ios-person"/>
        </a>
        <DropdownMenu slot="list">
          <DropdownItem name="changePassword">修改密码</DropdownItem>
          <DropdownItem name="logout" divided>退出登录</DropdownItem>
        </DropdownMenu>
      </Dropdown>
    </div>
    <base-modal v-model="modal.visible"
                :title="modal.title"
                :buttonLoading="loading"
                @on-ok="modal.onOk()"
                @on-cancel="modal.onCancel()">
      <Form
        ref="passwordForm"
        :model="passwordModel"
        :rules="passwordRules"
        label-position="right"
        :label-width="100">
        <FormItem label="当前密码"
                  :required="true"
                  :error="serverErrors.password"
                  prop="password">
          <Input type="password" v-model="passwordModel.password"
                 placeholder="请输入当前密码"/>
        </FormItem>
        <FormItem label="新密码"
                  :required="true"
                  :error="serverErrors.new_password"
                  prop="newPassword">
          <Input type="password" v-model="passwordModel.newPassword"
                 placeholder="至少需要8个字符"/>
        </FormItem>
        <FormItem label="确认密码"
                  :required="true"
                  :error="serverErrors.password_verify"
                  prop="passwordVerify">
          <Input type="password" v-model="passwordModel.passwordVerify"
                 placeholder="请再次输入密码"/>
        </FormItem>
      </Form>
    </base-modal>
  </div>
</template>

<script>
  import './user.less'
  import BaseModal from '@/components/modal/base-modal'
  import { FormErrorMixin } from '../../../../mixins/formErrorMixin'
  import { get } from 'lodash'

  export default {
    name: 'User',

    mixins: [FormErrorMixin],

    components: {
      BaseModal
    },

    computed: {
      name () {
        let username = this.$store.getters['user/username']
        let nickname = this.$store.getters['user/nickname']
        return nickname || username || ''
      }
    },

    data () {
      const validateNewPasswordCheck = (rule, value, callback) => {
        if (!value || value.trim().length === 0) {
          callback(new Error('请再次输入新密码'))
        } else if (value && value.trim().length < 8) {
          callback(new Error('新密码至少8个字符'))
        } else if (value !== this.passwordModel.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      }
      return {
        loggedOut: false,
        loading: false,
        modal: {
          visible: false,
          title: null,
          onOk: () => {
          },
          onCancel: () => {
          }
        },
        passwordModel: {
          password: '',
          newPassword: '',
          passwordVerify: ''
        },
        passwordRules: {
          password: [
            {required: true, message: '请输入当前密码', trigger: 'blur'}
          ],
          newPassword: [
            {required: true, message: '新密码不能为空', trigger: 'blur'}
          ],
          passwordVerify: [
            {required: true, validator: validateNewPasswordCheck, trigger: 'change'}
          ]
        },
        serverErrors: {
          password: null,
          new_password: null,
          password_verify: null,
        }
      }
    },

    props: {
      userAvatar: {
        type: String,
        default: ''
      }
    },

    methods: {
      logout () {
        this.loggedOut = true
        this.$store.dispatch('user/logout', {vue: this, makeRequest: true})
      },

      handleClick (name) {
        switch (name) {
          case 'logout':
            this.logout()
            break
          case 'changePassword':
            this.clearErrors()
            this.$refs.passwordForm.resetFields()
            this.modal = {
              visible: true,
              title: '修改密码',
              onOk: () => {
                this.changePassword()
              },
              onCancel: () => {
                this.modal.visible = false
              }
            }
            break
        }
      },

      changePassword () {
        this.$refs.passwordForm.validate(async (valid) => {
          if (valid) {
            this.loading = true
            this.clearErrors()
            try {
              let resp = await this.$http.put('/admin/users/update_password', {
                password: this.passwordModel.password,
                new_password: this.passwordModel.newPassword,
                password_verify: this.passwordModel.passwordVerify
              })
              if (resp.success) {
                this.$Message.success('修改成功，请重新登入')
                this.modal.visible = false
                this.logout()
              }
            } catch (error) {
              let statusCode = get(error, 'response.status')
              if (statusCode === 400) {
                this.setFormErrors(error)
              } else {
                throw error
              }
            } finally {
              this.loading = false
            }
          }
        })
      },
    },

    mounted () {
      this.$auth.ready(function () {
        if (this.$auth.check()) {
          this.$store.dispatch('user/refreshUser')
        }
      })
    }
  }
</script>
