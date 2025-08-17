// rubiks-cube-web/static/js/solver_worker.js

// Import the necessary scripts for the worker
// Use absolute paths from root
importScripts('/static/js/cube_model.js', '/static/js/solver_logic.js');

// Listen for messages from the main application thread
self.onmessage = function(e) {
    const { cubeState } = e.data;

    if (cubeState) {
        try {
            // Create a cube model and set its state
            const cube = new CubeModel();
            cube.state = cubeState;

            // Create a solver instance and solve the cube
            const solver = new CubeSolverJS(cube);
            const solution = solver.solve();
            
            // Send the successful result back to the main thread
            self.postMessage({
                success: true,
                solution: solution,
                move_count: solution.length
            });

        } catch (error) {
            // If an error occurs during solving, send an error message back
            self.postMessage({
                success: false,
                error: error.message || "An unknown error occurred in the solver worker."
            });
        }
    }
};