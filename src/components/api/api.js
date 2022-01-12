import axios from 'axios'

export default class API {
  constructor (url, params) {
    this.url = url
    this.baseURL = 'http://127.0.0.1:5000/api'
    this.responseType = 'json'
    this.axios = axios.create({
      baseURL: this.baseURL,
      responseType: this.responseType,
      ...params
    })
  }

  async call (config) {
    try {
      const response = await this.axios.request(config)
      return response.data
    } catch (error) {
      console.log(error)
      // return error
    }
  }

  async get (params) {
    // Get promised data
    return await this.call({ url: this.url, method: 'get', params: params })
  }
}