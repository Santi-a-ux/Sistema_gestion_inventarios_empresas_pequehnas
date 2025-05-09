// Configuración de la API
const API_URL = '/api';

// Mostrar alertas
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

// Obtener productos
async function obtenerProductos() {
    const response = await fetch(`${API_URL}/productos`);
    if (!response.ok) throw new Error('Error al obtener productos');
    return await response.json();
}

// Crear producto
async function crearProductoAPI(producto) {
    const response = await fetch(`${API_URL}/productos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(producto)
    });
    if (!response.ok) throw new Error('Error al crear producto');
    return await response.json();
}

// Actualizar producto
async function actualizarProductoAPI(id, producto) {
    const response = await fetch(`${API_URL}/productos/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(producto)
    });
    if (!response.ok) throw new Error('Error al actualizar producto');
    return await response.json();
}

// Eliminar producto
async function eliminarProductoAPI(id) {
    const response = await fetch(`${API_URL}/productos/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Error al eliminar producto');
    return true;
}

// Obtener productos para reordenar
async function obtenerProductosReordenar() {
    const response = await fetch(`${API_URL}/productos/reordenar`);
    if (!response.ok) throw new Error('Error al obtener productos para reordenar');
    return await response.json();
}

// Botón Reordenar
async function manejarReordenar(event) {
    event.preventDefault();
    try {
        const productos = await obtenerProductosReordenar();
        if (productos.length === 0) {
            showAlert('No hay productos que necesiten reorden.', 'info');
            return;
        }
        let mensaje = '¡Atención! Los siguientes productos necesitan ser reordenados:\n\n';
        productos.forEach(p => {
            mensaje += `- ${p.nombre} (Stock: ${p.cantidad}, Umbral: ${p.umbral_reorden})\n`;
        });
        alert(mensaje);
    } catch (error) {
        showAlert('Error al obtener productos para reordenar', 'danger');
    }
}

// Mostrar productos en la tabla (con estado visual)
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
                <button class="btn btn-sm btn-warning me-1" onclick="editarProducto(${producto.id})">Editar</button>
                <button class="btn btn-sm btn-danger" onclick="eliminarProducto(${producto.id})">Eliminar</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Cargar productos al iniciar
async function cargarProductos() {
    try {
        const productos = await obtenerProductos();
        mostrarProductos(productos);
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
        cargarProductos();
        showAlert('Producto creado exitosamente');
        const modal = bootstrap.Modal.getInstance(document.getElementById('nuevoProductoModal'));
        if (modal) modal.hide();
    } catch (error) {
        showAlert('Error al crear producto: ' + error.message, 'danger');
    }
}

// Editar producto (abrir modal con datos)
async function editarProducto(id) {
    try {
        const productos = await obtenerProductos();
        const producto = productos.find(p => p.id === id);
        if (!producto) throw new Error('Producto no encontrado');
        const form = document.getElementById('editarProductoForm');
        form.editId.value = producto.id;
        form.editNombre.value = producto.nombre;
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
    const id = form.editId.value;
    const producto = {
        nombre: form.editNombre.value,
        descripcion: form.editDescripcion.value,
        cantidad: parseInt(form.editCantidad.value),
        umbral_reorden: parseInt(form.editUmbral.value)
    };
    try {
        await actualizarProductoAPI(id, producto);
        cargarProductos();
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
        cargarProductos();
        showAlert('Producto eliminado');
    } catch (error) {
        showAlert('Error al eliminar producto', 'danger');
    }
}
window.eliminarProducto = eliminarProducto;

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    // Mostrar siempre el contenedor principal
    const appContainer = document.getElementById('appContainer');
    if (appContainer) appContainer.style.display = 'block';
    const loginContainer = document.getElementById('loginContainer');
    if (loginContainer) loginContainer.style.display = 'none';
    cargarProductos();
    const nuevoProductoForm = document.getElementById('nuevoProductoForm');
    if (nuevoProductoForm) {
        nuevoProductoForm.addEventListener('submit', manejarNuevoProducto);
    }
    const editarProductoForm = document.getElementById('editarProductoForm');
    if (editarProductoForm) {
        editarProductoForm.addEventListener('submit', manejarEditarProducto);
    }
}); 