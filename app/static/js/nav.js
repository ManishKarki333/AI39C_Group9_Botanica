document.addEventListener("DOMContentLoaded", () => {
    // 1. Element Hooks
    const themeToggleBtn = document.getElementById("theme-toggle-btn");
    const menuToggle = document.getElementById("menu-toggle-btn");
    const navMenu = document.getElementById("main-nav-menu"); 

    if (!themeToggleBtn) {
        console.warn("Nav Warning: Element with ID 'theme-toggle-btn' was not found in the DOM.");
    }

    // 2. Dark Mode Logic
    function updateThemeIcon(isDark) {
        if (!themeToggleBtn) return;
        const icon = themeToggleBtn.querySelector("i");
        if (icon) {
            icon.className = isDark ? "ri-sun-fill util-icon" : "ri-moon-line util-icon";
        }
    }

    // Initialize icon based on the <html> class set by base.html inline script
    const isCurrentlyDark = document.documentElement.classList.contains("dark-theme");
    updateThemeIcon(isCurrentlyDark);

    // Theme Toggle Click
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            document.documentElement.classList.toggle("dark-theme");
            const isDark = document.documentElement.classList.contains("dark-theme");
            localStorage.setItem("theme", isDark ? "dark" : "light");
            updateThemeIcon(isDark);
        });
    }

    // 3. Mobile Navigation Logic
    if (menuToggle && navMenu) {
        menuToggle.addEventListener("click", () => {
            const isExpanded = menuToggle.getAttribute("aria-expanded") === "true";
            
            // Toggle States
            menuToggle.setAttribute("aria-expanded", !isExpanded);
            navMenu.classList.toggle("nav-menu--active");
            
            // Update Toggle Icon
            const toggleIcon = menuToggle.querySelector("i");
            if (toggleIcon) {
                toggleIcon.className = navMenu.classList.contains("nav-menu--active") 
                    ? "ri-close-line" 
                    : "ri-menu-line";
            }
        });
    }
});