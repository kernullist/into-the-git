// Shared dashboard utilities
window.escapeHtml = function(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
};

window.formatDate = function(d) {
    if (!d) return 'N/A';
    return new Date(d).toLocaleDateString();
};

window.scoreColor = function(score) {
    if (score >= 75) return '#dc3545';
    if (score >= 50) return '#fd7e14';
    if (score >= 25) return '#ffc107';
    return '#17a2b8';
};
