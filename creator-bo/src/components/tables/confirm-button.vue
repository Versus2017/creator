<style scoped lang="less">
  .action {
    margin: 0 5px 0 0;
  }
</style>

<template>
  <Poptip confirm :title="confirmTitle" transfer @on-ok="handleOk"
          placement="top" class="action">
    <Button :type="type" :loading="loading" :disabled="disabled">
      {{ label }}
    </Button>
  </Poptip>
</template>

<script>
  export default {
    props: {
      label: String,
      type: {
        type: String,
        default: 'primary',
      },
      loading: {
        type: Boolean,
        default: false,
      },
      disabled: {
        type: Boolean,
        default: false,
      }
    },

    computed: {
      confirmTitle () {
        return `您确定要${this.label}吗?`
      },
    },

    methods: {
      handleOk () {
        this.$emit('on-ok')
      },
    },
  }
</script>
