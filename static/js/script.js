/* =================================================================
   QUESTLOG SCRIPT
   =================================================================
   This file contains all client-side logic for the QuestLog application.
   It is organized as follows:
   1. GLOBAL STATE & INITIALIZATION
   2. EVENT LISTENERS
   3. UI & NOTIFICATION FUNCTIONS
   4. QUEST-RELATED FUNCTIONS
   5. SETTINGS FUNCTIONS
   ================================================================= */

/* =================================================================
   1. GLOBAL STATE & INITIALIZATION
   ================================================================= */

/**
 * @global {number} currentXp - The user's current total experience points.
 * @global {number} level - The user's current level.
 */
let currentXp = 0;
let level = 1;

/**
 * Initializes the XP bar and user level from data provided by the server.
 * This function is called when the page loads.
 * @param {number} initialXp - The user's starting XP.
 * @param {number} initialLevel - The user's starting level.
 */
function initXp(initialXp, initialLevel) {
    currentXp = initialXp;
    level = initialLevel;
    updateXpBar();
}

/* =================================================================
   2. EVENT LISTENERS
   ================================================================= */

/**
 * Main event listener that runs when the DOM is fully loaded.
 * It sets up all page-specific event listeners to avoid errors on pages
 * where certain elements don't exist.
 */
document.addEventListener('DOMContentLoaded', function () {

    // --- MODAL TOGGLES & INTERACTIVITY ---

    // Toggles the "Add Custom Quest" modal visibility.
    const addQuestBtn = document.getElementById("addQuestBtn");
    if (addQuestBtn) {
        addQuestBtn.addEventListener("click", () => {
            const modal = document.getElementById("addQuestModal");
            if (modal) {
                const isVisible = modal.style.display === "block";
                modal.style.display = isVisible ? "none" : "block";
                if (!isVisible) {
                    modal.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    }

    // Shows the "Generate Random Quest" modal and scrolls to it.
    const randomQuestBtn = document.getElementById("randomQuestBtn");
    if (randomQuestBtn) {
        randomQuestBtn.addEventListener("click", () => {
            const modal = document.getElementById("randomQuestModal");
            if (modal) {
                modal.style.display = 'block';
                modal.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }

    // Resets the random quest result when a new category or difficulty is chosen.
    const questSelectors = document.querySelectorAll("#questDifficultySelect, #questCategorySelect");
    questSelectors.forEach(selector => {
        if (selector) {
            selector.addEventListener("change", () => {
                const resultDiv = document.getElementById("randomQuestResult");
                if (resultDiv) resultDiv.innerHTML = "";
            });
        }
    });

    // --- AJAX QUEST COMPLETION ---

    // Attaches an AJAX submit handler to all quest completion forms.
    const questForms = document.querySelectorAll('.quest-complete-form');
    questForms.forEach(form => {
        form.addEventListener('submit', handleQuestCompletion);
    });
});

/**
 * Handles the submission of the quest completion form via AJAX.
 * @param {Event} e - The form submission event.
 */
function handleQuestCompletion(e) {
    e.preventDefault();

    const form = e.target;
    const button = form.querySelector('.complete-btn');
    const xpReward = parseInt(button.getAttribute('data-xp-reward'), 10);
    const csrfToken = form.querySelector('input[name="csrf_token"]').value;

    button.disabled = true;
    button.textContent = 'Completing...';

    fetch(form.action, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: new URLSearchParams(new FormData(form))
    })
        .then(response => {
            // If the response is not ok, try to parse it as JSON for an error message.
            // If that fails, it's likely a non-JSON response (e.g., HTML from a redirect).
            if (!response.ok) {
                // Check content type to see if we got HTML (like a login page redirect)
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.indexOf("application/json") === -1) {
                    throw new Error("Your session may have expired. Please log in again.");
                }
                // Otherwise, we expect a JSON error message from the server.
                return response.json().then(err => { throw new Error(err.error || 'Server error'); });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Update XP and animate quest card removal
                addXp(xpReward);
                const questCard = form.closest('.quest-card');
                questCard.style.transition = 'all 0.5s ease';
                questCard.style.transform = 'scale(0.8)';
                questCard.style.opacity = '0';

                setTimeout(() => {
                    questCard.remove();
                    if (document.querySelectorAll('.quest-card').length === 0) {
                        const grid = document.getElementById('todayQuestsGrid');
                        if (grid) {
                            grid.innerHTML = '<p class="no-quests">No active quests. Click "Give Me a Quest" to get started!</p>';
                        }
                    }
                }, 500);

                showAlert(data.message, 'success');

                if (data.earned_trophies && data.earned_trophies.length > 0) {
                    data.earned_trophies.forEach(showTrophyNotification);
                }
            } else {
                throw new Error(data.error || 'Quest completion failed');
            }
        })
        .catch(error => {
            console.error('Error completing quest:', error);
            showAlert(error.message, 'error');
            button.disabled = false;
            button.textContent = 'Complete Quest';

            // If the error suggests a session timeout, reload the page to force login.
            if (error.message.includes("session may have expired")) {
                setTimeout(() => {
                    window.location.reload();
                }, 2000); // Wait 2 seconds for the user to read the alert.
            }
        });
}

/* =================================================================
   3. UI & NOTIFICATION FUNCTIONS
   ================================================================= */

/**
 * Updates the XP circle UI with the current XP and level.
 */
function updateXpBar() {
    const xpCircle = document.getElementById('xpCircle');
    const xpLevelEl = document.getElementById('xpLevel');
    const xpAmountEl = document.getElementById('xpAmount');

    if (!xpCircle || !xpLevelEl || !xpAmountEl) return;

    const xpForCurrentLevel = Math.pow(level - 1, 2) * 100;
    const xpForNextLevel = Math.pow(level, 2) * 100;
    const xpNeededForLevel = xpForNextLevel - xpForCurrentLevel;
    const xpProgressInLevel = currentXp - xpForCurrentLevel;
    const fillPercentage = Math.max(0, Math.min(100, (xpProgressInLevel / xpNeededForLevel) * 100));

    xpLevelEl.textContent = `Level ${level}`;
    xpAmountEl.textContent = `${xpProgressInLevel}/${xpNeededForLevel} XP`;

    xpCircle.style.setProperty('--fill-percentage', `${fillPercentage}%`);
    xpCircle.style.background = `conic-gradient(var(--accent) 0% ${fillPercentage}%, var(--bg-dark) ${fillPercentage}% 100%)`;
}

/**
 * Adds XP, updates the UI, and checks if the user has leveled up.
 * @param {number} amount - The amount of XP to add.
 */
function addXp(amount) {
    const oldLevel = level;
    currentXp += amount;
    const newLevel = Math.floor(Math.sqrt(currentXp / 100)) + 1;

    updateXpBar();

    if (newLevel > oldLevel) {
        level = newLevel; // Update global level
        setTimeout(() => {
            showOverlay();
            triggerConfetti();
        }, 1200); // Delay to allow the XP bar animation to finish.
    }
}

/**
 * Triggers a confetti animation for level-ups.
 */
function triggerConfetti() {
    if (typeof confetti === 'function') {
        confetti({
            particleCount: 150,
            spread: 100,
            origin: { y: 1 }
        });
    }
}

/**
 * Shows the full-screen level up overlay.
 */
function showOverlay() {
    const overlay = document.getElementById('levelUpOverlay');
    if (overlay) overlay.style.display = 'flex';
}

/**
 * Hides the level up overlay and reloads the page.
 */
function hideOverlay() {
    window.location.reload();
}

/**
 * Displays a temporary notification alert at the top of the page.
 * @param {string} message - The message to display.
 * @param {string} type - The type of alert ('success', 'error', or 'info').
 */
function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.container');
    if (!alertContainer) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alertContainer.insertBefore(alert, alertContainer.firstChild);

    setTimeout(() => {
        alert.style.transition = 'opacity 0.5s ease';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 500);
    }, 3000);
}

/**
 * Shows a pop-up notification for a newly unlocked trophy.
 * @param {object} trophy - The trophy object from the server.
 */
function showTrophyNotification(trophy) {
    const notification = document.createElement('div');
    notification.className = 'trophy-notification';
    notification.innerHTML = `
        <div class="trophy-icon">${trophy.icon}</div>
        <div class="trophy-info">
            <h4>Trophy Unlocked!</h4>
            <p>${trophy.name}</p>
            <small>+${trophy.xp_reward} XP</small>
        </div>
    `;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(20px)';
        setTimeout(() => notification.remove(), 500);
    }, 4000);
}

/* =================================================================
   4. QUEST-RELATED FUNCTIONS
   ================================================================= */

/**
 * Fetches a randomly generated quest from the server.
 */
function generateRandomQuest() {
    const category = document.getElementById("questCategorySelect").value;
    const difficulty = document.getElementById("questDifficultySelect").value;
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const resultDiv = document.getElementById("randomQuestResult");

    if (!resultDiv) return;
    resultDiv.innerHTML = '<p>Generating quest...</p>';

    fetch('/generate_random_quest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: `category=${category}&difficulty=${difficulty}`
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                resultDiv.innerHTML = `
                <div class="generated-quest">
                    <h4>Generated Quest:</h4>
                    <p class="quest-text">${data.quest.name}</p>
                    <div class="quest-details">
                        <span class="category-badge category-${data.quest.category}">${data.quest.category}</span>
                        <span class="difficulty-badge difficulty-${data.quest.difficulty}">${data.quest.difficulty}</span>
                        <span class="quest-xp">+${data.quest.xp_reward} XP</span>
                    </div>
                    <div class="quest-actions">
                        <button onclick="acceptRandomQuest()" class="btn-primary">Accept Quest</button>
                        <button onclick="generateRandomQuest()" class="btn-secondary">Generate Another</button>
                    </div>
                </div>
            `;
            } else {
                resultDiv.innerHTML = `<p class="error-message">${data.error || 'Failed to generate quest.'}</p>`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            resultDiv.innerHTML = '<p class="error-message">Error generating quest. Please try again.</p>';
        });
}

/**
 * Sends the accepted random quest to the server.
 */
function acceptRandomQuest() {
    const resultDiv = document.getElementById("randomQuestResult");
    if (!resultDiv) return;

    const questTextEl = resultDiv.querySelector('.quest-text');
    if (!questTextEl) {
        showAlert('Could not find quest to accept.', 'error');
        return;
    }

    const body = new URLSearchParams({
        name: questTextEl.textContent,
        category: document.getElementById("questCategorySelect").value,
        difficulty: document.getElementById("questDifficultySelect").value
    });

    fetch('/add_random_quest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: body.toString()
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message || 'Quest added successfully!', 'success');
                document.getElementById("randomQuestModal").style.display = "none";
                resultDiv.innerHTML = "";
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showAlert(data.error || 'Failed to add quest.', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error adding quest. Please try again.', 'error');
        });
}

/**
 * Sends a new custom quest to the server.
 */
function addCustomQuest() {
    const name = document.getElementById('customQuestName').value.trim();
    if (!name) {
        showAlert('Quest name is required.', 'error');
        return;
    }

    const body = new URLSearchParams({
        name: name,
        description: document.getElementById('customQuestDescription').value.trim(),
        category: document.getElementById('customQuestCategory').value,
        difficulty: document.getElementById('customQuestDifficulty').value
    });

    fetch('/add_random_quest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: body.toString()
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Custom quest added successfully!', 'success');
                document.getElementById('addQuestModal').style.display = 'none';
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showAlert(data.error || 'Failed to add custom quest.', 'error');
            }
        })
        .catch(error => {
            console.error('Error adding custom quest:', error);
            showAlert('An error occurred while adding the quest.', 'error');
        });
}

/* =================================================================
   5. SETTINGS FUNCTIONS
   ================================================================= */

/**
 * Navigates to the settings page.
 */
function openSettings() {
    window.location.href = '/settings';
}

/**
 * Resets user progress. NOTE: This is a demo function.
 */
function resetProgress() {
    if (confirm("Are you sure you want to reset everything? This action cannot be undone.")) {
        localStorage.clear();
        showAlert("Your progress has been reset.", 'info');
        setTimeout(() => window.location.href = '/', 1000);
    }
}

/**
 * Shows a simple credits alert.
 */
function showCredits() {
    const email1 = 'delbani3232@gmail.com'
    alert(`QuestLog made by Delbani 🖤.\nIf you have any problems please contact the developer!\nEmail: ${email1}`);
}
