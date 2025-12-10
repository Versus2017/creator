<template>
  <div class="title">{{ title }}</div>
</template>

<script>
import InforCard from '_c/info-card'
import CountTo from '_c/count-to'
import { ChartPie, ChartBar } from '_c/charts'
import { BO_NAME } from '../../../libs/constants'

export default {
  name: 'Home',
  components: {
    InforCard,
    CountTo,
    ChartPie,
    ChartBar,
  },
  data () {
    return {
      title: BO_NAME
    }
  },
  mounted () {
    //
  }
}
</script>

<style lang="less" scoped>
  .title {
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 36px;
  }
</style>
