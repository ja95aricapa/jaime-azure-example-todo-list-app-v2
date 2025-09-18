import { useEffect, useState } from "react";
import { getTasks, createTask, updateTask, deleteTask } from "../api";
import TaskModal from "../components/TaskModal";
import { useNavigate } from "react-router-dom";

function Dashboard() {
	const [tasks, setTasks] = useState([]);
	const [modalOpen, setModalOpen] = useState(false);
	const [editing, setEditing] = useState(null);
	const token = localStorage.getItem("token");
	const navigate = useNavigate();

	useEffect(() => {
		if (!token) navigate("/");
		loadTasks();
	}, []);

	const loadTasks = async () => {
		try {
			const res = await getTasks(token);
			setTasks(res.data);
		} catch (err) {
			console.error(err);
		}
	};

	const handleSave = async (task) => {
		if (editing) {
			await updateTask(editing.id, task, token);
		} else {
			await createTask(task, token);
		}
		setEditing(null);
		setModalOpen(false);
		loadTasks();
	};

	return (
		<div style={{ display: "flex", padding: "2rem", gap: "2rem" }}>
			<div style={{ flex: 2 }}>
				<h2>Tareas</h2>
				<button onClick={() => setModalOpen(true)}>Nueva Tarea</button>
				<ul>
					{tasks.map((t) => (
						<li key={t.id}>
							{t.title} - {t.status}
							<button
								onClick={() => {
									setEditing(t);
									setModalOpen(true);
								}}
							>
								Editar
							</button>
							<button onClick={() => deleteTask(t.id, token).then(loadTasks)}>
								Borrar
							</button>
						</li>
					))}
				</ul>
				{modalOpen && (
					<TaskModal
						task={editing}
						onSave={handleSave}
						onClose={() => {
							setModalOpen(false);
							setEditing(null);
						}}
					/>
				)}
			</div>
			<div
				style={{ flex: 1, borderLeft: "1px solid #ccc", paddingLeft: "2rem" }}
			>
				<h2>Perfil</h2>
				<button onClick={() => navigate("/profile")}>Mi Perfil</button>
			</div>
		</div>
	);
}

export default Dashboard;
