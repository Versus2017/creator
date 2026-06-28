<style lang="less" scoped>
  @import '../../styles/common.less';

  .search-input {
    .ivu-btn {
      padding: 6px 10px;
    }
  }
</style>

<template>
  <Input v-model="currentValue"
         :style="`width:${width}px`"
         class="search-input"
         :class="{'pull-right': placement === 'right', 'pull-left': placement === 'left'}"
         :placeholder="placeholder"
         :clearable="!!currentValue"
         ref="searchInput"
         @on-change="onSearch" @on-enter="onSearch">
    <Button slot="prepend" icon="ios-search"
            @click="$refs.searchInput.focus()"></Button>
  </Input>
</template>

<script>
  import _ from 'lodash'

  export default {
    name: 'SearchInput',

    props: {
      placeholder: {
        type: String,
        default: '请输入搜索关键字',
      },
      placement: {
        type: String,
        default: 'left',
      },
      value: String,
      width: Number
    },

    data () {
      return {
        currentValue: this.value,
      }
    },

    watch: {
      value (val) {
        this.currentValue = val
      },
    },

    methods: {
      onSearch: _.debounce(
        function () {
          this.$emit('input', this.currentValue)
          this.$emit('on-search', this.currentValue)
        }, 500),
    },
  }
</script>

