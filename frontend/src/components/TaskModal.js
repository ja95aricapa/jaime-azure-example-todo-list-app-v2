import { useState, useEffect } from "react";

const CREATION_STATUS_OPTIONS = [
	{ value: "pending", label: "Pendiente" },
	{ value: "in_progress", label: "En Curso" },
];

const EDIT_STATUS_OPTIONS = [
	...CREATION_STATUS_OPTIONS,
	{ value: "blocked", label: "Bloqueado" },
	{ value: "done", label: "Terminado" },
];

function TaskModal({ task, onSave, onClose }) {
	const [form, setForm] = useState({ title: "", status: "pending" });

	useEffect(() => {
		if (task) {
			setForm({
				title: task.title || "",
				status: task.status || "pending",
			});
		} else {
			setForm({ title: "", status: "pending" });
		}
	}, [task]);

	const handleSubmit = (e) => {
		e.preventDefault();
		const title = form.title.trim();
		if (!title) {
			alert("El título no puede estar vacío");
			return;
		}
		onSave({ title, status: form.status });
	};

	const statusOptions = task ? EDIT_STATUS_OPTIONS : CREATION_STATUS_OPTIONS;

	return (
		<div className='modal-overlay'>
			<div className='modal'>
				<div className='modal-header'>
					<h3>{task ? "Editar Tarea" : "Nueva Tarea"}</h3>
					<button
						className='icon-button'
						type='button'
						onClick={onClose}
						aria-label='Cerrar'
					>
						x
					</button>
				</div>
				<form onSubmit={handleSubmit} className='modal-form'>
					<label className='input-group'>
						<span>Título</span>
						<input
							required
							placeholder='Describe la tarea'
							value={form.title}
							onChange={(e) => setForm({ ...form, title: e.target.value })}
						/>
					</label>
					<label className='input-group'>
						<span>Estado</span>
						<select
							value={form.status}
							onChange={(e) => setForm({ ...form, status: e.target.value })}
						>
							{statusOptions.map((option) => (
								<option key={option.value} value={option.value}>
									{option.label}
								</option>
							))}
						</select>
					</label>
					<div className='modal-actions'>
						<button className='btn primary' type='submit'>
							Guardar
						</button>
						<button className='btn ghost' type='button' onClick={onClose}>
							Cancelar
						</button>
					</div>
				</form>
			</div>
		</div>
	);
}

export default TaskModal;
