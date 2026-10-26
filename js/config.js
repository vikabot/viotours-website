/* viotours.in — site settings. Edit these, then reload. No rebuild needed. */
window.VIOTOURS = {
  // Where enquiry, contact, partner and newsletter forms POST (JSON).
  // The bundled Python endpoint (server/enquiry_server.py) listens on /api/enquiry behind nginx.
  // Leave "" to skip the POST and hand the message straight to WhatsApp / email instead.
  // GitHub Pages is static-only, so there is no /api/ there: leave "" and forms hand off to WhatsApp/email.
  // Set to a form service URL (Formspree, Web3Forms…) or your own server's /api/enquiry to store leads.
  enquiryEndpoint: "",

  // Fallback contact if the endpoint is down. International format, digits only.
  whatsappNumber: "919595251177",          // +91 95952 51177 (wa.me format: country code + number, digits only)
  email: "connect@viotours.in",            // forwards to viotours.in@gmail.com (Spaceship email forwarding)

  // Theme music (design system: plays once on load at 35%, mute remembered for the session).
  music: { enabled: true, volume: 0.35, loop: false },

  // Approximate rates for the AED / USD hint under INR prices. Update when you reprice.
  fx: { AED: 22.7, USD: 83.5 }   // INR per 1 unit
};
