// rubiks-cube-web/static/js/cube3d.js

/**
 * Enhanced 3D Rubik's Cube renderer with persistent display and animation support
 * @class Cube3D
 */
class Cube3D {
    /**
     * @param {string} containerId - The ID of the container element
     * @param {Object} options - Configuration options for the renderer
     */
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container with ID ${containerId} not found`);
            return;
        }

        // --- Configuration with defaults ---
        this.options = {
            size: options.size || 'auto',
            interactive: options.interactive !== false,
            animationDuration: options.animationDuration || 300,
            autoRotate: options.autoRotate || false,
            cameraDistance: options.cameraDistance || 10
        };

        // Check WebGL support
        if (!window.WebGLRenderingContext) {
            console.error('WebGL not supported');
            this.container.innerHTML = '<p class="text-center text-muted">3D view requires WebGL support</p>';
            return;
        }

        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(
            50, 
            this.container.clientWidth / this.container.clientHeight, 
            0.1, 
            1000
        );
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true, 
            alpha: true
        });
        
        this.mainGroup = new THREE.Group();
        this.cubies = {};
        this.initialCubieStates = {}; // To store original position/rotation
        this.isAnimating = false;
        this.animationQueue = [];
        this.modelLoaded = false;
        
        // This variable will hold the logical state for animations
        this.cubeStateForAnimation = null;

        this.colors = {
            'W': new THREE.Color(0xffffff),
            'Y': new THREE.Color(0xffff00),
            'R': new THREE.Color(0xff0000),
            'O': new THREE.Color(0xffa500),
            'G': new THREE.Color(0x00ff00),
            'B': new THREE.Color(0x0000ff),
            'X': new THREE.Color(0x333333)
        };
        
        this.faceMaterialIndex = {
            right: 0,  // +X
            left:  1,  // -X  
            up:    2,  // +Y
            down:  3,  // -Y
            front: 4,  // +Z
            back:  5   // -Z
        };

        // Material creation helper
        this.createFaceMaterial = (color) => {
            return new THREE.MeshLambertMaterial({ 
                color: color || 0x1a1a1a,
                side: THREE.DoubleSide 
            });
        };

        this._init();
    }

    /**
     * Initializes the scene, camera, renderer, and lighting.
     * @private
     */
    _init() {
        const width = this.options.size === 'auto' ? this.container.clientWidth : this.options.size;
        const height = this.options.size === 'auto' ? this.container.clientHeight : this.options.size;
        
        this.renderer.setSize(width, height);
        this.renderer.setClearColor(0x000000, 0);
        this.container.appendChild(this.renderer.domElement);

        this.scene.background = null;
        
        const distance = this.options.cameraDistance;
        this.camera.position.set(distance * 0.7, distance * 0.7, distance);
        this.camera.lookAt(0, 0, 0);

        const ambientLight = new THREE.AmbientLight(0xaaaaaa);
        this.scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 10, 7.5);
        this.scene.add(directionalLight);

        this.scene.add(this.mainGroup);
        
        this.createProceduralCube();
        
        if (this.options.interactive) {
            this._initControls();
        }

        this.animate = this.animate.bind(this);
        this.animate();

        window.addEventListener('resize', () => this.handleResize());
    }

    /**
     * Generates a 3x3x3 cube procedurally from 26 individual cubie meshes.
     */
createProceduralCube() {
        const cubieSize = 0.98;  // Slightly smaller to prevent z-fighting
        const gap = 0.02;  // Much smaller gap
        const totalSize = 1;  // Keep total size at 1 unit

        for (let x = -1; x <= 1; x++) {
            for (let y = -1; y <= 1; y++) {
                for (let z = -1; z <= 1; z++) {
                    if (x === 0 && y === 0 && z === 0) continue;

                    const geometry = new THREE.BoxGeometry(cubieSize, cubieSize, cubieSize);
                    const materials = [
                        this.createFaceMaterial(0x1a1a1a), // Right (+X)
                        this.createFaceMaterial(0x1a1a1a), // Left (-X)
                        this.createFaceMaterial(0x1a1a1a), // Up (+Y)
                        this.createFaceMaterial(0x1a1a1a), // Down (-Y)
                        this.createFaceMaterial(0x1a1a1a), // Front (+Z)
                        this.createFaceMaterial(0x1a1a1a)  // Back (-Z)
                    ];

                    const cubie = new THREE.Mesh(geometry, materials);
                    cubie.position.set(x * totalSize, y * totalSize, z * totalSize);
                    
                    const name = this._getCubieNameByPosition({x, y, z});
                    cubie.name = name;
                    this.cubies[name] = cubie;

                    // Store the initial state for resetting animations
                    this.initialCubieStates[name] = {
                        position: cubie.position.clone(),
                        quaternion: cubie.quaternion.clone()
                    };

                    this.mainGroup.add(cubie);
                }
            }
        }
        
        this.modelLoaded = true;
        // Don't update colors here - wait for explicit call
        // this.updateCubeColors(new CubeModel().state);  // Remove this line
    }

    /**
     * Determines a cubie's name based on its position in the 3x3x3 grid.
     * @private
     */
    _getCubieNameByPosition(pos) {
        let name = 'cubie';
        if (pos.y > 0.5) name += 'U'; else if (pos.y < -0.5) name += 'D';
        if (pos.x < -0.5) name += 'L'; else if (pos.x > 0.5) name += 'R';
        if (pos.z > 0.5) name += 'F'; else if (pos.z < -0.5) name += 'B';
        if (name.length === 7) name = 'cubie' + name.substring(6, 7);
        return name;
    }

    /**
     * Updates the 3D model's sticker colors and resets physical orientation.
     * @param {Object} cubeState - The state object with 'up', 'down', etc., arrays.
     */
    updateCubeColors(cubeState) {
        if (!this.modelLoaded || !cubeState) return;
        
        // Store state for animation
        this.cubeStateForAnimation = JSON.parse(JSON.stringify(cubeState));
        
        // Reset all cubies to initial state before applying colors
        for (const cubieName in this.cubies) {
            const cubie = this.cubies[cubieName];
            const initialState = this.initialCubieStates[cubieName];
            
            // Reset position and rotation
            if (initialState) {
                cubie.position.copy(initialState.position);
                cubie.quaternion.copy(initialState.quaternion);
            }
            
            // Reset all materials to black first
            if (Array.isArray(cubie.material)) {
                cubie.material.forEach(mat => mat.color.set(0x1a1a1a));
            }
        }
        
        // Apply new colors
        const stickerData = this._mapStateToStickers(cubeState);
        for (const cubieName in stickerData) {
            const cubie = this.cubies[cubieName];
            if (!cubie) continue;
            
            const pieceData = stickerData[cubieName];
            if (pieceData && pieceData.colors) {
                for (const faceName in pieceData.colors) {
                    const colorChar = pieceData.colors[faceName];
                    const materialIndex = this.faceMaterialIndex[faceName];
                    if (materialIndex !== undefined && cubie.material[materialIndex]) {
                        cubie.material[materialIndex].color.set(this.colors[colorChar] || this.colors['X']);
                    }
                }
            }
        }
    }

    /**
     * Maps the flat 2D cube state object to a 3D piece-oriented structure.
     * @private
     */
    _mapStateToStickers(cubeState) {
    return {
        // Corner pieces - Fixed indices
        'cubieURF': { colors: { up: cubeState.up[8], right: cubeState.right[2], front: cubeState.front[2] } },
        'cubieULF': { colors: { up: cubeState.up[6], left: cubeState.left[0], front: cubeState.front[0] } },
        'cubieURB': { colors: { up: cubeState.up[2], right: cubeState.right[0], back: cubeState.back[0] } },
        'cubieULB': { colors: { up: cubeState.up[0], left: cubeState.left[2], back: cubeState.back[2] } },
        'cubieDRF': { colors: { down: cubeState.down[2], right: cubeState.right[8], front: cubeState.front[8] } },
        'cubieDLF': { colors: { down: cubeState.down[0], left: cubeState.left[6], front: cubeState.front[6] } },
        'cubieDRB': { colors: { down: cubeState.down[8], right: cubeState.right[6], back: cubeState.back[6] } },
        'cubieDLB': { colors: { down: cubeState.down[6], left: cubeState.left[8], back: cubeState.back[8] } },

        // Edge pieces - Fixed indices
        'cubieUF': { colors: { up: cubeState.up[7], front: cubeState.front[1] } },
        'cubieUB': { colors: { up: cubeState.up[1], back: cubeState.back[1] } },
        'cubieUR': { colors: { up: cubeState.up[5], right: cubeState.right[1] } },
        'cubieUL': { colors: { up: cubeState.up[3], left: cubeState.left[1] } },
        'cubieDF': { colors: { down: cubeState.down[1], front: cubeState.front[7] } },
        'cubieDB': { colors: { down: cubeState.down[7], back: cubeState.back[7] } },
        'cubieDR': { colors: { down: cubeState.down[5], right: cubeState.right[7] } },
        'cubieDL': { colors: { down: cubeState.down[3], left: cubeState.left[7] } },
        'cubieRF': { colors: { right: cubeState.right[5], front: cubeState.front[5] } },
        'cubieLF': { colors: { left: cubeState.left[3], front: cubeState.front[3] } },
        'cubieRB': { colors: { right: cubeState.right[3], back: cubeState.back[3] } },
        'cubieLB': { colors: { left: cubeState.left[5], back: cubeState.back[5] } },
        
        // Center pieces
        'cubieU': { colors: { up: cubeState.up[4] } },
        'cubieD': { colors: { down: cubeState.down[4] } },
        'cubieF': { colors: { front: cubeState.front[4] } },
        'cubieB': { colors: { back: cubeState.back[4] } },
        'cubieL': { colors: { left: cubeState.left[4] } },
        'cubieR': { colors: { right: cubeState.right[4] } }
    };
}
    /**
     * Animates a single move (e.g., "R", "U'", "F2").
     * @param {string} move - The move to animate.
     * @param {Function} callback - Function to call after the animation completes.
     */
    animateMove(move, callback) {
        if (this.isAnimating) {
            this.animationQueue.push({ move, callback });
            return;
        }
        
        this.isAnimating = true;

        const face = move[0].toUpperCase();
        const prime = move.includes("'");
        const double = move.includes("2");
        const angle = (double ? Math.PI : Math.PI / 2) * (prime ? 1 : -1);

        const axis = new THREE.Vector3(0, 0, 0);
        if (face === 'R') axis.set(1, 0, 0);
        else if (face === 'L') axis.set(-1, 0, 0);
        else if (face === 'U') axis.set(0, 1, 0);
        else if (face === 'D') axis.set(0, -1, 0);
        else if (face === 'F') axis.set(0, 0, 1);
        else if (face === 'B') axis.set(0, 0, -1);

        const pivot = new THREE.Group();
        this.mainGroup.add(pivot);

        const cubiesToMove = this.getCubiesForFace(face);
        
        cubiesToMove.forEach(cubie => {
            this.mainGroup.attach(cubie);
            pivot.attach(cubie);
        });

        const startRotation = new THREE.Quaternion();
        const endRotation = new THREE.Quaternion().setFromAxisAngle(axis, angle);
        let startTime = null;
        const duration = this.options.animationDuration * (double ? 1.5 : 1);

        const animateRotation = (timestamp) => {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / duration, 1);
            
            THREE.Quaternion.slerp(startRotation, endRotation, pivot.quaternion, progress);

            if (progress < 1) {
                requestAnimationFrame(animateRotation);
            } else {
                cubiesToMove.forEach(cubie => {
                    this.mainGroup.attach(cubie);
                });
                
                this.mainGroup.remove(pivot);
                this.isAnimating = false;
                
                if (callback) callback();
                
                if (this.animationQueue.length > 0) {
                    const next = this.animationQueue.shift();
                    this.animateMove(next.move, next.callback);
                }
            }
        };
        requestAnimationFrame(animateRotation);
    }
    
    /**
     * Gets an array of cubie meshes belonging to a specific face.
     * @param {string} face - The face identifier (U, D, R, L, F, B).
     * @returns {Array<THREE.Mesh>}
     */
    getCubiesForFace(face) {
        const threshold = 0.5;
        const cubiesList = Object.values(this.cubies);
        
        switch (face) {
            case 'U': return cubiesList.filter(c => c.position.y > threshold);
            case 'D': return cubiesList.filter(c => c.position.y < -threshold);
            case 'R': return cubiesList.filter(c => c.position.x > threshold);
            case 'L': return cubiesList.filter(c => c.position.x < -threshold);
            case 'F': return cubiesList.filter(c => c.position.z > threshold);
            case 'B': return cubiesList.filter(c => c.position.z < -threshold);
            default: return [];
        }
    }
    
    /**
     * The main render loop.
     */
    animate() {
        requestAnimationFrame(this.animate);
        
        if (this.options.autoRotate && !this.isAnimating) {
            this.mainGroup.rotation.y += 0.005;
        }
        
        this.renderer.render(this.scene, this.camera);
    }

    /**
     * Initializes mouse/touch controls for interactive rotation.
     * @private
     */
    _initControls() {
        let mouseDown = false, mouseX = 0, mouseY = 0;
        
        const onMouseDown = (event) => {
            if (this.isAnimating) return;
            mouseDown = true;
            mouseX = event.clientX;
            mouseY = event.clientY;
        };
        
        const onMouseUp = () => { mouseDown = false; };
        
        const onMouseMove = (event) => {
            if (!mouseDown || this.isAnimating) return;
            
            const deltaX = event.clientX - mouseX;
            const deltaY = event.clientY - mouseY;

            const quatX = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), deltaX * 0.01);
            const quatY = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), deltaY * 0.01);
            
            this.mainGroup.quaternion.premultiply(quatX).premultiply(quatY);

            mouseX = event.clientX;
            mouseY = event.clientY;
        };

        this.container.addEventListener('mousedown', onMouseDown);
        this.container.addEventListener('mouseup', onMouseUp);
        this.container.addEventListener('mousemove', onMouseMove);
        this.container.addEventListener('mouseleave', onMouseUp);
        
        // Touch events with proper handling
        this.container.addEventListener('touchstart', (e) => {
            e.preventDefault(); // Prevent scrolling
            if (e.touches.length === 1) {
                onMouseDown({ clientX: e.touches[0].clientX, clientY: e.touches[0].clientY });
            }
        }, { passive: false });
        
        this.container.addEventListener('touchmove', (e) => {
            e.preventDefault(); // Prevent scrolling
            if (e.touches.length === 1) {
                onMouseMove({ clientX: e.touches[0].clientX, clientY: e.touches[0].clientY });
            }
        }, { passive: false });
        
        this.container.addEventListener('touchend', (e) => {
            e.preventDefault();
            onMouseUp();
        }, { passive: false });
    }

    /**
     * Handles window resizing to keep the canvas dimensions correct.
     */
    handleResize() {
        if (this.options.size === 'auto' && this.container.clientWidth > 0) {
            this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        }
    }

    /**
     * Resets the 3D cube to its initial orientation and clears animations.
     */
    reset() {
        this.mainGroup.quaternion.identity();
        this.animationQueue = [];
        this.isAnimating = false;
    }

    /**
     * Cleans up Three.js resources to prevent memory leaks.
     */
    destroy() {
        // Stop animation loop
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        
        // Clear animation queue
        this.animationQueue = [];
        this.isAnimating = false;
        
        // Dispose of all geometries and materials
        for (const cubieName in this.cubies) {
            const cubie = this.cubies[cubieName];
            if (cubie) {
                // Dispose geometry
                if (cubie.geometry) {
                    cubie.geometry.dispose();
                }
                
                // Dispose materials
                if (cubie.material) {
                    if (Array.isArray(cubie.material)) {
                        cubie.material.forEach(mat => {
                            if (mat.dispose) mat.dispose();
                        });
                    } else {
                        if (cubie.material.dispose) cubie.material.dispose();
                    }
                }
                
                // Remove from scene
                if (this.mainGroup) {
                    this.mainGroup.remove(cubie);
                }
            }
        }
        
        // Clear lights
        if (this.scene) {
            this.scene.traverse((child) => {
                if (child instanceof THREE.Light) {
                    this.scene.remove(child);
                }
            });
        }
        
        // Dispose renderer
        if (this.renderer) {
            this.renderer.dispose();
            this.renderer.forceContextLoss();
            this.renderer.context = null;
            this.renderer.domElement = null;
            
            if (this.container && this.renderer.domElement && this.renderer.domElement.parentElement) {
                this.container.removeChild(this.renderer.domElement);
            }
        }
        
        // Clear all references
        this.cubies = {};
        this.initialCubieStates = {};
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.mainGroup = null;
        this.container = null;
        
        // Force garbage collection hint
        if (window.gc) {
            window.gc();
        }
    }
    
    // Add cleanup on page unload
    handleUnload() {
        window.addEventListener('beforeunload', () => {
            this.destroy();
        });
    }
}