// rubiks-cube-web/static/js/cube_model.js

/**
 * A JavaScript implementation of the Rubik's Cube model to allow for
 * client-side scrambling and state manipulation. This mirrors the Python logic.
 */
class CubeModel {
    constructor() {
        // This color mapping corresponds to the default solved state in `solver/cube.py`
        // Use face notation instead of colors for internal state
        this.faceNotation = {
            'W': 'U', 'Y': 'D', 'R': 'F', 
            'O': 'B', 'G': 'L', 'B': 'R'
        };
        this.solvedState = {
            up: Array(9).fill('W'),
            down: Array(9).fill('Y'),
            front: Array(9).fill('R'),
            back: Array(9).fill('O'),
            left: Array(9).fill('G'),
            right: Array(9).fill('B'),
        };
        this.reset();
    }

    reset() {
        this.state = JSON.parse(JSON.stringify(this.solvedState));
    }

    // Rotates the stickers on a single face
    _rotateFace(face, clockwise = true) {
        const faceState = this.state[face];
        const temp = [...faceState];
        const mapping = clockwise
            ? [2, 5, 8, 1, 4, 7, 0, 3, 6] // Fixed clockwise rotation
            : [6, 3, 0, 7, 4, 1, 8, 5, 2]; // Counter-clockwise

        for (let i = 0; i < 9; i++) {
            faceState[i] = temp[mapping[i]];
        }
    }

    // Generic move function to handle side effects
    _move(face, prime, double) {
        const cycles = double ? 2 : (prime ? 3 : 1);
        for (let i = 0; i < cycles; i++) {
            this._performMove(face);
        }
    }

    // The core logic for a single clockwise turn, matching cube.py
    _performMove(face) {
        const s = this.state;
        let temp;

        switch (face) {
            case 'F':
                this._rotateFace('front');
                temp = [s.up[6], s.up[7], s.up[8]];
                s.up[6] = s.left[8]; s.up[7] = s.left[5]; s.up[8] = s.left[2];
                s.left[2] = s.down[0]; s.left[5] = s.down[1]; s.left[8] = s.down[2];
                s.down[0] = s.right[6]; s.down[1] = s.right[3]; s.down[2] = s.right[0];
                s.right[0] = temp[0]; s.right[3] = temp[1]; s.right[6] = temp[2];
                break;
            case 'B':
                this._rotateFace('back');
                temp = [s.up[0], s.up[1], s.up[2]];
                s.up[0] = s.right[2]; s.up[1] = s.right[5]; s.up[2] = s.right[8];
                s.right[2] = s.down[8]; s.right[5] = s.down[7]; s.right[8] = s.down[6];
                s.down[6] = s.left[0]; s.down[7] = s.left[3]; s.down[8] = s.left[6];
                s.left[0] = temp[2]; s.left[3] = temp[1]; s.left[6] = temp[0];
                break;
            case 'U':
                this._rotateFace('up');
                temp = [s.front[0], s.front[1], s.front[2]];
                [s.front[0], s.front[1], s.front[2]] = [s.right[0], s.right[1], s.right[2]];
                [s.right[0], s.right[1], s.right[2]] = [s.back[0], s.back[1], s.back[2]];
                [s.back[0], s.back[1], s.back[2]] = [s.left[0], s.left[1], s.left[2]];
                [s.left[0], s.left[1], s.left[2]] = temp;
                break;
            case 'D':
                this._rotateFace('down');
                temp = [s.front[6], s.front[7], s.front[8]];
                [s.front[6], s.front[7], s.front[8]] = [s.left[6], s.left[7], s.left[8]];
                [s.left[6], s.left[7], s.left[8]] = [s.back[6], s.back[7], s.back[8]];
                [s.back[6], s.back[7], s.back[8]] = [s.right[6], s.right[7], s.right[8]];
                [s.right[6], s.right[7], s.right[8]] = temp;
                break;
            case 'L':
                this._rotateFace('left');
                temp = [s.up[0], s.up[3], s.up[6]];
                s.up[0] = s.back[8]; s.up[3] = s.back[5]; s.up[6] = s.back[2];
                s.back[2] = s.down[6]; s.back[5] = s.down[3]; s.back[8] = s.down[0];
                s.down[0] = s.front[0]; s.down[3] = s.front[3]; s.down[6] = s.front[6];
                s.front[0] = temp[0]; s.front[3] = temp[1]; s.front[6] = temp[2];
                break;
            case 'R':
                this._rotateFace('right');
                temp = [s.up[2], s.up[5], s.up[8]];
                s.up[2] = s.front[2]; s.up[5] = s.front[5]; s.up[8] = s.front[8];
                s.front[2] = s.down[2]; s.front[5] = s.down[5]; s.front[8] = s.down[8];
                s.down[2] = s.back[6]; s.down[5] = s.back[3]; s.down[8] = s.back[0];
                s.back[0] = temp[2]; s.back[3] = temp[1]; s.back[6] = temp[0];
                break;
        }
    }

    executeAlgorithm(algorithm) {
        const moves = algorithm.split(' ').filter(m => m);
        moves.forEach(move => {
            const face = move[0].toUpperCase();
            const prime = move.includes("'");
            const double = move.includes("2");
            this._move(face, prime, double);
        });
    }
}