// rubiks-cube-web/static/js/cube3d.js

/**
 * Renders and animates a 3D Rubik's Cube by loading a Collada (.dae) model.
 */
class Cube3D {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(50, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.mainGroup = new THREE.Group(); // Group for rotating the whole cube
        this.cubies = [];
        this.isAnimating = false;

        this.colors = {
            'W': new THREE.Color(0xffffff), 'Y': new THREE.Color(0xffff00),
            'R': new THREE.Color(0xff0000), 'O': new THREE.Color(0xffa500),
            'G': new THREE.Color(0x00ff00), 'B': new THREE.Color(0x0000ff),
        };
        
        // Map face names and indices to the face normal vectors of a cubie mesh
        this.faceNormals = {
            right: { index: 0, vector: new THREE.Vector3(1, 0, 0) },
            left:  { index: 1, vector: new THREE.Vector3(-1, 0, 0) },
            up:    { index: 2, vector: new THREE.Vector3(0, 1, 0) },
            down:  { index: 3, vector: new THREE.Vector3(0, -1, 0) },
            front: { index: 4, vector: new THREE.Vector3(0, 0, 1) },
            back:  { index: 5, vector: new THREE.Vector3(0, 0, -1) },
        };

        this._init();
    }

    _init() {
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setClearColor(0x000000, 0);
        this.container.appendChild(this.renderer.domElement);

        this.scene.background = null;
        this.camera.position.set(4, 4, 6);
        this.camera.lookAt(0, 0, 0);

        const ambientLight = new THREE.AmbientLight(0xaaaaaa);
        this.scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.7);
        directionalLight.position.set(5, 10, 7.5);
        this.scene.add(directionalLight);

        this.scene.add(this.mainGroup);
        this.loadDAEModel();
        this._initControls();

        this.animate = this.animate.bind(this);
        this.animate();

        window.addEventListener('resize', () => {
            this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        });
    }

    loadDAEModel() {
        const loader = new THREE.ColladaLoader();
        loader.load('static/RubixCube.dae', (collada) => {
            const modelScene = collada.scene;
            
            // Traverse the loaded model to find and store the cubies
            modelScene.traverse((node) => {
                if (node.isMesh && node.name.startsWith('cubie_')) {
                    // Ensure materials are unique for coloring
                    node.material = node.material.clone();
                    this.cubies.push(node);
                }
            });

            if (this.cubies.length < 26) {
                console.error("Model load error: Could not find 26 objects named 'cubie_*' in the .dae file.");
                // You could add a fallback or display an error message here.
            }

            this.mainGroup.add(modelScene);
            this.updateCubeColors(new CubeModel().state); // Color with solved state initially
        });
    }

    updateCubeColors(cubeState) {
        if (this.cubies.length === 0) return; // Model not loaded yet

        const stickerData = this.mapStateToStickers(cubeState);

        this.cubies.forEach(cubie => {
            // Find which piece this cubie corresponds to in the sticker data
            const piece = Object.values(stickerData).find(p => p.name === cubie.name);
            if (!piece) return;

            // Apply colors to the correct faces of this cubie's mesh
            for (const faceName in piece.colors) {
                const colorChar = piece.colors[faceName];
                const faceInfo = this.faceNormals[faceName];
                if (faceInfo) {
                    cubie.material.materials[faceInfo.index].color.set(this.colors[colorChar]);
                }
            }
        });
    }
    
    // This is a helper to map the flat cubeState to a piece-oriented structure
    mapStateToStickers(cubeState) {
         // This is a simplified mapping. A full implementation would be more complex
         // based on the exact names in your .dae file. This assumes names like "cubie_UFR".
        return {
            'UFR': { name: 'cubie_UFR', colors: { up: cubeState.up[8], front: cubeState.front[2], right: cubeState.right[2] } },
            // ... and so on for all 26 cubies
        };
    }

    animateMove(move, callback) {
        if (this.isAnimating) return;
        this.isAnimating = true;

        const face = move[0].toUpperCase();
        const prime = move.includes("'");
        const double = move.includes("2");
        const angle = (double ? Math.PI : Math.PI / 2) * (prime ? -1 : 1); // Adjusted direction

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
            pivot.attach(cubie);
        });

        const startRotation = new THREE.Quaternion();
        const endRotation = new THREE.Quaternion().setFromAxisAngle(axis, angle);
        let startTime = null;
        const duration = 300;

        const animateRotation = (timestamp) => {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / duration, 1);
            
            THREE.Quaternion.slerp(startRotation, endRotation, pivot.quaternion, progress);

            if (progress < 1) {
                requestAnimationFrame(animateRotation);
            } else {
                this.mainGroup.add(...pivot.children);
                this.mainGroup.remove(pivot);
                this.isAnimating = false;
                if (callback) callback();
            }
        };
        requestAnimationFrame(animateRotation);
    }
    
    getCubiesForFace(face) {
        // Return cubies based on their current position in the 3D scene
        const threshold = 0.5;
        switch (face) {
            case 'U': return this.cubies.filter(c => c.position.y > threshold);
            case 'D': return this.cubies.filter(c => c.position.y < -threshold);
            case 'R': return this.cubies.filter(c => c.position.x > threshold);
            case 'L': return this.cubies.filter(c => c.position.x < -threshold);
            case 'F': return this.cubies.filter(c => c.position.z > threshold);
            case 'B': return this.cubies.filter(c => c.position.z < -threshold);
            default: return [];
        }
    }
    
    animate() {
        requestAnimationFrame(this.animate);
        this.renderer.render(this.scene, this.camera);
    }

    _initControls() {
        let mouseDown = false, mouseX = 0, mouseY = 0;
        
        const onMouseDown = (event) => {
            mouseDown = true;
            mouseX = event.clientX;
            mouseY = event.clientY;
        };
        const onMouseUp = () => { mouseDown = false; };
        const onMouseMove = (event) => {
            if (!mouseDown || this.isAnimating) return;
            const deltaX = event.clientX - mouseX;
            const deltaY = event.clientY - mouseY;

            // Rotate around world axes, not local axes
            const quatX = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), deltaX * 0.01);
            const quatY = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), deltaY * 0.01);
            
            this.mainGroup.quaternion.premultiply(quatX).premultiply(quatY);

            mouseX = event.clientX;
            mouseY = event.clientY;
        };

        this.container.addEventListener('mousedown', onMouseDown);
        this.container.addEventListener('mouseup', onMouseUp);
        this.container.addEventListener('mousemove', onMouseMove);
    }
}