/**
 * ImageGenerationLoader — vanilla-JS port of the Aceternity UI component.
 * Renders the animated pixel-band loader on a canvas over a parent element.
 */
(function () {
    'use strict';

    const PIXEL_FONT = {
        A: '01110/10001/10001/11111/10001/10001/10001',
        B: '11110/10001/10001/11110/10001/10001/11110',
        C: '01111/10000/10000/10000/10000/10000/01111',
        D: '11110/10001/10001/10001/10001/10001/11110',
        E: '11111/10000/10000/11110/10000/10000/11111',
        F: '11111/10000/10000/11110/10000/10000/10000',
        G: '01111/10000/10000/10111/10001/10001/01111',
        H: '10001/10001/10001/11111/10001/10001/10001',
        I: '11111/00100/00100/00100/00100/00100/11111',
        J: '00111/00010/00010/00010/10010/10010/01100',
        K: '10001/10010/10100/11000/10100/10010/10001',
        L: '10000/10000/10000/10000/10000/10000/11111',
        M: '10001/11011/10101/10101/10001/10001/10001',
        N: '10001/11001/10101/10011/10001/10001/10001',
        O: '01110/10001/10001/10001/10001/10001/01110',
        P: '11110/10001/10001/11110/10000/10000/10000',
        Q: '01110/10001/10001/10001/10101/10010/01101',
        R: '11110/10001/10001/11110/10100/10010/10001',
        S: '01111/10000/10000/01110/00001/00001/11110',
        T: '11111/00100/00100/00100/00100/00100/00100',
        U: '10001/10001/10001/10001/10001/10001/01110',
        V: '10001/10001/10001/10001/10001/01010/00100',
        W: '10001/10001/10001/10101/10101/10101/01010',
        X: '10001/10001/01010/00100/01010/10001/10001',
        Y: '10001/10001/01010/00100/00100/00100/00100',
        Z: '11111/00001/00010/00100/01000/10000/11111',
        '0': '01110/10001/10011/10101/11001/10001/01110',
        '1': '00100/01100/00100/00100/00100/00100/01110',
        '2': '01110/10001/00001/00010/00100/01000/11111',
        '3': '11110/00001/00001/01110/00001/00001/11110',
        '4': '00010/00110/01010/10010/11111/00010/00010',
        '5': '11111/10000/10000/11110/00001/00001/11110',
        '6': '01110/10000/10000/11110/10001/10001/01110',
        '7': '11111/00001/00010/00100/01000/01000/01000',
        '8': '01110/10001/10001/01110/10001/10001/01110',
        '9': '01110/10001/10001/01111/00001/00001/01110',
        '-': '00000/00000/00000/11111/00000/00000/00000',
        '.': '00000/00000/00000/00000/00000/01100/01100',
        ':': '00000/01100/01100/00000/01100/01100/00000',
        '?': '01110/10001/00001/00010/00100/00000/00100'
    };

    const DEFAULT_COLORS = ['var(--color-blue-300)', 'var(--color-blue-600)'];
    const TAU = Math.PI * 2;
    const GLYPH_WIDTH = 5;
    const GLYPH_HEIGHT = 7;

    const EASING_CURVES = {
        linear: [0, 0, 1, 1],
        'ease-in': [0.42, 0, 1, 1],
        'ease-out': [0, 0, 0.58, 1],
        'ease-in-out': [0.42, 0, 0.58, 1]
    };

    const num = (value, fallback) => {
        const parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : fallback;
    };

    const randomFrom = (x, y, salt) => {
        const value = Math.sin(x * 12.9898 + y * 78.233 + salt * 37.719);
        return value * 43758.5453 - Math.floor(value * 43758.5453);
    };

    const cubicCoordinate = (time, point1, point2) => {
        const inverseTime = 1 - time;
        return 3 * inverseTime * inverseTime * time * point1 +
            3 * inverseTime * time * time * point2 +
            time * time * time;
    };

    const cubicDerivative = (time, point1, point2) => {
        const inverseTime = 1 - time;
        return 3 * inverseTime * inverseTime * point1 +
            6 * inverseTime * time * (point2 - point1) +
            3 * time * time * (1 - point2);
    };

    const createCubicBezier = (x1, y1, x2, y2) => {
        const safeX1 = Math.min(1, Math.max(0, x1));
        const safeX2 = Math.min(1, Math.max(0, x2));

        return progress => {
            let time = progress;
            for (let iteration = 0; iteration < 6; iteration++) {
                const difference = cubicCoordinate(time, safeX1, safeX2) - progress;
                const derivative = cubicDerivative(time, safeX1, safeX2);
                if (Math.abs(derivative) < 0.0001) break;
                time = Math.min(1, Math.max(0, time - difference / derivative));
            }
            return cubicCoordinate(time, y1, y2);
        };
    };

    const resolveEasing = easing => {
        if (typeof easing === 'function') return easing;
        if (typeof easing !== 'string') {
            return createCubicBezier(easing[0], easing[1], easing[2], easing[3]);
        }
        const preset = EASING_CURVES[easing];
        if (preset) return createCubicBezier(preset[0], preset[1], preset[2], preset[3]);
        const match = easing.match(
            /^cubic-bezier\(\s*(-?\d*\.?\d+)\s*,\s*(-?\d*\.?\d+)\s*,\s*(-?\d*\.?\d+)\s*,\s*(-?\d*\.?\d+)\s*\)$/
        );
        if (!match) return progress => progress;
        return createCubicBezier(
            Number(match[1]), Number(match[2]), Number(match[3]), Number(match[4])
        );
    };

    const normalize = options => {
        const source = Object.assign({}, options || {});
        const colors = Array.isArray(source.colors) && source.colors.length === 2
            ? [String(source.colors[0]), String(source.colors[1])]
            : DEFAULT_COLORS.slice();
        return {
            cellSize: num(source.cellSize, 5),
            gap: num(source.gap, 2),
            bandHeight: num(source.bandHeight, 48),
            duration: num(source.duration, 4000),
            effect: source.effect || 'shimmer',
            waveAmplitude: num(source.waveAmplitude, 12),
            scaleAmplitude: num(source.scaleAmplitude, 0.75),
            colors,
            text: source.text === undefined ? undefined : String(source.text),
            textLetterSpacing: source.textLetterSpacing,
            textWordSpacing: source.textWordSpacing,
            overlayOpacity: num(source.overlayOpacity, 0.3),
            overlayExitDuration: num(source.overlayExitDuration, 700),
            easing: source.easing === undefined ? 'ease-in-out' : source.easing
        };
    };

    function create(parent, options) {
        if (!parent) return null;

        const settings = normalize(options);
        const [fromColor, toColor] = settings.colors;

        const overlay = document.createElement('div');
        overlay.className = 'image-generation-loader__overlay';
        overlay.setAttribute('aria-hidden', 'true');
        overlay.style.setProperty('--loader-overlay-color', toColor);
        overlay.style.clipPath = 'inset(0 0 100% 0)';
        overlay.style.opacity = String(settings.overlayOpacity);

        const canvas = document.createElement('canvas');
        canvas.className = 'image-generation-loader__canvas';
        canvas.setAttribute('aria-hidden', 'true');

        parent.appendChild(overlay);
        parent.appendChild(canvas);

        const ctx = canvas.getContext('2d', { alpha: true });
        if (!ctx) {
            overlay.remove();
            canvas.remove();
            return null;
        }

        const colorProbe = document.createElement('span');
        colorProbe.hidden = true;
        parent.appendChild(colorProbe);

        const colorCanvas = document.createElement('canvas');
        colorCanvas.width = 1;
        colorCanvas.height = 1;
        const colorContext = colorCanvas.getContext('2d', { willReadFrequently: true });

        const decodeColor = color => {
            colorProbe.style.color = color;
            const resolvedColor = window.getComputedStyle(colorProbe).color;
            if (colorContext) {
                colorContext.clearRect(0, 0, 1, 1);
                colorContext.fillStyle = resolvedColor;
                colorContext.fillRect(0, 0, 1, 1);
            }
            const pixel = colorContext ? colorContext.getImageData(0, 0, 1, 1).data : null;
            return [pixel ? pixel[0] : 0, pixel ? pixel[1] : 0, pixel ? pixel[2] : 0];
        };

        const fromRgb = decodeColor(fromColor);
        const toRgb = decodeColor(toColor);
        colorProbe.remove();

        const rgba = (color, alpha) => `rgba(${color[0]}, ${color[1]}, ${color[2]}, ${alpha})`;

        let width = 0;
        let height = 0;
        let cells = [];
        let frameId = 0;
        let startTime = performance.now();
        let isVisible = true;
        const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        const pitch = Math.max(2, settings.cellSize + settings.gap);
        const easingFunction = resolveEasing(settings.easing);

        const buildCells = () => {
            const columnCount = Math.ceil(width / pitch) + 1;
            const rowCount = Math.max(1, Math.floor((settings.bandHeight + settings.gap) / pitch));
            const nextCells = [];
            const textCells = new Set();

            if (settings.text && rowCount >= GLYPH_HEIGHT) {
                const characters = Array.from(settings.text.trim().toUpperCase());
                const letterGapColumns = settings.textLetterSpacing === undefined
                    ? 1
                    : Math.max(0, Math.round(num(settings.textLetterSpacing, 0) / pitch));
                const wordGapColumns = settings.textWordSpacing === undefined
                    ? 3
                    : Math.max(1, Math.round(num(settings.textWordSpacing, 0) / pitch));
                const characterWidths = characters.map(character => character === ' ' ? wordGapColumns : GLYPH_WIDTH);
                const textWidth = characterWidths.reduce((total, value) => total + value, 0) +
                    Math.max(0, characters.length - 1) * letterGapColumns;
                const visibleColumnCount = Math.max(1, Math.floor((width + settings.gap) / pitch));
                const startColumn = Math.max(0, Math.floor((visibleColumnCount - textWidth) / 2));
                const startRow = Math.floor((rowCount - GLYPH_HEIGHT) / 2);
                let glyphColumn = startColumn;

                characters.forEach((character, characterIndex) => {
                    if (character === ' ') {
                        glyphColumn += wordGapColumns;
                    } else {
                        const glyph = (PIXEL_FONT[character] || PIXEL_FONT['?']).split('/');
                        for (let glyphRow = 0; glyphRow < GLYPH_HEIGHT; glyphRow++) {
                            for (let glyphPixel = 0; glyphPixel < GLYPH_WIDTH; glyphPixel++) {
                                if (glyph[glyphRow] && glyph[glyphRow][glyphPixel] === '1') {
                                    textCells.add(`${glyphColumn + glyphPixel}:${startRow + glyphRow}`);
                                }
                            }
                        }
                        glyphColumn += GLYPH_WIDTH;
                    }
                    if (characterIndex < characters.length - 1) glyphColumn += letterGapColumns;
                });
            }

            for (let row = 0; row < rowCount; row++) {
                for (let column = 0; column < columnCount; column++) {
                    nextCells.push({
                        column,
                        row,
                        opacity: 0.45 + randomFrom(column, row, 4) * 0.55,
                        phase: randomFrom(column, row, 5) * TAU,
                        scaleSeed: randomFrom(column, row, 6),
                        isText: textCells.has(`${column}:${row}`)
                    });
                }
            }
            cells = nextCells;
        };

        const resize = () => {
            const bounds = parent.getBoundingClientRect();
            width = Math.max(1, bounds.width);
            height = Math.max(1, bounds.height);
            const dpr = Math.min(window.devicePixelRatio || 1, 2);
            canvas.width = Math.round(width * dpr);
            canvas.height = Math.round(height * dpr);
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            buildCells();
        };

        const draw = now => {
            ctx.clearRect(0, 0, width, height);

            const cycleDuration = Math.max(1, settings.duration);
            const cycleElapsed = (now - startTime) % cycleDuration;
            const linearProgress = cycleElapsed / cycleDuration;
            const progress = reducedMotion.matches ? 0.5 : easingFunction(linearProgress);
            const centerY = -settings.bandHeight + progress * (height + settings.bandHeight * 2);
            const bandTop = Math.round(centerY - settings.bandHeight / 2);
            const bandCenter = bandTop + settings.bandHeight / 2;
            const revealEdge = Math.max(0, Math.min(height, bandTop));
            const exitWindow = Math.min(Math.max(1, settings.overlayExitDuration), cycleDuration / 2);
            const exitAmount = reducedMotion.matches
                ? 1
                : Math.min(1, (cycleDuration - cycleElapsed) / exitWindow);
            const easedExit = exitAmount * exitAmount * (3 - 2 * exitAmount);
            overlay.style.clipPath = `inset(0 0 ${height - revealEdge}px 0)`;
            overlay.style.opacity = `${settings.overlayOpacity * easedExit}`;

            const rowCount = Math.max(1, Math.floor((settings.bandHeight + settings.gap) / pitch));
            const gridHeight = rowCount * settings.cellSize + (rowCount - 1) * settings.gap;
            const gridTop = bandTop + Math.round((settings.bandHeight - gridHeight) / 2);
            const waveProgress = reducedMotion.matches ? 0.5 : ((now - startTime) % 1800) / 1800;
            const waveX = -100 + waveProgress * (width + 200);
            const getBulge = x => {
                if (settings.effect !== 'wave' || reducedMotion.matches) return 0;
                const distance = x - waveX;
                return settings.waveAmplitude * Math.exp(-(distance * distance) / (2 * 72 * 72));
            };

            const backgroundGradient = ctx.createLinearGradient(
                0, bandTop - settings.waveAmplitude,
                0, bandTop + settings.bandHeight + settings.waveAmplitude
            );
            backgroundGradient.addColorStop(0, rgba(toRgb, 0.03));
            backgroundGradient.addColorStop(0.18, rgba(toRgb, 0.12));
            backgroundGradient.addColorStop(0.5, rgba(fromRgb, 0.2));
            backgroundGradient.addColorStop(0.82, rgba(toRgb, 0.12));
            backgroundGradient.addColorStop(1, rgba(toRgb, 0.03));
            ctx.fillStyle = backgroundGradient;

            if (settings.effect === 'wave' && !reducedMotion.matches) {
                ctx.beginPath();
                ctx.moveTo(0, bandTop - getBulge(0));
                for (let x = 4; x <= width; x += 4) ctx.lineTo(x, bandTop - getBulge(x));
                for (let x = width; x >= 0; x -= 4) ctx.lineTo(x, bandTop + settings.bandHeight + getBulge(x));
                ctx.closePath();
                ctx.fill();
            } else {
                ctx.fillRect(0, bandTop, width, settings.bandHeight);
            }

            if (settings.effect === 'shimmer') {
                const shineProgress = reducedMotion.matches ? 0.5 : ((now - startTime) % 1400) / 1400;
                const shineX = -120 + shineProgress * (width + 240);
                const shineGradient = ctx.createLinearGradient(shineX - 120, 0, shineX + 120, 0);
                shineGradient.addColorStop(0, rgba(fromRgb, 0));
                shineGradient.addColorStop(0.5, rgba(fromRgb, 0.18));
                shineGradient.addColorStop(1, rgba(fromRgb, 0));
                ctx.fillStyle = shineGradient;
                ctx.fillRect(0, bandTop, width, settings.bandHeight);
            }

            for (const cell of cells) {
                const x = cell.column * pitch;
                const baseY = gridTop + cell.row * pitch;
                const distanceFromCenter = baseY + settings.cellSize / 2 - bandCenter;
                const stretch = 1 + getBulge(x + settings.cellSize / 2) / (settings.bandHeight / 2);
                const y = bandCenter + distanceFromCenter * stretch - settings.cellSize / 2;
                if (y + settings.cellSize < 0 || y > height) continue;

                const animatedColorMix = (Math.sin(now * 0.0022 + cell.phase) + 1) / 2;
                const colorMix = settings.text
                    ? (cell.isText ? 0.82 + animatedColorMix * 0.18 : animatedColorMix * 0.35)
                    : animatedColorMix;
                const red = Math.round(fromRgb[0] + (toRgb[0] - fromRgb[0]) * colorMix);
                const green = Math.round(fromRgb[1] + (toRgb[1] - fromRgb[1]) * colorMix);
                const blue = Math.round(fromRgb[2] + (toRgb[2] - fromRgb[2]) * colorMix);
                const pulse = 0.16 + ((Math.sin(now * 0.0045 + cell.phase) + 1) / 2) * 0.84;
                const cellCenterX = x + settings.cellSize / 2;
                let renderedSize = settings.cellSize;

                if (settings.effect === 'scale-wave' && !reducedMotion.matches && cell.scaleSeed > 0.42) {
                    const rowStagger = cell.row * 9;
                    const distanceFromScaleWave = cellCenterX - (waveX - rowStagger);
                    const scaleWaveInfluence = Math.exp(
                        -(distanceFromScaleWave * distanceFromScaleWave) / (2 * 52 * 52)
                    );
                    const randomStrength = (cell.scaleSeed - 0.42) / 0.58;
                    renderedSize = settings.cellSize * (1 + settings.scaleAmplitude * scaleWaveInfluence *
                        (0.35 + randomStrength * 0.65));
                }

                const cellCenterY = y + settings.cellSize / 2;

                if (settings.text && cell.isText) {
                    ctx.globalAlpha = 0.76 + pulse * 0.24;
                    ctx.fillStyle = `rgb(${fromRgb[0]} ${fromRgb[1]} ${fromRgb[2]})`;
                    ctx.fillRect(cellCenterX - renderedSize / 2, cellCenterY - renderedSize / 2, renderedSize, renderedSize);
                    const innerSize = Math.max(1, renderedSize * 0.55);
                    ctx.globalAlpha = 0.84 + pulse * 0.16;
                    ctx.fillStyle = `rgb(${toRgb[0]} ${toRgb[1]} ${toRgb[2]})`;
                    ctx.fillRect(cellCenterX - innerSize / 2, cellCenterY - innerSize / 2, innerSize, innerSize);
                } else {
                    ctx.globalAlpha = settings.text
                        ? pulse * (0.32 + cell.opacity * 0.3)
                        : pulse * (0.7 + cell.opacity * 0.3);
                    ctx.fillStyle = `rgb(${red} ${green} ${blue})`;
                    ctx.fillRect(cellCenterX - renderedSize / 2, cellCenterY - renderedSize / 2, renderedSize, renderedSize);
                }
            }

            ctx.globalAlpha = 1;
            if (!reducedMotion.matches && isVisible) frameId = requestAnimationFrame(draw);
        };

        const start = () => {
            parent.classList.remove('hidden');
            isVisible = true;
            cancelAnimationFrame(frameId);
            startTime = performance.now();
            if (reducedMotion.matches) draw(startTime);
            else frameId = requestAnimationFrame(draw);
        };

        const stop = () => {
            cancelAnimationFrame(frameId);
            frameId = 0;
            const hide = () => {
                ctx.clearRect(0, 0, width, height);
                overlay.style.opacity = '0';
                parent.classList.add('hidden');
            };
            // Keep the loader visible briefly so fast responses still show it.
            const elapsed = performance.now() - startTime;
            if (elapsed < 600) setTimeout(hide, 600 - elapsed);
            else hide();
        };

        const resizeObserver = new ResizeObserver(() => {
            resize();
            if (reducedMotion.matches && !parent.classList.contains('hidden')) draw(performance.now());
        });
        const intersectionObserver = new IntersectionObserver(entries => {
            const entry = entries[0];
            isVisible = entry ? entry.isIntersecting : false;
            if (isVisible && !parent.classList.contains('hidden')) start();
            else cancelAnimationFrame(frameId);
        });
        const handleMotionPreference = () => {
            if (!parent.classList.contains('hidden')) start();
        };

        resize();
        resizeObserver.observe(parent);
        intersectionObserver.observe(canvas);
        reducedMotion.addEventListener('change', handleMotionPreference);

        return {
            start,
            stop,
            destroy: () => {
                cancelAnimationFrame(frameId);
                resizeObserver.disconnect();
                intersectionObserver.disconnect();
                reducedMotion.removeEventListener('change', handleMotionPreference);
                overlay.remove();
                canvas.remove();
            }
        };
    }

    function mount(element, options) {
        return create(element, options);
    }

    window.ImageGenerationLoader = { create, mount };

    const bootstrap = () => {
        const host = document.getElementById('image-generation-loader-host');
        if (!host) return;
        window.imageGenerationLoader = create(host, {
            effect: 'scale-wave',
            easing: 'ease-in-out',
            text: 'Analysing',
            cellSize: 3,
            gap: 1,
            bandHeight: 48,
            colors: ['var(--color-blue-500)', 'var(--color-blue-800)']
        });
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootstrap, { once: true });
    } else {
        bootstrap();
    }
})();
