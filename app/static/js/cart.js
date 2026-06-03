document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize primary element hooks
    const cartItemsSection = document.querySelector('.cart-items-section');
    const subtotalDisplay = document.getElementById('cart-subtotal');
    const totalDisplay = document.getElementById('cart-total');
    const checkoutBtn = document.getElementById('checkout-btn');
    const deliveryWindowSelect = document.getElementById('delivery-window');

    /**
     * Recalculates the complete financial matrix of the basket rows.
     */
    function recalculateCartTotals() {
        let runningTotal = 0;
        const itemCards = document.querySelectorAll('.cart-item-card');

        itemCards.forEach(card => {
            // Read internal baseline value metadata attributes
            const quantity = parseInt(card.querySelector('.qty-display').textContent, 10);
            const priceElement = card.querySelector('.item-price');
            
            // Extract raw float number from inner text string (e.g., "$12.50" -> 12.50)
            const unitPrice = parseFloat(priceElement.textContent.replace(/[^\d.]/g, ''));
            
            runningTotal += (unitPrice * quantity);
        });

        // Format and render localized currency readouts
        const formattedTotal = `$${runningTotal.toFixed(2)}`;
        if (subtotalDisplay) subtotalDisplay.textContent = formattedTotal;
        if (totalDisplay) totalDisplay.textContent = formattedTotal;

        // Check if the basket is completely empty to prompt structural UI updates
        if (itemCards.length === 0 && cartItemsSection) {
            cartItemsSection.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #718096;">
                    <i class="ri-shopping-basket-line" style="font-size: 40pt; color: #cbd5e0; display:block; margin-bottom:10px;"></i>
                    <p>Your herbal basket is completely empty.</p>
                    <a href="/shop" style="color: #1b4d3e; font-weight: 600; text-decoration: underline;">Return to Shop</a>
                </div>
            `;
            if (checkoutBtn) checkoutBtn.disabled = true;
        }
    }

    /**
     * Generic structural event listener capturing clicks within the items column container.
     */
    if (cartItemsSection) {
        cartItemsSection.addEventListener('click', function(event) {
            const target = event.target;
            
            // Locate the enclosing card boundary mapping parameters
            const itemCard = target.closest('.cart-item-card');
            if (!itemCard) return;

            const qtyDisplay = itemCard.querySelector('.qty-display');

            // 1. Handle Increment Operations Click
            if (target.closest('.inc-btn')) {
                let currentQty = parseInt(qtyDisplay.textContent, 10);
                if (currentQty < 99) { // Prevent excessive bulk orders
                    qtyDisplay.textContent = currentQty + 1;
                    recalculateCartTotals();
                }
            }

            // 2. Handle Decrement Operations Click
            else if (target.closest('.dec-btn')) {
                let currentQty = parseInt(qtyDisplay.textContent, 10);
                if (currentQty > 1) {
                    qtyDisplay.textContent = currentQty - 1;
                    recalculateCartTotals();
                } else {
                    // Automatically execute removal drop if quantity hits 0
                    itemCard.remove();
                    recalculateCartTotals();
                }
            }

            // 3. Handle Explicit Single Line Item Deletions
            else if (target.closest('.item-remove-btn')) {
                itemCard.remove();
                recalculateCartTotals();
            }
        });
    }

    /**
     * Validates required data values before passing the data to the server.
     */
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', function(e) {
            // Ensure delivery window criteria is satisfied (US 5.4 Validation)
            if (!deliveryWindowSelect.value) {
                alert('Please select a preferred delivery window to complete your checkout.');
                deliveryWindowSelect.focus();
                return;
            }

            // Standard payload readiness verification
            alert('Proceeding to backend order generation pipeline...');
        });
    }

    // Run baseline execution routine on launch
    recalculateCartTotals();
});