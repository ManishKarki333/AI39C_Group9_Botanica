/**
 * Botanica Marketplace - Global Navigation Mechanics
 * Handles responsive hamburger menus and persistent Dark Mode styling rules.
 */

document.addEventListener("DOMContentLoaded", () => {
    // --- 1. Hamburger/Mobile Overlay Logic ---
    const menuToggle = document.getElementById("menu-toggle-btn");
    const navMenu = document.getElementById("main-nav-menu");

    if (menuToggle && navMenu) {
        menuToggle.addEventListener("click", () => {
            const isExpanded = menuToggle.getAttribute("aria-expanded") === "true";
            
            // Toggle active visual states
            menuToggle.setAttribute("aria-expanded", !isExpanded);
            navMenu.classList.toggle("nav-menu--active");
            
            // Swap icon appearances inside the toggle button if applicable
            const toggleIcon = menuToggle.querySelector("i");
            if (toggleIcon) {
                if (navMenu.classList.contains("nav-menu--active")) {
                    toggleIcon.className = "ri-close-line"; // Remix Icon for close
                } else {
                    toggleIcon.className = "ri-menu-line";  // Remix Icon for hamburger
                }
            }
        });
    }

    // --- 2. Dark Mode Toggle Module (US 2.3 / Local Storage Persistence) ---
    const themeToggleBtn = document.getElementById("theme-toggle-btn");
    const currentTheme = localStorage.getItem("theme");

    // Check for existing saved theme preferences on page initialization
    if (currentTheme === "dark") {
        document.documentElement.classList.add("dark-theme");
        updateThemeIcon(true);
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            // Toggle core structural classes on the document root element
            document.documentElement.classList.toggle("dark-theme");
            
            const isDarkActive = document.documentElement.classList.contains("dark-theme");
            
            // Update client-side browser cache mapping (Local Storage)
            localStorage.setItem("theme", isDarkActive ? "dark" : "light");
            
            // Smoothly adjust structural elements
            updateThemeIcon(isDarkActive);
        });
    }

    /**
     * Helper mapping function to change theme button icon shapes cleanly
     * @param {boolean} isDark 
     */
    function updateThemeIcon(isDark) {
        if (!themeToggleBtn) return;
        const icon = themeToggleBtn.querySelector("i");
        if (icon) {
            if (isDark) {
                icon.className = "ri-sun-fill"; // Show Sun icon when dark mode is active
            } else {
                icon.className = "ri-moon-line"; // Show Moon icon when light mode is active
            }
        }
    }
});