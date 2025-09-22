import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:7071/api";
const SHOW_HTTP_LOGS = process.env.REACT_APP_SHOW_HTTP_LOGS === "true";

const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (SHOW_HTTP_LOGS) {
      console.log("➡️ Request:", config);
    }
    return config;
  },
  (error) => {
    if (SHOW_HTTP_LOGS) {
      console.error("❌ Request Error:", error);
    }
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    if (SHOW_HTTP_LOGS) {
      console.log("⬅️ Response:", response);
    }
    return response;
  },
  (error) => {
    if (SHOW_HTTP_LOGS) {
      console.error("❌ Error:", error);
    }
    if (error?.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);

// --- Usuario ---
export const login = (email, password) => api.post("/user/login", { email, password });
export const register = (email, password, name) => api.post("/user/register", { email, password, name });
export const getProfile = () => api.get("/user/profile");
export const updateProfile = (user) => api.put("/user/profile", user);
export const logout = () => localStorage.removeItem("token");

// --- Tareas ---
export const getTasks = () => api.get("/tasks");
export const createTask = (task) => api.post("/tasks", task);
export const updateTask = (id, task) => api.put(`/tasks/${id}`, task);
export const deleteTask = (id) => api.delete(`/tasks/${id}`);
