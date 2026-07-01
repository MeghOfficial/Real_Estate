/* ============================================================
   ESTATIFY — Shared Animation Utilities
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ---------- Intersection Observer for scroll animations ---------- */
  const observerOptions = {
    root: null,
    rootMargin: '0px 0px -60px 0px',
    threshold: 0.1,
  };

  const animObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        animObserver.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.fade-in, .slide-up, .scale-in').forEach((el) => {
    animObserver.observe(el);
  });

  /* ---------- Staggered children animation ---------- */
  document.querySelectorAll('[data-stagger]').forEach((parent) => {
    const children = parent.children;
    const delay = parseInt(parent.dataset.stagger, 10) || 100;
    Array.from(children).forEach((child, i) => {
      child.style.transitionDelay = `${i * delay}ms`;
    });
  });

  /* ---------- Animated counters ---------- */
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('[data-counter]').forEach((el) => {
    counterObserver.observe(el);
  });

  function animateCounter(el) {
    const target = parseFloat(el.dataset.counter);
    const suffix = el.dataset.counterSuffix || '';
    const prefix = el.dataset.counterPrefix || '';
    const decimals = parseInt(el.dataset.counterDecimals, 10) || 0;
    const duration = parseInt(el.dataset.counterDuration, 10) || 2000;
    const start = 0;
    const startTime = performance.now();

    function easeOutExpo(t) {
      return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
    }

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easeOutExpo(progress);
      const current = start + (target - start) * easedProgress;

      el.textContent = prefix + current.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + suffix;

      if (progress < 1) {
        requestAnimationFrame(update);
      }
    }

    requestAnimationFrame(update);
  }

  /* ---------- Smooth scroll for anchor links ---------- */
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (e) => {
      const href = anchor.getAttribute('href');
      if (href === '#') return;
      e.preventDefault();
      const target = document.querySelector(href);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  /* ---------- Navbar scroll effect ---------- */
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    let lastScroll = 0;
    window.addEventListener('scroll', () => {
      const currentScroll = window.pageYOffset;
      if (currentScroll > 50) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
      lastScroll = currentScroll;
    }, { passive: true });
  }

  /* ---------- Theme Toggle ---------- */
  const themeToggle = document.querySelector('.theme-toggle');
  if (themeToggle) {
    const savedTheme = localStorage.getItem('estatify-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    themeToggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('estatify-theme', next);
    });
  }

  /* ---------- Mobile Menu ---------- */
  const hamburger = document.querySelector('.nav-hamburger');
  const mobileOverlay = document.querySelector('.nav-mobile-overlay');
  const mobileDrawer = document.querySelector('.nav-mobile-drawer');
  const mobileClose = document.querySelector('.nav-mobile-close');

  function openMobileMenu() {
    if (mobileOverlay) mobileOverlay.classList.add('active');
    if (mobileDrawer) mobileDrawer.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeMobileMenu() {
    if (mobileOverlay) mobileOverlay.classList.remove('active');
    if (mobileDrawer) mobileDrawer.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (hamburger) hamburger.addEventListener('click', openMobileMenu);
  if (mobileClose) mobileClose.addEventListener('click', closeMobileMenu);
  if (mobileOverlay) mobileOverlay.addEventListener('click', closeMobileMenu);

  /* ---------- Parallax effect ---------- */
  const heroSection = document.querySelector('.hero-section');
  if (heroSection) {
    window.addEventListener('scroll', () => {
      const scrolled = window.pageYOffset;
      const parallaxElements = heroSection.querySelectorAll('.parallax');
      parallaxElements.forEach((el) => {
        const speed = parseFloat(el.dataset.parallaxSpeed) || 0.3;
        el.style.transform = `translateY(${scrolled * speed}px)`;
      });
    }, { passive: true });
  }

  /* ---------- Typed text effect (for hero) ---------- */
  document.querySelectorAll('[data-typed]').forEach((el) => {
    const words = JSON.parse(el.dataset.typed);
    let wordIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    let isPausing = false;

    function type() {
      const currentWord = words[wordIndex];

      if (isPausing) {
        isPausing = false;
        isDeleting = true;
        setTimeout(type, 800);
        return;
      }

      if (!isDeleting) {
        el.textContent = currentWord.substring(0, charIndex + 1);
        charIndex++;
        if (charIndex === currentWord.length) {
          isPausing = true;
          setTimeout(type, 2000);
          return;
        }
      } else {
        el.textContent = currentWord.substring(0, charIndex - 1);
        charIndex--;
        if (charIndex === 0) {
          isDeleting = false;
          wordIndex = (wordIndex + 1) % words.length;
        }
      }

      setTimeout(type, isDeleting ? 50 : 100);
    }

    type();
  });
});
