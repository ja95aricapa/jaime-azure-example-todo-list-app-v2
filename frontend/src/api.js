import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:7071/api";
const SHOW_HTTP_LOGS = process.env.REACT_APP_SHOW_HTTP_LOGS === "true";

const api = axios.create({ baseURL: API_BASE });

// ▼▼▼ LA MAGIA OCURRE AQUÍ ▼▼▼
// Este interceptor se ejecuta ANTES de cada petición.
api.interceptors.request.use(
	(config) => {
		// Obtenemos el token de localStorage
		const token = localStorage.getItem("token");

		// Si el token existe, lo añadimos a la cabecera de la petición
		if (token) {
			config.headers.Authorization = `Bearer ${token}`;
		}

		if (SHOW_HTTP_LOGS) {
			console.log("➡️ Request:", config);
		}
		return config;
	},
	(error) => {
		// Si hay un error al configurar la petición, lo rechazamos.
		if (SHOW_HTTP_LOGS) {
			console.error("❌ Request Error:", error);
		}
		return Promise.reject(error);
	}
);

if (SHOW_HTTP_LOGS) {
	api.interceptors.response.use(
		(response) => {
			console.log("⬅️ Response:", response);
			return response;
		},
		(error) => {
			console.error("❌ Error:", error);
			// Podrías añadir lógica aquí para desloguear al usuario si el error es 401
			// if (error.response.status === 401) {
			//   logout();
			//   window.location.href = '/';
			// }
			return Promise.reject(error);
		}
	);
}

// --- Funciones de Usuario ---
// Nota: Ahora no necesitan recibir el token como argumento
export const login = (email, password) =>
	api.post("/user/login", { email, password });

export const register = (email, password, name) =>
	api.post("/user/register", { email, password, name });

export const updateProfile = (user) => api.put("/user/profile", user);

export const logout = () => localStorage.removeItem("token");

// --- Funciones de Tareas ---
// ¡Observa qué limpias quedan ahora! Ya no necesitan el token.
export const getTasks = () => api.get("/tasks");

export const createTask = (task) => api.post("/tasks", task);

export const updateTask = (id, task) => api.put(`/tasks/${id}`, task);

export const deleteTask = (id) => api.delete(`/tasks/${id}`);
