import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000/admin/chats'

function authHeader() {
  const token = localStorage.getItem('token')
  return {
    headers: {
      Authorization: `Bearer ${token}`
    }
  }
}

export async function fetchChats() {
  const res = await axios.get(`${API_URL}/`, authHeader())
  return res.data
}

export async function assignChat(chat_id, username) {
  const res = await axios.post(
    `${API_URL}/assign`,
    { chat_id, username },
    authHeader()
  )
  return res.data
}
export async function fetchOperators() {
  const res = await axios.get(`${API_URL}/operators`, authHeader())
  return res.data
}
export async function removeOperator(chat_id, username) {
  const res = await axios.post(
    `${API_URL}/remove`,
    { chat_id, username },
    authHeader()
  )
  return res.data
}