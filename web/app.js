/* ============================================================
   ReadEasy Reader - Application Logic & Dictionary Popover
   ============================================================ */

class ReadEasyApp {
  constructor() {
    this.currentPage = 1;
    this.totalPages = 171;
    this.currentMode = 'bilingual'; // 'bilingual', 'single', 'scan'
    this.currentTheme = 'sepia';    // 'sepia', 'light', 'dark'
    this.fontSize = 18;
    this.toc = [];
    this.vocabList = [];
    this.cachedPages = {};
    this.currentLookupData = null;
    this.selectedWord = '';
    this.speechSynth = window.speechSynthesis;
    this.swedishVoice = null;
    
    this.initElements();
    this.initSpeech();
    this.attachEvents();
    this.loadInitialData();
  }

  initElements() {
    this.scrollContainer = document.getElementById('reader-scroll-container');
    this.readerView = document.getElementById('reader-view');
    this.pageStatusLabel = document.getElementById('page-status-label');
    this.pagePercentLabel = document.getElementById('page-percent-label');
    this.pageSlider = document.getElementById('page-slider');
    this.pageJumpInput = document.getElementById('page-jump-input');
    this.fontSizeLabel = document.getElementById('font-size-label');
    this.dictPopover = document.getElementById('dict-popover');
    this.sidebar = document.getElementById('app-sidebar');
    this.tocList = document.getElementById('toc-list');
    this.vocabListEl = document.getElementById('vocab-list');
    this.vocabBadge = document.getElementById('vocab-count-badge');
  }

  initSpeech() {
    if (!this.speechSynth) return;
    const findVoice = () => {
      const voices = this.speechSynth.getVoices();
      this.swedishVoice = voices.find(v => v.lang.startsWith('sv')) || null;
    };
    findVoice();
    if (this.speechSynth.onvoiceschanged !== undefined) {
      this.speechSynth.onvoiceschanged = findVoice;
    }
  }

  attachEvents() {
    // Mode toggles
    document.getElementById('mode-bilingual').addEventListener('click', () => this.setMode('bilingual'));
    document.getElementById('mode-single').addEventListener('click', () => this.setMode('single'));
    document.getElementById('mode-scan').addEventListener('click', () => this.setMode('scan'));

    // Page navigation
    document.getElementById('btn-prev-page').addEventListener('click', () => this.prevPage());
    document.getElementById('btn-next-page').addEventListener('click', () => this.nextPage());
    document.getElementById('footer-prev-btn').addEventListener('click', () => this.prevPage());
    document.getElementById('footer-next-btn').addEventListener('click', () => this.nextPage());

    this.pageSlider.addEventListener('input', (e) => {
      this.goToPage(parseInt(e.target.value));
    });

    document.getElementById('btn-jump-go').addEventListener('click', () => {
      const p = parseInt(this.pageJumpInput.value);
      if (p >= 1 && p <= this.totalPages) this.goToPage(p);
    });

    this.pageJumpInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const p = parseInt(this.pageJumpInput.value);
        if (p >= 1 && p <= this.totalPages) this.goToPage(p);
      }
    });

    // Font size controls
    document.getElementById('btn-font-dec').addEventListener('click', () => this.adjustFontSize(-1));
    document.getElementById('btn-font-inc').addEventListener('click', () => this.adjustFontSize(1));

    // Theme toggles
    document.querySelectorAll('.theme-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const theme = e.target.getAttribute('data-theme');
        this.setTheme(theme);
      });
    });

    // Sidebar toggle
    document.getElementById('btn-sidebar-toggle').addEventListener('click', () => {
      this.sidebar.classList.toggle('collapsed');
    });

    // Sidebar tabs
    document.querySelectorAll('.sidebar-tabs .tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.sidebar-tabs .tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        btn.classList.add('active');
        const tabId = btn.getAttribute('data-tab');
        document.getElementById(`tab-${tabId}`).classList.add('active');
      });
    });

    // Search
    document.getElementById('btn-do-search').addEventListener('click', () => this.doSearch());
    document.getElementById('search-query').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') this.doSearch();
    });

    // Keyboard navigation
    window.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        this.prevPage();
      } else if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {
        e.preventDefault();
        this.nextPage();
      } else if (e.key === 'b' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        this.sidebar.classList.toggle('collapsed');
      }
    });

    // Selection Dictionary Popover
    document.addEventListener('selectionchange', () => this.handleSelectionChange());
    document.addEventListener('mouseup', (e) => {
      setTimeout(() => this.checkSelectedText(e), 50);
    });

    // Dismiss popover on outside click
    document.addEventListener('mousedown', (e) => {
      if (!this.dictPopover.classList.contains('hidden')) {
        if (!this.dictPopover.contains(e.target)) {
          this.hidePopover();
        }
      }
    });

    // Popover Audio Speech
    document.getElementById('popover-speak-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      this.speakCurrentWord();
    });

    // Popover Star / Save to Vocab
    document.getElementById('popover-save-vocab-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggleSaveVocab();
    });

    // Save scroll on debounce
    let scrollTimeout = null;
    this.scrollContainer.addEventListener('scroll', () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => this.saveState(), 400);
    });
  }

  async loadInitialData() {
    try {
      const resp = await fetch('/api/book_info');
      const data = await resp.json();
      
      this.totalPages = data.total_pages || 171;
      this.pageSlider.max = this.totalPages;
      this.pageJumpInput.max = this.totalPages;
      document.getElementById('toc-total-pages').innerText = `共 ${this.totalPages} 页`;
      
      if (data.book_title) {
        document.getElementById('book-title').innerText = data.book_title;
      }

      // Restore saved state
      const state = data.state || {};
      if (state.current_page) this.currentPage = state.current_page;
      if (state.mode) this.setMode(state.mode, false);
      if (state.theme) this.setTheme(state.theme, false);
      if (state.font_size) this.setFontSize(state.font_size, false);

      // Populate TOC
      this.toc = data.toc || [];
      this.renderTOC();

      // Load Vocab list
      this.loadVocabList();

      // Load initial page
      await this.goToPage(this.currentPage, state.scroll_y || 0);

    } catch (err) {
      console.error('Error loading initial data:', err);
      this.goToPage(1);
    }
  }

  renderTOC() {
    this.tocList.innerHTML = '';
    this.toc.forEach(item => {
      const li = document.createElement('li');
      li.className = `toc-item ${item.page === this.currentPage ? 'active' : ''}`;
      li.innerHTML = `
        <span class="toc-title">${this.escapeHtml(item.title)}</span>
        <span class="toc-page-num">${item.page}</span>
      `;
      li.addEventListener('click', () => {
        this.goToPage(item.page);
        if (window.innerWidth < 800) this.sidebar.classList.add('collapsed');
      });
      this.tocList.appendChild(li);
    });
  }

  async loadVocabList() {
    try {
      const res = await fetch('/api/vocab');
      this.vocabList = await res.json();
      this.renderVocabList();
    } catch (e) {
      console.error(e);
    }
  }

  renderVocabList() {
    this.vocabBadge.innerText = this.vocabList.length;
    this.vocabListEl.innerHTML = '';
    if (this.vocabList.length === 0) {
      this.vocabListEl.innerHTML = '<li class="text-muted" style="text-align:center;padding:20px 0;">生词本为空，选词查字典时点击 ⭐ 即可收藏</li>';
      return;
    }

    this.vocabList.forEach(item => {
      const li = document.createElement('li');
      li.className = 'vocab-item';
      li.innerHTML = `
        <div class="vocab-word-row">
          <span class="vocab-word">${this.escapeHtml(item.word)}</span>
          <span class="vocab-pos">${this.escapeHtml(item.pos || '')}</span>
        </div>
        <div class="vocab-zh">${this.escapeHtml(item.zh || '')}</div>
        <button class="vocab-del-btn" title="删除">×</button>
      `;
      li.querySelector('.vocab-del-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        this.removeVocab(item.word);
      });
      li.addEventListener('click', () => {
        this.showPopoverForVocab(item);
      });
      this.vocabListEl.appendChild(li);
    });
  }

  async removeVocab(word) {
    try {
      await fetch('/api/vocab/remove', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({word})
      });
      this.vocabList = this.vocabList.filter(x => x.word !== word);
      this.renderVocabList();
    } catch (e) {
      console.error(e);
    }
  }

  setMode(mode, save = true) {
    this.currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`mode-${mode}`).classList.add('active');

    this.readerView.className = `reader-view view-${mode}`;
    this.renderCurrentPage();
    if (save) this.saveState();
  }

  setTheme(theme, save = true) {
    this.currentTheme = theme;
    document.body.className = `theme-${theme} font-serif`;
    document.querySelectorAll('.theme-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-theme') === theme);
    });
    if (save) this.saveState();
  }

  adjustFontSize(delta) {
    this.setFontSize(Math.min(28, Math.max(14, this.fontSize + delta)));
  }

  setFontSize(size, save = true) {
    this.fontSize = size;
    document.body.style.fontSize = `${size}px`;
    this.fontSizeLabel.innerText = size;
    if (save) this.saveState();
  }

  prevPage() {
    if (this.currentPage > 1) {
      this.goToPage(this.currentPage - 1);
    }
  }

  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.goToPage(this.currentPage + 1);
    }
  }

  async goToPage(pageNum, scrollY = 0) {
    if (pageNum < 1) pageNum = 1;
    if (pageNum > this.totalPages) pageNum = this.totalPages;

    this.currentPage = pageNum;
    this.pageSlider.value = pageNum;
    this.pageJumpInput.value = pageNum;
    this.pageStatusLabel.innerText = `第 ${pageNum} 页 / 共 ${this.totalPages} 页`;
    const percent = ((pageNum / this.totalPages) * 100).toFixed(1);
    this.pagePercentLabel.innerText = `(${percent}%)`;

    // Highlight in TOC
    document.querySelectorAll('.toc-item').forEach(el => {
      el.classList.toggle('active', parseInt(el.querySelector('.toc-page-num')?.innerText) === pageNum);
    });

    this.hidePopover();
    await this.fetchAndRenderPage(pageNum, scrollY);
    this.saveState();
  }

  async fetchAndRenderPage(pageNum, scrollY = 0) {
    this.readerView.innerHTML = '<div class="reader-loading">正在排版第 ' + pageNum + ' 页...</div>';

    try {
      const resp = await fetch(`/api/page?num=${pageNum}&mode=${this.currentMode}`);
      const data = await resp.json();
      this.cachedPages[pageNum] = data;
      this.renderCurrentPage();
      
      if (scrollY > 0) {
        this.scrollContainer.scrollTop = scrollY;
      } else {
        this.scrollContainer.scrollTop = 0;
      }
    } catch (err) {
      console.error('Error fetching page:', err);
      this.readerView.innerHTML = '<div class="reader-loading" style="color:#ef4444;">页面加载失败，请重试</div>';
    }
  }

  renderCurrentPage() {
    const pageData = this.cachedPages[this.currentPage];
    if (!pageData) return;

    if (this.currentMode === 'bilingual') {
      this.renderBilingualView(pageData);
    } else if (this.currentMode === 'single') {
      this.renderSingleView(pageData);
    } else if (this.currentMode === 'scan') {
      this.renderScanView(pageData);
    }
  }

  renderBilingualView(data) {
    const parasSv = data.paragraphs || [];
    const parasZh = data.translations || [];

    if (parasSv.length === 0) {
      this.readerView.innerHTML = '<div class="reader-loading">本页为空白页或无文本</div>';
      return;
    }

    let html = '<div class="bilingual-grid">';
    for (let i = 0; i < parasSv.length; i++) {
      const sv = parasSv[i];
      const zh = parasZh[i] || '（正在翻译...）';
      const isTitle = sv.length < 30 && (sv === sv.toUpperCase() || sv.startsWith('PROLOG'));

      if (isTitle) {
        html += `
          <div class="para-pair chapter-title-pair" data-idx="${i}">
            <div class="chapter-title-sv">${this.escapeHtml(sv)}</div>
            <div class="chapter-title-zh">${this.escapeHtml(zh)}</div>
          </div>
        `;
      } else {
        html += `
          <div class="para-pair" data-idx="${i}">
            <div class="para-sv">${this.wrapWordsWithSpans(sv)}</div>
            <div class="para-zh">${this.escapeHtml(zh)}</div>
          </div>
        `;
      }
    }
    html += '</div>';

    this.readerView.innerHTML = html;
  }

  renderSingleView(data) {
    const parasSv = data.paragraphs || [];
    if (parasSv.length === 0) {
      this.readerView.innerHTML = '<div class="reader-loading">本页为空白页</div>';
      return;
    }

    let html = '<div class="single-text-container">';
    parasSv.forEach(sv => {
      const isTitle = sv.length < 30 && (sv === sv.toUpperCase() || sv.startsWith('PROLOG'));
      if (isTitle) {
        html += `<h2 class="single-chapter-title">${this.escapeHtml(sv)}</h2>`;
      } else {
        html += `<p class="single-para">${this.wrapWordsWithSpans(sv)}</p>`;
      }
    });
    html += '</div>';

    this.readerView.innerHTML = html;
  }

  renderScanView(data) {
    const imgUrl = `/api/page_image?num=${this.currentPage}`;
    const lines = data.lines || [];
    const imgW = data.img_width || 1240;
    const imgH = data.img_height || 1755;

    let overlayHtml = '';
    lines.forEach(line => {
      (line.words || []).forEach(w => {
        const box = w.box || [0,0,10,10];
        const leftPct = (box[0] / imgW) * 100;
        const topPct = (box[1] / imgH) * 100;
        const widthPct = (box[2] / imgW) * 100;
        const heightPct = (box[3] / imgH) * 100;
        overlayHtml += `
          <span class="scan-word-box" style="left:${leftPct}%;top:${topPct}%;width:${widthPct}%;height:${heightPct}%;" data-word="${this.escapeHtml(w.text)}">${this.escapeHtml(w.text)}</span>
        `;
      });
    });

    this.readerView.innerHTML = `
      <div class="scan-container">
        <img class="scan-img" src="${imgUrl}" alt="Page ${this.currentPage}">
        <div class="scan-overlay-layer">${overlayHtml}</div>
      </div>
    `;
  }

  wrapWordsWithSpans(text) {
    // Preserve words for selection
    return this.escapeHtml(text);
  }

  /* ================= DICTIONARY POPOVER LOGIC ================= */
  handleSelectionChange() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.toString().trim()) {
      // If selection is cleared, dismiss popover
      if (this.dictPopover && !this.dictPopover.classList.contains('hidden')) {
        // Wait briefly in case user is finishing a multi-click
        setTimeout(() => {
          const currentSel = window.getSelection();
          if (!currentSel || currentSel.isCollapsed) {
            this.hidePopover();
          }
        }, 120);
      }
    }
  }

  async checkSelectedText(e) {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) return;

    const rawText = sel.toString().trim();
    if (!rawText || rawText.length > 90) return;

    // Check if selection is inside reader view
    if (!this.readerView.contains(sel.anchorNode)) return;

    this.selectedWord = rawText;
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    
    // Position popover
    this.positionPopover(rect);
    // Fetch and show definitions
    await this.lookupWord(rawText);
  }

  positionPopover(rect) {
    this.dictPopover.classList.remove('hidden');
    const popoverW = 320;
    const popoverH = 200; // estimated

    let x = rect.left + (rect.width / 2) - 40;
    let y = rect.top - popoverH - 12;

    // Boundary detection
    if (x < 10) x = 10;
    if (x + popoverW > window.innerWidth - 10) {
      x = window.innerWidth - popoverW - 10;
    }

    const arrow = this.dictPopover.querySelector('.popover-arrow');

    if (y < 60) {
      // Place below selection
      y = rect.bottom + 12;
      arrow.style.top = '-7px';
      arrow.style.bottom = 'auto';
      arrow.style.borderTop = '1px solid var(--border-color)';
      arrow.style.borderLeft = '1px solid var(--border-color)';
      arrow.style.borderBottom = 'none';
      arrow.style.borderRight = 'none';
    } else {
      // Place above selection
      arrow.style.bottom = '-7px';
      arrow.style.top = 'auto';
      arrow.style.borderBottom = '1px solid var(--border-color)';
      arrow.style.borderRight = '1px solid var(--border-color)';
      arrow.style.borderTop = 'none';
      arrow.style.borderLeft = 'none';
    }

    // Set arrow horizontal position relative to selected word
    const arrowX = Math.max(16, Math.min(popoverW - 24, rect.left + (rect.width / 2) - x - 6));
    arrow.style.left = `${arrowX}px`;

    this.dictPopover.style.left = `${x}px`;
    this.dictPopover.style.top = `${y}px`;
  }

  async lookupWord(word) {
    document.getElementById('popover-word').innerText = word;
    document.getElementById('popover-pos').innerText = '...';
    document.getElementById('popover-zh-def').innerText = '正在查询字典...';
    document.getElementById('popover-lemma-row').classList.add('hidden');
    document.getElementById('popover-phonetic-row').classList.add('hidden');
    document.getElementById('popover-en-section').classList.add('hidden');
    
    const saveBtn = document.getElementById('popover-save-vocab-btn');
    const isSaved = this.vocabList.some(v => v.word.toLowerCase() === word.toLowerCase());
    saveBtn.classList.toggle('starred', isSaved);
    saveBtn.innerText = isSaved ? '⭐ 已保存' : '⭐ 记生词';

    try {
      const resp = await fetch(`/api/lookup?word=${encodeURIComponent(word)}`);
      const data = await resp.json();
      this.currentLookupData = data;

      document.getElementById('popover-word').innerText = data.word || word;
      document.getElementById('popover-pos').innerText = data.pos || '单词';
      document.getElementById('popover-zh-def').innerText = data.zh || '未找到释义';

      if (data.lemma && data.lemma.toLowerCase() !== data.word.toLowerCase()) {
        document.getElementById('popover-lemma').innerText = data.lemma;
        document.getElementById('popover-lemma-row').classList.remove('hidden');
      }

      if (data.phonetic) {
        document.getElementById('popover-phonetic').innerText = `[${data.phonetic}]`;
        document.getElementById('popover-phonetic-row').classList.remove('hidden');
      }

      if (data.en) {
        document.getElementById('popover-en-def').innerText = data.en;
        document.getElementById('popover-en-section').classList.remove('hidden');
      }

    } catch (e) {
      console.error(e);
      document.getElementById('popover-zh-def').innerText = '网络或字典服务暂时不可用';
    }
  }

  speakCurrentWord() {
    const word = this.selectedWord || document.getElementById('popover-word').innerText;
    if (!word) return;

    if (this.speechSynth) {
      const utter = new SpeechSynthesisUtterance(word);
      utter.lang = 'sv-SE';
      if (this.swedishVoice) utter.voice = this.swedishVoice;
      utter.rate = 0.9;
      this.speechSynth.speak(utter);
    }
  }

  async toggleSaveVocab() {
    if (!this.currentLookupData) return;
    const saveBtn = document.getElementById('popover-save-vocab-btn');
    const word = this.currentLookupData.word;
    const isSaved = this.vocabList.some(v => v.word.toLowerCase() === word.toLowerCase());

    if (isSaved) {
      await this.removeVocab(word);
      saveBtn.classList.remove('starred');
      saveBtn.innerText = '⭐ 记生词';
    } else {
      const item = {
        word: this.currentLookupData.word,
        pos: this.currentLookupData.pos,
        zh: this.currentLookupData.zh,
        lemma: this.currentLookupData.lemma,
        phonetic: this.currentLookupData.phonetic
      };
      await fetch('/api/vocab/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(item)
      });
      this.vocabList.unshift(item);
      this.renderVocabList();
      saveBtn.classList.add('starred');
      saveBtn.innerText = '⭐ 已保存';
    }
  }

  hidePopover() {
    if (this.dictPopover) {
      this.dictPopover.classList.add('hidden');
    }
  }

  /* ================= SEARCH LOGIC ================= */
  async doSearch() {
    const q = document.getElementById('search-query').value.trim();
    if (!q) return;

    const countEl = document.getElementById('search-results-count');
    const listEl = document.getElementById('search-results-list');
    countEl.innerText = '正在全书搜索中...';
    listEl.innerHTML = '';

    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      const results = data.results || [];
      countEl.innerText = `找到 ${results.length} 处匹配`;

      results.forEach(r => {
        const li = document.createElement('li');
        li.className = 'search-item';
        li.innerHTML = `
          <div class="search-item-page">第 ${r.page} 页</div>
          <div class="search-item-snippet">${r.snippet}</div>
        `;
        li.addEventListener('click', () => {
          this.goToPage(r.page);
          if (window.innerWidth < 800) this.sidebar.classList.add('collapsed');
        });
        listEl.appendChild(li);
      });
    } catch (e) {
      countEl.innerText = '搜索出错';
    }
  }

  /* ================= STATE PERSISTENCE ================= */
  async saveState() {
    const state = {
      current_page: this.currentPage,
      mode: this.currentMode,
      theme: this.currentTheme,
      font_size: this.fontSize,
      scroll_y: this.scrollContainer.scrollTop
    };

    try {
      await fetch('/api/save_state', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(state)
      });
    } catch (e) {
      // silently ignore network errors during close
    }
  }

  escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
}

window.addEventListener('DOMContentLoaded', () => {
  window.app = new ReadEasyApp();
});
