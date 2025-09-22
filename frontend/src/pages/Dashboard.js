import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getTasks, createTask, updateTask, deleteTask, logout } from "../api";
import TaskModal from "../components/TaskModal";

const STATUS_LABELS = {
	pending: "Pendiente",
	in_progress: "En Curso",
	done: "Terminado",
	blocked: "Bloqueado",
};

function Dashboard() {
	const [tasks, setTasks] = useState([]);
	const [modalOpen, setModalOpen] = useState(false);
	const [editing, setEditing] = useState(null);
	const navigate = useNavigate();

	useEffect(() => {
		const token = localStorage.getItem("token");
		if (!token) {
			navigate("/");
			return;
		}
		loadTasks();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	const loadTasks = async () => {
		try {
			const res = await getTasks();
			setTasks(res.data || []);
		} catch (err) {
			console.error(err);
			alert("No se pudieron cargar las tareas");
		}
	};

	const handleSave = async (task) => {
		try {
			if (editing) {
				await updateTask(editing.id, task);
			} else {
				await createTask(task);
			}
			setEditing(null);
			setModalOpen(false);
			loadTasks();
		} catch (e) {
			alert("Error: " + (e.response?.data?.error || e.message));
		}
	};

	const handleDelete = async (taskId) => {
		if (!window.confirm("¿Seguro que deseas borrar esta tarea?")) return;
		try {
			await deleteTask(taskId);
			loadTasks();
		} catch (e) {
			alert("Error: " + (e.response?.data?.error || e.message));
		}
	};

	const statusCounters = useMemo(() => {
		return tasks.reduce(
			(acc, task) => {
				const key = task.status || "pending";
				if (acc[key] === undefined) {
					acc[key] = 0;
				}
				acc[key] += 1;
				return acc;
			},
			{ pending: 0, in_progress: 0, done: 0, blocked: 0 }
		);
	}, [tasks]);

	return (
		<div className='page dashboard-page'>
			<header className='topbar'>
				<div>
					<h1>Panel de Tareas</h1>
					<p>Organiza tu trabajo y da seguimiento al progreso del equipo.</p>
				</div>
				<div className='topbar-actions'>
					<button className='btn ghost' onClick={() => navigate("/profile")}>
						Mi Perfil
					</button>
					<button
						className='btn ghost'
						onClick={() => {
							logout();
							navigate("/");
						}}
					>
						Cerrar Sesión
					</button>
					<button
						className='btn primary'
						onClick={() => {
							setEditing(null);
							setModalOpen(true);
						}}
					>
						Nueva Tarea
					</button>
				</div>
			</header>

			<section className='dashboard-grid'>
				<article className='card'>
					<header className='card-header'>
						<h2>Mis Tareas</h2>
						<span className='badge'>{tasks.length}</span>
					</header>
					<ul className='task-list'>
						{tasks.length === 0 ? (
							<li className='empty-state'>
								<p>Aún no tienes tareas registradas.</p>
								<button
									className='btn secondary'
									onClick={() => {
										setEditing(null);
										setModalOpen(true);
									}}
								>
									Crear mi primera tarea
								</button>
							</li>
						) : (
							tasks.map((task) => (
								<li className='task-item' key={task.id}>
									<div>
										<h3>{task.title}</h3>
										<span className={`status-pill status-${task.status}`}>
											{STATUS_LABELS[task.status] || task.status}
										</span>
									</div>
									<div className='task-actions'>
										<button
											className='btn ghost'
											onClick={() => {
												setEditing(task);
												setModalOpen(true);
											}}
										>
											Editar
										</button>
										<button
											className='btn danger'
											onClick={() => handleDelete(task.id)}
										>
											Borrar
										</button>
									</div>
								</li>
							))
						)}
					</ul>
				</article>

				<aside className='card stats-card'>
					<header className='card-header'>
						<h2>Resumen</h2>
					</header>
					<ul className='stats-list'>
							{Object.entries(statusCounters).map(([key, value]) => (
								<li key={key}>
									<span>{STATUS_LABELS[key] || key}</span>
								<strong>{value}</strong>
							</li>
						))}
					</ul>
				</aside>
			</section>

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
	);
}

export default Dashboard;
