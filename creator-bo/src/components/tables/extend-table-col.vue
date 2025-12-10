<template>
  <div>
    <Table :columns="columns" :data="data" border></Table>
  </div>
</template>

<script>
  export default {
    name: 'ExtendTableCol',

    props: {
      columns: {
        type: Array,
        default: () => []
      },

      data: {
        type: Array,
        default: () => []
      }
    },

    data () {
      return {}
    }
  }
</script>

<style scoped>

</style>