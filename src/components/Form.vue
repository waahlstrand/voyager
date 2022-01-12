<template>
  <v-form ref="form" v-model="valid" lazy-validation>
    <v-container>
      <v-row>
        <v-col>
          <v-card color="#F2EFE9" class="my-3">
            <v-card-title>{{ header.title }}</v-card-title>
            <v-card-subtitle>{{ header.subtitle }}</v-card-subtitle>
            <v-card-text>{{ header.blurb }}</v-card-text>
            <v-card-actions>
              <v-dialog
                v-model="instructionsDialog"
                scrollable
                max-width="800px"
              >
                <template v-slot:activator="{ on }">
                  <v-btn
                    v-on="on"
                    text
                    color="#E66E89"
                    @click="instructionsDialog = true"
                  >
                    Instructions
                  </v-btn>
                </template>
                <v-card>
                  <v-card-text>
                    <v-card-title>{{ instructions.title }}</v-card-title>
                    <v-card-subtitle
                      ><h3 class="pt-2">
                        {{ instructions.subtitlePurpose }}
                      </h3></v-card-subtitle
                    >
                    <span v-html="instructions.textPurpose"></span>
                    <v-card-subtitle
                      ><h3 class="pt-2">
                        {{ instructions.subtitleInstructions }}
                      </h3></v-card-subtitle
                    >
                    <div
                      v-for="step in instructions.steps"
                      v-bind:key="step.id"
                      class="image-text"
                    >
                      <div class="image-text">
                        <img :src="step.image" align="left" width="300px" />
                      </div>
                      <div class="image-text__text">
                        <span v-html="step.text"></span>
                      </div>
                    </div>
                  </v-card-text>
                  <v-card-actions>
                    <v-btn text @click="instructionsDialog = false">
                      Close
                    </v-btn>
                  </v-card-actions>
                </v-card>
              </v-dialog>

              <v-dialog v-model="aboutDialog" max-width="900px">
                <template v-slot:activator="{ on }">
                  <v-btn
                    v-on="on"
                    text
                    color="#E66E89"
                    @click="aboutDialog = true"
                  >
                    About
                  </v-btn>
                </template>
                <v-card>
                  <v-card-title> {{ about.title }} </v-card-title>
                  <v-card-text>
                    <span v-html="about.text"></span>
                  </v-card-text>
                  <v-card-actions>
                    <v-btn text @click="aboutDialog = false"> Close </v-btn>
                  </v-card-actions>
                </v-card>
              </v-dialog>
            </v-card-actions>
          </v-card>
          <v-card color="#FFFCF5">
            <v-card-title>Settings</v-card-title>

            <v-window v-model="step">
              <v-window-item :value="1">
                <v-dialog
                  ref="dialog"
                  v-model="form.modal"
                  :return-value.sync="form.dates"
                  width="290px"
                >
                  <template v-slot:activator="{ on, attrs }">
                    <v-text-field
                      ref="datesField"
                      v-model="dateRangeText"
                      label="Select a date range:"
                      :rules="rules.dates"
                      readonly
                      v-bind="attrs"
                      v-on="on"
                      required
                      outlined
                      class="px-8 pt-2"
                    ></v-text-field>
                  </template>
                  <v-date-picker v-model="form.params.dates" range scrollable>
                    <v-spacer></v-spacer>
                    <v-btn text color="primary" @click="form.modal = false">
                      Cancel
                    </v-btn>
                    <v-btn
                      text
                      color="primary"
                      @click="$refs.dialog.save(form.params.dates)"
                    >
                      OK
                    </v-btn>
                  </v-date-picker>
                </v-dialog>

                <v-select
                  v-model="form.params.propulsionType"
                  :items="propulsionTypes"
                  :rules="rules.propulsionTypes"
                  label="Propulsion type"
                  outlined
                  required
                  class="px-8"
                  @change="fetchVesselTypes"
                ></v-select>

                <v-select
                  v-model="form.params.vesselType"
                  :items="vesselTypes"
                  :rules="rules.vesselTypes"
                  label="Vessel type"
                  outlined
                  required
                  class="px-8"
                ></v-select>

                <v-text-field
                  v-model="form.params.paddlingSpeed"
                  :rules="isPaddling ? rules.paddlingSpeed : []"
                  label="Paddling speed"
                  type="number"
                  suffix="m/s"
                  outlined
                  :disabled="!isPaddling"
                  class="px-8"
                ></v-text-field>
              </v-window-item>

              <v-window-item :value="2">
                <v-text-field
                  v-model="form.params.launchInterval"
                  :rules="rules.launchInterval"
                  label="Launch interval"
                  type="number"
                  suffix="days"
                  outlined
                  required
                  class="px-8 pt-2"
                ></v-text-field>

                <v-text-field
                  v-model="form.params.journeyLength"
                  :rules="rules.journeyLength"
                  label="Max journey length"
                  type="number"
                  suffix="days"
                  outlined
                  required
                  class="px-8"
                ></v-text-field>

                <v-text-field
                  v-model="form.params.timestep"
                  :rules="rules.timestep"
                  label="Timestep"
                  type="number"
                  suffix="hours"
                  outlined
                  required
                  class="px-8"
                ></v-text-field>
              </v-window-item>
            </v-window>

            <v-card-actions>
              <v-btn
                v-show="step != 1"
                :disabled="step === 1"
                text
                @click="step--"
              >
                Back
              </v-btn>
              <v-spacer></v-spacer>
              <v-btn
                text
                v-show="step != 2"
                :disabled="step === 2"
                color="teal accent-4"
                @click="step++"
              >
                Advanced
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12" md="8">
          <v-card-actions>
            <v-btn text @click="clearForm"> Clear form</v-btn>
            <v-spacer></v-spacer>
            <v-btn text color="primary" @click="submit"> Run </v-btn>
          </v-card-actions>
        </v-col>
      </v-row>
    </v-container>
  </v-form>
</template>

<script>
import config from "../assets/config";
import rules from "../assets/rules";
import vesselsAPI from "./api/vessels.api";

export default {
  data() {
    // A default form with data from the store
    const defaultForm = Object.freeze({
      params: {
        dates: this.$store.state.params.dates,
        launchInterval: this.$store.state.params.launchInterval,
        journeyLength: this.$store.state.params.journeyLength,
        timestep: this.$store.state.params.timestep / 3600,
        propulsionType: this.$store.state.params.propulsionType,
        vesselType: this.$store.state.params.vesselType,
        paddlingSpeed: this.$store.state.params.paddlingSpeed,
      },
      modal: false,
    });

    return {
      form: Object.assign({}, defaultForm),

      // Rules from config
      rules: rules.rules,
      propulsionTypes: ["sailing", "paddling", "drifting"],
      vesselTypes: [],
      valid: false,
      defaultForm,

      // Controls the advanced settings tab
      step: 1,

      instructionsDialog: false,
      aboutDialog: false,

      // Text from the config
      about: config.about,
      instructions: config.instructions,
      header: config.header,
    };
  },

  computed: {
    start_date() {
      if (this.form.dates.length === 2) {
        return this.form.dates[0];
      } else {
        return undefined;
      }
    },

    end_date() {
      if (this.form.dates.length === 2) {
        return this.form.dates[1];
      } else {
        return undefined;
      }
    },

    isPaddling() {
      return this.form.params.propulsionType === "paddling";
    },

    dateRangeText() {
      if (this.form.params.dates) {
        return this.form.params.dates.join(" ~ ");
      } else {
        return undefined;
      }
    },
  },

  mounted: function () {
    this.fetchVesselTypes();
  },

  methods: {
    clearForm() {
      this.form = Object.assign({}, this.defaultForm);
      this.$refs.form.reset();
    },

    submit() {
      // TODO: Call the backend and get data
      if (!this.valid) {
        this.$refs.form.resetValidation();
      }

      this.valid = this.$refs.form.validate();

      if (this.valid) {
        const SECONDS_PER_HOUR = 3600;

        const { timestep, ...ps } = this.form.params;

        this.update({ timestep: timestep * SECONDS_PER_HOUR, ps });
        this.$root.$emit("form", this.$store.state.params);
      }
    },

    update(params) {
      for (let key in params) {
        this.$store.commit("updateState", {
          which: key,
          value: params[key],
        });
      }
    },

    fetchVesselTypes() {
      vesselsAPI
        .get({ mode: this.form.params.propulsionType })
        .then((response) => {
          this.vesselTypes = response.map((x) => {
            return { text: x.name, value: x.id };
          });
        });
    },
  },
};
</script>

<style>
.v-card--reveal {
  bottom: 0;
  opacity: 1 !important;
  position: absolute;
  width: 100%;
  height: 100%;
}

.image-text {
  display: flex;
  align-items: center;
}
.image-text__image {
  flex: 0 0 auto;
  padding: 16px;
}
.image-text__image img {
  display: block;
}
.image-text__text {
  flex: 1 1 auto;
  padding: 1em;
}
</style>