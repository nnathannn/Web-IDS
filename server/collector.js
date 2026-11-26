async function collectAndSend() {
  const payload = {
    nonce: window.__NONCE__,
    ua: navigator.userAgent,
    platform: navigator.userAgentData?.platform ?? navigator.platform,
    lang: navigator.language,
    tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
    screen: {
      w: screen.width,
      h: screen.height,
      dpr: window.devicePixelRatio,
      depth: screen.colorDepth,
    },
    cores: navigator.hardwareConcurrency,
    touch: navigator.maxTouchPoints,
    webdriver: navigator.webdriver === true,
  };

  try {
    const res = await fetch("/fp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(payload),
    });
    const { verdict } = await res.json();
    if (verdict === "ALLOW") {
      window.location.href = "/home";
    } else {
      document.body.textContent = "Access denied: " + verdict;
    }
  } catch (e) {
    console.error("fingerprint post failed", e);
  }
}

window.addEventListener("load", collectAndSend);
