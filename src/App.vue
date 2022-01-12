<template>
  <v-app>
    <Main/>
  </v-app>
</template>

<script>
import Main from './components/Main.vue'
import config from './assets/config'

export default {
  name: 'App',

  components: {
    Main
  },

  data: () => ({
    //
  }),

  mounted() {
    document.title = config.document.title;
  },

};
</script>
