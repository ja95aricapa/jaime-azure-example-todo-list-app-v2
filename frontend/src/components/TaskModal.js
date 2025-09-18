import { useState, useEffect } from "react";

function TaskModal({ task, onSave, onClose }) {
	const [form, setForm] = useState({ title: "", status: "pending" });

	useEffect(() => {
		if (task) setForm(task);
	}, [task]);

	const handleSubmit = (e) => {
		e.preventDefault();
		onSave(form);
	};

	return (
		<div style={{ background: "#eee", padding: "1rem", borderRadius: "8px" }}>
			<h3>{task ? "Editar Tarea" : "Nueva Tarea"}</h3>
			<form onSubmit={handleSubmit}>
				<input
					placeholder='Título'
					value={form.title}
					onChange={(e) => setForm({ ...form, title: e.target.value })}
				/>
				<select
					value={form.status}
					onChange={(e) => setForm({ ...form, status: e.target.value })}
				>
					<option value='pending'>Pendiente</option>
					<option value='done'>Completada</option>
				</select>
				<button type='submit'>Guardar</button>
				<button type='button' onClick={onClose}>
					Cancelar
				</button>
			</form>
		</div>
	);
}

export default TaskModal;
