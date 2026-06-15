import axios from 'axios'

const API_URL = 'http://185.125.201.136:8000/api/users'

export async function register(username, password) {
  return axios.post(`${API_URL}/register`, { username, password })
}