document.addEventListener('DOMContentLoaded', () => {
    // DOM Node Cache Mapping
    const searchInput = document.getElementById('global-search-input');
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

    // Context Search Text Input Interceptor Event Listener
    let debounceTimeout;
    searchInput.addEventListener('input', (e) => {
        activeState.query = e.target.value;
        
        // Optimizes networking payload overhead frequency using standard debouncing
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
            fetchMarketplaceData();
        }, 250); // Updates standard DOM elements within a < 2s frame budget cleanly
    });

    // Sidebar Category Tag Interaction Selector Routing
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Toggles highlight style rules active across views safely
            filterButtons.forEach(btn => btn.classList.remove('active'));
            
            button.classList.add('active');
            activeState.benefit = button.getAttribute('data-benefit');
            
            fetchMarketplaceData();
        });
    });

    // Reset Routine Reset Controller Action Handler
    clearFiltersBtn.addEventListener('click', () => {
        searchInput.value = '';
        filterButtons.forEach(btn => btn.classList.remove('active'));
        
        activeState.query = '';
        activeState.benefit = '';
        
        fetchMarketplaceData();
    });

    /**
     * Engine controller performing remote endpoint operations asynchronously
     */
    async function fetchMarketplaceData() {
        try {
            // Evaluates and asserts formatting logic configurations on standard button controllers
            if (activeState.query !== '' || activeState.benefit !== '') {
                clearFiltersBtn.classList.remove('hidden');
            } else {
                clearFiltersBtn.classList.add('hidden');
            }

            // Maps parameters seamlessly to query routing structures
            const urlParams = new URLSearchParams({
                q: activeState.query,
                benefit: activeState.benefit
            });

            const response = await fetch(`/api/search?${urlParams.toString()}`);
            if (!response.ok) throw new Error('Network error during data fetching workflow.');
            
            const payload = await response.json();
            renderUIElements(payload.data, payload.count);
            
        } catch (error) {
            console.error('Search Failure Tracker Log:', error);
            productGrid.innerHTML = '';
            emptyState.classList.remove('hidden');
            resultsCounter.textContent = '0 items found';
        }
    }

    /**
     * Injects formatted code configurations natively directly to live layout structures
     */
    function renderUIElements(items, totalCount) {
        // Clear past iterations natively
        productGrid.innerHTML = '';
        
        // Render current item scope calculation tags
        resultsCounter.textContent = `${totalCount} item${totalCount === 1 ? '' : 's'} found`;

        // Empty state validation mapping logic condition branch rule check
        if (!items || items.length === 0) {
            emptyState.classList.remove('hidden');
            return;
        }
        
        emptyState.classList.add('hidden');

        // Layout parsing constructor loop
        items.forEach(herb => {
            const productCard = document.createElement('div');
            productCard.className = 'product-card-node';
            
            productCard.innerHTML = `
                <div class="card-image-box">
                    <img src="${herb.image_url || '/static/images/placeholder.jpg'}" alt="${herb.common_name}">
                </div>
                <div class="card-details-info">
                    <h4>${herb.common_name}</h4>
                    <p class="scientific-text"><i>${herb.scientific_name}</i></p>
                    <span class="benefit-tag-badge">${herb.benefits}</span>
                    <div class="card-footer-row">
                        <span class="price-indicator">$${parseFloat(herb.price).toFixed(2)}</span>
                        <a href="/shop/item/${herb.id}" class="view-item-link-btn">
                            <i class="ri-arrow-right-line"></i>
                        </a>
                    </div>
                </div>
            `;
            productGrid.appendChild(productCard);
        });
    }
});