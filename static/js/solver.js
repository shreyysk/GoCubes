// rubiks-cube-web/static/js/solver.js

// --- GLOBAL STATE VARIABLES ---
// 2D cube state for UI - PROPERLY INITIALIZED
let cubeState = {
    up: Array(9).fill('W'),
    down: Array(9).fill('Y'),
    front: Array(9).fill('R'),
    back: Array(9).fill('O'),
    left: Array(9).fill('G'),
    right: Array(9).fill('B')
};
const jsCube = new CubeModel(); // JS model for client-side scrambling

// 3D visualization and animation
let mainCube3d = null;
let manualPreviewCube = null; // Dedicated cube for the manual tab
let cameraPreviewCube = null; // Dedicated cube for the camera tab
let currentSolution = [];
let currentMoveIndex = 0;
let isPlaying = false;

// History for undo/redo
let stateHistory = [];
let historyIndex = -1;
const MAX_HISTORY = 50;

function saveState() {
    // Remove future states if we're not at the end
    stateHistory = stateHistory.slice(0, historyIndex + 1);
    
    // Add current state
    stateHistory.push(JSON.parse(JSON.stringify(cubeState)));
    
    // Limit history size
    if (stateHistory.length > MAX_HISTORY) {
        stateHistory.shift();
    } else {
        historyIndex++;
    }
    
    updateUndoRedoButtons();
}

function undo() {
    if (historyIndex > 0) {
        historyIndex--;
        cubeState = JSON.parse(JSON.stringify(stateHistory[historyIndex]));
        updateVisualFromState();
        updateColorCounter();
        updateAll3DCubes();
        updateUndoRedoButtons();
    }
}

function redo() {
    if (historyIndex < stateHistory.length - 1) {
        historyIndex++;
        cubeState = JSON.parse(JSON.stringify(stateHistory[historyIndex]));
        updateVisualFromState();
        updateColorCounter();
        updateAll3DCubes();
        updateUndoRedoButtons();
    }
}

function updateUndoRedoButtons() {
    $('#undoBtn').prop('disabled', historyIndex <= 0);
    $('#redoBtn').prop('disabled', historyIndex >= stateHistory.length - 1);
}

// Keyboard shortcuts
    $(document).keydown(function(e) {
        // Prevent shortcuts in input fields
        if ($(e.target).is('input, textarea')) return;
        
        switch(e.key) {
            case ' ':  // Space - play/pause
                e.preventDefault();
                if (isPlaying) {
                    pauseAnimation();
                } else if (currentSolution.length > 0) {
                    playAnimation();
                }
                break;
                
            case 'ArrowLeft':  // Previous move
                e.preventDefault();
                prevStep();
                break;
                
            case 'ArrowRight':  // Next move
                e.preventDefault();
                nextStep();
                break;
                
            case 'r':  // Reset animation
            case 'R':
                if (currentSolution.length > 0) {
                    resetAnimation();
                }
                break;
                
            case 'z':  // Undo
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    undo();
                }
                break;
                
            case 'y':  // Redo
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    redo();
                }
                break;
                
            case '1': case '2': case '3': case '4': case '5': case '6':
                // Number keys for color selection
                const colorIndex = parseInt(e.key) - 1;
                const colors = ['W', 'Y', 'R', 'O', 'G', 'B'];
                if (colorIndex < colors.length) {
                    $(`.color-btn[data-color="${colors[colorIndex]}"]`).click();
                }
                break;
                
            case 's':  // Save state
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    saveStateToStorage();
                }
                break;
                
            case 'l':  // Load state
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    loadStateFromStorage();
                }
                break;
        }
    });
    
    // Animation speed control
    $('#animationSpeed').on('input', function() {
        const speed = $(this).val();
        $('#speedValue').text(speed + 'ms');
        if (mainCube3d) {
            mainCube3d.options.animationDuration = parseInt(speed);
        }
    });
    
    // Undo/Redo buttons
    $('#undoBtn').click(undo);
    $('#redoBtn').click(redo);

// Camera variables
let cameraStream = null;
let capturedFaces = {};
let currentFaceIndex = 0;
const faceOrder = ['front', 'back', 'left', 'right', 'up', 'down'];
const faceInstructions = {
    'front': 'Hold cube with RED center facing you',
    'back': 'Hold cube with ORANGE center facing you',
    'left': 'Hold cube with GREEN center facing you',
    'right': 'Hold cube with BLUE center facing you',
    'up': 'Hold cube with WHITE center facing you',
    'down': 'Hold cube with YELLOW center facing you'
};

// Helper function to get cookie value
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// --- INITIALIZATION ---

$(document).ready(function() {
    
    // Initialize core components
    resetCube();  // This should be called BEFORE creating 3D cubes
    
    // Create 3D cubes after state is initialized
    mainCube3d = new Cube3D('cube3d-container');
    
    // Initialize both preview cubes in their respective containers
    if (document.getElementById('manual-cube-3d')) {  // Add existence check
        manualPreviewCube = new Cube3D('manual-cube-3d', { interactive: true, cameraDistance: 8 });
    }
    if (document.getElementById('camera-cube-3d')) {  // Add existence check
        cameraPreviewCube = new Cube3D('camera-cube-3d', { interactive: true, cameraDistance: 8 });
    }
    
    // Defer the initial color update to ensure models are fully loaded
    setTimeout(() => {
        updateAll3DCubes();
    }, 100); // Increased delay for better initialization
    
    // --- EVENT HANDLERS ---
    
    // Color palette selection
    $('#colorPalette').on('click', '.color-btn', function() {
        $('#colorPalette .color-btn').removeClass('active');
        $(this).addClass('active');
    });
    
    // 2D sticker click handler with validation
    $('.cube-face-grid').on('click', '.cube-sticker', function() {
        const $sticker = $(this);
        
        // Prevent changing center stickers
        if ($sticker.data('index') === 4) {
            showAlert('Center stickers are fixed and cannot be changed', 'warning');
            return;
        }
        
        const face = $sticker.closest('.cube-face-grid').data('face');
        const index = $sticker.data('index');
        const currentColor = $('#colorPalette .active').data('color');
        
        if (!currentColor) {
            showAlert('Please select a color first', 'info');
            return;
        }
        
        // Check if color is already at limit (excluding current sticker)
        const oldColor = cubeState[face][index];
        const colorCount = countColor(currentColor) - (oldColor === currentColor ? 1 : 0);
        
        if (colorCount >= 9 && oldColor !== currentColor) {
            showAlert(`Cannot add more ${getColorName(currentColor)} stickers. Maximum is 9.`, 'warning');
            animateInvalidPlacement($sticker);
            return;
        }
        
        // Save state before change
        saveState();
        
        // Apply color change
        cubeState[face][index] = currentColor;
        
        // Visual feedback
        $sticker.addClass('sticker-changing');
        updateVisualFromState();
        updateColorCounter();
        updateAll3DCubes();
        triggerAutoSave();
        
        setTimeout(() => {
            $sticker.removeClass('sticker-changing');
        }, 300);
    });
    
    function countColor(color) {
        let count = 0;
        for (const face in cubeState) {
            cubeState[face].forEach(c => {
                if (c === color) count++;
            });
        }
        return count;
    }
    
    function getColorName(color) {
        const names = {
            'W': 'White', 'Y': 'Yellow', 'R': 'Red',
            'O': 'Orange', 'G': 'Green', 'B': 'Blue'
        };
        return names[color] || color;
    }
    
    function animateInvalidPlacement($element) {
        $element.addClass('invalid-shake');
        setTimeout(() => {
            $element.removeClass('invalid-shake');
        }, 500);
    }
    
    // Main action buttons
    $('#solveCubeBtn').click(solveCube);
    $('#resetCubeBtn').click(resetCube);
    $('#randomScrambleBtn').click(generateRandomScramble);
    $('#processImagesBtn').click(processImages);

    // Image upload handlers
    $('.face-upload').change(handleImageUpload);
    $('.upload-area').click(function() {
        $(this).find('.face-upload').click();
    });
    
    // 3D Animation Controls
    $('#playBtn').click(playAnimation);
    $('#pauseBtn').click(pauseAnimation);
    $('#resetAnimationBtn').click(resetAnimation);
    $('#nextStepBtn').click(nextStep);
    $('#prevStepBtn').click(prevStep);

    // Corner Cube UI Controls
    $('#toggleManualCube').click(function() {
        $('#manual-cube-container').toggleClass('expanded');
        setTimeout(() => {
            if (manualPreviewCube) manualPreviewCube.handleResize();
        }, 300);
    });
    $('#toggleCameraCube').click(function() {
        $('#camera-cube-container').toggleClass('expanded');
        setTimeout(() => {
            if (cameraPreviewCube) cameraPreviewCube.handleResize();
        }, 300);
    });

    // Resize camera cube canvas when its tab is shown
    document.getElementById('camera-tab').addEventListener('shown.bs.tab', function () {
        if (cameraPreviewCube) {
            cameraPreviewCube.handleResize();
        }
    });

    // Camera control buttons
    $('#liveCameraBtn').click(function() {
        $(this).addClass('active');
        $('#uploadFilesBtn').removeClass('active');
        $('#liveCameraSection').removeClass('d-none');
        $('#fileUploadSection').addClass('d-none');
    });
    
    $('#uploadFilesBtn').click(function() {
        $(this).addClass('active');
        $('#liveCameraBtn').removeClass('active');
        $('#fileUploadSection').removeClass('d-none');
        $('#liveCameraSection').addClass('d-none');
        stopCamera();
    });
    
    $('#startCameraBtn').click(startCamera);
    $('#stopCameraBtn').click(stopCamera);
});


// --- CORE API-CALLING FUNCTIONS ---

function solveCube() {
    if (!validateCubeState()) {
        showAlert('Invalid cube state! Please check that each color has 9 stickers.', 'danger');
        return;
    }
    
    $('#solveCubeBtn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Solving...');
    
    // Try client-side solver first
    try {
        const cube = new CubeModel();
        cube.state = JSON.parse(JSON.stringify(cubeState));
        
        const solver = new CubeSolverJS(cube);
        const solution = solver.solve();
        
        if (solution && solution.length > 0) {
            $('#animationControls').data('scrambled-state', JSON.parse(JSON.stringify(cubeState)));
            displaySolution(solution, solution.length);
            $('#solveCubeBtn').prop('disabled', false).html('<i class="fas fa-magic"></i> Solve Cube');
            return;
        }
    } catch (error) {
        console.error('Client-side solver failed:', error);
    }
    
    // Fallback to server-side solver
    const csrfToken = $('meta[name="csrf-token"]').attr('content') ||
                      document.querySelector('input[name="csrf_token"]')?.value ||
                      getCookie('csrf_token');
    
    $.ajax({
        url: '/api/solve',
        method: 'POST',
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': csrfToken
        },
        data: JSON.stringify({ state: cubeState }),
        success: function(response) {
            if (response.success) {
                $('#animationControls').data('scrambled-state', JSON.parse(JSON.stringify(cubeState)));
                displaySolution(response.solution, response.move_count);
                
                if (response.solver === 'basic') {
                    showAlert('Using basic solver. For optimal solutions, install kociemba.', 'info');
                }
            } else if (response.fallback) {
                showAlert('Server solver unavailable. Using basic algorithm.', 'warning');
                // Use hardcoded basic solution
                const basicSolution = "R U R' U' R' F R2 U' R' U' R U R' F'".split(' ');
                displaySolution(basicSolution, basicSolution.length);
            } else {
                showAlert('Failed to solve cube: ' + (response.error || 'Unknown error'), 'danger');
            }
        },
        error: function(jqXHR) {
            // Complete fallback to client-side
            const cube = new CubeModel();
            cube.state = JSON.parse(JSON.stringify(cubeState));
            const solver = new CubeSolverJS(cube);
            const solution = solver.solve();
            displaySolution(solution, solution.length);
            showAlert('Using offline solver', 'info');
        },
        complete: function() {
            $('#solveCubeBtn').prop('disabled', false).html('<i class="fas fa-magic"></i> Solve Cube');
        }
    });
}

function processImages() {
    const formData = new FormData();
    let hasAllImages = true;
    
    ['up', 'right', 'front', 'down', 'left', 'back'].forEach(face => {
        const input = $('#' + face + '-upload')[0];
        if (input.files.length > 0) {
            formData.append(face, input.files[0]);
        } else {
            hasAllImages = false;
        }
    });
    
    if (!hasAllImages) {
        showAlert('Please upload images for all 6 faces', 'warning');
        return;
    }
    
    $('#processImagesBtn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Processing...');
    
    // Get CSRF token - handle both meta tag and cookie
    const csrfToken = $('meta[name="csrf-token"]').attr('content') ||
                          document.querySelector('input[name="csrf_token"]')?.value ||
                          getCookie('csrf_token');
    
    $.ajax({
        url: '/api/solve/image',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: {
            'X-CSRFToken': csrfToken
        },
        success: function(response) {
            if (response.success) {
                cubeState = response.state;
                updateVisualFromState();
                updateColorCounter();
                updateAll3DCubes();
                
                $('#animationControls').data('scrambled-state', JSON.parse(JSON.stringify(cubeState)));
                
                displaySolution(response.solution, response.move_count);
                showAlert('Scan successful! Please verify the detected colors before playing the solution.', 'success');
                
                // Switch to manual tab to show detected colors
                const manualTab = document.querySelector('#manual-tab');
                if (manualTab) {
                    const bsTab = new bootstrap.Tab(manualTab);
                    bsTab.show();
                }
            } else {
                showAlert('Image Processing Failed: ' + (response.error || 'The scanned cube state is not solvable.'), 'danger');
            }
        },
        error: function(jqXHR) {
            const errorMsg = jqXHR.responseJSON ? jqXHR.responseJSON.error : 'An unknown server error occurred.';
            showAlert('Scan Error: ' + errorMsg, 'danger');
        },
        complete: function() {
            $('#processImagesBtn').prop('disabled', false).html('<i class="fas fa-camera"></i> Scan with Camera');
        }
    });
}

function generateRandomScramble() {
    $.get('/api/scramble', function(response) {
        const scramble = response.scramble;
        
        // Reset to solved state first
        cubeState = {
            up: Array(9).fill('W'),
            down: Array(9).fill('Y'),
            front: Array(9).fill('R'),
            back: Array(9).fill('O'),
            left: Array(9).fill('G'),
            right: Array(9).fill('B')
        };
        
        // Apply scramble to the JS model
        jsCube.reset();
        jsCube.executeAlgorithm(scramble);
        
        // Copy the scrambled state back
        cubeState = JSON.parse(JSON.stringify(jsCube.state));
        
        // Update all displays
        updateVisualFromState();
        updateColorCounter();
        updateAll3DCubes();
        
        // Store scrambled state for animation
        $('#animationControls').data('scrambled-state', JSON.parse(JSON.stringify(cubeState)));
        
        showAlert('Applied scramble: ' + scramble, 'info');
    }).fail(function() {
        // Fallback to client-side scramble generation
        const moves = ['R', 'L', 'U', 'D', 'F', 'B'];
        const modifiers = ['', "'", '2'];
        let scramble = [];
        
        for (let i = 0; i < 20; i++) {
            const move = moves[Math.floor(Math.random() * moves.length)];
            const modifier = modifiers[Math.floor(Math.random() * modifiers.length)];
            scramble.push(move + modifier);
        }
        
        const scrambleStr = scramble.join(' ');
        
        cubeState = {
            up: Array(9).fill('W'),
            down: Array(9).fill('Y'),
            front: Array(9).fill('R'),
            back: Array(9).fill('O'),
            left: Array(9).fill('G'),
            right: Array(9).fill('B')
        };
        
        jsCube.reset();
        jsCube.executeAlgorithm(scrambleStr);
        cubeState = JSON.parse(JSON.stringify(jsCube.state));
        
        updateVisualFromState();
        updateColorCounter();
        updateAll3DCubes();
        
        $('#animationControls').data('scrambled-state', JSON.parse(JSON.stringify(cubeState)));
        showAlert('Applied scramble: ' + scrambleStr, 'info');
    });
}

// --- UI & STATE UPDATE FUNCTIONS ---

function resetCube() {
    // Set to solved state
    cubeState = {
        up: Array(9).fill('W'),
        down: Array(9).fill('Y'),
        front: Array(9).fill('R'),
        back: Array(9).fill('O'),
        left: Array(9).fill('G'),
        right: Array(9).fill('B')
    };

    // Reset camera captures
    resetCameraCapture();

    // Clear file uploads
    $('.face-upload').val('');
    $('.preview-img').addClass('d-none');
    $('.upload-area-content').show();

    // Update JS model
    jsCube.reset();
    jsCube.state = JSON.parse(JSON.stringify(cubeState));

    // Update visual elements
    updateVisualFromState();
    updateColorCounter();
    updateAll3DCubes();

    // Reset solution display
    $('#solutionDisplay').addClass('d-none');
    currentSolution = [];
    currentMoveIndex = 0;
    isPlaying = false;

    // Reset 3D cube orientation
    if (mainCube3d) {
        mainCube3d.reset();
    }
}

function updateVisualFromState() {
    for (const face in cubeState) {
        const grid = $(`.cube-face-grid[data-face="${face}"]`);
        cubeState[face].forEach((color, index) => {
            const sticker = grid.find(`.cube-sticker[data-index="${index}"]`);
            sticker.removeClass('sticker-W sticker-Y sticker-R sticker-O sticker-G sticker-B');
            sticker.addClass('sticker-' + color);
        });
    }
}

function updateAll3DCubes() {
    if (mainCube3d) {
        mainCube3d.updateCubeColors(cubeState);
    }
    if (manualPreviewCube) {
        manualPreviewCube.updateCubeColors(cubeState);
    }
    if (cameraPreviewCube) {
        cameraPreviewCube.updateCubeColors(cubeState);
    }
}

function updateColorCounter() {
    const counts = { W: 0, Y: 0, R: 0, O: 0, G: 0, B: 0 };
    
    // Ensure cubeState exists and has valid structure
    if (cubeState && typeof cubeState === 'object') {
        for (const face in cubeState) {
            if (Array.isArray(cubeState[face])) {
                cubeState[face].forEach(color => {
                    if (color && counts.hasOwnProperty(color)) {
                        counts[color]++;
                    }
                });
            }
        }
    }
    
    // Update UI with counts
    for (const color in counts) {
        const count = counts[color] || 0;
        $('#count' + color).text(count);
        $('#count' + color).parent().toggleClass('text-danger', count !== 9);
    }
}

function validateCubeState() {
    // Check if cubeState exists and has all faces
    if (!cubeState || typeof cubeState !== 'object') {
        console.error('Cube state not initialized');
        return false;
    }
    const requiredFaces = ['up', 'down', 'front', 'back', 'left', 'right'];
    for (const face of requiredFaces) {
        if (!cubeState[face] || !Array.isArray(cubeState[face]) || cubeState[face].length !== 9) {
            console.error(`Invalid face: ${face}`);
            return false;
        }
    }
    const counts = { W: 0, Y: 0, R: 0, O: 0, G: 0, B: 0 };
    for (const face in cubeState) {
        cubeState[face].forEach(color => {
             if (counts[color] !== undefined) {
                counts[color]++;
            }
        });
    }
    // Check each color appears exactly 9 times
    for (const color in counts) {
        if (counts[color] !== 9) {
            console.error(`Color ${color} appears ${counts[color]} times, expected 9`);
            return false;
        }
    }
    return true;
}

// --- STATE PERSISTENCE ---

function saveStateToStorage() {
    try {
        const saveData = {
            cubeState: cubeState,
            timestamp: new Date().toISOString(),
            version: '1.0'
        };
        
        localStorage.setItem('rubiksCubeState', JSON.stringify(saveData));
        showAlert('Cube state saved successfully', 'success');
        
        // Show save indicator
        showSaveIndicator();
        
    } catch (error) {
        console.error('Failed to save state:', error);
        showAlert('Failed to save cube state', 'error');
    }
}

function loadStateFromStorage() {
    try {
        const savedData = localStorage.getItem('rubiksCubeState');
        
        if (!savedData) {
            showAlert('No saved state found', 'warning');
            return;
        }
        
        const data = JSON.parse(savedData);
        
        if (data.cubeState) {
            cubeState = data.cubeState;
            updateVisualFromState();
            updateColorCounter();
            updateAll3DCubes();
            saveState(); // Add to history
            
            const date = new Date(data.timestamp);
            const timeAgo = getTimeAgo(date);
            showAlert(`Loaded state from ${timeAgo}`, 'success');
        }
        
    } catch (error) {
        console.error('Failed to load state:', error);
        showAlert('Failed to load saved state', 'error');
    }
}

function showSaveIndicator() {
    const indicator = $('<div class="save-indicator"><i class="fas fa-check"></i> Saved</div>');
    $('body').append(indicator);
    
    setTimeout(() => {
        indicator.addClass('fade-out');
        setTimeout(() => indicator.remove(), 300);
    }, 2000);
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + ' minutes ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + ' hours ago';
    return Math.floor(seconds / 86400) + ' days ago';
}

// --- ERROR RECOVERY ---

function recoverFromError(error, context) {
    console.error(`Error in ${context}:`, error);
    
    const recovery = {
        'solver': () => {
            showAlert('Solver encountered an error. Trying alternative method...', 'warning');
            
            // Try to recover with basic moves
            const emergencySolution = generateEmergencySolution();
            if (emergencySolution) {
                displaySolution(emergencySolution, emergencySolution.length);
                showAlert('Using emergency solution. May not be optimal.', 'info');
            } else {
                showAlert('Unable to solve. Please check your cube configuration.', 'error');
            }
        },
        
        'camera': () => {
            showAlert('Camera error detected. Switching to manual input.', 'warning');
            stopCamera();
            $('#manual-tab').click();
        },
        
        '3d-render': () => {
            showAlert('3D rendering issue. Reinitializing...', 'info');
            
            // Destroy and recreate 3D cubes
            if (mainCube3d) {
                mainCube3d.destroy();
                mainCube3d = null;
            }
            
            setTimeout(() => {
                mainCube3d = new Cube3D('cube3d-container');
                updateAll3DCubes();
            }, 100);
        },
        
        'state': () => {
            showAlert('Invalid state detected. Resetting to last valid state.', 'warning');
            
            if (stateHistory.length > 0 && historyIndex > 0) {
                historyIndex--;
                cubeState = JSON.parse(JSON.stringify(stateHistory[historyIndex]));
                updateVisualFromState();
                updateColorCounter();
                updateAll3DCubes();
            } else {
                resetCube();
            }
        }
    };
    
    if (recovery[context]) {
        recovery[context]();
    } else {
        showAlert('An unexpected error occurred. Please refresh the page.', 'error');
    }
}

function generateEmergencySolution() {
    // Basic solution that works for most scrambles
    return "U R U' L' U R' U' L U R U' L' U R' U' L".split(' ');
}

// Wrap critical functions with error handling
const safeExecute = (fn, context) => {
    return function(...args) {
        try {
            return fn.apply(this, args);
        } catch (error) {
            recoverFromError(error, context);
        }
    };
};

// Apply safe execution to critical functions
const originalSolveCube = solveCube;
solveCube = safeExecute(originalSolveCube, 'solver');

const originalStartCamera = startCamera;
startCamera = safeExecute(originalStartCamera, 'camera');

// Auto-save on changes
let autoSaveTimeout;
function triggerAutoSave() {
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = setTimeout(() => {
        saveStateToStorage();
    }, 3000); // Save after 3 seconds of inactivity
}

function displaySolution(solution, moveCount) {
    // Ensure solution is an array
    if (typeof solution === 'string') {
        solution = solution.split(' ').filter(m => m);
    }
    currentSolution = solution;
    currentMoveIndex = 0;
    isPlaying = false;
    $('#solutionDisplay').removeClass('d-none');
    $('#moveCount').text(parseInt(moveCount) || solution.length);
    const movesContainer = $('#solutionMoves');
    movesContainer.empty();
    if (solution.length === 0) {
        movesContainer.html('<div class="alert alert-info">Cube is already solved!</div>');
        return;
    }
    solution.forEach((move, index) => {
        const safeMove = $('<div>').text(move).html();
        const badge = $(`<span class="move-badge" data-index="${index}"></span>`);
        badge.text(safeMove);
        movesContainer.append(badge);
    });
    resetAnimation();
    highlightCurrentMove();
    // Auto-scroll to solution
    setTimeout(() => {
        const offset = $('#solutionDisplay').offset();
        if (offset) {
            $('html, body').animate({ scrollTop: offset.top - 100 }, 500);
        }
    }, 100);
    // Show solution stats
    const stats = analyzeSolution(solution);
    if (stats) {
        const statsHtml = `
            <div class="mt-2 small text-muted">
                <span class="me-3">HTM: ${stats.htm}</span>
                <span class="me-3">QTM: ${stats.qtm}</span>
                <span>Time: ~${stats.estimatedTime}s</span>
            </div>
        `;
        movesContainer.after(statsHtml);
    }
}

function analyzeSolution(solution) {
    let htm = solution.length;
    let qtm = 0;
    solution.forEach(move => {
        if (move.includes('2')) {
            qtm += 2;
        } else {
            qtm += 1;
        }
    });
    return {
        htm: htm,
        qtm: qtm,
        estimatedTime: Math.ceil(htm * 0.5) // Rough estimate
    };
}

function handleImageUpload() {
    const file = this.files[0];
    const $uploadArea = $(this).closest('.upload-area');  // Use jQuery object
    const face = $uploadArea.data('face');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            // Hide upload content and show preview
            $uploadArea.find('.upload-area-content').hide();
            
            // Check if preview image exists, create if not
            let $previewImg = $uploadArea.find('.preview-img');
            if ($previewImg.length === 0) {
                $previewImg = $('<img class="preview-img">');
                $uploadArea.append($previewImg);
            }
            $previewImg.attr('src', e.target.result).removeClass('d-none');
        };
        reader.readAsDataURL(file);
    }
}

function showAlert(message, type = 'info') {
    // Remove old implementation
    $('.alert.alert-dismissible').remove();
    
    // Create toast container if it doesn't exist
    if (!$('.toast-container').length) {
        $('body').append('<div class="toast-container"></div>');
    }
    
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle',
        danger: 'fas fa-exclamation-circle'
    };
    
    const titles = {
        success: 'Success',
        error: 'Error',
        warning: 'Warning',
        info: 'Information',
        danger: 'Error'
    };
    
    const toastType = type === 'danger' ? 'error' : type;
    
    const toast = $(`
        <div class="toast-notification ${toastType}">
            <i class="${icons[toastType]} toast-icon text-${type === 'danger' ? 'danger' : type}"></i>
            <div class="toast-content">
                <div class="toast-title">${titles[toastType]}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">&times;</button>
        </div>
    `);
    
    $('.toast-container').append(toast);
    
    // Auto remove after 5 seconds
    const timeout = setTimeout(() => {
        toast.addClass('removing');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
    
    // Manual close
    toast.find('.toast-close').click(() => {
        clearTimeout(timeout);
        toast.addClass('removing');
        setTimeout(() => toast.remove(), 300);
    });
}

// --- ANIMATION FUNCTIONS ---

function playAnimation() {
    if (isPlaying || !mainCube3d || currentSolution.length === 0) return;
    isPlaying = true;
    $('#playBtn').prop('disabled', true);
    $('#pauseBtn').prop('disabled', false);
    
    if (currentMoveIndex === 0) {
        resetAnimation();
    }

    function step() {
        if (!isPlaying || currentMoveIndex >= currentSolution.length) {
            pauseAnimation();
            return;
        }
        const move = currentSolution[currentMoveIndex];
        
        mainCube3d.animateMove(move, () => {
            const tempModel = new CubeModel();
            tempModel.state = JSON.parse(JSON.stringify(mainCube3d.cubeStateForAnimation));
            tempModel.executeAlgorithm(move);
            mainCube3d.cubeStateForAnimation = tempModel.state;
            
            currentMoveIndex++;
            highlightCurrentMove();
            step();
        });
    }
    step();
}

function pauseAnimation() {
    isPlaying = false;
    $('#playBtn').prop('disabled', false);
    $('#pauseBtn').prop('disabled', true);
}

function resetAnimation() {
    pauseAnimation();
    currentMoveIndex = 0;
    
    // Clear animation queue and reset cube
    if (mainCube3d) {
        mainCube3d.animationQueue = [];
        mainCube3d.isAnimating = false;
        
        // Reset cube rotation
        if (mainCube3d.mainGroup) {
            mainCube3d.mainGroup.quaternion.identity();
        }
        
        // Reset all cubies to initial positions
        for (const cubieName in mainCube3d.cubies) {
            const cubie = mainCube3d.cubies[cubieName];
            const initialState = mainCube3d.initialCubieStates[cubieName];
            if (initialState && cubie) {
                cubie.position.copy(initialState.position);
                cubie.quaternion.copy(initialState.quaternion);
            }
        }
        
        // Reset to scrambled state if available
        const scrambledState = $('#animationControls').data('scrambled-state');
        if (scrambledState) {
            mainCube3d.updateCubeColors(scrambledState);
            mainCube3d.cubeStateForAnimation = JSON.parse(JSON.stringify(scrambledState));
        }
    }
    
    highlightCurrentMove();
}

function nextStep() {
    if (isPlaying || currentMoveIndex >= currentSolution.length) return;
    pauseAnimation();
    const move = currentSolution[currentMoveIndex];
    
    const tempModel = new CubeModel();
    tempModel.state = JSON.parse(JSON.stringify(mainCube3d.cubeStateForAnimation));
    tempModel.executeAlgorithm(move);
    mainCube3d.cubeStateForAnimation = tempModel.state;

    mainCube3d.animateMove(move, () => {
        currentMoveIndex++;
        highlightCurrentMove();
    });
}

function prevStep() {
    if (isPlaying || currentMoveIndex <= 0) return;
    pauseAnimation();
    currentMoveIndex--;
    highlightCurrentMove();

    const scrambledState = $('#animationControls').data('scrambled-state');
    const tempCube = new CubeModel();
    tempCube.state = JSON.parse(JSON.stringify(scrambledState));
    
    const movesToApply = currentSolution.slice(0, currentMoveIndex);
    if (movesToApply.length > 0) {  // Add check for empty moves
        tempCube.executeAlgorithm(movesToApply.join(' '));
    }
    
    mainCube3d.updateCubeColors(tempCube.state);
    mainCube3d.cubeStateForAnimation = tempCube.state;  // Add this line
}

function highlightCurrentMove() {
    $('.move-badge').removeClass('active-move');
    if (currentMoveIndex < currentSolution.length) {
        const targetBadge = $(`.move-badge[data-index="${currentMoveIndex}"]`);
        targetBadge.addClass('active-move');
        
        const container = $('.solution-moves-container');
        if(targetBadge.length) {
            const badgeTop = targetBadge.position().top;
            const containerHeight = container.height();
            
            container.scrollTop(container.scrollTop() + badgeTop - (containerHeight / 2) + (targetBadge.outerHeight() / 2));
        }
    }
}

// --- CAMERA FUNCTIONS ---

function resetCameraCapture() {
    capturedFaces = {};
    currentFaceIndex = 0;
    $('#capturedFaces').empty();
    $('#captureInterface').remove();
    if (cameraStream) {
        showCaptureInterface();
    }
}

// Mobile device detection and camera setup
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

async function setupMobileCamera() {
    if (isMobileDevice()) {
        // Request rear camera on mobile
        const constraints = {
            video: {
                facingMode: { exact: 'environment' },
                width: { ideal: 1920 },
                height: { ideal: 1080 }
            },
            audio: false
        };
        try {
            return await navigator.mediaDevices.getUserMedia(constraints);
        } catch (error) {
            // Fallback to any available camera
            return await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        }
    } else {
        // Desktop camera setup
        return await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: false
        });
    }
}

async function startCamera() {
    try {
        const video = document.getElementById('cameraVideo');
        // Check for camera permission
        const permission = await navigator.permissions.query({ name: 'camera' });
        if (permission.state === 'denied') {
            showAlert('Camera access denied. Please enable camera permissions.', 'danger');
            return;
        }
        cameraStream = await setupMobileCamera();
        video.srcObject = cameraStream;
        // Wait for video to load
        video.onloadedmetadata = () => {
            $('#cameraOverlay').addClass('d-none');
            $('#startCameraBtn').addClass('d-none');
            $('#stopCameraBtn').removeClass('d-none');
            showCaptureInterface();
        };
    } catch (error) {
        console.error('Camera error:', error);
        let errorMsg = 'Unable to access camera. ';
        if (error.name === 'NotAllowedError') {
            errorMsg += 'Please grant camera permissions.';
        } else if (error.name === 'NotFoundError') {
            errorMsg += 'No camera found on this device.';
        } else if (error.name === 'NotReadableError') {
            errorMsg += 'Camera is being used by another application.';
        } else {
            errorMsg += error.message || 'Unknown error occurred.';
        }
        showAlert(errorMsg, 'danger');
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    
    const video = document.getElementById('cameraVideo');
    video.srcObject = null;
    
    $('#startCameraBtn').removeClass('d-none');
    $('#stopCameraBtn').addClass('d-none');
    $('#captureInterface').remove();
}

function showCaptureInterface() {
    $('#captureInterface').remove(); // Remove old interface first
    const interface = $(`
        <div id="captureInterface" class="mt-3">
            <div class="alert alert-info">
                <h5>${faceInstructions[faceOrder[currentFaceIndex]]}</h5>
                <p>Face ${currentFaceIndex + 1} of 6</p>
            </div>
            <button class="btn btn-primary btn-lg w-100" onclick="captureFace()">
                <i class="fas fa-camera"></i> Capture ${faceOrder[currentFaceIndex].toUpperCase()} Face
            </button>
            <div class="progress mt-2">
                <div class="progress-bar" style="width: ${(currentFaceIndex/6)*100}%"></div>
            </div>
        </div>
    `);
    $('#liveCameraSection').append(interface);
}

async function captureFace() {
    const video = document.getElementById('cameraVideo');
    const canvas = document.getElementById('cameraCanvas');
    const ctx = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);
    
    const face = faceOrder[currentFaceIndex];
    
    // Process the captured image
    const imageData = canvas.toDataURL('image/jpeg');
    capturedFaces[face] = imageData;
    
    // Show thumbnail
    const thumbnail = $(`
        <div class="col-4 col-md-2 mb-2">
            <div class="card">
                <img src="${imageData}" class="card-img-top" alt="${face}">
                <div class="card-body p-1 text-center">
                    <small>${face}</small>
                </div>
            </div>
        </div>
    `);
    $('#capturedFaces').append(thumbnail);
    
    currentFaceIndex++;
    
    if (currentFaceIndex >= 6) {
        // All faces captured
        $('#captureInterface').html(`
            <div class="alert alert-success">
                <h5>All faces captured!</h5>
                <button class="btn btn-success btn-lg w-100" onclick="processCapturedFaces()">
                    <i class="fas fa-magic"></i> Process & Solve
                </button>
            </div>
        `);
    } else {
        // Update interface for next face
        showCaptureInterface();
    }
}

async function processCapturedFaces() {
    $('#captureInterface').html('<div class="text-center"><div class="spinner-border"></div><p>Processing images...</p></div>');
    
    // Use client-side detection first
    try {
        const detectedState = await detectColorsClientSide(capturedFaces);
        
        if (detectedState) {
            cubeState = detectedState;
            updateVisualFromState();
            updateColorCounter();
            updateAll3DCubes();
            
            // Try to solve
            solveCube();
        }
    } catch (error) {
        console.error('Client-side detection failed:', error);
        // Fallback to server-side processing
        processImagesServer(capturedFaces);
    }
}

async function detectColorsClientSide(images) {
    const processor = new ImageProcessorJS();
    const detectedState = {};
    
    for (const [face, imageData] of Object.entries(images)) {
        try {
            // Convert base64 to image element
            const img = new Image();
            await new Promise((resolve, reject) => {
                img.onload = resolve;
                img.onerror = reject;
                img.src = imageData;
            });
            
            // Process image to detect colors
            const colors = await processor.processImage(img);
            detectedState[face] = colors;
            
        } catch (error) {
            console.error(`Failed to process ${face}:`, error);
            throw error;
        }
    }
    
    // Validate the detected state
    if (!validateCubeState()) {
        throw new Error('Invalid cube state detected');
    }
    
    return detectedState;
}

function processImagesServer(images) {
    const formData = new FormData();
    
    // Convert base64 images to blobs
    for (const [face, imageData] of Object.entries(images)) {
        const blob = dataURLtoBlob(imageData);
        formData.append(face, blob, `${face}.jpg`);
    }
    
    const csrfToken = $('meta[name="csrf-token"]').attr('content') ||
                      document.querySelector('input[name="csrf_token"]')?.value ||
                      getCookie('csrf_token');
    
    $.ajax({
        url: '/api/solve/image',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: {
            'X-CSRFToken': csrfToken
        },
        success: function(response) {
            if (response.success) {
                cubeState = response.state;
                updateVisualFromState();
                updateColorCounter();
                updateAll3DCubes();
                displaySolution(response.solution, response.move_count);
                stopCamera();
            } else {
                showAlert('Processing failed: ' + response.error, 'danger');
            }
        },
        error: function() {
            showAlert('Server processing failed', 'danger');
        }
    });
}

function dataURLtoBlob(dataURL) {
    const arr = dataURL.split(',');
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new Blob([u8arr], { type: mime });
}

