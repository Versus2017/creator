<template>
  <div @click="onClick">
    <div  class="qr-container">
      <qrcode :value="value" :options="{ size: 60 }"></qrcode>
    </div>
    <BaseModal v-model="modalVisible"
               :title="title"
               :show-ok-button="false">
      <div class="qr-container">
        <qrcode :value="qrUrl" :options="{ size: 300 }"></qrcode>
      </div>
    </BaseModal>
  </div>
</template>

<script>
  import BaseModal from '../modal/base-modal'

  export default {
    name: 'QRCodeCol',

    components: {
      BaseModal
    },

    props: {
      value: {
        type: String
      },
      title: {
        type: String
      },
      remoteUrl: {
        type: String
      }
    },

    data () {
      return {
        modalVisible: false,
        qrUrl: this.value
      }
    },

    methods: {
      async onClick () {
        if (this.remoteUrl) {
          let resp = await this.$http.get(this.remoteUrl)
          this.qrUrl = resp.qr_url
        }
        this.modalVisible = true
      }
    }
  }
</script>

<style lang="less" scoped>
  .qr-container {
    display: flex;
    align-items: center;
    justify-content: center;

    padding: 5px;
  }
</style>