/* viotours.in — site settings. Edit these, then reload. No rebuild needed. */
window.VIOTOURS = {
  // Where enquiry, contact, partner and newsletter forms POST (JSON).
  // The bundled Python endpoint (server/enquiry_server.py) listens on /api/enquiry behind nginx.
  // Leave "" to skip the POST and hand the message straight to WhatsApp / email instead.
  enquiryEndpoint: "/api/enquiry",

  // Fallback contact if the endpoint is down. International format, digits only.
  whatsappNumber: "910000000000",          // TODO: your WhatsApp Business number
  email: "hello@viotours.in",              // TODO: confirm the inbox

  // Theme music (design system: plays once on load at 35%, mute remembered for the session).
  music: { enabled: true, volume: 0.35, loop: false },

  // Approximate rates for the AED / USD hint under INR prices. Update when you reprice.
  fx: { AED: 22.7, USD: 83.5 }   // INR per 1 unit
};
