document.addEventListener('DOMContentLoaded', () => {
    // DOM Node Cache
    const searchInput = document.getElementById('global-search');
    const filterButtons = document.querySelectorAll('.filter-btn');
    const clearFiltersBtn = document.getElementById('clear-all-filters');
    const resultsCounter = document.getElementById('results-counter-badge');
    const productGrid = document.getElementById('product-results-grid');
    const emptyState = document.getElementById('empty-state-container');

    // Global State
    let activeState = { query: '', benefit: '' };
    let debounceTimeout;

    // --- Core Logic ---

    // 1. Search Input Interceptor
    searchInput?.addEventListener('input', (e) => {
        activeState.query = e.target.value;
        debounce(fetchMarketplaceData, 300);
    });

    // 2. Filter Interaction Routing
    // 2. Filter Interaction Routing
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            const isAlreadyActive = button.classList.contains('active');
            
            filterButtons.forEach(btn => btn.classList.remove('active'));
            if (!isAlreadyActive) {
                button.classList.add('active');
                // ADDED .trim() to prevent whitespace issues
                activeState.benefit = button.getAttribute('data-benefit')?.trim() || '';
            } else {
                activeState.benefit = '';
            }
            fetchMarketplaceData();
        });
    });

    // 3. Clear Filters
    clearFiltersBtn?.addEventListener('click', () => {
        if (searchInput) searchInput.value = '';
        activeState.query = '';
        activeState.benefit = '';
        filterButtons.forEach(btn => btn.classList.remove('active'));
        fetchMarketplaceData();
    });

    // --- Engine ---

    async function fetchMarketplaceData() {
        // Toggle clear button visibility
        clearFiltersBtn?.classList.toggle('hidden', activeState.query === '' && activeState.benefit === '');

        const params = new URLSearchParams({ q: activeState.query, benefit: activeState.benefit });

        try {
            const response = await fetch(`/shop/api/search?${params.toString()}`);
            if (!response.ok) throw new Error('Search request failed');
            
            const payload = await response.json();
            renderUI(payload.data, payload.count);
        } catch (error) {
            console.error('Dynamic Search Error:', error);
        }
    }

    function renderUI(items, totalCount) {
        // Safely remove only the product cards, leaving the empty state container intact (if it's a child)
        const cards = productGrid.querySelectorAll('.product-card');
        cards.forEach(card => card.remove());
        
        resultsCounter.textContent = `${totalCount} item${totalCount === 1 ? '' : 's'} found`;

        if (!items || items.length === 0) {
            emptyState?.classList.remove('hidden');
            return;
        }

        if (emptyState) {
            emptyState.classList.add('hidden');
        }

        // Rebuild the Grid
        items.forEach(herb => {
            const article = document.createElement('article');
            article.className = `product-card ${herb.on_vacation ? 'on-vacation' : ''}`;
            article.setAttribute('data-benefits', herb.benefit_category);
            article.innerHTML = `
                <a href="/shop/herb_details/${herb.id}" class="product-card-media-link">
                    <div class="card-image-wrapper">
                        ${herb.on_vacation ? '<span class="vacation-banner">On Vacation</span>' : ''}
                        <img src="${herb.image_url || '/static/uploads/default_herb.png'}" alt="${herb.common_name}" class="product-image">
                        <div class="card-badge">${herb.form_factor || 'Raw Herb'}</div>
                    </div>
                </a>
                <div class="card-body">
                    <a href="/shop/herb_details/${herb.id}" class="product-card-info-link">
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
                            <span class="unit">/100g</span>
                        </div>
                        <button class="action-add-cart" data-id="${herb.id}" title="Add to Cart" ${herb.on_vacation ? 'disabled' : ''}>
                            <i class="ri-shopping-cart-2-line"></i>
                        </button>
                    </div>
                </div>
            `;
            // Insert before the empty state so it stays at the end of the grid
            if (emptyState) {
                productGrid.insertBefore(article, emptyState);
            } else {
                productGrid.appendChild(article);
            }
        });
    }

    function debounce(func, delay) {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(func, delay);
    }
});