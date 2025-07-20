// Pinterest-style grid auto-sizing
function setPinterestGrid() {
    const grid = document.getElementById('pinterest-grid');
    if (!grid) return;
    
    const cards = grid.querySelectorAll('.pinterest-card');
    cards.forEach(card => {
        const img = card.querySelector('.card-image');
        if (img && img.complete) {
            const spans = Math.ceil((img.offsetHeight + 40) / 10);
            card.style.setProperty('--row-span', spans);
        } else if (img) {
            img.addEventListener('load', () => {
                const spans = Math.ceil((img.offsetHeight + 40) / 10);
                card.style.setProperty('--row-span', spans);
            });
        }
    });
}

// Form submission
function submitForm() {
    document.getElementById('search-form').submit();
}

// Toggle functions
function toggleLike(postId) {
    fetch(`/auth/like-post/${postId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.liked !== undefined) {
            location.reload();
        }
    })
    .catch(error => console.error('Error:', error));
}

function toggleBookmark(postId) {
    fetch(`/auth/bookmark-toggle/${postId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.bookmarked !== undefined) {
            location.reload();
        }
    })
    .catch(error => console.error('Error:', error));
}

// Initialize grid and auto-submit
document.addEventListener('DOMContentLoaded', function() {
    // Set up Pinterest grid
    setPinterestGrid();
    
    // Auto-resize on window resize
    window.addEventListener('resize', setPinterestGrid);
    
    // Auto-submit search on Enter
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                submitForm();
            }
        });
    }
}); 