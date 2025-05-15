
## ***📁 Documentación Técnica Tools:***

### **🧾🐍 `assistant_tool.py`**

**Descripcion:** 
Archivo que contiene herramientas (tools) con única responsabilidad para ser utilizadas por agentes/asistentes inteligentes, facilitando la interacción con servicios externos como WhatsApp a través de Baileys.

**📦 Dependencias:**

- `aiohttp`: Para realizar peticiones HTTP asíncronas.
- `json`: Para formatear y serializar los datos enviados.
- `menu_service`: Servicio personalizado que obtiene información del menú desde el backend.
- `BAILEYS_SERVER_URL`: URL del servidor que conecta con WhatsApp a través de la API de Baileys.
- `tool`: Decorador que registra las funciones como herramientas disponibles para el asistente.

**🛠️ Listado de Tools**

🔧 `send_menu_images:` Permite enviar todas las imágenes del menú disponibles al cliente mediante WhatsApp, utilizando un servidor intermedio (como Baileys) para gestionar el envío de imágenes codificadas en hexadecimal.

**Argumentos:**

**phone (str):** Número de teléfono del cliente (en formato internacional).


**Funcionamiento:**

- Recupera todas las imágenes del menú disponibles desde el backend a través de menu_service.

- Verifica que cada imagen tenga contenido en formato hexadecimal (image_hex).

- Envía cada imagen individualmente al número indicado, incluyendo una descripción basada en el tipo de menú (ej.:   Menú almuerzo).

- Maneja y reporta cualquier error durante el envío, devolviendo un mensaje claro del estado de la operación.

**Caso de usos:**
Esta herramienta permite enviar menús actualizados por WhatsApp sin intervención manual, mejorando la eficiencia operativa en restaurantes o servicios de comida.

🔧 `send_location_tool:` Permite enviar la ubicación del restaurante al cliente mediante WhatsApp, utilizando un servidor intermedio (como Baileys) que gestiona el envío de mensajes de ubicación.

**Argumentos:**

**phone (str):** Número de teléfono del cliente (en formato internacional).

**Funcionamiento:**

- Define los datos de ubicación que serán enviados al numero de celular del cliente.

- Establece una sesión HTTP utilizando aiohttp y realiza una solicitud POST al endpoint /api/send-location del servidor Baileys.

- Verifica la respuesta del servidor:

Si la respuesta es exitosa (status == 200), devuelve un mensaje de confirmación.

Si ocurre un error, intenta capturar el mensaje de error del cuerpo de la respuesta o muestra el texto plano como fallback.

- Maneja errores de red o ejecución, devolviendo un mensaje claro sobre el estado de la operación.

**Caso de usos:**
Esta herramienta permite compartir la ubicación del restaurante de manera automatizada a través de WhatsApp, útil para mejorar la experiencia del cliente, especialmente en servicios de entrega, reservas o nuevas visitas.

---

### **🧾🐍 `menu_tool.py`**

**Descripcion:**  
Archivo que contiene una herramienta con única responsabilidad: recuperar el menú actualizado de productos desde la base de datos, agrupándolos por categoría. Esta función puede ser utilizada por asistentes inteligentes para responder consultas sobre disponibilidad o estructura del menú.

**📦 Dependencias:**

- `asyncio`: Permite ejecutar funciones asincrónicas en un entorno síncrono.
- `InventoryService`: Servicio personalizado que se conecta a la base de datos para obtener los productos disponibles.
- `tool`: Decorador que registra la función como una herramienta accesible para el asistente.

**🛠️ Listado de Tools**

🔧 `get_menu:` Recupera el menú completo de productos desde la base de datos y los organiza por categoría (por ejemplo: hamburguesas, bebidas, combos, etc.).

**Argumentos:**  
**Sin argumentos.**

**Funcionamiento:**

- Crea una instancia de `InventoryService`, un servicio personalizado para acceder a la base de datos de productos.

- Ejecuta asincrónicamente la función `get_menu_products()` que obtiene todos los productos disponibles.

- Recorre la lista de productos obtenida y los organiza en un diccionario, donde cada clave representa una categoría y su valor es una lista de productos correspondientes.

- Devuelve el diccionario estructurado, útil para mostrar el menú de manera clara y jerarquizada.

**Caso de usos:**  
Esta herramienta permite a asistentes virtuales consultar dinámicamente el menú de un restaurante, útil para responder preguntas sobre la disponibilidad de productos, generar menús personalizados o integrarse con otras herramientas como generadores de menús visuales o sistemas de pedidos.

---

### **🧾🐍 `order_tool.py`**

**Descripción:**  
Este archivo contiene herramientas relacionadas con la creación y modificación de órdenes de compra de productos por parte de un cliente. Permite confirmar pedidos, obtener la última orden de un cliente, añadir productos a una orden existente y actualizar productos previamente añadidos.

**📦 Dependencias:**
- `OrderService`: Servicio encargado de la lógica de manejo de órdenes.
- `database_service`: Servicio para gestionar usuarios y datos persistentes.
- `Session` de `sqlmodel`: Para gestionar sesiones con la base de datos.
- `asyncio`: Para ejecutar funciones asincrónicas.
- `UUID`: Para manejar identificadores únicos de órdenes.
- `tool` de `langchain_core`: Para registrar funciones como herramientas utilizables por asistentes inteligentes.


 🔧 `confirm_product`

**Descripción:**  
Confirma un pedido con los productos seleccionados por el cliente.

**Argumentos:**
- `phone`: Número de teléfono del cliente.
- `name`: Nombre del cliente.
- `address`: Dirección de entrega.
- `products`: Lista de productos, cada uno con:
  - `product_name`
  - `quantity`
  - `unit_price`
  - `subtotal`
  - `details` *(opcional)*

**Retorna:**
Un diccionario con el `order_id`, `status`, `total_amount`, `address` y los productos confirmados o un mensaje de error o solicitud de dirección.

**Casos de uso:**
Confirmar pedidos de manera estructurada, registrar órdenes en la base de datos y asegurar que el cliente tenga una dirección válida.


🔧 `get_last_order`

**Descripción:**  
Obtiene la última orden registrada por un cliente, si existe.

**Argumentos:**
- `phone`: Número de teléfono del cliente.

**Retorna:**
Un diccionario con un mensaje, el estado de si tiene o no órdenes, y el contenido de la última orden.

**Casos de uso:**
Consultar el historial inmediato de compras del cliente para mostrar el estado del pedido o reutilizar productos anteriores.

---

🔧 `add_products_to_order`

**Descripción:**  
Añade nuevos productos a la última orden pendiente del cliente.

**Argumentos:**
- `phone`: Número de teléfono del cliente.
- `products`: Lista de nuevos productos a añadir con:
  - `product_name`
  - `quantity`
  - `unit_price`
  - `subtotal`
  - `details` *(opcional)*

**Retorna:**
Un diccionario con mensaje de éxito o error, y el estado actualizado de la orden.

**Casos de uso:**
Permitir modificaciones sobre pedidos en curso, añadiendo productos adicionales antes de que la orden sea completada.


🔧 `update_order_product`

**Descripción:**  
Modifica un producto específico dentro de la última orden del cliente.

**Argumentos:**
- `phone`: Número de teléfono del cliente.
- `product_name`: Producto a modificar.
- `new_data`: Diccionario con los campos a actualizar:
  - `quantity` *(opcional)*
  - `unit_price` *(opcional)*
  - `details` *(opcional)*

**Retorna:**
Un mensaje y la orden con los datos del producto actualizado, o un error si no fue posible modificarlo.

**Casos de uso:**
Modificar cantidades, precios o comentarios de productos antes de confirmar una orden de compra definitiva.

---

## ***📁 Documentación Técnica Graph:***

### **🧾🐍 `create_graph()`**

**Descripción:**  
La función `create_graph` construye y compila un grafo de estado utilizando LangGraph, coordinando un flujo de trabajo asincrónico entre múltiples agentes especializados y herramientas. Se asegura de que el grafo solo se cree una vez (`self._graph is None`) y utiliza un orquestador para enrutar solicitudes según la intención detectada.

Además, configura los puntos de entrada, nodos condicionales y de finalización, y permite la integración con una base de datos PostgreSQL para persistencia del estado del grafo usando `AsyncPostgresSaver`.

### **🌐 Nodos del Agente y su Propósito**

#### 🧠🤖 `orchestrator`  
**Descripción:** Nodo de entrada principal del grafo.  
**Función:** Dirige el flujo hacia el agente adecuado dependiendo de la intención del usuario (`self.route_by_intent`).  
**Destino posible:** Cualquiera de los agentes especializados.

#### 🗣️ `conversation_agent`  
**Descripción:** Agente especializado en conversaciones generales.  
**Función:** Maneja diálogos abiertos o preguntas generales.  
**Interacción:** Llama a `conversation_tool_call` si se requiere una herramienta adicional.

####  📄  `order_data_agent`  
**Descripción:** Agente responsable de proporcionar información sobre órdenes.  
**Función:** Consulta el estado o detalles de una orden.  
**Interacción:** Llama a `order_data_tool_call` si es necesario acceder a datos externos.

#### 📝 `update_order_agent`  
**Descripción:** Agente encargado de modificar datos de órdenes existentes.  
**Función:** Procesa cambios como dirección, método de pago o estado de la orden.  
**Interacción:** Utiliza `update_order_tool_call` cuando se requiere una operación externa.

#### 📬 `pqrs_agent`  
**Descripción:** Agente especializado en Peticiones, Quejas, Reclamos y Sugerencias (PQRS).  
**Función:** Recibe y gestiona interacciones relacionadas con la experiencia del usuario o cliente.

---

### ** 🤖  Nodos de Herramienta y su Propósito**

#### 🔧📞 `conversation_tool_call`  
**Función:** Herramienta auxiliar de `conversation_agent` para operaciones adicionales como consultas a APIs externas.

#### 🔧📞 `order_data_tool_call`  
**Función:** Herramienta de soporte para `order_data_agent`, usada para acceder a información externa de órdenes.

#### 🔧📞 `update_order_tool_call`  
**Función:** Herramienta de ayuda para `update_order_agent`, ejecuta operaciones externas necesarias para modificar órdenes.

---

### **⚙️ Configuraciones Clave**

- `builder.set_entry_point("orchestrator")`: Define el nodo inicial del grafo.
- `builder.add_conditional_edges(...)`: Configura el flujo condicional desde el `orchestrator` hacia cada agente.
- `builder.set_finish_point(...)`: Establece los puntos de finalización para cada agente especializado.
- `checkpointer = AsyncPostgresSaver(...)`: Permite la persistencia del estado del grafo usando PostgreSQL si está configurado.

---

### **❌🚨 Manejo de Errores**

- Si ocurre un error durante la creación del grafo:
  - Se registra en el logger.
  - En producción: se retorna `None` y se continúa sin grafo.
  - En desarrollo: se lanza una excepción para facilitar el debugging.

---

### **Resultado**

Devuelve una instancia de `CompiledStateGraph`, lista para enrutar y ejecutar solicitudes a través de los agentes definidos.

