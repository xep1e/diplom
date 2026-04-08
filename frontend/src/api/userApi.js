import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000/api/users' // база с префиксом

export async function fetchUsers() {
  const res = await axios.get(`${API_URL}/`)  // GET /api/users/
  return res.data
}

export async function createUser(username, password) {
  const res = await axios.post(`${API_URL}/register`, { username, password }) // POST /api/users/register
  return res.data
}