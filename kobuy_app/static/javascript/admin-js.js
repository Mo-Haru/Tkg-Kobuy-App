/**
 * Kobuy Admin Application - JavaScript
 * Modern, modular, and accessible JavaScript for the admin interface
 */

(function () {
  "use strict";

  // Global state management
  const AdminState = {
    navigation: {
      isNarrow: false,
      isMobile: false,
    },
    modals: {
      active: null,
    },
    user: {
      isAuthenticated: false,
    },
    currentPage: window.location.pathname,
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

    // Show loading indicator
    showLoading: function () {
      const loading = document.createElement("div");
      loading.id = "page-loading";
      loading.className = "page-loading";
      loading.innerHTML = `
        <div class="loading-spinner">
          <div class="spinner"></div>
          <p>読み込み中...</p>
        </div>
      `;
      document.body.appendChild(loading);
    },

    // Hide loading indicator
    hideLoading: function () {
      const loading = document.getElementById("page-loading");
      if (loading) {
        loading.remove();
      }
    },

    // Update browser history without page reload
    updateHistory: function (url, title = "") {
      if (window.history && window.history.pushState) {
        window.history.pushState({ url: url }, title, url);
      }
    },

    // Extract content from HTML response
    extractContent: function (html) {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      const content = doc.querySelector(".page-content");
      return content ? content.innerHTML : html;
    },
  };

  // Navigation Management
  const Navigation = {
    init: function () {
      this.elements = {
        navigation: Utils.safeQuerySelector("#adminNavigation"),
        mobileToggle: Utils.safeQuerySelector("#mobileMenuToggle"),
        main: Utils.safeQuerySelector("#main-content"),
        navToggle: Utils.safeQuerySelector("#navToggle"),
        footer: Utils.safeQuerySelector(".admin-footer"),
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

      // Only bind mobile toggle if it exists
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

      const icon = document.getElementById("navToggleIcon");
      const label = document.getElementById("navToggleLabel");
      const btn = document.getElementById("navToggle");
      if (btn) {
        btn.style.width = "";
        if (this.state.isNarrow) {
          if (icon) icon.textContent = "menu";
          if (label) label.style.display = "none";
          btn.classList.remove("open");
          btn.style.width = "48px";
        } else {
          if (icon) icon.textContent = "close";
          if (label) label.style.display = "inline";
          btn.classList.add("open");
          btn.style.width = "auto";
          const fullWidth = btn.scrollWidth + "px";
          btn.style.width = "48px";
          setTimeout(() => {
            btn.style.width = fullWidth;
          }, 10);
        }
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
      if (!this.elements.navigation) return;

      const isClickInsideNav = this.elements.navigation.contains(event.target);
      const isClickOnToggle =
        this.elements.navToggle &&
        this.elements.navToggle.contains(event.target);
      const isClickOnMobileToggle =
        this.elements.mobileToggle &&
        this.elements.mobileToggle.contains(event.target);

      if (
        !isClickInsideNav &&
        !isClickOnToggle &&
        !isClickOnMobileToggle &&
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
        const savedState = localStorage.getItem("kobuy_admin_navigation_state");
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
          "kobuy_admin_navigation_state",
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

  // Modal management
  const ModalManager = {
    elements: {
      modals: {},
    },

    init: function () {
      this.registerModals();
      this.bindEvents();
    },

    registerModals: function () {
      const modalIds = [
        "productDetailModal",
        "reservationDetailModal",
        "contactDetailModal",
      ];

      modalIds.forEach((id) => {
        const modal = Utils.safeQuerySelector(`#${id}`);
        if (modal) {
          this.elements.modals[id] = modal;
        }
      });
    },

    bindEvents: function () {
      // Close modal when clicking outside
      Utils.addEventListener(
        document,
        "click",
        this.handleOutsideClick.bind(this)
      );

      // Close modal with Escape key
      Utils.addEventListener(
        document,
        "keydown",
        this.handleKeydown.bind(this)
      );
    },

    show: function (modalId) {
      const modal = this.elements.modals[modalId];
      if (modal) {
        modal.classList.add("show");
        modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
        AdminState.modals.active = modalId;

        // Focus first focusable element
        const firstFocusable = modal.querySelector(
          'button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (firstFocusable) {
          firstFocusable.focus();
        }
      }
    },

    hide: function (modalId) {
      const modal = this.elements.modals[modalId];
      if (modal) {
        modal.classList.remove("show");
        modal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
        AdminState.modals.active = null;
      }
    },

    hideAll: function () {
      Object.keys(this.elements.modals).forEach((modalId) => {
        this.hide(modalId);
      });
    },

    handleOutsideClick: function (event) {
      Object.values(this.elements.modals).forEach((modal) => {
        if (modal.classList.contains("show") && !modal.contains(event.target)) {
          const modalId = modal.id;
          this.hide(modalId);
        }
      });
    },

    handleKeydown: function (event) {
      if (event.key === "Escape") {
        this.hideAll();
      }
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

  // Admin-specific functions
  const AdminFunctions = {
    // Product detail modal
    showProductDetail: function (productId) {
      Ajax.get(`/api/admin/product/${productId}`)
        .then((data) => {
          if (data.success) {
            const modal = Utils.safeQuerySelector("#productDetailModal");
            const content = modal.querySelector(".modal-body");

            content.innerHTML = this.buildProductDetailHTML(data);
            ModalManager.show("productDetailModal");
          } else {
            FlashMessages.show("商品情報の取得に失敗しました", "error");
          }
        })
        .catch((error) => {
          console.error("Error fetching product details:", error);
          FlashMessages.show("商品情報の取得に失敗しました", "error");
        });
    },

    buildProductDetailHTML: function (data) {
      const product = data.product;
      const stock = data.stock;

      return `
        <div class="product-detail">
          <div class="product-image-container">
            ${
              product.image
                ? `<img src="${product.image}" alt="${product.name}" class="product-image">`
                : `<div class="product-image-placeholder">
                  <span class="material-icons">restaurant</span>
                </div>`
            }
          </div>
          <div class="product-info">
            <h3>${product.name}</h3>
            <p><strong>価格:</strong> ¥${product.price}</p>
            <p><strong>説明:</strong> ${product.description || "説明なし"}</p>
            <p><strong>カテゴリー:</strong> ${product.category}</p>
            
            <div class="product-stats">
              <div class="stat-item">
                <div class="stat-value">${stock.current}</div>
                <div class="stat-label">現在の在庫</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">${stock.limit}</div>
                <div class="stat-label">在庫上限</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">${product.sales}</div>
                <div class="stat-label">販売数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">${product.order}</div>
                <div class="stat-label">表示順序</div>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    // Reservation detail modal
    showReservationDetail: function (reservationId) {
      Ajax.get(`/api/admin/reservation/${reservationId}`)
        .then((data) => {
          if (data.success) {
            const modal = Utils.safeQuerySelector("#reservationDetailModal");
            const content = modal.querySelector(".modal-body");

            content.innerHTML = this.buildReservationDetailHTML(data);
            ModalManager.show("reservationDetailModal");
          } else {
            FlashMessages.show("予約情報の取得に失敗しました", "error");
          }
        })
        .catch((error) => {
          console.error("Error fetching reservation details:", error);
          FlashMessages.show("予約情報の取得に失敗しました", "error");
        });
    },

    buildReservationDetailHTML: function (data) {
      const reservation = data.reservation;
      const user = data.user;

      const items = [];
      if (reservation.product_0) items.push(reservation.product_0);
      if (reservation.product_1) items.push(reservation.product_1);
      if (reservation.product_2) items.push(reservation.product_2);
      if (reservation.product_3) items.push(reservation.product_3);
      if (reservation.product_4) items.push(reservation.product_4);

      return `
        <div class="reservation-detail">
          <div class="reservation-header">
            <h3>予約 #${reservation.id}</h3>
            <p>${user.grade}年${user.cls}組${user.num}番 ${user.lastname}${
        user.firstname
      }</p>
            <p>予約日時: ${reservation.date} ${reservation.time}</p>
          </div>
          
          <div class="reservation-items">
            ${items
              .map(
                (item) => `
              <div class="reservation-item">
                <span>${item.name}</span>
                <span>¥${item.price}</span>
              </div>
            `
              )
              .join("")}
          </div>
          
          <div class="reservation-total">
            合計: ¥${reservation.total}
          </div>
          
          <div class="reservation-status">
            <span class="status-badge status-${reservation.status.toLowerCase()}">
              ${reservation.status}
            </span>
          </div>
        </div>
      `;
    },

    // Update reservation status
    updateReservationStatus: function (reservationId, status) {
      Ajax.post(`/api/admin/reservation/${reservationId}/status`, { status })
        .then((data) => {
          if (data.success) {
            FlashMessages.show("ステータスを更新しました", "success");
            setTimeout(() => {
              window.location.reload();
            }, 1000);
          } else {
            FlashMessages.show(
              data.message || "ステータスの更新に失敗しました",
              "error"
            );
          }
        })
        .catch((error) => {
          console.error("Error updating status:", error);
          FlashMessages.show("ステータスの更新に失敗しました", "error");
        });
    },

    // Update stock
    updateStock: function (productId, action) {
      Ajax.post(`/api/admin/stock/${productId}/${action}`)
        .then((data) => {
          if (data.success) {
            FlashMessages.show("在庫を更新しました", "success");
            const stockElement = Utils.safeQuerySelector(
              `[data-product-id="${productId}"] .stock-value`
            );
            if (stockElement) {
              stockElement.textContent = data.newStock;
            }
          } else {
            FlashMessages.show(
              data.message || "在庫の更新に失敗しました",
              "error"
            );
          }
        })
        .catch((error) => {
          console.error("Error updating stock:", error);
          FlashMessages.show("在庫の更新に失敗しました", "error");
        });
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

        const elements = Utils.safeQuerySelectorAll(".card, .table, .nav-item");
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
      }
    },

    showOnMobile: function () {
      if (window.innerWidth <= 768) {
        this.elements.mobileNav.classList.add("show");
      } else {
        this.elements.mobileNav.classList.remove("show");
      }
    },

    handleResize: function () {
      window.addEventListener("resize", () => {
        this.showOnMobile();
      });
    },
  };

  // Async Navigation Management
  const AsyncNavigation = {
    init: function () {
      this.bindEvents();
      this.handleInitialState();
    },

    bindEvents: function () {
      // Bind navigation links
      const navLinks = Utils.safeQuerySelectorAll(
        ".nav-link, .mobile-nav-item"
      );
      navLinks.forEach((link) => {
        Utils.addEventListener(link, "click", this.handleNavigation.bind(this));
      });

      // Handle browser back/forward buttons
      Utils.addEventListener(
        window,
        "popstate",
        this.handlePopState.bind(this)
      );

      // Handle form submissions
      const forms = Utils.safeQuerySelectorAll("form");
      forms.forEach((form) => {
        Utils.addEventListener(
          form,
          "submit",
          this.handleFormSubmit.bind(this)
        );
      });
    },

    handleNavigation: function (event) {
      const link = event.currentTarget;
      const href = link.getAttribute("href");

      if (!href || href.startsWith("#") || href.startsWith("javascript:")) {
        return; // Allow default behavior for anchors and javascript links
      }

      event.preventDefault();
      this.navigateTo(href, link);
    },

    handlePopState: function (event) {
      if (event.state && event.state.url) {
        this.loadPage(event.state.url, false);
      }
    },

    handleFormSubmit: function (event) {
      const form = event.currentTarget;
      const action = form.getAttribute("action");
      const method = form.getAttribute("method") || "GET";

      if (method.toLowerCase() === "get") {
        event.preventDefault();
        this.navigateTo(
          action + "?" + new URLSearchParams(new FormData(form)).toString()
        );
      }
    },

    navigateTo: function (url, link = null) {
      if (AdminState.currentPage === url) return;

      Utils.showLoading();

      // Update active state
      this.updateActiveState(url, link);

      // Load page content
      this.loadPage(url, true);
    },

    loadPage: function (url, updateHistory = true) {
      fetch(url, {
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          Accept:
            "text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
        },
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.text();
        })
        .then((html) => {
          const content = Utils.extractContent(html);
          this.updatePageContent(content);

          if (updateHistory) {
            Utils.updateHistory(url);
          }

          AdminState.currentPage = url;
          this.updatePageTitle(html);
          this.handlePageSpecificScripts(url);

          Utils.hideLoading();
        })
        .catch((error) => {
          console.error("Navigation error:", error);
          Utils.hideLoading();
          // Fallback to normal navigation
          window.location.href = url;
        });
    },

    updatePageContent: function (content) {
      const pageContent = Utils.safeQuerySelector(".page-content");
      if (pageContent) {
        // Fade out current content
        pageContent.style.opacity = "0";
        pageContent.style.transform = "translateY(10px)";

        setTimeout(() => {
          pageContent.innerHTML = content;
          pageContent.style.opacity = "1";
          pageContent.style.transform = "translateY(0)";

          // Reinitialize page-specific functionality
          this.reinitializePageScripts();
        }, 150);
      }
    },

    updateActiveState: function (url, link = null) {
      // Remove active class from all links
      const allLinks = Utils.safeQuerySelectorAll(
        ".nav-link, .mobile-nav-item"
      );
      allLinks.forEach((l) => l.classList.remove("active"));

      // Add active class to current link
      if (link) {
        link.classList.add("active");
      } else {
        // Find matching link
        const matchingLink = Array.from(allLinks).find((l) => {
          const href = l.getAttribute("href");
          return href && url.includes(href);
        });
        if (matchingLink) {
          matchingLink.classList.add("active");
        }
      }
    },

    updatePageTitle: function (html) {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      const title = doc.querySelector("title");
      if (title) {
        document.title = title.textContent;
      }
    },

    handlePageSpecificScripts: function (url) {
      // Handle specific page scripts
      if (url.includes("/admin/reserve_list")) {
        this.initializeReserveList();
      } else if (url.includes("/admin/menu/edit")) {
        this.initializeMenuEdit();
      } else if (url.includes("/admin/statistics")) {
        this.initializeStatistics();
      }
    },

    reinitializePageScripts: function () {
      // Reinitialize modals
      ModalManager.init();

      // Reinitialize flash messages
      FlashMessages.init();

      // Reinitialize any other page-specific functionality
      const currentUrl = AdminState.currentPage;
      this.handlePageSpecificScripts(currentUrl);
    },

    initializeReserveList: function () {
      // Initialize reservation list specific functionality
      const actionButtons = Utils.safeQuerySelectorAll(".action-btn");
      actionButtons.forEach((button) => {
        Utils.addEventListener(
          button,
          "click",
          this.handleReservationAction.bind(this)
        );
      });
    },

    initializeMenuEdit: function () {
      // Initialize menu edit specific functionality
      const editButtons = Utils.safeQuerySelectorAll(".edit-btn");
      editButtons.forEach((button) => {
        Utils.addEventListener(button, "click", this.handleMenuEdit.bind(this));
      });
    },

    initializeStatistics: function () {
      // Initialize statistics specific functionality
      // Add any chart initialization or data loading here
    },

    handleReservationAction: function (event) {
      const button = event.currentTarget;
      const action = button.getAttribute("data-action");
      const reservationId = button.getAttribute("data-id");

      if (action && reservationId) {
        this.performReservationAction(action, reservationId);
      }
    },

    handleMenuEdit: function (event) {
      const button = event.currentTarget;
      const menuId = button.getAttribute("data-id");

      if (menuId) {
        this.loadMenuEditForm(menuId);
      }
    },

    performReservationAction: function (action, reservationId) {
      const url = `/admin/reservation/${reservationId}/${action}`;

      fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            FlashMessages.show(data.message, "success");
            // Refresh the current page content
            this.loadPage(AdminState.currentPage, false);
          } else {
            FlashMessages.show(data.message || "エラーが発生しました", "error");
          }
        })
        .catch((error) => {
          console.error("Action error:", error);
          FlashMessages.show("エラーが発生しました", "error");
        });
    },

    loadMenuEditForm: function (menuId) {
      const url = `/admin/menu/edit/${menuId}`;
      this.loadPage(url, true);
    },

    handleInitialState: function () {
      // Set initial active state
      const currentPath = window.location.pathname;
      this.updateActiveState(currentPath);
      AdminState.currentPage = currentPath;
    },
  };

  // Main application initialization
  const AdminApp = {
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
        ModalManager.init();
        FlashMessages.init();
        UserMenu.init();
        Accessibility.init();
        Performance.init();
        MobileNav.init(); // Initialize MobileNav
        AsyncNavigation.init(); // Initialize AsyncNavigation

        // Update navigation active state
        Navigation.updateActiveState();

        // Add global error handler
        this.handleGlobalErrors();

        // Expose functions to global scope
        this.exposeGlobalFunctions();

        console.log("Kobuy Admin Application initialized successfully");
      } catch (error) {
        console.error("Failed to initialize admin application:", error);
      }
    },

    handleGlobalErrors: function () {
      window.addEventListener("error", (event) => {
        console.error("Global error:", event.error);
        FlashMessages.show("予期しないエラーが発生しました", "error");
      });

      window.addEventListener("unhandledrejection", (event) => {
        console.error("Unhandled promise rejection:", event.reason);
        FlashMessages.show("予期しないエラーが発生しました", "error");
      });
    },

    exposeGlobalFunctions: function () {
      // Expose modal manager to global scope
      window.modalManager = ModalManager;

      // Expose admin functions to global scope
      window.showProductDetail =
        AdminFunctions.showProductDetail.bind(AdminFunctions);
      window.showReservationDetail =
        AdminFunctions.showReservationDetail.bind(AdminFunctions);
      window.updateReservationStatus =
        AdminFunctions.updateReservationStatus.bind(AdminFunctions);
      window.updateStock = AdminFunctions.updateStock.bind(AdminFunctions);
    },
  };

  // Expose modules to global scope for debugging
  window.KobuyAdmin = {
    Navigation,
    ModalManager,
    FlashMessages,
    UserMenu,
    Ajax,
    AdminFunctions,
    Accessibility,
    Performance,
    Utils,
    AdminState,
    MobileNav, // Expose MobileNav to global scope
  };

  // Initialize the application
  AdminApp.init();
})();
