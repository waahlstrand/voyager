// src/plugins/vuetify.js

import Vue from 'vue'
import Vuetify from 'vuetify'
import 'vuetify/dist/vuetify.min.css'
import colors from 'vuetify/lib/util/colors'

Vue.use(Vuetify)

const opts = {
    theme: {
        themes: {
          light: {
            primary: colors.teal.accent4,
            // secondary: colors.teal,
            // anchor: '#8c9eff',
          },
        },
      },
}

export default new Vuetify(opts)
