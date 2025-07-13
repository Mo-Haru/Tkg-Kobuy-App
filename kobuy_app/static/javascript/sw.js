// Service Worker for Push Notifications
const CACHE_NAME = "kobuy-app-v1";
const urlsToCache = [
  "/",
  "/static/css/style.css",
  "/static/javascript/kari.js",
];

// Install event
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache);
    })
  );
});

// Fetch event
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      // Return cached version or fetch from network
      return response || fetch(event.request);
    })
  );
});

// Push event
self.addEventListener("push", (event) => {
  console.log("Push event received:", event);

  let notificationData = {
    title: "Kobuy App",
    body: "新しい通知があります",
    icon: "/static/favicon.ico",
    badge: "/static/favicon.ico",
    tag: "kobuy-notification",
    data: {},
  };

  if (event.data) {
    try {
      const data = event.data.json();
      notificationData = {
        ...notificationData,
        title: data.title || notificationData.title,
        body: data.message || notificationData.body,
        data: data.data || {},
      };
    } catch (error) {
      console.error("Error parsing push data:", error);
    }
  }

  const notificationPromise = self.registration.showNotification(
    notificationData.title,
    {
      body: notificationData.body,
      icon: notificationData.icon,
      badge: notificationData.badge,
      tag: notificationData.tag,
      data: notificationData.data,
      requireInteraction: true,
      actions: [
        {
          action: "open",
          title: "開く",
          icon: "/static/favicon.ico",
        },
        {
          action: "close",
          title: "閉じる",
        },
      ],
    }
  );

  event.waitUntil(notificationPromise);
});

// Notification click event
self.addEventListener("notificationclick", (event) => {
  console.log("Notification clicked:", event);

  event.notification.close();

  if (event.action === "close") {
    return;
  }

  // Open the app when notification is clicked
  event.waitUntil(
    clients
      .matchAll({
        type: "window",
        includeUncontrolled: true,
      })
      .then((clientList) => {
        // Check if there's already a window/tab open with the target URL
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i];
          if (client.url.includes("/") && "focus" in client) {
            return client.focus();
          }
        }

        // If no window/tab is open, open a new one
        if (clients.openWindow) {
          return clients.openWindow("/");
        }
      })
  );
});

// Background sync (for offline support)
self.addEventListener("sync", (event) => {
  console.log("Background sync event:", event);

  if (event.tag === "background-sync") {
    event.waitUntil(
      // Perform background sync tasks here
      console.log("Background sync completed")
    );
  }
});

// Message event (for communication with main thread)
self.addEventListener("message", (event) => {
  console.log("Service Worker received message:", event.data);

  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});
