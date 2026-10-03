// Server-rendered pages: apply the reader's saved theme and text size.
(() => {
  const root = document.documentElement;
  const theme = localStorage.getItem("curanews_theme");
  const size = localStorage.getItem("curanews_font_size");
  if (theme) root.dataset.theme = theme;
  if (size) root.dataset.fontSize = size;
})();
