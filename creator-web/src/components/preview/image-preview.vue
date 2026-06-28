<template>
  <base-modal v-model="value" :mask-closable="true"
              @on-close="$emit('input', false)"
              :custom-content="true">
    <div class="preview">
      <img :src="url" alt="">
    </div>
  </base-modal>
</template>

<script>
  import BaseModal from '_c/preview/custom-modal.vue'
  export default {
    name: 'image-preview',
    components: { BaseModal },

    props: {
      url: {
        type: String,
        default: ''
      },

      value: {
        type: Boolean,
        default: false,
      }
    },

  }
</script>

<style scoped lang="less">
  .preview {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;

    img {
      width: auto;
      height: 100%;
      flex-shrink: 0;
    }
  }

  @media screen and (max-width: 600px) {
    .preview {
      width: 80%;
      height: auto;
    }
  }

</style>