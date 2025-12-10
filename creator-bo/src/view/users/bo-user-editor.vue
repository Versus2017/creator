<template>
  <base-modal v-model="visible"
              @input="val => $emit('input', val)"
              :title="title"
              :buttonLoading="loading"
              @on-ok="onOk"
              @on-cancel="onCancel"
              @on-visible-change="onVisibleChange">
    <Form ref="userForm"
          :model="copiedUser"
          :rules="ruleValidate"
          :label-width="120"
          label-position="right">
      <FormItem prop="nickname"
                :error="serverErrors.nickname"
                label="用户昵称">
        <Input v-model="copiedUser.nickname"
               type="text"
               placeholder="请输入用户昵称" />
      </FormItem>
      <FormItem prop="mobile"
                :error="serverErrors.mobile"
                label="手机号码">
        <Input v-model="copiedUser.mobile"
               type="text"
               placeholder="请输入手机号码" />
      </FormItem>
      <FormItem prop="role_id"
                :error="serverErrors.role_id"
                label="用户角色">
        <Select v-model="copiedUser.role_id"
                placeholder="选择角色">
            <Option v-for="option in roleOptions"
                    :value="option.value"
                    :key="option.value">{{ option.label }}</Option>
        </Select>
      </FormItem>
      <FormItem prop="username"
                :error="serverErrors.username"
                label="登入账号">
        <Input v-model="copiedUser.username"
               type="text"
               placeholder="请输入登入账号" />
      </FormItem>
      <FormItem prop="password"
                :error="serverErrors.password"
                label="登入密码">
        <Input v-model="copiedUser.password"
               type="password"
               placeholder="请输入登入账号" />
      </FormItem>
      <FormItem prop="confirm_password"
                :error="serverErrors.confirm_password"
                label="确认密码">
        <Input v-model="copiedUser.confirm_password"
               type="password"
               placeholder="请再次输入密码" />
      </FormItem>
      <FormItem label="启用账户">
        <i-switch size="large" v-model="copiedUser.active">
          <span slot="open">启用</span>
          <span slot="close">禁用</span>
        </i-switch>
      </FormItem>
    </Form>
  </base-modal>
</template>

<script>
  import BaseModal from '../../components/modal/base-modal'
  import { get } from 'lodash'
  import { FormErrorMixin } from '../../mixins/formErrorMixin'

  export default {
    name: 'BoUserEditor',

    mixins: [FormErrorMixin],

    components: {
      BaseModal
    },

    props: {
      value: {
        type: Boolean,
        default: false
      },
      user: {
        type: Object,
        default: null
      },
      roleOptions: {
        type: Array,
        default: () => []
      }
    },

    data () {
      return {
        loading: false,
        visible: this.value,
        copiedUser: this.user ? Object.assign({}, this.user, {role_id: this.getRoleId()}) : {},
        ruleValidate: {
          nickname: [
            {required: true, message: '用户昵称不能为空', trigger: 'blur'}
          ],
          mobile: [
            {required: true, message: '手机号不能为空', trigger: 'blur'}
          ],
          role_id: [
            {required: true, type: 'number', message: '角色不能为空', trigger: 'blur'}
          ],
          username: [
            {required: true, message: '账号不能为空', trigger: 'blur'}
          ],
          password: [
            {required: this.isCreate, message: '登入密码不能为空', trigger: 'blur'}
          ],
          confirm_password: [
            {required: this.isCreate, message: '确认密码不能为空', trigger: 'blur'},
            {validator: this.passwordVerify, trigger: 'blur'}
          ],
        },
        serverErrors: {
          nickname: null,
          mobile: null,
          role_id: null,
          username: null,
          password: null,
          confirm_password: null,
        }
      }
    },

    computed: {
      title () {
        return this.isCreate ? '创建用户' : `编辑用户 ${this.copiedUser.username}`
      },

      isCreate () {
        return !this.user
      },
    },

    methods: {
      getRoleId () {
        return get(this.user, 'role.id')
      },

      passwordVerify (rule, value, callback) {
        if (this.copiedUser.password === value) {
          callback()
        } else {
          callback(new Error('两次输入的密码不一致'))
        }
      },

      onOk () {
        this.$refs.userForm.validate(async (valid) => {
          if (!valid) return
          this.loading = true
          this.clearErrors()
          try {
            this.copiedUser.roles = [this.copiedUser.role]
            if (this.isCreate) {
              let path = '/admin/users'
              await this.$http.post(path, this.copiedUser)
            } else {
              let resp = await this.$http.put(`/admin/users/${this.copiedUser.id}`, this.copiedUser)
              let isEditingSelf = this.$store.getters['user/username'] === this.copiedUser.username
              if (isEditingSelf && resp.success) {
                this.$store.dispatch('user/refreshUser')
              }
            }
            this.$emit('success')
            this.$Message.success('保存成功')
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
        })
      },

      onCancel () {
        this.$refs.userForm.resetFields()
      },

      onVisibleChange (visible) {
        if (!visible) return
      }
    },

    watch: {
      value (val) {
        this.clearErrors()
        this.$refs.userForm.resetFields()
        this.visible = val
        if (!val) return
        // init copiedUser when modal show
        if (this.user !== null) {
          let role = this.getRoleId()
          this.copiedUser = Object.assign({}, this.user, {role_id: role})
        } else {
          this.copiedUser = {}
        }
      }
    },
  }
</script>

<style lang="less" scoped>

</style>