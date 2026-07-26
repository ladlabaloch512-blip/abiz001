/**
 * Main JavaScript File
 * Handles animations, mobile nav, canvas ripple, and UI interactions.
 */

document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Global Loader ---
    const loader = document.getElementById('global-loader');
    if (loader) {
        setTimeout(() => {
            loader.classList.add('fade-out');
            setTimeout(() => {
                loader.style.display = 'none';
            }, 500);
        }, 300); // Fast load simulation
    }

    // --- 2. Header Scroll Effect ---
    const header = document.getElementById('site-header');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });

    // --- 3. Mobile Navigation ---
    const mobileBtn = document.getElementById('mobile-menu-btn');
    const navMenu = document.getElementById('nav-menu');

    if (mobileBtn && navMenu) {
        mobileBtn.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            if(navMenu.classList.contains('active')) {
                mobileBtn.textContent = '✕';
            } else {
                mobileBtn.textContent = '☰';
            }
        });
    }

    // --- 4. Scroll Reveal Animations ---
    const reveals = document.querySelectorAll('.reveal');

    const revealOnScroll = () => {
        const windowHeight = window.innerHeight;
        const elementVisible = 100; // Trigger point

        reveals.forEach(reveal => {
            const elementTop = reveal.getBoundingClientRect().top;
            if (elementTop < windowHeight - elementVisible) {
                reveal.classList.add('active');
            }
        });
    };

    window.addEventListener('scroll', revealOnScroll);
    revealOnScroll(); // Trigger on load

    // --- 5. Testimonial Slider ---
    const track = document.getElementById('testimonial-track');
    const dots = document.querySelectorAll('.slider-dot');

    if (track && dots.length > 0) {
        dots.forEach(dot => {
            dot.addEventListener('click', (e) => {
                const slideIndex = parseInt(e.target.getAttribute('data-slide'));

                // Update track position
                track.style.transform = `translateX(-${slideIndex * 100}%)`;

                // Update dots
                dots.forEach(d => d.style.opacity = '0.3');
                e.target.style.opacity = '1';
            });
        });

        // Auto-play (optional, simple implementation)
        let currentSlide = 0;
        setInterval(() => {
            currentSlide = (currentSlide + 1) % dots.length;
            dots[currentSlide].click();
        }, 8000);
    }

    // --- 6. FAQ Accordion ---
    const accordions = document.querySelectorAll('.accordion-header');

    accordions.forEach(acc => {
        acc.addEventListener('click', function() {
            // Close all others
            accordions.forEach(otherAcc => {
                if (otherAcc !== this) {
                    otherAcc.classList.remove('active');
                    otherAcc.setAttribute('aria-expanded', 'false');
                    otherAcc.nextElementSibling.style.maxHeight = null;
                }
            });

            // Toggle current
            this.classList.toggle('active');
            const body = this.nextElementSibling;

            if (this.classList.contains('active')) {
                this.setAttribute('aria-expanded', 'true');
                body.style.maxHeight = body.scrollHeight + "px";
            } else {
                this.setAttribute('aria-expanded', 'false');
                body.style.maxHeight = null;
            }
        });
    });

    // --- 6. Hero Canvas Water Ripple Effect (Lightweight) ---
    const canvas = document.getElementById('water-ripple-canvas');
    const wrapper = document.getElementById('hero-canvas-wrapper');

    if (canvas && wrapper && window.innerWidth > 768) {
        // Only initialize on desktop to save mobile battery/performance
        const ctx = canvas.getContext('2d');
        let width, height;
        let drops = [];

        const resizeCanvas = () => {
            width = canvas.width = wrapper.offsetWidth;
            height = canvas.height = wrapper.offsetHeight;
        };

        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();

        class Ripple {
            constructor(x, y) {
                this.x = x;
                this.y = y;
                this.radius = 1;
                this.maxRadius = Math.random() * 100 + 100; // Max size
                this.speed = Math.random() * 2 + 1;
                this.opacity = 0.5;
            }

            update() {
                this.radius += this.speed;
                this.opacity -= 0.5 / (this.maxRadius / this.speed); // Fade out relative to growth
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.strokeStyle = `rgba(0, 180, 216, ${this.opacity})`;
                ctx.lineWidth = 2;
                ctx.stroke();
            }
        }

        const createDrop = (e) => {
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            drops.push(new Ripple(x, y));
        };

        canvas.addEventListener('mousemove', (e) => {
            // Throttling ripple creation
            if (Math.random() > 0.8) {
                createDrop(e);
            }
        });

        const animate = () => {
            ctx.clearRect(0, 0, width, height);

            for (let i = 0; i < drops.length; i++) {
                drops[i].update();
                drops[i].draw();

                if (drops[i].opacity <= 0) {
                    drops.splice(i, 1);
                    i--;
                }
            }
            requestAnimationFrame(animate);
        };

        animate();
    }
});