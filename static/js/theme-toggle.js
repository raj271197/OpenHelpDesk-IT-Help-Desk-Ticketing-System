const themeToggle = document.getElementById('theme-toggle');
const storedTheme = localStorage.getItem('theme');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const currentTheme = storedTheme || (prefersDark ? 'dark' : 'light');

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  if (themeToggle) {
    themeToggle.textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
    themeToggle.classList.toggle('btn-outline-light', theme === 'light');
    themeToggle.classList.toggle('btn-outline-dark', theme === 'dark');
  }
}

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const nextTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', nextTheme);
    applyTheme(nextTheme);
  });
}

applyTheme(currentTheme);
