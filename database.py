# database.py - Versión para despliegue independiente
import sqlite3
import os
from datetime import datetime, date, time
import uuid

class DatabaseManager:
    def __init__(self, db_path="clinica.db"):
        self.db_path = db_path
        self.init_database()
        self.populate_initial_data()
    
    def init_database(self):
        """Inicializa la base de datos con todas las tablas necesarias"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla de médicos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medicos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    especialidad TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT,
                    activo BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Tabla de servicios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS servicios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    precio REAL NOT NULL,
                    duracion INTEGER DEFAULT 30,
                    medico_id INTEGER,
                    medico TEXT,
                    activo BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (medico_id) REFERENCES medicos (id)
                )
            ''')
            
            # Tabla de citas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS citas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_confirmacion TEXT UNIQUE NOT NULL,
                    paciente_nombre TEXT NOT NULL,
                    paciente_telefono TEXT NOT NULL,
                    servicio_id INTEGER NOT NULL,
                    medico_id INTEGER NOT NULL,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    estado TEXT DEFAULT 'confirmada',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (servicio_id) REFERENCES servicios (id),
                    FOREIGN KEY (medico_id) REFERENCES medicos (id)
                )
            ''')
            
            conn.commit()
    
    def populate_initial_data(self):
        """Llena la base de datos con datos iniciales si está vacía"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar si ya hay datos
            cursor.execute("SELECT COUNT(*) FROM servicios")
            if cursor.fetchone()[0] > 0:
                return  # Ya hay datos, no hacer nada
            
            # Insertar médicos
            medicos = [
                ("Dr. García", "Pediatría", "3312345001", "garcia@medicare.com"),
                ("Dra. Martínez", "Cardiología", "3312345002", "martinez@medicare.com"),
                ("Dr. López", "Dermatología", "3312345003", "lopez@medicare.com"),
                ("Dr. Rodríguez", "Medicina General", "3312345004", "rodriguez@medicare.com"),
                ("QFB Angel Carrizalez", "Laboratorio", "3312345005", "acarrizalez@medicare.com")
            ]
            
            cursor.executemany('''
                INSERT INTO medicos (nombre, especialidad, telefono, email)
                VALUES (?, ?, ?, ?)
            ''', medicos)
            
            # Insertar servicios (exactamente 5 servicios únicos)
            servicios = [
                ("Consulta General", 500, 30, 4, "Dr. Rodríguez"),
                ("Pediatría", 600, 45, 1, "Dr. García"),
                ("Cardiología", 800, 60, 2, "Dra. Martínez"),
                ("Dermatología", 700, 30, 3, "Dr. López"),
                ("Laboratorio", 250, 15, 5, "QFB Angel Carrizalez")
            ]
            
            cursor.executemany('''
                INSERT INTO servicios (nombre, precio, duracion, medico_id, medico)
                VALUES (?, ?, ?, ?, ?)
            ''', servicios)
            
            conn.commit()
    
    def obtener_servicios(self):
        """Obtiene todos los servicios disponibles (máximo 5 únicos)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT id, nombre, precio, duracion, medico_id, medico
                FROM servicios WHERE activo = TRUE
                ORDER BY id
                LIMIT 5
            ''')
            
            servicios_unicos = []
            nombres_vistos = set()
            
            for row in cursor.fetchall():
                nombre = row[1]
                if nombre not in nombres_vistos:
                    nombres_vistos.add(nombre)
                    servicios_unicos.append({
                        'id': row[0],
                        'nombre': row[1],
                        'precio': row[2],
                        'duracion': row[3],
                        'medico_id': row[4],
                        'medico': row[5]
                    })
            
            return servicios_unicos
    
    def obtener_horarios_disponibles(self, fecha):
        """Obtiene horarios disponibles para una fecha específica"""
        # Horarios base (simulación)
        horarios_base = [
            "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
            "12:00", "12:30", "14:00", "14:30", "15:00", "15:30",
            "16:00", "16:30", "17:00", "17:30"
        ]
        
        # Verificar horarios ocupados
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT hora FROM citas 
                WHERE fecha = ? AND estado != 'cancelada'
            ''', (fecha,))
            
            horarios_ocupados = [row[0] for row in cursor.fetchall()]
        
        # Retornar horarios disponibles
        return [h for h in horarios_base if h not in horarios_ocupados]
    
    def crear_cita(self, paciente_nombre, paciente_telefono, servicio_id, medico_id, fecha, hora):
        """Crea una nueva cita"""
        # Generar número de confirmación único
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        numero_confirmacion = f"MC{timestamp}"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO citas (numero_confirmacion, paciente_nombre, paciente_telefono,
                                     servicio_id, medico_id, fecha, hora)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (numero_confirmacion, paciente_nombre, paciente_telefono,
                      servicio_id, medico_id, fecha, hora))
                
                conn.commit()
                
                return {
                    'success': True,
                    'numero_confirmacion': numero_confirmacion,
                    'mensaje': 'Cita creada exitosamente'
                }
        except sqlite3.Error as e:
            return {
                'success': False,
                'mensaje': f'Error al crear la cita: {str(e)}'
            }
    
    def cancelar_cita(self, numero_confirmacion):
        """Cancela una cita existente"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar si la cita existe
                cursor.execute('''
                    SELECT id FROM citas WHERE numero_confirmacion = ? AND estado != 'cancelada'
                ''', (numero_confirmacion,))
                
                if cursor.fetchone() is None:
                    return {
                        'success': False,
                        'mensaje': 'Cita no encontrada o ya cancelada'
                    }
                
                # Cancelar la cita
                cursor.execute('''
                    UPDATE citas SET estado = 'cancelada' 
                    WHERE numero_confirmacion = ?
                ''', (numero_confirmacion,))
                
                conn.commit()
                
                return {
                    'success': True,
                    'mensaje': 'Cita cancelada exitosamente'
                }
        except sqlite3.Error as e:
            return {
                'success': False,
                'mensaje': f'Error al cancelar la cita: {str(e)}'
            }
    
    def buscar_citas(self, criterio, valor):
        """Busca citas por nombre o teléfono"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if criterio == 'nombre':
                    cursor.execute('''
                        SELECT c.numero_confirmacion, c.paciente_nombre, c.fecha, c.hora,
                               s.nombre as servicio, c.estado
                        FROM citas c
                        JOIN servicios s ON c.servicio_id = s.id
                        WHERE c.paciente_nombre LIKE ? AND c.estado != 'cancelada'
                        ORDER BY c.fecha DESC
                    ''', (f"%{valor}%",))
                elif criterio == 'telefono':
                    cursor.execute('''
                        SELECT c.numero_confirmacion, c.paciente_nombre, c.fecha, c.hora,
                               s.nombre as servicio, c.estado
                        FROM citas c
                        JOIN servicios s ON c.servicio_id = s.id
                        WHERE c.paciente_telefono = ? AND c.estado != 'cancelada'
                        ORDER BY c.fecha DESC
                    ''', (valor,))
                
                results = cursor.fetchall()
                return [
                    {
                        'numero_confirmacion': row[0],
                        'paciente_nombre': row[1],
                        'fecha': row[2],
                        'hora': row[3],
                        'servicio': row[4],
                        'estado': row[5]
                    }
                    for row in results
                ]
        except sqlite3.Error as e:
            return []