(() => {
  const language = document.documentElement.lang.startsWith("zh") ? "zh" : "en";
  document.querySelectorAll(".site-language-switch").forEach(link => {
    const base = link.getAttribute("href").split("#")[0];
    const sync = () => { link.href = base + window.location.hash; };
    sync();
    window.addEventListener("hashchange", sync);
    link.addEventListener("click", () => {
      try { localStorage.setItem("academic-site-language", language === "zh" ? "en" : "zh"); } catch (_) {}
    });
  });
})();
