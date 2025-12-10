<style lang="less" scoped>
  @import '../../styles/common.less';

  .editable-col {
    display: flex;
    align-items: center;
    justify-content: space-between;

    .ivu-form-item {
      margin-bottom: 0;
    }

    .extra-label {
      font-size: 12px;
      color: orangered;
    }
  }
</style>

<template>
  <div class="editable-col">
    <div v-if="canManage && editing">
      <Select v-model="currentValue"
              v-if="isSelect"
              transfer
              @on-change="onChange"
              :style="{width: width}"
              :label-in-value="true"
              :label="currentValue">
        <Option v-for="option of options"
                :value="option.value"
                :key="option.label">
          {{ option.label }}
        </Option>
      </Select>
      <i-switch v-else-if="isSwitch"
                v-model="currentValue"
                @on-change="switchChange">
        <span slot="open">{{ switchOn }}</span>
        <span slot="close">{{ switchOff }}</span>
      </i-switch>
      <Poptip v-else-if="isInput" trigger="focus" transfer
              :content="placeholder">
        <Input :style="{width: width}" v-model="currentValue"
               @on-change="inputChange" />
      </Poptip>
      <image-upload :show-image-on-new-window="true"
                    v-else-if="isUpload"
                    :default-list="fileImgs"
                    @success="onFileUploaded"
                    @delete="onFileRemoved" />
    </div>
    <div v-else>
      <p>
        {{ formatValue(value) }}
      </p>
      <p class="extra-label" v-if="extraLabel">
        {{ this.extraLabel }}
      </p>
    </div>
    <Button v-if="showEditButton" class="edit-btn" type="text" :icon="icon"
            @click="handleClick" />
  </div>
</template>

<script>
  import ISwitch from 'iview/src/components/switch/switch'
  import imageUpload from '_c/media/image-upload.vue'
  import ImageUpload from '_c/media/image-upload.vue'

  const switchType = 'switch'
  const inputType = 'input'
  const selectType = 'select'
  const uploadType = 'upload'

  export default {
    name: 'EditableCol',

    components: { ImageUpload, ISwitch },

    props: {
      value: [String, Number, Boolean],
      editing: {
        type: Boolean,
        default: false
      },
      inputType: {
        type: String,
        default: inputType
      },
      format: {
        type: Function,
        default: (value) => {
          return value
        }
      },
      placeholder: {
        type: String,
        default: '请输入'
      },
      options: {
        type: Array,
        default: () => {
        }
      },
      extraLabel: {
        type: String,
        default: null
      },
      width: {
        type: String,
        default: '100px'
      },
      canManage: {
        type: Boolean,
        default: true
      },
      showEditButton: {
        type: Boolean,
        default: false
      },
      switchOn: {
        type: String,
        default: 'ON'
      },
      switchOff: {
        type: String,
        default: 'OFF'
      }
    },

    data () {
      return {
        currentValue: this.isSwitch ? !!this.value : this.value
      }
    },

    computed: {
      icon () {
        return this.editing ? 'checkmark' : 'edit'
      },
      isSelect () {
        return this.inputType === selectType
      },
      isInput () {
        return this.inputType === inputType
      },
      isSwitch () {
        return this.inputType === switchType
      },
      isUpload () {
        return this.inputType === uploadType
      },

      fileImgs () {
        if (this.value) {
          return [{
            url: this.value
          }]
        }
        return []
      }
    },

    watch: {
      value (val) {
        this.currentValue = val
      }
    },

    methods: {
      formatValue () {
        if (this.inputType === switchType) {
          return this.value ? this.switchOn : this.switchOff
        }
        if (!(this.value === null || this.value === undefined) && this.format) {
          return this.format(this.value)
        }
        return this.value
      },

      onChange (option) {
        this.$emit('selected', option)
      },

      inputChange (event) {
        if (event && event.target) {
          this.$emit('input', event.target.value)
        }
      },

      switchChange (value) {
        this.$emit('switchChanged', value)
      },

      handleClick () {
        this.$emit('click', this.currentValue)
      },

      onFileUploaded  (file) {
        this.currentValue = file.url
        this.$emit('onUploaded', this.currentValue)
      },

      onFileRemoved (file) {
        this.currentValue = ''
      }
    }
  }
</script>
