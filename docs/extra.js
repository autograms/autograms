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

  // Create a MutationObserver to detect changes in the DOM
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'childList') {
        console.log("Content updated");
        initialize();
      }
    });
  });

  // Observe the body for changes
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
});