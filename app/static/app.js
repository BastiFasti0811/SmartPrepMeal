(() => {
  const copyButton = document.getElementById("copy-markdown");
  const markdown = document.getElementById("markdown-output");
  if (!copyButton || !markdown) {
    return;
  }

  copyButton.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(markdown.value);
      const old = copyButton.textContent;
      copyButton.textContent = "Kopiert";
      window.setTimeout(() => {
        copyButton.textContent = old;
      }, 1400);
    } catch (_err) {
      copyButton.textContent = "Copy fehlgeschlagen";
    }
  });
})();
