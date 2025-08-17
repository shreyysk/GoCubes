// Polyfills for older browsers

// Array.from polyfill
if (!Array.from) {
    Array.from = function(object) {
        return [].slice.call(object);
    };
}

// Object.assign polyfill
if (!Object.assign) {
    Object.assign = function(target) {
        for (var i = 1; i < arguments.length; i++) {
            var source = arguments[i];
            for (var key in source) {
                if (Object.prototype.hasOwnProperty.call(source, key)) {
                    target[key] = source[key];
                }
            }
        }
        return target;
    };
}

// String.includes polyfill
if (!String.prototype.includes) {
    String.prototype.includes = function(search, start) {
        if (typeof start !== 'number') {
            start = 0;
        }
        if (start + search.length > this.length) {
            return false;
        } else {
            return this.indexOf(search, start) !== -1;
        }
    };
}

// Promise polyfill check
if (typeof Promise === 'undefined') {
    console.warn('Promise not supported. Please include a Promise polyfill.');
}