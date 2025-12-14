const form = document.getElementById("profiling-form");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

const loaderEl = document.getElementById("loader");
const loaderTextEl = document.getElementById("loader-text");

const loaderSteps = [
    { id: "step-linkedin", text: "Scraping LinkedIn..." },
    { id: "step-company", text: "Analyse du site entreprise..." },
    { id: "step-news", text: "Recherche d'actualités..." },
    { id: "step-social", text: "Exploration réseaux sociaux..." },
];

let currentStep = 0;
let stepInterval;

function showLoader() {
    loaderEl.classList.remove("hidden");
    currentStep = 0;
    
    // Animer les étapes progressivement
    stepInterval = setInterval(() => {
        if (currentStep > 0) {
            const prevStep = document.getElementById(loaderSteps[currentStep - 1].id);
            prevStep.classList.remove("active");
            prevStep.classList.add("done");
        }
        
        if (currentStep < loaderSteps.length) {
            const step = loaderSteps[currentStep];
            document.getElementById(step.id).classList.add("active");
            loaderTextEl.textContent = step.text;
            currentStep++;
        }
    }, 3000); // Change d'étape toutes les 3 secondes
}

function hideLoader() {
    clearInterval(stepInterval);
    loaderEl.classList.add("hidden");
    
    // Réinitialiser les étapes
    loaderSteps.forEach(step => {
        const el = document.getElementById(step.id);
        el.classList.remove("active", "done");
    });
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    statusEl.textContent = "";
    resultsEl.classList.add("hidden");
    showLoader();

    const payload = {
        first_name: document.getElementById("first_name").value.trim(),
        last_name: document.getElementById("last_name").value.trim(),
        company: document.getElementById("company").value.trim() || null,
    };

    try {
        const res = await fetch("/profiling/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        
        hideLoader();
        statusEl.textContent = "✓ Analyse terminée avec succès";
        statusEl.style.color = "var(--success)";
        renderResults(data);
        resultsEl.classList.remove("hidden");
    } catch (err) {
        console.error(err);
        hideLoader();
        statusEl.textContent = "✗ Erreur lors de l'analyse";
        statusEl.style.color = "#ff6b6b";
    }
});

function renderResults(data) {
    // L'API retourne { debug: {...}, profile: {...} }
    const profile = data.profile || data;
    
    // Profil de base
    setText("r-first", profile.first_name || "");
    setText("r-last", profile.last_name || "");
    setText("r-company", profile.company || "");
    setText("r-role", profile.current_role || "");
    setText("r-summary", profile.summary || "Aucun résumé disponible");

    // Compétences
    const skills = Array.isArray(profile.skills) ? profile.skills : [];
    fillList("r-skills", skills.length ? skills : ["Aucune compétence détectée"]);

    // Score fiabilité
    setText("r-score", profile?.reliability?.score ?? "—");
    
    // Justification en liste
    const justifRoot = document.getElementById("r-score-justif");
    justifRoot.innerHTML = "";
    const justification = profile?.reliability?.justification ?? "";
    
    if (justification) {
        // Séparer par phrases (points, virgules, ou retours ligne)
        const sentences = justification
            .split(/[.;]|\n/)
            .map(s => s.trim())
            .filter(s => s.length > 10); // Ignorer les fragments trop courts
        
        if (sentences.length > 0) {
            sentences.forEach(sentence => {
                const li = document.createElement("li");
                li.textContent = sentence;
                justifRoot.appendChild(li);
            });
        } else {
            justifRoot.innerHTML = '<li>Calcul en cours...</li>';
        }
    } else {
        justifRoot.innerHTML = '<li>Calcul en cours...</li>';
    }

    // Expériences
    const exps = Array.isArray(profile.experiences) ? profile.experiences : [];
    const expRoot = document.getElementById("r-experiences");
    expRoot.innerHTML = "";
    if (exps.length === 0) {
        expRoot.innerHTML = '<div class="muted">Aucune expérience détectée</div>';
    } else {
        exps.forEach((e) => {
            const el = document.createElement("div");
            el.className = "exp";
            el.innerHTML = `
          <div><strong>${safe(e.title)}</strong> ${e.company ? `— ${safe(e.company)}` : ""}</div>
          <div class="muted">${safe(e.start_date || "")} → ${safe(e.end_date || e.is_current ? "Présent" : "")}</div>
          ${e.description ? `<p class="muted">${safe(e.description)}</p>` : ""}
        `;
            expRoot.appendChild(el);
        });
    }

    // Posts LinkedIn
    const linkedinAnalysis = profile.linkedin_analysis || {};
    const posts = Array.isArray(linkedinAnalysis.posts) ? linkedinAnalysis.posts : [];
    const postsRoot = document.getElementById("r-posts");
    postsRoot.innerHTML = "";
    
    if (posts.length === 0) {
        postsRoot.innerHTML = '<div class="muted">Aucun post LinkedIn trouvé</div>';
    } else {
        // Afficher les thèmes récurrents d'abord
        if (linkedinAnalysis.recurring_themes && linkedinAnalysis.recurring_themes.length > 0) {
            const themesEl = document.createElement("div");
            themesEl.innerHTML = `<h4>Thèmes récurrents:</h4>${arrayToTags(linkedinAnalysis.recurring_themes)}`;
            postsRoot.appendChild(themesEl);
        }
        
        posts.forEach((p) => {
            const el = document.createElement("div");
            el.className = "post";
            const url = p.url ? `<a href="${safe(p.url)}" target="_blank">Voir</a>` : "";
            el.innerHTML = `
          <div class="meta">${safe(p.date || "")} ${url}</div>
          <div>${safe(p.content || p.summary || "Contenu non disponible")}</div>
        `;
            postsRoot.appendChild(el);
        });
    }

    // Réputation
    const reputation = profile.reputation || {};
    const repRoot = document.getElementById("r-reputation");
    let repHTML = "";
    
    if (reputation.summary) {
        repHTML += `<div class="muted"><strong>Synthèse:</strong> ${safe(reputation.summary)}</div>`;
    }
    
    if (reputation.strengths && reputation.strengths.length > 0) {
        repHTML += arrayToList(reputation.strengths, "Points forts");
    }
    
    if (reputation.weak_signals && reputation.weak_signals.length > 0) {
        repHTML += arrayToList(reputation.weak_signals, "Signaux faibles");
    }
    
    if (!repHTML) {
        repHTML = '<div class="muted">Analyse de réputation non disponible</div>';
    }
    
    repRoot.innerHTML = repHTML;

    // Publications / contacts
    const publications = Array.isArray(profile.publications) ? profile.publications : [];
    const contacts = profile.contact_info || {};
    
    // Formater les publications avec liens
    const pubRoot = document.getElementById("r-publications");
    pubRoot.innerHTML = "";
    
    if (publications.length === 0) {
        pubRoot.innerHTML = '<div class="muted" style="padding: 20px; text-align: center;">Aucune publication trouvée</div>';
    } else {
        publications.forEach(pub => {
            const pubDiv = document.createElement("div");
            pubDiv.className = "publication-item";
            
            // Extraire titre et URL si format "Titre - URL"
            let title = pub;
            let url = "";
            let source = "";
            
            if (pub.includes(" - http")) {
                const parts = pub.split(" - ");
                title = parts[0];
                url = parts[1];
                
                // Extraire le domaine pour la source
                try {
                    const domain = new URL(url).hostname.replace("www.", "");
                    source = domain;
                } catch (e) {}
            } else if (pub.startsWith("Mention - ")) {
                title = pub.replace("Mention - ", "Mention dans ");
                source = pub.replace("Mention - ", "");
            }
            
            if (url) {
                pubDiv.innerHTML = `
                    <span class="pub-icon">📄</span>
                    <div>
                        <a href="${safe(url)}" target="_blank">${safe(title)}</a>
                        ${source ? `<span class="pub-source">${safe(source)}</span>` : ""}
                    </div>
                `;
            } else {
                pubDiv.innerHTML = `
                    <span class="pub-icon">📰</span>
                    <div>${safe(title)}</div>
                `;
            }
            
            pubRoot.appendChild(pubDiv);
        });
    }
    
    // Construire la grille des contacts avec icônes
    const contactsRoot = document.getElementById("r-contacts");
    contactsRoot.innerHTML = "";
    
    const contactItems = [];
    
    if (contacts.linkedin_url) {
        contactItems.push({
            icon: "💼",
            label: "LinkedIn",
            url: contacts.linkedin_url
        });
    }
    
    if (contacts.twitter) {
        contactItems.push({
            icon: "🐦",
            label: "Twitter / X",
            url: contacts.twitter
        });
    }
    
    if (contacts.github) {
        contactItems.push({
            icon: "💻",
            label: "GitHub",
            url: contacts.github
        });
    }
    
    if (contacts.website) {
        contactItems.push({
            icon: "🌐",
            label: "Site web",
            url: contacts.website
        });
    }
    
    if (contacts.email) {
        contactItems.push({
            icon: "📧",
            label: "Email",
            url: `mailto:${contacts.email}`
        });
    }
    
    if (contactItems.length === 0) {
        contactsRoot.innerHTML = '<div class="muted" style="padding: 20px; text-align: center;">Aucun contact public trouvé</div>';
    } else {
        contactItems.forEach(item => {
            const contactDiv = document.createElement("div");
            contactDiv.className = "contact-item";
            contactDiv.innerHTML = `
                <span class="contact-icon">${item.icon}</span>
                <a href="${safe(item.url)}" target="_blank">
                    ${safe(item.label)}
                    <span class="contact-label">${safe(item.url.replace(/^https?:\/\//, "").substring(0, 40))}${item.url.length > 43 ? "..." : ""}</span>
                </a>
            `;
            contactsRoot.appendChild(contactDiv);
        });
    }

    // JSON brut
    document.getElementById("raw-json").textContent = JSON.stringify(data, null, 2);
}

function setText(id, text) { document.getElementById(id).textContent = text; }
function safe(s) { return String(s ?? "").replace(/[<>&]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;" }[c])); }
function fillList(id, items) {
    const root = document.getElementById(id);
    root.innerHTML = items.map((x) => `<li>${safe(x)}</li>`).join("");
}
function arrayToList(arr, title) {
    arr = Array.isArray(arr) ? arr : [];
    if (!arr.length) return "";
    return `<div><h4>${safe(title)}</h4><ul class="list">${arr.map((x) => `<li>${safe(x)}</li>`).join("")}</ul></div>`;
}
function arrayToTags(arr) {
    arr = Array.isArray(arr) ? arr : [];
    if (!arr.length) return "";
    return `<ul class="tags">${arr.map((x) => `<li>${safe(x)}</li>`).join("")}</ul>`;
}