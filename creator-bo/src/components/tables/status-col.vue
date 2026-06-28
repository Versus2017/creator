<style lang="less" scoped>
  @import '../../styles/common.less';

  .status-btn {
    padding: 0;

    &:focus {
      box-shadow: none;
    }

    &[disabled] {
      .ivu-tag-dot {
        background: #f7f7f7 !important;
      }

      .ivu-tag-text {
        color: #bbbec4;
      }
    }
  }

  .disable-hint {
    white-space: normal;
  }
</style>

<template>
  <div v-if="canManage">
    <Tooltip :delay="200" transfer v-if="disabled">
      <div slot="content" class="disable-hint">
        {{ disabledHint }}
      </div>
      <Button type="text" class="status-btn" disabled>
        <span>
          <div class="ivu-tag ivu-tag-dot ivu-tag-checked">
            <span v-if="showDot" class="ivu-tag-dot-inner" :style="{background: statusColor}"></span>
            <span class="ivu-tag-text">{{ currentStatus }}</span>
          </div>
        </span>
      </Button>
    </Tooltip>
    <Poptip confirm :title="confirmTitle" transfer @on-ok="handleOk" v-else>
      <Button type="text" :loading="changing" class="status-btn"
              :disabled="disabled">
        <span>
          <div class="ivu-tag ivu-tag-dot ivu-tag-checked">
            <span v-if="showDot" class="ivu-tag-dot-inner" :style="{background: statusColor}"></span>
            <span class="ivu-tag-text">{{ currentStatus }}</span>
          </div>
        </span>
      </Button>
    </Poptip>
  </div>
  <div v-else>
    <span class="ivu-tag-text">{{ currentStatus }}</span>
  </div>
</template>

<script>
  export default {
    name: 'StatusCol',

    props: {
      showDot: {
        type: Boolean,
        default: true,
      },
      canManage: {
        // if the col can be accessed by the user due to permission control
        type: Boolean,
        default: true,
      },
      status: {
        type: Boolean,
        default: false,
      },
      changing: {
        type: Boolean,
        default: false,
      },
      disabled: {
        type: Boolean,
        default: false,
      },
      disabledHint: {
        type: String,
        default: '无法操作这条数据',
      },
      activeText: {
        type: String,
        default: '正常',
      },
      inactiveText: {
        type: String,
        default: '停用',
      },
      activateText: {
        type: String,
        default: '您确定要启用这条数据吗?',
      },
      deactivateText: {
        type: String,
        default: '您确定要停用这条数据吗?',
      },
    },

    computed: {
      currentStatus () {
        return this.status ? this.activeText : this.inactiveText
      },

      confirmTitle () {
        return this.status ? this.deactivateText : this.activateText
      },

      statusColor () {
        if (this.disabled) {
          return '#e9eaec'
        }
        return this.status ? 'lightseagreen' : 'orange'
      },
    },

    methods: {
      handleOk () {
        this.$emit('on-ok')
      }
    },
  }
</script>
