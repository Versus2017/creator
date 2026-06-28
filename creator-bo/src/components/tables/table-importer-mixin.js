import InvalidCol from './invalid-col'

export const TableImporterMixin = {
  components: {
    InvalidCol
  },

  methods: {
    renderInvalidCell (h, params) {
      if (params.row.errors[params.column.key]) {
        return h(InvalidCol, {
          props: {
            content: params.row[params.column.key],
            error: params.row.errors[params.column.key]
          }
        })
      } else {
        return h('span', {}, params.row[params.column.key])
      }
    },

    composeInvalidData (invalidDatas) {
      let result = invalidDatas.map(row => {
        let cellClasses = {}
        for (let col in row.errors) {
          cellClasses[col] = row.errors[col] ? 'invalid-cell' : ''
        }
        return Object.assign({}, row, {cellClassName: cellClasses})
      })
      return result
    }
  }
}
