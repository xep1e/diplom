import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000/api/users'

export async function login(username, password) {
  const res = await axios.post(`${API_URL}/login`, { username, password })

  localStorage.setItem("token", res.data.access_token)
  return res.data
}

export async function getMe() {
  const token = localStorage.getItem("token")

  const res = await axios.get(`${API_URL}/me`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })

  return res.data
}