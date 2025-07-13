/**
 * Kobuy Application - Main JavaScript
 * Modern, modular, and accessible JavaScript for the user interface
 */

(function () {
  "use strict";

  // Global state management
  const AppState = {
    navigation: {
      isNarrow: false,
      isMobile: false,
    },
    user: {
      isAuthenticated: false,
    },
    ui: {
      theme: "light",
      language: "ja",
    },
  };

  // Utility functions
  const Utils = {
    // Debounce function for performance
    debounce: function (func, wait) {
      let timeout;
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    },

    // Throttle function for scroll events
    throttle: function (func, limit) {
      let inThrottle;
      return function () {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
          func.apply(context, args);
          inThrottle = true;
          setTimeout(() => (inThrottle = false), limit);
        }
      };
    },

    // Safe DOM query selector
    safeQuerySelector: function (selector, parent = document) {
      try {
        return parent.querySelector(selector);
      } catch (error) {
        console.warn("Invalid selector:", selector);
        return null;
      }
    },

    // Safe DOM query selector all
    safeQuerySelectorAll: function (selector, parent = document) {
      try {
        return parent.querySelectorAll(selector);
      } catch (error) {
        console.warn("Invalid selector:", selector);
        return [];
      }
    },

    // Add event listener with error handling
    addEventListener: function (element, event, handler, options = {}) {
      if (element && typeof element.addEventListener === "function") {
        element.addEventListener(event, handler, options);
      } else {
        console.warn("Invalid element for event listener:", element);
      }
    },

    // Remove event listener with error handling
    removeEventListener: function (element, event, handler, options = {}) {
      if (element && typeof element.removeEventListener === "function") {
        element.removeEventListener(event, handler, options);
      }
    },
  };

  // Navigation Management
  const Navigation = {
    init: function () {
      this.elements = {
        navigation: Utils.safeQuerySelector("#appNavigation"),
        mobileToggle: Utils.safeQuerySelector("#mobileMenuToggle"),
        main: Utils.safeQuerySelector("#main-content"),
        navToggle: Utils.safeQuerySelector("#navToggle"),
        footer: Utils.safeQuerySelector(".app-footer"),
      };

      this.state = {
        isNarrow: false,
        isMobile: window.innerWidth <= 768,
        preventAnimation: false,
      };

      this.loadState();
      this.bindEvents();
      this.handleResponsive();
      this.adjustFooterSize();
    },

    bindEvents: function () {
      if (this.elements.navToggle) {
        this.elements.navToggle.addEventListener(
          "click",
          this.toggleNavigation.bind(this)
        );
      }

      if (this.elements.mobileToggle) {
        this.elements.mobileToggle.addEventListener(
          "click",
          this.toggleMobileNavigation.bind(this)
        );
      }

      document.addEventListener("click", this.handleOutsideClick.bind(this));
      document.addEventListener("keydown", this.handleKeydown.bind(this));
      window.addEventListener("resize", this.handleResize.bind(this));
    },

    toggleNavigation: function () {
      if (this.state.preventAnimation) return;

      this.state.isNarrow = !this.state.isNarrow;

      if (this.elements.navigation) {
        this.elements.navigation.classList.toggle(
          "navi-narrow",
          this.state.isNarrow
        );
      }

      if (this.elements.main) {
        this.elements.main.classList.toggle("main-s", this.state.isNarrow);
        this.elements.main.style.marginLeft = this.state.isNarrow
          ? "80px"
          : "280px";
      }

      this.adjustFooterSize();
      this.saveState();
    },

    toggleMobileNavigation: function () {
      if (this.state.preventAnimation) return;

      if (this.elements.navigation) {
        this.elements.navigation.classList.toggle("show");
      }

      this.adjustFooterSize();
    },

    adjustFooterSize: function () {
      if (!this.elements.footer) return;

      const isNarrow =
        this.elements.navigation &&
        this.elements.navigation.classList.contains("navi-narrow");
      const isMobile = window.innerWidth <= 768;

      if (isMobile) {
        // モバイルではフッターサイズを固定
        this.elements.footer.style.marginLeft = "0";
        this.elements.footer.style.width = "100%";
      } else {
        // デスクトップではナビゲーションの幅に応じて調整
        const navWidth = isNarrow ? 80 : 280;
        this.elements.footer.style.marginLeft = navWidth + "px";
        this.elements.footer.style.width = `calc(100% - ${navWidth}px)`;
      }
    },

    handleOutsideClick: function (event) {
      if (!this.elements.navigation || !this.elements.mobileToggle) return;

      const isClickInsideNav = this.elements.navigation.contains(event.target);
      const isClickOnToggle =
        this.elements.navToggle &&
        this.elements.navToggle.contains(event.target);

      if (
        !isClickInsideNav &&
        !isClickOnToggle &&
        this.elements.navigation.classList.contains("show")
      ) {
        this.elements.navigation.classList.remove("show");
        this.adjustFooterSize();
      }
    },

    handleKeydown: function (event) {
      if (event.key === "Escape") {
        if (
          this.elements.navigation &&
          this.elements.navigation.classList.contains("show")
        ) {
          this.elements.navigation.classList.remove("show");
          this.adjustFooterSize();
        }
      }
    },

    handleResize: function () {
      this.handleResponsive();
      this.adjustFooterSize();
    },

    handleResponsive: function () {
      const isMobile = window.innerWidth <= 768;
      this.state.isMobile = isMobile;

      if (isMobile) {
        // Hide desktop navigation on mobile
        if (this.elements.navigation) {
          this.elements.navigation.classList.remove("navi-narrow", "show");
        }
        if (this.elements.main) {
          this.elements.main.classList.remove("main-s");
          this.elements.main.style.marginLeft = "0";
        }
      } else {
        // Restore desktop navigation state
        if (this.elements.navigation) {
          this.elements.navigation.classList.remove("show");
        }
        this.restoreState();
      }

      this.adjustFooterSize();
    },

    loadState: function () {
      try {
        const savedState = localStorage.getItem("kobuy_navigation_state");
        if (savedState) {
          const state = JSON.parse(savedState);
          this.state.isNarrow = state.isNarrow || false;
          this.state.isMobile = state.isMobile || window.innerWidth <= 768;
        }
      } catch (error) {
        console.warn("Failed to load navigation state:", error);
      }

      this.restoreState();
    },

    restoreState: function () {
      if (this.elements.navigation) {
        this.elements.navigation.classList.toggle(
          "navi-narrow",
          this.state.isNarrow
        );
      }

      if (this.elements.main) {
        this.elements.main.classList.toggle("main-s", this.state.isNarrow);
        this.elements.main.style.marginLeft = this.state.isNarrow
          ? "80px"
          : "280px";
      }

      this.adjustFooterSize();
    },

    saveState: function () {
      try {
        localStorage.setItem(
          "kobuy_navigation_state",
          JSON.stringify({
            isNarrow: this.state.isNarrow,
            isMobile: this.state.isMobile,
          })
        );
      } catch (error) {
        console.warn("Failed to save navigation state:", error);
      }
    },

    updateActiveState: function () {
      const currentPath = window.location.pathname;
      const navLinks = Utils.safeQuerySelectorAll(".nav-link");

      navLinks.forEach((link) => {
        const href = link.getAttribute("href");
        if (href && currentPath === href) {
          link.classList.add("active");
        } else {
          link.classList.remove("active");
        }
      });
    },
  };

  // Flash messages management
  const FlashMessages = {
    elements: {
      container: null,
    },

    init: function () {
      this.elements.container = Utils.safeQuerySelector("#flashMessages");
      if (this.elements.container) {
        this.bindEvents();
        this.autoHide();
      }
    },

    bindEvents: function () {
      const closeButtons = Utils.safeQuerySelectorAll(
        ".alert-close",
        this.elements.container
      );
      closeButtons.forEach((button) => {
        Utils.addEventListener(button, "click", this.closeAlert.bind(this));
      });
    },

    closeAlert: function (event) {
      const alert = event.target.closest(".alert");
      if (alert) {
        alert.style.animation = "slideOutRight 0.3s ease-out";
        setTimeout(() => {
          alert.remove();
        }, 300);
      }
    },

    autoHide: function () {
      const alerts = Utils.safeQuerySelectorAll(
        ".alert",
        this.elements.container
      );
      alerts.forEach((alert) => {
        setTimeout(() => {
          if (alert.parentNode) {
            this.closeAlert({
              target: alert.querySelector(".alert-close") || alert,
            });
          }
        }, 5000);
      });
    },

    show: function (message, type = "info", duration = 5000) {
      if (!this.elements.container) return;

      const alert = document.createElement("div");
      alert.className = `alert alert-${type}`;
      alert.setAttribute("role", "alert");

      const icon = this.getIconForType(type);
      const closeButton = `
        <button type="button" class="alert-close" aria-label="アラートを閉じる">
          <span class="material-icons">close</span>
        </button>
      `;

      alert.innerHTML = `
        <span class="material-icons">${icon}</span>
        <span class="alert-text">${message}</span>
        ${closeButton}
      `;

      this.elements.container.appendChild(alert);
      Utils.addEventListener(
        alert.querySelector(".alert-close"),
        "click",
        this.closeAlert.bind(this)
      );

      if (duration > 0) {
        setTimeout(() => {
          if (alert.parentNode) {
            this.closeAlert({ target: alert.querySelector(".alert-close") });
          }
        }, duration);
      }
    },

    getIconForType: function (type) {
      const icons = {
        success: "check_circle",
        error: "error",
        warning: "warning",
        info: "info",
      };
      return icons[type] || "info";
    },
  };

  // User menu management
  const UserMenu = {
    elements: {
      anchor: null,
      menu: null,
    },

    init: function () {
      this.elements.anchor = Utils.safeQuerySelector("#user-menu-anchor");
      this.elements.menu = Utils.safeQuerySelector("#user-menu");

      if (this.elements.anchor && this.elements.menu) {
        this.bindEvents();
      }
    },

    bindEvents: function () {
      Utils.addEventListener(
        this.elements.anchor,
        "click",
        this.toggleMenu.bind(this)
      );

      // Close menu when clicking outside
      Utils.addEventListener(
        document,
        "click",
        this.handleOutsideClick.bind(this)
      );

      // Close menu on escape key
      Utils.addEventListener(
        document,
        "keydown",
        this.handleKeydown.bind(this)
      );
    },

    toggleMenu: function (event) {
      event.preventDefault();
      if (this.elements.menu) {
        this.elements.menu.open = !this.elements.menu.open;
      }
    },

    handleOutsideClick: function (event) {
      if (!this.elements.anchor || !this.elements.menu) return;

      const isClickInsideMenu = this.elements.menu.contains(event.target);
      const isClickOnAnchor = this.elements.anchor.contains(event.target);

      if (!isClickInsideMenu && !isClickOnAnchor && this.elements.menu.open) {
        this.elements.menu.open = false;
      }
    },

    handleKeydown: function (event) {
      if (
        event.key === "Escape" &&
        this.elements.menu &&
        this.elements.menu.open
      ) {
        this.elements.menu.open = false;
      }
    },
  };

  // Ajax utilities
  const Ajax = {
    // GET request
    get: function (url, options = {}) {
      return this.request(url, {
        method: "GET",
        ...options,
      });
    },

    // POST request
    post: function (url, data = {}, options = {}) {
      return this.request(url, {
        method: "POST",
        body: JSON.stringify(data),
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
        ...options,
      });
    },

    // PUT request
    put: function (url, data = {}, options = {}) {
      return this.request(url, {
        method: "PUT",
        body: JSON.stringify(data),
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
        ...options,
      });
    },

    // DELETE request
    delete: function (url, options = {}) {
      return this.request(url, {
        method: "DELETE",
        ...options,
      });
    },

    // Main request function
    request: function (url, options = {}) {
      const defaultOptions = {
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          Accept: "application/json",
        },
        credentials: "same-origin",
      };

      const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
          ...defaultOptions.headers,
          ...options.headers,
        },
      };

      return fetch(url, finalOptions)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response;
        })
        .then((response) => {
          const contentType = response.headers.get("content-type");
          if (contentType && contentType.includes("application/json")) {
            return response.json();
          }
          return response.text();
        })
        .catch((error) => {
          console.error("Ajax request failed:", error);
          throw error;
        });
    },
  };

  // Form handling
  const FormHandler = {
    init: function () {
      this.bindFormEvents();
    },

    bindFormEvents: function () {
      const ajaxForms = Utils.safeQuerySelectorAll('form[data-ajax="true"]');
      ajaxForms.forEach((form) => {
        Utils.addEventListener(
          form,
          "submit",
          this.handleAjaxSubmit.bind(this)
        );
      });
    },

    handleAjaxSubmit: function (event) {
      event.preventDefault();

      const form = event.target;
      const submitBtn = form.querySelector('button[type="submit"]');

      if (submitBtn) {
        this.setLoadingState(submitBtn, true);
      }

      const formData = new FormData(form);
      const data = {};
      formData.forEach((value, key) => {
        data[key] = value;
      });

      const url = form.action || window.location.href;
      const method = form.method.toUpperCase();

      const request =
        method === "GET"
          ? Ajax.get(url, { params: data })
          : Ajax.post(url, data);

      request
        .then((response) => {
          if (response.success) {
            FlashMessages.show(
              response.message || "操作が完了しました",
              "success"
            );
            if (response.redirect) {
              window.location.href = response.redirect;
            }
          } else {
            FlashMessages.show(
              response.message || "エラーが発生しました",
              "error"
            );
          }
        })
        .catch((error) => {
          console.error("Form submission failed:", error);
          FlashMessages.show("エラーが発生しました", "error");
        })
        .finally(() => {
          if (submitBtn) {
            this.setLoadingState(submitBtn, false);
          }
        });
    },

    setLoadingState: function (button, isLoading) {
      if (isLoading) {
        button.classList.add("loading");
        button.disabled = true;
        const originalText = button.innerHTML;
        button.setAttribute("data-original-text", originalText);
        button.innerHTML =
          '<span class="material-icons rotating">refresh</span> 処理中...';
      } else {
        button.classList.remove("loading");
        button.disabled = false;
        const originalText = button.getAttribute("data-original-text");
        if (originalText) {
          button.innerHTML = originalText;
        }
      }
    },
  };

  // Search functionality
  const Search = {
    elements: {
      searchInput: null,
      searchResults: null,
    },

    init: function () {
      this.elements.searchInput = Utils.safeQuerySelector("[data-search]");
      this.elements.searchResults = Utils.safeQuerySelector(
        "[data-search-results]"
      );

      if (this.elements.searchInput) {
        this.bindEvents();
      }
    },

    bindEvents: function () {
      Utils.addEventListener(
        this.elements.searchInput,
        "input",
        Utils.debounce(this.handleSearch.bind(this), 300)
      );
    },

    handleSearch: function (event) {
      const query = event.target.value.trim();

      if (query.length < 2) {
        this.clearResults();
        return;
      }

      this.performSearch(query);
    },

    performSearch: function (query) {
      // Implement search logic here
      console.log("Searching for:", query);
    },

    clearResults: function () {
      if (this.elements.searchResults) {
        this.elements.searchResults.innerHTML = "";
      }
    },
  };

  // Accessibility enhancements
  const Accessibility = {
    init: function () {
      this.handleSkipLinks();
      this.handleFocusManagement();
      this.handleKeyboardNavigation();
    },

    handleSkipLinks: function () {
      const skipLinks = Utils.safeQuerySelectorAll(".skip-link");
      skipLinks.forEach((link) => {
        Utils.addEventListener(link, "click", this.handleSkipLink.bind(this));
      });
    },

    handleSkipLink: function (event) {
      const targetId = event.target.getAttribute("href").substring(1);
      const target = document.getElementById(targetId);

      if (target) {
        event.preventDefault();
        target.focus();
        target.scrollIntoView({ behavior: "smooth" });
      }
    },

    handleFocusManagement: function () {
      // Trap focus in modals when they're open
      document.addEventListener("keydown", (event) => {
        if (event.key === "Tab") {
          const modals = Utils.safeQuerySelectorAll('[role="dialog"]');
          modals.forEach((modal) => {
            if (modal.style.display !== "none") {
              this.trapFocus(modal, event);
            }
          });
        }
      });
    },

    trapFocus: function (modal, event) {
      const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    },

    handleKeyboardNavigation: function () {
      // Add keyboard navigation for custom components
      document.addEventListener("keydown", (event) => {
        if (
          event.key === "Enter" &&
          document.activeElement.tagName === "BUTTON"
        ) {
          document.activeElement.click();
        }
      });
    },
  };

  // Performance monitoring
  const Performance = {
    init: function () {
      this.observeIntersections();
      this.observeMutations();
    },

    observeIntersections: function () {
      if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(
          (entries) => {
            entries.forEach((entry) => {
              if (entry.isIntersecting) {
                entry.target.classList.add("fade-in");
              }
            });
          },
          {
            threshold: 0.1,
            rootMargin: "0px 0px -50px 0px",
          }
        );

        const elements = Utils.safeQuerySelectorAll(
          ".card, .menu-item, .nav-item"
        );
        elements.forEach((el) => observer.observe(el));
      }
    },

    observeMutations: function () {
      if ("MutationObserver" in window) {
        const observer = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
            if (mutation.type === "childList") {
              mutation.addedNodes.forEach((node) => {
                if (node.nodeType === Node.ELEMENT_NODE) {
                  this.enhanceNewElements(node);
                }
              });
            }
          });
        });

        observer.observe(document.body, {
          childList: true,
          subtree: true,
        });
      }
    },

    enhanceNewElements: function (element) {
      // Add any necessary enhancements to newly added elements
      const buttons = Utils.safeQuerySelectorAll("button", element);
      buttons.forEach((button) => {
        if (!button.hasAttribute("data-enhanced")) {
          button.setAttribute("data-enhanced", "true");
          // Add any button enhancements here
        }
      });
    },
  };

  // Mobile Navigation Management
  const MobileNav = {
    init: function () {
      this.elements = {
        mobileNav: Utils.safeQuerySelector("#mobileBottomNav"),
      };

      if (this.elements.mobileNav) {
        this.showOnMobile();
        this.handleResize();
        this.bindMobileEvents();
      }
    },

    showOnMobile: function () {
      try {
        if (window.innerWidth <= 768) {
          this.elements.mobileNav.classList.add("show");
        } else {
          this.elements.mobileNav.classList.remove("show");
        }
      } catch (error) {
        console.warn("Mobile navigation error:", error);
      }
    },

    handleResize: function () {
      const debouncedResize = Utils.debounce(() => {
        this.showOnMobile();
      }, 250);

      window.addEventListener("resize", debouncedResize);
    },

    bindMobileEvents: function () {
      // モバイルナビゲーションのアイテムにイベントを追加
      const mobileNavItems = Utils.safeQuerySelectorAll(".mobile-nav-item");
      mobileNavItems.forEach((item) => {
        Utils.addEventListener(item, "click", (event) => {
          // タッチデバイスでのタップ遅延を防ぐ
          event.preventDefault();
          const href = item.getAttribute("href");
          if (href) {
            window.location.href = href;
          }
        });
      });
    },
  };

  // Main application initialization
  const App = {
    init: function () {
      // Wait for DOM to be ready
      if (document.readyState === "loading") {
        Utils.addEventListener(
          document,
          "DOMContentLoaded",
          this.start.bind(this)
        );
      } else {
        this.start();
      }
    },

    start: function () {
      try {
        // Initialize all modules
        Navigation.init();
        FlashMessages.init();
        UserMenu.init();
        FormHandler.init();
        Search.init();
        Accessibility.init();
        Performance.init();
        MobileNav.init(); // Initialize MobileNav

        // Update navigation active state
        Navigation.updateActiveState();

        // Add global error handler
        this.handleGlobalErrors();

        console.log("Kobuy Application initialized successfully");
      } catch (error) {
        console.error("Failed to initialize application:", error);
      }
    },

    handleGlobalErrors: function () {
      window.addEventListener("error", (event) => {
        console.error("Global error:", event.error);
        console.error("Error details:", {
          message: event.message,
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
          error: event.error,
        });

        // モバイル特有のエラーをチェック
        if (event.message && event.message.includes("touch")) {
          console.warn("Touch event error detected");
        }

        FlashMessages.show("予期しないエラーが発生しました", "error");
      });

      window.addEventListener("unhandledrejection", (event) => {
        console.error("Unhandled promise rejection:", event.reason);
        FlashMessages.show("予期しないエラーが発生しました", "error");
      });

      // モバイル特有のエラーハンドリング
      if ("ontouchstart" in window) {
        // タッチデバイスでのエラーハンドリング
        document.addEventListener("touchstart", function () {}, {
          passive: true,
        });
        document.addEventListener("touchmove", function () {}, {
          passive: true,
        });
        document.addEventListener("touchend", function () {}, {
          passive: true,
        });
      }
    },
  };

  // Expose modules to global scope
  window.KobuyApp = {
    Navigation,
    FlashMessages,
    UserMenu,
    FormHandler,
    Search,
    Accessibility,
    Performance,
    Utils,
    MobileNav,
  };

  // Initialize the application
  App.init();
})();
