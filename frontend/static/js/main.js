// Configuración de la API
const API_URL = 'http://localhost:5000/api';

let productosCargados = [];

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
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(producto)
    });
    if (!response.ok) throw new Error('Error al crear producto');
    return await response.json();
}

// Actualizar producto
async function actualizarProductoAPI(id, producto) {
    const response = await fetch(`${API_URL}/productos/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(producto)
    });
    if (!response.ok) throw new Error('Error al actualizar producto');
    return await response.json();
}

// Eliminar producto
async function eliminarProductoAPI(id) {
    const response = await fetch(`${API_URL}/productos/${id}`, {
        method: 'DELETE'
    });
    if (!response.ok) throw new Error('Error al eliminar producto');
    return true;
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
                <button class="btn btn-sm btn-warning me-1" onclick="editarProducto(${producto.id})">Editar</button>
                <button class="btn btn-sm btn-danger" onclick="eliminarProducto(${producto.id})">Eliminar</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
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

function filtrarProductos() {
    const nombre = document.getElementById('searchNombre').value.toLowerCase();
    const sku = document.getElementById('searchSKU').value.toLowerCase();
    const categoria = document.getElementById('searchCategoria').value;

    const filtrados = productosCargados.filter(producto => {
        const coincideNombre = producto.nombre.toLowerCase().includes(nombre);
        const coincideSKU = producto.sku && producto.sku.toLowerCase().includes(sku);
        const coincideCategoria = !categoria || (producto.categoria && producto.categoria == categoria);
        return coincideNombre && coincideSKU && coincideCategoria;
    });

    mostrarProductos(filtrados);
}

function llenarSelectCategorias() {
    const select = document.getElementById('searchCategoria');
    const categorias = [...new Set(productosCargados.map(p => p.categoria).filter(Boolean))];
    select.innerHTML = '<option value="">Todas las categorías</option>' +
        categorias.map(cat => `<option value="${cat}">${cat}</option>`).join('');
}

document.addEventListener('DOMContentLoaded', () => {
    showApp();
    cargarProductos().then(llenarSelectCategorias);
    showSection('inventario');

    document.querySelectorAll('.nav-link[data-section]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = e.target.dataset.section;
            showSection(section);
        });
    });

    const nuevoProductoForm = document.getElementById('nuevoProductoForm');
    if (nuevoProductoForm) {
        nuevoProductoForm.addEventListener('submit', manejarNuevoProducto);
    }
    const editarProductoForm = document.getElementById('editarProductoForm');
    if (editarProductoForm) {
        editarProductoForm.addEventListener('submit', manejarEditarProducto);
    }

    document.getElementById('searchNombre').addEventListener('input', filtrarProductos);
    document.getElementById('searchSKU').addEventListener('input', filtrarProductos);
    document.getElementById('searchCategoria').addEventListener('change', filtrarProductos);
});
