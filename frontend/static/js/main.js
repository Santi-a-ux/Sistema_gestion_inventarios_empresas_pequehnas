// Configuración de la API
const API_URL = window.location.hostname === "localhost"
  ? "http://localhost:5001/api"
  : "/api";
const API_TOKEN = 'mi_token_api_super_seguro_456';  // Este token debe coincidir con el del backend

let productosCargados = [];

// --- LOGIN Y ROLES ---
const JWT_KEY = 'admin_jwt';
const USER_KEY = 'admin_user';

function isAdminLoggedIn() {
    return !!localStorage.getItem(JWT_KEY);
}

function getAdminUser() {
    try {
        return JSON.parse(localStorage.getItem(USER_KEY));
    } catch {
        return null;
    }
}

function getJWT() {
    return localStorage.getItem(JWT_KEY);
}

function setAdminSession(token, user) {
    localStorage.setItem(JWT_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearAdminSession() {
    localStorage.removeItem(JWT_KEY);
    localStorage.removeItem(USER_KEY);
}

async function loginAdmin(username, password) {
    try {
        const res = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.error || 'Error de autenticación');
        }
        
        if (!data.token || !data.user) {
            throw new Error('Respuesta inválida del servidor');
        }
        
        setAdminSession(data.token, data.user);
        return data.user;
    } catch (error) {
        console.error('Error en login:', error);
        throw error;
    }
}

function updateUIForRole() {
    const isAdmin = isAdminLoggedIn();
    const user = getAdminUser();

    // Mostrar/ocultar login/logout
    document.getElementById('loginNavItem').classList.toggle('d-none', isAdmin);
    document.getElementById('logoutNavItem').classList.toggle('d-none', !isAdmin);

    // Mostrar nombre de usuario solo si es admin
    document.getElementById('adminUserLabel').textContent = isAdmin && user
        ? `Admin: ${user.username}`
        : (isAdmin ? '' : 'Empleado');

    // Mostrar/ocultar botones de administración
    document.querySelectorAll('.admin-only').forEach(btn => {
        btn.style.display = isAdmin ? '' : 'none';
    });

    // El botón de "Nuevo Producto" siempre visible
    const btnNuevoProducto = document.querySelector('[data-bs-target="#nuevoProductoModal"]');
    if (btnNuevoProducto) btnNuevoProducto.style.display = '';
}

function showApp() {
    const appContainer = document.getElementById('appContainer');
    if (appContainer) appContainer.style.display = 'block';
}

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    const targetSection = document.getElementById(sectionId + 'Section');
    if (targetSection) targetSection.style.display = 'block';
}

function showAlert(message, type = 'success') {
    const alertContainer = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertContainer.appendChild(alert);
    setTimeout(() => alert.remove(), 4000);
}

// Función auxiliar para hacer peticiones a la API
async function apiRequest(url, options = {}) {
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'X-API-Token': API_TOKEN
    };
    if (isAdminLoggedIn()) {
        defaultHeaders['Authorization'] = 'Bearer ' + getJWT();
    }
    const finalOptions = { ...options, headers: { ...defaultHeaders, ...(options.headers || {}) } };
    console.log('URL de la petición:', url);
    console.log('Método de la petición:', finalOptions.method || 'GET');
    console.log('Headers completos:', finalOptions.headers);
    if (finalOptions.body) {
        console.log('Body de la petición:', finalOptions.body);
    }
    
    try {
        const response = await fetch(url, finalOptions);
        console.log('Status de la respuesta:', response.status);
        console.log('Headers de la respuesta:', Object.fromEntries(response.headers.entries()));
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error en la respuesta:', errorText);
            throw new Error(`Error en la petición: ${response.statusText} - ${errorText}`);
        }
        
        // Si la respuesta es 204 (No Content), retornar null
        if (response.status === 204) {
            return null;
        }
        
        // Intentar parsear la respuesta como JSON
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            console.log('Datos de la respuesta:', data);
            return data;
        }
        
        // Si no es JSON, retornar el texto
        const text = await response.text();
        console.log('Respuesta de texto:', text);
        return text;
    } catch (error) {
        console.error('Error completo:', error);
        throw error;
    }
}

// Obtener productos
async function obtenerProductos() {
    return await apiRequest(`${API_URL}/productos`);
}

// Crear producto
async function crearProductoAPI(producto) {
    return await apiRequest(`${API_URL}/productos`, {
        method: 'POST',
        body: JSON.stringify(producto)
    });
}

// Actualizar producto
async function actualizarProductoAPI(id, producto) {
    return await apiRequest(`${API_URL}/productos/${id}`, {
        method: 'PUT',
        body: JSON.stringify(producto)
    });
}

// Eliminar producto
async function eliminarProductoAPI(id) {
    return await apiRequest(`${API_URL}/productos/${id}`, {
        method: 'DELETE'
    });
}

// Mostrar productos en la tabla
function mostrarProductos(productos) {
    const tbody = document.getElementById('productosTableBody');
    tbody.innerHTML = '';
    productos.forEach(producto => {
        const estado = producto.cantidad <= producto.umbral_reorden ?
            '<span class="badge bg-danger">Bajo</span>' :
            '<span class="badge bg-success">OK</span>';
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${producto.sku || ''}</td>
            <td>${producto.nombre}</td>
            <td>${producto.categoria || ''}</td>
            <td>${producto.precio_costo !== undefined ? producto.precio_costo : ''}</td>
            <td>${producto.precio_venta !== undefined ? producto.precio_venta : ''}</td>
            <td>${producto.cantidad}</td>
            <td>${producto.umbral_reorden}</td>
            <td>${estado}</td>
            <td>
                <button class="btn btn-sm btn-danger admin-only" onclick="eliminarProducto(${producto.id})">
                    <i class="bi bi-trash"></i> Eliminar
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    updateUIForRole();
}

// Cargar productos
async function cargarProductos() {
    try {
        const productos = await obtenerProductos();
        productosCargados = productos;
        mostrarProductos(productos);
        llenarSelectCategorias();
        return productos;
    } catch (error) {
        showAlert('Error al cargar productos', 'danger');
    }
}

// Manejar envío de nuevo producto
async function manejarNuevoProducto(event) {
    event.preventDefault();
    const form = event.target;
    const producto = {
        nombre: form.nombre.value,
        sku: form.sku ? form.sku.value : '',
        precio_costo: form.precio_costo ? parseFloat(form.precio_costo.value) : 0,
        precio_venta: form.precio_venta ? parseFloat(form.precio_venta.value) : 0,
        descripcion: form.descripcion ? form.descripcion.value : '',
        cantidad: form.cantidad ? parseInt(form.cantidad.value) : 0,
        umbral_reorden: form.umbral_reorden ? parseInt(form.umbral_reorden.value) : 10,
        categoria_id: form.categoria ? (form.categoria.value || null) : null
    };
    try {
        await crearProductoAPI(producto);
        form.reset();
        await cargarProductos();
        showAlert('Producto creado exitosamente');
        const modal = bootstrap.Modal.getInstance(document.getElementById('nuevoProductoModal'));
        if (modal) modal.hide();
    } catch (error) {
        showAlert('Error al crear producto: ' + error.message, 'danger');
    }
}

// Editar producto
async function editarProducto(id) {
    try {
        const productos = await obtenerProductos();
        const producto = productos.find(p => p.id === id);
        if (!producto) throw new Error('Producto no encontrado');
        const form = document.getElementById('editarProductoForm');

        // Llenar el select de categorías y seleccionar la actual
        await llenarSelectCategorias();
        if (form.editCategoria) {
            form.editCategoria.value = producto.categoria_id || '';
        }

        form.editProductoId.value = producto.id;
        form.editNombre.value = producto.nombre;
        form.editSKU.value = producto.sku || '';
        form.editPrecioCosto.value = producto.precio_costo !== undefined ? producto.precio_costo : '';
        form.editPrecioVenta.value = producto.precio_venta !== undefined ? producto.precio_venta : '';
        form.editDescripcion.value = producto.descripcion || '';
        form.editCantidad.value = producto.cantidad;
        form.editUmbral.value = producto.umbral_reorden;

        const modal = new bootstrap.Modal(document.getElementById('editarProductoModal'));
        modal.show();
    } catch (error) {
        showAlert('Error al cargar producto', 'danger');
    }
}
window.editarProducto = editarProducto;

// Manejar envío de edición
async function manejarEditarProducto(event) {
    event.preventDefault();
    const form = event.target;
    const id = form.editProductoId.value;
    const producto = {
        nombre: form.editNombre.value,
        sku: form.editSKU.value,
        precio_costo: parseFloat(form.editPrecioCosto.value),
        precio_venta: parseFloat(form.editPrecioVenta.value),
        descripcion: form.editDescripcion.value,
        cantidad: parseInt(form.editCantidad.value),
        umbral_reorden: parseInt(form.editUmbral.value),
        categoria_id: form.editCategoria.value || null
    };
    try {
        await actualizarProductoAPI(id, producto);
        await cargarProductos();
        showAlert('Producto actualizado');
        const modal = bootstrap.Modal.getInstance(document.getElementById('editarProductoModal'));
        modal.hide();
    } catch (error) {
        showAlert('Error al actualizar producto', 'danger');
    }
}

// Eliminar producto
async function eliminarProducto(id) {
    if (!confirm('¿Seguro que deseas eliminar este producto?')) return;
    try {
        await eliminarProductoAPI(id);
        await cargarProductos();
        showAlert('Producto eliminado');
    } catch (error) {
        showAlert('Error al eliminar producto', 'danger');
    }
}
window.eliminarProducto = eliminarProducto;

// --- FILTRADO DE PRODUCTOS ---

// 1. Listeners para los filtros (agrega esto en tu DOMContentLoaded)
document.getElementById('searchNombre').addEventListener('input', filtrarProductos);
document.getElementById('searchSKU').addEventListener('input', filtrarProductos);
document.getElementById('searchCategoria').addEventListener('change', filtrarProductos);

// 2. Función de filtrado
function filtrarProductos() {
    const nombre = document.getElementById('searchNombre').value.toLowerCase();
    const sku = document.getElementById('searchSKU').value.toLowerCase();
    const categoria = document.getElementById('searchCategoria').value;

    const filtrados = productosCargados.filter(producto => {
        const coincideNombre = producto.nombre.toLowerCase().includes(nombre);
        const coincideSKU = producto.sku && producto.sku.toLowerCase().includes(sku);
        const coincideCategoria = !categoria || (producto.categoria_id && String(producto.categoria_id) === categoria);
        return coincideNombre && coincideSKU && coincideCategoria;
    });

    mostrarProductos(filtrados);
}

// 3. Llenar el select de categorías correctamente
async function llenarSelectCategorias() {
    try {
        const categorias = await obtenerCategorias();
        
        // Llenar el select de búsqueda (por id)
        const selectBusqueda = document.getElementById('searchCategoria');
        selectBusqueda.innerHTML = '<option value="">Todas las categorías</option>' +
            categorias.map(cat => `<option value="${cat.id}">${cat.nombre_categoria}</option>`).join('');

        // Llenar el select del formulario de nuevo producto (por id)
        const selectNuevoProducto = document.getElementById('categoria');
        if (selectNuevoProducto) {
            selectNuevoProducto.innerHTML = '<option value="">Sin categoría</option>' +
                categorias.map(cat => `<option value="${cat.id}">${cat.nombre_categoria}</option>`).join('');
        }
    } catch (error) {
        showAlert('Error al cargar categorías', 'danger');
    }
}



// Obtener categorías
async function obtenerCategorias() {
    return await apiRequest(`${API_URL}/categorias`);
}

// Crear categoría
async function crearCategoriaAPI(categoria) {
    return await apiRequest(`${API_URL}/categorias`, {
        method: 'POST',
        body: JSON.stringify(categoria)
    });
}

// Actualizar categoría
async function actualizarCategoriaAPI(id, categoria) {
    return await apiRequest(`${API_URL}/categorias/${id}`, {
        method: 'PUT',
        body: JSON.stringify(categoria)
    });
}

// Eliminar categoría
async function eliminarCategoriaAPI(id) {
    return await apiRequest(`${API_URL}/categorias/${id}`, {
        method: 'DELETE'
    });
}

// Cargar categorías
async function cargarCategorias() {
    try {
        const categorias = await obtenerCategorias();
        mostrarCategorias(categorias);
        return categorias;
    } catch (error) {
        showAlert('Error al cargar categorías', 'danger');
    }
}

// Mostrar categorías en la tabla
function mostrarCategorias(categorias) {
    const tbody = document.getElementById('categoriasTableBody');
    tbody.innerHTML = categorias.map(cat => `
        <tr>
            <td>${cat.id}</td>
            <td>${cat.nombre_categoria}</td>
            <td>
                <button class="btn btn-sm btn-danger admin-only" onclick="eliminarCategoria(${cat.id})">
                    <i class="bi bi-trash"></i> Eliminar
                </button>
            </td>
        </tr>
    `).join('');
    updateUIForRole();
}

// Manejar envío de nueva categoría
async function manejarNuevaCategoria(event) {
    event.preventDefault();
    const form = event.target;
    const categoria = {
        nombre_categoria: form.nombreCategoria.value
    };
    try {
        await crearCategoriaAPI(categoria);
        form.reset();
        await cargarCategorias();
        showAlert('Categoría creada exitosamente');
        const modal = bootstrap.Modal.getInstance(document.getElementById('nuevaCategoriaModal'));
        if (modal) modal.hide();
    } catch (error) {
        showAlert('Error al crear categoría: ' + error.message, 'danger');
    }
}

// Editar categoría
async function editarCategoria(id) {
    try {
        const categorias = await obtenerCategorias();
        const categoria = categorias.find(c => c.id === id);
        if (!categoria) throw new Error('Categoría no encontrada');
        const form = document.getElementById('editarCategoriaForm');
        form.editCategoriaId.value = categoria.id;
        form.editNombreCategoria.value = categoria.nombre_categoria;
        const modal = new bootstrap.Modal(document.getElementById('editarCategoriaModal'));
        modal.show();
    } catch (error) {
        showAlert('Error al cargar categoría', 'danger');
    }
}
window.editarCategoria = editarCategoria;

// Manejar envío de edición de categoría
async function manejarEditarCategoria(event) {
    event.preventDefault();
    const form = event.target;
    const id = form.editCategoriaId.value;
    const categoria = {
        nombre_categoria: form.editNombreCategoria.value
    };
    try {
        await actualizarCategoriaAPI(id, categoria);
        await cargarCategorias();
        showAlert('Categoría actualizada');
        const modal = bootstrap.Modal.getInstance(document.getElementById('editarCategoriaModal'));
        modal.hide();
    } catch (error) {
        showAlert('Error al actualizar categoría', 'danger');
    }
}

// Eliminar categoría
async function eliminarCategoria(id) {
    if (!confirm('¿Seguro que deseas eliminar esta categoría?')) return;
    try {
        await eliminarCategoriaAPI(id);
        await cargarCategorias();
        showAlert('Categoría eliminada');
    } catch (error) {
        showAlert('Error al eliminar categoría', 'danger');
    }
}
window.eliminarCategoria = eliminarCategoria;

// Obtener proveedores
async function obtenerProveedores() {
    return await apiRequest(`${API_URL}/proveedores`);
}

// Crear proveedor
async function crearProveedorAPI(proveedor) {
    return await apiRequest(`${API_URL}/proveedores`, {
        method: 'POST',
        body: JSON.stringify(proveedor)
    });
}

// Actualizar proveedor
async function actualizarProveedorAPI(id, proveedor) {
    return await apiRequest(`${API_URL}/proveedores/${id}`, {
        method: 'PUT',
        body: JSON.stringify(proveedor)
    });
}

// Eliminar proveedor
async function eliminarProveedorAPI(id) {
    return await apiRequest(`${API_URL}/proveedores/${id}`, {
        method: 'DELETE'
    });
}

// Cargar proveedores
async function cargarProveedores() {
    try {
        const proveedores = await obtenerProveedores();
        mostrarProveedores(proveedores);
        return proveedores;
    } catch (error) {
        showAlert('Error al cargar proveedores', 'danger');
    }
}

// Mostrar proveedores en la tabla
function mostrarProveedores(proveedores) {
    const tbody = document.getElementById('proveedoresTableBody');
    tbody.innerHTML = proveedores.map(prov => `
        <tr>
            <td>${prov.id}</td>
            <td>${prov.nombre}</td>
            <td>${prov.email || ''}</td>
            <td>${prov.telefono || ''}</td>
            <td>
                <button class="btn btn-sm btn-danger admin-only" onclick="eliminarProveedor(${prov.id})">
                    <i class="bi bi-trash"></i> Eliminar
                </button>
            </td>
        </tr>
    `).join('');
    updateUIForRole();
}

// Manejar envío de nuevo proveedor
async function manejarNuevoProveedor(event) {
    event.preventDefault();
    const form = event.target;
    const proveedor = {
        nombre: form.nombreProveedor.value,
        email: form.emailProveedor.value,
        telefono: form.telefonoProveedor.value
    };
    try {
        await crearProveedorAPI(proveedor);
        form.reset();
        await cargarProveedores();
        showAlert('Proveedor creado exitosamente');
        const modal = bootstrap.Modal.getInstance(document.getElementById('nuevoProveedorModal'));
        if (modal) modal.hide();
    } catch (error) {
        showAlert('Error al crear proveedor: ' + error.message, 'danger');
    }
}

// Editar proveedor
async function editarProveedor(id) {
    try {
        const proveedores = await obtenerProveedores();
        const proveedor = proveedores.find(p => p.id === id);
        if (!proveedor) throw new Error('Proveedor no encontrado');
        const form = document.getElementById('editarProveedorForm');
        form.editProveedorId.value = proveedor.id;
        form.editNombreProveedor.value = proveedor.nombre;
        form.editEmailProveedor.value = proveedor.email || '';
        form.editTelefonoProveedor.value = proveedor.telefono || '';
        const modal = new bootstrap.Modal(document.getElementById('editarProveedorModal'));
        modal.show();
    } catch (error) {
        showAlert('Error al cargar proveedor', 'danger');
    }
}
window.editarProveedor = editarProveedor;

// Manejar envío de edición de proveedor
async function manejarEditarProveedor(event) {
    event.preventDefault();
    const form = event.target;
    const id = form.editProveedorId.value;
    const proveedor = {
        nombre: form.editNombreProveedor.value,
        email: form.editEmailProveedor.value,
        telefono: form.editTelefonoProveedor.value
    };
    try {
        await actualizarProveedorAPI(id, proveedor);
        await cargarProveedores();
        showAlert('Proveedor actualizado');
        const modal = bootstrap.Modal.getInstance(document.getElementById('editarProveedorModal'));
        modal.hide();
    } catch (error) {
        showAlert('Error al actualizar proveedor', 'danger');
    }
}

// Eliminar proveedor
async function eliminarProveedor(id) {
    if (!confirm('¿Seguro que deseas eliminar este proveedor?')) return;
    try {
        await eliminarProveedorAPI(id);
        await cargarProveedores();
        showAlert('Proveedor eliminado');
    } catch (error) {
        showAlert('Error al eliminar proveedor', 'danger');
    }
}
window.eliminarProveedor = eliminarProveedor;

async function llenarSelectProductos(selectElement) {
    try {
        const productos = await obtenerProductos();
        console.log('Productos cargados:', productos);
        selectElement.innerHTML = '<option value="">Seleccione un producto</option>';
        productos.forEach(prod => {
            selectElement.innerHTML += `<option value="${prod.id}">${prod.nombre}</option>`;
        });
    } catch (error) {
        showAlert('Error al cargar productos', 'danger');
    }
}

async function llenarSelectProveedores(selectElement) {
    try {
        const proveedores = await obtenerProveedores();
        selectElement.innerHTML = '<option value="">Seleccione un proveedor</option>';
        proveedores.forEach(prov => {
            selectElement.innerHTML += `<option value="${prov.id}">${prov.nombre}</option>`;
        });
    } catch (error) {
        showAlert('Error al cargar proveedores', 'danger');
    }
}

async function manejarNuevaOrdenCompra(event) {
    event.preventDefault();
    const form = event.target;
    const proveedorId = form.querySelector('select[name="proveedor"]').value;
    let fechaEntrega = form.querySelector('#fechaEntrega').value;

    // CORRECCIÓN DE FORMATO DE FECHA
    if (fechaEntrega) {
        // Si solo viene YYYY-MM-DD, agrega la hora
        if (!fechaEntrega.includes('T')) {
            fechaEntrega = fechaEntrega + 'T00:00:00';
        }
    } else {
        fechaEntrega = null;
    }

    // Obtener los items de la orden
    const items = [];
    form.querySelectorAll('#itemsOrdenContainer .row').forEach(row => {
        const productoId = row.querySelector('.item-producto').value;
        const cantidad = row.querySelector('.item-cantidad').value;
        const precio = row.querySelector('.item-precio').value;
        if (productoId && cantidad && precio) {
            items.push({
                producto_id: parseInt(productoId),
                cantidad: parseInt(cantidad),
                precio_unitario: parseFloat(precio)
            });
        }
    });

    if (!proveedorId || items.length === 0) {
        showAlert('Debe seleccionar un proveedor y al menos un producto.', 'danger');
        return;
    }

    const orden = {
        proveedor_id: parseInt(proveedorId),
        fecha_entrega: fechaEntrega,
        items: items
    };

    try {
        await crearOrdenCompraAPI(orden);
        showAlert('Orden de compra creada exitosamente');
        form.reset();
        document.getElementById('itemsOrdenContainer').innerHTML = '';
        const modal = bootstrap.Modal.getInstance(document.getElementById('nuevaOrdenCompraModal'));
        if (modal) modal.hide();
        await cargarOrdenesCompra();
    } catch (error) {
        showAlert('Error al crear la orden: ' + error.message, 'danger');
    }
}

// Crear orden de compra
async function crearOrdenCompraAPI(orden) {
    return await apiRequest(`${API_URL}/ordenes-compra`, {
        method: 'POST',
        body: JSON.stringify(orden)
    });
}

// Obtener órdenes de compra
async function obtenerOrdenesCompra() {
    return await apiRequest(`${API_URL}/ordenes-compra`);
}

function mostrarOrdenesCompra(ordenes) {
    const tbody = document.getElementById('ordenesCompraTableBody');
    tbody.innerHTML = '';
    ordenes.forEach(orden => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${orden.id}</td>
            <td>${orden.proveedor}</td>
            <td>${orden.fecha_creacion ? orden.fecha_creacion.split('T')[0] : ''}</td>
            <td>${orden.fecha_entrega ? orden.fecha_entrega.split('T')[0] : ''}</td>
            <td>${orden.estado}</td>
            <td>
                <button class="btn btn-sm btn-warning me-2 admin-only" onclick="verDetalleOrden(${orden.id})">
                    <i class="bi bi-eye"></i> Ver
                </button>
                <button class="btn btn-sm btn-danger admin-only" onclick="eliminarOrdenCompra(${orden.id})">
                    <i class="bi bi-trash"></i> Eliminar
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    updateUIForRole();
}

async function cargarOrdenesCompra() {
    try {
        const ordenes = await obtenerOrdenesCompra();
        mostrarOrdenesCompra(ordenes);
    } catch (error) {
        showAlert('Error al cargar órdenes de compra', 'danger');
    }
}

async function verDetalleOrden(id) {
    try {
        // Pide el detalle directamente al backend
        const orden = await apiRequest(`${API_URL}/ordenes-compra/${id}`);
        console.log('Orden seleccionada:', orden);
        if (!orden) throw new Error('Orden no encontrada');

        // Info general
        const infoDiv = document.getElementById('detalleOrdenInfo');
        infoDiv.innerHTML = `
            <b>Proveedor:</b> ${orden.proveedor}<br>
            <b>Fecha de entrega:</b> ${orden.fecha_entrega ? orden.fecha_entrega.split('T')[0] : 'No especificada'}<br>
            <b>Estado:</b>
            <select id="selectEstadoOrden" class="form-select form-select-sm" style="width:auto;display:inline-block;">
                <option value="pendiente" ${orden.estado === 'pendiente' ? 'selected' : ''}>Pendiente</option>
                <option value="completada" ${orden.estado === 'completada' ? 'selected' : ''}>Completada</option>
                <option value="cancelada" ${orden.estado === 'cancelada' ? 'selected' : ''}>Cancelada</option>
            </select>
            <button class="btn btn-sm btn-primary ms-2" onclick="cambiarEstadoOrden(${orden.id}, document.getElementById('selectEstadoOrden').value)">Guardar</button>
        `;

        // Items
        const itemsTbody = document.getElementById('detalleOrdenItems');
        if (!orden.items || orden.items.length === 0) {
            itemsTbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">Sin productos en esta orden</td></tr>`;
        } else {
            itemsTbody.innerHTML = orden.items.map(item => `
                <tr>
                    <td>${item.producto}</td>
                    <td>${item.cantidad}</td>
                    <td>$${item.precio_unitario}</td>
                    <td>$${item.subtotal}</td>
                </tr>
            `).join('');
        }

        // Total
        const total = orden.total !== undefined
            ? orden.total
            : (orden.items || []).reduce((acc, item) => acc + (item.subtotal || 0), 0);
        document.getElementById('detalleOrdenTotal').textContent = `$${total}`;

        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('detalleOrdenModal'));
        modal.show();
    } catch (error) {
        showAlert('Error al mostrar detalle de la orden', 'danger');
    }
}
window.verDetalleOrden = verDetalleOrden;

// Cambiar estado de orden
async function cambiarEstadoOrden(id, nuevoEstado) {
    return await apiRequest(`${API_URL}/ordenes-compra/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ estado: nuevoEstado })
    });
}

async function cargarInventarioValorado() {
    try {
        const response = await fetch(`${API_URL}/productos`);
        if (!response.ok) throw new Error('Error al obtener productos');
        const productos = await response.json();

        const tbody = document.getElementById('inventarioValoradoBody');
        const totalInventarioCell = document.getElementById('totalInventario');
        tbody.innerHTML = '';
        let totalInventario = 0;

        productos.forEach(producto => {
            const valorTotal = producto.cantidad * producto.precio_costo;
            totalInventario += valorTotal;
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${producto.nombre}</td>
                <td>${producto.cantidad}</td>
                <td>$${producto.precio_costo.toFixed(2)}</td>
                <td>$${valorTotal.toFixed(2)}</td>
            `;
            tbody.appendChild(tr);
        });

        totalInventarioCell.textContent = `$${totalInventario.toFixed(2)}`;
    } catch (error) {
        showAlert('Error al cargar inventario valorado', 'danger');
    }
}

async function cargarReporteMovimientos() {
    console.log('Entrando a cargarReporteMovimientos');
    console.log('API_URL:', API_URL);

    const fechaInicio = document.getElementById('fechaInicio')?.value;
    const fechaFin = document.getElementById('fechaFin')?.value;
    let url = `${API_URL}/reportes/movimientos`;
    const params = [];
    if (fechaInicio) params.push(`fecha_inicio=${fechaInicio}`);
    if (fechaFin) params.push(`fecha_fin=${fechaFin}`);
    if (params.length) url += '?' + params.join('&');

    console.log('URL de reporte:', url);

    try {
        const response = await fetch(url);
        console.log('Fetch ejecutado, response:', response);
        if (!response.ok) throw new Error('Error al obtener movimientos');
        const movimientos = await response.json();
        console.log('Movimientos recibidos:', movimientos);
        mostrarMovimientos(movimientos);
    } catch (error) {
        console.error('Error en cargarReporteMovimientos:', error);
        showAlert('Error al cargar reporte de movimientos: ' + error.message, 'danger');
    }
}

function mostrarMovimientos(movimientos) {
    const tbody = document.getElementById('ventasUsoBody');
    tbody.innerHTML = '';
    if (!Array.isArray(movimientos) || movimientos.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Sin movimientos en este periodo</td></tr>`;
        return;
    }
    movimientos.forEach(mov => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${mov.fecha ? mov.fecha.split('T')[0] : ''}</td>
            <td>${mov.producto || ''}</td>
            <td>${mov.tipo || ''}</td>
            <td>${mov.cantidad || ''}</td>
            <td>${mov.usuario || ''}</td>
        `;
        tbody.appendChild(tr);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    updateUIForRole();
    cargarProductos();

    // Evento logout
    document.getElementById('btnLogout').addEventListener('click', () => {
        clearAdminSession();
        updateUIForRole();
        showApp();
        cargarProductos();
    });

    // Evento login
    document.getElementById('loginForm').addEventListener('submit', async function(event) {
        event.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        const loginError = document.getElementById('loginError');
        try {
            await loginAdmin(username, password);
            updateUIForRole();
            showApp();
            cargarProductos();
            // Cierra el modal de login
            const loginModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('loginModal'));
            loginModal.hide();
            // Limpia errores
            loginError.classList.add('d-none');
            loginError.textContent = '';
            // --- AGREGA SOLO AQUÍ ---
            const user = getAdminUser();
            showAlert(`¡Bienvenido, ${user.username}! Has iniciado sesión como administrador.`, 'success');
        } catch (error) {
            loginError.textContent = 'Credenciales inválidas';
            loginError.classList.remove('d-none');
        }
    });

    // Limpia el mensaje de error al abrir el modal de login
    document.getElementById('loginModal').addEventListener('show.bs.modal', () => {
        const loginError = document.getElementById('loginError');
        loginError.classList.add('d-none');
        loginError.textContent = '';
    });

    // Limpia error también al hacer clic en el botón de login
    document.getElementById('btnLogin').addEventListener('click', () => {
        const loginError = document.getElementById('loginError');
        loginError.classList.add('d-none');
        loginError.textContent = '';
    });

    // Navegación entre secciones
    document.querySelectorAll('[data-section]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            showSection(section);

            // Cargar datos según la sección seleccionada
            if (section === 'categorias') cargarCategorias();
            if (section === 'proveedores') cargarProveedores();
            if (section === 'ordenes-compra') cargarOrdenesCompra();
            if (section === 'inventario') cargarProductos();
            if (section === 'reportes') {
                cargarInventarioValorado();
                cargarReporteMovimientos();
            }
        });
    });

    // Conectar formulario de nuevo producto
    const nuevoProductoForm = document.getElementById('nuevoProductoForm');
    if (nuevoProductoForm) {
        nuevoProductoForm.addEventListener('submit', manejarNuevoProducto);
    }

    // Conectar formulario de nueva categoría
    const nuevaCategoriaForm = document.getElementById('nuevaCategoriaForm');
    if (nuevaCategoriaForm) {
        nuevaCategoriaForm.addEventListener('submit', manejarNuevaCategoria);
    }

    // Conectar formulario de nuevo proveedor
    const nuevoProveedorForm = document.getElementById('nuevoProveedorForm');
    if (nuevoProveedorForm) {
        nuevoProveedorForm.addEventListener('submit', manejarNuevoProveedor);
    }

    // Conectar formulario de nueva orden de compra
    const nuevaOrdenCompraForm = document.getElementById('nuevaOrdenCompraForm');
    if (nuevaOrdenCompraForm) {
        nuevaOrdenCompraForm.addEventListener('submit', manejarNuevaOrdenCompra);
    }

    // Llenar select de proveedores al abrir el modal de nueva orden de compra
    const nuevaOrdenCompraModal = document.getElementById('nuevaOrdenCompraModal');
    if (nuevaOrdenCompraModal) {
        nuevaOrdenCompraModal.addEventListener('show.bs.modal', () => {
            const selectProveedor = nuevaOrdenCompraModal.querySelector('select[name="proveedor"]');
            if (selectProveedor) llenarSelectProveedores(selectProveedor);

            // Llenar todos los selects de productos existentes en los ítems
            nuevaOrdenCompraModal.querySelectorAll('#itemsOrdenContainer .item-producto').forEach(llenarSelectProductos);
        });
    }

    // --- AGREGA ESTO ---
    const btnGenerarReporte = document.getElementById('btnGenerarReporte');
    if (btnGenerarReporte) {
        btnGenerarReporte.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Botón Generar Reporte clickeado');
            cargarReporteMovimientos();
        });
    }

    // Llenar el select de productos
    async function llenarSelectProductosMovimiento() {
        const select = document.getElementById('productoMovimiento');
        if (!select) return;
        try {
            const response = await fetch(`${API_URL}/productos`);
            const productos = await response.json();
            select.innerHTML = productos.map(p =>
                `<option value="${p.id}">${p.nombre}</option>`
            ).join('');
        } catch (e) {
            select.innerHTML = '<option value="">Error al cargar productos</option>';
        }
    }
    llenarSelectProductosMovimiento();

    // Manejar el submit del formulario de movimiento
    const formMovimiento = document.getElementById('formMovimientoInventario');
    if (formMovimiento) {
        formMovimiento.addEventListener('submit', async function(e) {
            e.preventDefault();
            const data = {
                producto_id: document.getElementById('productoMovimiento').value,
                tipo: document.getElementById('tipoMovimiento').value,
                cantidad: document.getElementById('cantidadMovimiento').value,
                usuario: document.getElementById('usuarioMovimiento').value
            };
            try {
                const response = await fetch(`${API_URL}/movimientos`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                if (!response.ok) throw new Error('Error al registrar movimiento');
                showAlert('Movimiento registrado correctamente', 'success');
                cargarReporteMovimientos(); // Actualiza el reporte
                formMovimiento.reset();
            } catch (error) {
                showAlert('Error al registrar movimiento: ' + error.message, 'danger');
            }
        });
    }
});

// Exposición de funciones globales necesarias para el HTML inline
window.loginAdmin = loginAdmin;
window.updateUIForRole = updateUIForRole;
window.clearAdminSession = clearAdminSession;
window.showApp = showApp;
window.cargarProductos = cargarProductos;
window.llenarSelectCategorias = llenarSelectCategorias;
window.showSection = showSection;

function agregarItemOrden() {
    const container = document.getElementById('itemsOrdenContainer');
    const row = document.createElement('div');
    row.className = 'row mb-2';

    row.innerHTML = `
        <div class="col">
            <select class="form-select item-producto"></select>
        </div>
        <div class="col">
            <input type="number" class="form-control item-cantidad" min="1" placeholder="Cantidad">
        </div>
        <div class="col">
            <input type="number" class="form-control item-precio" min="0" step="0.01" placeholder="Precio U">
        </div>
        <div class="col-auto">
            <button type="button" class="btn btn-danger" onclick="this.closest('.row').remove()">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `;
    container.appendChild(row);

    // Llenar el select de productos de este nuevo item
    const selectProducto = row.querySelector('.item-producto');
    llenarSelectProductos(selectProducto);
}
window.agregarItemOrden = agregarItemOrden;