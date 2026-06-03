document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize primary element hooks
    const cartItemsSection = document.querySelector('.cart-items-section');
    const subtotalDisplay = document.getElementById('cart-subtotal');
    const totalDisplay = document.getElementById('cart-total');
    const checkoutBtn = document.getElementById('checkout-btn');
    const deliveryWindowSelect = document.getElementById('delivery-window');

    /**
     * Updates the financial readouts across the document layout using localized formats
     */
    function updateUISummary(subtotalValue) {
        // FIXED: Standardized to Nepalese Rs. formatting to match templates perfectly
        const formattedTotal = `Rs. ${subtotalValue.toFixed(2)}`;
        if (subtotalDisplay) subtotalDisplay.textContent = formattedTotal;
        if (totalDisplay) totalDisplay.textContent = formattedTotal;
    }

    /**
     * Checks if the basket is completely empty to prompt structural UI updates
     */
    function checkEmptyCartState() {
        const itemCards = document.querySelectorAll('.cart-item-card');
        
        if (itemCards.length === 0 && cartItemsSection) {
            // FIXED: Synchronized with cart.html template typography and classes
            cartItemsSection.innerHTML = `
                <div class="empty-cart-fallback" style="text-align: center; padding: 3rem 1rem;">
                    <i class="ri-shopping-basket-line" style="font-size: 4rem; color: #ccc;"></i>
                    <h3>Your basket is empty</h3>
                    <p>Explore our organic remedies directory to add botanicals here.</p>
                    <a href="/shop" class="btn btn-primary" style="display: inline-block; margin-top: 1rem; text-decoration: none;">Browse Storefront</a>
                </div>
            `;
            if (checkoutBtn) checkoutBtn.disabled = true;
            if (subtotalDisplay) subtotalDisplay.textContent = "Rs. 0.00";
            if (totalDisplay) totalDisplay.textContent = "Rs. 0.00";
        }
    }

    /**
     * Sends asynchronous quantity shifts directly to the Flask session engine
     */
    function modifyBackendCartQuantity(herbId, action, cardElement) {
        fetch('/api/cart/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ herb_id: herbId, action: action })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateUISummary(data.subtotal);
                checkEmptyCartState();
            } else {
                console.error("Session update synchronization failure:", data.message);
            }
        })
        .catch(err => console.error("Network communication crash:", err));
    }

    /**
     * Sends a direct deletion request to completely drop an item row from memory
     */
    function removeBackendCartItem(herbId, cardElement) {
        fetch('/api/cart/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ herb_id: herbId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                cardElement.remove();
                updateUISummary(data.subtotal);
                checkEmptyCartState();
            }
        })
        .catch(err => console.error("Network erasure tracking crash:", err));
    }

    /**
     * Event listener capturing clicks within the items column container
     */
    if (cartItemsSection) {
        cartItemsSection.addEventListener('click', function(event) {
            const target = event.target;
            const itemCard = target.closest('.cart-item-card');
            if (!itemCard) return;

            const herbId = itemCard.dataset.herbId;
            const qtyDisplay = itemCard.querySelector('.qty-display');
            let currentQty = parseInt(qtyDisplay.textContent, 10);

            // 1. Handle Increment Operations Click
            if (target.closest('.inc-btn')) {
                if (currentQty < 99) {
                    qtyDisplay.textContent = currentQty + 1;
                    modifyBackendCartQuantity(herbId, 'increment', itemCard);
                }
            }

            // 2. Handle Decrement Operations Click
            else if (target.closest('.dec-btn')) {
                if (currentQty > 1) {
                    qtyDisplay.textContent = currentQty - 1;
                    modifyBackendCartQuantity(herbId, 'decrement', itemCard);
                } else {
                    // Automatically execute removal drop if quantity hits zero
                    removeBackendCartItem(herbId, itemCard);
                }
            }

            // 3. Handle Explicit Single Line Item Deletions
            else if (target.closest('.item-remove-btn')) {
                removeBackendCartItem(herbId, itemCard);
            }
        });
    }

    /**
     * Validates delivery selections before final routing execution
     */
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', function(e) {
            if (!deliveryWindowSelect.value) {
                alert('Please select a preferred delivery window to complete your checkout.');
                deliveryWindowSelect.focus();
                return;
            }
            alert('Proceeding to backend order generation pipeline...');
        });
    }
});