import API from './api'

class TrajectoryAPI extends API {
  constructor() {
    super('/trajectory/', {})
  }

  async get(params) {
    return super.get(params)
  }

  APIParams(params) {

    const renamed = {}

    for (let key in params) {

      switch (key) {
        case 'departurePoint':
          renamed['departure_lon'] = params['departurePoint'][0]
          renamed['departure_lat'] = params['departurePoint'][1]
          break;
        case 'destinationPoint':
          renamed['destination_lon'] = params[key][0]
          renamed['destination_lat'] = params[key][1]
          break;
        case 'journeyLength':
          renamed['duration'] = params[key]
          break;
        case 'propulsionType':
          renamed['mode'] = params[key]
          break;
        case 'vesselType':
          renamed['craft'] = params[key]
          break;
        case 'paddlingSpeed':
          renamed['speed'] = params[key]
          break;
        case 'start_date':
          renamed['start_date'] = params[key]
          break;
        case 'timestep':
          renamed['timestep'] = params[key]
          break;
        case 'bbox':
          renamed['lon_min'] = params[key][0]
          renamed['lon_max'] = params[key][2]
          renamed['lat_min'] = params[key][1]
          renamed['lat_max'] = params[key][3]
          break;
        default:
          console.log(`Invalid parameter: ${key}`)
      }
    }

    return renamed;
  }
}

const trajectoryAPI = new TrajectoryAPI()
export default trajectoryAPI