<template>
  <Poptip
      confirm
      :title="confirmText"
      placement="top-start"
      @on-ok="onOk">
      <Button :type="buttonType">{{ buttonTitle }}</Button>
  </Poptip>
</template>

<script>
  export default {
    name: 'PoptipBtn',

    props: {
      buttonType: {
        type: String,
        default: 'warning'
      },

      buttonTitle: {
        type: String,
        default: '确定'
      },

      confirmText: {
        type: String,
        default: '您确定要执行该操作吗？'
      }
    },

    methods: {
      onOk () {
        this.$emit('ok')
      }
    }
  }
</script>

<style scoped>

</style>