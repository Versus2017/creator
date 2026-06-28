<template>
  <div class="wrapper">
    <div class="actions-container" ref="container">
      <slot />
    </div>
  </div>
</template>

<script>
  export default {
    name: 'ActionsCol',

    data () {
      return {
        margin: 18
      }
    },

    mounted () {
      let container = this.$refs.container
      this.$emit('actionWidthChanged', container.offsetWidth + this.margin * 2)
    }
  }
</script>

<style scoped lang="less">
  .wrapper {
  }
  .actions-container {
    display: inline-block;
    white-space: nowrap;

    > * {
      margin-right: 4px;
      display: inline;
    }

    > *:last-child {
      margin-right: 0;
    }
  }
</style>