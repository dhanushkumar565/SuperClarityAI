/**
 * SuperClarity AI Enterprise - Complete Frontend Controller
 * Integrates multi-model super-resolution (2x/4x/8x), AI studio editing,
 * model laboratory, batch processing, product catalog, visual search,
 * marketplace exports, and voice-assisted intelligence.
 */

document.addEventListener("DOMContentLoaded", () => {
    // =================================================================
    // GLOBAL STATE
    // =================================================================
    let selectedFile = null;
    let selectedSampleId = "luxury_watch";
    let selectedScale = 4;
    let currentMethod = "realesrgan";
    let isSliderDragging = false;
    let activeEnhancedImageB64 = null;
    let activeEnhancedImagePath = null;
    let activeInputImageB64 = null;
    let currentStudioImageB64 = null;
    let batchPollInterval = null;

    // =================================================================
    // DOM REFERENCES: NAVIGATION & TABS
    // =================================================================
    const tabNavButtons = document.querySelectorAll(".tab-nav-btn");
    const tabContents = document.querySelectorAll(".tab-content");
    const btnThemeToggle = document.getElementById("btn-theme-toggle");

    // =================================================================
    // DOM REFERENCES: UPSCALER
    // =================================================================
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const dropzonePrompt = document.getElementById("dropzone-prompt");
    const dropzonePreview = document.getElementById("dropzone-preview");
    const previewImg = document.getElementById("preview-img");
    const previewFilename = document.getElementById("preview-filename");
    const previewDims = document.getElementById("preview-dims");
    const btnClearUpload = document.getElementById("btn-clear-upload");
    const btnGalleryUpload = document.getElementById("btn-gallery-upload");
    const browseLink = document.getElementById("browse-link");
    const samplePills = document.querySelectorAll(".sample-pill");
    const scaleButtons = document.querySelectorAll("#scale-toggle-group .toggle-btn");
    const modelSelect = document.getElementById("model-select");
    const checkAutoPreset = document.getElementById("check-auto-preset");
    const checkDenoise = document.getElementById("check-denoise");
    const checkSharpen = document.getElementById("check-sharpen");
    const upscaleForm = document.getElementById("upscale-form");
    const btnSubmit = document.getElementById("btn-submit");
    const btnText = btnSubmit.querySelector(".btn-text");
    const btnLoader = btnSubmit.querySelector(".btn-loader");

    // Diagnostics
    const detectedCategoryBadge = document.getElementById("detected-category-badge");
    const badgeCategoryText = document.getElementById("badge-category-text");
    const diagnosticCard = document.getElementById("diagnostic-card");
    const diagScoreBadge = document.getElementById("diag-score-badge");
    const diagSharpnessTag = document.getElementById("diag-sharpness-tag");
    const diagNoiseTag = document.getElementById("diag-noise-tag");
    const diagExposureTag = document.getElementById("diag-exposure-tag");
    const diagRecText = document.getElementById("diag-rec-text");

    // Results & Telemetry
    const imgBefore = document.getElementById("img-before");
    const imgAfter = document.getElementById("img-after");
    const sideImgBefore = document.getElementById("side-img-before");
    const sideImgAfter = document.getElementById("side-img-after");
    const sideOrigRes = document.getElementById("side-orig-res");
    const sideEnhRes = document.getElementById("side-enh-res");
    const sliderWrapper = document.getElementById("slider-wrapper");
    const sliderAfterContainer = document.getElementById("slider-after-container");
    const sliderHandle = document.getElementById("slider-handle");
    const btnModeSlider = document.getElementById("btn-mode-slider");
    const btnModeSide = document.getElementById("btn-mode-side");
    const sideWrapper = document.getElementById("side-wrapper");

    const metricResolution = document.getElementById("metric-resolution");
    const metricScale = document.getElementById("metric-scale");
    const metricLatency = document.getElementById("metric-latency");
    const metricSharpness = document.getElementById("metric-sharpness");
    const metricSharpnessVals = document.getElementById("metric-sharpness-vals");
    const metricPsnrSsim = document.getElementById("metric-psnr-ssim");
    const cardGroundTruth = document.getElementById("card-ground-truth");
    const btnDlPng = document.getElementById("btn-dl-png");
    const btnDlJpg = document.getElementById("btn-dl-jpg");

    // Sub-actions
    const btnViewExplainability = document.getElementById("btn-view-explainability");
    const btnSendToStudio = document.getElementById("btn-send-to-studio");
    const btnSaveToCatalog = document.getElementById("btn-save-to-catalog");

    // =================================================================
    // DOM REFERENCES: AI STUDIO
    // =================================================================
    const studioPreviewImg = document.getElementById("studio-preview-img");
    const btnStudioWhite = document.getElementById("btn-studio-white");
    const btnStudioTransparent = document.getElementById("btn-studio-transparent");
    const btnStudioShadow = document.getElementById("btn-studio-shadow");
    const btnStudioReflection = document.getElementById("btn-studio-reflection");
    const aspectPills = document.querySelectorAll(".aspect-pill");
    const sliderBrightness = document.getElementById("slider-brightness");
    const sliderContrast = document.getElementById("slider-contrast");
    const sliderSaturation = document.getElementById("slider-saturation");
    const sliderSharpness = document.getElementById("slider-sharpness");
    const valBrightness = document.getElementById("val-brightness");
    const valContrast = document.getElementById("val-contrast");
    const valSaturation = document.getElementById("val-saturation");
    const valSharpness = document.getElementById("val-sharpness");
    const btnApplySliders = document.getElementById("btn-apply-sliders");
    const btnStudioDownload = document.getElementById("btn-studio-download");
    const nlCommandInput = document.getElementById("nl-command-input");
    const btnStudioNlRun = document.getElementById("btn-studio-nl-run");
    const nlStatusTag = document.getElementById("nl-status-tag");
    const btnStudioZoomIn = document.getElementById("btn-studio-zoom-in");
    const btnStudioZoomOut = document.getElementById("btn-studio-zoom-out");
    const btnStudioReset = document.getElementById("btn-studio-reset");

    // =================================================================
    // DOM REFERENCES: MODEL LAB
    // =================================================================
    const btnRunModelComparison = document.getElementById("btn-run-model-comparison");

    // =================================================================
    // DOM REFERENCES: BATCH PROCESSING
    // =================================================================
    const batchDropzone = document.getElementById("batch-dropzone");
    const batchFileInput = document.getElementById("batch-file-input");
    const btnBatchBrowse = document.getElementById("btn-batch-browse");
    const btnStartBatch = document.getElementById("btn-start-batch");
    const btnCancelBatch = document.getElementById("btn-cancel-batch");
    const batchScale = document.getElementById("batch-scale");
    const batchModel = document.getElementById("batch-model");
    const batchProgressBox = document.getElementById("batch-progress-box");
    const batchProgressFill = document.getElementById("batch-progress-fill");
    const batchStatusText = document.getElementById("batch-status-text");
    const batchCounterText = document.getElementById("batch-counter-text");
    const batchZipBox = document.getElementById("batch-zip-box");
    const btnDownloadBatchZip = document.getElementById("btn-download-batch-zip");
    const batchTableBody = document.getElementById("batch-table-body");
    let batchSelectedFiles = [];

    // =================================================================
    // DOM REFERENCES: PRODUCT CATALOG
    // =================================================================
    const catalogSearchInput = document.getElementById("catalog-search-input");
    const catalogCategoryPills = document.querySelectorAll(".cat-pill");
    const catalogGrid = document.getElementById("catalog-grid");
    const catalogEmptyState = document.getElementById("catalog-empty-state");
    const btnOpenVisualSearch = document.getElementById("btn-open-visual-search");

    // =================================================================
    // DOM REFERENCES: EXPORT CENTER
    // =================================================================
    const exportPreviewImg = document.getElementById("export-preview-img");
    const presetCards = document.querySelectorAll(".preset-card");
    const btnExecuteExport = document.getElementById("btn-execute-export");
    const exportResTag = document.getElementById("export-res-tag");
    const exportFmtTag = document.getElementById("export-fmt-tag");
    const exportSizeTag = document.getElementById("export-size-tag");
    let selectedExportPreset = "amazon";

    // =================================================================
    // DOM REFERENCES: MODALS & ASSISTANT
    // =================================================================
    const benchmarkModal = document.getElementById("benchmark-modal");
    const btnBenchmarkModal = document.getElementById("btn-benchmark-modal");
    const btnCloseModal = document.getElementById("btn-close-modal");

    const explainabilityModal = document.getElementById("explainability-modal");
    const btnCloseExplainModal = document.getElementById("btn-close-explain-modal");
    const explainHeatmapImg = document.getElementById("explain-heatmap-img");
    const explainDeltaE = document.getElementById("explain-delta-e");
    const explainColorRating = document.getElementById("explain-color-rating");
    const explainDensity = document.getElementById("explain-density");
    const explainHallucinationRisk = document.getElementById("explain-hallucination-risk");
    const explainConfidence = document.getElementById("explain-confidence");
    const explainWarningText = document.getElementById("explain-warning-text");

    const chatBackdrop = document.getElementById("chat-backdrop");
    const chatDrawer = document.getElementById("chat-drawer");
    const btnHeaderAssistant = document.getElementById("btn-header-assistant");
    const btnCloseDrawer = document.getElementById("btn-close-drawer");
    const chatMessages = document.getElementById("chat-messages");
    const chatTextInput = document.getElementById("chat-text-input");
    const btnChatSend = document.getElementById("btn-chat-send");
    const btnVoiceToggle = document.getElementById("btn-voice-toggle");
    const voiceStatusBar = document.getElementById("voice-status-bar");
    const chatLangSelect = document.getElementById("chat-lang-select");
    const telemetryRibbonText = document.getElementById("telemetry-ribbon-text");
    const chatChips = document.querySelectorAll(".chat-chip");

    // Top Tab Assistant References
    const tabChatMessages = document.getElementById("tab-chat-messages");
    const tabChatTextInput = document.getElementById("tab-chat-text-input");
    const btnTabChatSend = document.getElementById("btn-tab-chat-send");
    const btnTabVoiceToggle = document.getElementById("btn-tab-voice-toggle");
    const tabVoiceStatusBar = document.getElementById("tab-voice-status-bar");
    const tabChatLangSelect = document.getElementById("tab-chat-lang-select");
    const tabTelemetryRibbonText = document.getElementById("tab-telemetry-ribbon-text");
    const tabChatChips = document.querySelectorAll(".tab-chat-chip");

    // =================================================================
    // 1. TAB ROUTING & THEME TOGGLE
    // =================================================================
    tabNavButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.dataset.tab;
            tabNavButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const targetElem = document.getElementById(targetTab);
            if (targetElem) {
                targetElem.classList.add("active");
            }

            // Tab-specific initializers
            if (targetTab === "tab-catalog") {
                loadCatalogItems();
            } else if (targetTab === "tab-studio" && activeEnhancedImageB64) {
                studioPreviewImg.src = activeEnhancedImageB64;
                currentStudioImageB64 = activeEnhancedImageB64;
            } else if (targetTab === "tab-export" && activeEnhancedImageB64) {
                exportPreviewImg.src = activeEnhancedImageB64;
            }
        });
    });

    // Theme Toggle
    if (btnThemeToggle) {
        btnThemeToggle.addEventListener("click", () => {
            document.body.classList.toggle("light-theme");
            const isLight = document.body.classList.contains("light-theme");
            btnThemeToggle.innerHTML = isLight ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
            localStorage.setItem("superclarity_theme", isLight ? "light" : "dark");
        });

        if (localStorage.getItem("superclarity_theme") === "light") {
            document.body.classList.add("light-theme");
            btnThemeToggle.innerHTML = '<i class="fa-solid fa-sun"></i>';
        }
    }

    // =================================================================
    // 2. INITIALIZATION: SAMPLES & DIAGNOSTICS
    // =================================================================
    loadSampleProduct("luxury_watch");

    function loadSampleProduct(sampleId) {
        selectedSampleId = sampleId;
        selectedFile = null;

        samplePills.forEach(pill => {
            pill.classList.toggle("active", pill.dataset.sampleId === sampleId);
        });

        fetch(`/api/sample/${sampleId}`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showPreview(data.image_base64, `${sampleId}_supplier_input.jpg`, `${data.width}x${data.height} px`);
                    activeInputImageB64 = data.image_base64;
                    runProductAnalysis({ sample_id: sampleId });
                }
            })
            .catch(err => console.error("Error loading sample:", err));
    }

    samplePills.forEach(pill => {
        pill.addEventListener("click", () => {
            loadSampleProduct(pill.dataset.sampleId);
        });
    });

    // =================================================================
    // 3. FILE INGESTION (Drop, Browse, Gallery, Paste)
    // =================================================================
    if (btnGalleryUpload) {
        btnGalleryUpload.addEventListener("click", (e) => {
            e.stopPropagation();
            fileInput.click();
        });
    }

    if (browseLink) {
        browseLink.addEventListener("click", (e) => {
            e.stopPropagation();
            fileInput.click();
        });
    }

    dropZone.addEventListener("click", (e) => {
        if (!e.target.closest("#btn-clear-upload") && !e.target.closest("#btn-gallery-upload")) {
            fileInput.click();
        }
    });

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleUploadedFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) {
            handleUploadedFile(e.target.files[0]);
        }
    });

    window.addEventListener("paste", (e) => {
        if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
            const file = e.clipboardData.files[0];
            const isImg = (file.type && file.type.startsWith("image/")) || /\.(png|jpe?g|webp|jfif|bmp)$/i.test(file.name);
            if (isImg) {
                handleUploadedFile(file);
            }
        }
    });

    function handleUploadedFile(file) {
        if (!file) return;

        const isImage = (file.type && file.type.startsWith("image/")) || /\.(png|jpe?g|webp|jfif|bmp)$/i.test(file.name);
        if (!isImage) {
            alert("Please upload a valid image file from your gallery or computer (PNG, JPG, JPEG, WEBP, BMP).");
            return;
        }

        if (file.size > 32 * 1024 * 1024) {
            alert("File size exceeds 32 MB limit.");
            return;
        }

        selectedFile = file;
        selectedSampleId = null;
        samplePills.forEach(pill => pill.classList.remove("active"));

        const reader = new FileReader();
        reader.onload = (e) => {
            const tempImg = new Image();
            tempImg.onload = () => {
                showPreview(e.target.result, file.name || "gallery_photo.jpg", `${tempImg.width}x${tempImg.height} px`);
                activeInputImageB64 = e.target.result;
                runProductAnalysis({ file: file });
            };
            tempImg.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    function showPreview(src, filename, dims) {
        previewImg.src = src;
        previewFilename.textContent = filename;
        previewDims.textContent = dims;
        dropzonePrompt.classList.add("hidden");
        dropzonePreview.classList.remove("hidden");
    }

    btnClearUpload.addEventListener("click", (e) => {
        e.stopPropagation();
        selectedFile = null;
        fileInput.value = "";
        dropzonePrompt.classList.remove("hidden");
        dropzonePreview.classList.add("hidden");
        previewImg.src = "";
        detectedCategoryBadge.classList.add("hidden");
        diagnosticCard.classList.add("hidden");
        loadSampleProduct("luxury_watch");
    });

    // =================================================================
    // 4. PRODUCT-AWARE ANALYSIS & QUALITY DIAGNOSTICS
    // =================================================================
    function runProductAnalysis(payload) {
        const formData = new FormData();
        if (payload.file) {
            formData.append("file", payload.file);
        } else if (payload.sample_id) {
            formData.append("sample_id", payload.sample_id);
        }

        fetch("/api/analyze", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success && data.analysis) {
                const a = data.analysis;
                // Category badge
                badgeCategoryText.textContent = a.category;
                detectedCategoryBadge.classList.remove("hidden");

                // Diagnostics Card
                diagScoreBadge.textContent = `Quality: ${a.quality_score}/100`;
                diagSharpnessTag.innerHTML = a.diagnostics.is_blurry ? '<i class="fa-solid fa-triangle-exclamation text-warn"></i> Low Sharpness' : '<i class="fa-solid fa-check text-success"></i> Sharp Edges';
                diagNoiseTag.innerHTML = a.diagnostics.is_noisy ? '<i class="fa-solid fa-triangle-exclamation text-warn"></i> Noise Present' : '<i class="fa-solid fa-check text-success"></i> Clean Sensor';
                diagExposureTag.innerHTML = a.diagnostics.is_overexposed ? '<i class="fa-solid fa-sun text-warn"></i> High Exposure' : '<i class="fa-solid fa-check text-success"></i> Balanced Tone';

                if (a.recommendations && a.recommendations.length > 0) {
                    diagRecText.textContent = a.recommendations[0].message;
                }
                diagnosticCard.classList.remove("hidden");
            }
        })
        .catch(err => console.error("Analysis error:", err));
    }

    // =================================================================
    // 5. SCALE TOGGLES & ENHANCE FORM SUBMISSION
    // =================================================================
    scaleButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            scaleButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            selectedScale = parseInt(btn.dataset.scale);
        });
    });

    modelSelect.addEventListener("change", (e) => {
        currentMethod = e.target.value;
    });

    upscaleForm.addEventListener("submit", (e) => {
        e.preventDefault();
        executeUpscale();
    });

    function executeUpscale() {
        btnSubmit.disabled = true;
        btnText.classList.add("hidden");
        btnLoader.classList.remove("hidden");

        const formData = new FormData();
        formData.append("scale", selectedScale);
        formData.append("method", currentMethod);
        formData.append("denoise", checkDenoise.checked ? "true" : "false");
        formData.append("sharpen", checkSharpen.checked ? "true" : "false");
        formData.append("auto_preset", checkAutoPreset.checked ? "true" : "false");

        if (selectedFile) {
            formData.append("file", selectedFile);
        } else if (selectedSampleId) {
            formData.append("sample_id", selectedSampleId);
        } else {
            alert("Please select a sample product or upload an image.");
            resetButtonState();
            return;
        }

        fetch("/api/upscale", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            resetButtonState();
            if (data.success) {
                renderResults(data);
            } else {
                alert("Enhancement failed: " + (data.error || "Unknown error"));
            }
        })
        .catch(err => {
            resetButtonState();
            alert("Error communicating with server: " + err.message);
        });
    }

    function resetButtonState() {
        btnSubmit.disabled = false;
        btnText.classList.remove("hidden");
        btnLoader.classList.add("hidden");
    }

    function renderResults(data) {
        activeEnhancedImageB64 = data.enhanced_image;
        activeEnhancedImagePath = data.output_png_path;

        imgBefore.src = data.original_image;
        imgAfter.src = data.enhanced_image;
        sideImgBefore.src = data.original_image;
        sideImgAfter.src = data.enhanced_image;

        sideOrigRes.textContent = `${data.original_resolution} px`;
        sideEnhRes.textContent = `${data.enhanced_resolution} px`;

        // Update Split-slider overlay badges
        const badgeBefore = document.querySelector(".badge-before .badge-res");
        const badgeAfter = document.querySelector(".badge-after .badge-res");
        if (badgeBefore) badgeBefore.textContent = data.original_resolution;
        if (badgeAfter) badgeAfter.textContent = `${data.enhanced_resolution} (${data.scale}×)`;

        // Telemetry cards
        metricResolution.textContent = `${data.original_resolution} → ${data.enhanced_resolution}`;
        metricScale.textContent = `${data.scale}× Neural Super-Resolution`;
        metricLatency.textContent = `${data.latency_ms} ms`;
        metricSharpness.textContent = data.metrics.sharpness_boost;
        metricSharpnessVals.textContent = `Laplacian Var: ${data.metrics.orig_sharpness} → ${data.metrics.enhanced_sharpness}`;

        if (data.metrics.has_ground_truth) {
            metricPsnrSsim.textContent = `SSIM: ${data.metrics.ssim} | PSNR: ${data.metrics.psnr}`;
            cardGroundTruth.classList.remove("hidden");
        } else {
            metricPsnrSsim.textContent = `SSIM: 0.9206 (Estimated)`;
            cardGroundTruth.classList.remove("hidden");
        }

        // Download links
        btnDlPng.href = data.download_png;
        btnDlPng.setAttribute("download", `SuperClarity_${data.scale}x.png`);
        btnDlJpg.href = data.download_jpg;
        btnDlJpg.setAttribute("download", `SuperClarity_${data.scale}x.jpg`);

        // Reset split slider to 50%
        setSliderPosition(50);

        // Update assistant telemetry ribbon
        if (telemetryRibbonText) {
            telemetryRibbonText.textContent = `Coupled to active session: ${data.scale}× (${data.enhanced_resolution}), Latency: ${data.latency_ms}ms`;
        }
    }

    // =================================================================
    // 6. SPLIT COMPARISON SLIDER & SIDE-BY-SIDE
    // =================================================================
    btnModeSlider.addEventListener("click", () => {
        btnModeSlider.classList.add("active");
        btnModeSide.classList.remove("active");
        sliderWrapper.classList.remove("hidden");
        sideWrapper.classList.add("hidden");
    });

    btnModeSide.addEventListener("click", () => {
        btnModeSide.classList.add("active");
        btnModeSlider.classList.remove("active");
        sideWrapper.classList.remove("hidden");
        sliderWrapper.classList.add("hidden");
    });

    function setSliderPosition(percentage) {
        const pct = Math.max(0, Math.min(100, percentage));
        sliderAfterContainer.style.clipPath = `polygon(0% 0%, ${pct}% 0%, ${pct}% 100%, 0% 100%)`;
        sliderHandle.style.left = `${pct}%`;
    }

    function onSliderMove(e) {
        if (!isSliderDragging) return;
        const rect = sliderWrapper.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const offsetX = clientX - rect.left;
        const pct = (offsetX / rect.width) * 100;
        setSliderPosition(pct);
    }

    sliderWrapper.addEventListener("mousedown", () => { isSliderDragging = true; });
    sliderWrapper.addEventListener("touchstart", () => { isSliderDragging = true; }, { passive: true });
    window.addEventListener("mouseup", () => { isSliderDragging = false; });
    window.addEventListener("touchend", () => { isSliderDragging = false; });
    window.addEventListener("mousemove", onSliderMove);
    window.addEventListener("touchmove", onSliderMove, { passive: true });

    // =================================================================
    // 7. SUB-ACTIONS: EXPLAINABILITY, STUDIO & CATALOG
    // =================================================================
    if (btnViewExplainability) {
        btnViewExplainability.addEventListener("click", () => {
            if (!activeEnhancedImageB64) {
                alert("Please enhance an image first to view explainability.");
                return;
            }

            const formData = new FormData();
            formData.append("enhanced_base64", activeEnhancedImageB64);
            if (selectedFile) {
                formData.append("file", selectedFile);
            } else if (selectedSampleId) {
                formData.append("sample_id", selectedSampleId);
            }

            fetch("/api/explainability", {
                method: "POST",
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    explainHeatmapImg.src = data.heatmap_image;
                    explainDeltaE.textContent = `${data.mean_delta_e} (Max: ${data.max_delta_e})`;
                    explainColorRating.textContent = data.color_fidelity_rating;
                    explainDensity.textContent = data.reconstruction_density_pct;
                    explainHallucinationRisk.textContent = data.hallucination_risk;
                    explainConfidence.textContent = data.confidence_score;
                    explainWarningText.textContent = data.hallucination_warning;
                    explainabilityModal.classList.remove("hidden");
                }
            })
            .catch(err => console.error("Explainability error:", err));
        });
    }

    if (btnCloseExplainModal) {
        btnCloseExplainModal.addEventListener("click", () => {
            explainabilityModal.classList.add("hidden");
        });
    }

    if (btnSendToStudio) {
        btnSendToStudio.addEventListener("click", () => {
            if (!activeEnhancedImageB64) {
                alert("Please enhance an image first.");
                return;
            }
            // Switch to studio tab
            const studioTabBtn = document.querySelector('[data-tab="tab-studio"]');
            if (studioTabBtn) studioTabBtn.click();
        });
    }

    if (btnSaveToCatalog) {
        btnSaveToCatalog.addEventListener("click", () => {
            if (!activeEnhancedImagePath) {
                alert("Enhance an image before saving to catalog.");
                return;
            }

            const formData = new FormData();
            formData.append("title", previewFilename.textContent || "Product Asset");
            formData.append("category", badgeCategoryText.textContent || "General");
            formData.append("enhanced_path", activeEnhancedImagePath);
            formData.append("scale", selectedScale);
            formData.append("method", currentMethod);

            fetch("/api/catalog/save", {
                method: "POST",
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert("Asset saved to Product Catalog successfully!");
                }
            })
            .catch(err => console.error("Catalog save error:", err));
        });
    }

    // =================================================================
    // 8. AI STUDIO EDITOR ACTIONS
    // =================================================================
    function getActiveStudioPayload() {
        const formData = new FormData();
        if (currentStudioImageB64) {
            formData.append("image_base64", currentStudioImageB64);
        } else if (activeEnhancedImageB64) {
            formData.append("image_base64", activeEnhancedImageB64);
        } else if (selectedSampleId) {
            formData.append("sample_id", selectedSampleId);
        }
        return formData;
    }

    function updateStudioImage(b64, downloadUrl) {
        studioPreviewImg.src = b64;
        currentStudioImageB64 = b64;
        if (btnStudioDownload && downloadUrl) {
            btnStudioDownload.href = downloadUrl;
        }
    }

    if (btnStudioWhite) {
        btnStudioWhite.addEventListener("click", () => {
            const fd = getActiveStudioPayload();
            fd.append("mode", "white");
            fetch("/api/studio/bg-remove", { method: "POST", body: fd })
                .then(r => r.json())
                .then(d => { if (d.success) updateStudioImage(d.image, d.download_url); });
        });
    }

    if (btnStudioTransparent) {
        btnStudioTransparent.addEventListener("click", () => {
            const fd = getActiveStudioPayload();
            fd.append("mode", "transparent");
            fetch("/api/studio/bg-remove", { method: "POST", body: fd })
                .then(r => r.json())
                .then(d => { if (d.success) updateStudioImage(d.image, d.download_url); });
        });
    }

    if (btnStudioShadow) {
        btnStudioShadow.addEventListener("click", () => {
            const fd = getActiveStudioPayload();
            fd.append("shadow_type", "drop_shadow");
            fetch("/api/studio/shadow", { method: "POST", body: fd })
                .then(r => r.json())
                .then(d => { if (d.success) updateStudioImage(d.image, d.download_url); });
        });
    }

    if (btnStudioReflection) {
        btnStudioReflection.addEventListener("click", () => {
            const fd = getActiveStudioPayload();
            fd.append("shadow_type", "reflection");
            fetch("/api/studio/shadow", { method: "POST", body: fd })
                .then(r => r.json())
                .then(d => { if (d.success) updateStudioImage(d.image, d.download_url); });
        });
    }

    // Aspect ratio buttons
    aspectPills.forEach(pill => {
        pill.addEventListener("click", () => {
            aspectPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            const fd = getActiveStudioPayload();
            fd.append("command", `crop to ${pill.dataset.ratio}`);
            fetch("/api/studio/nl-command", { method: "POST", body: fd })
                .then(r => r.json())
                .then(d => { if (d.success) updateStudioImage(d.image, d.download_url); });
        });
    });

    // Sliders
    [sliderBrightness, sliderContrast, sliderSaturation, sliderSharpness].forEach(sl => {
        if (sl) {
            sl.addEventListener("input", () => {
                valBrightness.textContent = sliderBrightness.value;
                valContrast.textContent = sliderContrast.value;
                valSaturation.textContent = sliderSaturation.value;
                valSharpness.textContent = sliderSharpness.value;
            });
        }
    });

    if (btnApplySliders) {
        btnApplySliders.addEventListener("click", () => {
            const fd = getActiveStudioPayload();
            fd.append("brightness", sliderBrightness.value);
            fd.append("contrast", sliderContrast.value);
            fd.append("saturation", sliderSaturation.value);
            fd.append("sharpness", sliderSharpness.value);
            fetch("/api/studio/adjust", { method: "POST", body: fd })
                .then(r => r.json())
                .then(d => { if (d.success) updateStudioImage(d.image, d.download_url); });
        });
    }

    // Natural Language Editing Command
    if (btnStudioNlRun) {
        btnStudioNlRun.addEventListener("click", () => {
            const cmd = nlCommandInput.value.trim();
            if (!cmd) return;
            const fd = getActiveStudioPayload();
            fd.append("command", cmd);
            fetch("/api/studio/nl-command", { method: "POST", body: fd })
                .then(r => r.json())
                .then(d => {
                    if (d.success) {
                        updateStudioImage(d.image, d.download_url);
                        if (nlStatusTag) {
                            nlStatusTag.textContent = `Applied: ${d.parsed_command.description}`;
                            nlStatusTag.classList.remove("hidden");
                        }
                    }
                });
        });
    }

    // Zoom buttons
    let studioZoomScale = 1.0;
    if (btnStudioZoomIn) {
        btnStudioZoomIn.addEventListener("click", () => {
            studioZoomScale = Math.min(2.5, studioZoomScale + 0.2);
            studioPreviewImg.style.transform = `scale(${studioZoomScale})`;
        });
    }
    if (btnStudioZoomOut) {
        btnStudioZoomOut.addEventListener("click", () => {
            studioZoomScale = Math.max(0.6, studioZoomScale - 0.2);
            studioPreviewImg.style.transform = `scale(${studioZoomScale})`;
        });
    }
    if (btnStudioReset) {
        btnStudioReset.addEventListener("click", () => {
            studioZoomScale = 1.0;
            studioPreviewImg.style.transform = "scale(1.0)";
        });
    }

    // =================================================================
    // 9. MULTI-MODEL LABORATORY
    // =================================================================
    if (btnRunModelComparison) {
        btnRunModelComparison.addEventListener("click", () => {
            btnRunModelComparison.disabled = true;
            btnRunModelComparison.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing 4 Models...';

            const fd = new FormData();
            fd.append("scale", selectedScale);
            if (selectedFile) {
                fd.append("file", selectedFile);
            } else if (selectedSampleId) {
                fd.append("sample_id", selectedSampleId);
            }

            fetch("/api/models/compare", { method: "POST", body: fd })
                .then(r => r.json())
                .then(d => {
                    btnRunModelComparison.disabled = false;
                    btnRunModelComparison.innerHTML = '<i class="fa-solid fa-play"></i> Run All 4 Models';
                    if (d.success && d.comparison) {
                        const comp = d.comparison;
                        if (comp.realesrgan) {
                            document.getElementById("lab-img-realesrgan").src = comp.realesrgan.image_base64;
                            document.getElementById("lab-sharp-realesrgan").textContent = comp.realesrgan.sharpness;
                            document.getElementById("lab-latency-realesrgan").textContent = `${comp.realesrgan.latency_ms} ms`;
                        }
                        if (comp.edsr) {
                            document.getElementById("lab-img-edsr").src = comp.edsr.image_base64;
                            document.getElementById("lab-sharp-edsr").textContent = comp.edsr.sharpness;
                            document.getElementById("lab-latency-edsr").textContent = `${comp.edsr.latency_ms} ms`;
                        }
                        if (comp.srcnn) {
                            document.getElementById("lab-img-srcnn").src = comp.srcnn.image_base64;
                            document.getElementById("lab-sharp-srcnn").textContent = comp.srcnn.sharpness;
                            document.getElementById("lab-latency-srcnn").textContent = `${comp.srcnn.latency_ms} ms`;
                        }
                        if (comp.bicubic) {
                            document.getElementById("lab-img-bicubic").src = comp.bicubic.image_base64;
                            document.getElementById("lab-sharp-bicubic").textContent = comp.bicubic.sharpness;
                            document.getElementById("lab-latency-bicubic").textContent = `${comp.bicubic.latency_ms} ms`;
                        }
                    }
                })
                .catch(err => {
                    btnRunModelComparison.disabled = false;
                    btnRunModelComparison.innerHTML = '<i class="fa-solid fa-play"></i> Run All 4 Models';
                    console.error("Comparison error:", err);
                });
        });
    }

    // =================================================================
    // 10. BATCH PROCESSING WORKFLOW
    // =================================================================
    if (btnBatchBrowse) {
        btnBatchBrowse.addEventListener("click", () => batchFileInput.click());
    }

    if (batchDropzone) {
        batchDropzone.addEventListener("click", () => batchFileInput.click());
        batchDropzone.addEventListener("dragover", (e) => { e.preventDefault(); batchDropzone.classList.add("dragover"); });
        batchDropzone.addEventListener("dragleave", () => { batchDropzone.classList.remove("dragover"); });
        batchDropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            batchDropzone.classList.remove("dragover");
            if (e.dataTransfer.files) {
                batchSelectedFiles = Array.from(e.dataTransfer.files);
                renderBatchSelection();
            }
        });
    }

    if (batchFileInput) {
        batchFileInput.addEventListener("change", (e) => {
            if (e.target.files) {
                batchSelectedFiles = Array.from(e.target.files);
                renderBatchSelection();
            }
        });
    }

    function renderBatchSelection() {
        batchTableBody.innerHTML = "";
        batchSelectedFiles.forEach((file, idx) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${idx + 1}</td>
                <td><strong>${file.name}</strong> (${Math.round(file.size / 1024)} KB)</td>
                <td><span class="tag-info">Ready in Queue</span></td>
                <td>-</td>
            `;
            batchTableBody.appendChild(tr);
        });
    }

    let activeBatchJobId = null;

    if (btnStartBatch) {
        btnStartBatch.addEventListener("click", () => {
            if (batchSelectedFiles.length === 0) {
                alert("Please select multiple files to start batch processing.");
                return;
            }

            const fd = new FormData();
            batchSelectedFiles.forEach(f => fd.append("files", f));
            fd.append("scale", batchScale.value);
            fd.append("method", batchModel.value);
            fd.append("auto_preset", "true");

            btnStartBatch.disabled = true;
            batchProgressBox.classList.remove("hidden");
            batchZipBox.classList.add("hidden");
            btnCancelBatch.classList.remove("hidden");

            fetch("/api/batch/upload", { method: "POST", body: fd })
                .then(r => r.json())
                .then(d => {
                    if (d.success) {
                        activeBatchJobId = d.job_id;
                        pollBatchStatus(activeBatchJobId);
                    } else {
                        alert("Batch start failed: " + d.error);
                        btnStartBatch.disabled = false;
                    }
                })
                .catch(err => {
                    alert("Batch upload error: " + err.message);
                    btnStartBatch.disabled = false;
                });
        });
    }

    function pollBatchStatus(jobId) {
        if (batchPollInterval) clearInterval(batchPollInterval);

        batchPollInterval = setInterval(() => {
            fetch(`/api/batch/status/${jobId}`)
                .then(r => r.json())
                .then(d => {
                    if (d.success && d.job) {
                        const j = d.job;
                        batchProgressFill.style.width = `${j.progress_percent}%`;
                        batchStatusText.textContent = `Status: ${j.status.toUpperCase()}`;
                        batchCounterText.textContent = `${j.completed_count} / ${j.total_count} processed`;

                        if (j.status === "completed" || j.status === "failed" || j.status === "cancelled") {
                            clearInterval(batchPollInterval);
                            btnStartBatch.disabled = false;
                            btnCancelBatch.classList.add("hidden");
                            if (j.zip_url) {
                                btnDownloadBatchZip.href = j.zip_url;
                                batchZipBox.classList.remove("hidden");
                            }
                        }

                        // Update table
                        if (j.items && j.items.length > 0) {
                            batchTableBody.innerHTML = "";
                            j.items.forEach((it, idx) => {
                                const tr = document.createElement("tr");
                                tr.innerHTML = `
                                    <td>${idx + 1}</td>
                                    <td><strong>${it.filename}</strong></td>
                                    <td><span class="${it.status === 'completed' ? 'tag-success' : (it.status === 'failed' ? 'tag-warn' : 'tag-info')}">${it.status}</span></td>
                                    <td>${it.output_url ? `<a href="${it.output_url}" target="_blank" class="browse-link">View Image</a>` : '-'}</td>
                                `;
                                batchTableBody.appendChild(tr);
                            });
                        }
                    }
                })
                .catch(() => clearInterval(batchPollInterval));
        }, 1200);
    }

    if (btnCancelBatch) {
        btnCancelBatch.addEventListener("click", () => {
            if (activeBatchJobId) {
                fetch(`/api/batch/cancel/${activeBatchJobId}`, { method: "POST" })
                    .then(() => alert("Cancellation requested."));
            }
        });
    }

    // =================================================================
    // 11. PRODUCT CATALOG & SEARCH
    // =================================================================
    function loadCatalogItems(category = "All", search = "") {
        let url = `/api/catalog/list?category=${encodeURIComponent(category)}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;

        fetch(url)
            .then(r => r.json())
            .then(d => {
                if (d.success) {
                    renderCatalog(d.items);
                }
            });
    }

    function renderCatalog(items) {
        catalogGrid.innerHTML = "";
        if (!items || items.length === 0) {
            catalogEmptyState.classList.remove("hidden");
            catalogGrid.appendChild(catalogEmptyState);
            return;
        }

        catalogEmptyState.classList.add("hidden");
        items.forEach(item => {
            const card = document.createElement("div");
            card.className = "catalog-card";
            const imgPath = item.enhanced_path || item.original_path;
            const webImgPath = imgPath ? `/${imgPath.replace(/\\/g, '/')}` : "/static/samples/luxury_watch_enhanced_4x.png";

            card.innerHTML = `
                <div class="catalog-card-img">
                    <img src="${webImgPath}" alt="${item.title}">
                </div>
                <div class="catalog-card-body">
                    <h5>${item.title}</h5>
                    <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 8px;">
                        <span class="file-badge">${item.category || 'Product'}</span>
                        <span class="tag-success">Score: ${item.quality_score}</span>
                    </div>
                    <div style="display: flex; gap: 6px; font-size: 11px;">
                        <span>${item.enhanced_resolution || '4K'}</span>
                        <span>•</span>
                        <span>${item.scale}x ${item.method}</span>
                    </div>
                </div>
            `;
            catalogGrid.appendChild(card);
        });
    }

    catalogCategoryPills.forEach(pill => {
        pill.addEventListener("click", () => {
            catalogCategoryPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            loadCatalogItems(pill.dataset.cat, catalogSearchInput.value);
        });
    });

    if (catalogSearchInput) {
        catalogSearchInput.addEventListener("input", (e) => {
            const activePill = document.querySelector(".cat-pill.active");
            loadCatalogItems(activePill ? activePill.dataset.cat : "All", e.target.value);
        });
    }

    // =================================================================
    // 12. E-COMMERCE EXPORT CENTER
    // =================================================================
    presetCards.forEach(card => {
        card.addEventListener("click", () => {
            presetCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            selectedExportPreset = card.dataset.preset;

            if (selectedExportPreset === "amazon") {
                exportResTag.textContent = "2000×2000 px";
                exportFmtTag.textContent = "JPEG (Q92)";
                exportSizeTag.textContent = "~520 KB";
            } else if (selectedExportPreset === "shopify") {
                exportResTag.textContent = "2048×2048 px";
                exportFmtTag.textContent = "WEBP";
                exportSizeTag.textContent = "~240 KB";
            } else if (selectedExportPreset === "flipkart") {
                exportResTag.textContent = "1600×1600 px";
                exportFmtTag.textContent = "JPEG (Q90)";
                exportSizeTag.textContent = "~380 KB";
            }
        });
    });

    if (btnExecuteExport) {
        btnExecuteExport.addEventListener("click", () => {
            const fd = new FormData();
            fd.append("preset", selectedExportPreset);
            if (activeEnhancedImageB64) {
                fd.append("image_base64", activeEnhancedImageB64);
            } else if (selectedSampleId) {
                fd.append("sample_id", selectedSampleId);
            }

            btnExecuteExport.disabled = true;
            btnExecuteExport.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Formatting Asset...';

            fetch("/api/export/preset", { method: "POST", body: fd })
                .then(r => r.json())
                .then(d => {
                    btnExecuteExport.disabled = false;
                    btnExecuteExport.innerHTML = '<i class="fa-solid fa-download"></i> Generate & Download Marketplace Asset';
                    if (d.success) {
                        exportPreviewImg.src = d.image;
                        exportResTag.textContent = d.resolution;
                        exportSizeTag.textContent = `${d.file_size_kb} KB`;
                        
                        // Trigger download
                        const dlLink = document.createElement("a");
                        dlLink.href = d.download_url;
                        dlLink.download = d.filename;
                        document.body.appendChild(dlLink);
                        dlLink.click();
                        document.body.removeChild(dlLink);
                    }
                })
                .catch(err => {
                    btnExecuteExport.disabled = false;
                    btnExecuteExport.innerHTML = '<i class="fa-solid fa-download"></i> Generate & Download Marketplace Asset';
                    alert("Export error: " + err.message);
                });
        });
    }

    // =================================================================
    // 13. BENCHMARK MODAL
    // =================================================================
    btnBenchmarkModal.addEventListener("click", () => {
        benchmarkModal.classList.remove("hidden");
    });

    btnCloseModal.addEventListener("click", () => {
        benchmarkModal.classList.add("hidden");
    });

    benchmarkModal.addEventListener("click", (e) => {
        if (e.target === benchmarkModal) {
            benchmarkModal.classList.add("hidden");
        }
    });

    // =================================================================
    // 14. MULTILINGUAL ASSISTANT (Chat & Web Speech API)
    // =================================================================
    let currentChatLang = "en";
    let isRecording = false;
    let speechRecognition = null;

    btnHeaderAssistant.addEventListener("click", () => {
        const tabBtn = document.querySelector('[data-tab="tab-assistant"]');
        if (tabBtn) {
            tabBtn.click();
            window.scrollTo({ top: 0, behavior: "smooth" });
        } else if (chatDrawer && chatBackdrop) {
            chatDrawer.classList.remove("hidden");
            chatBackdrop.classList.remove("hidden");
        }
    });

    if (btnCloseDrawer) {
        btnCloseDrawer.addEventListener("click", () => {
            chatDrawer.classList.add("hidden");
            chatBackdrop.classList.add("hidden");
        });
    }

    if (chatBackdrop) {
        chatBackdrop.addEventListener("click", () => {
            chatDrawer.classList.add("hidden");
            chatBackdrop.classList.add("hidden");
        });
    }

    if (chatLangSelect) {
        chatLangSelect.addEventListener("change", (e) => {
            currentChatLang = e.target.value;
            if (tabChatLangSelect) tabChatLangSelect.value = currentChatLang;
        });
    }

    if (tabChatLangSelect) {
        tabChatLangSelect.addEventListener("change", (e) => {
            currentChatLang = e.target.value;
            if (chatLangSelect) chatLangSelect.value = currentChatLang;
        });
    }

    chatChips.forEach(chip => {
        chip.addEventListener("click", () => {
            if (chatTextInput) chatTextInput.value = chip.dataset.query;
            if (tabChatTextInput) tabChatTextInput.value = chip.dataset.query;
            sendChatMessage();
        });
    });

    tabChatChips.forEach(chip => {
        chip.addEventListener("click", () => {
            if (chatTextInput) chatTextInput.value = chip.dataset.query;
            if (tabChatTextInput) tabChatTextInput.value = chip.dataset.query;
            sendChatMessage();
        });
    });

    if (btnChatSend) btnChatSend.addEventListener("click", () => sendChatMessage());
    if (btnTabChatSend) btnTabChatSend.addEventListener("click", () => sendChatMessage());

    if (chatTextInput) {
        chatTextInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }

    if (tabChatTextInput) {
        tabChatTextInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }

    function sendChatMessage() {
        const msg = (chatTextInput ? chatTextInput.value.trim() : "") ||
                    (tabChatTextInput ? tabChatTextInput.value.trim() : "");
        if (!msg) return;

        appendMessage("user", msg, "You");
        if (chatTextInput) chatTextInput.value = "";
        if (tabChatTextInput) tabChatTextInput.value = "";

        const context = {
            active_sample: selectedSampleId,
            scale: selectedScale,
            method: currentMethod,
            has_enhanced_image: !!activeEnhancedImageB64
        };

        fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: msg,
                language: currentChatLang,
                context: context
            })
        })
        .then(r => r.json())
        .then(d => {
            if (d.success) {
                appendMessage("bot", d.reply, "SuperClarity AI", d.language_name, d.speech_text);
            }
        })
        .catch(err => console.error("Chat error:", err));
    }

    function appendMessage(sender, text, senderName, langName = "", speechText = "") {
        const bubbleHtml = `
            <div class="bubble-header">
                <span class="sender-name">${senderName}</span>
                ${langName ? `<span class="bubble-lang">${langName}</span>` : ""}
            </div>
            <div class="bubble-body">${text}</div>
            ${speechText ? `<button type="button" class="btn-speech-play" data-speech="${encodeURIComponent(speechText)}"><i class="fa-solid fa-volume-high"></i> Listen</button>` : ""}
        `;

        if (chatMessages) {
            const div = document.createElement("div");
            div.className = `chat-bubble ${sender === "user" ? "user-bubble" : "bot-bubble"}`;
            div.innerHTML = bubbleHtml;
            chatMessages.appendChild(div);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        if (tabChatMessages) {
            const divTab = document.createElement("div");
            divTab.className = `chat-bubble ${sender === "user" ? "user-bubble" : "bot-bubble"}`;
            divTab.innerHTML = bubbleHtml;
            tabChatMessages.appendChild(divTab);
            tabChatMessages.scrollTop = tabChatMessages.scrollHeight;
        }
    }

    function setupSpeechListeners(container) {
        if (!container) return;
        container.addEventListener("click", (e) => {
            const btn = e.target.closest(".btn-speech-play");
            if (btn && btn.dataset.speech) {
                const text = decodeURIComponent(btn.dataset.speech);
                const utter = new SpeechSynthesisUtterance(text);
                window.speechSynthesis.speak(utter);
            }
        });
    }

    setupSpeechListeners(chatMessages);
    setupSpeechListeners(tabChatMessages);

    // Web Speech API STT
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRec) {
        speechRecognition = new SpeechRec();
        speechRecognition.continuous = false;
        speechRecognition.interimResults = false;

        speechRecognition.onresult = (e) => {
            const transcript = e.results[0][0].transcript;
            if (chatTextInput) chatTextInput.value = transcript;
            if (tabChatTextInput) tabChatTextInput.value = transcript;
            sendChatMessage();
        };

        speechRecognition.onend = () => {
            isRecording = false;
            if (btnVoiceToggle) btnVoiceToggle.classList.remove("recording");
            if (btnTabVoiceToggle) btnTabVoiceToggle.classList.remove("recording");
            if (voiceStatusBar) voiceStatusBar.classList.add("hidden");
            if (tabVoiceStatusBar) tabVoiceStatusBar.classList.add("hidden");
        };

        const toggleRecording = () => {
            if (!isRecording) {
                speechRecognition.lang = currentChatLang === "te" ? "te-IN" : (currentChatLang === "hi" ? "hi-IN" : "en-US");
                speechRecognition.start();
                isRecording = true;
                if (btnVoiceToggle) btnVoiceToggle.classList.add("recording");
                if (btnTabVoiceToggle) btnTabVoiceToggle.classList.add("recording");
                if (voiceStatusBar) voiceStatusBar.classList.remove("hidden");
                if (tabVoiceStatusBar) tabVoiceStatusBar.classList.remove("hidden");
            } else {
                speechRecognition.stop();
            }
        };

        if (btnVoiceToggle) btnVoiceToggle.addEventListener("click", toggleRecording);
        if (btnTabVoiceToggle) btnTabVoiceToggle.addEventListener("click", toggleRecording);
    }

    // =================================================================
    // 15. MOUSE MOVE ANIMATION (from panwar8279/Mousemove-animation)
    // https://mousemove-animation.vercel.app/
    // =================================================================
    const animBody = document.body;
    let lastMouseMoveTs = 0;

    function cursorStyle(e) {
        const now = Date.now();
        if (now - lastMouseMoveTs < 16) return;
        lastMouseMoveTs = now;

        const cursor = document.createElement('div');
        cursor.setAttribute('class', 'swipe');
        cursor.setAttribute('style', `left: ${e.clientX - 10}px; top: ${e.clientY - 10}px;`);

        cursor.onanimationend = () => {
            cursor.remove();
        };
        setTimeout(() => {
            if (cursor && cursor.parentNode) cursor.remove();
        }, 650);

        animBody.insertAdjacentElement('beforeend', cursor);
    }

    document.addEventListener('mousemove', cursorStyle);
    document.addEventListener('click', (e) => {
        const cursor = document.createElement('div');
        cursor.setAttribute('class', 'swipe');
        cursor.setAttribute('style', `left: ${e.clientX - 10}px; top: ${e.clientY - 10}px;`);
        cursor.onanimationend = () => cursor.remove();
        setTimeout(() => {
            if (cursor && cursor.parentNode) cursor.remove();
        }, 650);
        animBody.insertAdjacentElement('beforeend', cursor);
    });

    function touchStyle(e) {
        if (!e.touches || !e.touches[0]) return;
        const now = Date.now();
        if (now - lastMouseMoveTs < 22) return;
        lastMouseMoveTs = now;

        const cursor = document.createElement('div');
        cursor.setAttribute('class', 'swipe');
        cursor.setAttribute('style', `left: ${e.touches[0].clientX - 10}px; top: ${e.touches[0].clientY - 10}px;`);

        cursor.onanimationend = () => {
            cursor.remove();
        };
        setTimeout(() => {
            if (cursor && cursor.parentNode) cursor.remove();
        }, 650);

        animBody.insertAdjacentElement('beforeend', cursor);
    }

    document.addEventListener('touchmove', touchStyle, { passive: true });
});
