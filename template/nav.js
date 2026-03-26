document.addEventListener("DOMContentLoaded", () => {
  const nav = document.querySelector(".site-nav");
  const btn = document.querySelector(".nav-toggle");
  if (nav) {
    document.body.classList.add("has-side-nav");
  }
  if (!nav || !btn) return;
  btn.addEventListener("click", () => {
    nav.classList.toggle("open");
  });
});
