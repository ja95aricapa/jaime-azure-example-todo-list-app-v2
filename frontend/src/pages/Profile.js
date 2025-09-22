import { useEffect, useState } from "react";
import { getProfile, updateProfile, logout } from "../api";
import { useNavigate } from "react-router-dom";

function Profile() {
	const [form, setForm] = useState({ name: "", email: "" });
	const navigate = useNavigate();

	useEffect(() => {
		(async () => {
			try {
				const res = await getProfile();
				const u = res.data.user || {};
				setForm({ name: u.name || "", email: u.email || "" });
			} catch (e) {
				// 401 se maneja global en el interceptor
				console.error(e);
			}
		})();
	}, []);

	const handleUpdate = async (e) => {
		e.preventDefault();
		try {
			await updateProfile({ name: form.name }); // 👈 no mandamos email (no se permite cambiar)
			alert("Perfil actualizado");
		} catch (e) {
			alert("Error: " + (e.response?.data?.error || e.message));
		}
	};

	const handleLogout = () => {
		logout();
		navigate("/");
	};

	const handleGoToDashboard = () => navigate("/dashboard");

	return (
		<div style={{ padding: "2rem" }}>
			<h2>Perfil</h2>
			<form onSubmit={handleUpdate}>
				<input
					placeholder='Nombre'
					value={form.name}
					onChange={(e) => setForm({ ...form, name: e.target.value })}
				/>
				<input placeholder='Email' value={form.email} disabled readOnly />
				<button type='submit'>Actualizar</button>
			</form>
			<button onClick={handleLogout}>Cerrar Sesión</button>
			<button onClick={handleGoToDashboard}>Regresar al Dashboard</button>
		</div>
	);
}

export default Profile;
