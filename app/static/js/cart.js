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
                        if (qtySpan) qtySpan.textContent = result.cart_count; // Or item-specific quantity if isolated
                        
                        // If decremented to 0, remove the element completely
                        if (action === 'decrement' && parseInt(qtySpan.textContent) <= 0) {
                            btn.closest('.cart-item-card').remove();
                        }

                        // Update order summary subtotal & total amounts
                        if (result.subtotal !== undefined) {
                            const formattedSub = `Rs. ${parseFloat(result.subtotal).toFixed(2)}`;
                            document.getElementById('cart-subtotal').textContent = formattedSub;
                            document.getElementById('cart-total').textContent = formattedSub;
                        }
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
                    } else {
                        throw new Error(result.message);
                    }
                } catch (error) {
                    console.error("Cart Removal Error:", error);
                }
            }
        });
    }
});