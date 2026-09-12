// AeroDoc Executive Universal Studio Controller
document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const browseBtn = document.getElementById('browseBtn');
  const loadSampleBtn = document.getElementById('loadSampleBtn');
  const fileNamePreview = document.getElementById('fileNamePreview');
  const convertBtn = document.getElementById('convertBtn');
  const btnSpinner = document.getElementById('btnSpinner');
  const btnText = document.getElementById('btnText');

  const emptyState = document.getElementById('emptyState');
  const viewerContent = document.getElementById('viewerContent');
  const dualPanes = document.getElementById('dualPanes');

  // Architecture Guide Modal
  const openGuideBtn = document.getElementById('openGuideBtn');
  const closeGuideBtn = document.getElementById('closeGuideBtn');
  const guideOverlay = document.getElementById('guideOverlay');

  // Telemetry
  const statFormat = document.getElementById('statFormat');
  const statDocType = document.getElementById('statDocType');
  const statReadability = document.getElementById('statReadability');
  const statPages = document.getElementById('statPages');
  const statWords = document.getElementById('statWords');
  const statTables = document.getElementById('statTables');
  const statEquations = document.getElementById('statEquations');
  const statCallouts = document.getElementById('statCallouts');
  const statSpeed = document.getElementById('statSpeed');

  // Action Bar
  const uniqueFilenameBadge = document.getElementById('uniqueFilenameBadge');
  const copyBtn = document.getElementById('copyBtn');
  const downloadMdBtn = document.getElementById('downloadMdBtn');
  const downloadZipBtn = document.getElementById('downloadZipBtn');
  const modeBtns = document.querySelectorAll('.mode-btn');

  // Left & Right Canvases
  const pdfPane = document.getElementById('pdfPane');
  const pdfPageImg = document.getElementById('pdfPageImg');
  const prevPageBtn = document.getElementById('prevPageBtn');
  const nextPageBtn = document.getElementById('nextPageBtn');
  const pageIndicator = document.getElementById('pageIndicator');
  const mdRendered = document.getElementById('mdRendered');
  const mdRaw = document.getElementById('mdRaw');
  const toast = document.getElementById('toast');

  // State
  let currentFile = null;
  let currentSessionId = null;
  let currentPage = 1;
  let totalPages = 1;
  let currentMarkdown = '';

  // Allowed format extensions
  const ALLOWED_EXTS = [
    '.pdf', '.docx', '.doc', '.txt', '.text', '.log',
    '.csv', '.tsv', '.html', '.htm', '.rtf', '.json', '.yaml', '.md'
  ];

  // Modal Handlers
  openGuideBtn.addEventListener('click', () => {
    guideOverlay.style.display = 'flex';
  });

  closeGuideBtn.addEventListener('click', () => {
    guideOverlay.style.display = 'none';
  });

  guideOverlay.addEventListener('click', (e) => {
    if (e.target === guideOverlay) {
      guideOverlay.style.display = 'none';
    }
  });

  // Keyboard Shortcuts
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && guideOverlay.style.display === 'flex') {
      guideOverlay.style.display = 'none';
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      if (!convertBtn.disabled) {
        convertBtn.click();
      }
    }
  });

  // Drag and Drop
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      const fileName = files[0].name.toLowerCase();
      const isValid = ALLOWED_EXTS.some(ext => fileName.endsWith(ext));
      if (isValid) {
        handleFileSelected(files[0]);
      } else {
        showToast('Unsupported document type. Supported: PDF, DOCX, TXT, HTML, CSV, JSON.');
      }
    }
  });

  browseBtn.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('click', (e) => {
    if (e.target !== browseBtn && e.target !== loadSampleBtn && !loadSampleBtn.contains(e.target)) {
      fileInput.click();
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  function handleFileSelected(file) {
    currentFile = file;
    const ext = file.name.substring(file.name.lastIndexOf('.')).toUpperCase();
    fileNamePreview.textContent = `Selected: ${file.name} [${ext}] (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    convertBtn.disabled = false;
  }

  // 1-Click Sample Benchmark Trigger
  loadSampleBtn.addEventListener('click', async (e) => {
    e.stopPropagation();
    loadSampleBtn.disabled = true;
    showToast('Loading benchmark quantum architecture document...');

    try {
      const resp = await fetch('/api/sample');
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.error?.message || err.detail || 'Failed to load sample.');
      }
      const data = await resp.json();
      displayResults(data);
      showToast('Benchmark document synthesized successfully.');
    } catch (err) {
      showToast(`Error: ${err.message}`);
    } finally {
      loadSampleBtn.disabled = false;
    }
  });

  // Convert Trigger
  convertBtn.addEventListener('click', async () => {
    if (!currentFile) return;

    convertBtn.disabled = true;
    btnSpinner.style.display = 'inline-block';
    btnText.textContent = 'Synthesizing AST...';

    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('embed_images', document.getElementById('embedImages').checked);
    formData.append('include_frontmatter', document.getElementById('includeFrontmatter').checked);
    formData.append('detect_tables', document.getElementById('detectTables').checked);
    formData.append('detect_math', document.getElementById('detectMath').checked);
    formData.append('detect_callouts', document.getElementById('detectCallouts').checked);
    formData.append('unroll_columns', document.getElementById('unrollColumns').checked);

    try {
      const response = await fetch('/api/convert', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const err = await response.json();
        const msg = err.error?.message || err.detail || 'Conversion failed.';
        throw new Error(msg);
      }

      const data = await response.json();
      displayResults(data);
      showToast('Conversion complete. Document ready.');
    } catch (err) {
      console.error(err);
      showToast(`System Error: ${err.message}`);
    } finally {
      convertBtn.disabled = false;
      btnSpinner.style.display = 'none';
      btnText.textContent = 'Convert to Markdown (Ctrl+Enter)';
    }
  });

  // Display Conversion Results
  function displayResults(data) {
    currentSessionId = data.sessionId;
    currentMarkdown = data.markdown;
    totalPages = data.stats.pages || 1;
    currentPage = 1;

    // Populate Telemetry
    statFormat.textContent = data.format || 'DOCUMENT';
    statDocType.textContent = data.stats.document_type || 'Executive Document';
    statReadability.textContent = data.stats.readability_grade || 'Professional Audience';
    statPages.textContent = data.stats.pages || 1;
    statWords.textContent = data.stats.word_count.toLocaleString();
    statTables.textContent = data.stats.tables_extracted || 0;
    statEquations.textContent = data.stats.equations_found || 0;
    statCallouts.textContent = data.stats.callouts_transformed || 0;
    statSpeed.textContent = `${data.stats.elapsed_seconds || 0}s`;

    // Unique Download Name
    uniqueFilenameBadge.textContent = data.uniqueFilename;
    uniqueFilenameBadge.title = `Unique Download Name: ${data.uniqueFilename}`;

    // Setup Download Links
    downloadMdBtn.href = `/api/download/md/${data.sessionId}`;
    downloadMdBtn.setAttribute('download', data.uniqueFilename);

    if (data.uniqueZipFilename) {
      downloadZipBtn.href = `/api/download/zip/${data.sessionId}`;
      downloadZipBtn.setAttribute('download', data.uniqueZipFilename);
      downloadZipBtn.style.display = 'inline-flex';
    } else {
      downloadZipBtn.style.display = 'none';
    }

    // Set Raw Content
    mdRaw.value = currentMarkdown;

    // Render Editorial Markdown with Antigravity Alerts & KaTeX
    renderEditorialMarkdown(currentMarkdown);

    // Update Blueprint Viewport
    updateBlueprintPreview();

    // Toggle Visibility
    emptyState.style.display = 'none';
    viewerContent.style.display = 'flex';
  }

  // Antigravity Markdown Renderer (Clean Hairline Styling)
  function renderEditorialMarkdown(mdText) {
    // 1. Transform Antigravity / GitHub Alerts
    let processedText = mdText.replace(
      />\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\n((?:>.*(?:\n|$))*)/g,
      (match, alertType, content) => {
        const cleanContent = content.replace(/^>\s?/gm, '').trim();
        return `<div class="alert-box alert-${alertType}">
          <div class="alert-title">${alertType}</div>
          <p>${cleanContent}</p>
        </div>`;
      }
    );

    // 2. Parse Markdown with marked.js
    const html = marked.parse(processedText);
    mdRendered.innerHTML = html;

    // 3. Render KaTeX Formulas
    if (window.renderMathInElement) {
      renderMathInElement(mdRendered, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\(', right: '\\)', display: false },
          { left: '\\[', right: '\\]', display: true }
        ],
        throwOnError: false
      });
    }

    // 4. Syntax Highlight Code Blocks
    if (window.Prism) {
      Prism.highlightAllUnder(mdRendered);
    }
  }

  // Blueprint Preview Navigation
  function updateBlueprintPreview() {
    pageIndicator.textContent = `Page ${currentPage} / ${totalPages}`;
    prevPageBtn.disabled = (currentPage <= 1);
    nextPageBtn.disabled = (currentPage >= totalPages);

    if (currentSessionId) {
      pdfPageImg.src = `/api/page-preview/${currentSessionId}/${currentPage}`;
    }
  }

  prevPageBtn.addEventListener('click', () => {
    if (currentPage > 1) {
      currentPage--;
      updateBlueprintPreview();
    }
  });

  nextPageBtn.addEventListener('click', () => {
    if (currentPage < totalPages) {
      currentPage++;
      updateBlueprintPreview();
    }
  });

  // Mode View Switcher
  modeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      modeBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const view = btn.getAttribute('data-view');
      dualPanes.classList.remove('rendered-only', 'raw-only');

      if (view === 'split') {
        mdRendered.style.display = 'block';
        mdRaw.style.display = 'none';
      } else if (view === 'rendered') {
        dualPanes.classList.add('rendered-only');
        mdRendered.style.display = 'block';
        mdRaw.style.display = 'none';
      } else if (view === 'raw') {
        dualPanes.classList.add('raw-only');
      }
    });
  });

  // Clipboard Copy Action
  copyBtn.addEventListener('click', async () => {
    if (!currentMarkdown) return;
    try {
      await navigator.clipboard.writeText(currentMarkdown);
      showToast('Document Markdown copied to system clipboard.');
    } catch (err) {
      mdRaw.select();
      document.execCommand('copy');
      showToast('Copied to clipboard.');
    }
  });

  // Download Feedback
  downloadMdBtn.addEventListener('click', () => {
    showToast(`Streaming: ${uniqueFilenameBadge.textContent}`);
  });

  function showToast(msg) {
    toast.textContent = msg;
    toast.style.display = 'block';
    setTimeout(() => {
      toast.style.display = 'none';
    }, 3800);
  }
});
