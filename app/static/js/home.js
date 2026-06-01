document.addEventListener('DOMContentLoaded', function() {
    // Select interactive node structures
    const searchInput = document.getElementById('home-search-input');
    const searchButton = document.getElementById('home-search-submit');
    const quickTags = document.querySelectorAll('.quick-filter-tag');

    /**
     * Executes context extraction queries by forwarding data parameters 
     * seamlessly into the corresponding Sprint 2 Library Search routes.
     */
    function executeSearchQuery(queryString) {
        if (!queryString.trim()) {
            searchInput.focus();
            return;
        }
        
        // Formulates target path parameter appending safe URL segments
        const targetUrl = `/auth/herb-library?search=${encodeURIComponent(queryString.trim())}`;
        
        // Immediate clean client transition mapping
        window.location.href = targetUrl;
    }

    // Trigger on structural action click
    searchButton.addEventListener('click', function() {
        executeSearchQuery(searchInput.value);
    });

    // Intercept standard terminal Enter key presses
    searchInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            executeSearchQuery(searchInput.value);
        }
    });

    // Process immediate quick benefit filtering badge queries
    quickTags.forEach(tag => {
        tag.addEventListener('click', function() {
            const benefitValue = this.getAttribute('data-benefit');
            if (benefitValue) {
                // Route query sequence into live target module parameters
                window.location.href = `/auth/herb-library?filter=${encodeURIComponent(benefitValue)}`;
            }
        });
    });
});