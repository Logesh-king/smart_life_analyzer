/* ═══════════════════════════════════════════════════════════════
   Smart Life Analyzer — Main JavaScript
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    initMobileSidebar();
    initEmojiSelector();
    initDailyEntryForm();
    initCharts();
    initAlertDismiss();
    initAccordion();
    initDeactivateModal();
    initThemeCards();
    initPhotoUpload();
});

/* ── Mobile Sidebar Toggle ──────────────────────────────────── */

function initMobileSidebar() {
    const hamburger = document.getElementById('hamburger-btn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (!hamburger || !sidebar) return;

    function openSidebar() {
        sidebar.classList.add('open');
        if (overlay) overlay.classList.add('show');
        hamburger.innerHTML = '<i class="fas fa-times"></i>';
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('show');
        hamburger.innerHTML = '<i class="fas fa-bars"></i>';
        document.body.style.overflow = '';
    }

    hamburger.addEventListener('click', () => {
        if (sidebar.classList.contains('open')) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    // Close on overlay click
    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    // Close on ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && sidebar.classList.contains('open')) {
            closeSidebar();
        }
    });

    // Close sidebar when a nav link is clicked (mobile)
    const navLinks = sidebar.querySelectorAll('.nav-item');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                closeSidebar();
            }
        });
    });

    // Handle resize - close sidebar if resizing past breakpoint
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (window.innerWidth > 768 && sidebar.classList.contains('open')) {
                closeSidebar();
            }
        }, 150);
    });

    // Touch swipe to close sidebar
    let touchStartX = 0;
    let touchEndX = 0;

    sidebar.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    sidebar.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        if (touchStartX - touchEndX > 60) {
            closeSidebar();
        }
    }, { passive: true });
}

/* ── Emoji Selector ──────────────────────────────────────────── */

function initEmojiSelector() {
    const emojiOptions = document.querySelectorAll('.emoji-option');
    const moodValue = document.getElementById('mood-value');

    if (!moodValue) return;

    emojiOptions.forEach(option => {
        option.addEventListener('click', () => {
            emojiOptions.forEach(opt => opt.classList.remove('selected'));
            option.classList.add('selected');
            moodValue.value = option.getAttribute('data-mood');
        });
    });
}

/* ── Daily Entry Form (AJAX submit) ──────────────────────────── */

function initDailyEntryForm() {
    const form = document.getElementById('daily-entry-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;

        try {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            submitBtn.disabled = true;

            const response = await fetch(form.action || window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            const data = await response.json();

            if (data.success) {
                showAlert('Entry saved successfully!', 'success');
                // Reload to show updated recent entries
                setTimeout(() => window.location.reload(), 800);
            } else {
                showAlert(data.message || 'Error saving entry.', 'error');
            }
        } catch (error) {
            // If not JSON (regular form post), reload
            form.submit();
        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    });
}

/* ── Chart.js Initialization ─────────────────────────────────── */

function initCharts() {
    initWeeklyChart();
    initMoodChart();
}

function initWeeklyChart() {
    const canvas = document.getElementById('weeklyChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const labels = JSON.parse(canvas.dataset.labels || '[]');
    const sleepData = JSON.parse(canvas.dataset.sleep || '[]');
    const workData = JSON.parse(canvas.dataset.work || '[]');

    if (labels.length === 0) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Sleep (hours)',
                    data: sleepData,
                    borderColor: '#4361ee',
                    backgroundColor: 'rgba(67, 97, 238, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#4361ee',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                },
                {
                    label: 'Study/Work (hours)',
                    data: workData,
                    borderColor: '#4cc9f0',
                    backgroundColor: 'rgba(76, 201, 240, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#4cc9f0',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: { family: 'Poppins', size: 13 },
                    },
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 12,
                    title: {
                        display: true,
                        text: 'Hours',
                        font: { family: 'Poppins' },
                    },
                    grid: { color: 'rgba(0,0,0,0.05)' },
                },
                x: {
                    grid: { display: false },
                },
            },
            interaction: {
                intersect: false,
                mode: 'index',
            },
        },
    });
}

function initMoodChart() {
    const canvas = document.getElementById('moodChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const labels = JSON.parse(canvas.dataset.labels || '[]');
    const scores = JSON.parse(canvas.dataset.scores || '[]');
    const colors = JSON.parse(canvas.dataset.colors || '[]');
    const borders = JSON.parse(canvas.dataset.borders || '[]');

    if (labels.length === 0) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Mood Score',
                data: scores,
                backgroundColor: colors,
                borderColor: borders,
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10,
                    title: {
                        display: true,
                        text: 'Score (1-10)',
                        font: { family: 'Poppins' },
                    },
                    grid: { color: 'rgba(0,0,0,0.05)' },
                },
                x: {
                    grid: { display: false },
                },
            },
        },
    });
}

/* ── Alert Helper ────────────────────────────────────────────── */

function showAlert(message, type = 'success') {
    const existing = document.querySelector('.alert-dynamic');
    if (existing) existing.remove();

    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
    };

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dynamic`;
    alert.innerHTML = `<i class="${icons[type] || icons.success}"></i> ${message}`;

    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.insertBefore(alert, mainContent.firstChild);
    }

    setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 300);
    }, 4000);
}

/* ── Dismiss Alerts ──────────────────────────────────────────── */

function initAlertDismiss() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}

/* ── Accordion (Only One Open at a Time) ─────────────────────── */

function initAccordion() {
    const headers = document.querySelectorAll('.accordion-header');
    if (headers.length === 0) return;

    headers.forEach(header => {
        header.addEventListener('click', () => {
            const item = header.closest('.accordion-item');
            const isOpen = item.classList.contains('active');

            // Close all accordion items
            document.querySelectorAll('.accordion-item.active').forEach(openItem => {
                openItem.classList.remove('active');
            });

            // Open the clicked one (if it wasn't already open)
            if (!isOpen) {
                item.classList.add('active');

                // Smooth scroll so the opened section is fully visible
                setTimeout(() => {
                    item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 150);
            }
        });
    });
}

/* ── Deactivation Confirmation Modal ─────────────────────────── */

function initDeactivateModal() {
    const deactivateBtn = document.getElementById('deactivate-btn');
    const modal = document.getElementById('deactivate-modal');
    const cancelBtn = document.getElementById('modal-cancel');
    const confirmBtn = document.getElementById('modal-confirm');
    const form = document.getElementById('deactivate-form');

    if (!deactivateBtn || !modal) return;

    deactivateBtn.addEventListener('click', () => {
        modal.classList.add('show');
    });

    cancelBtn.addEventListener('click', () => {
        modal.classList.remove('show');
    });

    // Close modal when clicking on overlay background
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.remove('show');
    });

    confirmBtn.addEventListener('click', () => {
        form.submit();
    });
}

/* ── Theme Card Selection ────────────────────────────────────── */

function initThemeCards() {
    const cards = document.querySelectorAll('.theme-card');
    if (cards.length === 0) return;

    cards.forEach(card => {
        const radio = card.querySelector('input[type="radio"]');
        card.addEventListener('click', () => {
            // Deselect all
            cards.forEach(c => c.classList.remove('active'));
            // Select clicked
            card.classList.add('active');
            radio.checked = true;
        });
    });
}

/* ── Profile Photo Upload ────────────────────────────────────── */

function initPhotoUpload() {
    const photoInput = document.getElementById('profile-photo-input');
    const photoForm = document.getElementById('photo-upload-form');
    const photoPreview = document.getElementById('photo-preview');

    if (!photoInput || !photoForm) return;

    photoInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
            showAlert('Please select a valid image file.', 'error');
            return;
        }

        // Validate file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            showAlert('Image file size must be under 5MB.', 'error');
            return;
        }

        // Show instant preview
        if (photoPreview) {
            const reader = new FileReader();
            reader.onload = (ev) => {
                photoPreview.innerHTML = `<img src="${ev.target.result}" alt="Preview" style="width:100%;height:100%;object-fit:cover;">`;
            };
            reader.readAsDataURL(file);
        }

        // Auto-submit the form
        photoForm.submit();
    });
}

