<template>
  <Modal ref="modal" class="dtool-modal" v-model="visible" v-bind="$props" @on-cancel="cancel">
    <slot name="close" slot="close"></slot>
    <slot name="header" slot="header"></slot>
    <slot></slot>
    <div slot="footer">
      <div v-if="!hideFooter">
        <i-button type="text" size="large" @click.native="cancel">{{ cancelText }}</i-button>
        <i-button v-if="showOkButton" type="primary" size="large" :loading="buttonLoading" @click.native="ok">{{ okText }}</i-button>
      </div>
    </div>
  </Modal>
</template>

<script>
  export default {
    name: 'BaseModal',

    props: {
      value: {
        type: Boolean,
        default: false
      },
      closable: {
        type: Boolean,
        default: true
      },
      maskClosable: {
        type: Boolean,
        default: true
      },
      title: {
        type: String
      },
      width: {
        type: [Number, String],
        default: 520
      },
      showOkButton: {
        type: Boolean,
        default: true
      },
      okText: {
        type: String,
        default: '确定'
      },
      cancelText: {
        type: String,
        default: '取消'
      },
      loading: {
        type: Boolean,
        default: false
      },
      buttonLoading: {
        type: Boolean,
        default: false
      },
      styles: {
        type: Object
      },
      className: {
        type: String
      },
      // for instance
      footerHide: {
        type: Boolean,
        default: false
      },
      scrollable: {
        type: Boolean,
        default: false
      },
      transitionNames: {
        type: Array,
        default () {
          return ['ease', 'fade'];
        }
      },
      transfer: {
        type: Boolean,
        default: true
      },
      hideFooter: {
        type: Boolean,
        default: false,
      }
    },

    data () {
      return {
        visible: this.value
      }
    },

    watch: {
      value (val) {
        this.visible = val
      }
    },

    methods: {
      ok () {
        this.$emit('on-ok')
      },

      cancel () {
        this.$emit('input', false)
        this.$emit('on-cancel')
        this.visible = false
      }
    }
  }
</script>

<style lang="less">

  .dtool-modal {
    .ivu-modal-wrap {
      display: flex;
      align-items: center;
      justify-content: center;

      .ivu-modal {
        top: 0;
        margin: 0;
      }
    }
  }
  .ivu-modal-body {
    max-height: 70vh;
    overflow-y: scroll;
  }

</style>
