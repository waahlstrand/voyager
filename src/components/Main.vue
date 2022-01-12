<template>
    <v-main>
      <v-container id="main-container" fluid class="fill-height fill-width">
        <v-row id="content-row" no-gutters>
          <v-col class="sidebar-container" :cols="4">
            <div class='sidebar pa-5'>
              <Form/>
            </div>
          </v-col>
          <v-col :cols="8">
            <Map/>
          </v-col>
        </v-row>
      </v-container>
      <Footer/>
    </v-main>
</template>

<script>
import Form from './Form.vue';
import Map from './Map.vue'
import Footer from './Footer.vue'
export default {
  name: 'Main',

  components: {
    Form,
    Map,
    Footer
  },

  data: () => ({
    trajectories: [],
    vessels: []
  }),

};
</script>

<style>
/* @import './GUITemplate/css/base.css'; */
@import './GUITemplate/css/components.css';
/* @import './GUITemplate/css/style.css'; */
@import './GUITemplate/css/utilities.css';

@import url('https://fonts.googleapis.com/css2?family=Antic+Didone&display=swap');
@import url('https://fonts.googleapis.com/css?family=Barlow+Condensed:100,200&display=swap');
@import url('https://fonts.googleapis.com/css?family=Clicker+Script&display=swap');

.foot {
  margin-top: 0;
  height: 180px;
  background-color: rgb(114, 177, 196);
}

#content-row {
  height: 100%;
  width: 100%;
}

#main-container {
  padding: 0;
}

.v-main {
  height: 100%;
  width: 100%;
}

.sidebar-container {
    background-color: rgb(170,211,223);
    padding: 10px;
}
.map-container {
    width: 70%;
    height: 100%;
}
</style>
