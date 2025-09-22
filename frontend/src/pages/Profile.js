import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getProfile, updateProfile, logout } from "../api";

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
				console.error(e);
			}
		})();
	}, []);

	const handleUpdate = async (e) => {
		e.preventDefault();
		try {
			await updateProfile({ name: form.name });
			alert("Perfil actualizado");
		} catch (e) {
			alert("Error: " + (e.response?.data?.error || e.message));
		}
	};

	const handleLogout = () => {
		logout();
		navigate("/");
	};

	return (
		<div className='page profile-page'>
			<div className='card profile-card'>
				<header className='card-header'>
					<div>
						<h1>Mi Perfil</h1>
						<p className='subtitle'>Actualiza tus datos y gestiona tu cuenta.</p>
					</div>
					<button className='btn ghost' onClick={() => navigate("/dashboard")}>Regresar</button>
				</header>
				<form onSubmit={handleUpdate} className='form'>
					<label className='input-group'>
						<span>Nombre</span>
						<input
							required
							value={form.name}
							onChange={(e) => setForm({ ...form, name: e.target.value })}
						/>
					</label>
					<label className='input-group'>
						<span>Correo</span>
						<input value={form.email} disabled readOnly />
					</label>
					<div className='form-actions'>
						<button className='btn primary' type='submit'>Guardar cambios</button>
						<button className='btn danger outline' type='button' onClick={handleLogout}>
							Cerrar Sesión
						</button>
					</div>
				</form>
			</div>
		</div>
	);
}

export default Profile;
