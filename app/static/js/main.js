const herbs = [
    {
        commonName: "Chamomile",
        scientificName: "Matricaria chamomilla",
        description: "A calming herb often used in teas for relaxation and sleep.",
        benefits: ["Sleep", "Stress Relief", "Digestion"]
    },
    {
        commonName: "Ginger",
        scientificName: "Zingiber officinale",
        description: "A warming root used for digestion, nausea, and immunity support.",
        benefits: ["Digestion", "Immunity"]
    },
    {
        commonName: "Turmeric",
        scientificName: "Curcuma longa",
        description: "Popular for anti-inflammatory support and general wellness.",
        benefits: ["Immunity", "Skin Health"]
    },
    {
        commonName: "Lavender",
        scientificName: "Lavandula angustifolia",
        description: "Known for calming aroma and stress-relief properties.",
        benefits: ["Sleep", "Stress Relief"]
    },
    {
        commonName: "Aloe Vera",
        scientificName: "Aloe barbadensis miller",
        description: "Used for skin soothing and topical support.",
        benefits: ["Skin Health"]
    }
];

const libraryArticles = [
    {
        title: "Chamomile for Rest and Relaxation",
        herb: "Chamomile",
        summary: "Learn how chamomile is traditionally used in herbal wellness."
    },
    {
        title: "The Digestive Benefits of Ginger",
        herb: "Ginger",
        summary: "Explore how ginger supports digestion and daily wellness."
    },
    {
        title: "Turmeric in Traditional Herbal Practice",
        herb: "Turmeric",
        summary: "A short introduction to turmeric’s role in herbal traditions."
    }
];

function renderHerbs(filteredHerbs) {
    const productGrid = document.getElementById("productGrid");
    const noResults = document.getElementById("noResults");

    if (!productGrid) return;

    productGrid.innerHTML = "";

    if (filteredHerbs.length === 0) {
        noResults.classList.remove("hidden");
        return;
    }

    noResults.classList.add("hidden");

    filteredHerbs.forEach(herb => {
        const card = document.createElement("div");
        card.className = "card";

        card.innerHTML = `
            <h3>${herb.commonName}</h3>
            <p class="scientific">${herb.scientificName}</p>
            <p>${herb.description}</p>
            <div class="badges">
                ${herb.benefits.map(benefit => `<span class="badge">${benefit}</span>`).join("")}
            </div>
        `;

        productGrid.appendChild(card);
    });
}

function filterHerbs() {
    const commonValue = document.getElementById("commonSearch")?.value.toLowerCase() || "";
    const scientificValue = document.getElementById("scientificSearch")?.value.toLowerCase() || "";
    const checkedBenefits = [...document.querySelectorAll(".benefit-filter:checked")].map(cb => cb.value);

    document.getElementById("filterCount").textContent = checkedBenefits.length;

    const filtered = herbs.filter(herb => {
        const commonMatch = herb.commonName.toLowerCase().includes(commonValue);
        const scientificMatch = herb.scientificName.toLowerCase().includes(scientificValue);
        const benefitMatch =
            checkedBenefits.length === 0 ||
            checkedBenefits.every(benefit => herb.benefits.includes(benefit));

        return commonMatch && scientificMatch && benefitMatch;
    });

    renderHerbs(filtered);
}

function renderLibrary(filteredArticles) {
    const libraryGrid = document.getElementById("libraryGrid");
    const noResults = document.getElementById("libraryNoResults");

    if (!libraryGrid) return;

    libraryGrid.innerHTML = "";

    if (filteredArticles.length === 0) {
        noResults.classList.remove("hidden");
        return;
    }

    noResults.classList.add("hidden");

    filteredArticles.forEach(article => {
        const card = document.createElement("div");
        card.className = "card";

        card.innerHTML = `
            <h3>${article.title}</h3>
            <p><strong>Herb:</strong> ${article.herb}</p>
            <p>${article.summary}</p>
        `;

        libraryGrid.appendChild(card);
    });
}

function filterLibrary() {
    const searchValue = document.getElementById("librarySearch")?.value.toLowerCase() || "";

    const filtered = libraryArticles.filter(article =>
        article.title.toLowerCase().includes(searchValue) ||
        article.herb.toLowerCase().includes(searchValue) ||
        article.summary.toLowerCase().includes(searchValue)
    );

    renderLibrary(filtered);
}

function setupPasswordValidation() {
    const form = document.getElementById("changePasswordForm");
    const message = document.getElementById("passwordMessage");

    if (!form) return;

    form.addEventListener("submit", function (e) {
        const newPassword = document.getElementById("new_password").value;
        const confirmPassword = document.getElementById("confirm_password").value;

        if (newPassword.length < 8) {
            e.preventDefault();
            message.textContent = "New password must be at least 8 characters.";
            message.style.color = "#b91c1c";
            return;
        }

        if (newPassword !== confirmPassword) {
            e.preventDefault();
            message.textContent = "New password and confirmation do not match.";
            message.style.color = "#b91c1c";
            return;
        }

        message.textContent = "Frontend validation passed. Backend update comes next.";
        message.style.color = "#166534";
    });
}

document.addEventListener("DOMContentLoaded", function () {
    renderHerbs(herbs);
    renderLibrary(libraryArticles);
    setupPasswordValidation();

    document.getElementById("commonSearch")?.addEventListener("input", filterHerbs);
    document.getElementById("scientificSearch")?.addEventListener("input", filterHerbs);
    document.querySelectorAll(".benefit-filter").forEach(cb => {
        cb.addEventListener("change", filterHerbs);
    });

    document.getElementById("clearFilters")?.addEventListener("click", function () {
        document.querySelectorAll(".benefit-filter").forEach(cb => cb.checked = false);
        document.getElementById("commonSearch").value = "";
        document.getElementById("scientificSearch").value = "";
        filterHerbs();
    });

    document.getElementById("librarySearch")?.addEventListener("input", filterLibrary);
});
