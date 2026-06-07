document.addEventListener('DOMContentLoaded', () => {
    // DOM Node Cache Mapping
    const searchInput = document.getElementById('global-search'); 
    const filterButtons = document.querySelectorAll('.filter-btn');
    const clearFiltersBtn = document.getElementById('clear-all-filters');
    const resultsCounter = document.getElementById('results-counter-badge');
    const productGrid = document.getElementById('product-results-grid');
    const emptyState = document.getElementById('empty-state-container');

    // Global Component State Matrix Tracker
    let activeState = {
        query: '',
        benefit: ''
    };

    // Initializes UI view layout content on page load event safely
    fetchMarketplaceData();

    // 🛒 SUCCESS: Event Delegation Container targeting Blueprint endpoints seamlessly
    if (productGrid) {
        productGrid.addEventListener('click', async (e) => {
            const cartButton = e.target.closest('.action-add-cart');
            
            if (cartButton) {
                e.preventDefault(); 
                
                const herbId = cartButton.getAttribute('data-id');
                
                // Visual feedback micro-interaction
                const originalIcon = cartButton.innerHTML;
                cartButton.innerHTML = '<i class="ri-loader-4-line ri-spin"></i>';
                cartButton.disabled = true; 

                try {
                    // 🌟 FIXED: Target the proper Flask Blueprint prefix path namespace
                    const response = await fetch('/shop/cart/add', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ herb_id: herbId })
                    });

                    const result = await response.json();

                    if (response.ok && result.status === 'success') {
                        cartButton.innerHTML = '<i class="ri-check-line"></i>';
                        cartButton.style.backgroundColor = '#2c5e3b'; 
                        
                        // Optional: Global navbar item badge synchronization hook
                        const navbarBadge = document.getElementById('navbar-cart-count');
                        if (navbarBadge && result.cart_count) {
                            navbarBadge.textContent = result.cart_count;
                        }
                    } else {
                        throw new Error(result.message || 'Failed to update cart session.');
                    }
                } catch (error) {
                    console.error('Cart Operations Error Log:', error);
                    cartButton.innerHTML = '<i class="ri-error-warning-line"></i>';
                    cartButton.style.backgroundColor = '#e53e3e'; 
                } finally {
                    setTimeout(() => {
                        cartButton.innerHTML = originalIcon;
                        cartButton.style.backgroundColor = '';
                        cartButton.disabled = false; 
                    }, 1200);
                }
            }
        });
    }

    // Context Search Text Input Interceptor Event Listener
    let debounceTimeout;
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            activeState.query = e.target.value;
            
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                fetchMarketplaceData();
            }, 250); 
        });
    }

    // Sidebar Category Tag Interaction Selector Routing
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            if (button.classList.contains('active')) {
                button.classList.remove('active');
                activeState.benefit = '';
            } else {
                filterButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                activeState.benefit = button.getAttribute('data-benefit');
            }
            
            fetchMarketplaceData();
        });
    });

    // Reset Routine Reset Controller Action Handler
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            filterButtons.forEach(btn => btn.classList.remove('active'));
            
            activeState.query = '';
            activeState.benefit = '';
            
            fetchMarketplaceData();
        });
    }

    /**
     * Engine controller performing remote endpoint operations asynchronously
     */
    async function fetchMarketplaceData() {
        try {
            if (clearFiltersBtn) {
                if (activeState.query !== '' || activeState.benefit !== '') {
                    clearFiltersBtn.classList.remove('hidden');
                } else {
                    clearFiltersBtn.classList.add('hidden');
                }
            }

            const urlParams = new URLSearchParams({
                q: activeState.query,
                benefit: activeState.benefit
            });

            // 🌟 FIXED: Routed through the /shop/ prefix to find your api_search_and_filter endpoint
            let response = await fetch(`/shop/api/search?${urlParams.toString()}`);
            
            // Absolute root fallback loop check if you are not running Blueprint prefixes on your routes
            if (!response.ok && response.status === 404) {
                response = await fetch(`/api/search?${urlParams.toString()}`);
            }
            
            if (!response.ok) throw new Error('Network error during data fetching.');
            
            const payload = await response.json();
            renderUIElements(payload.data, payload.count);
            
        } catch (error) {
            console.error('Search Failure Tracker Log:', error);
        }
    }

    /**
     * Injects formatted code configurations natively directly to live layout structures
     */
    function renderUIElements(items, totalCount) {
        if (!productGrid || !resultsCounter || !emptyState) return;

        productGrid.innerHTML = '';
        resultsCounter.textContent = `${totalCount} item${totalCount === 1 ? '' : 's'} found`;

        if (!items || items.length === 0) {
            emptyState.classList.remove('hidden');
            return;
        }
        
        emptyState.classList.add('hidden');

        items.forEach(herb => {
            const productCard = document.createElement('article');
            productCard.className = `product-card ${herb.on_vacation ? 'on-vacation' : ''}`;
            productCard.setAttribute('data-benefits', herb.benefit_category || '');
            
            productCard.innerHTML = `
                <a href="/shop/item/${herb.id}" class="product-card-media-link" aria-label="View details for ${herb.common_name}">
                    <div class="card-image-wrapper">
                        ${herb.on_vacation ? '<span class="vacation-banner">On Vacation</span>' : ''}
                        <img src="${herb.image_url || '/static/uploads/default_herb.png'}" alt="${herb.common_name}" class="product-image">
                        <div class="card-badge">${herb.form_factor || 'Raw Herb'}</div>
                    </div>
                </a>

                <div class="card-body">
                    <a href="/shop/item/${herb.id}" class="product-card-info-link">
                        <div class="meta-names">
                            <h2 class="common-name">${herb.common_name}</h2>
                            <p class="scientific-name"><em>${herb.scientific_name}</em></p>
                        </div>
                    </a>

                    <p class="herb-excerpt">${herb.description || ''}</p>
                    
                    <div class="card-footer">
                        <div class="price-block">
                            <span class="currency">Rs.</span>
                            <span class="price-value">${herb.price}</span>
                            <span class="unit">/${herb.unit_weight || '100g'}</span>
                        </div>
                        
                        <button class="action-add-cart" data-id="${herb.id}" title="Add to Cart" ${herb.on_vacation ? 'disabled' : ''}>
                            <i class="ri-shopping-cart-2-line"></i>
                        </button>
                    </div>
                </div>
            `;
            productGrid.appendChild(productCard);
        });
    }
});