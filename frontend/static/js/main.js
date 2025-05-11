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

async function llenarSelectCategorias() {
    try {
        const categorias = await obtenerCategorias();
        
        // Llenar el select de búsqueda
        const selectBusqueda = document.getElementById('searchCategoria');
        selectBusqueda.innerHTML = '<option value="">Todas las categorías</option>' +
            categorias.map(cat => `<option value="${cat.nombre_categoria}">${cat.nombre_categoria}</option>`).join('');

        // Llenar el select del formulario de nuevo producto
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
    const response = await fetch(`${API_URL}/categorias`);
    if (!response.ok) throw new Error('Error al obtener categorías');
    return await response.json();
}

// Crear categoría
async function crearCategoriaAPI(categoria) {
    const response = await fetch(`${API_URL}/categorias`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(categoria)
    });
    if (!response.ok) throw new Error('Error al crear categoría');
    return await response.json();
}

// Actualizar categoría
async function actualizarCategoriaAPI(id, categoria) {
    const response = await fetch(`${API_URL}/categorias/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(categoria)
    });
    if (!response.ok) throw new Error('Error al actualizar categoría');
    return await response.json();
}

// Eliminar categoría
async function eliminarCategoriaAPI(id) {
    const response = await fetch(`${API_URL}/categorias/${id}`, {
        method: 'DELETE'
    });
    if (!response.ok) throw new Error('Error al eliminar categoría');
    return true;
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
                <button class="btn btn-sm btn-warning me-2" onclick="editarCategoria(${cat.id})">
                    <i class="bi bi-pencil"></i> Editar
                </button>
                <button class="btn btn-sm btn-danger" onclick="eliminarCategoria(${cat.id})">
                    <i class="bi bi-trash"></i> Eliminar
                </button>
            </td>
        </tr>
    `).join('');
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
        form.editId.value = categoria.id;
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
    const id = form.editId.value;
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
    const response = await fetch(`${API_URL}/proveedores`);
    if (!response.ok) throw new Error('Error al obtener proveedores');
    return await response.json();
}

// Crear proveedor
async function crearProveedorAPI(proveedor) {
    const response = await fetch(`${API_URL}/proveedores`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(proveedor)
    });
    if (!response.ok) throw new Error('Error al crear proveedor');
    return await response.json();
}

// Actualizar proveedor
async function actualizarProveedorAPI(id, proveedor) {
    const response = await fetch(`${API_URL}/proveedores/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(proveedor)
    });
    if (!response.ok) throw new Error('Error al actualizar proveedor');
    return await response.json();
}

// Eliminar proveedor
async function eliminarProveedorAPI(id) {
    const response = await fetch(`${API_URL}/proveedores/${id}`, {
        method: 'DELETE'
    });
    if (!response.ok) throw new Error('Error al eliminar proveedor');
    return true;
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
                <button class="btn btn-sm btn-warning me-2" onclick="editarProveedor(${prov.id})">
                    <i class="bi bi-pencil"></i> Editar
                </button>
                <button class="btn btn-sm btn-danger" onclick="eliminarProveedor(${prov.id})">
                    <i class="bi bi-trash"></i> Eliminar
                </button>
            </td>
        </tr>
    `).join('');
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
        form.editId.value = proveedor.id;
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
    const id = form.editId.value;
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
    const fechaEntrega = form.querySelector('#fechaEntrega').value;

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

async function crearOrdenCompraAPI(orden) {
    const response = await fetch(`${API_URL}/ordenes-compra`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(orden)
    });
    if (!response.ok) throw new Error('Error al crear orden de compra');
    return await response.json();
}

async function obtenerOrdenesCompra() {
    const response = await fetch(`${API_URL}/ordenes-compra`);
    if (!response.ok) throw new Error('Error al obtener órdenes de compra');
    return await response.json();
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
                <button class="btn btn-sm btn-warning me-2" onclick="verDetalleOrden(${orden.id})">
                    <i class="bi bi-eye"></i> Ver
                </button>
                <button class="btn btn-sm btn-danger" onclick="eliminarOrdenCompra(${orden.id})">
                    <i class="bi bi-trash"></i> Eliminar
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
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
        const ordenes = await obtenerOrdenesCompra();
        const orden = ordenes.find(o => o.id === id);
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

async function cambiarEstadoOrden(id, nuevoEstado) {
    await fetch(`${API_URL}/ordenes-compra/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ estado: nuevoEstado })
    });
    await cargarOrdenesCompra();
}

async function cargarInventarioValorado() {
    try {
        const response = await fetch('http://localhost:5000/api/productos');
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
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;
    let url = `${API_URL}/reportes/movimientos`;
    const params = [];
    if (fechaInicio) params.push(`fecha_inicio=${fechaInicio}`);
    if (fechaFin) params.push(`fecha_fin=${fechaFin}`);
    if (params.length) url += '?' + params.join('&');

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Error al obtener movimientos');
        const movimientos = await response.json();
        mostrarMovimientos(movimientos);
    } catch (error) {
        showAlert('Error al cargar reporte de movimientos', 'danger');
    }
}

function mostrarMovimientos(movimientos) {
    const tbody = document.getElementById('ventasUsoBody');
    tbody.innerHTML = '';
    if (movimientos.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Sin movimientos en este periodo</td></tr>`;
        return;
    }
    movimientos.forEach(mov => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${mov.fecha}</td>
            <td>${mov.producto}</td>
            <td>${mov.tipo}</td>
            <td>${mov.cantidad}</td>
            <td>${mov.usuario || ''}</td>
        `;
        tbody.appendChild(tr);
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    showApp();
    await cargarProductos();
    await llenarSelectCategorias();
    showSection('inventario');

    document.querySelectorAll('.nav-link[data-section]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = e.target.dataset.section;
            showSection(section);
            if (section === 'reportes') {
                cargarInventarioValorado();
            }
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

    cargarCategorias();
    const nuevaCategoriaForm = document.getElementById('nuevaCategoriaForm');
    if (nuevaCategoriaForm) {
        nuevaCategoriaForm.addEventListener('submit', manejarNuevaCategoria);
    }

    const editarCategoriaForm = document.getElementById('editarCategoriaForm');
    if (editarCategoriaForm) {
        editarCategoriaForm.addEventListener('submit', manejarEditarCategoria);
    }

    cargarProveedores();
    const nuevoProveedorForm = document.getElementById('nuevoProveedorForm');
    if (nuevoProveedorForm) {
        nuevoProveedorForm.addEventListener('submit', manejarNuevoProveedor);
    }

    const editarProveedorForm = document.getElementById('editarProveedorForm');
    if (editarProveedorForm) {
        editarProveedorForm.addEventListener('submit', manejarEditarProveedor);
    }

    const nuevaOrdenModal = document.getElementById('nuevaOrdenCompraModal');
    if (nuevaOrdenModal) {
        nuevaOrdenModal.addEventListener('show.bs.modal', () => {
            // Llenar proveedores
            const selectProveedor = nuevaOrdenModal.querySelector('select[name="proveedor"]');
            if (selectProveedor) {
                llenarSelectProveedores(selectProveedor);
            }
            // Llenar productos en la fila inicial
            const selectProductoInicial = nuevaOrdenModal.querySelector('.item-producto');
            if (selectProductoInicial) {
                llenarSelectProductos(selectProductoInicial);
            }
        });
    }

    document.getElementById('btnAgregarItem').addEventListener('click', () => {
        const nuevaFila = document.createElement('div');
        nuevaFila.className = 'row mb-2';
        nuevaFila.innerHTML = `
            <div class="col-md-4">
                <select class="form-select item-producto">
                    <option value="">Seleccione un producto</option>
                </select>
            </div>
            <div class="col-md-2">
                <input type="number" class="form-control item-cantidad" placeholder="Cantidad" min="1">
            </div>
            <div class="col-md-3">
                <input type="number" class="form-control item-precio" placeholder="Precio Unit." step="0.01" min="0">
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-danger btn-remove-item">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;
        document.getElementById('itemsOrdenContainer').appendChild(nuevaFila);

        // LLENAR EL SELECT DE PRODUCTOS
        const selectProducto = nuevaFila.querySelector('.item-producto');
        llenarSelectProductos(selectProducto);
    });

    const nuevaOrdenCompraForm = document.getElementById('nuevaOrdenCompraForm');
    if (nuevaOrdenCompraForm) {
        nuevaOrdenCompraForm.addEventListener('submit', manejarNuevaOrdenCompra);
    }

    await cargarOrdenesCompra();

    // Asocia el botón
    document.getElementById('btnGenerarReporte').addEventListener('click', cargarReporteMovimientos);
});
