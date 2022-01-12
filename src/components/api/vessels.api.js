import API from './api'

class VesselsAPI extends API {
  constructor () {
    super('/vessels/', {})
  }

  async get (params) {
    return super.get(params)
  }
}

const vesselsAPI = new VesselsAPI()
export default vesselsAPI