<style lang="less" scoped>
  @import '../../styles/common.less';

  .invalid-col-icon {
    margin-right: 4px;
  }

  .error-hint {
    white-space: normal;
  }
</style>

<template>
  <Tooltip :delay="200" transfer>
    <Icon type="ios-information-circle" color="#ec5926" size="15" class="invalid-col-icon"/>
    <span :style="errorStyle">{{ content }}</span>
    <div slot="content" class="error-hint">
      <p v-for="err in error">{{ err }}</p>
    </div>
  </Tooltip>
</template>

<script>
  export default {
    name: 'invalid-col',

    props: {
      content: [String, Number],
      error: Array,
      errorStyle: Object,
    }
  }
</script>
