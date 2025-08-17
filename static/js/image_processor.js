// rubiks-cube-web/static/js/image_processor.js

/**
 * A client-side image processor for detecting Rubik's Cube colors using OpenCV.js.
 */
class ImageProcessorJS {
    constructor() {
        // Reference BGR colors for the 6 cube faces.
        // We will convert these to LAB color space for accurate comparisons.
        this.referenceColors = {
            'W': [255, 255, 255], // White
            'Y': [0, 255, 255],   // Yellow
            'R': [0, 0, 255],     // Red
            'O': [0, 165, 255],   // Orange
            'G': [0, 255, 0],     // Green
            'B': [255, 0, 0],     // Blue
        };
        this.referenceLab = {};
        for (const key in this.referenceColors) {
            this.referenceLab[key] = this.rgbToLab(this.referenceColors[key].slice().reverse()); // BGR to RGB
        }

        // --- Fix 26: Add cache for color distance calculations ---
        this.distanceCache = new Map();
    }

    /**
     * Main function to process an image element and return the 9 detected sticker colors.
     * @param {HTMLImageElement} imageElement - The image to process.
     * @returns {Promise<Array<string>>} A promise that resolves with an array of 9 color codes (e.g., ['W', 'R', 'B', ...]).
     */
    async processImage(imageElement) {
        return new Promise((resolve, reject) => {
            try {
                // Create canvas for image processing
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                canvas.width = imageElement.width;
                canvas.height = imageElement.height;
                ctx.drawImage(imageElement, 0, 0);
                
                // Simple grid-based color detection
                const colors = this.detectColorsSimple(canvas, ctx);
                resolve(colors);
                
            } catch (error) {
                console.error("Error during image processing:", error);
                reject("An error occurred during image processing.");
            }
        });
    }
    
    detectColorsSimple(canvas, ctx) {
        const width = canvas.width;
        const height = canvas.height;
        const gridSize = 3;
        const cellWidth = width / gridSize;
        const cellHeight = height / gridSize;
        const colors = [];
        
        for (let row = 0; row < gridSize; row++) {
            for (let col = 0; col < gridSize; col++) {
                // Sample center of each cell
                const x = Math.floor(col * cellWidth + cellWidth / 2);
                const y = Math.floor(row * cellHeight + cellHeight / 2);
                
                // Get average color in a small region
                const sampleSize = 20;
                const imageData = ctx.getImageData(
                    x - sampleSize/2, 
                    y - sampleSize/2, 
                    sampleSize, 
                    sampleSize
                );
                
                let r = 0, g = 0, b = 0;
                for (let i = 0; i < imageData.data.length; i += 4) {
                    r += imageData.data[i];
                    g += imageData.data[i + 1];
                    b += imageData.data[i + 2];
                }
                
                const pixels = imageData.data.length / 4;
                r = Math.floor(r / pixels);
                g = Math.floor(g / pixels);
                b = Math.floor(b / pixels);
                
                const color = this.getClosestColor([r, g, b]);
                colors.push(color);
            }
        }
        
        return colors;
    }

    findFaceContour(src) {
        let gray = new cv.Mat();
        cv.cvtColor(src, gray, cv.COLOR_RGBA2GRAY, 0);
        cv.GaussianBlur(gray, gray, new cv.Size(5, 5), 0, 0, cv.BORDER_DEFAULT);
        let thresh = new cv.Mat();
        cv.adaptiveThreshold(gray, thresh, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 11, 2);

        let contours = new cv.MatVector();
        let hierarchy = new cv.Mat();
        cv.findContours(thresh, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);

        let largestArea = 0;
        let bestContour = null;
        for (let i = 0; i < contours.size(); ++i) {
            let contour = contours.get(i);
            let area = cv.contourArea(contour, false);
            if (area > largestArea) {
                let peri = cv.arcLength(contour, true);
                let approx = new cv.Mat();
                cv.approxPolyDP(contour, approx, 0.04 * peri, true);
                if (approx.rows === 4 && area > 10000) { // Must be a quadrilateral and large enough
                    largestArea = area;
                    if (bestContour) bestContour.delete();
                    bestContour = approx.clone();
                }
                approx.delete();
            }
            contour.delete();
        }

        gray.delete();
        thresh.delete();
        contours.delete();
        hierarchy.delete();
        return bestContour;
    }

    getPerspectiveWarp(src, contour) {
        // Order the 4 points of the contour: top-left, top-right, bottom-right, bottom-left.
        let points = [];
        for (let i = 0; i < contour.rows; i++) {
            points.push({ x: contour.data32S[i * 2], y: contour.data32S[i * 2 + 1] });
        }
        points.sort((a, b) => a.y - b.y);
        let top = points.slice(0, 2).sort((a, b) => a.x - b.x);
        let bottom = points.slice(2, 4).sort((a, b) => a.x - b.x);
        let [tl, tr] = top;
        let [bl, br] = bottom;

        let srcTri = cv.matFromArray(4, 1, cv.CV_32FC2, [tl.x, tl.y, tr.x, tr.y, br.x, br.y, bl.x, bl.y]);

        const size = 300;
        let dstTri = cv.matFromArray(4, 1, cv.CV_32FC2, [0, 0, size, 0, size, size, 0, size]);
        
        let M = cv.getPerspectiveTransform(srcTri, dstTri);
        let warped = new cv.Mat();
        cv.warpPerspective(src, warped, M, new cv.Size(size, size));

        srcTri.delete();
        dstTri.delete();
        M.delete();
        return warped;
    }

    sampleStickerColors(warped) {
        const size = warped.cols;
        const stickerSize = size / 3;
        const margin = stickerSize * 0.2; // Sample from the center of the sticker
        
        let detectedColors = [];
        for (let row = 0; row < 3; row++) {
            for (let col = 0; col < 3; col++) {
                let rect = new cv.Rect(
                    col * stickerSize + margin,
                    row * stickerSize + margin,
                    stickerSize - 2 * margin,
                    stickerSize - 2 * margin
                );
                let roi = warped.roi(rect);
                
                // Calculate the average color of the region
                let meanColor = cv.mean(roi); // Returns [B, G, R, A]
                let rgb = [meanColor[2], meanColor[1], meanColor[0]];
                
                // Find the closest reference color
                detectedColors.push(this.getClosestColor(rgb));
                roi.delete();
            }
        }
        return detectedColors;
    }

    getClosestColor(rgb) {
        const lab = this.rgbToLab(rgb);
        let minDistance = Infinity;
        let closestColor = 'X';
        
        // --- Fix 26: Check cache first ---
        const cacheKey = `${rgb[0]},${rgb[1]},${rgb[2]}`;
        if (this.distanceCache.has(cacheKey)) {
            return this.distanceCache.get(cacheKey);
        }

        for (const key in this.referenceLab) {
            const distance = this.ciede2000(lab, this.referenceLab[key]);
            if (distance < minDistance) {
                minDistance = distance;
                closestColor = key;
            }
        }

        // --- Fix 26: Cache the result ---
        this.distanceCache.set(cacheKey, closestColor);

        // Limit cache size
        if (this.distanceCache.size > 1000) {
            const firstKey = this.distanceCache.keys().next().value;
            this.distanceCache.delete(firstKey);
        }

        return closestColor;
    }
    
    // --- COLOR SPACE CONVERSION AND COMPARISON ---
    // These functions are a JS port of the standard color science formulas.

    rgbToLab(rgb) {
        let [r, g, b] = rgb.map(c => c / 255);
        r = (r > 0.04045) ? Math.pow((r + 0.055) / 1.055, 2.4) : r / 12.92;
        g = (g > 0.04045) ? Math.pow((g + 0.055) / 1.055, 2.4) : g / 12.92;
        b = (b > 0.04045) ? Math.pow((b + 0.055) / 1.055, 2.4) : b / 12.92;
        
        let x = (r * 0.4124 + g * 0.3576 + b * 0.1805) * 100;
        let y = (r * 0.2126 + g * 0.7152 + b * 0.0722) * 100;
        let z = (r * 0.0193 + g * 0.1192 + b * 0.9505) * 100;

        x /= 95.047;
        y /= 100.000;
        z /= 108.883;

        x = (x > 0.008856) ? Math.pow(x, 1 / 3) : (7.787 * x) + 16 / 116;
        y = (y > 0.008856) ? Math.pow(y, 1 / 3) : (7.787 * y) + 16 / 116;
        z = (z > 0.008856) ? Math.pow(z, 1 / 3) : (7.787 * z) + 16 / 116;

        return [(116 * y) - 16, 500 * (x - y), 200 * (y - z)];
    }

    ciede2000(lab1, lab2) {
        const [L1, a1, b1] = lab1;
        const [L2, a2, b2] = lab2;

        const C1 = Math.sqrt(a1 * a1 + b1 * b1);
        const C2 = Math.sqrt(a2 * a2 + b2 * b2);
        const C_bar = (C1 + C2) / 2;
        
        const G = 0.5 * (1 - Math.sqrt(Math.pow(C_bar, 7) / (Math.pow(C_bar, 7) + Math.pow(25, 7))));
        
        const a1_prime = (1 + G) * a1;
        const a2_prime = (1 + G) * a2;
        
        const C1_prime = Math.sqrt(a1_prime * a1_prime + b1 * b1);
        const C2_prime = Math.sqrt(a2_prime * a2_prime + b2 * b2);
        
        let h1_prime = Math.atan2(b1, a1_prime) * (180 / Math.PI);
        if (h1_prime < 0) h1_prime += 360;
        let h2_prime = Math.atan2(b2, a2_prime) * (180 / Math.PI);
        if (h2_prime < 0) h2_prime += 360;

        const delta_L_prime = L2 - L1;
        const delta_C_prime = C2_prime - C1_prime;
        
        let delta_h_prime;
        if (C1_prime * C2_prime === 0) delta_h_prime = 0;
        else if (Math.abs(h1_prime - h2_prime) <= 180) delta_h_prime = h2_prime - h1_prime;
        else if (h2_prime <= h1_prime) delta_h_prime = h2_prime - h1_prime + 360;
        else delta_h_prime = h2_prime - h1_prime - 360;

        const delta_H_prime = 2 * Math.sqrt(C1_prime * C2_prime) * Math.sin((delta_h_prime / 2) * (Math.PI / 180));
        
        const L_bar_prime = (L1 + L2) / 2;
        const C_bar_prime = (C1_prime + C2_prime) / 2;
        
        let h_bar_prime;
        if (C1_prime * C2_prime === 0) h_bar_prime = h1_prime + h2_prime;
        else if (Math.abs(h1_prime - h2_prime) <= 180) h_bar_prime = (h1_prime + h2_prime) / 2;
        else if (h1_prime + h2_prime < 360) h_bar_prime = (h1_prime + h2_prime + 360) / 2;
        else h_bar_prime = (h1_prime + h2_prime - 360) / 2;

        const T = 1 - 0.17 * Math.cos((h_bar_prime - 30) * (Math.PI / 180)) +
                      0.24 * Math.cos((2 * h_bar_prime) * (Math.PI / 180)) +
                      0.32 * Math.cos((3 * h_bar_prime + 6) * (Math.PI / 180)) -
                      0.20 * Math.cos((4 * h_bar_prime - 63) * (Math.PI / 180));

        const S_L = 1 + (0.015 * Math.pow(L_bar_prime - 50, 2)) / Math.sqrt(20 + Math.pow(L_bar_prime - 50, 2));
        const S_C = 1 + 0.045 * C_bar_prime;
        const S_H = 1 + 0.015 * C_bar_prime * T;
        
        const delta_theta = 30 * Math.exp(-Math.pow((h_bar_prime - 275) / 25, 2));
        const R_C = 2 * Math.sqrt(Math.pow(C_bar_prime, 7) / (Math.pow(C_bar_prime, 7) + Math.pow(25, 7)));
        const R_T = -R_C * Math.sin((2 * delta_theta) * (Math.PI / 180));
        
        const dE = Math.sqrt(
            Math.pow(delta_L_prime / S_L, 2) +
            Math.pow(delta_C_prime / S_C, 2) +
            Math.pow(delta_H_prime / S_H, 2) +
            R_T * (delta_C_prime / S_C) * (delta_H_prime / S_H)
        );
        
        return dE;
    }
}