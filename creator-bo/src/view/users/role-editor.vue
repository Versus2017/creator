<template>
  <div>
    <div class="header">
      <h2>{{ isCreate ? '创建角色' : '编辑角色' }}</h2>
    </div>
    <div class="content">
      <Form ref="createRoleForm" :model="role" label-position="right" :rules="rules">
        <FormItem label="角色名称" prop="name" :label-width="120" required>
          <Input v-model="role.name" placeholder="请输入角色名称" />
        </FormItem>
        <FormItem label="角色描述" prop="description" :label-width="120" required>
          <Input v-model="role.description" placeholder="请输入角色描述" />
        </FormItem>
        <FormItem label="权限配置" :label-width="120" prop="permissions">
          <CheckboxGroup v-model="role.permissions">
            <div v-for="(group, index) in permissionGroups" :key="index">
              <h4 class="subtitle">{{ group.name }}</h4>
              <Row>
                <Col span="6" v-for="p in group.perms" :key="p.value">
                  <Checkbox :label="p.value">{{ p.name }}</Checkbox>
                </Col>
              </Row>
            </div>
          </CheckboxGroup>
        </FormItem>
      </Form>
    </div>
    <div class="footer">
      <ButtonGroup>
        <Button type="default" @click="back">返回列表</Button>
        <Button type="primary" @click="validate" :loading="loading">
          <span v-if="isCreate">创建</span>
          <span v-else>提交</span>
        </Button>
      </ButtonGroup>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'role-editor',

    data () {
      return {
        loading: false,
        roleId: this.$route.params.roleId,
        role: {
          name: null,
          description: null,
          permissions: []
        },
        permissionGroups: [],
        rules: {
          name: [
            {required: true, message: '角色名称不可为空', trigger: 'blur'}
          ],
          description: [
            {required: true, message: '角色描述不可为空', trigger: 'blur'}
          ],
          permissions: [
            {required: true, type: 'array', min: 1, message: '请至少选择一个权限', trigger: 'change'}
          ]
        }
      }
    },

    computed: {
      isCreate () {
        return !this.roleId
      }
    },

    methods: {
      async loadRole () {
        let resp = await this.$http.get(`/admin/roles/${this.roleId}`)
        this.role = resp.role
      },

      async loadPermissions () {
        let resp = await this.$http.get('/admin/permissions')
        this.permissionGroups = resp.groups
      },

      validate () {
        this.$refs.createRoleForm.validate((res) => {
          if (res) {
            this.commit()
          }
        })
      },

      async commit () {
        if (this.loading) {
          return
        }
        let method, path, actionName
        if (this.isCreate) {
          method = this.$http.post
          path = '/admin/roles'
          actionName = '创建'
        } else {
          method = this.$http.put
          path = `/admin/roles/${this.roleId}`
          actionName = '编辑'
        }
        this.loading = true
        try {
          await method(path, this.role)
          this.$Message.success(`${actionName}成功`)
          this.back()
        } finally {
          this.loading = false
        }
      },

      back () {
        this.$router.back()
      }
    },

    async mounted () {
      await this.loadPermissions()
      if (this.roleId) {
        await this.loadRole()
      }
    }
  }
</script>

<style lang="less" scoped>
  .header {
    margin-bottom: 20px;

    h2 {
      text-align: center;
    }
  }

  .subtitle {
    color: steelblue;
  }

  .footer {
    display: flex;
    justify-content: flex-end;
  }
</style>