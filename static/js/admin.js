let currentView = 'dashboard';
let allInventory = [];
let allLeads = [];
let allClosedLeads = [];

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    loadDashboardStats();
    loadInventory();
    loadLeads();
    loadClosedLeads();
    setupSearch();
    loadSheetUrl();
});

async function loadSheetUrl() {
    try {
        const response = await fetch('/api/sheet-url');
        const result = await response.json();
        if (result.success) {
            const sheetLink = document.getElementById('sheet-link');
            if (sheetLink) {
                sheetLink.href = result.url;
            }
        }
    } catch (error) {
        console.error('Error loading sheet URL:', error);
    }
}

// ==================== NAVIGATION ====================
function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            // Don't prevent default for the external sheet link
            if (item.id === 'sheet-link') return;

            e.preventDefault();
            const view = item.dataset.view;
            if (view) switchView(view);

            // Update active state
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

function switchView(viewName) {
    currentView = viewName;
    const views = document.querySelectorAll('.view');
    views.forEach(view => view.classList.remove('active'));
    document.getElementById(`${viewName}-view`).classList.add('active');

    // Reload data when switching views
    if (viewName === 'dashboard') {
        loadDashboardStats();
    } else if (viewName === 'inventory') {
        loadInventory();
    } else if (viewName === 'leads') {
        loadLeads();
    } else if (viewName === 'closed') {
        loadClosedLeads();
    }
}

// ==================== DASHBOARD ====================
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/stats');
        const result = await response.json();

        if (result.success) {
            const stats = result.data;
            document.getElementById('stat-revenue').textContent = `₹${stats.total_revenue.toLocaleString()}`;
            document.getElementById('stat-confirmed').textContent = stats.confirmed_count;
            document.getElementById('stat-closed').textContent = stats.closed_count || 0;
            document.getElementById('stat-active').textContent = stats.active_count;
            document.getElementById('stat-cancelled').textContent = stats.cancelled_count || 0;
            document.getElementById('stat-conversion').textContent = `${stats.conversion_rate}%`;

            // Display hot products
            displayHotProducts(stats.hot_products);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        showToast('Failed to load dashboard stats', 'error');
    }
}

function displayHotProducts(products) {
    const container = document.getElementById('hot-products-list');

    if (products.length === 0) {
        container.innerHTML = '<p class="loading">No data available</p>';
        return;
    }

    container.innerHTML = products.map(product => `
        <div class="hot-product-item">
            <span class="product-name">${product.name}</span>
            <span class="product-count">${product.count} requests</span>
        </div>
    `).join('');
}

function refreshStats() {
    loadDashboardStats();
    showToast('Dashboard refreshed', 'success');
}

// ==================== INVENTORY ====================
async function loadInventory() {
    try {
        const response = await fetch('/api/inventory');
        const result = await response.json();

        if (result.success) {
            allInventory = result.data;
            displayInventory(allInventory);
        }
    } catch (error) {
        console.error('Error loading inventory:', error);
        showToast('Failed to load inventory', 'error');
    }
}

function displayInventory(products) {
    const tbody = document.getElementById('inventory-tbody');

    if (products.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No products found</td></tr>';
        return;
    }

    tbody.innerHTML = products.map(product => `
        <tr>
            <td>${product.Product_Name}</td>
            <td>${product.Brand || 'N/A'}</td>
            <td>₹${product.Base_Price}</td>
            <td>${product.Stock_Quantity || 'N/A'}</td>
            <td>${product.Unit_Type || product.Category || 'N/A'}</td>
            <td>
                <button class="btn-edit" onclick="showEditProductModal('${product.Product_Name}')">Edit</button>
                <button class="btn-danger" onclick="deleteProduct('${product.Product_Name}')">Delete</button>
            </td>
        </tr>
    `).join('');
}

// Add Product
function showAddProductModal() {
    document.getElementById('add-product-modal').classList.add('active');
}

function closeAddProductModal() {
    document.getElementById('add-product-modal').classList.remove('active');
    document.getElementById('add-product-form').reset();
}

async function handleAddProduct(event) {
    event.preventDefault();

    const productData = {
        Product_Name: document.getElementById('product-name').value,
        Brand: document.getElementById('product-brand').value,
        Base_Price: document.getElementById('product-price').value,
        Stock_Quantity: document.getElementById('product-stock').value,
        Unit_Type: document.getElementById('product-category').value
    };

    try {
        const response = await fetch('/api/inventory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(productData)
        });

        const result = await response.json();

        if (result.success) {
            showToast('Product added successfully', 'success');
            closeAddProductModal();
            loadInventory();
        } else {
            showToast(result.error || 'Failed to add product', 'error');
        }
    } catch (error) {
        console.error('Error adding product:', error);
        showToast('Failed to add product', 'error');
    }
}

// Edit Product
function showEditProductModal(productName) {
    const product = allInventory.find(p => p.Product_Name === productName);
    if (!product) return;

    document.getElementById('edit-product-original-name').value = productName;
    document.getElementById('edit-product-name').value = product.Product_Name;
    document.getElementById('edit-product-brand').value = product.Brand || '';
    document.getElementById('edit-product-price').value = product.Base_Price;
    document.getElementById('edit-product-stock').value = product.Stock_Quantity || '';
    document.getElementById('edit-product-category').value = product.Unit_Type || 'KG';

    document.getElementById('edit-product-modal').classList.add('active');
}

function closeEditProductModal() {
    document.getElementById('edit-product-modal').classList.remove('active');
    document.getElementById('edit-product-form').reset();
}

async function handleEditProduct(event) {
    event.preventDefault();

    const originalName = document.getElementById('edit-product-original-name').value;
    const updates = {
        Product_Name: document.getElementById('edit-product-name').value,
        Brand: document.getElementById('edit-product-brand').value,
        Base_Price: document.getElementById('edit-product-price').value,
        Stock_Quantity: document.getElementById('edit-product-stock').value,
        Unit_Type: document.getElementById('edit-product-category').value
    };

    try {
        const response = await fetch(`/api/inventory/${encodeURIComponent(originalName)}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updates)
        });

        const result = await response.json();

        if (result.success) {
            showToast('Product updated successfully', 'success');
            closeEditProductModal();
            loadInventory();
        } else {
            showToast(result.error || 'Failed to update product', 'error');
        }
    } catch (error) {
        console.error('Error updating product:', error);
        showToast('Failed to update product', 'error');
    }
}

// Delete Product
async function deleteProduct(productName) {
    if (!confirm(`Are you sure you want to delete "${productName}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/inventory/${encodeURIComponent(productName)}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showToast('Product deleted successfully', 'success');
            loadInventory();
        } else {
            showToast(result.error || 'Failed to delete product', 'error');
        }
    } catch (error) {
        console.error('Error deleting product:', error);
        showToast('Failed to delete product', 'error');
    }
}

// ==================== LEADS ====================
async function loadLeads() {
    try {
        const response = await fetch('/api/leads');
        const result = await response.json();

        if (result.success) {
            allLeads = result.data;
            displayLeads(allLeads);
        }
    } catch (error) {
        console.error('Error loading leads:', error);
        showToast('Failed to load leads', 'error');
    }
}

function displayLeads(leads) {
    const tbody = document.getElementById('leads-tbody');

    // Filter out empty leads (rows with no Lead_ID or Customer_Name)
    const validLeads = leads.filter(lead =>
        lead.Lead_ID && String(lead.Lead_ID).trim() !== '' &&
        lead.Customer_Name && String(lead.Customer_Name).trim() !== ''
    );

    if (validLeads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No leads found</td></tr>';
        return;
    }

    tbody.innerHTML = validLeads.map(lead => {
        const statusClass = lead.Status.toLowerCase();
        // Calculate total amount: use Total_Amount if available, else Price × Quantity
        let totalAmount = lead.Total_Amount || '';
        if (!totalAmount && lead.Price_Shown && lead.Quantity_Asked) {
            try {
                totalAmount = (parseFloat(lead.Price_Shown) * parseFloat(lead.Quantity_Asked)).toFixed(2);
            } catch (e) { totalAmount = ''; }
        }
        return `
            <tr>
                <td>${lead.Lead_ID}</td>
                <td>${lead.Customer_Name}</td>
                <td>${lead.Phone}</td>
                <td>${lead.Product_Name}</td>
                <td>${lead.Quantity_Asked || 'N/A'}</td>
                <td>₹${lead.Price_Shown}</td>
                <td>${totalAmount ? '₹' + totalAmount : 'N/A'}</td>
                <td><span class="status-badge status-${statusClass}">${lead.Status}</span></td>
                <td>
                    ${lead.Status === 'CONFIRMED' ?
                `<button class="btn-success" onclick="moveLeadToClosed('${lead.Lead_ID}')">Close Order</button>` :
                lead.Status === 'CANCELLED' ?
                    `<span class="status-badge status-cancelled">Cancelled</span>` :
                    `<button class="btn-edit" onclick="updateLeadStatus('${lead.Lead_ID}', 'CONFIRMED')">Confirm</button>`
            }
                </td>
            </tr>
        `;
    }).join('');
}

async function moveLeadToClosed(leadId) {
    if (!confirm('Move this lead to CLOSED sheet?')) {
        return;
    }

    try {
        const response = await fetch('/api/leads/move-to-closed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ lead_id: leadId })
        });

        const result = await response.json();

        if (result.success) {
            showToast('Lead moved to closed successfully', 'success');
            loadLeads();
        } else {
            showToast(result.error || 'Failed to move lead', 'error');
        }
    } catch (error) {
        console.error('Error moving lead:', error);
        showToast('Failed to move lead', 'error');
    }
}

async function updateLeadStatus(leadId, newStatus) {
    try {
        const response = await fetch(`/api/leads/${leadId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: newStatus })
        });

        const result = await response.json();

        if (result.success) {
            showToast('Lead status updated successfully', 'success');
            loadLeads();
        } else {
            showToast(result.error || 'Failed to update status', 'error');
        }
    } catch (error) {
        console.error('Error updating lead status:', error);
        showToast('Failed to update status', 'error');
    }
}

function filterLeads() {
    const statusFilter = document.getElementById('filter-status').value;
    const searchTerm = document.getElementById('search-leads').value.toLowerCase();

    let filtered = allLeads;

    if (statusFilter) {
        filtered = filtered.filter(lead => lead.Status === statusFilter);
    }

    if (searchTerm) {
        filtered = filtered.filter(lead =>
            lead.Customer_Name.toLowerCase().includes(searchTerm) ||
            lead.Phone.includes(searchTerm) ||
            lead.Product_Name.toLowerCase().includes(searchTerm)
        );
    }

    displayLeads(filtered);
}

// ==================== CLOSED ORDERS ====================
let allClosedOrders = [];

async function loadClosedLeads() {
    try {
        const response = await fetch('/api/leads/closed');
        const result = await response.json();

        if (result.success) {
            allClosedOrders = result.data;
            displayClosedLeads(allClosedOrders);
        }
    } catch (error) {
        console.error('Error loading closed leads:', error);
        showToast('Failed to load closed orders', 'error');
    }
}

function displayClosedLeads(closedLeads) {
    const tbody = document.getElementById('closed-tbody');

    // Filter out empty leads (rows with no Lead_ID or Customer_Name)
    const validClosedLeads = closedLeads.filter(lead =>
        lead.Lead_ID && String(lead.Lead_ID).trim() !== '' &&
        lead.Customer_Name && String(lead.Customer_Name).trim() !== ''
    );

    if (validClosedLeads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No closed orders found</td></tr>';
        return;
    }

    tbody.innerHTML = validClosedLeads.map(lead => {
        const total = (parseFloat(lead.Price_Shown) || 0) * (parseFloat(lead.Quantity_Asked) || 0);
        return `
            <tr>
                <td>${lead.Lead_ID}</td>
                <td>${lead.Customer_Name}</td>
                <td>${lead.Phone}</td>
                <td>${lead.Product_Name}</td>
                <td>${lead.Quantity_Asked || 'N/A'}</td>
                <td>₹${lead.Price_Shown}</td>
                <td>₹${total.toLocaleString()}</td>
                <td>${lead.Lead_Date || 'N/A'}</td>
            </tr>
        `;
    }).join('');
}

// ==================== SEARCH ====================
function setupSearch() {
    const inventorySearch = document.getElementById('search-inventory');
    const leadsSearch = document.getElementById('search-leads');

    if (inventorySearch) {
        inventorySearch.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const filtered = allInventory.filter(product =>
                product.Product_Name.toLowerCase().includes(searchTerm) ||
                (product.Brand && product.Brand.toLowerCase().includes(searchTerm)) ||
                (product.Category && product.Category.toLowerCase().includes(searchTerm))
            );
            displayInventory(filtered);
        });
    }

    if (leadsSearch) {
        leadsSearch.addEventListener('input', filterLeads);
    }

    const closedSearch = document.getElementById('search-closed');
    if (closedSearch) {
        closedSearch.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const filtered = allClosedOrders.filter(lead =>
                lead.Customer_Name.toLowerCase().includes(searchTerm) ||
                lead.Phone.includes(searchTerm) ||
                lead.Product_Name.toLowerCase().includes(searchTerm)
            );
            displayClosedLeads(filtered);
        });
    }
}

// ==================== TOAST NOTIFICATIONS ====================
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
