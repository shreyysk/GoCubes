// rubiks-cube-web/static/js/solver_logic.js

/**
 * A JavaScript port of the Python beginner's method solver.
 * It takes a CubeModel object, solves it, and returns the solution moves.
 */
class CubeSolverJS {
    constructor(cubeModel) {
        // We work on a deep copy of the cube model to not alter the original
        this.cube = new CubeModel();
        this.cube.state = JSON.parse(JSON.stringify(cubeModel.state));
        this.solution = [];
    }

    solve() {
        if (this.isSolved()) {
            return [];
        }

        this.solveWhiteCross();
        this.solveWhiteCorners();
        this.solveMiddleLayer();
        this.solveYellowCross();
        this.positionYellowEdges();
        this.positionYellowCorners();
        this.orientYellowCorners();
        this.alignTopFace();

        return this.simplifyMoves(this.solution);
    }

    execute(moves) {
        this.cube.executeAlgorithm(moves);
        this.solution.push(...moves.split(' ').filter(m => m));
    }

    isSolved() {
        for (const face of Object.keys(this.cube.state)) {
            const faceColors = this.cube.state[face];
            const centerColor = faceColors[4];
            if (!faceColors.every(c => c === centerColor)) {
                return false;
            }
        }
        return true;
    }

    // --- SOLVER STEPS ---

    solveWhiteCross() {
        const white = 'W';
        const centers = { 'R': 'front', 'B': 'right', 'O': 'back', 'G': 'left' };
        // Find and position each white edge correctly
        for (const [color, faceName] of Object.entries(centers)) {
            // Find edge with white and current color
            let found = false;
            let attempts = 0;
            
            while (!found && attempts < 20) {
                attempts++;
                
                // Check all edges for white-color pair
                const edges = [
                    { pos: ['up', 1], pair: ['back', 1] },
                    { pos: ['up', 3], pair: ['left', 1] },
                    { pos: ['up', 5], pair: ['right', 1] },
                    { pos: ['up', 7], pair: ['front', 1] },
                    { pos: ['down', 1], pair: ['front', 7] },
                    { pos: ['down', 3], pair: ['left', 7] },
                    { pos: ['down', 5], pair: ['right', 7] },
                    { pos: ['down', 7], pair: ['back', 7] },
                    { pos: ['front', 3], pair: ['left', 5] },
                    { pos: ['front', 5], pair: ['right', 3] },
                    { pos: ['back', 3], pair: ['right', 5] },
                    { pos: ['back', 5], pair: ['left', 3] }
                ];
                
                for (const edge of edges) {
                    const color1 = this.cube.state[edge.pos[0]][edge.pos[1]];
                    const color2 = this.cube.state[edge.pair[0]][edge.pair[1]];
                    
                    if ((color1 === white && color2 === color) || 
                        (color2 === white && color1 === color)) {
                        // Found the edge, now position it
                        found = true;
                        break;
                    }
                }
                
                if (!found) {
                    this.execute('U');
                }
            }
            
            // Position edge in place with simplified moves
            this.execute('F2');
        }
    }
    
    solveWhiteCorners() {
        const white = 'W';
        const cornersToSolve = [['R', 'G'], ['B', 'R'], ['O', 'B'], ['G', 'O']];

        cornersToSolve.forEach(([frontColor, leftColor]) => {
            // Position the target slot at Front-Right
            while (this.cube.state.front[4] !== frontColor || this.cube.state.right[4] !== leftColor) {
                this.execute('y');
            }
            
            // Find the corner with white, frontColor, and leftColor
            // Move it to the URF position if it isn't there
            for (let i = 0; i < 5; i++) { // safety loop
                const u_colors = [this.cube.state.up[8], this.cube.state.front[2], this.cube.state.right[0]];
                if (u_colors.includes(white) && u_colors.includes(frontColor) && u_colors.includes(leftColor)) {
                    break;
                }
                this.execute('U');
            }
            
            // The corner is now at the top-front-right. Insert it correctly.
            while (this.cube.state.down[2] !== white || this.cube.state.front[8] !== frontColor) {
                this.execute("R' D' R D");
            }
        });
    }

    solveMiddleLayer() {
        const yellow = 'Y';
        let maxAttempts = 12; // Increased from 5
        
        for (let i = 0; i < maxAttempts; i++) {
            // Check if middle layer is already solved
            let middleSolved = true;
            const middleEdges = [
                ['front', 3], ['front', 5],
                ['right', 3], ['right', 5],
                ['back', 3], ['back', 5],
                ['left', 3], ['left', 5]
            ];
            
            for (const [face, idx] of middleEdges) {
                if (this.cube.state[face][idx] !== this.cube.state[face][4]) {
                    middleSolved = false;
                    break;
                }
            }
            
            if (middleSolved) return; // Middle layer complete
            
            // Find a non-yellow edge in the top layer
            let edgeFound = false;
            for (let j = 0; j < 4; j++) {
                if (this.cube.state.up[7] !== yellow && this.cube.state.front[1] !== yellow) {
                    edgeFound = true;
                    break;
                }
                this.execute('U');
            }

            // If no suitable edge is on top, one must be misplaced. Pop one out.
            if (!edgeFound) {
                 if (this.cube.state.front[5] !== this.cube.state.front[4] || this.cube.state.right[3] !== this.cube.state.right[4]) {
                     this.execute("U R U' R' U' F' U F");
                     continue; // Restart the process
                 } else {
                     this.execute('y'); // Check next slot
                 }
            }
            
            // Align the front color of the edge with its center
            while (this.cube.state.front[1] !== this.cube.state.front[4]) {
                this.execute('U');
            }

            // Insert to the right or left
            if (this.cube.state.up[7] === this.cube.state.right[4]) {
                this.execute("U R U' R' U' F' U F");
            } else {
                this.execute("U' L' U L U F U' F'");
            }
        }
    }

    solveYellowCross() {
        const yellow = 'Y';
        const isUp = (idx) => this.cube.state.up[idx] === yellow;
        
        // Check current state
        const state = [isUp(1), isUp(3), isUp(5), isUp(7)]; // B, L, R, F
        const yellowCount = state.filter(Boolean).length;

        if (yellowCount === 4) return;
        
        const alg = "F R U R' U' F'";
        if (yellowCount === 0) { // Dot
            this.execute(alg);
        }

        // L-Shape or Line-Shape
        for (let i=0; i < 4; i++) {
            if (isUp(3) && isUp(7)) { // L-Shape
                this.execute(alg);
                break;
            }
            this.execute('U');
        }
        
        for (let i=0; i < 2; i++) {
             if (isUp(3) && isUp(5)) { // Line-Shape
                this.execute(alg);
                break;
            }
            this.execute('U');
        }
    }
    
    positionYellowEdges() {
        const alg = "R U R' U R U2 R'";
        for (let i = 0; i < 4; i++) {
            if (this.cube.state.front[1] === this.cube.state.front[4]) break;
            this.execute('U');
        }

        for (let i = 0; i < 5; i++) {
            let correctCount = 0;
            for(let j=0; j<4; j++){
                if (this.cube.state.front[1] === this.cube.state.front[4]) correctCount++;
                this.execute('y');
            }
            if(correctCount === 4) return;
            
            // Position for the algorithm
            while (this.cube.state.back[1] !== this.cube.state.back[4]) {
                this.execute('y');
            }
            this.execute(alg);
        }
    }

    positionYellowCorners() {
        const alg = "U R U' L' U R' U' L";
        while (!this.areCornersPositioned()) {
            this.execute(alg);
        }
    }
    
    areCornersPositioned() {
        for (let i = 0; i < 4; i++) {
            const expected = new Set([this.cube.state.front[4], this.cube.state.right[4], 'Y']);
            const actual = new Set([this.cube.state.front[2], this.cube.state.right[0], this.cube.state.up[8]]);
            if (expected.size !== 3 || actual.size !== 3) return false; // Error case
            let diff = new Set([...expected].filter(x => !actual.has(x)));
            if (diff.size !== 0) return false;
            this.execute('y');
        }
        return true;
    }
    
    orientYellowCorners() {
        const alg = "R' D' R D";
        while(this.cube.state.up.filter(c => c === 'Y').length !== 9) {
            if (this.cube.state.up[8] !== 'Y') {
                for(let i=0; i<4; i++) { // Max 4 reps to orient
                     this.execute(alg);
                     if(this.cube.state.up[8] === 'Y') break;
                }
            }
            this.execute('U');
        }
    }
    
    alignTopFace() {
        while (this.cube.state.front[1] !== this.cube.state.front[4]) {
            this.execute('U');
        }
    }

    // --- UTILITY ---
    
    simplifyMoves(moves) {
        let simplified = [...moves];
        let changed = true;
        while (changed) {
            changed = false;
            if (simplified.length < 2) break;
            let newMoves = [];
            let i = 0;
            while (i < simplified.length) {
                if (i + 1 < simplified.length) {
                    const m1 = simplified[i];
                    const m2 = simplified[i + 1];
                    
                    // Same face moves
                    if (m1[0] === m2[0]) {
                        const face = m1[0];
                        let turns1 = m1.endsWith("'") ? 3 : (m1.endsWith("2") ? 2 : 1);
                        let turns2 = m2.endsWith("'") ? 3 : (m2.endsWith("2") ? 2 : 1);
                        let totalTurns = (turns1 + turns2) % 4;
                        
                        if (totalTurns === 0) {
                            // Moves cancel out
                            i += 2;
                            changed = true;
                        } else if (totalTurns === 1) {
                            newMoves.push(face);
                            i += 2;
                            changed = true;
                        } else if (totalTurns === 2) {
                            newMoves.push(face + '2');
                            i += 2;
                            changed = true;
                        } else { // totalTurns === 3
                            newMoves.push(face + "'");
                            i += 2;
                            changed = true;
                        }
                        continue;
                    }
                }
                newMoves.push(simplified[i]);
                i++;
            }
            simplified = newMoves;
        }
        return simplified;
    }
}