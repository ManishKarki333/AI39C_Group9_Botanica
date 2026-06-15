/**
 * Botanica - Merchant Dashboard JavaScript Client Engine
 * Handles Top Selling Herbs Sales Chart, Edit Product specifications,
 * and price fluctuation dynamic histories.
 */

let priceChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialise Sales Share Pie Chart
    initSalesChart();

    // 2. Attach Modal Close Triggers
    const updateModal = document.getElementById('updateProductModal');
    if (updateModal) {
        const modalBody = updateModal.querySelector('.modal-body-card');
        
        // Prevent closing modal when clicking inside card content
        modalBody?.addEventListener('click', (e) => {
            e.stopPropagation();
        });

        // Close modal when clicking outside on the overlay
        updateModal.addEventListener('click', () => {
            closeProductEditModal();
        });
    }

    // 3. Bind Click Event on Product Cards to open specs edit modal
    const productCards = document.querySelectorAll('.product-spec-card');
    productCards.forEach(card => {
        card.addEventListener('click', () => {
            const id = card.getAttribute('data-id');
            const name = card.getAttribute('data-name');
            const price = parseFloat(card.getAttribute('data-price')) || 0.0;
            const stock = parseInt(card.getAttribute('data-stock'), 10) || 0;
            openProductEditModal(id, name, price, stock);
        });
    });
});

/**
 * Initializes and renders the top-selling herbs pie chart using Chart.js
 */
function initSalesChart() {
    const pieCtx = document.getElementById('salesPieChart');
    if (!pieCtx) return;

    // Retrieve data populated safely in JSON container node
    const rawDataNode = document.getElementById('top-selling-data');
    let labels = [];
    let data = [];

    if (rawDataNode) {
        try {
            const parsed = JSON.parse(rawDataNode.textContent);
            parsed.forEach(item => {
                labels.push(item.common_name);
                data.push(item.total_sold);
            });
        } catch (e) {
            console.error('Error parsing top-selling sales JSON:', e);
        }
    }

    // Fallback display if no items have been sold yet
    if (data.length === 0) {
        labels.push('No Sales Recorded');
        data.push(1);
    }

    const isFallback = (labels.length === 1 && labels[0] === 'No Sales Recorded');

    new Chart(pieCtx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: isFallback ? ['#e2e8f0'] : [
                    '#2f855a', // Rich green
                    '#48bb78', // Soft green
                    '#38b2ac', // Teal
                    '#4299e1', // Blue
                    '#667eea', // Indigo
                    '#9f7aea', // Purple
                    '#ed64a6'  // Pink
                ],
                borderWidth: 1,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: !isFallback,
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        padding: 15,
                        font: {
                            family: "'Inter', sans-serif",
                            size: 11,
                            weight: '500'
                        },
                        color: '#475569'
                    }
                },
                tooltip: {
                    enabled: !isFallback,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.label}: ${context.raw} sold`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Opens the product specification editing modal, sets form action,
 * and fetches the pricing data points to render the line chart.
 * Exposed globally for the inline product card onclick attributes.
 */
function openProductEditModal(id, commonName, currentPrice, currentStock) {
    const modal = document.getElementById('updateProductModal');
    if (!modal) return;

    // Populate metadata
    const modalTitle = document.getElementById('updateModalTitle');
    if (modalTitle) modalTitle.innerText = `Edit Specs: ${commonName}`;

    const editPriceInput = document.getElementById('editPrice');
    if (editPriceInput) editPriceInput.value = currentPrice;

    const editStockInput = document.getElementById('editStock');
    if (editStockInput) editStockInput.value = currentStock;

    const updateForm = document.getElementById('updateProductForm');
    if (updateForm) updateForm.action = `/shop/update_product/${id}`;

    // Display modal container
    modal.style.display = 'flex';
    modal.classList.add('active');

    // Fetch pricing history points dynamically
    fetch(`/shop/api/price_history/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const prices = data.history.map(item => item.price);
                const dates = data.history.map(item => {
                    const d = new Date(item.date);
                    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
                });

                renderPriceHistoryChart(dates, prices);
            }
        })
        .catch(err => {
            console.error('Error fetching price history data:', err);
        });
}

/**
 * Renders the price history line chart
 */
function renderPriceHistoryChart(dates, prices) {
    const chartCanvas = document.getElementById('priceHistoryChart');
    if (!chartCanvas) return;

    const chartCtx = chartCanvas.getContext('2d');
    
    // Clean up previous instance to prevent visual duplication bugs
    if (priceChartInstance) {
        priceChartInstance.destroy();
    }

    priceChartInstance = new Chart(chartCtx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Price (NPR)',
                data: prices,
                borderColor: '#3d7a5a',
                backgroundColor: 'rgba(61, 122, 90, 0.08)',
                borderWidth: 2.5,
                fill: true,
                tension: 0.2,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#3d7a5a',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 1.5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` Rs. ${context.raw} per 100g`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: {
                        color: '#f1f5f9'
                    },
                    ticks: {
                        font: { 
                            family: "'Inter', sans-serif",
                            size: 10 
                        },
                        color: '#64748b',
                        callback: function(value) { return 'Rs.' + value; }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: { 
                            family: "'Inter', sans-serif",
                            size: 10 
                        },
                        color: '#64748b'
                    }
                }
            }
        }
    });
}

/**
 * Closes the product specification editing modal.
 * Exposed globally for modal buttons.
 */
function closeProductEditModal() {
    const modal = document.getElementById('updateProductModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
}
