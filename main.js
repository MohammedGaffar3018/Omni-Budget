// Main JavaScript file for OmniBudget

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips and other UI elements
    initializeTooltips();
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize any charts or data visualizations
    initializeCharts();
});

function initializeTooltips() {
    // Simple tooltip implementation
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltipText = this.getAttribute('data-tooltip');
            
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = tooltipText;
            
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
            
            this.tooltip = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this.tooltip) {
                document.body.removeChild(this.tooltip);
                this.tooltip = null;
            }
        });
    });
}

function setupEventListeners() {
    // Profile switcher
    const profileOptions = document.querySelectorAll('.profile-option');
    profileOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            const profile = this.getAttribute('data-profile');
            window.location.href = `/switch_profile/${profile}`;
        });
    });
    
    // Mobile menu toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navbarMenu = document.querySelector('.navbar-menu');
    
    if (mobileMenuToggle && navbarMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            navbarMenu.classList.toggle('active');
        });
    }
    
    // Voice command button for Guardian theme
    const voiceBtn = document.querySelector('.voice-btn');
    if (voiceBtn) {
        voiceBtn.addEventListener('click', function() {
            // Placeholder for voice command functionality
            alert('Voice commands would be activated here. This feature requires Web Speech API integration.');
        });
    }
}

function initializeCharts() {
    // Placeholder for chart initialization
    // In a real implementation, you would use a library like Chart.js
    console.log('Charts would be initialized here');
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-IN', options);
}

// Export to Excel functionality for Builder theme
function exportToExcel() {
    // Placeholder for Excel export functionality
    // In a real implementation, you would use a library like SheetJS
    alert('Excel export would be triggered here. This feature requires a library like SheetJS.');
}

// UPI intent link generation for Pacer theme
function generateUPIIntent(amount, note, recipient) {
    const upiID = recipient || ''; // Default empty, would be set by user
    const transactionNote = note || 'Payment via OmniBudget';
    
    // Create UPI intent URL
    const upiIntent = `upi://pay?pa=${upiID}&pn=OmniBudget&mc=0000&tid=TXN123456789&tr=TXN123456789&tn=${transactionNote}&am=${amount}&cu=INR`;
    
    // Open UPI app
    window.location.href = upiIntent;
}

// Accessibility functions for Guardian theme
function increaseFontSize() {
    document.body.style.fontSize = 'larger';
}

function decreaseFontSize() {
    document.body.style.fontSize = 'smaller';
}

function toggleHighContrast() {
    document.body.classList.toggle('high-contrast');
}