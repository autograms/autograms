function checkHomePage() {
  // Check if the current page is the home page
  const pathname = window.location.pathname;
 

  // Specific path for the home page
  if (pathname === '/autograms' || pathname === '/autograms/' || pathname === '/autograms/index.html') {

    document.body.classList.add('home-page');
  } else {

    document.body.classList.remove('home-page');
  }
}

function initialize() {
  checkHomePage();
}

document.addEventListener("DOMContentLoaded", function() {

  initialize();

  // Create a MutationObserver to detect changes in the DOM
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'childList') {

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