import { useState } from "react";
import { login, register } from "../api";
import { useNavigate } from "react-router-dom";

function Login() {
	const [isRegister, setIsRegister] = useState(false);
	const [form, setForm] = useState({ email: "", password: "", name: "" });
	const navigate = useNavigate();

	const handleSubmit = async (e) => {
		e.preventDefault();
		try {
			if (isRegister) {
				// 1. Llama a la función de registro
				await register(form.email, form.password, form.name);
				// 2. Muestra un mensaje de éxito
				alert("¡Registro exitoso! Ahora por favor inicia sesión.");
				// 3. Cambia el formulario de vuelta a modo Login
				setIsRegister(false);
			} else {
				// El flujo de login ya funciona bien
				const res = await login(form.email, form.password);
				localStorage.setItem("token", res.data.token);
				navigate("/dashboard");
			}
		} catch (err) {
			alert("Error: " + err.response?.data?.error || err.message);
		}
	};

	return (
		<div style={{ padding: "2rem" }}>
			<h2>{isRegister ? "Registro" : "Login"}</h2>
			<form onSubmit={handleSubmit}>
				{isRegister && (
					<input
						placeholder='Nombre'
						value={form.name}
						onChange={(e) => setForm({ ...form, name: e.target.value })}
					/>
				)}
				<input
					placeholder='Email'
					type='email'
					value={form.email}
					onChange={(e) => setForm({ ...form, email: e.target.value })}
				/>
				<input
					placeholder='Password'
					type='password'
					value={form.password}
					onChange={(e) => setForm({ ...form, password: e.target.value })}
				/>
				<button type='submit'>
					{isRegister ? "Registrarse" : "Iniciar Sesión"}
				</button>
			</form>
			<p
				onClick={() => setIsRegister(!isRegister)}
				style={{ cursor: "pointer" }}
			>
				{isRegister
					? "¿Ya tienes cuenta? Inicia sesión"
					: "¿No tienes cuenta? Regístrate"}
			</p>
		</div>
	);
}

export default Login;
