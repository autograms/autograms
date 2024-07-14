function checkHomePage() {
  // Check if the current page is the home page
  const pathname = window.location.pathname;
  console.log("Current pathname: " + pathname);  // Log the current URL path

  // Specific path for the home page
  if (pathname === '/autograms' || pathname === '/autograms/' || pathname === '/autograms/index.html') {
    console.log("This is the home page");  // Log to confirm the home page condition
    document.body.classList.add('home-page');
  } else {
    console.log("This is not the home page");  // Log to confirm other pages
    document.body.classList.remove('home-page');
  }
}

function initialize() {
  checkHomePage();
}

document.addEventListener("DOMContentLoaded", function() {
  console.log("DOM fully loaded and parsed");
  initialize();
});

if (typeof $ !== 'undefined' && $.events && $.events.on) {
  $.events.on('navigation.done', function() {
    console.log("Navigation done");
    initialize();
  });
} else {
  console.log("MkDocs Material events not available");
}