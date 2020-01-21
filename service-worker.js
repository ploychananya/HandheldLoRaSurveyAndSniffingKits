
importScripts("/workbox-sw.js");

importScripts(
  "/precache-manifest.0a5a7523691f2f8050c138c5fd093c87.js"
);

workbox.core.setCacheNameDetails({prefix: "handheld-lora-survey-sniffing-kits"});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

/**
 * The workboxSW.precacheAndRoute() method efficiently caches and responds to
 * requests for URLs in the manifest.
 * See https://goo.gl/S9QRab
 */
self.__precacheManifest = [].concat(self.__precacheManifest || []);
workbox.precaching.precacheAndRoute(self.__precacheManifest, {});
