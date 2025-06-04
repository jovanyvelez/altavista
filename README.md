### Voy a iniciar un proyecto nuevo, usando fastapi, Jinja2, sqlmodel

El proyecto consiste en desarrollar un sofware para apoyo a la gestión de administración de las zonas comunes de una comunidad de propietarios que reside en un edificio de viviendas.

### Descripción del proyecto
El proyecto tiene como objetivo proporcionar una plataforma para la gestión eficiente de las zonas comunes de un edificio residencial. Permitirá a los administradores, llevar un seguimiento de los gastos e ingresos, de acuerdo a las cuotas de cada propietario y el presupuesto anual.

### Funcionalidades principales
- Registro de propietarios y sus datos de contacto.
- Registro de conceptos de gastos e ingresos.
- Importación del presupuesto anual de gastos desde un archivo Excel.
- Registro del valor mensual de las cuotas de cada propietario para el año en curso.
- Registro de las tasas de interés aplicables a las cuotas en mora por mes y año.
- Registro de gastos extraordinarios, con respaldo digital del soporte de ingreso.
- Registro de ingresos por cuotas mensuales de propietarios, con respaldo digital del soporte de ingreso.
- Registro de gastos asociados a las zonas comunes, con ingreso de copia digital de factura o documento que soporte el egreso.
- Cálculo automático de cuotas mensuales para cada propietario.
- Cálculo de saldos pendientes por propietario, incluyendo cuotas mensuales, cuotas extraordinarias, cuotas en mora, intereses, etc. Los intereses se calcularán mensualmente.
- Generación de informes de saldos pendientes por propietario.
- Generación de informes de cuotas mensuales por propietario.
- Generación de informes de cuotas extraordinarias por propietario.
- Generación de informes de cuotas en mora por propietario.
- Generación de informes de gastos e ingresos.
- Comparativos de gastos e ingresos por periodo vs. presupuesto.
- Visualización de datos a través de gráficos.
- Generación de informes financieros.
- Interfaz web para la visualización y gestión de datos.
- Autenticación de usuarios para administradores y propietarios.

### Requisitos
- Python 3.10 o superior
- FastAPI
- Jinja2
- SQLModel
- SQLite para desarrollo, pero en producción se debe migrar a PostgreSQL con facilidad.

### Analisis y Diseño
Para el análisis y diseño del proyecto, se utilizará un enfoque basado en la arquitectura de software MVC (Modelo-Vista-Controlador). Esto permitirá una separación clara de las responsabilidades y facilitará el mantenimiento y la escalabilidad del sistema.

