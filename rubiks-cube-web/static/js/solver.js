// rubiks-cube-web/static/js/solver.js

// --- GLOBAL STATE VARIABLES ---

// 2D cube state for UI
let cubeState = {};
const jsCube = new CubeModel(); // JS model for client-side scrambling

// 3D visualization and animation
let cube3d = null;
let currentSolution = [];
let currentMoveIndex = 0;
let isPlaying = false;


// --- INITIALIZATION ---

$(document).ready(function() {
    
    // Initialize core components
    resetCube(); // Sets initial cubeState
    cube3d = new Cube3D('cube3d-container');
    update3DCubeColors();
    
    // --- EVENT HANDLERS ---
    
    // Color palette selection
    $('#colorPalette').on('click', '.color-btn', function() {
        $('#colorPalette .color-btn').removeClass('active');
        $(this).addClass('active');
    });
    
    // 2D sticker click handler
    $('.cube-face-grid').on('click', '.cube-sticker', function() {
        if ($(this).data('index') === 4) return;
        
        const face = $(this).closest('.cube-face-grid').data('face');
        const index = $(this).data('index');
        const currentColor = $('#colorPalette .active').data('color');
        
        cubeState[face][index] = currentColor;
        updateVisualFromState();
        updateColorCounter();
        update3DCubeColors();
    });
    
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
});


// --- CORE API-CALLING FUNCTIONS ---

function solveCube() {
    if (!validateCubeState()) {
        showAlert('Invalid cube state! Please check that each color has 9 stickers.', 'danger');
        return;
    }
    
    $('#solveCubeBtn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Solving...');
    
    $.ajax({
        url: '/api/solve',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ state: cubeState }),
        success: function(response) {
            if (response.success) {
                $('#animationControls').data('scrambled-state', JSON.parse(JSON.stringify(cubeState)));
                displaySolution(response.solution, response.move_count);
            } else {
                showAlert('Failed to solve cube: ' + (response.error || 'Unknown error'), 'danger');
            }
        },
        error: function() {
            showAlert('Error connecting to the server. Please try again.', 'danger');
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
    
    $.ajax({
        url: '/api/solve/image',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.success) {
                // Update the UI with the state detected by the server
                cubeState = response.state;
                updateVisualFromState();
                updateColorCounter();
                update3DCubeColors();
                
                // Store the detected state for animation reset
                $('#animationControls').data('scrambled-state', JSON.parse(JSON.stringify(cubeState)));
                
                // Show the solution and alert the user to verify
                displaySolution(response.solution, response.move_count);
                showAlert('Scan successful! Please verify the detected colors. The solution is ready below.', 'success');
                $('#manual-tab').tab('show');
            } else {
                 showAlert('Failed to process images: ' + (response.error || 'The scanned cube state is not solvable.'), 'danger');
            }
        },
        error: function() {
            showAlert('Error connecting to the server for image processing.', 'danger');
        },
        complete: function() {
            $('#processImagesBtn').prop('disabled', false).html('<i class="fas fa-camera"></i> Scan with Camera');
        }
    });
}

function generateRandomScramble() {
    $.get('/api/scramble', function(response) {
        const scramble = response.scramble;
        jsCube.reset();
        jsCube.executeAlgorithm(scramble);
        cubeState = JSON.parse(JSON.stringify(jsCube.state));
        
        updateVisualFromState();
        updateColorCounter();
        update3DCubeColors();
        showAlert('Applied scramble: ' + scramble, 'info');
    });
}

// --- UI & STATE UPDATE FUNCTIONS ---

function resetCube() {
    jsCube.reset();
    cubeState = JSON.parse(JSON.stringify(jsCube.state));
    
    updateVisualFromState();
    updateColorCounter();
    update3DCubeColors();
    
    $('#solutionDisplay').addClass('d-none');
    currentSolution = [];
    currentMoveIndex = 0;
    pauseAnimation();
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

function update3DCubeColors() {
    if (cube3d) {
        cube3d.updateCubeColors(cubeState);
    }
}

function updateColorCounter() {
    const counts = { W: 0, Y: 0, R: 0, O: 0, G: 0, B: 0 };
    for (const face in cubeState) {
        cubeState[face].forEach(color => { if(counts[color] !== undefined) counts[color]++; });
    }
    for (const color in counts) {
        $('#count' + color).text(counts[color]).parent().toggleClass('text-danger', counts[color] !== 9);
    }
}

function validateCubeState() {
    const counts = { W: 0, Y: 0, R: 0, O: 0, G: 0, B: 0 };
    for (const face in cubeState) {
        cubeState[face].forEach(color => { if(counts[color] !== undefined) counts[color]++; });
    }
    return Object.values(counts).every(count => count === 9);
}

function displaySolution(solution, moveCount) {
    currentSolution = solution;
    currentMoveIndex = 0;
    isPlaying = false;
    
    $('#solutionDisplay').removeClass('d-none');
    $('#moveCount').text(moveCount);
    
    const movesContainer = $('#solutionMoves');
    movesContainer.empty();
    solution.forEach((move, index) => {
        const badge = $(`<span class="move-badge" data-index="${index}">${move}</span>`);
        movesContainer.append(badge);
    });

    update3DCubeColors();
    highlightCurrentMove();
    
    $('html, body').animate({ scrollTop: $('#solutionDisplay').offset().top - 100 }, 500);
}

function handleImageUpload() {
    const file = this.files[0];
    const face = $(this).closest('.upload-area').data('face');
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const uploadArea = $(`.upload-area[data-face="${face}"]`);
            uploadArea.find('.upload-icon, p, h5').hide();
            uploadArea.find('.preview-img').attr('src', e.target.result).removeClass('d-none');
        };
        reader.readAsDataURL(file);
    }
}

function showAlert(message, type = 'info') {
    $('.alert.alert-dismissible').alert('close');
    const alert = $(`<div class="alert alert-${type} alert-dismissible fade show" role="alert">${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>`);
    $('.container').prepend(alert);
    setTimeout(() => alert.alert('close'), 6000);
}

// --- ANIMATION FUNCTIONS ---

function playAnimation() {
    if (isPlaying || !cube3d || currentSolution.length === 0) return;
    isPlaying = true;
    $('#playBtn').prop('disabled', true);
    $('#pauseBtn').prop('disabled', false);

    function step() {
        if (!isPlaying || currentMoveIndex >= currentSolution.length) {
            pauseAnimation();
            return;
        }
        const move = currentSolution[currentMoveIndex];
        cube3d.animateMove(move, () => {
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
    const scrambledState = $('#animationControls').data('scrambled-state');
    if (scrambledState) {
        cube3d.updateCubeColors(scrambledState);
    }
    highlightCurrentMove();
}

function nextStep() {
    if (isPlaying || currentMoveIndex >= currentSolution.length) return;
    const move = currentSolution[currentMoveIndex];
    cube3d.animateMove(move, () => {
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
    
    for(let i=0; i < currentMoveIndex; i++) {
        tempCube.executeAlgorithm(currentSolution[i]);
    }
    cube3d.updateCubeColors(tempCube.state);
}

function highlightCurrentMove() {
    $('.move-badge').removeClass('active-move');
    if (currentMoveIndex < currentSolution.length) {
        $(`.move-badge[data-index="${currentMoveIndex}"]`).addClass('active-move');
    }
}