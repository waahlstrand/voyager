<template>
  <div id="foot" class="foot">
      <v-container fluid id="foot-container">

          <v-row no-gutters style="flex-wrap: nowrap;"> 
            <v-col align='left' justify='left' cols="2">
                <div id='contacts' class='contacts'>
                    <b>CONTACT US:</b><br>
                    Professor Johan Ling <br>
                    <a href="mailto:johan.ling@gu.se">johan.ling@gu.se</a><br>
                    Centre for Digital Humanities<br> 
                    <a href="mailto:cdh@lir.gu.se">cdh@lir.gu.se</a>        
                </div>
            </v-col>

            <v-col align="right" justify="center" cols="3">
                <img height="100px" src="/assets/images/shfa_logo.png">
            </v-col>
            <v-col align="right" justify="center" cols="3">
                <img height='90px' src="/assets/images/RJ_logo_white.png">
            </v-col>
            <v-spacer></v-spacer>
            <v-col align="right" justify="right" class="flex-grow-1 flex-shrink-0" cols="4">
                <CdhLogo />
            </v-col>
          </v-row>

    </v-container>
  </div>
</template>

<script>
import CdhLogo from "./GUITemplate/vue/CdhLogo.vue";

export default {
  name: "Footer",
  components: { CdhLogo },
};
</script>

<style>
.contacts {
    font-size: 15px;
}

a:link {
    color: #E66E89 !important;
}

#foot-container {
    margin-left: 0;
    margin-right: 0;
}

.foot {
  background-color: rgb(65, 65, 65);
  color: white;
  margin-top: 150px;
  padding: 20px 65px 30px;
  height: auto !important;
  /* min-height: 120px; */
  padding-left: 1.5rem !important;
}

.foot .cdh-logo {
  float: right;
}

@media screen and (max-width: 600px) {
  .foot .cdh-logo {
    display: none;
  }
}
</style>
