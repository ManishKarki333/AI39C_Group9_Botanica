document.addEventListener('DOMContentLoaded', () => {
    // ────────────────────────────────────────────────────────────────
    // 1. STOREFRONT: ADD TO CART LISTENER
    // ────────────────────────────────────────────────────────────────
    document.addEventListener('click', async (e) => {
        const cartButton = e.target.closest('.action-add-cart');
        
        if (cartButton) {
            e.preventDefault();
            const herbId = cartButton.getAttribute('data-id');
            const originalIcon = cartButton.innerHTML;

            // Visual feedback
            cartButton.innerHTML = '<i class="ri-loader-4-line ri-spin"></i>';
            cartButton.disabled = true;

            try {
                const response = await fetch('/shop/add_to_cart', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ herb_id: herbId })
                });

                const result = await response.json();

                if (response.ok) {
                    cartButton.innerHTML = '<i class="ri-check-line"></i>';
                    cartButton.style.backgroundColor = '#2c5e3b';
                    
                    // Update global navbar count if it exists
                    const navbarBadge = document.getElementById('navbar-cart-count');
                    if (navbarBadge) navbarBadge.textContent = result.cart_count;
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                console.error("Cart Error:", error);
                cartButton.innerHTML = '<i class="ri-error-warning-line"></i>';
                cartButton.style.backgroundColor = '#e53e3e';
                alert(error.message);
            } finally {
                setTimeout(() => {
                    cartButton.innerHTML = originalIcon;
                    cartButton.style.backgroundColor = '';
                    cartButton.disabled = false;
                }, 1200);
            }
        }
    });

    // ────────────────────────────────────────────────────────────────
    // 2. SHOPPING CART PAGE: QUANTITY CONTROLS & REMOVAL
    // ────────────────────────────────────────────────────────────────
    const cartLayout = document.querySelector('.cart-layout');

    if (cartLayout) {
        cartLayout.addEventListener('click', async (e) => {
            const incBtn = e.target.closest('.inc-btn');
            const decBtn = e.target.closest('.dec-btn');
            const removeBtn = e.target.closest('.item-remove-btn');

            // Handle Increment / Decrement
            if (incBtn || decBtn) {
                const btn = incBtn || decBtn;
                const herbId = btn.getAttribute('data-id');
                const action = incBtn ? 'increment' : 'decrement';

                try {
                    const response = await fetch('/shop/update_cart', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ herb_id: herbId, action: action })
                    });

                    const result = await response.json();

                    if (response.ok && result.status === 'success') {
                        // Update individual item quantity display
                        const qtySpan = document.getElementById(`qty-${herbId}`);
                        
                        if (action === 'decrement' && qtySpan) {
                            const currentVal = parseInt(qtySpan.textContent, 10) - 1;
                            if (currentVal <= 0) {
                                btn.closest('.cart-item-card').remove();
                            } else {
                                qtySpan.textContent = currentVal;
                            }
                        } else if (action === 'increment' && qtySpan) {
                            qtySpan.textContent = parseInt(qtySpan.textContent, 10) + 1;
                        }

                        // Update order summary subtotal & total amounts
                        if (result.subtotal !== undefined) {
                            const formattedSub = `Rs. ${parseFloat(result.subtotal).toFixed(2)}`;
                            document.getElementById('cart-subtotal').textContent = formattedSub;
                            document.getElementById('cart-total').textContent = formattedSub;
                        }

                        // Check if cart is empty after modification
                        evaluateCartEmptyState();
                    } else {
                        throw new Error(result.message);
                    }
                } catch (error) {
                    console.error("Cart Update Error:", error);
                }
            }

            // Handle Item Removal
            if (removeBtn) {
                const herbId = removeBtn.getAttribute('data-id');

                try {
                    const response = await fetch('/shop/remove_from_cart', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ herb_id: herbId })
                    });

                    const result = await response.json();

                    if (response.ok && result.status === 'success') {
                        // Purge card visual tree structure completely
                        removeBtn.closest('.cart-item-card').remove();

                        // Refresh order summary values
                        if (result.subtotal !== undefined) {
                            const formattedSub = `Rs. ${parseFloat(result.subtotal).toFixed(2)}`;
                            document.getElementById('cart-subtotal').textContent = formattedSub;
                            document.getElementById('cart-total').textContent = formattedSub;
                        }

                        // Check if cart is empty after purge
                        evaluateCartEmptyState();
                    } else {
                        throw new Error(result.message);
                    }
                } catch (error) {
                    console.error("Cart Removal Error:", error);
                }
            }
        });
    }

    // ────────────────────────────────────────────────────────────────
    // 3. CHECKOUT & CART HANDLER
    // ────────────────────────────────────────────────────────────────
    const checkoutBtn = document.getElementById('checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', () => {
            const deliveryWindow = document.getElementById('delivery-window').value;

            if (!deliveryWindow) {
                alert("Please select a preferred delivery window before proceeding.");
                return;
            }

            // Redirect to your processing/checkout endpoint 
            // (Pass window info along or read it server-side from session/form if submitted via form)
            window.location.href = `/shop/checkout?window=${deliveryWindow}`;
        });
    }

    // ────────────────────────────────────────────────────────────────
    // 4. UTILITY: EMPTY CART STATE FALLBACK
    // ────────────────────────────────────────────────────────────────
    function evaluateCartEmptyState() {
        const remainingCards = document.querySelectorAll('.cart-item-card');
        const itemsSection = document.querySelector('.cart-items-section');
        const checkoutBtn = document.getElementById('checkout-btn');

        if (remainingCards.length === 0) {
            // Disable Checkout Button
            if (checkoutBtn) checkoutBtn.disabled = true;

            // Inject empty state HTML dynamically
            if (itemsSection && !document.querySelector('.empty-cart-fallback')) {
                itemsSection.innerHTML = `
                    <div class="empty-cart-fallback" style="text-align: center; padding: 3rem 1rem;">
                        <i class="ri-shopping-basket-line" style="font-size: 4rem; color: #ccc;"></i>
                        <h3>Your basket is empty</h3>
                        <p>Explore our organic remedies directory to add botanicals here.</p>
                        <a href="/shop" class="btn btn-primary" style="display: inline-block; margin-top: 1rem; text-decoration: none;">Browse Storefront</a>
                    </div>
                `;
            }
            
            // Update global badge count to 0
            const navbarBadge = document.getElementById('navbar-cart-count');
            if (navbarBadge) navbarBadge.textContent = '0';
        }
    }
});