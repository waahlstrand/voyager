<template>
  <div ref="map-root" style="position: relative; width: 100%; height: 100%">
    <div ref="tip" class="tip">{{ tip }}</div>
    <div ref="tooltip" class="tooltip"></div>
    <v-overlay :value="overlay" :absolute="true">
      <v-progress-circular
        v-if="!error"
        :rotate="-90"
        :size="100"
        :width="15"
        :value="progress"
        color="white"
        >{{ Math.ceil(progress) }}</v-progress-circular
      >
      <div v-else-if="error">{{ error }}</div>
    </v-overlay>
  </div>
</template>

<script>
import Map from "ol/Map";
import View from "ol/View";

import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import TileLayer from "ol/layer/Tile";
import OSM from "ol/source/OSM";
import GeoJSON from "ol/format/GeoJSON";
import Overlay from "ol/Overlay";

import * as control from "ol/control";
import ContextMenu from "ol-contextmenu";

import Style from "ol/style/Style";
import Icon from "ol/style/Icon";
import Stroke from "ol/style/Stroke";
import Fill from "ol/style/Fill";
import Text from "ol/style/Text";

import Point from "ol/geom/Point";
import Feature from "ol/Feature";
import * as proj from "ol/proj";

import "ol-contextmenu/dist/ol-contextmenu.css";
import "ol/ol.css";

import trajectoryAPI from "./api/trajectory.api";
import config from "../assets/config";

export default {
  name: "Map",
  components: {},
  props: {
    features: Array,
  },

  data: () => ({
    overlay: false,
    progress: 0,
    icons: config.icons,
    projection: config.projection,
    tip: config.tip,
    selected: null,
    error: null
  }),

  computed: {
    contextMenuItems() {
      return [
        {
          text: "Add a departure point",
          classname: "departure-marker",
          icon: this.icons.pin,
          callback: this.addDepartureMarker,
        },

        {
          text: "Add a destination point",
          classname: "destination-marker",
          icon: this.icons.target,
          callback: this.addDestinationMarker,
        },

        {
          text: "Clear all markers",
          icon: this.icons.clear,
          callback: this.clearMarkers,
        },

        {
          text: "Remove all trajectories",
          icon: this.icons.clear,
          callback: this.removeAllTrajectories,
        },
        "-",
      ];
    },

    removeMarkerItem() {
      return {
        text: "Remove this marker",
        classname: "marker",
        icon: this.icons.clear,
        callback: this.removeMarker,
      };
    },

    tileLayers() {
      return [
        new TileLayer({
          source: new OSM(), // tiles are served by OpenStreetMap
        }),
      ];
    },

    vectorLayer() {
      return new VectorLayer({
        source: new VectorSource(),
      });
    },

    map() {
      const attribution = new control.Attribution({
        collapsible: false,
      });

      const contextMenuControl = new ContextMenu({
        width: 'auto',
        defaultItems: true,
        items: this.contextMenuItems,
      });

      var tipControl = new control.Control({element: this.$refs.tip});

      
      const overlay = new Overlay({
        element: this.$refs.tooltip,
        offset: [10, 0],
        positioning: "bottom-left",
      });

      const map = new Map({
        controls: control.defaults().extend([attribution, contextMenuControl, tipControl]),
        target: this.$refs["map-root"],
        layers: [...this.tileLayers, this.vectorLayer],
        overlays: [overlay],
        logo: false,
        view: new View({
          zoom: this.projection.zoom,
          center: proj.transform(
            this.projection.center,
            this.projection.to,
            this.projection.from
          ),
          constrainResolution: true,
        }),
      });


      // Callbacks
      map.on("pointermove", (e) =>
        this.onPointerMove(e, map, overlay)
      );

      map.on("moveend", this.updateBbox);

      contextMenuControl.on("open", (e) => 
        this.onContextMenuOpen(e, contextMenuControl)
      );


      return map;
    },
  },

  mounted() {
    // Map must be used to actually appear
    this.map;

    // Creates responsiveness on submitting the form
    this.$root.$on("form", (params) => {
      this.computeTrajectories(params);
    });
  },

  methods: {
    onContextMenuOpen(e, contextMenuControl) {

        const feature = this.map.forEachFeatureAtPixel(e.pixel, f => f);

        if (feature && feature.get("type") === "removable") {
          contextMenuControl.clear();
          this.removeMarkerItem.data = { marker: feature };
          contextMenuControl.push(this.removeMarkerItem);
        } else {
          contextMenuControl.clear();
          contextMenuControl.extend(this.contextMenuItems);
          contextMenuControl.extend(contextMenuControl.getDefaultItems());
        }

    },

    onPointerMove(e, map, overlay) {
      const selectStyle = new Style({
        fill: new Fill({
          color: "#eeeeee",
        }),
        stroke: new Stroke({
          color: "rgba(255, 255, 255, 0.7)",
          width: 5,
        }),
      });

      // When dragging the map, the pointer can move faster than the map.
      // Prevent it from triggering other tooltips in the meantime.

      if (e.dragging) {
        return;
      }

      if (this.selected !== null) {
        this.selected.setStyle(undefined);
        this.selected = null;
      }

      const feature = map.forEachFeatureAtPixel(e.pixel, f => f)

      this.$refs.tooltip.style.display = feature ? "" : "none";
    
      if (feature) {
        if (feature.getId() === 'trajectory') {
          this.selected = feature;

          // selectStyle.getFill().setColor(f.get("COLOR") || "#eeeeee");
          feature.setStyle(selectStyle);


          overlay.setPosition(e.coordinate);
          this.$refs.tooltip.innerHTML = `
                                  <b>Start</b>: ${feature.get("start_date")}<br>
                                  <b>Stop</b>: ${feature.get("stop_date")}<br>
                                  <b>Distance</b>: ${feature
                                    .get("distance")
                                    .toFixed(0)} km <br>
                                  <b>Mean speed</b>: ${feature
                                    .get("mean_speed")
                                    .toFixed(2)} m/s
                                  `;
        }
      }

    },

    updateBbox() {
      const extent = proj.transformExtent(
        this.map.getView().calculateExtent(this.map.getSize()),
        this.projection.from,
        this.projection.to
      );

      this.$store.commit("updateState", {
        which: "bbox",
        value: extent,
      });
    },

    arraysMatch(arr1, arr2) {
      // Check if the arrays are the same length
      if (arr1.length !== arr2.length) return false;

      // Check if all items exist and are in the same order
      for (var i = 0; i < arr1.length; i++) {
        if (arr1[i] !== arr2[i]) return false;
      }

      // Otherwise, return true
      return true;
    },

    clearMarkers() {
      // Clear in vector layer
      this.vectorLayer.getSource().clear();

      // Clear in store
      this.removeDeparturePoints();
      this.removeDestinationPoint();
    },

    removeMarker(obj) {
      // Check which point to remove

      // If a single departure point, we must remove it by coordinate
      if (obj.data.marker.get("name") === "departure-point") {
        this.removeSingleDeparturePoint(
          this.coordinatesFromFeature(obj.data.marker)
        );

        // Only one destination point is allowed, we can safely remove them all
      } else if (obj.data.marker.get("name") === "destination-point") {
        this.removeDestinationPoint();
      }

      // Remove from layer
      this.vectorLayer.getSource().removeFeature(obj.data.marker);
    },

    markerStyle(icon) {
      return new Style({
        image: new Icon({ scale: 0.6, src: icon }),
        text: new Text({
          offsetY: 25,
          font: "15px Open Sans,sans-serif",
          fill: new Fill({ color: "#111" }),
          stroke: new Stroke({ color: "#eee", width: 2 }),
        }),
      });
    },

    addDepartureMarker(obj) {
      const feature = new Feature({
        type: "removable",
        name: "departure-point",
        geometry: new Point(obj.coordinate),
      });

      feature.setStyle(this.markerStyle(this.icons.pin));
      this.vectorLayer.getSource().addFeature(feature);

      this.updateDeparturePoints();
    },

    addDestinationMarker(obj) {
      // Check if there is already a marker. If so, remove it
      let feature = this.vectorLayer.getSource().getFeatureById("target");
      if (feature) {
        this.vectorLayer.getSource().removeFeature(feature);
      }

      feature = new Feature({
        type: "removable",
        name: "destination-point",
        geometry: new Point(obj.coordinate),
      });

      feature.setId("target");
      feature.setStyle(this.markerStyle(this.icons.target));
      this.vectorLayer.getSource().addFeature(feature);

      this.updateDestinationPoint();
    },

    coordinatesFromFeature(feature) {
      return proj.transform(
        feature.getGeometry().getCoordinates(),
        this.projection.from,
        this.projection.to
      );
    },

    removeSingleDeparturePoint(coords) {
      this.$store.commit("updateState", {
        which: "departurePoints",
        value: this.$store.state.params.departurePoints.filter(
          (value) => !this.arraysMatch(value, coords)
        ),
      });
    },

    removeDeparturePoints() {
      this.$store.commit("updateState", {
        which: "departurePoints",
        value: [],
      });
    },

    removeDestinationPoint() {
      this.$store.commit("updateState", {
        which: "destinationPoint",
        value: null,
      });
    },

    updateDeparturePoints() {
      const departurePoints = this.vectorLayer
        .getSource()
        .getFeatures()
        .map((feature) => {
          if (feature.get("name") === "departure-point") {
            return this.coordinatesFromFeature(feature);
          }
        });

      this.$store.commit("updateState", {
        which: "departurePoints",
        value: departurePoints,
      });
    },

    updateDestinationPoint() {
      const destinationPoint = this.coordinatesFromFeature(
        this.vectorLayer.getSource().getFeatureById("target")
      );

      this.$store.commit("updateState", {
        which: "destinationPoint",
        value: destinationPoint,
      });
    },

    addFeatureFromGeoJSON(geoJSON) {
      const features = new GeoJSON({
        featureProjection: this.projection.from,
        geometryName: "trajectory",
        extractGeometryName: true,
      })
        .readFeatures(geoJSON)
        .map((f) => {
          f.setId("trajectory");
          return f;
        });

      const vectorSource = new VectorSource({
        features: features,
      });

      const vectorLayer = new VectorLayer({
        name: "trajectory",
        source: vectorSource,
        style: (feature) => {
          feature.getGeometry().getType();

          return new Style({
            stroke: new Stroke({
              color: "#E66E89",
              width: 2,
            }),
          });
        },
      });

      this.map.addLayer(vectorLayer);
    },

    removeAllLayers(name) {
      this.map
        .getLayers()
        .getArray()
        .filter((layer) => layer.get("name") === name)
        .forEach((layer) => this.map.removeLayer(layer));
    },

    removeAllTrajectories() {
      this.removeAllLayers("trajectory");
    },

    datesInRange(dateRange, interval) {
      const dates = [];

      let currentDate = new Date(dateRange[0]);
      let stopDate = new Date(dateRange[1]);

      while (currentDate <= stopDate) {
        // Add date to range
        dates.push(currentDate.toISOString().substring(0, 10));

        // Create temporary date
        let nextDate = new Date(currentDate);

        // Increment the date and assign
        nextDate.setDate(nextDate.getDate() + interval);
        currentDate = nextDate;
      }

      return dates;
    },

    computeTrajectories(params) {
      // Reset progress bar
      this.progress = 0;
      this.overlay = true;
      this.error = null;

      const { departurePoints, launchInterval, dates, destinationPoint, ...ps } = params;

      if ((departurePoints.length === 0) || (!destinationPoint)) {
        this.error = "Please enter a destination and departure on the map."
        setTimeout(() => {
          this.overlay = false;
          this.error = null;
        }, 5000)

        return;
      }

      // const trajectories = []
      const dateRange = this.datesInRange(dates, launchInterval);

      // Combine dates and departure points to single iterable
      const combinations = dateRange.flatMap((d) =>
        departurePoints.map((v) => [d, v])
      );

      let promises = [];

      for (let c of combinations) {
        let apiParams = trajectoryAPI.APIParams({
          departurePoint: c[1],
          start_date: c[0],
          destinationPoint: destinationPoint,
          ...ps,
        });

        promises.push(
          trajectoryAPI.get(apiParams)
          .then(response => {
            if (response) {
              this.progress += 100 * (1 / combinations.length);
              this.addFeatureFromGeoJSON(response);
            }


            return response;
          })
        );
      }

      // Commit all the promises
      Promise.all(promises)
        .finally(() => {
          this.overlay = false;
        });
    },
  },
};
</script>

<style>

.ol-ctx-menu-zoom-out {
  background-image: url("https://img.icons8.com/material/50/000000/minus--v2.png") !important;
}

.ol-ctx-menu-zoom-in {
  background-image: url("https://img.icons8.com/material/50/000000/plus-math--v2.png") !important;
}

.ol-ctx-menu-container {
  padding: 1.5em;
  background: #f2efe9;
  color: rgb(80, 79, 79);
 }

.ol-ctx-menu-container li.ol-ctx-menu-separator hr {
   background-image: none;

}

.ol-ctx-menu-container ul {
  padding-left: 0px !important;
}

.ol-control button {
  background: #f2efe9;
  color: rgb(80, 79, 79);
}

.ol-control button:active, .ol-control button:hover, .ol-control button:focus {
  background: #cecbc4;

}

.tip {

  width: 300px;
  position: absolute;
  top: .5em;
  right: .5em;
  padding: 15px;
  background: #f2efe9;
  color: rgb(80, 79, 79);
  opacity: 1;

  box-shadow: 0 3px 1px -2px rgb(0 0 0 / 20%), 0 2px 2px 0 rgb(0 0 0 / 14%),
    0 1px 5px 0 rgb(0 0 0 / 12%);
}


/* Tooltip container */
.tooltip {
  height: 80px;
  position: absolute;
  padding: 10px;
  background: #f2efe9;
  color: rgb(80, 79, 79);
  opacity: 1;
  white-space: nowrap;
  font: 10pt sans-serif;
  border-radius: 5px;
  top: -40px;
  left: 105%;
  box-shadow: 0 3px 1px -2px rgb(0 0 0 / 20%), 0 2px 2px 0 rgb(0 0 0 / 14%),
    0 1px 5px 0 rgb(0 0 0 / 12%);
}

.tooltip::after {
  content: " ";
  position: absolute;
  top: 50%;
  right: 100%; /* To the left of the tooltip */
  margin-top: -5px;
  border-width: 5px;
  border-style: solid;
  border-color: transparent #f2efe9 transparent transparent;
}
</style>