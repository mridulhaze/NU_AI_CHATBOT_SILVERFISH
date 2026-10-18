(function() {
  if (window.NUChatWidgetInitialized) return;
  window.NUChatWidgetInitialized = true;

  const currentScript = document.currentScript || (function() {
    const scripts = document.getElementsByTagName('script');
    return scripts[scripts.length - 1];
  })();

  const scriptSrc = currentScript ? currentScript.src : '';
  const apiBase = scriptSrc ? new URL(scriptSrc).origin : window.location.origin;

  // Configuration options via data attributes
  const title = currentScript?.getAttribute('data-title') || 'জাতীয় বিশ্ববিদ্যালয় এআই কাউন্সেলর';
  const primaryColor = currentScript?.getAttribute('data-color') || '#047857';

  // Floating Button Styles
  const style = document.createElement('style');
  style.innerHTML = `
    #nu-chat-bubble-btn {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: ${primaryColor};
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 14px rgba(0,0,0,0.25);
      cursor: pointer;
      z-index: 999998;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    #nu-chat-bubble-btn:hover {
      transform: scale(1.06);
      box-shadow: 0 6px 18px rgba(0,0,0,0.3);
    }
    #nu-chat-widget-frame {
      position: fixed;
      bottom: 90px;
      right: 24px;
      width: 380px;
      height: 560px;
      max-width: calc(100vw - 32px);
      max-height: calc(100vh - 110px);
      background: #ffffff;
      border-radius: 16px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.2);
      border: 1px solid #e2e8f0;
      z-index: 999999;
      display: none;
      flex-direction: column;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    #nu-chat-widget-frame.open {
      display: flex;
    }
    #nu-widget-header {
      background: ${primaryColor};
      color: white;
      padding: 12px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-weight: 600;
      font-size: 14px;
    }
    #nu-widget-iframe {
      width: 100%;
      height: 100%;
      border: none;
    }
  `;
  document.head.appendChild(style);

  // Widget Container
  const widgetBox = document.createElement('div');
  widgetBox.id = 'nu-chat-widget-frame';
  widgetBox.innerHTML = `
    <div id="nu-widget-header">
      <span>🎓 ${title}</span>
      <button id="nu-widget-close" style="background:none;border:none;color:white;font-size:18px;cursor:pointer;line-height:1;">✕</button>
    </div>
    <iframe id="nu-widget-iframe" src="${apiBase}/chat" title="NU AI Academic Counselor"></iframe>
  `;
  document.body.appendChild(widgetBox);

  // Floating Button
  const btn = document.createElement('div');
  btn.id = 'nu-chat-bubble-btn';
  btn.innerHTML = `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>`;
  btn.title = 'জাতীয় বিশ্ববিদ্যালয় এআই কাউন্সেলর';
  document.body.appendChild(btn);

  btn.addEventListener('click', () => {
    widgetBox.classList.toggle('open');
  });

  document.getElementById('nu-widget-close').addEventListener('click', () => {
    widgetBox.classList.remove('open');
  });
})();