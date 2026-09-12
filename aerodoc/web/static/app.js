// AeroDoc Web Studio Client Controller
document.addEventListener('DOMContentLoaded', () => {
  // Elements
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

  // How to Use Modal
  const openGuideBtn = document.getElementById('openGuideBtn');
  const closeGuideBtn = document.getElementById('closeGuideBtn');
  const guideOverlay = document.getElementById('guideOverlay');

  // Stats
  const statDocType = document.getElementById('statDocType');
  const statReadability = document.getElementById('statReadability');
  const statPages = document.getElementById('statPages');
  const statWords = document.getElementById('statWords');
  const statTables = document.getElementById('statTables');
  const statEquations = document.getElementById('statEquations');
  const statCallouts = document.getElementById('statCallouts');
  const statImages = document.getElementById('statImages');
  const statSpeed = document.getElementById('statSpeed');

  // Toolbar & Actions
  const uniqueFilenameBadge = document.getElementById('uniqueFilenameBadge');
  const copyBtn = document.getElementById('copyBtn');
  const downloadMdBtn = document.getElementById('downloadMdBtn');
  const downloadZipBtn = document.getElementById('downloadZipBtn');
  const tabBtns = document.querySelectorAll('.tab-btn');

  // Viewer Panes
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
    if (files.length > 0 && files[0].name.toLowerCase().endsWith('.pdf')) {
      handleFileSelected(files[0]);
    } else {
      showToast('Please provide a valid .pdf document.');
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
    fileNamePreview.textContent = `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    convertBtn.disabled = false;
  }

  // 1-Click Sample Test Document
  loadSampleBtn.addEventListener('click', async (e) => {
    e.stopPropagation();
    loadSampleBtn.disabled = true;
    showToast('Loading pre-built benchmark test document...');

    try {
      const resp = await fetch('/api/sample');
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.error?.message || err.detail || 'Failed to load sample.');
      }
      const data = await resp.json();
      displayResults(data);
      showToast('Sample document synthesized successfully!');
    } catch (err) {
      showToast(`Error: ${err.message}`);
    } finally {
      loadSampleBtn.disabled = false;
    }
  });

  // Convert Trigger
  convertBtn.addEventListener('click', async () => {
    if (!currentFile) return;

    // UI Loading state
    convertBtn.disabled = true;
    btnSpinner.style.display = 'inline-block';
    btnText.textContent = 'Synthesizing...';

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
      showToast('Conversion complete! File ready.');
    } catch (err) {
      console.error(err);
      showToast(`Error: ${err.message}`);
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
    totalPages = data.stats.pages;
    currentPage = 1;

    // Populate Metrics
    statDocType.textContent = data.stats.document_type || 'Technical Document';
    statReadability.textContent = data.stats.readability_grade || 'General Audience';
    statPages.textContent = data.stats.pages;
    statWords.textContent = data.stats.word_count.toLocaleString();
    statTables.textContent = data.stats.tables_extracted;
    statEquations.textContent = data.stats.equations_found;
    statCallouts.textContent = data.stats.callouts_transformed;
    statImages.textContent = data.stats.images_extracted;
    statSpeed.textContent = `${data.stats.elapsed_seconds}s`;

    // Unique Download Filename
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

    // Render Formatted Content with Antigravity Alerts & KaTeX
    renderAntigravityMarkdown(currentMarkdown);

    // Update PDF page preview
    updatePagePreview();

    // Toggle Visibility
    emptyState.style.display = 'none';
    viewerContent.style.display = 'flex';
  }

  // Antigravity Markdown Renderer (Zero Blue)
  function renderAntigravityMarkdown(mdText) {
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

    // 4. Highlight code blocks
    if (window.Prism) {
      Prism.highlightAllUnder(mdRendered);
    }
  }

  // Page Preview Navigation
  function updatePagePreview() {
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
      updatePagePreview();
    }
  });

  nextPageBtn.addEventListener('click', () => {
    if (currentPage < totalPages) {
      currentPage++;
      updatePagePreview();
    }
  });

  // Tab View Switcher
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
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
      showToast('Copied full Antigravity Markdown to clipboard!');
    } catch (err) {
      mdRaw.select();
      document.execCommand('copy');
      showToast('Copied to clipboard!');
    }
  });

  // Download Action Listeners
  downloadMdBtn.addEventListener('click', () => {
    showToast(`Downloading: ${uniqueFilenameBadge.textContent}`);
  });

  function showToast(msg) {
    toast.textContent = msg;
    toast.style.display = 'block';
    setTimeout(() => {
      toast.style.display = 'none';
    }, 4000);
  }
});
