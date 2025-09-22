import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, register } from "../api";

function Login() {
	const [isRegister, setIsRegister] = useState(false);
	const [form, setForm] = useState({ email: "", password: "", name: "" });
	const navigate = useNavigate();

	const handleSubmit = async (e) => {
		e.preventDefault();
		try {
			if (isRegister) {
				await register(form.email, form.password, form.name);
				alert("¡Registro exitoso! Ahora inicia sesión.");
				setIsRegister(false);
			} else {
				const res = await login(form.email, form.password);
				localStorage.setItem("token", res.data.token);
				navigate("/dashboard");
			}
		} catch (err) {
			const message = err.response?.data?.error || err.message;
			alert("Error: " + message);
		}
	};

	return (
		<div className='page auth-page'>
			<div className='auth-card'>
				<h1>{isRegister ? "Crear cuenta" : "Bienvenido"}</h1>
				<p className='subtitle'>
					{isRegister
						? "Regístrate para comenzar a gestionar tus tareas"
						: "Inicia sesión para continuar con tus pendientes"}
				</p>
				<form onSubmit={handleSubmit} className='form'>
					{isRegister && (
						<label className='input-group'>
							<span>Nombre</span>
							<input
								required
								placeholder='¿Cómo te llamas?'
								value={form.name}
								onChange={(e) => setForm({ ...form, name: e.target.value })}
							/>
						</label>
					)}
					<label className='input-group'>
						<span>Correo</span>
						<input
							required
							type='email'
							placeholder='tu@email.com'
							value={form.email}
							onChange={(e) => setForm({ ...form, email: e.target.value })}
						/>
					</label>
					<label className='input-group'>
						<span>Contraseña</span>
						<input
							required
							type='password'
							placeholder='Introduce tu contraseña'
							value={form.password}
							onChange={(e) => setForm({ ...form, password: e.target.value })}
						/>
					</label>
					<button className='btn primary full-width' type='submit'>
						{isRegister ? "Registrarme" : "Iniciar Sesión"}
					</button>
				</form>
				<button
					type='button'
					className='btn link'
					onClick={() => setIsRegister(!isRegister)}
				>
					{isRegister
						? "¿Ya tienes cuenta? Inicia sesión"
						: "¿No tienes cuenta? Regístrate"}
				</button>
			</div>
		</div>
	);
}

export default Login;
