document.addEventListener("DOMContentLoaded", () => {
    
    // --- 1. Element Hooks Registration ---
    const themeToggleBtn = document.getElementById("theme-toggle-btn");
    const menuToggle = document.getElementById("menu-toggle-btn");
    const navMenu = document.getElementById("main-nav-menu");
    const currentTheme = localStorage.getItem("theme");

    // --- 2. Dark Mode Module (US 2.3 / Local Storage Persistence) ---

    /**
     * Smoothly updates the visual aesthetic states of the interface theme toggle button icon
     * @param {boolean} isDark 
     */
    function updateThemeIcon(isDark) {
        if (!themeToggleBtn) return;
        const icon = themeToggleBtn.querySelector("i");
        if (icon) {
            if (isDark) {
                // Remix Icon filled sun when dark mode is enabled
                icon.className = "ri-sun-fill util-icon"; 
            } else {
                // Remix Icon outline moon when light mode is enabled
                icon.className = "ri-moon-line util-icon"; 
            }
        }
    }

    // Initialize saved configuration parameters from local browser storage cache
    if (currentTheme === "dark") {
        document.documentElement.classList.add("dark-theme");
        updateThemeIcon(true);
    } else {
        // Fallback default state setup
        updateThemeIcon(false);
    }

    // Interactive Theme Toggle Listener Click Action
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            document.documentElement.classList.toggle("dark-theme");
            
            const isDarkActive = document.documentElement.classList.contains("dark-theme");
            localStorage.setItem("theme", isDarkActive ? "dark" : "light");
            
            updateThemeIcon(isDarkActive);
        });
    }

    // --- 3. Responsive Mobile Drawer Fallback Safe Guards ---
    // Defensively verifies elements to prevent runtime errors if responsive tokens are modified
    if (menuToggle && navMenu) {
        menuToggle.addEventListener("click", () => {
            const isExpanded = menuToggle.getAttribute("aria-expanded") === "true";
            
            menuToggle.setAttribute("aria-expanded", !isExpanded);
            navMenu.classList.toggle("nav-menu--active");
            
            const toggleIcon = menuToggle.querySelector("i");
            if (toggleIcon) {
                if (navMenu.classList.contains("nav-menu--active")) {
                    toggleIcon.className = "ri-close-line"; 
                } else {
                    toggleIcon.className = "ri-menu-line";  
                }
            }
        });
    }
});