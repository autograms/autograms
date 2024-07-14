function checkHomePage() {
  // Check if the current page is the home page
  const pathname = window.location.pathname;
  console.log("Current pathname: " + pathname);  // Log the current URL path
  alert("Current pathname: " + pathname);  // Alert to display the current URL path

  // Specific path for the home page
  if (pathname === '/autograms' || pathname === '/autograms/' || pathname === '/autograms/index.html') {
    console.log("This is the home page");  // Log to confirm the home page condition
    alert("This is the home page");  // Alert to confirm the home page condition
    document.body.classList.add('home-page');
  } else {
    console.log("This is not the home page");  // Log to confirm other pages
    alert("This is not the home page");  // Alert to confirm other pages
    document.body.classList.remove('home-page');
  }
}

function initialize() {
  checkHomePage();
}

document.addEventListener("DOMContentLoaded", function() {
  console.log("DOM fully loaded and parsed");
  alert("DOM fully loaded and parsed");
  initialize();
});

if (typeof document$1 !== 'undefined') {
  document$1.events.on('content', function() {
    console.log("Content updated");
    alert("Content updated");
    initialize();
  });
}